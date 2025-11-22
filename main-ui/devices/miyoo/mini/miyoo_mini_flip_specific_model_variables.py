

from pathlib import Path


class MiyooMiniSpecificModelVariables():

    def __init__(self, width, height, supports_wifi, poweroff_cmd, reboot_cmd):
        self.width = width
        self.height = height
        self.supports_wifi = supports_wifi
        self.poweroff_cmd = poweroff_cmd
        self.reboot_cmd = reboot_cmd

# --- Constant model presets ---

MIYOO_MINI_V1_V2_V3_VARIABLES = MiyooMiniSpecificModelVariables(
    width=640,
    height=480,
    supports_wifi=False,
    poweroff_cmd="reboot",
    reboot_cmd=None
)

MIYOO_MINI_V4_VARIABLES = MiyooMiniSpecificModelVariables(
    width=750,
    height=560,
    supports_wifi=False,
    poweroff_cmd="reboot",
    reboot_cmd=None
)

MIYOO_MINI_PLUS = MiyooMiniSpecificModelVariables(
    width=640,
    height=480,
    supports_wifi=True,
    poweroff_cmd="reboot",
    reboot_cmd=None
)

MIYOO_MINI_FLIP_VARIABLES = MiyooMiniSpecificModelVariables(
    width=750,
    height=560,
    supports_wifi=True,
    poweroff_cmd="poweroff",
    reboot_cmd="reboot"
)
