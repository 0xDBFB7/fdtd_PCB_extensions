import fdtd_PCB_extensions as fd
from fdtd_PCB_extensions import fdtd
from fdtd_PCB_extensions import X,Y,Z, gaussian_derivative_pulse
from scipy.constants import mu_0, epsilon_0
import scipy.constants
import numpy as np
from math import sin, pi, pow, exp, sqrt
import time
import os
import matplotlib.pyplot as plt
import copy
from scipy.signal import gausspulse
import dill
from pytexit import py2tex
import pickle
# fdtd.set_backend("torch.float64")
fdtd.set_backend("torch.cuda.float32")
# fdtd.set_backend("numpy")

#include store.py
import sys
sys.path.append('/home/arthurdent/covidinator/electronics/')
import store

#Polycarb. permittivity @ 10 GHz: 2.9 [10.6028/jres.071C.014] - conductivity is very low, no need for absorb.
#Water permittivity @ 10 GHz: 65 - use AbsorbingObject

#analytic 8 GHz patch antenna - ~240 ohms at the edge
patch_width = 11.4e-3
patch_length = 8.7e-3
feed_length = 5e-3
substrate_thickness = 0.8e-3
dielectric_constant = 4.4

#python -u U_patch_antenna_designer.py | tee stdout.log

#
# patch_width =  22.26e-3
# patch_length = 16.95e-3
# feed_length = 5e-3
# substrate_thickness = 1.6e-3
# A good reference design on 1.6 mm FR4 is 10.1109/ATSIP.2016.7523197 [Werfelli 2016]
# return loss -19.5 dB, VSWR 1.237, impedance
# I'm not convinced that this ref. design is correct.


# [Samaras 2004]
# patch_width =  59.4e-3
# patch_length = 40.4e-3
# feed_length = 0e-3
# substrate_thickness = 1.2e-3
# dielectric_constant = 2.42
#1
pcb = fd.PCB(0.0002, xy_margin=25, z_margin=25)
fd.initialize_grid(pcb,int((patch_width)/pcb.cell_size),int((patch_length+feed_length)/pcb.cell_size),
                                int(0.005/pcb.cell_size), courant_number = None)

fd.create_planes(pcb, 0.032e-3, 6e7)
fd.create_substrate(pcb, substrate_thickness, dielectric_constant, 0.02, 9e9)

#900/126

