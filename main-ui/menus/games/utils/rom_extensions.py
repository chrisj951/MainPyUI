class RomExtensions:
    """A mapping of common game systems to their ROM file extensions."""

    EXTENSIONS = {
        # Arcade
        "mame": [".zip", ".7z"],
        "neo_geo": [".zip"],

        # Nintendo
        "nes": [".nes", ".fds"],
        "snes": [".smc", ".sfc"],
        "n64": [".n64", ".z64", ".v64"],
        "game_boy": [".gb"],
        "game_boy_color": [".gbc"],
        "game_boy_advance": [".gba"],
        "nintendo_ds": [".nds"],
        "nintendo_3ds": [".3ds", ".cia"],
        "wii": [".iso", ".wbfs", ".wad"],
        "wii_u": [".wud", ".wux", ".rpx"],
        "switch": [".xci", ".nsp"],

        # Sega
        "sg_1000": [".sg"],
        "master_system": [".sms"],
        "game_gear": [".gg"],
        "genesis": [".bin", ".gen", ".md"],
        "sega_32x": [".32x"],
        "sega_cd": [".iso", ".bin", ".cue"],
        "saturn": [".cue", ".bin", ".iso"],
        "dreamcast": [".cdi", ".gdi", ".chd"],

        # Sony PlayStation
        "ps1": [".cue", ".bin", ".img", ".pbp"],
        "ps2": [".iso"],
        "psp": [".iso", ".cso", ".pbp"],
        "ps3": [".iso", ".pkg"],
        "ps4": [".pkg"],

        # Atari
        "atari_2600": [".a26", ".bin"],
        "atari_5200": [".a52"],
        "atari_7800": [".a78"],
        "atari_lynx": [".lnx"],
        "atari_jaguar": [".j64", ".jag"],
        "atari_jaguar_cd": [".cue", ".bin"],

        # Neo Geo Handhelds
        "neo_geo_pocket": [".ngp"],
        "neo_geo_pocket_color": [".ngc"],

        # NEC
        "pc_engine": [".pce"],
        "pc_engine_cd": [".cue", ".bin"],
        "supergrafx": [".sgx"],

        # Commodore / Computers
        "commodore_64": [".d64", ".t64", ".prg"],
        "amiga": [".adf", ".adz", ".dms"],
        "msx": [".rom", ".mx1", ".mx2"],
        "zx_spectrum": [".tap", ".tzx", ".z80"],

        # Misc Handhelds
        "wonderswan": [".ws"],
        "wonderswan_color": [".wsc"],
        "colecovision": [".col"],
        "intellivision": [".int", ".bin"],

        # Common compressed disc format
        "chd_supported": [".chd"],  # Universal compressed format

        # Ports
        "ports": [".sh"],

    }

    @classmethod
    def get_extensions(cls, system_name: str):
        """
        Return a list of valid ROM extensions for a given system.
        :param system_name: The system name key (e.g., 'snes', 'ps1')
        :return: List of file extensions or an empty list if not found.
        """
        return cls.EXTENSIONS.get(system_name.lower(), [])

    @classmethod
    def is_valid_rom(cls, system_name: str, filename: str) -> bool:
        """
        Check if the given filename has a valid ROM extension for the specified system.
        :param system_name: The system name key (e.g., 'snes', 'ps1')
        :param filename: The ROM filename to validate
        :return: True if valid, False otherwise
        """
        filename = filename.lower()
        return any(filename.endswith(ext) for ext in cls.get_extensions(system_name))
