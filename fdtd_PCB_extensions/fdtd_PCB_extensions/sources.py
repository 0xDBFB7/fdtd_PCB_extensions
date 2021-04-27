from fdtd_PCB_extensions import X,Y,Z
from scipy.constants import mu_0, epsilon_0
from math import sin, pi, pow, exp, sqrt


#need a function that slices including the PML margin

def gaussian_derivative_pulse(pcb, dt, beta):

    #fixme: normalize
    t = pcb.time
    s = 4.0/(beta*dt)
    b = (t - beta*dt)
    exponent_1 = -1.0*((s)**2.0)*((b)**2.0)
    part_one = exp(exponent_1)
    part_two = -2.0*(s**2.0)*b
    return part_one * part_two


class Port:
    def __init__(self, pcb, SPICE_net, F_x, F_y):

        self.SPICE_net = SPICE_net

        self.N_x = pcb.xy_margin+int((F_x)/pcb.cell_size)
        self.N_y = pcb.xy_margin+int((F_y)/pcb.cell_size)

        if(not pcb.copper_mask[self.N_x, self.N_y, pcb.component_plane_z]):
            raise Exception("Port added without copper above.")

        self.voltage = 0.0
        self.current = 0.0
        self.dV_dt = 0.0
        self.voltage_history = []
        self.current_history = []

        pcb.copper_mask[self.N_x,self.N_y,pcb.ground_plane_z_top:pcb.component_plane_z-1] = 1 #make a conductor
        pcb.copper_mask[self.N_x,self.N_y,pcb.component_plane_z:pcb.component_plane_z] = 1 #make a conductor

    def get_current(self, pcb):
        #really needs to be fixed!

        #[Luebbers 1996 1992]

        z_slice = slice(pcb.component_plane_z-1,pcb.component_plane_z)

        current = (((pcb.grid.H[self.N_x,self.N_y-1,z_slice,X]/sqrt(mu_0))-
                    (pcb.grid.H[self.N_x,self.N_y,z_slice,X]/sqrt(mu_0)))*pcb.cell_size)
        current += (((pcb.grid.H[self.N_x,self.N_y,z_slice,Y]/sqrt(mu_0))-
                    (pcb.grid.H[self.N_x-1,self.N_y,z_slice,Y]/sqrt(mu_0)))*pcb.cell_size)

        current = float(current.cpu())
        # current /= (pcb.cell_size)

        #field normalized according to Flaport's thesis, chapter 4.1.6

        # account for Yee cell inaccuracies [Fang 1994].
        z_slice_2 = slice(pcb.component_plane_z-2,pcb.component_plane_z-1)

        current_2 = (((pcb.grid.H[self.N_x,self.N_y-1,z_slice_2,X]/sqrt(mu_0))-
                    (pcb.grid.H[self.N_x,self.N_y,z_slice_2,X]/sqrt(mu_0)))*pcb.cell_size)
        current_2 += (((pcb.grid.H[self.N_x,self.N_y,z_slice_2,Y]/sqrt(mu_0))-
                    (pcb.grid.H[self.N_x-1,self.N_y,z_slice_2,Y]/sqrt(mu_0)))*pcb.cell_size)
        # current
        current_2 = float(current_2.cpu())
        # current_2 /= (pcb.cell_size)


        current = ((current+current_2) / 2.0)

        return current

    def set_voltage(self, pcb, voltage):
        z_slice = slice(pcb.component_plane_z-1,pcb.component_plane_z)

        pcb.grid.E[self.N_x,self.N_y,z_slice,Z] = sqrt(epsilon_0) * (voltage / (pcb.cell_size))


    def get_voltage(self, pcb):
        z_slice = slice(pcb.component_plane_z-1,pcb.component_plane_z)

        return (pcb.grid.E[self.N_x,self.N_y,z_slice,Z]/sqrt(epsilon_0))*(pcb.cell_size)


# see http://www.cse.yorku.ca/~kosta/CompVis_Notes/fourier_transform_Gaussian.pdf
# http://www.sci.utah.edu/~gerig/CS7960-S2010/handouts/04%20Gaussian%20derivatives.pdf

def normalized_gaussian_pulse(pcb,fwhm):
    t = pcb.time
    sigma = fwhm/2.355
    return exp(-((t**2.0)/(2.0*(sigma**2.0))))

