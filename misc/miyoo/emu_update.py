#!/usr/bin/env python3
import os
import json
import sys
import re
from collections import defaultdict

TARGET_NAMES = ("Emu Core", "CPU")
CLEANUP_REGEX = re.compile(r"[()\[\]✔✗❌•●]")

CONVERSION_MAP = {
    "PUAE2021": "puae2021",
    "UAE4ARM": "uae4arm",
    "MAME2003+": "mame2003_plus",
    "FBALPHA2012": "fbalpha2012",
    "FBNEO": "fbneo",
    "GEARCOLECO": "gearcoleco",
    "BLUEMSX": "bluemsx",
    "CROCODS": "crocods",
    "CAP32": "cap32",
    "FLYCAST-ALT": "flycast_xtreme",
    "FLYCAST_LR": "flycast",
    "FCEUMM": "fceumm",
    "NESTOPIA": "nestopia",
    "QUICKNES": "quicknes",
    "MGBA": "mgba",
    "TGBDUAL": "tgbdual",
    "GAMBATTE": "gambatte",
    "GPSP": "gpsp",
    "PICODRIVE": "picodrive",
    "GEARSYSTEM": "gearsystem",
    "GENESIS+GX": "genesis_plus_gx",
    "MEDNAFEN": "mednafen_ngp",
    "HANDY": "handy",
    "FMSX": "fmsx",
    "LUDICROUSN64": "km_ludicrousn64_2k22_xtreme_amped",
    "PARALLEL": "parallel_n64",
    "MUPEN64PLUS": "mupen64plus",
    "STEWARD": "drastic_steward",
    "ORIGINAL": "drastic_original",
    "TRNGAJE": "drastic_trngaje",
    "RACE": "race",
    "PCSX_REARMED": "pcsx_rearmed",
    "DUCKSWANSTATION": "km_duckswanstation_xtreme_amped",
    "SA_HLE": "sa_hle",
    "LIBRETRO": "yabasanshiro",
    "SA_BIOS": "sa_bios",
    "SUPAFAUST": "mednafen_supafaust",
    "SNES9X": "snes9x",
    "CHIMERASNES": "chimerasnes",
}

def parse_options_and_selected(raw_name: str, matched_target: str):
    """
    Parses a raw launchlist name and returns a tuple:
      - options: list of cleaned option names (converted if in conversion_map)
      - selected_option: the selected option (converted if in conversion_map)
    """

    s = raw_name.strip()
    if ":" in s:
        body = s.split(":", 1)[1]
    else:
        body = s[len(matched_target):] if s.startswith(matched_target) else s

    raw_parts = [part.strip() for part in body.split("-") if part.strip()]
    options = []
    selected_option = None

    for part in raw_parts:
        has_checkmark = "✓" in part
        cleaned = CLEANUP_REGEX.sub("", part.replace("✓", "")).strip().strip(":").strip()

        # Convert using conversion_map if present
        cleaned_converted = CONVERSION_MAP.get(cleaned, cleaned)

        if cleaned_converted:
            options.append(cleaned_converted)
            if has_checkmark:
                selected_option = cleaned_converted

    return options, selected_option

def process_folders(base_dir: str):
    if not os.path.isdir(base_dir):
        print(f"[ERROR] The specified directory does not exist: {base_dir}")
        return

    for folder_name in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.isdir(folder_path):
            continue

        config_path = os.path.join(folder_path, "config.json")
        if not os.path.isfile(config_path):
            print(f"[ERROR] No config.json found in: {folder_path}")
            continue

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON in {config_path}: {e}")
            continue

        launchlist = config_data.get("launchlist")
        if not isinstance(launchlist, list):
            launchlist = []

        options_by_key = defaultdict(list)
        selected_by_key = {}

        for item in launchlist:
            if not isinstance(item, dict):
                continue
            raw_name = item.get("name", "").strip()
            matched_target = next((t for t in TARGET_NAMES if raw_name.startswith(t)), None)
            if matched_target:
                options, selected = parse_options_and_selected(raw_name, matched_target)
                for opt in options:
                    if opt not in options_by_key[matched_target]:
                        options_by_key[matched_target].append(opt)
                if selected:
                    selected_by_key[matched_target] = selected

        config_data["cpuOptions"] = options_by_key.get("CPU", [])
        config_data["selectedCpu"] = selected_by_key.get("CPU", "")
        config_data["coreOptions"] = options_by_key.get("Emu Core", [])
        config_data["selectedCore"] = selected_by_key.get("Emu Core", "")

        # Write JSON with UNIX-style \n line endings
        try:
            with open(config_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                f.write("\n")  # ensure single newline at end
        except Exception as e:
            print(f"[ERROR] Failed to write updated JSON for {config_path}: {e}")
            continue

        # Optional: print summary
        print(f"{folder_name} updated:")
        print(f"  CPU Options: {config_data['cpuOptions']}, Selected: {config_data['selectedCpu']}")
        print(f"  Emu Core Options: {config_data['coreOptions']}, Selected: {config_data['selectedCore']}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <BASE_DIR>")
        sys.exit(1)

    base_dir_arg = sys.argv[1]
    process_folders(base_dir_arg)
