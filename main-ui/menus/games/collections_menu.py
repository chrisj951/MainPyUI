
import os
import subprocess
from devices.device import Device
from menus.games.roms_menu_common import RomsMenuCommon
from menus.games.utils.collections_manager import CollectionsManager
from menus.games.utils.favorites_manager import FavoritesManager
from menus.games.utils.rom_info import RomInfo
from views.grid_or_list_entry import GridOrListEntry


class CollectionsMenu(RomsMenuCommon):
    def __init__(self):
        super().__init__()

    def _get_rom_list(self) -> list[GridOrListEntry]:
        rom_list = []
        collections = CollectionsManager.get_collection_names()
        for collection in collections:
            rom_info = RomInfo(None, collection, is_collection=True)
            # Get the base filename without extension
            img_path = os.path.join(Device.get_collections_path(),"Imgs",collection+".png")

            rom_list.append(
                GridOrListEntry(
                    primary_text=collection,
                    image_path=img_path,
                    image_path_selected=img_path,
                    description="Collections", 
                    icon=None,
                    value=rom_info)
            )
        return rom_list

    def run_rom_selection(self) :
        return self._run_rom_selection("Collections")

    def _run_subfolder_menu(self, rom_info : RomInfo) -> list[GridOrListEntry]:
        rom_list = CollectionsManager.get_games_in_collection(rom_info.rom_file_path)
        return self._run_rom_selection_for_rom_list(rom_info.rom_file_path, rom_list)
