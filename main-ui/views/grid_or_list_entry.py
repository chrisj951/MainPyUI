import threading
from typing import Callable, TypeVar

from menus.games.utils.rom_info import RomInfo

T = TypeVar('T')  # Generic input type

class GridOrListEntry:
    def __init__(
        self,
        primary_text,
        value_text=None,
        image_path=None,
        image_path_selected=None,
        description=None,
        icon=None,
        value: T = None,
        image_path_searcher: Callable[[T], str] = None,
        image_path_selected_searcher: Callable[[T], str] = None,
        icon_searcher: Callable[[T], str] = None,
        primary_text_long=None,
    ):        
        self.primary_text = primary_text
        self.primary_text_long = primary_text_long
        self.value_text = value_text
        self.image_path = image_path
        self.image_path_searcher = image_path_searcher
        self.image_path_selected_searcher = image_path_selected_searcher
        self.icon_searcher = icon_searcher

        self.image_path_selected = image_path_selected or image_path
        self.value = value if value is not None else primary_text
        self.icon = icon

        self._description = None
        self._description_func = None
        self._description_event = threading.Event()

        if callable(description):
            self._description_func = description
            threading.Thread(target=self._load_description, daemon=True).start()
        else:
            self._description = description
            self._description_event.set()  # Already available

    def _load_description(self):
        try:
            self._description = self._description_func()
        except Exception as e:
            self._description = f"[Error loading description: {e}]"
        finally:
            self._description_event.set()

    def __str__(self) -> str:
        return self.primary_text

    def __repr__(self) -> str:
        return f"<GridOrListEntry {self.primary_text!r}>"
    
    def get_image_path(self):
        if self.image_path is None and self.image_path_searcher is not None:
            return self.image_path_searcher(self.value)
        return self.image_path
    
    def get_image_path_selected(self):
        if self.image_path_selected is None and self.image_path_selected_searcher is not None:
            return self.image_path_selected_searcher(self.value)
        return self.image_path_selected
    
    def get_primary_text(self):
        return self.primary_text
    
    def get_primary_text_long(self):
        return self.primary_text_long or self.primary_text
    
    def get_value_text(self):
        return self.value_text
    
    def get_value(self):
        return self.value
    
    def get_description(self):
        self._description_event.wait()  # Block until description is loaded
        return self._description

    def get_icon(self):
        if self.icon is None and self.icon_searcher is not None:
            return self.icon_searcher(self.value)
        return self.icon
    
    def __eq__(self, other):
        if not isinstance(other, GridOrListEntry):
            return NotImplemented
        return self.value == other.value