def create_patch_antenna(pcb, patch_width, patch_length):
    MICROSTRIP_FEED_WIDTH = 3e-3
    MICROSTRIP_FEED_LENGTH = 5e-3

    z_slice = slice(pcb.component_plane_z,(pcb.component_plane_z+1))

    #wipe copper
    pcb.copper_mask[:, :, z_slice] = 0
    pcb.copper_mask[:,:,pcb.ground_plane_z_top:pcb.component_plane_z] = 0 # vias

    #rectangle
    p_N_x = int(patch_width / pcb.cell_size)
    p_N_y = int(patch_length / pcb.cell_size)
    pcb.copper_mask[pcb.xy_margin:pcb.xy_margin+p_N_x, pcb.xy_margin:pcb.xy_margin+p_N_y, z_slice] = 1

    # #feedport
    # fp_N_x = int(MICROSTRIP_FEED_WIDTH/pcb.cell_size)
    # fp_N_y = int(MICROSTRIP_FEED_LENGTH/pcb.cell_size)
    # pcb.copper_mask[pcb.xy_margin+(p_N_x//2 - (fp_N_x//2)):pcb.xy_margin+(p_N_x//2 + (fp_N_x//2)),  \
    #                                     pcb.xy_margin+p_N_y:pcb.xy_margin+p_N_y+fp_N_y, z_slice] = 1


    probe_position = (p_N_y-1)

    pcb.component_ports = [] # wipe ports
    pcb.component_ports.append(fd.Port(pcb, 0, ((p_N_x//2)-1)*pcb.cell_size, probe_position*pcb.cell_size))

def create_U_patch_antenna(patch_width, patch_length, slots, probe_position):
#     # U-patch antenna from 10.1109/LAWP.2007.914122.
    z_slice = slice(pcb.component_plane_z,(pcb.component_plane_z+1))

    #wipe copper
    pcb.copper_mask[:, :, z_slice] = 0
    pcb.copper_mask[:,:,pcb.ground_plane_z_top:pcb.component_plane_z] = 0 # vias

    #rectangle
    p_N_x = int(patch_width / pcb.cell_size)
    p_N_y = int(patch_length / pcb.cell_size)
    pcb.copper_mask[pcb.xy_margin:pcb.xy_margin+p_N_x, pcb.xy_margin:pcb.xy_margin+p_N_y, z_slice] = 1

    # #feedport
    # fp_N_x = int(MICROSTRIP_FEED_WIDTH/pcb.cell_size)
    # fp_N_y = int(MICROSTRIP_FEED_LENGTH/pcb.cell_size)
    # pcb.copper_mask[pcb.xy_margin+(p_N_x//2 - (fp_N_x//2)):pcb.xy_margin+(p_N_x//2 + (fp_N_x//2)),  \
    #                                     pcb.xy_margin+p_N_y:pcb.xy_margin+p_N_y+fp_N_y, z_slice] = 1

    # U slot
    pcb.copper_mask[pcb.xy_margin:pcb.xy_margin+p_N_x, pcb.xy_margin:pcb.xy_margin+p_N_y, z_slice] = 1
    pcb.copper_mask[pcb.xy_margin:pcb.xy_margin+p_N_x, pcb.xy_margin:pcb.xy_margin+p_N_y, z_slice] = 1


    probe_position = (p_N_y-1)

    pcb.component_ports = [] # wipe ports
    pcb.component_ports.append(fd.Port(pcb, 0, ((p_N_x//2)-1)*pcb.cell_size, probe_position*pcb.cell_size))




#500 ohms

def sim_VSWR(pcb):
    print_step = 500
    dump_step = None

    # print(pcb.grid.time_step)

    prev_dump_time = 0

    # end_time = 1500e-12

    pcb.grid.reset()
    fd.reset(pcb)


    voltages = np.array([])

    currents = np.array([])
    currents_2 = np.array([])

    c_spect_prev = 0
    while(True):

        port = pcb.component_ports[0]

        source_voltage = gaussian_derivative_pulse(pcb, 4e-12, 32)/(26.804e9/100.0)

        z_slice = slice(pcb.component_plane_z-1,pcb.component_plane_z)


        current = (((pcb.grid.H[port.N_x,port.N_y-1,z_slice,X]/sqrt(mu_0))-
                    (pcb.grid.H[port.N_x,port.N_y,z_slice,X]/sqrt(mu_0)))*pcb.cell_size)
        current += (((pcb.grid.H[port.N_x,port.N_y,z_slice,Y]/sqrt(mu_0))-
                    (pcb.grid.H[port.N_x-1,port.N_y,z_slice,Y]/sqrt(mu_0)))*pcb.cell_size)
        # current

        current = current.cpu()
        # current /= mu_0*(pcb.cell_size/pcb.grid.time_step)

        #[Luebbers 1996]

        source_resistive_voltage = (50.0 * current) / (pcb.cell_size)


        pcb.grid.E[port.N_x,port.N_y,z_slice,Z] = sqrt(epsilon_0) * (source_voltage / (pcb.cell_size) + source_resistive_voltage)



        # account for Yee cell inaccuracies [Fang 1994].
        z_slice_2 = slice(pcb.component_plane_z-2,pcb.component_plane_z-1)

        current_2 = (((pcb.grid.H[port.N_x,port.N_y-1,z_slice_2,X]/sqrt(mu_0))-
                    (pcb.grid.H[port.N_x,port.N_y,z_slice_2,X]/sqrt(mu_0)))*pcb.cell_size)
        current_2 += (((pcb.grid.H[port.N_x,port.N_y,z_slice_2,Y]/sqrt(mu_0))-
                    (pcb.grid.H[port.N_x-1,port.N_y,z_slice_2,Y]/sqrt(mu_0)))*pcb.cell_size)
        # current
        current_2 = current_2.cpu()
        # current_2 /= mu_0*(pcb.cell_size/pcb.grid.time_step)




        if((dump_step and abs(pcb.time-prev_dump_time) > dump_step) or pcb.grid.time_steps_passed == 0):
            #paraview gets confused if the first number isn't zero.
            fd.dump_to_vtk(pcb,'dumps/test',pcb.grid.time_steps_passed)
            prev_dump_time = pcb.time

        fd.just_FDTD_step(pcb)

        if(pcb.grid.time_steps_passed % print_step == 0 and pcb.grid.time_steps_passed):
            print(sum(abs(currents[-700:-1]))/700.0, pcb.grid.time_steps_passed)


            c_spectrum = abs(np.fft.fft(currents))
            spectrum_freqs = np.fft.fftfreq(len(currents), d=pcb.grid.time_step)
            # sample_freq = np.abs(spectrum_freqs - 1e9).argmin()
            sample_freq = 10
            print(abs(c_spectrum[sample_freq] - c_spect_prev))
            # if(
            c_spect_prev = c_spectrum[sample_freq]


        voltages = np.append(voltages, source_voltage)
        currents = np.append(currents, current)
        currents_2 = np.append(currents_2, current_2)
        #
        # if(sum(abs(currents[-700:-1]))/700.0 < max(abs(currents))*0.0005 and len(currents) > 700):
        #     # the key phrase here is "after all transients have dissipated."
        #     #they use 2000 timesteps at 1.8 ps each. We find depending on the cirumstance, 7000
        #     break

        if(len(currents) > 10000):
            break

    print("=========== Finished! ============")

    voltages = np.array(voltages)
    currents = np.array(currents)

    return voltages, currents, currents_2


create_patch_antenna(pcb, patch_width, patch_length)

# create_U_patch_antenna(pcb, patch_width, patch_length)

filename = 'globalsave.pkl'
try:
    dill.load_session(filename)
except:
    os.system("rm dumps/*")
    os.system("rm data/*")
    voltages, currents, currents_2 = sim_VSWR(pcb)
    dill.dump_session(filename)

desired_res = 300 #100 points below F_max
fft_F_max = 15e9
required_length = int(desired_res / (fft_F_max * pcb.grid.time_step))
print(required_length)


voltages = np.pad(voltages, (0, required_length), 'edge')
currents = np.pad(currents, (0, required_length), 'edge')
currents_2 = np.pad(currents_2, (0, required_length), 'edge')

times_padded = np.pad(pcb.times, (0, required_length), 'edge')

# currents = currents[len(times_padded)//2:-1]
# currents_2 = currents_2[len(times_padded)//2:-1]
# times_padded = times_padded[len(times_padded)//2:-1]

# factor of 50000000



voltage_spectrum = np.fft.fft(voltages)

current_spectrum = np.fft.fft(currents)
current_spectrum_2 = np.fft.fft(currents_2)
#
# voltage_spectrum *= np.max(abs(voltages))/np.max(abs(voltage_spectrum)) # normalize to 1 - why?
# current_spectrum *= np.max(abs(currents))/np.max(abs(current_spectrum)) # why?

# spectrum_freqs = np.fft.fftfreq(len(voltages), d=pcb.time/len(voltages))
spectrum_freqs = np.fft.fftfreq(len(voltages), d=pcb.grid.time_step)

# return spectrum_freqs, voltage_spectrum, current_spectrum

begin_freq = np.abs(spectrum_freqs - 1e9).argmin()
end_freq = np.abs(spectrum_freqs - 15e9).argmin()

plt.plot(times_padded, voltages)

plt.savefig('/tmp/voltages.svg')
plt.figure()
plt.plot(times_padded, currents)
plt.savefig('/tmp/currents.svg')
plt.figure()
plt.plot(spectrum_freqs[begin_freq:end_freq], abs(voltage_spectrum[begin_freq:end_freq]), label="volt")
plt.plot(spectrum_freqs[begin_freq:end_freq], abs(current_spectrum[begin_freq:end_freq]), label="curr")
plt.savefig('/tmp/spectrum.svg')
plt.legend()
# power_spectrum = -1.0*((voltage_spectrum[begin_freq:end_freq]*np.conj(current_spectrum[begin_freq:end_freq])).real)
# power_spectrum /= np.linalg.norm(power_spectrum)
# plt.plot(spectrum_freqs[begin_freq:end_freq],power_spectrum)

plt.figure()

# Z0 = scipy.constants.physical_constants['characteristic impedance of vacuum'][0]

impedance_spectrum = (abs(2.0*voltage_spectrum/(current_spectrum+current_spectrum_2))) / 2.0

plt.plot(spectrum_freqs[begin_freq:end_freq],impedance_spectrum[begin_freq:end_freq])
# plt.plot(spectrum_freqs[begin_freq:end_freq],impedance_spectrum[begin_freq:end_freq])
plt.savefig('/tmp/impedance_spectrum.svg')
# # plt.plot(spectrum_freqs,(voltage_spectrum/current_spectrum))
# plt.plot(spectrum_freqs[begin_freq:end_freq],(voltage_spectrum[begin_freq:end_freq]/current_spectrum[begin_freq:end_freq]).real)
# plt.plot(spectrum_freqs[begin_freq:end_freq],(voltage_spectrum[begin_freq:end_freq]/current_spectrum[begin_freq:end_freq]).imag)

plt.draw()
plt.pause(0.001)
#
# print("Z: ", impedance_spectrum[np.abs(spectrum_freqs - 2.3e9).argmin()])

files = ['/tmp/voltages.svg', '/tmp/currents.svg', '/tmp/spectrum.svg', '/tmp/impedance_spectrum.svg', "U_patch_antenna_designer.py", "stdout.log"]
store.ask(files)





# for port in pcb.component_ports:
#     np.savetxt("data/"+str(port.SPICE_net)+".csv", np.array(port.voltage_history).reshape(-1, 1), delimiter=",",fmt='%10.5f')
#
# np.savetxt("data/times.csv", np.array(pcb.times).reshape(-1, 1), delimiter=",",fmt='%10.5f')
