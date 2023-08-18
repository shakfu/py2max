from py2max import Patcher

# is this is redundant ?

class RnboSubPatcher(Patcher):
    """Core Patcher class describing a Max patchers from the ground up.

    Any Patcher can be converted to a .maxpat file.
    """

    def __init__(
        self,
        path: Optional[str | Path] = None,
        parent: Optional["Patcher"] = None,
        classnamespace: Optional[str] = None,
        reset_on_render: bool = True,
        layout: str = "horizontal",
        auto_hints: bool = False,
        openinpresentation: int = 0,
    ):
        super().__init__(path, parent, "rnbo", reset_on_render, layout, auto_hints, openinpresentation)
        self.accentcolor = [
          0.343034118413925,
          0.506230533123016,
          0.86220508813858,
          1.0,
        ]
        self.bgfillcolor_angle =  270.0
        self.bgfillcolor_autogradient = 0.0
        self.bgfillcolor_color = [
          0.031372549019608,
          0.125490196078431,
          0.211764705882353,
          1.0,
        ]
        self.bgfillcolor_color1 = [
          0.031372549019608,
          0.125490196078431,
          0.211764705882353,
          1.0,
        ]
        self.bgfillcolor_color2 = [
          0.263682,
          0.004541,
          0.038797,
          1.0,
        ]
        self.bgfillcolor_proportion = 0.39
        self.bgfillcolor_type = "color"
        self.color: [
            0.929412,
            0.929412,
            0.352941,
            1.0,
        ]

        self.default_bgcolor = [
            0.031372549019608,
            0.125490196078431,
            0.211764705882353,
            1.0,
        ]

        self.elementcolor = [
            0.357540726661682,
            0.515565991401672,
            0.861786782741547,
            1.0,
        ]
