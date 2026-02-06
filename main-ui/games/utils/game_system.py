import os
from typing import TYPE_CHECKING, Union
from utils.type_guards import has_brand, has_release_year, has_sort_order, has_type

if TYPE_CHECKING:
    from menus.games.file_based_game_system_config import FileBasedGameSystemConfig
    from menus.games.muos_game_system_config import MuosGameSystemConfig

GameSystemConfig = Union["FileBasedGameSystemConfig", "MuosGameSystemConfig"]

class GameSystem:
    def __init__(self, folder_paths, display_name, game_system_config: GameSystemConfig):
        self._folder_paths = tuple(folder_paths)
        self._display_name = display_name
        self._game_system_config: GameSystemConfig = game_system_config

    @property
    def folder_name(self):
        return os.path.basename(self._folder_paths[0])

    @property
    def folder_paths(self):
        return self._folder_paths
    
    @property
    def display_name(self):
        return self._display_name
    
    @property
    def sort_order(self):
        cfg = self._game_system_config
        if has_sort_order(cfg):
            return cfg.get_sort_order()
        return 0
    
    @property
    def brand(self):
        cfg = self._game_system_config
        if has_brand(cfg):
            return cfg.get_brand()
        return ""
    
    @property
    def type(self):
        cfg = self._game_system_config
        if has_type(cfg):
            return cfg.get_type()
        return ""
    
    @property
    def release_year(self):
        cfg = self._game_system_config
        if has_release_year(cfg):
            return cfg.get_release_year()
        return ""
        
    @property
    def game_system_config(self) -> GameSystemConfig:
        return self._game_system_config
    
    # Equality: two systems are equal if their folder_paths are the same
    def __eq__(self, other):
        if not isinstance(other, GameSystem):
            return False
        return self._folder_paths == other._folder_paths

    # Hash: use folder_paths tuple
    def __hash__(self):
        return hash(self._folder_paths)
