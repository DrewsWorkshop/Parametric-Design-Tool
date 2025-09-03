def vaseSliderConfig():
    return [
        ("Segment Count", (2, 9), 5),
        ("Object Width", (2, 3), 2.5),
        ("Twist Angle", (0, 45), 20),
        ("Twist Groove Depth", (0, 5), 1),
        ("Vertical Wave Frequency", (0, 20), 3),
        ("Vertical Wave Depth", (0, 5), 1),
    ]

def vaseDefaults():
    return {
        "Segment Count": 5,
        "Object Width": 2.5,
        "Twist Angle": 20.0,
        "Twist Groove Depth": 1.0,
        "Vertical Wave Frequency": 3.0,
        "Vertical Wave Depth": 1.0,
    }