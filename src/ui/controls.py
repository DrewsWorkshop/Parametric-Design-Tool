from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectSlider import DirectSlider
from direct.gui.DirectButton import DirectButton
from direct.gui.DirectFrame import DirectFrame
from direct.showbase.ShowBase import ShowBase
 
import json
import os
from datetime import datetime
from src.utils.ui_utils import (
	get_default_param_configs,
	compute_page_size,
	format_slider_label_text,
	get_all_parameters_from_sliders,
	save_favorite_to_file,
	show_temporary_status,
)


class ParametricControls:
    
    def __init__(self, on_parameter_change_callback, slider_config_func=None, on_object_change_callback=None, get_current_object_type_callable=None, on_hide_object_callback=None, on_show_object_callback=None, on_rebuild_with_params_callback=None, on_display_all_favorites_callback=None, on_clear_favorite_objects_callback=None, on_highlight_favorite_callback=None):
        self.on_parameter_change = on_parameter_change_callback
        self.on_object_change = on_object_change_callback
        self.get_current_object_type = get_current_object_type_callable
        self.on_hide_object = on_hide_object_callback
        self.on_show_object = on_show_object_callback
        self.on_rebuild_with_params = on_rebuild_with_params_callback
        self.on_display_all_favorites = on_display_all_favorites_callback
        self.on_clear_favorite_objects = on_clear_favorite_objects_callback
        self.on_highlight_favorite = on_highlight_favorite_callback
        
        # Get slider configuration from the provided function or use default
        if slider_config_func:
            param_configs = slider_config_func()
        else:
            param_configs = get_default_param_configs()

        self.sliders = {}
        self.text_displays = {}
        self.slider_positions = {}  # Store fraction-based positions
        
        # Favorites state
        self.favorites_list = []
        self.current_favorite_index = 0

        # Generate positions for sliders (from top to bottom)
        for i, (name, range_vals, default) in enumerate(param_configs):
            # Calculate fraction-based positions: 15% from left, 15% from top with spacing
            x_fraction = 0.0  # 15% from left edge
            y_fraction = 0.85 - (i * 0.08)  # 15% from top (85% from bottom), 8% spacing
            
            # Store fraction positions for responsive updates
            self.slider_positions[name] = (x_fraction, y_fraction)
            
            # Convert to normalized coordinates
            pos = self.fraction_to_normalized(x_fraction, y_fraction)
            
            # Create slider
            slider = DirectSlider(
                range=range_vals, value=default, pageSize=compute_page_size(range_vals),
                orientation="horizontal",
                pos=pos, scale=0.4,
                thumb_frameColor=(0.6, 0.6, 0.8, 1),
                thumb_relief="flat",
                command=lambda n=name: self._on_slider_change(n)
            )
            self.sliders[name] = slider

            # Create text display
            text = OnscreenText(
                text=format_slider_label_text(name, default),
                pos=(pos[0] - 0.4, pos[2] + 0.05), scale=0.03,
                fg=(1, 1, 1, 1), align=0, mayChange=True
            )
            self.text_displays[name] = text

        # Add favorite button
        self.favorite_button = DirectButton(
            text="Save to Favorites",
            pos=(-1, 0, -0.2), scale=0.04,
            frameColor=(0.2, 0.8, 0.2, 1),
            relief="flat",
            command=self._save_favorite
        )

        # Add Favorites button
        self.favorites_button = DirectButton(
            text="Favorites",
            pos=(-1.4, 0, .95), scale=0.04,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._open_favorites
        )

        # Add Builder button
        self.builder_button = DirectButton(
            text="Builder",
            pos=(-1.6, 0, .95), scale=0.04,
            frameColor=(0.8, 0.6, 0.2, 1),
            relief="flat",
            command=self._open_builder
        )

        self.object_type_text = OnscreenText(
            text="Object Type:",
            pos=(-1.4, 0.85, 0), scale=0.04,
            fg=(1, 1, 1, 1), align=0, mayChange=True
        )

        # Add custom dropdown menu
        self.dropdown_items = ["Vace", "Table"]
        self.dropdown_open = False
        self.selected_option = "Vace"
        
        # Main dropdown button
        self.dropdown_button = DirectButton(
            text=self.selected_option,
            pos=(-1.1, 0, 0.85), scale=0.04,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._toggle_dropdown
        )
        
        # Dropdown options frame (initially hidden)
        self.dropdown_frame = DirectFrame(
            pos=(-1.1, 0, 0.8), scale=0.04,
            frameColor=(0.4, 0.4, 0.6, 1),
            relief="flat"
        )
        self.dropdown_frame.hide()
        
        # Create option buttons with better spacing
        self.option_buttons = []
        for i, option in enumerate(self.dropdown_items):
            button = DirectButton(
                text=option,
                pos=(0, 0, -i * 1.25), scale=1.0,
                frameColor=(0.5, 0.5, 0.7, 1),
                relief="flat",
                command=self._select_option,
                extraArgs=[option]
            )
            button.reparentTo(self.dropdown_frame)
            self.option_buttons.append(button)

        # Status text for save confirmation
        self.status_text = OnscreenText(
            text="",
            pos=(0, -0.9), scale=0.03,
            fg=(0, 1, 0, 1), align=1, mayChange=True
        )
        
        # Info panel to display favorites data (hidden until used)
        self.favorites_info_text = OnscreenText(
            text="",
            pos=(0, 0.6), scale=0.04,
            fg=(1, 1, 1, 1), align=1, mayChange=True
        )
        self.favorites_info_text.hide()

        # Favorites navigation arrows (hidden until Favorites opened)
        self.fav_prev_button = DirectButton(
            text="<",
            pos=(-1, 0, 0), scale=0.1,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._favorites_prev
        )
        self.fav_prev_button.hide()

        self.fav_next_button = DirectButton(
            text=">",
            pos=(1, 0, 0), scale=0.1,
            frameColor=(0.6, 0.6, 0.8, 1),
            relief="flat",
            command=self._favorites_next
        )
        self.fav_next_button.hide()
        
        # Set up window resize event handler
        from direct.showbase.ShowBaseGlobal import base
        base.accept('window-resized', self.on_window_resize)

    def fraction_to_normalized(self, x_fraction, y_fraction):
        normalized_x = x_fraction * 2 - 1
        normalized_y = y_fraction * 2 - 1
        return normalized_x, 0, normalized_y

    def on_window_resize(self):
        for name, (x_fraction, y_fraction) in self.slider_positions.items():
            new_pos = self.fraction_to_normalized(x_fraction, y_fraction)
            
            # Update slider position
            if name in self.sliders:
                self.sliders[name].setPos(new_pos)
            
            # Update text position (maintain offset above slider)
            if name in self.text_displays:
                text_pos = (new_pos[0], new_pos[2] + 0.05)
                self.text_displays[name].setPos(text_pos)

    def _on_slider_change(self, slider_name):
        value = self.sliders[slider_name]["value"]
        self.text_displays[slider_name].setText(format_slider_label_text(slider_name, value))
        
        if self.on_parameter_change:
            # Get all current parameter values
            params = self.get_all_parameters()
            self.on_parameter_change(params)

    def _save_favorite(self):
        try:
            params = self.get_all_parameters()
            object_type = self.get_current_object_type() if callable(self.get_current_object_type) else None
            total = save_favorite_to_file("tmp.txt", params, object_type=object_type)
            show_temporary_status(self.status_text, f"Favorite saved! ({total} total)", (0, 1, 0, 1), 3)
        except Exception as e:
            show_temporary_status(self.status_text, f"Error saving: {str(e)}", (1, 0, 0, 1), 3)

    def _open_favorites(self):
        print("Favorites button clicked!")
        show_temporary_status(self.status_text, "Favorites", (1, 1, 0, 1), 2)
        
        # Hide all sliders and their text displays
        for slider in self.sliders.values():
            slider.hide()
        for text in self.text_displays.values():
            text.hide()
        
        # Hide Object Type label and dropdown
        self.object_type_text.hide()
        self.dropdown_button.hide()
        self.dropdown_frame.hide()
        
        # Hide Save to Favorites button
        self.favorite_button.hide()
        
        # Hide the 3D object
        if callable(self.on_hide_object):
            self.on_hide_object()

        # Load favorites and display all at once
        try:
            self.favorites_list = []
            self.current_favorite_index = 0
            if os.path.exists("tmp.txt"):
                with open("tmp.txt", "r") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list):
                    self.favorites_list = loaded
            
            if callable(self.on_display_all_favorites):
                self.on_display_all_favorites(self.favorites_list)
            
            self._render_favorites_overview()
            
            if self.favorites_list:
                self._highlight_current_favorite()
        except Exception as e:
            show_temporary_status(self.status_text, f"Failed to load favorites: {e}", (1, 0, 0, 1), 3)
        
        self.fav_prev_button.show()
        self.fav_next_button.show()

    def _open_builder(self):
        """Open builder interface - restore all UI elements."""
        print("Builder button clicked!")
        show_temporary_status(self.status_text, "Builder mode", (1, 0.5, 0, 1), 2)
        
        for slider in self.sliders.values():
            slider.show()
        for text in self.text_displays.values():
            text.show()
        
        self.object_type_text.show()
        self.dropdown_button.show()
        
        self.favorite_button.show()
        
        if callable(self.on_show_object):
            self.on_show_object()

        self.favorites_info_text.hide()
        self.favorites_info_text.setText("")
        
        self.fav_prev_button.hide()
        self.fav_next_button.hide()
        
        if hasattr(self, 'on_clear_favorite_objects') and callable(self.on_clear_favorite_objects):
            self.on_clear_favorite_objects()

    def _favorites_prev(self):
        if not self.favorites_list:
            show_temporary_status(self.status_text, "No favorites", (1, 1, 0, 1), 1)
            return
        self.current_favorite_index = (self.current_favorite_index - 1) % len(self.favorites_list)
        self._highlight_current_favorite()
        self._render_favorites_overview()

    def _favorites_next(self):
        if not self.favorites_list:
            show_temporary_status(self.status_text, "No favorites", (1, 1, 0, 1), 1)
            return
        self.current_favorite_index = (self.current_favorite_index + 1) % len(self.favorites_list)
        self._highlight_current_favorite()
        self._render_favorites_overview()

    def _highlight_current_favorite(self):
        if not self.favorites_list or not hasattr(self, 'on_highlight_favorite'):
            return
        
        # Call the main app to highlight the current favorite
        if callable(self.on_highlight_favorite):
            self.on_highlight_favorite(self.current_favorite_index)

    def _load_current_favorite_object(self):
        if not self.favorites_list or not callable(self.on_rebuild_with_params):
            return
        entry = self.favorites_list[self.current_favorite_index]
        params = entry.get("parameters", {})
        object_type = entry.get("object_type", None)
        self.on_rebuild_with_params(params, object_type)

    def _render_current_favorite_info(self):
        if not self.favorites_list:
            self.favorites_info_text.setText("No favorites saved yet.")
            self.favorites_info_text.setFg((1, 1, 1, 1))
            self.favorites_info_text.show()
            return
        idx = max(0, min(self.current_favorite_index, len(self.favorites_list) - 1))
        entry = self.favorites_list[idx]
        object_type = entry.get("object_type", "Unknown")
        params = entry.get("parameters", {})
        header = f"Favorite {idx + 1}/{len(self.favorites_list)} — {object_type}"
        lines = [header]
        for key, val in params.items():
            lines.append(f"{key}: {val}")
        self.favorites_info_text.setText("\n".join(lines))
        self.favorites_info_text.setFg((1, 1, 1, 1))
        self.favorites_info_text.show()

    def _render_favorites_overview(self):
        if not self.favorites_list:
            self.favorites_info_text.setText("No favorites saved yet.")
            self.favorites_info_text.setFg((1, 1, 1, 1))
            self.favorites_info_text.show()
            return
        
        # Show current favorite details
        idx = self.current_favorite_index
        favorite = self.favorites_list[idx]
        object_type = favorite.get("object_type", "Unknown")
        timestamp = favorite.get("timestamp", "Unknown time")
        params = favorite.get("parameters", {})
        
        header = f"Favorite {idx + 1}/{len(self.favorites_list)} — {object_type}"
        timestamp_line = f"Created: {timestamp}"
        lines = [header, timestamp_line, ""]
        
        # Add parameter details
        for key, val in params.items():
            lines.append(f"{key}: {val:.2f}")
        
        self.favorites_info_text.setText("\n".join(lines))
        self.favorites_info_text.setFg((1, 1, 1, 1))
        self.favorites_info_text.show()

    def _toggle_dropdown(self):
        if self.dropdown_open:
            self.dropdown_frame.hide()
            self.dropdown_open = False
        else:
            self.dropdown_frame.show()
            self.dropdown_open = True

    def _select_option(self, option):
        self.selected_option = option
        self.dropdown_button['text'] = option
        self.dropdown_frame.hide()
        self.dropdown_open = False
        print(f"Selected: {option}")
        # Notify listener about object change if provided
        if callable(self.on_object_change):
            self.on_object_change(option)

    def reset_to_defaults(self, object_type):
        try:
            # Import here to avoid circular import issues at module load time
            from src.geometry.vase.config import vaseSliderConfig, vaseDefaults
            from src.geometry.table.config import tableSliderConfig, tableDefaults

            if object_type == 'Table':
                param_configs = tableSliderConfig()
                defaults = tableDefaults()
            else:
                param_configs = vaseSliderConfig()
                defaults = vaseDefaults()

            # Apply ranges and reset values/labels
            for (name, range_vals, default_val) in param_configs:
                if name in self.sliders:
                    self.sliders[name]['range'] = range_vals
                    new_value = defaults.get(name, default_val)
                    self.sliders[name]['value'] = new_value
                    if name in self.text_displays:
                        self.text_displays[name].setText(
                            format_slider_label_text(name, new_value)
                        )
                # If a slider does not exist (mismatched config), skip for now
        except Exception as e:
            # Keep UI resilient; log for debugging
            print(f"Failed to reset defaults for {object_type}: {e}")

    def get_all_parameters(self):
        return get_all_parameters_from_sliders(self.sliders)

    def get_parameter(self, name):
        return self.sliders[name]["value"] if name in self.sliders else 0.0

    def set_favorites_list(self, favorites_list):
        self.favorites_list = favorites_list
        self.current_favorite_index = 0


# Keep the old class for backward compatibility
class HeightSlider(ParametricControls):
    
    def __init__(self, on_height_change_callback):
        # Create a wrapper callback that extracts just the height
        def height_wrapper(params):
            on_height_change_callback(params.get("Height", 1.0))
        
        super().__init__(height_wrapper)
