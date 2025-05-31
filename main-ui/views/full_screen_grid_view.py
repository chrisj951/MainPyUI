from typing import List
from controller.controller_inputs import ControllerInput
from devices.device import Device
from display.font_purpose import FontPurpose
from display.display import Display
from display.render_mode import RenderMode
from display.resize_type import ResizeType
from display.y_render_option import YRenderOption
from controller.controller import Controller
from themes.theme import Theme
from utils.py_ui_config import PyUiConfig
from views.grid_or_list_entry import GridOrListEntry
from views.selection import Selection
from views.view import View


class FullScreenGridView(View):
    def __init__(self, top_bar_text, options: List[GridOrListEntry], selected_bg: str = None,
                 selected_index=0, show_grid_text=True,
                 set_top_bar_text_to_selection=False, 
                 unselected_bg = None, missing_image_path=None):
        super().__init__()
        self.resized_width = int(Device.screen_width() * 1.0)
        self.resized_height = int(Device.screen_height() * 0.75)
        self.resize_type = ResizeType.ZOOM
        self.top_bar_text = top_bar_text
        self.set_top_bar_text_to_selection = set_top_bar_text_to_selection
        self.options: List[GridOrListEntry] = options

        self.max_img_height = self.resized_height
        if (self.max_img_height is None):
            self.max_img_height = 0
            for option in options:
                self.max_img_height = max(
                    self.max_img_height, Display.get_image_dimensions(option.get_image_path())[1])

        self.selected = selected_index
        self.toggles = [False] * len(options)

        self.current_left = 0
        self.current_right = min(len(options), 10)

        self.font_purpose = FontPurpose.GRID_ONE_ROW

        self.selected_bg = selected_bg
        self.unselected_bg = unselected_bg
        self.show_grid_text = show_grid_text
        self.missing_image_path = missing_image_path
        # TODO Get hard coded values for padding from theme
        self.x_pad = 10
        self.usable_width = Device.screen_width() - (2 * self.x_pad)
        self.icon_width = self.usable_width  # Initial icon width
        self.x_text_pad = 20 #TODO
        self.option_text_widths = []
        for option in self.options:
            self.option_text_widths.append(Display.get_text_dimensions(self.font_purpose, option.get_primary_text())[0])

        self.last_selected = -1
        self.last_start = 0


    def set_options(self, options):
        self.options = options

    def correct_selected_for_off_list(self):
        while (self.selected < 0):
            self.selected = len(self.options) + self.selected
        if(self.selected >= len(self.options)):
            self.selected = 0

        self.selected = max(0, self.selected)

        while(self.selected < self.current_left):
            self.current_left -= 1
            self.current_right -=1

        while(self.selected >= self.current_right):
            self.current_left += 1
            self.current_right +=1

    def _render_shadowed_text(self, primary_text, y_offset_base, backdrop_font, front_font, x_offset):

        #TODO hardcoded values of 25        
        shadow_color =  Theme.text_color(backdrop_font)
        # Render black text surfaces at offsets for the "outline"
        shift_amt = 5
        for dx in range (1,shift_amt):
            for dy in range(1,shift_amt):
                Display.render_text(primary_text,
                                        x_offset + dx,
                                        y_offset_base + dy,
                                        shadow_color,
                                        backdrop_font,
                                        render_mode=RenderMode.TOP_LEFT_ALIGNED)
                Display.render_text(primary_text,
                                        x_offset - dx,
                                        y_offset_base + dy,
                                        shadow_color,
                                        backdrop_font,
                                        render_mode=RenderMode.TOP_LEFT_ALIGNED)
                Display.render_text(primary_text,
                                        x_offset + dx,
                                        y_offset_base - dy,
                                        shadow_color,
                                        backdrop_font,
                                        render_mode=RenderMode.TOP_LEFT_ALIGNED)
                Display.render_text(primary_text,
                                        x_offset - dx,
                                        y_offset_base - dy,
                                        shadow_color,
                                        backdrop_font,
                                        render_mode=RenderMode.TOP_LEFT_ALIGNED)
        primary_color =  Theme.text_color(front_font)

        # Render text in primary color
        offsets = [(0,0)]  # diagonal directions
        for dx, dy in offsets:
            Display.render_text(primary_text,
                                    x_offset + dx,
                                    y_offset_base + dy,
                                    primary_color,
                                    front_font,
                                    render_mode=RenderMode.TOP_LEFT_ALIGNED)

    def _render_primary_image(self,
                              image_path: str,
                              primary_text: str,
                              secondary_text: str,
                              x: int, 
                              y: int, 
                              render_mode=RenderMode.TOP_LEFT_ALIGNED, 
                              target_width=None, 
                              target_height=None, 
                              resize_type=None):
        
        w,h = Display.render_image(image_path=image_path,
                                   x=x,
                                   y=y,
                                   render_mode=render_mode,
                                   target_width=target_width,
                                   target_height=target_height,
                                   resize_type=resize_type)
        
        if(w == 0):
            w,h = Display.render_image(image_path=self.missing_image_path,
                                   x=x,
                                   y=y,
                                   render_mode=render_mode,
                                   target_width=target_width,
                                   target_height=target_height,
                                   resize_type=resize_type)
        self._render_shadowed_text(primary_text, Device.screen_height() * 0.68, FontPurpose.SHADOWED_BACKDROP, FontPurpose.SHADOWED, 25)
        self._render_shadowed_text(secondary_text, Device.screen_height() * 0.78, FontPurpose.SHADOWED_BACKDROP_SMALL, FontPurpose.SHADOWED_SMALL, 27)

        return w,h

    def _render_image(self):
        imageTextPair = self.options[self.selected]
        image_path = imageTextPair.get_image_path_selected() 
        primary_text = imageTextPair.get_primary_text_long()
        secondary_text = imageTextPair.get_description()
        x_offset = 0
        render_mode = RenderMode.TOP_LEFT_ALIGNED
                    
        self._render_primary_image( image_path,
                                    primary_text,
                                    secondary_text,
                                    x_offset,
                                    Display.get_top_bar_height(False),
                                    render_mode,
                                    target_width=self.resized_width,
                                    target_height=self.resized_height,
                                    resize_type=self.resize_type)
        
    def calculate_start_index(self):
        start_index = self.selected + 1 if self.selected != len(self.options) -1 else self.selected
        current_width = self.option_text_widths[start_index] + self.x_text_pad

        for i in range(start_index - 1, -1, -1):
            added_width = self.option_text_widths[i] + self.x_text_pad
            if current_width + added_width > Device.screen_width():
                break
            current_width += added_width
            start_index = i

        return start_index
        
    def _render_bottom_bar_text(self):
        start_index = self.calculate_start_index()
        if(self.last_start > start_index):
            if(self.selected >= self.last_start):
                start_index = self.last_start
            else:
                while(self.last_start < start_index):
                    start_index = self.last_start - 1

        visible_text_options = self.options[start_index:len(self.options)]

        y_offset = Device.screen_height() - 10 #TODO
        x_offset = self.x_text_pad

        for visible_index, imageTextPair in enumerate(visible_text_options):
            actual_index = start_index + visible_index
            color = Theme.text_color_selected(
                self.font_purpose) if actual_index == self.selected else Theme.text_color(self.font_purpose)
            w, h = Display.render_text(imageTextPair.get_primary_text(),
                                 x_offset,
                                 y_offset,
                                 color,
                                 self.font_purpose,
                                 render_mode=RenderMode.BOTTOM_LEFT_ALIGNED)
            x_offset += self.x_text_pad + w

        self.last_selected = self.selected
        self.last_start = start_index

    def _render(self):
        if (self.set_top_bar_text_to_selection) and len(self.options) > 0:
            Display.clear(
                self.options[self.selected].get_primary_text(), hide_top_bar_icons=True, render_bottom_bar=False)
        else:
            Display.clear(self.top_bar_text, render_bottom_bar_icons_and_images=False)
        self.correct_selected_for_off_list()

        self._render_image()
        self._render_bottom_bar_text()

        Display.present()

    def get_selected_option(self):
        if 0 <= self.selected < len(self.options):
            return self.options[self.selected]
        else:
            return None

    def get_selection(self, select_controller_inputs=[ControllerInput.A]):
        self._render()

        if (Controller.get_input()):
            if Controller.last_input() == ControllerInput.DPAD_LEFT:
                self.selected -= 1
                self.correct_selected_for_off_list()
            elif Controller.last_input() == ControllerInput.DPAD_RIGHT:
                self.selected += 1
                self.correct_selected_for_off_list()
            elif Controller.last_input() == ControllerInput.L1:
                self.selected -= 1
                self.correct_selected_for_off_list()
            elif Controller.last_input() == ControllerInput.R1:
                self.selected += 1
                self.correct_selected_for_off_list()
            elif Controller.last_input() in select_controller_inputs:
                return Selection(self.get_selected_option(), Controller.last_input(), self.selected)
            elif Controller.last_input() == ControllerInput.B:
                return Selection(self.get_selected_option(), Controller.last_input(), self.selected)

        return Selection(self.get_selected_option(), None, self.selected)