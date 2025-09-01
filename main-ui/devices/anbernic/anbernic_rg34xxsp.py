from pathlib import Path
import subprocess
import threading
from controller.controller_inputs import ControllerInput
from controller.key_watcher import KeyWatcher
import os
from devices.anbernic.anbernic_device import AnbernicDevice
from devices.miyoo.flip.miyoo_flip_poller import MiyooFlipPoller
from devices.miyoo.miyoo_games_file_parser import MiyooGamesFileParser
from devices.miyoo.system_config import SystemConfig
from devices.utils.process_runner import ProcessRunner
import sdl2
from utils import throttle
from utils.config_copier import ConfigCopier
from utils.logger import PyUiLogger
from utils.py_ui_config import PyUiConfig

class AnbernicRG34XXSP(AnbernicDevice):
    OUTPUT_MIXER = 2
    SOUND_DISABLED = 0

    def __init__(self):
        PyUiLogger.get_logger().info("Initializing RG34XXSP")        
        
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
        
        #os.environ["SDL_VIDEODRIVER"] = "KMSDRM"
        #os.environ["SDL_RENDER_DRIVER"] = "kmsdrm"
        
        script_dir = Path(__file__).resolve().parent
        source = script_dir / 'rg34xxsp-system.json'
        ConfigCopier.ensure_config("/mnt/sdcard/Saves/rg34xxsp-system.json", source)
        self.system_config = SystemConfig("/mnt/sdcard/Saves/rg34xxsp-system.json")
        self.miyoo_games_file_parser = MiyooGamesFileParser()        
        self._set_lumination_to_config()
        self._set_contrast_to_config()
        self._set_saturation_to_config()
        self._set_brightness_to_config()
        self._set_hue_to_config()
        threading.Thread(target=self.monitor_wifi, daemon=True).start()
        self.hardware_poller = MiyooFlipPoller(self)
        threading.Thread(target=self.hardware_poller.continuously_monitor, daemon=True).start()

        if(PyUiConfig.enable_button_watchers()):
            from controller.controller import Controller
            #/dev/miyooio if we want to get rid of miyoo_inputd
            # debug in terminal: hexdump  /dev/miyooio
            self.volume_key_watcher = KeyWatcher("/dev/input/event0")
            Controller.add_button_watcher(self.volume_key_watcher.poll_keyboard)
            volume_key_polling_thread = threading.Thread(target=self.volume_key_watcher.poll_keyboard, daemon=True)
            volume_key_polling_thread.start()
            self.power_key_watcher = KeyWatcher("/dev/input/event2")
            power_key_polling_thread = threading.Thread(target=self.power_key_watcher.poll_keyboard, daemon=True)
            power_key_polling_thread.start()
            self.controller_watcher = KeyWatcher("/dev/input/event1", ev_keys={0x01, 0x03})
            Controller.add_button_watcher(self.controller_watcher.poll_keyboard)
            controller_watching_thread = threading.Thread(target=self.controller_watcher.poll_keyboard, daemon=True)
            controller_watching_thread.start()

        self.unknown_axis_ranges = {}  # axis -> (min, max)
        self.unknown_axis_stats = {}   # axis -> (sum, count)
        self.sdl_axis_names = {
            0: "SDL_CONTROLLER_AXIS_LEFTX",
            1: "SDL_CONTROLLER_AXIS_LEFTY",
            2: "SDL_CONTROLLER_AXIS_RIGHTX",
            3: "SDL_CONTROLLER_AXIS_RIGHTY",
            4: "SDL_CONTROLLER_AXIS_TRIGGERLEFT",
            5: "SDL_CONTROLLER_AXIS_TRIGGERRIGHT"
        }

        self.init_bluetooth()
        config_volume = self.system_config.get_volume()
        self._set_volume(config_volume)
        super().__init__()

    def init_bluetooth(self):
        pass


    def are_headphones_plugged_in(self):
        try:
            with open("/sys/class/gpio/gpio150/value", "r") as f:
                value = f.read().strip()
                return "0" == value 
        except (FileNotFoundError, IOError) as e:
            return False
        
    def is_lid_closed(self):
        try:
            with open("/sys/devices/platform/hall-mh248/hallvalue", "r") as f:
                value = f.read().strip()
                return "0" == value 
        except (FileNotFoundError, IOError) as e:
            return False

    @throttle.limit_refresh(5)
    def is_hdmi_connected(self):
        return False

    @property
    def screen_width(self):
        return 720

    @property
    def screen_height(self):
        return 480
    
    
    @property
    def output_screen_width(self):
        if(self.should_scale_screen()):
            return 1920
        else:
            return 720
        
    @property
    def output_screen_height(self):
        if(self.should_scale_screen()):
            return 1080
        else:
            return 480

    def get_scale_factor(self):
        if(self.is_hdmi_connected()):
            return 2.25
        else:
            return 1
    
    def _set_lumination_to_config(self):
        pass
    
    def _set_contrast_to_config(self):
        pass
    
    def _set_saturation_to_config(self):
        pass

    def _set_brightness_to_config(self):
        pass

    def _set_hue_to_config(self):
        pass
