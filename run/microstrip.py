# import torch
# import numpy as np
# import gc
# torch.cuda.empty_cache()
#
# gc.collect()

# np.seterr(all='raise')
# torch.autograd.set_detect_anomaly(True)
import fdtd_PCB_extensions as fd
from fdtd_PCB_extensions import fdtd
from fdtd_PCB_extensions import X,Y,Z, gaussian_derivative_pulse
from scipy.constants import mu_0, epsilon_0
import scipy.constants
from math import sin, pi, pow, exp, sqrt
import time
import os
import matplotlib.pyplot as plt
import copy
from scipy.signal import gausspulse
import dill
from pytexit import py2tex
import pickle

import numpy as np



fdtd.set_backend("torch.cuda.float32")


# fdtd.set_backend("numpy")

#include store.py
import sys
sys.path.append('/home/arthurdent/covidinator/electronics/')
import store

os.system("rm dumps/*")
os.system("rm data/*")

#Polycarb. permittivity @ 10 GHz: 2.9 [10.6028/jres.071C.014] - conductivity is very low, no need for absorb.
#Water permittivity @ 10 GHz: 65 - use AbsorbingObject

substrate_thickness = 0.8e-3
substrate_dielectric_constant = 4.4


microstrip_width = 1.4e-3
microstrip_length = 10e-3

ribbon_dielectric_constant = 2.9
ribbon_thickness = 1.6e-3
ribbon_length = 10e-3

cover_tape_thickness = 0.1e-3

fluid_dielectric_constant = 65
fluid_thickness = (0.14+0.1+0.14) * 1e-3
fluid_width = 0.8e-3

pcb = fd.PCB(0.00005, xy_margin=15, z_margin=15)
fd.initialize_grid(pcb,int((10e-3)/pcb.cell_size),int((microstrip_length)/pcb.cell_size),
                                int(0.0025/pcb.cell_size), courant_number = 0.4)

fd.create_planes(pcb, 0.032e-3, 6e7)
fd.create_substrate(pcb, substrate_thickness, substrate_dielectric_constant, 0.02, 9e9)


z_slice = slice(pcb.component_plane_z,(pcb.component_plane_z+1))


centerline = int((5e-3 / pcb.cell_size ) / 2.0) + pcb.xy_margin


#wipe copper
pcb.copper_mask[:, :, z_slice] = 0
pcb.copper_mask[:,:,pcb.ground_plane_z_top:pcb.component_plane_z] = 0 # vias

microstrip_gap = 3e-3 # distance to ground plane
#microstrip line
m_w_N = int((microstrip_width/2)/pcb.cell_size)
pcb.copper_mask[centerline-m_w_N:centerline+m_w_N, \
                    pcb.xy_margin:int(pcb.xy_margin+(int(microstrip_length/pcb.cell_size))), z_slice] = 1
# pcb.copper_mask[pcb.xy_margin:centerline-m_w_N-int(microstrip_gap/pcb.cell_size), \
#                     pcb.xy_margin:int(pcb.xy_margin+(int(microstrip_length/pcb.cell_size))), z_slice] = 1
pcb.copper_mask[centerline+m_w_N+int(microstrip_gap/pcb.cell_size):-pcb.xy_margin, \
                    pcb.xy_margin:int(pcb.xy_margin+(int(microstrip_length/pcb.cell_size))), z_slice] = 1


#cover tape
pcb.grid[pcb.xy_margin:-pcb.xy_margin, pcb.xy_margin:-pcb.xy_margin, \
            (pcb.component_plane_z+1):(pcb.component_plane_z+1+int(cover_tape_thickness/pcb.cell_size))] = fdtd.Object(permittivity=ribbon_dielectric_constant, name="cover_tape")


#polycarb ribbon
pcb.grid[pcb.xy_margin:-pcb.xy_margin, pcb.xy_margin:-pcb.xy_margin, \
        (pcb.component_plane_z+1+int(cover_tape_thickness/pcb.cell_size)):\
            (pcb.component_plane_z+1+int(ribbon_thickness/pcb.cell_size))] = fdtd.Object(permittivity=ribbon_dielectric_constant, name="ribbon")




#fluid
conductivity_scaling = 1.0/(pcb.cell_size / epsilon_0) #again, flaport's thesis.
f_w_N = int((fluid_width/2)/pcb.cell_size)
pcb.grid[centerline-f_w_N:centerline+f_w_N, pcb.xy_margin:-pcb.xy_margin, \
            (pcb.component_plane_z+1+int(cover_tape_thickness/pcb.cell_size)):(pcb.component_plane_z+1+\
                                    int(cover_tape_thickness/pcb.cell_size))+int(fluid_thickness/pcb.cell_size)] \
                    = fdtd.AbsorbingObject(conductivity=0.010*conductivity_scaling, permittivity=fluid_dielectric_constant, name="fluid")


fd.dump_to_vtk(pcb,'dumps/test',0)
pcb.component_ports = [] # wipe ports
pcb.component_ports.append(fd.Port(pcb, 0, int((5e-3 / pcb.cell_size ) / 2.0)*pcb.cell_size, (microstrip_length*pcb.cell_size)-pcb.cell_size))
pcb.component_ports.append(fd.Port(pcb, 0, int((5e-3 / pcb.cell_size ) / 2.0)*pcb.cell_size, pcb.cell_size))




print_step = 500
dump_step = 2e-12

prev_dump_time = 0

f = 8e9
while(pcb.time < (2.0 * 2.0 * pi * f)):

    # # source_voltage = gaussian_derivative_pulse(pcb, 4e-12, 32)/(26.804e9/100.0)
    # source_resistive_voltage = (50.0 * pcb.component_ports[0].get_current(pcb))
    # pcb.component_ports[0].set_voltage(pcb, source_voltage + source_resistive_voltage)
    #
    # source_voltage = 0
    # source_resistive_voltage = (50.0 * pcb.component_ports[1].get_current(pcb))
    # pcb.component_ports[1].set_voltage(pcb, source_voltage + source_resistive_voltage)
    #
    # print(source_voltage)
    # print(pcb.component_ports[0].get_current(pcb))
    # print(pcb.component_ports[1].get_current(pcb))

    source_voltage = sin(pcb.time * 2.0 * pi * f)
    print(source_voltage)

    z_slice = slice(pcb.component_plane_z-1,pcb.component_plane_z)

    current = pcb.component_ports[0].get_current(pcb)
    #[Luebbers 1996]

    source_resistive_voltage = (50.0 * current)


    pcb.component_ports[0].set_voltage(pcb, source_voltage + source_resistive_voltage)

    pcb.component_ports[1].set_voltage(pcb, 0 + (pcb.component_ports[1].get_current(pcb)*50.0))


    print(current)

    if((dump_step and abs(pcb.time-prev_dump_time) > dump_step) or pcb.grid.time_steps_passed == 0):
        #paraview gets confused if the first number isn't zero.
        fd.dump_to_vtk(pcb,'dumps/test',pcb.grid.time_steps_passed)
        prev_dump_time = pcb.time

    fd.just_FDTD_step(pcb)
