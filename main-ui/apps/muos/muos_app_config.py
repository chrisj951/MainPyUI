import os

from apps.app_config import AppConfig

class MuosAppConfig(AppConfig):
    def __init__(self, folder_path):       
        self.folder = folder_path
        folder_name = os.path.basename(folder_path) 
        self.label = folder_name
        self.icontop = None
        self.icon = None
        self.launch = os.path.join(self.folder,"mux_launch.sh")

        self.description = folder_path

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
