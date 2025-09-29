from dataclasses import dataclass
from enum import Enum, auto
import mmap
import os
import time
from devices.device import Device
from display.font_purpose import FontPurpose
from display.loaded_font import LoadedFont
from display.render_mode import RenderMode
from display.resize_type import ResizeType
from display.x_render_option import XRenderOption
from display.y_render_option import YRenderOption
from menus.common.bottom_bar import BottomBar
from menus.common.top_bar import TopBar
import sdl2
import sdl2.ext
import sdl2.sdlttf
from themes.theme import Theme
from utils.logger import PyUiLogger
import ctypes
from ctypes import c_double

@dataclass
class CachedImageTexture:
    def __init__(self, surface, texture):
        self.surface = surface
        self.texture = texture

class ImageTextureCache:
    def __init__(self):
        self.cache = {} 

    def get_texture(self, texture_id) -> CachedImageTexture:
        return self.cache.get(texture_id)

    def add_texture(self, texture_id, surface, texture):
        self.cache[texture_id] = CachedImageTexture(surface,texture)
    
    def clear_cache(self):
        for entry in self.cache.values():
            sdl2.SDL_DestroyTexture(entry.texture)
            sdl2.SDL_FreeSurface(entry.surface)
        self.cache.clear()

@dataclass(frozen=True)
class TextTextureKey:
    texture_id : str
    font : object
    color : tuple

@dataclass
class CachedTextTexture:
    def __init__(self, surface, texture):
        self.surface = surface
        self.texture = texture

class TextTextureCache:
    def __init__(self):
        self.cache = {} 

    def get_texture(self, texture_id, font, color) -> CachedTextTexture:
        return self.cache.get(TextTextureKey(texture_id, font, color))

    def add_texture(self, texture_id, font, color, surface, texture):
        self.cache[TextTextureKey(texture_id, font, color)] = CachedTextTexture(surface,texture)
    
    def clear_cache(self):
        for entry in self.cache.values():
            sdl2.SDL_DestroyTexture(entry.texture)
            sdl2.SDL_FreeSurface(entry.surface)
        self.cache.clear()
        
