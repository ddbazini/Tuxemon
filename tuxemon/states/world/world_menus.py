#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# Leif Theden <leif.theden@gmail.com>
# Carlos Ramos <vnmabus@gmail.com>
#
#
# states.WorldMenuState
#
from __future__ import annotations

import logging
from functools import partial
from typing import Any, Callable, Sequence, Tuple

import pygame_menu

from tuxemon import prepare
from tuxemon.animation import Animation
from tuxemon.locale import T
from tuxemon.menu.interface import MenuItem
from tuxemon.menu.menu import Menu, PygameMenuState
from tuxemon.session import local_session
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)


WorldMenuGameObj = Callable[[], object]


def add_menu_items(
    menu: pygame_menu.Menu,
    items: Sequence[Tuple[str, WorldMenuGameObj]],
) -> None:

    menu.add.vertical_fill()
    for key, callback in items:
        label = T.translate(key).upper()
        menu.add.button(label, callback)
        menu.add.vertical_fill()
        pass

    width, height = prepare.SCREEN_SIZE
    widgets_size = menu.get_size(widget=True)
    b_width, b_height = menu.get_scrollarea().get_border_size()
    menu.resize(
        widgets_size[0],
        height - 2 * b_height,
        position=(width + b_width, b_height, False),
    )


class WorldMenuState(PygameMenuState):
    """Menu for the world state."""

    def startup(self, **kwargs: Any) -> None:
        _, height = prepare.SCREEN_SIZE

        super().startup(height=height, **kwargs)

        self.animation_offset = 0

        def change_state(state: str, **kwargs: Any) -> Callable[[], object]:
            return partial(self.client.replace_state, state, **kwargs)

        def exit_game() -> None:
            self.client.event_engine.execute_action("quit")

        def not_implemented_dialog() -> None:
            open_dialog(local_session, [T.translate("not_implemented")])

        # Main Menu - Allows users to open the main menu in game.
        menu_items_map = (
            ("menu_journal", not_implemented_dialog),
            ("menu_monster", self.open_monster_menu),
            ("menu_bag", change_state("ItemMenuState")),
            ("menu_player", not_implemented_dialog),
            ("menu_save", change_state("SaveMenuState")),
            ("menu_load", change_state("LoadMenuState")),
            ("menu_options", change_state("ControlState")),
            ("exit", exit_game),
        )
        add_menu_items(self.menu, menu_items_map)

    def open_monster_menu(self) -> None:
        from tuxemon.states.monster import MonsterMenuState

        def monster_menu_hook() -> None:
            """
            Used to rearrange monsters interactively.

            This is slow b/c forces each slot to be re-rendered.
            Probably not an issue except for very slow systems.

            """
            monster = context.get("monster")
            if monster:
                # TODO: maybe some API for re-arranging menu items
                # at this point, the cursor will have changed
                # so we need to re-arrange the list before it is rendered again
                # TODO: API for getting the game player object
                player = local_session.player
                monster_list = player.monsters

                # get the newly selected item.  it will be set to previous
                # position
                original_monster = monster_menu.get_selected_item().game_object

                # get the position in the list of the cursor
                index = monster_list.index(original_monster)

                # set the old spot to the old monster
                monster_list[context["old_index"]] = original_monster

                # set the current cursor position to the monster we move
                monster_list[index] = context["monster"]

                # store the old index
                context["old_index"] = index

            # call the super class to re-render the menu with new positions
            # TODO: maybe add more hooks to eliminate this runtime patching
            MonsterMenuState.on_menu_selection_change(monster_menu)

        def select_first_monster() -> None:
            # TODO: API for getting the game player obj
            player = local_session.player
            monster = monster_menu.get_selected_item().game_object
            context["monster"] = monster
            context["old_index"] = player.monsters.index(monster)
            self.client.pop_state()  # close the info/move menu

        def open_monster_stats() -> None:
            open_dialog(local_session, [T.translate("not_implemented")])

        def positive_answer() -> None:
            success = False
            player = local_session.player
            monster = monster_menu.get_selected_item().game_object
            success = player.release_monster(monster)

            # TODO: Currently the menu does not close automatically.
            # It needs to be completely refreshed (by backing out or moving the cursor) in order for the player to see the change.
            # It still has the desired effect, but it would be better if the menu refreshed automatically.
            if success:
                self.client.pop_state()
                self.client.pop_state()
                open_dialog(
                    local_session,
                    [T.format("tuxemon_released", {"name": monster.name})],
                )
            else:
                open_dialog(local_session, [T.translate("cant_release")])

        def negative_answer() -> None:
            self.client.pop_state()  # close menu

        def release_monster_from_party() -> None:
            monster = monster_menu.get_selected_item().game_object
            menu = self.client.push_state(Menu)
            open_dialog(
                local_session,
                [T.format("release_confirmation", {"name": monster.name})],
            )

            menu_items_map = (
                ("no", negative_answer),
                ("yes", positive_answer),
            )

            add_menu_items(menu, menu_items_map)

        def open_monster_submenu(
            menu_item: MenuItem[WorldMenuGameObj],
        ) -> None:
            menu_items_map = (
                ("monster_menu_info", open_monster_stats),
                ("monster_menu_move", select_first_monster),
                ("monster_menu_release", release_monster_from_party),
            )
            menu = self.client.push_state(PygameMenuState)

            for key, callback in menu_items_map:
                label = T.translate(key).upper()
                menu.menu.add.button(label, callback)

            size = menu.menu.get_size(widget=True)
            menu.menu.resize(*size)

        def handle_selection(menu_item: MenuItem[WorldMenuGameObj]) -> None:
            if "monster" in context:
                del context["monster"]
            else:
                open_monster_submenu(menu_item)

        context = (
            dict()
        )  # dict passed around to hold info between menus/callbacks
        monster_menu = self.client.replace_state("MonsterMenuState")
        monster_menu.on_menu_selection = handle_selection
        monster_menu.on_menu_selection_change = monster_menu_hook

    def update_animation_position(self) -> None:
        self.menu.translate(-self.animation_offset, 0)

    def animate_open(self) -> Animation:
        """
        Animate the menu sliding in.

        Returns:
            Sliding in animation.

        """

        width = self.menu.get_width(border=True)
        self.animation_offset = 0

        ani = self.animate(self, animation_offset=width, duration=0.50)
        ani.update_callback = self.update_animation_position

        return ani

    def animate_close(self) -> Animation:
        """
        Animate the menu sliding out.

        Returns:
            Sliding out animation.

        """
        ani = self.animate(self, animation_offset=0, duration=0.50)
        ani.update_callback = self.update_animation_position

        return ani