def normalized_gaussian_derivative_pulse(pcb,fwhm):
    t = pcb.time
    sigma = fwhm/2.355
    return (exp((1.0/2.0) - (t**2.0)/(2.0*sigma**2.0))*t)/sigma

###############################################################################

def gaussian_derivative_pulse(pcb, dt, beta):
    #have to normalize
    t = pcb.time
    s = 4.0/(beta*dt)
    b = (t - beta*dt)
    exponent_1 = -1.0*((s)**2.0)*((b)**2.0)
    part_one = exp(exponent_1)
    part_two = -2.0*(s**2.0)*b
    return part_one * part_two

#scipy.stats.norm.pdf(x, mu, sigma)*(mu - x)/sigma**2

def compute_all_voltages(pcb):
    for port in pcb.component_ports:
        # port.voltage = self.e_field_integrate(port, self.reference_port)
        # Perfect Electrical Conductors have zero internal electric field

        port.voltage = float(sum(pcb.grid.E[port.N_x,port.N_y,pcb.component_plane_z-3:pcb.component_plane_z-2,Z])*pcb.cell_size)
        port.voltage_history.append(port.voltage)

def compute_deltas(pcb):
    # delta_vs = []
    max_delta_V = 0.0
    for idx, port in enumerate(pcb.component_ports):

        #
        # self.grid.E[port.N_x,port.N_y,self.ground_plane_z_top:self.component_plane_z-3,Z] = 0 #make a conductor
        # self.grid.E[port.N_x,port.N_y,self.component_plane_z-2:self.component_plane_z,Z] = 0 #make a conductor
        #
        # C = epsilon_0*(self.cell_size**2.0)*(self.substrate_permittivity)/(1.0*self.cell_size)
        # # print(C)
        #
        # # C *= 10.0
        #
        # dvdt = (port.current / C)
        #
        # port.voltage += (dvdt * self.grid.time_step)
        #
        # self.grid.E[port.N_x,port.N_y,self.component_plane_z-3:self.component_plane_z-2,Z] = port.voltage / (self.cell_size)


        #equation 4, 5 in [Toland 1993]

        # a slightly simplified version is
        # https://www.eecs.wsu.edu/~schneidj/ufdtd/chap3.pdf, eq. 3.26
        # Aha! First we let the update occur normally, *then* we apply the J source, eq. 3.28 in the latter.
        # Toland uses a current averaging method
        # self.current = 1.0


        # scale_factor = (pcb.grid.time_step/(pcb.substrate_permittivity * 8.85e-12))

        z_slice = slice(pcb.component_plane_z-3,pcb.component_plane_z-2)
        permittivity = pcb.substrate_permittivity * 8.85e-12

        current_density = port.current/(pcb.cell_size*pcb.cell_size)

        dE_dt = 1.0 * (current_density/permittivity)

        port.dV_dt = dE_dt * pcb.cell_size

        if(abs(port.dV_dt) > max_delta_V):
            max_delta_V = abs(port.dV_dt)

        # self.grid.E[port.N_x,port.N_y,z_slice,Z] -=
        #
        #
        # E_n = self.grid.E[port.N_x,port.N_y,z_slice,Z]*perm_factor
        #
        # L_H =  ((self.grid.H[port.N_x,port.N_y-1,z_slice,X] - self.grid.H[port.N_x,port.N_y,z_slice,X]) / self.cell_size)
        # L_H += ((self.grid.H[port.N_x,port.N_y,z_slice,Y] - self.grid.H[port.N_x-1,port.N_y,z_slice,Y]) / self.cell_size)
        #
        # I = -1.0*(port.old_current+port.current)/(2.0*(self.cell_size**2.0))
        # print(E_n, L_H, I)
        # E_new =  E_n
        # E_new += L_H
        # E_new -= I
        #
        # E_new /= perm_factor
        #
        # self.grid.E[port.N_x,port.N_y,z_slice,Z] = E_new
        #
        # print("E_new",E_new)
        #
        # port.old_current = port.current
    return max_delta_V

