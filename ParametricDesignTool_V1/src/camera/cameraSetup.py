def disable_controls(self):
    self._dragging = False
    self._last_mouse = None

def enable_controls(self):
    # Controls are enabled by default, just ensure dragging is reset
    self._dragging = False
    self._last_mouse = None