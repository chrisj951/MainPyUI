import os
from pathlib import Path
import subprocess
import json
import re
import time
import urllib.request
from typing import List, Optional

from devices.device import Device
from display.display import Display
from games.utils.box_art_resizer import BoxArtResizer
from utils.logger import PyUiLogger
import re
import difflib
from typing import Optional

class BoxArtScraper:
    # optional abbreviation mapping
    ABBREVIATIONS = {
        "ff": "final fantasy",
        "zelda": "legend of zelda",
        "mario": "super mario",
        # add more as needed
    }

    # numbers → roman numerals
    NUM_TO_ROMAN = {
        "2": "ii", "3": "iii", "4": "iv", "5": "v",
        "6": "vi", "7": "vii", "8": "viii", "9": "ix", "10": "x"
    }

    STOPWORDS = {"and", "the", "of", "in", "is", "a", "an"}
    """
    Python version of the box art scraper script, converted into a class.
    Matches original shell behavior but without watchdog logic.
    """

    def __init__(self):
        self.base_dir = "/mnt/SDCARD"
        self.roms_dir = Device.get_roms_dir()
        script_dir = Path(__file__).resolve().parent
        self.db_dir = os.path.join(script_dir,"db")
        self.game_system_utils = Device.get_game_system_utils()
        self.preferred_region = Device.get_system_config().get_preferred_region()
    # ==========================================================
    # Helper Methods
    # ==========================================================

    def _ping(self, host: str, count: int = 2, timeout: int = 2) -> bool:
        """Ping a host to check connectivity."""
        result = subprocess.call(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result == 0

    def log_message(self, msg: str):
        PyUiLogger.get_logger().info(msg)

    def log_and_display_message(self, msg: str):
        self.log_message(msg)
        Display.display_message(msg)

    def is_wifi_connected(self) -> bool:
        """Check network connectivity by pinging Cloudflare."""
        if self._ping("1.1.1.1", count=3, timeout=2):
            self.log_message("Cloudflare ping successful; device is online.")
            return True
        else:
            self.log_and_display_message("Cloudflare ping failed; device is offline. Aborting.")
            return False

    def get_ra_alias(self, system: str) -> str:
        """Return Libretro alias name for system."""
        mapping = {
            "AMIGA": "Commodore - Amiga",
            "ATARI": "Atari - 2600",
            "ATARIST": "Atari - ST",
            "ARCADE": "MAME",
            "CPS1": "MAME",
            "CPS2": "MAME",
            "CPS3": "MAME",
            "ARDUBOY": "Arduboy Inc - Arduboy",
            "CHAI": "ChaiLove",
            "COLECO": "Coleco - ColecoVision",
            "COMMODORE": "Commodore - 64",
            "CPC": "Amstrad - CPC",
            "DC": "Sega - Dreamcast",
            "DOOM": "DOOM",
            "DOS": "DOS",
            "EIGHTHUNDRED": "Atari - 8-bit",
            "FAIRCHILD": "Fairchild - Channel F",
            "FBNEO": "FBNeo - Arcade Games",
            "FC": "Nintendo - Nintendo Entertainment System",
            "FDS": "Nintendo - Family Computer Disk System",
            "FIFTYTWOHUNDRED": "Atari - 5200",
            "GB": "Nintendo - Game Boy",
            "GBA": "Nintendo - Game Boy Advance",
            "GBC": "Nintendo - Game Boy Color",
            "GG": "Sega - Game Gear",
            "GW": "Handheld Electronic Game",
            "INTELLIVISION": "Mattel - Intellivision",
            "LYNX": "Atari - Lynx",
            "MD": "Sega - Mega Drive - Genesis",
            "MS": "Sega - Master System - Mark III",
            "MSU1": "Nintendo - Super Nintendo Entertainment System",
            "MSUMD": "Sega - Mega Drive - Genesis",
            "MSX": "Microsoft - MSX",
            "N64": "Nintendo - Nintendo 64",
            "NDS": "Nintendo - Nintendo DS",
            "NEOCD": "SNK - Neo Geo CD",
            "NEOGEO": "SNK - Neo Geo",
            "NGP": "SNK - Neo Geo Pocket",
            "NGPC": "SNK - Neo Geo Pocket Color",
            "ODYSSEY": "Magnavox - Odyssey2",
            "PCE": "NEC - PC Engine - TurboGrafx 16",
            "PCECD": "NEC - PC Engine CD - TurboGrafx-CD",
            "POKE": "Nintendo - Pokemon Mini",
            "PS": "Sony - PlayStation",
            "PSP": "Sony - PlayStation Portable",
            "QUAKE": "Quake",
            "SATELLAVIEW": "Nintendo - Satellaview",
            "SATURN": "Sega - Saturn",
            "SCUMMVM": "ScummVM",
            "SEGACD": "Sega - Mega-CD - Sega CD",
            "SEGASGONE": "Sega - SG-1000",
            "SEVENTYEIGHTHUNDRED": "Atari - 7800",
            "SFC": "Nintendo - Super Nintendo Entertainment System",
            "SGB": "Nintendo - Game Boy",
            "SGFX": "NEC - PC Engine SuperGrafx",
            "SUFAMI": "Nintendo - Sufami Turbo",
            "SUPERVISION": "Watara - Supervision",
            "THIRTYTWOX": "Sega - 32X",
            "TIC": "TIC-80",
            "VB": "Nintendo - Virtual Boy",
            "VECTREX": "GCE - Vectrex",
            "VIC20": "Commodore - VIC-20",
            "VIDEOPAC": "Philips - Videopac+",
            "WOLF": "Wolfenstein 3D",
            "WS": "Bandai - WonderSwan",
            "WSC": "Bandai - WonderSwan Color",
            "X68000": "Sharp - X68000",
            "ZXS": "Sinclair - ZX Spectrum",
        }
        return mapping.get(system.upper(), "")

    def _get_supported_extensions(self, sys_name: str) -> list[str]:
        """Get extensions from Emu config.json."""
        game_system = self.game_system_utils.get_game_system_by_name(sys_name)
        if(game_system is None):
            return []
        else:
            return game_system.game_system_config.get_extlist()

    def find_image_name(self, sys_name: str, rom_file_name: str) -> Optional[str]:
        """Match ROM to image name based on db/<system>_games.txt."""
        image_list_file = os.path.join(self.db_dir, f"{sys_name}_games.txt")
        if not os.path.exists(image_list_file):
            PyUiLogger.get_logger().warning(f"BoxartScraper: Image list file not found for {sys_name}.")
            return None

        rom_without_ext = os.path.splitext(rom_file_name)[0]
        with open(image_list_file, "r", encoding="utf-8", errors="ignore") as f:
            image_list = f.read().splitlines()

        return self.find_image_from_list(rom_without_ext, image_list)

    def preprocess_token(self, token: str) -> str:
        token = token.lower()
        if token in self.ABBREVIATIONS:
            return self.ABBREVIATIONS[token]
        if token in self.NUM_TO_ROMAN:
            return self.NUM_TO_ROMAN[token]
        return token

    def strip_parentheses(self, s: str) -> str:
        s = re.sub(r"\(.*?\)", "", s)
        return re.sub(r"[\s\-_,]+", " ", s).strip()

    def tokenize(self, s: str) -> set[str]:
        s = s.replace("_", " ").lower()
        s = re.sub(r"[^\w\s]+", " ", s)  # remove punctuation
        token_list = [self.preprocess_token(t) for t in s.split() if t not in self.STOPWORDS]

        # Build 2-word compounds
        compounds = {"".join(token_list[i:i+2]) for i in range(len(token_list)-1)}

        return set(token_list) | compounds

    def weighted_similarity(self, target: str, candidate: str) -> float:
        candidate_for_match = candidate
        if "(" not in target:
            candidate_for_match = self.strip_parentheses(candidate)

        t_tokens = list(self.tokenize(target))
        c_tokens = list(self.tokenize(candidate_for_match))

        if not t_tokens or not c_tokens:
            return 0.0

        # Penalize missing tokens, ignoring '1' or 'i'
        missing_tokens = set(t_tokens) - set(c_tokens)
        penalty = 0
        for tok in missing_tokens:
            if tok not in {"1", "i"}:
                penalty += 0.3

        # Intersection over union
        score = len(set(t_tokens) & set(c_tokens)) / len(set(t_tokens) | set(c_tokens))
        score -= penalty
        return max(score, 0.0)

    def find_image_from_list(self, rom_without_ext: str, image_list: List[str]) -> Optional[str]:
        best_score = 0.0
        best_candidates = []

        for name in image_list:
            candidate = name.lower().replace(".png", "")
            score = self.weighted_similarity(rom_without_ext, candidate)

            if score > best_score:
                best_score = score
                best_candidates = [name]
            elif score == best_score:
                best_candidates.append(name)

        if not best_candidates or best_score < 0.3:
            return None

        # Preferred region tie-breaker
        if self.preferred_region:
            for candidate in best_candidates:
                matches = re.findall(r"\(([^)]*?)\)", candidate, re.IGNORECASE)
                for match in matches:
                    if self.preferred_region in match.upper():
                        return candidate

        # Shortest filename tie-breaker
        return min(best_candidates, key=len)

    # ==========================================================
    # Main Scraper Logic
    # ==========================================================
    def scrape_boxart(self):
        self.log_and_display_message(
            "Scraping box art. Please be patient, especially with large libraries!"
        )
        #time.sleep(1)

        if not Device.is_wifi_enabled():
            Display.display_message("Wifi must be connected",2000)

        if not self._ping("thumbnails.libretro.com"):
            self.log_and_display_message("Libretro thumbnail service unavailable; trying fallback.")
            if not self._ping("github.com"):
                self.log_and_display_message(
                    "Libretro thumbnail GitHub repo is also currently unavailable. Please try again later."
                )
                time.sleep(3)
                return

        for sys_dir in [d for d in os.listdir(self.roms_dir) if os.path.isdir(os.path.join(self.roms_dir, d))]:
            sys_path = os.path.join(self.roms_dir, sys_dir)
            sys_name = os.path.basename(sys_path)

            ra_name = self.get_ra_alias(sys_name)
            if not ra_name:
                self.log_message(f"BoxartScraper: Remote system name not found - skipping {sys_name}.")
                continue

            extensions = self._get_supported_extensions(sys_name)
            if not extensions:
                self.log_message(f"BoxartScraper: No supported extensions found for {sys_name}.")
                continue

            first_game = True
            for root, _, files in os.walk(sys_path):
                if "Imgs" in root:
                    continue
                for file in files:
                    if not any(file.lower().endswith(f"{ext.lower()}") for ext in extensions):
                        #self.log_message(f"BoxartScraper: {file} does not end with {extensions}.")
                        continue

                    if not os.path.exists(os.path.join(root, "Imgs")):
                        os.makedirs(os.path.join(root, "Imgs"), exist_ok=True)

                    rom_name = os.path.splitext(file)[0]
                    image_path = os.path.join(root, "Imgs", f"{rom_name}.png")

                    # Skip if any image already exists
                    existing = [
                        f for f in os.listdir(os.path.join(root, "Imgs"))
                        if f.startswith(rom_name + ".")
                    ]
                    if existing:
                        continue

                    if first_game:
                        self.log_and_display_message(f"BoxartScraper: Scraping box art for {sys_name}")
                        first_game = False

                    remote_image_name = self.find_image_name(sys_name, file)
                    if not remote_image_name:
                        self.log_message(f"BoxartScraper: No image found for {file} in {sys_name}.")
                        continue

                    boxart_url = f"http://thumbnails.libretro.com/{ra_name}/Named_Boxarts/{remote_image_name}".replace(" ", "%20")
                    fallback_url = f"https://raw.githubusercontent.com/libretro-thumbnails/{ra_name.replace(' ', '_')}/master/Named_Boxarts/{remote_image_name}".replace(" ", "%20")

                    self.log_message(f"BoxartScraper: Downloading {boxart_url}")
                    success = self._download_file(boxart_url, image_path)
                    if not success:
                        self.log_message(f"BoxartScraper: failed {boxart_url}, trying fallback.")
                        if not self._download_file(fallback_url, image_path):
                            self.log_message(f"BoxartScraper: failed {fallback_url}.")

        self.log_and_display_message("Scraping complete!")
        time.sleep(2)
        BoxArtResizer.patch_boxart()

    # ==========================================================
    # File Download
    # ==========================================================

    def _download_file(self, url: str, dest_path: str) -> bool:
        """Download file to destination path."""
        try:
            urllib.request.urlretrieve(url, dest_path)
            return True
        except Exception:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False
