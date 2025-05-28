import array
import ctypes
import fcntl
import math
from pathlib import Path
import re
import socket
import subprocess
import threading
import time
from apps.miyoo.miyoo_app_finder import MiyooAppFinder
from controller.controller_inputs import ControllerInput
from controller.key_watcher import KeyWatcher
from devices.charge.charge_status import ChargeStatus
from devices.abstract_device import AbstractDevice
from devices.bluetooth.bluetooth_scanner import BluetoothScanner
import os
from devices.device_common import DeviceCommon
from devices.miyoo.miyoo_games_file_parser import MiyooGamesFileParser
from devices.miyoo.system_config import SystemConfig
from devices.miyoo_trim_common import MiyooTrimCommon
from devices.trimui.trim_ui_device import TrimUIDevice
from devices.utils.process_runner import ProcessRunner
from devices.wifi.wifi_connection_quality_info import WiFiConnectionQualityInfo
from devices.wifi.wifi_status import WifiStatus
from display.font_purpose import FontPurpose
from games.utils.game_entry import GameEntry
from games.utils.rom_utils import RomUtils
from menus.games.utils.recents_manager import RecentsManager
import sdl2
from utils import throttle
from utils.logger import PyUiLogger
import psutil

from utils.py_ui_config import PyUiConfig

class TrimUISmartPro(TrimUIDevice):
    
    def __init__(self):
        self.path = self
        self.sdl_button_to_input = {
            sdl2.SDL_CONTROLLER_BUTTON_A: ControllerInput.B,
            sdl2.SDL_CONTROLLER_BUTTON_B: ControllerInput.A,
            sdl2.SDL_CONTROLLER_BUTTON_X: ControllerInput.Y,
            sdl2.SDL_CONTROLLER_BUTTON_Y: ControllerInput.X,
            sdl2.SDL_CONTROLLER_BUTTON_GUIDE: ControllerInput.MENU,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: ControllerInput.DPAD_UP,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: ControllerInput.DPAD_DOWN,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: ControllerInput.DPAD_LEFT,
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: ControllerInput.DPAD_RIGHT,
            sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: ControllerInput.L1,
            sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: ControllerInput.R1,
            sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: ControllerInput.L3,
            sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: ControllerInput.R3,
            sdl2.SDL_CONTROLLER_BUTTON_START: ControllerInput.START,
            sdl2.SDL_CONTROLLER_BUTTON_BACK: ControllerInput.SELECT,
        }

        #Idea is if something were to change from he we can reload it
        #so it always has the more accurate data
        self.system_config = SystemConfig("/mnt/UDISK/system.json")


        self.miyoo_games_file_parser = MiyooGamesFileParser()        
        self._set_lumination_to_config()
        self._set_contrast_to_config()
        self._set_saturation_to_config()
        self._set_brightness_to_config()
        self.ensure_wpa_supplicant_conf()
        threading.Thread(target=self.monitor_wifi, daemon=True).start()
        if(PyUiConfig.enable_button_watchers()):
            from controller.controller import Controller
            #/dev/miyooio if we want to get rid of miyoo_inputd
            # debug in terminal: hexdump  /dev/miyooio
            self.volume_key_watcher = KeyWatcher("/dev/input/event3")
            Controller.add_button_watcher(self.volume_key_watcher.poll_keyboard)
            volume_key_polling_thread = threading.Thread(target=self.volume_key_watcher.poll_keyboard, daemon=True)
            volume_key_polling_thread.start()
            self.power_key_watcher = KeyWatcher("/dev/input/event1")
            power_key_polling_thread = threading.Thread(target=self.power_key_watcher.poll_keyboard, daemon=True)
            power_key_polling_thread.start()
            
    #Untested
    @throttle.limit_refresh(5)
    def is_hdmi_connected(self):
        return False

    def should_scale_screen(self):
        return self.is_hdmi_connected()

    @property
    def screen_width(self):
        return 1280

    @property
    def screen_height(self):
        return 720
    
    @property
    def output_screen_width(self):
        return 1920

    @property
    def output_screen_height(self):
        return 1080

    def get_scale_factor(self):
        if(self.is_hdmi_connected()):
            return 1.5
        else:
            return 1
    
    
    def disable_bluetooth(self):
        ProcessRunner.run(["killall","-15","bluetoothd"])
        time.sleep(0.1)  
        ProcessRunner.run(["killall","-9","bluetoothd"])

    def enable_bluetooth(self):
        if(not MiyooTrimCommon.is_bluetooth_enabled()):
            subprocess.Popen(['./bluetoothd',"-f","/etc/bluetooth/main.conf"],
                            cwd='/usr/libexec/bluetooth/',
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)

    def get_bluetooth_scanner(self):
        return BluetoothScanner()

    def supports_analog_calibration(self):
        return True

    def calibrate_sticks(self):
        from controller.controller import Controller
        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER)
        ProcessRunner.run(["killall","-9","trimui_inputd"])
        time.sleep(0.5)
        joystick = TrimUIJoystick()
        joystick.open()
        MiyooTrimCommon.run_analog_stick_calibration(self,"Left stick",joystick,"/mnt/UDISK/joypad.config","L")
        MiyooTrimCommon.run_analog_stick_calibration(self,"Right stick",joystick,"/mnt/UDISK/joypad_right.config","R")
        subprocess.Popen(["/usr/trimui/bin/trimui_inputd"],
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        Controller.re_init_controller()