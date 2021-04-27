import fdtd

from cairosvg import svg2png
import lxml.etree as etree
from PIL import Image
import io
import math
from pyevtk.hl import gridToVTK
from math import pi, ceil, cos, sin, log, sqrt
from scipy.constants import mu_0,epsilon_0
import numpy as np
import torch

from importlib import reload

import gc


# import subprocess
import sys
# import signal

import copy

# import ngspyce
# from ngspyce.sharedspice import *


from fdtd.backend import NumpyBackend
from fdtd.backend import backend as bd


from numpy import array
import fdtd

from cairosvg import svg2png
import lxml.etree as etree
from PIL import Image
import io
import math
from math import pi, ceil, cos, sin, log
from scipy.constants import mu_0,epsilon_0
import numpy as np
import torch

from importlib import reload

import gc


# import subprocess
import sys
# import signal

import copy

# import ngspyce
# from ngspyce.sharedspice import *

from numpy import array

# from pykicad.pcb import *
# from pykicad.module import * unfortunately, got an error immediately with this. probably for a different version of kicad.



X = 0
Y = 1
Z = 2

class PCB:
    def __init__(self, cell_size, z_height=2e-3, xy_margin=15, z_margin=11, pml_cells=10):

        self.time = 0
        self.grid = None
        self.cell_size = cell_size

        self.z_height = z_height
        self.xy_margin = xy_margin
        self.z_margin = z_margin

        self.pml_cells = pml_cells

        self.ground_plane_z_top = None
        self.component_plane_z = None

        # self.reference_port = None
        self.component_ports = []
        self.substrate_permittivity = None

        self.copper_mask = None

        self.times = []
        self.time_step_history = []
