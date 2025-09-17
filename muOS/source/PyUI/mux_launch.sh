#!/bin/sh

# Goes in /mnt/mmc/MUOS/application/PyUI
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

. /opt/muos/script/var/func.sh

cat "performance" >"$(GET_VAR "device" "cpu/governor")"

SETUP_SDL_ENVIRONMENT


killall -9 hotkey.sh
killall -9 muhotkey


cd "${SCRIPT_DIR}/setup"
./install.sh 2>&1 | tee /mnt/mmc/MUOS/log/pyui/setup.log

cd "${SCRIPT_DIR}"

python "${SCRIPT_DIR}/main-ui/mainui.py" -device ANBERNIC_MUOS -pyUiConfig "${SCRIPT_DIR}/py-ui-config.json" -logDir /mnt/mmc/MUOS/log/pyui/

/opt/muos/script/mux/hotkey.sh &
/opt/muos/frontend/muhotkey /opt/muos/device/control/hotkey.json &


unset SDL_ASSERT SDL_HQ_SCALER SDL_ROTATION SDL_BLITTER_DISABLED