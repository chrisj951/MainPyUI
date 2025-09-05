#!/bin/sh

# Goes in /mnt/mmc/MUOS/application/PyUI

. /opt/muos/script/var/func.sh

echo app >/tmp/act_go

cat "performance" >"$(GET_VAR "device" "cpu/governor")"

SETUP_SDL_ENVIRONMENT


killall -9 hotkey.sh
killall -9 muhotkey

python /mnt/sdcard/pyui/main-ui/mainui.py -device ANBERNIC_RG28XX -logDir /mnt/sdcard/pyui/logs

/opt/muos/script/mux/hotkey.sh &
/opt/muos/frontend/muhotkey /opt/muos/device/control/hotkey.json &


unset SDL_ASSERT SDL_HQ_SCALER SDL_ROTATION SDL_BLITTER_DISABLED