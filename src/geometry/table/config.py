def tableSliderConfig():
    return [
        ("Segment Count", (2, 9), 5),
        ("Object Width", (0.5, 2.0), 1.0),
        ("Twist Angle", (0, 45), 20),
        ("Twist Groove Depth", (0, 5), 1),
        ("Vertical Wave Frequency", (0, 20), 3),
        ("Vertical Wave Depth", (0, 5), 1),
    ]

def tableDefaults():
    return {
        "Segment Count": 9,
        "Object Width": 1.2,
        "Twist Angle": 10.0,
        "Twist Groove Depth": 1.0,
        "Vertical Wave Frequency": 4.0,
        "Vertical Wave Depth": 1.0,
    }