class Display:
    debug = False
    renderer = None
    fonts = {}
    bg_canvas = None
    render_canvas = None
    bg_path = ""
    page_bg = ""
    top_bar = TopBar()
    bottom_bar = BottomBar()
    window = None
    background_surface = None
    top_bar_text = None
    _image_texture_cache = ImageTextureCache()
    _text_texture_cache = TextTextureCache()
    fb_fd = None
    fb_mem = None
    # Software surface to render into CPU memory
    render_surface = None

    @classmethod
    def init(cls):
        cls._init_display()
        #Outside init_fonts as it should only ever be called once
        if sdl2.sdlttf.TTF_Init() == -1:
            raise RuntimeError("Failed to initialize SDL_ttf")
        cls.init_fonts()
        cls.render_canvas = sdl2.SDL_CreateRGBSurfaceWithFormat(
            0,
            Device.screen_width(),
            Device.screen_height(),
            32,
            sdl2.SDL_PIXELFORMAT_ARGB8888
        )
        if not cls.render_canvas:
            raise RuntimeError(f"Failed to create render_canvas: {sdl2.SDL_GetError().decode()}")
        PyUiLogger.get_logger().info(f"sdl2.SDL_GetError() : {sdl2.SDL_GetError()}")
       # sdl2.SDL_SetRenderTarget(cls.renderer.renderer, cls.render_canvas)
        PyUiLogger.get_logger().info(f"sdl2.SDL_GetError() : {sdl2.SDL_GetError()}")
        sdl2.SDL_SetRenderDrawBlendMode(cls.renderer.renderer, sdl2.SDL_BLENDMODE_BLEND)
        PyUiLogger.get_logger().info(f"sdl2.SDL_GetError() : {sdl2.SDL_GetError()}")
        cls.setup_fb()

        cls.restore_bg()
        cls.clear("init")
        cls.present()

    @classmethod
    def init_fonts(cls):
        cls.fonts = {
            purpose: cls._load_font(purpose)
            for purpose in FontPurpose
        }


    @classmethod
    def _init_display(cls):
        sdl2.ext.init(controller=True)
        sdl2.SDL_InitSubSystem(sdl2.SDL_INIT_GAMECONTROLLER)

        display_mode = sdl2.SDL_DisplayMode()
        if sdl2.SDL_GetCurrentDisplayMode(0, display_mode) != 0:
            PyUiLogger.get_logger().error("Failed to get display mode, using fallback 640x480")
            width, height = Device.screen_width(), Device.screen_height()
        else:
            width, height = display_mode.w, display_mode.h
            PyUiLogger.get_logger().info(f"Display size: {width}x{height}")

        cls.window = sdl2.ext.Window("Minimal SDL2 GUI", size=(width, height), flags=sdl2.SDL_WINDOW_FULLSCREEN)
        cls.window.show()

        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"2")
        cls.renderer = sdl2.ext.Renderer(cls.window, flags=sdl2.SDL_RENDERER_SOFTWARE)

    @classmethod
    def deinit_display(cls):
        if cls.render_canvas:
            sdl2.SDL_DestroyTexture(cls.render_canvas)
            cls.render_canvas = None
        if cls.bg_canvas:
            sdl2.SDL_DestroyTexture(cls.bg_canvas)
            cls.bg_canvas = None
        if cls.renderer is not None:
            sdl2.SDL_DestroyRenderer(cls.renderer.sdlrenderer)
            cls.renderer = None
        if cls.window is not None:
            sdl2.SDL_DestroyWindow(cls.window.window)
            cls.window = None
        cls.deinit_fonts()
        cls._unload_bg_texture()
        cls._text_texture_cache.clear_cache()
        cls._image_texture_cache.clear_cache()
        sdl2.SDL_QuitSubSystem(sdl2.SDL_INIT_VIDEO)
        PyUiLogger.get_logger().debug("Display deinitialized")    

    @classmethod
    def clear_text_cache(cls):
        PyUiLogger.get_logger().debug("Clearing text cache")    
        cls._text_texture_cache.clear_cache()
        cls.deinit_fonts()
        cls.init_fonts()

    @classmethod
    def clear_image_cache(cls):
        PyUiLogger.get_logger().debug("Clearing image cache")    
        cls._image_texture_cache.clear_cache()

    @classmethod
    def clear_cache(cls):
        cls.clear_image_cache()
        cls.clear_text_cache()

    @classmethod
    def deinit_fonts(cls):
        for loaded_font in cls.fonts.values():
            sdl2.sdlttf.TTF_CloseFont(loaded_font.font)
        cls.fonts.clear()

    @classmethod
    def reinitialize(cls, bg=None):
        PyUiLogger.get_logger().info("reinitialize display")
        cls.deinit_display()
        cls._unload_bg_texture()
        cls._init_display()
        cls.init_fonts()
        cls.restore_bg(bg)
        cls.clear("reinitialize")
        cls.present()


    @classmethod
    def _unload_bg_surface(cls):
        """Free the current background surface."""
        if getattr(cls, "background_surface", None):
            sdl2.SDL_FreeSurface(cls.background_surface)
            cls.background_surface = None
            PyUiLogger.get_logger().debug("Destroyed background surface")

    @classmethod
    def restore_bg(cls, bg=None):
        """Restore a previous or default background."""
        if bg is not None:
            cls.set_new_bg(bg)
        else:
            cls.set_new_bg(Theme.background())

    @classmethod
    def set_new_bg(cls, bg_path):
        """Load a PNG background into a surface."""
        cls._unload_bg_surface()
        cls.bg_path = bg_path
        logger = PyUiLogger.get_logger()
        logger.info(f"Using {bg_path} as the background")

        if bg_path is None:
            return

        # Load PNG using SDL_image
        surface = sdl2.sdlimage.IMG_Load(bg_path.encode("utf-8"))
        if not surface:
            logger.error(f"Failed to load image: {bg_path}")
            return

        # Optional: convert surface to match render_surface pixel format
        if cls.render_surface:
            converted = sdl2.SDL_ConvertSurfaceFormat(surface, sdl2.SDL_PIXELFORMAT_ARGB8888, 0)
            sdl2.SDL_FreeSurface(surface)
            surface = converted
            if not surface:
                logger.error(f"Failed to convert background surface: {bg_path}")
                return

        cls.background_surface = surface

    @classmethod
    def set_page_bg(cls, page_bg):
        if(page_bg != cls.page_bg):
            cls.page_bg = page_bg 
            background = Theme.background(page_bg)
            if(os.path.exists(background)):
                cls.set_new_bg(background)
            else:
                PyUiLogger.get_logger().debug(f"Theme did not provide bg for {background}")

    @classmethod
    def set_selected_tab(cls, tab):
        cls.top_bar.set_selected_tab(tab)

    @classmethod
    def _load_font(cls, font_purpose):
        font_path = Theme.get_font(font_purpose)
        font_size = Theme.get_font_size(font_purpose)

        font = sdl2.sdlttf.TTF_OpenFont(font_path.encode("utf-8"), font_size)
        if not font:
            raise RuntimeError(
                f"Could not load font {font_path} : {sdl2.sdlttf.TTF_GetError().decode('utf-8')}"
            )

        line_height = sdl2.sdlttf.TTF_FontHeight(font)
        surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(font, "A".encode('utf-8'), sdl2.SDL_Color(0, 0, 0))
        if not surface:
            line_height = 0
        else:
            sdl2.SDL_FreeSurface(surface)

        return LoadedFont(font, line_height, font_path)

    @classmethod
    def lock_current_image(cls):
        if cls.bg_canvas:
            sdl2.SDL_DestroyTexture(cls.bg_canvas)
            cls.bg_canvas = None
    
        cls.bg_canvas = cls.render_canvas
        cls.render_canvas = sdl2.SDL_CreateTexture(
            cls.renderer.renderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_TARGET,
            Device.screen_width(),
            Device.screen_height()
        )
        sdl2.SDL_SetRenderTarget(cls.renderer.renderer, cls.render_canvas)
        sdl2.SDL_RenderCopy(cls.renderer.sdlrenderer, cls.bg_canvas, None, None)

    @classmethod
    def unlock_current_image(cls):
        if cls.bg_canvas:
            sdl2.SDL_DestroyTexture(cls.bg_canvas)
            cls.bg_canvas = None

    @classmethod
    def clear(
        cls,
        top_bar_text,
        hide_top_bar_icons=False,
        bottom_bar_text=None,
        render_bottom_bar_icons_and_images=True
    ):
        cls.top_bar_text = top_bar_text
        logger = PyUiLogger.get_logger()

        # Make sure the render_surface exists
        if cls.render_canvas is None:
            raise RuntimeError("Render surface not initialized; cannot clear")

        # Blit background
        if cls.background_surface is not None:
            ret = sdl2.SDL_BlitSurface(
                cls.background_surface,  # source surface
                None,                    # src rect = full surface
                cls.render_canvas,      # destination surface
                None                     # dst rect = upper-left
            )
            if ret != 0:
                raise RuntimeError(
                    f"SDL_BlitSurface failed for background_surface: {sdl2.SDL_GetError().decode()}"
                )
        else:
            # Clear to black if no background
            sdl2.SDL_FillRect(cls.render_canvas, None, 0x000000FF)

        # Render top/bottom bars if needed
        if not Theme.render_top_and_bottom_bar_last():
            cls.top_bar.render_top_bar(cls.top_bar_text, hide_top_bar_icons)
            cls.bottom_bar.render_bottom_bar(
                bottom_bar_text,
                render_bottom_bar_icons_and_images=render_bottom_bar_icons_and_images
            )

    @classmethod
    def _log(cls, msg):
        if cls.debug:
            PyUiLogger.get_logger().info(msg)

    @staticmethod
    def _calculate_scaled_width_and_height(orig_w, orig_h, target_width, target_height, resize_type):
        if resize_type == ResizeType.FIT:
            if target_width and target_height:
                scale = min(target_width / orig_w, target_height / orig_h)
            elif target_width:
                scale = target_width / orig_w
            elif target_height:
                scale = target_height / orig_h
            else:
                scale = 1.0
            render_w = int(orig_w * scale)
            render_h = int(orig_h * scale)

        elif resize_type == ResizeType.ZOOM:
            if target_width and target_height:
                scale = max(target_width / orig_w, target_height / orig_h)
                render_w = int(orig_w * scale)
                render_h = int(orig_h * scale)
            else:
                render_w = orig_w
                render_h = orig_h
        else:
            render_w = orig_w
            render_h = orig_h

        return render_w, render_h


    @classmethod
    def _render_surface_texture(cls, x, y, surface, render_mode: RenderMode,
                                scale_width=None, scale_height=None, crop_w=None, crop_h=None,
                                resize_type=ResizeType.FIT):
        """Render a surface to cls.render_canvas using software blitting, keeping alignment, crop, scaling."""
        if resize_type is None:
            resize_type = ResizeType.FIT

        orig_w = surface.contents.w
        orig_h = surface.contents.h
        render_w, render_h = cls._calculate_scaled_width_and_height(orig_w, orig_h, scale_width, scale_height, resize_type)

        # Compute alignment offsets
        adj_x, adj_y = x, y
        if XRenderOption.CENTER == render_mode.x_mode:
            adj_x = x - render_w // 2
        elif XRenderOption.RIGHT == render_mode.x_mode:
            adj_x = x - render_w
        if YRenderOption.CENTER == render_mode.y_mode:
            adj_y = y - render_h // 2
        elif YRenderOption.BOTTOM == render_mode.y_mode:
            adj_y = y - render_h
        adj_x, adj_y = int(adj_x), int(adj_y)

        # Crop handling
        if crop_w is None or crop_w > orig_w:
            crop_w = orig_w
        if crop_h is None or crop_h > orig_h:
            crop_h = orig_h
        src_rect = sdl2.SDL_Rect(0, 0, crop_w, crop_h)
        dst_rect = sdl2.SDL_Rect(adj_x, adj_y, render_w, render_h)

        # Scale surface if needed
        if render_w != crop_w or render_h != crop_h:
            tmp_surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, render_w, render_h, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
            sdl2.SDL_BlitScaled(surface, src_rect, tmp_surface, sdl2.SDL_Rect(0, 0, render_w, render_h))
            sdl2.SDL_BlitSurface(tmp_surface, None, cls.render_canvas, dst_rect)
            sdl2.SDL_FreeSurface(tmp_surface)
        else:
            sdl2.SDL_BlitSurface(surface, src_rect, cls.render_canvas, dst_rect)

        return render_w, render_h


    @classmethod
    def render_text(cls, text, x, y, color, purpose: FontPurpose, render_mode=RenderMode.TOP_LEFT_ALIGNED,
                    crop_w=None, crop_h=None, alpha=None):
        loaded_font = cls.fonts[purpose]
        cache : CachedTextTexture = cls._text_texture_cache.get_texture(text, purpose, color)

        if cache and alpha is None:
            surface = cache.surface
        else:
            sdl_color = sdl2.SDL_Color(color[0], color[1], color[2])
            surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(loaded_font.font, text.encode('utf-8'), sdl_color)
            if not surface:
                PyUiLogger.get_logger().error(f"Failed to render text surface for {text}: {sdl2.sdlttf.TTF_GetError().decode('utf-8')}")
                return 0, 0

            if alpha is not None:
                # Temporary alpha blend
                sdl2.SDL_SetSurfaceBlendMode(surface, sdl2.SDL_BLENDMODE_BLEND)
                # SDL_SetSurfaceAlphaMod requires SDL2 >= 2.0.12; otherwise pre-multiply manually
                sdl2.SDL_SetSurfaceAlphaMod(surface, alpha)

            cls._text_texture_cache.add_texture(text, purpose, color, surface, None)

        return cls._render_surface_texture(x=x, y=y, surface=surface, render_mode=render_mode,
                                        crop_w=crop_w, crop_h=crop_h)


    @classmethod
    def render_text_centered(cls, text, x, y, color, purpose: FontPurpose):
        return cls.render_text(text, x, y, color, purpose, RenderMode.TOP_CENTER_ALIGNED)



    @classmethod
    def render_image(cls, image_path: str, x: int, y: int, render_mode=RenderMode.TOP_LEFT_ALIGNED,
                    target_width=None, target_height=None, resize_type=None):
        if image_path is None:
            return 0, 0

        cache : CachedImageTexture = cls._image_texture_cache.get_texture(image_path)

        if cache:
            surface = cache.surface
        else:
            surface = sdl2.sdlimage.IMG_Load(image_path.encode('utf-8'))
            if not surface:
                PyUiLogger.get_logger().error(f"Failed to load image: {image_path}")
                return 0, 0
            cls._image_texture_cache.add_texture(image_path, surface, None)

        return cls._render_surface_texture(x=x, y=y, surface=surface, render_mode=render_mode,
                                        scale_width=target_width, scale_height=target_height,
                                        resize_type=resize_type)



    @classmethod
    def render_image_centered(cls, image_path: str, x: int, y: int, target_width=None, target_height=None):
        return cls.render_image(image_path, x, y, RenderMode.TOP_CENTER_ALIGNED, target_width, target_height)

    @classmethod
    def render_box(cls, color, x, y, w, h):
        sdl2.SDL_SetRenderDrawColor(cls.renderer.renderer, color[0], color[1], color[2], 255)
        rect = sdl2.SDL_Rect(x, y, w, h)
        sdl2.SDL_RenderFillRect(cls.renderer.renderer, rect)


    @classmethod
    def get_line_height(cls, purpose: FontPurpose):
        return cls.fonts[purpose].line_height

    @classmethod
    def scale_texture_to_fit(cls, src_surface: sdl2.SDL_Surface, target_width: int, target_height: int) -> sdl2.SDL_Surface:
        """
        Scale src_surface to fit within target_width x target_height, preserving aspect ratio.
        Returns a new SDL_Surface with dimensions target_width x target_height.
        """
        src_w = src_surface.contents.w
        src_h = src_surface.contents.h

        # Compute scale factor (fit inside target)
        scale = min(target_width / src_w, target_height / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)

        offset_x = (target_width - new_w) // 2
        offset_y = (target_height - new_h) // 2

        # Create target surface
        scaled_surface = sdl2.SDL_CreateRGBSurfaceWithFormat(
            0, target_width, target_height, 32, sdl2.SDL_PIXELFORMAT_ARGB8888
        )
        if not scaled_surface:
            raise RuntimeError(f"Failed to create target surface: {sdl2.SDL_GetError().decode()}")

        # Fill target with black
        sdl2.SDL_FillRect(scaled_surface, None, 0xFF000000)

        # Source rect
        src_rect = sdl2.SDL_Rect(0, 0, src_w, src_h)
        # Destination rect (centered)
        dst_rect = sdl2.SDL_Rect(offset_x, offset_y, new_w, new_h)

        # Blit scaled surface
        if sdl2.SDL_BlitScaled(src_surface, src_rect, scaled_surface, dst_rect) != 0:
            raise RuntimeError(f"SDL_BlitScaled failed: {sdl2.SDL_GetError().decode()}")

        return scaled_surface


    FADE_DURATION_MS = 96  # 0.25 seconds

    @classmethod
    def fade_transition(cls, texture1, texture2):
        renderer = cls.renderer.renderer

        # Get renderer output size (window size)
        width = ctypes.c_int()
        height = ctypes.c_int()
        sdl2.SDL_GetRendererOutputSize(renderer, width, height)

        # Create an intermediate render target texture
        render_target = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_RGBA8888,
            sdl2.SDL_TEXTUREACCESS_TARGET,
            width.value, height.value
        )

        # Enable blending on both target and texture2
        sdl2.SDL_SetTextureBlendMode(texture2, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetTextureBlendMode(render_target, sdl2.SDL_BLENDMODE_BLEND)

        TARGET_FRAME_MS = 16
        start_time = sdl2.SDL_GetTicks()

        while True:
            frame_start = sdl2.SDL_GetTicks()

            now = sdl2.SDL_GetTicks()
            elapsed = now - start_time
            alpha = int(255 * (elapsed / cls.FADE_DURATION_MS))
            if alpha > 255:
                alpha = 255

            sdl2.SDL_SetTextureAlphaMod(texture2, alpha)

            # Set render target to the intermediate texture
            sdl2.SDL_SetRenderTarget(renderer, render_target)

            # Composite both images into the target
            sdl2.SDL_RenderClear(renderer)
            sdl2.SDL_RenderCopy(renderer, texture1, None, None)
            sdl2.SDL_RenderCopy(renderer, texture2, None, None)

            # Set render target back to default (the screen)
            sdl2.SDL_SetRenderTarget(renderer, None)

            # Draw final composited texture to the screen
            sdl2.SDL_RenderClear(renderer)
            sdl2.SDL_RenderCopy(renderer, render_target, None, None)
            sdl2.SDL_RenderPresent(renderer)

            if alpha == 255:
                break

            # Frame pacing
            frame_time = sdl2.SDL_GetTicks() - frame_start
            delay = TARGET_FRAME_MS - frame_time
            if delay > 0:
                sdl2.SDL_Delay(delay)

        # Cleanup render target (optional, good practice)
        sdl2.SDL_DestroyTexture(render_target)


    @classmethod
    def rotate_canvas(cls) -> sdl2.SDL_Texture:
        """
        Rotates a texture by a given angle (supports 90, 180, 270) without scaling.
        Returns a new texture with dimensions swapped if needed.
        """
        # Query source texture size
        w = sdl2.c_int()
        h = sdl2.c_int()
        query_texture_result = sdl2.SDL_QueryTexture(cls.render_canvas, None, None, w, h)
        
        if query_texture_result != 0:
            # Destroy the old texture if it exists
            if cls.render_canvas:
                sdl2.SDL_DestroyTexture(cls.render_canvas)
                cls.render_canvas = None

            # Decide default size (fallback to current display size)
            width, height = Device.screen_width(), Device.screen_height()

            cls.render_canvas = sdl2.SDL_CreateTexture(
                cls.renderer.sdlrenderer,
                sdl2.SDL_PIXELFORMAT_RGBA8888,
                sdl2.SDL_TEXTUREACCESS_TARGET,
                width,
                height
            )
            if not cls.render_canvas:
                PyUiLogger.get_logger().error("Failed to recreate render_canvas: " + sdl2.SDL_GetError().decode())
                return None        
            
        src_w, src_h = w.value, h.value

        # Determine new target size after rotation
        angle_mod = Device.screen_rotation() % 360
        if angle_mod in (90, 270):
            new_w, new_h = src_h, src_w
        else:
            new_w, new_h = src_w, src_h

        # Create a new target texture
        rotated_texture = sdl2.SDL_CreateTexture(
            cls.renderer.sdlrenderer,
            sdl2.SDL_PIXELFORMAT_RGBA8888,
            sdl2.SDL_TEXTUREACCESS_TARGET,
            new_w,
            new_h
        )
        if not rotated_texture:
            PyUiLogger.get_logger().error(f"new_w = {new_w}, new_h = {new_h}")
            PyUiLogger.get_logger().error("Failed to create target texture: " + sdl2.SDL_GetError().decode())
            return None

        # Set render target
        sdl2.SDL_SetRenderTarget(cls.renderer.sdlrenderer, rotated_texture)
        
        # Clear it
        sdl2.SDL_SetRenderDrawColor(cls.renderer.sdlrenderer, 0, 0, 0, 0)
        sdl2.SDL_RenderClear(cls.renderer.sdlrenderer)

        # Destination rectangle uses **original texture size** (no scaling)
        dst_rect = sdl2.SDL_Rect(
            (new_w - src_w) // 2,  # center horizontally
            (new_h - src_h) // 2,  # center vertically
            src_w,
            src_h
        )

        # Center of rotation inside the dst_rect
        center = sdl2.SDL_Point(src_w // 2, src_h // 2)

        # Render with rotation
        sdl2.SDL_RenderCopyEx(
            cls.renderer.sdlrenderer,
            cls.render_canvas,
            None,
            dst_rect,
            Device.screen_rotation(),
            center,
            sdl2.SDL_FLIP_NONE
        )

        # Reset render target
        sdl2.SDL_SetRenderTarget(cls.renderer.sdlrenderer, None)

        return rotated_texture
         
    @classmethod
    def present(cls, fade=False):
        if Theme.render_top_and_bottom_bar_last():
            cls.top_bar.render_top_bar(cls.top_bar_text)
            cls.bottom_bar.render_bottom_bar()

        #sdl2.SDL_SetRenderTarget(cls.renderer.renderer, None)

        if Device.should_scale_screen():
            scaled_canvas = cls.scale_texture_to_fit(cls.render_canvas, Device.output_screen_width(), Device.output_screen_height())
            sdl2.SDL_RenderCopy(cls.renderer.sdlrenderer, scaled_canvas, None, None)
            sdl2.SDL_DestroyTexture(scaled_canvas)
        elif(0 == Device.screen_rotation()):
            pass
            #if(fade):
            #    cls.fade_transition(cls.bg_canvas, cls.render_canvas)
            #else:
            #    sdl2.SDL_RenderCopy(cls.renderer.sdlrenderer, cls.render_canvas, None, None)
        else:   
                rotated_texture = cls.rotate_canvas()
                if(rotated_texture is not None):
                    sdl2.SDL_RenderCopy(cls.renderer.sdlrenderer, rotated_texture, None, None)
                    sdl2.SDL_DestroyTexture(rotated_texture)  # free GPU memory

        #sdl2.SDL_SetRenderTarget(cls.renderer.renderer, cls.render_canvas)
        cls.renderer.present()
        cls.present_to_fb()
        #sdl2.SDL_SetRenderTarget(cls.renderer.renderer, cls.render_canvas)

    @classmethod
    def setup_fb(cls, fb_path="/dev/fb0"):
        """Open and mmap framebuffer once at startup."""
        cls.fb_fd = os.open(fb_path, os.O_RDWR)
        cls.fb_mem = mmap.mmap(
            cls.fb_fd,
            Device.screen_width() * Device.screen_height() * 4,
            mmap.MAP_SHARED,
            mmap.PROT_WRITE | mmap.PROT_READ
        )

        # Create main offscreen surface (software ARGB8888)
        cls.render_surface = sdl2.SDL_CreateRGBSurfaceWithFormat(
            0,
            Device.screen_width(),
            Device.screen_height(),
            32,
            sdl2.SDL_PIXELFORMAT_ARGB8888
        )
        if not cls.render_surface:
            raise RuntimeError(f"Failed to create software surface: {sdl2.SDL_GetError().decode()}")

        # Fill black initially
        sdl2.SDL_FillRect(cls.render_surface, None, 0xFF000000)

    @classmethod
    def present_to_fb(cls):
        """Fast copy of cls.render_canvas (SDL_Surface) to /dev/fb0."""
        logger = PyUiLogger.get_logger()
        logger.debug("present_to_fb_fast called")

        if cls.fb_mem is None or cls.render_surface is None:
            logger.info("Framebuffer or render_surface not initialized; calling setup_fb")
            cls.setup_fb()

        if cls.render_canvas is None:
            logger.warning("render_canvas is None; nothing to render")
            return

        width = Device.screen_width()
        height = Device.screen_height()
        surface = cls.render_canvas

        # Lock surface if needed
        if sdl2.SDL_MUSTLOCK(surface):
            sdl2.SDL_LockSurface(surface)

        src_ptr = ctypes.cast(surface.contents.pixels, ctypes.POINTER(ctypes.c_uint8))
        fb_ptr = ctypes.cast(ctypes.addressof(ctypes.c_char.from_buffer(cls.fb_mem)), ctypes.POINTER(ctypes.c_uint8))

        src_pitch = surface.contents.pitch
        fb_pitch = cls.render_surface.contents.pitch

        if src_pitch == fb_pitch:
            # Direct block copy
            size = src_pitch * height
            ctypes.memmove(fb_ptr, src_ptr, size)
        else:
            # Row-by-row copy (slower)
            logger.debug(f"Pitch mismatch detected (src: {src_pitch}, fb: {fb_pitch}), copying row by row")
            for y in range(height):
                src_offset = y * src_pitch
                fb_offset = y * fb_pitch
                ctypes.memmove(ctypes.byref(fb_ptr, fb_offset),
                            ctypes.byref(src_ptr, src_offset),
                            min(src_pitch, fb_pitch))

        if sdl2.SDL_MUSTLOCK(surface):
            sdl2.SDL_UnlockSurface(surface)

        logger.debug("Frame copied to framebuffer (fast)")


    #TODO make default false and fix everywhere
    @classmethod
    def get_top_bar_height(cls, force_include_top_bar = True):
        return 0 if Theme.ignore_top_and_bottom_bar_for_layout() and not force_include_top_bar else cls.top_bar.get_top_bar_height()

    @classmethod
    def get_bottom_bar_height(cls):
        return 0 if Theme.ignore_top_and_bottom_bar_for_layout() else cls.bottom_bar.get_bottom_bar_height()

    @classmethod
    def get_usable_screen_height(cls, force_include_top_bar = False):
        return Device.screen_height() if Theme.ignore_top_and_bottom_bar_for_layout() and not force_include_top_bar else Device.screen_height() - cls.get_bottom_bar_height() - cls.get_top_bar_height()

    @classmethod
    def get_center_of_usable_screen_height(cls, force_include_top_bar = False):
        return ((Device.screen_height() - cls.get_bottom_bar_height() - cls.get_top_bar_height(force_include_top_bar)) // 2) + cls.get_top_bar_height(force_include_top_bar)

    @classmethod
    def get_image_dimensions(cls, img):
        if(img is None):
            return 0, 0
        
        surface = sdl2.sdlimage.IMG_Load(img.encode('utf-8'))
        if not surface:
            return 0, 0
        width, height = surface.contents.w, surface.contents.h
        sdl2.SDL_FreeSurface(surface)
        return width, height

    @classmethod
    def get_text_dimensions(cls, purpose, text="A"):
        sdl_color = sdl2.SDL_Color(0, 0, 0)
        surface = sdl2.sdlttf.TTF_RenderUTF8_Blended(cls.fonts[purpose].font, text.encode('utf-8'), sdl_color)
        if not surface:
            return 0, 0
        width, height = surface.contents.w, surface.contents.h
        sdl2.SDL_FreeSurface(surface)
        return width, height

    @classmethod
    def add_index_text(cls, index, total, force_include_index = False, letter = None):
        if(force_include_index or Theme.show_index_text()):
            y_padding = max(5, cls.get_bottom_bar_height() // 4)
            y_value = Device.screen_height() - y_padding
            x_padding = 10

            x_offset = Device.screen_width() - x_padding
            total_text_w, _ = cls.render_text(
                str(total),
                x_offset,
                y_value,
                Theme.text_color(FontPurpose.LIST_TOTAL),
                FontPurpose.LIST_TOTAL,
                RenderMode.BOTTOM_RIGHT_ALIGNED
            )

            x_offset -= total_text_w
            index_text_w, index_text_h = cls.render_text(
                str(index).zfill(len(str(total))) + "/",
                x_offset,
                y_value,
                Theme.text_color(FontPurpose.LIST_INDEX),
                FontPurpose.LIST_INDEX,
                RenderMode.BOTTOM_RIGHT_ALIGNED
            )

            x_offset -= index_text_w  + x_padding
            if(letter is not None):
                cls.render_text(
                    letter,
                    x_offset,
                    y_value,
                    Theme.text_color(FontPurpose.LIST_INDEX),
                    FontPurpose.LIST_INDEX,
                    RenderMode.BOTTOM_RIGHT_ALIGNED
                )


    @classmethod
    def get_current_top_bar_title(cls):
        return cls.top_bar.get_current_title()

    @classmethod
    def volume_changed(cls, vol):
        cls.top_bar.volume_changed(vol)

