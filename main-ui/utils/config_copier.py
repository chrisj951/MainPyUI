from pathlib import Path
import shutil

class ConfigCopier:

    @classmethod
    def ensure_config(cls, file_path, default_config_file):
        """
        Ensures that a config file exists at the given file_path.
        If it does not, copies 'config.json' from the script's directory to that location.
        """
        dest = Path(file_path)

        # Only copy if the file is missing or empty
        if dest.exists() and dest.stat().st_size > 0:
            return # Do nothing.

        if not default_config_file.exists():
            raise FileNotFoundError(f"Source config file not found: {default_config_file}")

        # Create parent directories if necessary
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Copy the file
        shutil.copy2(default_config_file, dest)