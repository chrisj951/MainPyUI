from typing import Protocol, TypeGuard


class HasSortOrder(Protocol):
    def get_sort_order(self): ...


class HasBrand(Protocol):
    def get_brand(self): ...


class HasType(Protocol):
    def get_type(self): ...


class HasReleaseYear(Protocol):
    def get_release_year(self): ...


class HasIgnoreList(Protocol):
    def get_ignore_list(self): ...


class HasDevices(Protocol):
    def get_devices(self): ...


class HasMenuOptions(Protocol):
    def get_menu_options(self): ...


class HasMenuOverrides(Protocol):
    def contains_menu_override(self, name, rom_file_path): ...
    def delete_menu_override(self, name, rom_file_path): ...
    def get_effective_menu_selection(self, name, rom_file_path): ...
    def set_menu_override(self, name, rom_file_path, value): ...
    def set_menu_option(self, name, value): ...


class HasReloadConfig(Protocol):
    def reload_config(self): ...


class HasForceRefresh(Protocol):
    def force_refresh(self): ...


def has_sort_order(obj) -> TypeGuard[HasSortOrder]:
    return hasattr(obj, "get_sort_order")


def has_brand(obj) -> TypeGuard[HasBrand]:
    return hasattr(obj, "get_brand")


def has_type(obj) -> TypeGuard[HasType]:
    return hasattr(obj, "get_type")


def has_release_year(obj) -> TypeGuard[HasReleaseYear]:
    return hasattr(obj, "get_release_year")


def has_ignore_list(obj) -> TypeGuard[HasIgnoreList]:
    return hasattr(obj, "get_ignore_list")


def has_devices(obj) -> TypeGuard[HasDevices]:
    return hasattr(obj, "get_devices")


def has_menu_options(obj) -> TypeGuard[HasMenuOptions]:
    return hasattr(obj, "get_menu_options")


def has_menu_overrides(obj) -> TypeGuard[HasMenuOverrides]:
    return all(
        hasattr(obj, attr)
        for attr in (
            "contains_menu_override",
            "delete_menu_override",
            "get_effective_menu_selection",
            "set_menu_override",
            "set_menu_option",
        )
    )


def has_reload_config(obj) -> TypeGuard[HasReloadConfig]:
    return hasattr(obj, "reload_config")


def has_force_refresh(obj) -> TypeGuard[HasForceRefresh]:
    return callable(getattr(obj, "force_refresh", None))
