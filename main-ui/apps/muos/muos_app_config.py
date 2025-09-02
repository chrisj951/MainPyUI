import os

from apps.app_config import AppConfig

class MuosAppConfig(AppConfig):
    def __init__(self, folder_path):       
        self.folder = folder_path
        folder_name = os.path.basename(folder_path) 
        self.label = folder_name
        self.icontop = None
        self.launch = os.path.join(self.folder,"mux_launch.sh")
        self.description = folder_path
        self.icon = self._get_icon_from_launch()

    def _get_icon_from_launch(self):
        glyph_base = "/opt/muos/default/MUOS/theme/active/glyph/muxapp"
        if not os.path.isfile(self.launch):
            return None

        try:
            with open(self.launch, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# ICON:"):
                        icon_value = line.split(":", 1)[1].strip()
                        return os.path.join(glyph_base, icon_value + ".png")
        except Exception as e:
            print(f"Error reading {self.launch}: {e}")

        return None
    def get_label(self):
        return self.label

    def get_icontop(self):
        return self.icontop

    def get_icon(self):
        return self.icon

    def get_launch(self):
        return self.launch

    def get_description(self):
        return self.description
    
    def get_folder(self):
        return self.folder
