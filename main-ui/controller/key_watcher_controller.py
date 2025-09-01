

from dataclasses import dataclass
import os
import struct
import select
import time

from controller.controller_inputs import ControllerInput
from controller.controller_interface import ControllerInterface
from controller.key_state import KeyState

# Constants for Linux input
EVENT_FORMAT = 'llHHI'
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)
KEY_PRESS = 1
KEY_RELEASE = 0
KEY_REPEAT = 2


@dataclass
class InputResult:
    controller_input: ControllerInput
    key_state: KeyState

@dataclass(frozen=True)
class KeyEvent:
    event_type: int
    code: int
    value: int

    
class KeyWatcherController(ControllerInterface):

    def __init__(self, event_path, key_mappings):
        """
        :param event_path: Path to /dev/input/eventX
        :param repeat_interval: Time between repeats (seconds)
        """
        self.event_path = event_path
        self.key_mappings = key_mappings
        self.held_keys = {}  # Maps keycode -> last seen time
        self.held_inputs = {}  # Maps input -> last seen time

        try:
            self.fd = os.open(self.event_path, os.O_RDONLY | os.O_NONBLOCK)
        except OSError as e:
            print(f"Error opening {self.event_path}: {e}")
            self.fd = None
        
        self.last_held_input = None


    def still_held_down(self):
        if(self.last_held_input):
            return False
        elif(self.last_held_input in self.held_inputs):
            return True

    def last_input(self):
        return self.last_held_input

    def clear_input(self):
        count = 0
        while(count < 50 and self.get_input(0.01) != (None, None)):
            count += 1

    def cache_last_event(self):
        self.cached_input = self.last_held_input
        self.clear_input()

    def restore_cached_event(self):
        self.last_held_input = self.cached_input



    def get_input(self, timeout):
        """
        Polls for a single key event or simulates a repeat if a key is held.

        Returns:
            tuple: (keycode, is_down)
        """
        now = time.time()


        try:
            rlist, _, _ = select.select([self.fd], [], [], timeout)
            if rlist:
                data = os.read(self.fd, EVENT_SIZE)

                if len(data) == EVENT_SIZE:
                    _, _, event_type, code, value = struct.unpack(EVENT_FORMAT, data)
                    key_event = KeyEvent(event_type, code, value)
                    #print(f"event_type: {event_type}, code: {code}, value: {value}")
                    if key_event in self.key_mappings:
                        mapped_events = self.key_mappings[key_event]
                        for mapped_event in mapped_events:
                            if mapped_event.key_state == KeyState.PRESS:
                                self.held_keys[mapped_event.controller_input] = now
                                return mapped_event.controller_input
                            elif mapped_event.key_state == KeyState.RELEASE:
                                self.held_keys.pop(mapped_event.controller_input, None)

        except Exception as e:
            print(f"Error reading input: {e}")

        # Simulate repeat for held keys
        for controller_input, last_time in list(self.held_keys.items()):
            self.held_keys[controller_input] = now
            return controller_input
    
        return (None, None)

    def clear_input_queue(self):
        pass

    def init_controller(self):
        pass
    
    def re_init_controller(self):
        pass
    
    def close(self):
        pass

    def force_refresh(self):
        pass