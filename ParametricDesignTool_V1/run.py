###### RUN THIS FILE TO START THE APPLICATION ######

import sys
import os

#This src/core/app.py is the main app file
from src.core.app import MainApp


### Source files are in the src directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    app = MainApp()
    app.run()
