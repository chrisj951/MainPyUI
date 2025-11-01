

import os
import threading
import time
from controller.controller import Controller
from controller.controller_inputs import ControllerInput
from devices.device import Device
from display.display import Display
from utils.logger import PyUiLogger


class BoxArtResizer():
    _last_display_time = 0  # class-level timestamp
    _aborted = False
    _monitoring = False
    _to_delete = []
    @classmethod
    def patch_boxart(cls):
        cls.process_rom_folders()


    @classmethod
    def monitor_for_input(cls):
        while(cls._monitoring):
            if(Controller.get_input() and Controller.last_input() == ControllerInput.B):
                cls._monitoring = False
                cls._aborted = True


    @classmethod
    def process_rom_folders(cls):
        """Search through ROM directories and scale images inside Imgs folders."""
        rom_paths = ["/mnt/SDCARD/Roms/", "/media/sdcard1/Roms/"]
        target_medium_width, target_medium_height = Device.get_boxart_medium_resize_dimensions()
        target_small_width, target_small_height = Device.get_boxart_small_resize_dimensions()
        target_large_width, target_large_height = Device.get_boxart_large_resize_dimensions()
        cls._aborted = False
        cls._monitoring = True

        threading.Thread(target=cls.monitor_for_input, daemon=True).start()

        for base_path in rom_paths:
            if not os.path.exists(base_path):
                continue

            scan_count = 0
            patched_count = 0
            for folder_name in os.listdir(base_path):
                folder_path = os.path.join(base_path, folder_name)
                if not os.path.isdir(folder_path):
                    continue

                imgs_path = os.path.join(folder_path, "Imgs")
                if not os.path.exists(imgs_path):
                    continue
                os.makedirs(os.path.join(folder_path, "Imgs_small"), exist_ok=True)
                os.makedirs(os.path.join(folder_path, "Imgs_med"), exist_ok=True)
                os.makedirs(os.path.join(folder_path, "Imgs_large"), exist_ok=True)

                for root, _, files in os.walk(imgs_path):
                    for file in files:
                        if file.lower().endswith((".png", ".jpg", ".jpeg")):
                            scan_count = scan_count + 1
                            cls._to_delete = []
                            if(cls._aborted):
                                Display.display_message(f"Aborting boxart patching", 2000)
                                cls._monitoring = False
                                return


                            full_path = os.path.join(root, file)
                            tga_path = os.path.splitext(full_path)[0] + ".tga"
                            if os.path.exists(tga_path):
                                continue


                            now = time.time()
                            if now - cls._last_display_time >= 1.0:
                                Display.display_message_multiline([f"Optimizing boxart {os.path.basename(file)}", f"Scanned {scan_count}, Patched {patched_count}","","Press B to Abort"])
                                cls._last_display_time = now
                                
                            try:
                                Device.get_image_utils().convert_from_png_to_tga(full_path)
                            except Exception as e:
                                PyUiLogger().get_logger().warning(f"Unable to convert {full_path} : {e}")
                                continue

                            try:
                                # Replace 'Imgs' with 'Imgs_large' in the path
                                large_image_path = full_path.replace(
                                    os.path.join(folder_path, "Imgs"),
                                    os.path.join(folder_path, "Imgs_large"),
                                )
                                if(not cls.scale_image(full_path,large_image_path, target_large_width, target_large_height)):
                                    large_image_path = full_path
                            except Exception as e:
                                print(f"Error converting for large image {full_path} : {e}")
                                continue


                            try:
                                # Replace 'Imgs' with 'Imgs_med' in the path
                                medium_image_path = full_path.replace(
                                    os.path.join(folder_path, "Imgs"),
                                    os.path.join(folder_path, "Imgs_med"),
                                )
                                if(not cls.scale_image(large_image_path,medium_image_path, target_medium_width, target_medium_height)):
                                    medium_image_path = full_path
                            except Exception as e:
                                print(f"Error converting for medium image {full_path} : {e}")
                                continue

                            try:
                                # Replace 'Imgs' with 'Imgs_small' in the path
                                small_image_path = full_path.replace(
                                    os.path.join(folder_path, "Imgs"),
                                    os.path.join(folder_path, "Imgs_small"),
                                )
                                cls.scale_image(medium_image_path,small_image_path, target_small_width, target_small_height)
                            except Exception as e:
                                print(f"Error converting for small image {full_path} : {e}")
                                continue

                            for output_path in cls._to_delete:
                                try:
                                    os.remove(output_path)
                                except Exception as e:
                                    print(f"Error deleting {output_path}")

                            patched_count = patched_count + 1

        cls._monitoring = False
        Display.display_message(f"All boxart is optimized", 2000)


    @classmethod
    def scale_image(cls, image_file, output_path, target_width, target_height):
        """Open an image and shrink it (preserving aspect ratio) to fit within target size."""

        # Early return if the TGA version already exists
        tga_path = os.path.splitext(output_path)[0] + ".tga"
        if os.path.exists(tga_path):
            return True
        

        needed_shrink = Device.get_image_utils().shrink_image_if_needed(image_file,output_path,target_width, target_height)
        if(needed_shrink):
            try:
                Device.get_image_utils().convert_from_png_to_tga(output_path)
                #cls._to_delete.append(output_path)
                return needed_shrink
            except Exception as e:
                PyUiLogger().get_logger().warning(f"Unable to convert {output_path} : {e}")

        return needed_shrink