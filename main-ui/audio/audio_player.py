import sdl2
import sdl2.sdlmixer as sdlmixer
import threading
import sys
import time
from utils.logger import PyUiLogger

class AudioPlayer:
    _initialized = False
    _loop_thread = None
    _stop_loop = False
    _current_volume = 128  # max volume by default

    @staticmethod
    def _init():
        if not AudioPlayer._initialized:
            sdl2.SDL_Init(sdl2.SDL_INIT_AUDIO)
            if sdlmixer.Mix_OpenAudio(44100, sdlmixer.MIX_DEFAULT_FORMAT, 2, 1024) != 0:
                PyUiLogger.get_logger().warning(
                    f"Failed to initialize audio: SDL_mixer error: {sdlmixer.Mix_GetError().decode()}"
                )
            AudioPlayer._initialized = True

    @staticmethod
    def set_volume(volume: int):
        """
        Sets the playback volume in real-time.
        volume: 0 (silent) to 10 (max)
        """
        #SDL maxes at 128, so scale 0-10 based on that
        AudioPlayer._current_volume = max(0, min(128, int(volume*12.8)))
        # Apply volume to all channels (-1)
        sdlmixer.Mix_Volume(-1, AudioPlayer._current_volume)

    @staticmethod
    def play_wav(file_path: str):
        """Plays the WAV file once (blocking)."""
        PyUiLogger.get_logger().info(f"Playing {file_path}")
        AudioPlayer._init()
        sound = sdlmixer.Mix_LoadWAV(file_path.encode())
        if not sound:
            PyUiLogger.get_logger().warning(
                f"Failed to load WAV: {file_path}, SDL_mixer error: {sdlmixer.Mix_GetError().decode()}"
            )
            return

        # Apply current volume to this chunk
        sdlmixer.Mix_VolumeChunk(sound, AudioPlayer._current_volume)

        channel = sdlmixer.Mix_PlayChannel(-1, sound, 0)
        if channel == -1:
            PyUiLogger.get_logger().warning(
                f"Failed to play WAV: {file_path}, SDL_mixer error: {sdlmixer.Mix_GetError().decode()}"
            )
            sdlmixer.Mix_FreeChunk(sound)
            return

        while sdlmixer.Mix_Playing(channel) != 0:
            sdl2.SDL_Delay(50)

        sdlmixer.Mix_FreeChunk(sound)

    @staticmethod
    def loop_wav(file_path: str):
        PyUiLogger.get_logger().info(f"Looping {file_path}")

        def loop():
            sound = sdlmixer.Mix_LoadWAV(file_path.encode())
            if not sound:
                PyUiLogger.get_logger().warning(
                    f"Failed to load WAV: {file_path}, SDL_mixer error: {sdlmixer.Mix_GetError().decode()}"
                )
                return

            # Apply current volume to this chunk
            sdlmixer.Mix_VolumeChunk(sound, AudioPlayer._current_volume)

            channel = sdlmixer.Mix_PlayChannel(-1, sound, -1)  # -1 = loop forever
            if channel == -1:
                PyUiLogger.get_logger().warning(
                    f"Failed to play WAV: {file_path}, SDL_mixer error: {sdlmixer.Mix_GetError().decode()}"
                )
                sdlmixer.Mix_FreeChunk(sound)
                return

            while not AudioPlayer._stop_loop:
                sdl2.SDL_Delay(50)

            sdlmixer.Mix_HaltChannel(channel)
            sdlmixer.Mix_FreeChunk(sound)

        AudioPlayer._init()
        AudioPlayer._stop_loop = False
        AudioPlayer._loop_thread = threading.Thread(target=loop, daemon=True)
        AudioPlayer._loop_thread.start()

    @staticmethod
    def stop_loop():
        """Stops the looping WAV playback."""
        AudioPlayer._stop_loop = True
        if AudioPlayer._loop_thread:
            AudioPlayer._loop_thread.join()
            AudioPlayer._loop_thread = None

    @staticmethod
    def cleanup():
        AudioPlayer.stop_loop()
        if AudioPlayer._initialized:
            sdlmixer.Mix_CloseAudio()
            sdl2.SDL_Quit()
            AudioPlayer._initialized = False
