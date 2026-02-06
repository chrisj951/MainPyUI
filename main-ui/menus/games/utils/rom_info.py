

from dataclasses import dataclass
import os
from typing import Optional

from games.utils.game_system import GameSystem
from menus.games.utils.rom_file_name_utils import RomFileNameUtils


@dataclass
class RomInfo:
    game_system: GameSystem | None
    rom_file_path: str
    is_collection: bool
    display_name: Optional[str]

    def __init__(self, game_system: GameSystem | None, rom_file_path: str, display_name=None, is_collection=False):
        self.game_system = game_system
        self.rom_file_path = rom_file_path
        self.display_name = display_name
        if self.display_name is None:
            if self.game_system is not None:
                self.display_name = RomFileNameUtils.get_rom_name_without_extensions(game_system, rom_file_path)
            else:
                self.display_name = rom_file_path
        self.is_collection = is_collection
        
