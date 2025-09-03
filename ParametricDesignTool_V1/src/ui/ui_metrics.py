from direct.gui.OnscreenText import OnscreenText


class UIMetrics:

    def __init__(self):
        self.bb_text = None

    def show_bounding_box(self, *, width=None, height=None, depth=None, diameter=None, decimals: int = 2):

        if self.bb_text:
            self.bb_text.removeNode()
            self.bb_text = None

        # Build label
        if diameter is not None and height is not None:
            text = f"Height: {height:.{decimals}f} inches | Diameter: {diameter:.{decimals}f} inches"
        elif width is not None and height is not None and depth is not None:
            text = (
                f"Dimensions\n"
                f"Height: {height:.{decimals}f}\n"
                f"Depth: {depth:.{decimals}f}"
            )
        else:
            text = "Bounding Box: N/A"

        # Create on-screen text at center of the screen
        self.bb_text = OnscreenText(
            text=text,
            pos=(-.25, -.85),
            scale=0.04,
            fg=(1, 1, 1, 1),
            align=0,  # left
            mayChange=True,
            bg=(0, 0, 0, 0.5),
            shadow=(0, 0, 0, 1),
        )

    def clear(self):
        if self.bb_text:
            self.bb_text.removeNode()
            self.bb_text = None
