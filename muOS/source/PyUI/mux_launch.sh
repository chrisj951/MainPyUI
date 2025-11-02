#!/bin/sh



update_theme_dir() {
    # 1. Get the directory this script resides in
    SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

    # 2. Define the config file path
    CONFIG_FILE="$SCRIPT_DIR/py-ui-config.json"

    # 3. Check if file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: py-ui-config.json not found in $SCRIPT_DIR"
        return 1
    fi

    # 4. Compute the theme directory path
    THEME_DIR="${SCRIPT_DIR}/Themes/"

    # 5. Update the "themeDir" key using jq
    tmpfile=$(mktemp)
    if jq --arg dir "$THEME_DIR" '.themeDir = $dir' "$CONFIG_FILE" > "$tmpfile"; then
        mv "$tmpfile" "$CONFIG_FILE"
        echo "Updated themeDir in $CONFIG_FILE to $THEME_DIR"
        return 0
    else
        echo "Failed to update themeDir in $CONFIG_FILE"
        rm -f "$tmpfile"
        return 1
    fi
}

update_theme_dir 

# Goes in /mnt/mmc/MUOS/application/PyUI
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

. /opt/muos/script/var/func.sh

cat "performance" >"$(GET_VAR "device" "cpu/governor")"

SETUP_SDL_ENVIRONMENT


killall -9 hotkey.sh
killall -9 muhotkey


mkdir -p /mnt/mmc/MUOS/log/pyui/

cd "${SCRIPT_DIR}/setup"
./install.sh 2>&1 | tee /mnt/mmc/MUOS/log/pyui/setup.log

cd "${SCRIPT_DIR}"

python "${SCRIPT_DIR}/main-ui/mainui.py" -device ANBERNIC_MUOS -pyUiConfig "${SCRIPT_DIR}/py-ui-config.json" -logDir /mnt/mmc/MUOS/log/pyui/

/opt/muos/script/mux/hotkey.sh &
/opt/muos/frontend/muhotkey /opt/muos/device/control/hotkey.json &


unset SDL_ASSERT SDL_HQ_SCALER SDL_ROTATION SDL_BLITTER_DISABLED