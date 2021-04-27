#
# import sexpdata #hehe
#
# #
# # def _set_pdeathsig(sig=signal.SIGTERM):
# #     """help function to ensure once parent process exits, its childrent processes will automatically die
# #     """
# #     def callable():
# #         libc = ctypes.CDLL("libc.so.6")
# #         return libc.prctl(1, sig)
# #     return callable
#
#
# # Compiled ngspice 32 with
# # make clean
# #../configure --with-x --enable-xspice --disable-debug --enable-cider
# #--with-readline=yes --with-ngshared --enable-openmp --prefix=/home/arthurdent/Programs/ngspice-32/install/
# # then set export LIBNGSPICE=/home/arthurdent/Programs/ngspice-32/lib/lib/libngspice.so
# # had to compile twice; once with prefix lib and --ngshared,
# # and the other with prefix install and no ngshared
#
#     def error(self, i):
#         if i:
#             print("Error", i)
#             sys.exit("Spice error")
#
#     def init_SPICE(self, source_file):
#         ngspyce.source(source_file)
#
#
#
#     def set_spice_voltages(self):
#         for port in self.component_ports:
#             try:
#                 self.set_spice_voltage(port.SPICE_net, port.voltage)
#             except:
#                 print(f"No such source vs{port.SPICE_net}")
#
#     def get_spice_currents(self):
#         for port in self.component_ports:
#             try:
#                 port.current = self.get_spice_current(port.SPICE_net)
#             except:
#                 port.current = 0
#
#
#     def get_spice_current(self, SPICE_net):
#         try:
#             return ngspyce.vector('i(vs' + SPICE_net.lower() + ")")[-1]
#         except:
#             print(f"No such source vs{port.SPICE_net}")
#             return 0
#
#
#     def set_spice_voltage(self, SPICE_net, voltage):
#         ngspyce.cmd('alter vs' + SPICE_net.lower() + ' = ' + str(voltage))
#
#     def reset_spice(self):
#         # resets simulation without reloading file from disk
#         ngspyce.cmd('reset')
#         # self.error(ngspyce.cmd('altermod cstd cap = {}'.format(C)))
#
#     def run_spice_step(self):
#         # ngspyce.cmd('tran {} {} uic'.format(self.grid.time_step, self.grid.time_step))
#         ngspyce.cmd('tran 1p 1p uic'.format(self.grid.time_step, self.grid.time_step))
#         # WARNING ! THIS IS WRONG !
#         # for any non-linear circuit, this will produce incorrect results.
#         # with this combination of parts,
#         # ngspice refuses to sim at tstep < 1p.
#
#     def save_voltages(self):
#         for port in self.component_ports:
#             port.voltage_history.append(port.voltage)
#             port.current_history.append(port.current)
#
#
#
# #
# # def _set_pdeathsig(sig=signal.SIGTERM):
# #     """help function to ensure once parent process exits, its childrent processes will automatically die
# #     """
# #     def callable():
# #         libc = ctypes.CDLL("libc.so.6")
# #         return libc.prctl(1, sig)
# #     return callable
#
#     def munge_SPICE_nets(self, pads, spice_file_string, skip_source_creation_names):
#         '''
#         Renames SPICE nets and pad nets so each pad is only connected to its port, not other components,
#         then inserts the voltage sources needed for SPICE<->FDTD coupling.
#
#         Some pads could already have sources defined; we skip source creation for these.
#         '''
#
#         spice_file_array = spice_file_string.splitlines()
#
#         for pad_idx,pad in enumerate(pads):
#             new_net_name = "NET"+pad["reference"]+str(pad["mod_pad_idx"])
#             if(not pad["reference"] in skip_source_creation_names):
#                 spice_file_array.insert(spice_file_array.index('//start vsources')+1,"Vs"+new_net_name + " " + new_net_name + " 0 0")
#
#             for idx, line in enumerate(spice_file_array[0:spice_file_array.index('//start vsources')]):
#                 line_array = line.split()
#                 if(line_array and not "Vs" in line_array[0] and pad["reference"] in line_array[0]):
#                     line_net_idx = line_array.index(pad["net"])
#                     # new_net_name = pad["net"]+str(pad_idx)
#                     line_array[line_net_idx] = new_net_name
#
#                     spice_file_array[idx] = " ".join(line_array)
#
#                     break
#
#             pads[pad_idx]["net"] = new_net_name
#
#         return pads, "\n".join(spice_file_array)
#
#     def insert_ports(self, pads):
#         for pad_idx,pad in enumerate(pads):
#             self.component_ports.append(Port(self, pad["net"], pad['x'], pad['y']))
#
#         self.create_source_vias()
#         # ngspyce.__init__("")
#         # ngspyce.source('/tmp/wideband_LO_mod.cir')
#
#     # def constrain_values(self):
#     #     for port in self.component_ports:
#     #         if(current > 0.5
#             # port.voltage = np.clip(port.voltage, -40, 40)
#             # port.current = np.clip(port.current, -1, 1)
#
#
#
#     self.reset_spice()
#     self.set_spice_voltages()
#     self.run_spice_step()
#     self.get_spice_currents()
#     self.forcings()
#     ngspyce.cmd("destroy all")