def apply_deltas(pcb):
    for idx, port in enumerate(pcb.component_ports):
        port.voltage += (port.dV_dt * pcb.grid.time_step)

        pcb.grid.E[port.N_x,port.N_y,pcb.component_plane_z-3:pcb.component_plane_z-2,Z] = port.voltage / (pcb.cell_size)


def zero_conductor_fields(pcb):
    pcb.grid.E[pcb.copper_mask] = 0


# def compute_time_step(pcb, max_delta_V):


def just_FDTD_step(pcb):

    # compute_all_voltages(pcb)
    # max_delta_V = compute_deltas(pcb)
    # # voltage_tolerance = 0.05
    # # courant_time_step = 0.9 / (3*(3e8/pcb.cell_size))
    # # required_time_step = voltage_tolerance / max(max_delta_V, 1e-5) #avoid div0
    # # set_time_step(pcb, min(courant_time_step, required_time_step))
    #
    # # print("max_delta_V {:.3e}, | time_step: {:.3e} | * {:.3f}".format(max_delta_V, pcb.grid.time_step, pcb.grid.time_step*max_delta_V))
    # this is not at all correct. We need the difference in voltage between the two times
    #
    # apply_deltas(pcb)

    pcb.grid.update_E()

    zero_conductor_fields(pcb)

    # self.constrain_values()
    pcb.grid.update_H()

    pcb.grid.time_steps_passed += 1
    pcb.time += pcb.grid.time_step # the adaptive
    pcb.times.append(pcb.time)

def reset(pcb):
    for port in pcb.component_ports:
        port.voltage = 0
        port.current = 0
        port.voltage_history = []
        port.current_history = []

    pcb.grid.time_steps_passed = 0
    pcb.time = 0
    # pcb.times.append(pcb.time)

#
# def forcings(self):
#     for port in self.component_ports:
#     # if(current > 0.5
#     # port.voltage = np.clip(port.voltage, -40, 40)
#         port.current = np.clip(port.current, -10, 10)
#
# def to_taste(self):
#     #Using an adaptive timestep method as per [Ciampolini 1995]
#
#     z_slice = slice(self.component_plane_z-3,self.component_plane_z-2)
#
#     failsafe_port_voltages = []
#     failsafe_port_currents = []
#     failsafe_port_old_currents = []
#
#     for idx,port in enumerate(self.component_ports):
#         failsafe_port_voltages.append(self.grid.E[port.N_x,port.N_y,z_slice,Z].cpu())
#         failsafe_port_currents.append(port.current)
#         failsafe_port_old_currents.append(port.old_current)
#     # failsafe_ports = copy.deepcopy(self.component_ports)
#
#     delta_v = 0
#
#
#
#     # we know the dV/dt, just compute the timestep directly.
#
#     # this coefficient is somewhat tricky.
#     # higher, and the loop below will have to try more timesteps to find convergence.
#     # lower, and changes in required timestep will take longer to propagate.
#     self.set_time_step(self.grid.time_step*4.0)
#
#     # a better convergence metric would be useful.
#     while(True):
#
#         self.apply_all_currents()
#         self.compute_all_voltages()
#
#         delta_vs = [abs(failsafe_port_voltages[idx]-val.voltage) for idx,val in enumerate(self.component_ports)]
#         delta_v = max(delta_vs)
#         fastest_net = self.component_ports[delta_vs.index(delta_v)].SPICE_net
#         print("DV",delta_v)
#         # print("Delta V:" , delta_v)
#         convergence = delta_v < 0.1
#
#         if(convergence):
#             break
#         else:
#             self.set_time_step(self.grid.time_step*0.5)
#             print("Decreased timestep to " , self.grid.time_step)
#
#             for idx,port in enumerate(self.component_ports):
#                 self.grid.E[port.N_x:port.N_x+1,port.N_y:port.N_y+1,z_slice,Z] = failsafe_port_voltages[idx]
#                 print("AAAAAAAA",self.grid.E[port.N_x,port.N_y,z_slice,Z])
#                 port.current = failsafe_port_currents[idx]
#                 port.old_current = failsafe_port_old_currents[idx]
#
#         # prev_convergence = copy.copy(new_convergence)


def set_time_step(pcb, ts):
    pcb.grid.time_step = ts
    pcb.grid.courant_number = pcb.grid.time_step/(pcb.grid.grid_spacing / 3.0e8)
