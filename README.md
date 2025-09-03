# Parametric Design Tool V1 
>NOTE: THIS IS A PROOF OF CONCEPT FOR THE UPDATED DESIGN TOOL TO SHOWCASE THE CORE FUNCTION. CODE WILL BE CLEANED AND EXPANDED UPON...

## Structure
```
ParametricDesignTool_V1/
├── src/                         # Source code
│   ├── core/                    # Core application logic
│   │   ├── app.py               # MainApp class (performance optimized)
│   ├── geometry/                # Geometry modules
│   │   ├── vase/                # Vase object geometry
│   │   │   ├── geometry.py      # Vase geometry generation
│   │   │   └── config.py        # Vase parameter configuration
│   │   └── table/               # Table object geometry
│   │       ├── geometry.py      # Table geometry generation
│   │       │   └── config.py    # Table parameter configuration
│   ├── ui/                      # User interface
│   │   ├── controls.py          # ParametricControls class
│   │   └── ui_metrics.py        # UI metrics display
│   ├── camera/                  # Camera system
│   │   └── controller.py        # OrbitCamera with optimal view calculation
│   ├── rendering/               # Rendering system
│   │   └── lighting.py          # Lighting setup
│   └── utils/                   # Utilities
│       └── ui_utils.py          # UI utility functions
├── requirements.txt             # Dependencies
├── run.py                      # Entry point
└── README.md                   # This file
```

## Running the Application

```bash
python run.py
```

