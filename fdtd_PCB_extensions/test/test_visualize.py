import pytest
import fdtd_PCB_extensions as fd
from test_fixtures import setup_basic_grid



def test_vtk_dump(setup_basic_grid):
    pcb = setup_basic_grid

    DUMP_FOLDER = '../../run/dumps/'
    DUMP_FOLDER += "test"

    fd.dump_to_vtk(pcb, DUMP_FOLDER, 0)
