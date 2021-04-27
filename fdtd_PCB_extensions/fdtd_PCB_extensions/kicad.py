
def initialize_kicad_and_spice(self, kicad_filename,SPICE_filename, SPICE_modified_filename, skip_source_creation_names):
    pads = self.parse_kicad_pcb(kicad_filename)
    spice_file_string = open(SPICE_filename, 'r').read()
    pads, spice_file_string = self.munge_SPICE_nets(pads, spice_file_string, skip_source_creation_names)
    self.insert_ports(pads)

    with open(SPICE_modified_filename, 'w') as file:
        file.write(spice_file_string)

    self.init_SPICE(SPICE_modified_filename)
    self.reset_spice()

def parse_kicad_pcb(self, pcb_filename):
    '''
    given a .kicad_pcb filename, returns a list of module_reference, abs pad_x, abs pad_y, net
    '''

    pcb_string = open(pcb_filename, 'r').read()
    pcb_data = sexpdata.loads(pcb_string)
    setup = [i for i in pcb_data if isinstance(i, list) and i[0] == sexpdata.Symbol('setup')][0]
    aux_origin = [i for i in setup if isinstance(i, list) and i[0] == sexpdata.Symbol('aux_axis_origin')][0]
    aux_origin_x = float(aux_origin[1])*1e-3
    aux_origin_y = float(aux_origin[2])*1e-3

    pads = []

    modules = [i for i in pcb_data if isinstance(i, list) and i[0] == sexpdata.Symbol('module')]
    for module in modules:
        module_at = [i for i in module if isinstance(i, list) and i[0] == sexpdata.Symbol('at')][0]
        module_x = float(module_at[1])*1e-3
        module_y = float(module_at[2])*1e-3
        module_angle = None

        try: #some modules don't have an angle
            module_angle = (float(module_at[3])/360.0)*2.0*pi
        except:
            pass

        module_reference = [i for i in module if isinstance(i, list) and len(i) >= 2 and i[1] == sexpdata.Symbol('reference')][0][2].value()
        for pad_idx, pad in enumerate([i for i in module if isinstance(i, list) and i[0] == sexpdata.Symbol('pad')]):
            pad_at = [i for i in pad if isinstance(i, list) and i[0] == sexpdata.Symbol('at')][0]

            pad_relative_x = float(pad_at[1])*1e-3
            pad_relative_y = float(pad_at[2])*1e-3

            if(module_angle): #some modules don't have an angle
                pad_rotated_vector_x = pad_relative_x*cos(module_angle) - pad_relative_y*sin(module_angle)
                pad_rotated_vector_y = pad_relative_x*sin(module_angle) + pad_relative_y*cos(module_angle)
                pad_x = module_x + pad_rotated_vector_x - aux_origin_x
                pad_y = module_y + pad_rotated_vector_y - aux_origin_y
            else:
                pad_x = module_x + pad_relative_x - aux_origin_x
                pad_y = module_y + pad_relative_y - aux_origin_y

            net = [i for i in pad if isinstance(i, list) and i[0] == sexpdata.Symbol('net')][0][2]
            try:
                net = net.value() #sometimes the net is a sexpdata.Symbol().
            except:
                pass
            net = net.replace("(", "_")
            net = net.replace(")", "_")
            pads.append({"reference": module_reference, "x": pad_x, "y": pad_y, "net": net, "mod_pad_idx": pad_idx})
            # self.component_ports.append(Port(self, , ))


    return pads
