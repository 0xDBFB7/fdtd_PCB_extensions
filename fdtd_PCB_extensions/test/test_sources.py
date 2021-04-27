import fdtd_PCB_extensions as fd
from fdtd_PCB_extensions import X,Y,Z
from test_fixtures import setup_basic_grid




def test_ports(setup_basic_grid):
    pcb = setup_basic_grid

    # pcb.copper_mask[]

    print(pcb)
    pcb.component_ports.append(fd.Port(pcb, 0, 0, 0))
    pcb.dump_to_vtk('test/test_ports/dumps/test',0)
