import re
import subprocess
import time
from apps.miyoo.miyoo_app_finder import MiyooAppFinder
from controller.controller_inputs import ControllerInput
from devices.bluetooth.bluetooth_scanner import BluetoothScanner
from devices.charge.charge_status import ChargeStatus
import os
from devices.device_common import DeviceCommon
from devices.miyoo.trim_ui_joystick import TrimUIJoystick
from devices.miyoo_trim_common import MiyooTrimCommon
from devices.utils.process_runner import ProcessRunner
from devices.wifi.wifi_connection_quality_info import WiFiConnectionQualityInfo
from games.utils.game_entry import GameEntry
from menus.games.utils.rom_info import RomInfo
from menus.settings.button_remapper import ButtonRemapper
import sdl2
from utils import throttle
from utils.logger import PyUiLogger

from devices.device_common import DeviceCommon


class AnbernicDevice(DeviceCommon):
    OUTPUT_MIXER = 2
    SOUND_DISABLED = 0

    def __init__(self):
        self.button_remapper = ButtonRemapper(self.system_config)

    def sleep(self):
        with open("/sys/power/mem_sleep", "w") as f:
            f.write("deep")
        with open("/sys/power/state", "w") as f:
            f.write("mem")  

    def ensure_wpa_supplicant_conf(self):
        pass

    def should_scale_screen(self):
        return self.is_hdmi_connected()

    @property
    def power_off_cmd(self):
        return "poweroff"
    
    @property
    def reboot_cmd(self):
        return "reboot"

    def _set_volume(self, volume):
        return volume 


    def get_current_mixer_value(self, numid):
        return None

    def get_volume(self):
        return self.system_config.get_volume()

    def read_volume(self):
         return 0 

    def run_game(self, rom_info: RomInfo) -> subprocess.Popen:
        return MiyooTrimCommon.run_game(self,rom_info)

    def run_app(self, args, dir = None):
        MiyooTrimCommon.run_app(self, args, dir)

    #TODO untested
    def map_analog_axis(self,sdl_input, value, threshold=16000):
        if sdl_input == sdl2.SDL_CONTROLLER_AXIS_LEFTX:
            if value < -threshold:
                return ControllerInput.LEFT_STICK_LEFT
            elif value > threshold:
                return ControllerInput.LEFT_STICK_RIGHT
        elif sdl_input == sdl2.SDL_CONTROLLER_AXIS_LEFTY:
            if value < -threshold:
                return ControllerInput.LEFT_STICK_UP
            elif value > threshold:
                return ControllerInput.LEFT_STICK_DOWN
        elif sdl_input == sdl2.SDL_CONTROLLER_AXIS_RIGHTX:
            if value < -threshold:
                return ControllerInput.RIGHT_STICK_LEFT
            elif value > threshold:
                return ControllerInput.RIGHT_STICK_RIGHT
        elif sdl_input == sdl2.SDL_CONTROLLER_AXIS_RIGHTY:
            if value < -threshold:
                return ControllerInput.RIGHT_STICK_UP
            elif value > threshold:
                return ControllerInput.RIGHT_STICK_DOWN
        return None
    
    def map_digital_input(self, sdl_input):
        mapping = self.sdl_button_to_input.get(sdl_input, ControllerInput.UNKNOWN)
        if(ControllerInput.UNKNOWN == mapping):
            PyUiLogger.get_logger().error(f"Unknown input {sdl_input}")
        return self.button_remapper.get_mappping(mapping)

    def map_analog_input(self, sdl_axis, sdl_value):
        if sdl_axis == 5 and sdl_value == 32767:
            return self.button_remapper.get_mappping(ControllerInput.R2)
        elif sdl_axis == 4 and sdl_value == 32767:
            return self.button_remapper.get_mappping(ControllerInput.L2)
        else:
            # Update min/max range
            if sdl_axis not in self.unknown_axis_ranges:
                self.unknown_axis_ranges[sdl_axis] = (sdl_value, sdl_value)
            else:
                current_min, current_max = self.unknown_axis_ranges[sdl_axis]
                self.unknown_axis_ranges[sdl_axis] = (
                    min(current_min, sdl_value),
                    max(current_max, sdl_value)
                )

            # Update sum/count for average
            if sdl_axis not in self.unknown_axis_stats:
                self.unknown_axis_stats[sdl_axis] = (sdl_value, 1)
            else:
                total, count = self.unknown_axis_stats[sdl_axis]
                self.unknown_axis_stats[sdl_axis] = (total + sdl_value, count + 1)

            min_val, max_val = self.unknown_axis_ranges[sdl_axis]
            total, count = self.unknown_axis_stats[sdl_axis]
            avg_val = total / count if count > 0 else 0

            axis_name = self.sdl_axis_names.get(sdl_axis, "UNKNOWN_AXIS")
            #PyUiLogger.get_logger().error(
            #    f"Received unknown analog input axis = {sdl_axis} ({axis_name}), value = {sdl_value} "
            #    f"(range: min = {min_val}, max = {max_val}, avg = {avg_val:.2f})"
            #)
            return None

    def prompt_power_down(self):
        DeviceCommon.prompt_power_down(self)

    def special_input(self, controller_input, length_in_seconds):
        if(ControllerInput.POWER_BUTTON == controller_input):
            if(length_in_seconds < 1):
                self.sleep()
            else:
                self.prompt_power_down()
        elif(ControllerInput.VOLUME_UP == controller_input):
            self.change_volume(5)
        elif(ControllerInput.VOLUME_DOWN == controller_input):
            self.change_volume(-5)

    def map_key(self, key_code):
        if(304 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.A)
        elif(305 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.B)
        elif(306 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.Y)
        elif(307 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.X)
        elif(308 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.L1)
        elif(309 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.R1)
        elif(310 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.SELECT)
        elif(311 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.START)
        elif(312 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.MENU)
        elif(313 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.L3)
        elif(314 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.L2)
        elif(315 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.R2)
        elif(316 == key_code):
            return self.button_remapper.get_mappping(ControllerInput.R3)
        else:
            PyUiLogger.get_logger().debug(f"Unrecognized keycode {key_code}")
            return None


    def get_wifi_connection_quality_info(self) -> WiFiConnectionQualityInfo:
        return WiFiConnectionQualityInfo(noise_level=0, signal_level=0, link_quality=0)


    def set_wifi_power(self, value):
        pass

    def stop_wifi_services(self):
        pass

    def start_wpa_supplicant(self):
        pass

    def is_wifi_enabled(self):
        return self.system_config.is_wifi_enabled()

    def disable_wifi(self):
        pass

    def enable_wifi(self):
        pass

    @throttle.limit_refresh(5)
    def get_charge_status(self):
        return ChargeStatus.DISCONNECTED
    
    @throttle.limit_refresh(15)
    def get_battery_percent(self):
        return 0
        
    def get_app_finder(self):
        return MiyooAppFinder()
    
    def parse_favorites(self) -> list[GameEntry]:
        return self.miyoo_games_file_parser.parse_favorites()
    
    def parse_recents(self) -> list[GameEntry]:
        return self.miyoo_games_file_parser.parse_recents()

    def is_bluetooth_enabled(self):
        return False
    
    def disable_bluetooth(self):
        pass

    def enable_bluetooth(self):
        pass
            
    def perform_startup_tasks(self):
        pass

    def get_bluetooth_scanner(self):
        return BluetoothScanner()

    def get_favorites_path(self):
        return "/mnt/sdcard/Saves/pyui-favorites.json"
    
    def get_recents_path(self):
        return "/mnt/sdcard/Saves/pyui-recents.json"
    
    def launch_stock_os_menu(self):
        self.run_app("/usr/miyoo/bin/runmiyoo-original.sh")

    def get_state_path(self):
        return "/mnt/sdcard/Saves/pyui-state.json"

    def calibrate_sticks(self):
        from controller.controller import Controller

    def supports_analog_calibration(self):
        return False
    
    def remap_buttons(self):
        self.button_remapper.remap_buttons()