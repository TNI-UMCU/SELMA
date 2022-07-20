# -*- coding: utf-8 -*-
from cx_Freeze import setup, Executable

base = None    

executables = [Executable("SELMA.py", base=base)]

packages = ["idna", "sys", "PyQt5", "numpy", "pydicom",
            "scipy", "time", "cv2", "imageio", "h5py",
            "qimage2ndarray" ]
options = {
    'build_exe': {    
        'packages':packages,
    },    
}

setup(
    name = "SELMA",
    options = options,
    version = "0.2.6.2",
    description = 'Trial-ready Small Vessel MRI Markers',
    executables = executables
)