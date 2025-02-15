#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations
import logging

from tuxemon.event.eventaction import EventAction
from typing import NamedTuple, final

logger = logging.getLogger(__name__)


class StopCinemaModeActionParameters(NamedTuple):
    pass


@final
class StopCinemaModeAction(EventAction[StopCinemaModeActionParameters]):
    """
    Stop cinema mode by animating black bars back to the normal aspect ratio.

    Script usage:
        .. code-block::

            stop_cinema_mode

    """

    name = "stop_cinema_mode"
    param_class = StopCinemaModeActionParameters

    def start(self) -> None:
        world = self.session.client.current_state
        if world.cinema_state == "on":
            logger.info("Turning off cinema mode")
            world.cinema_state = "turning off"
