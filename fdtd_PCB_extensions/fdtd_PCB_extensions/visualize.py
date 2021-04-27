from pyevtk.hl import gridToVTK
from .PCB import *
from math import pi, ceil, cos, sin, log, sqrt
from scipy.constants import mu_0,epsilon_0

def E_magnitude(E):
    return np.sqrt(E[:,:,:,X]**2.0 + E[:,:,:,Y]**2.0 + E[:,:,:,Z]**2.0) / sqrt(epsilon_0)


def dump_to_vtk(pcb, filename, iteration, Ex_dump=False, Ey_dump=False, Ez_dump=False, Emag_dump=True, objects_dump=True, ports_dump=True):
    '''
    Extension is automatically chosen, you don't need to supply it

    thanks
    https://pyscience.wordpress.com/2014/09/06/numpy-to-vtk-converting-your-numpy-arrays-to-vtk-arrays-and-files/
    https://bitbucket.org/pauloh/pyevtk/src/default/src/hl.py

    Paraview needs a threshold operation to view the objects correctly.

    '''


    x = np.linspace(0, pcb.cell_size*pcb.grid.Nx, pcb.grid.Nx+1) #there might be an off-by-one error here.
    y = np.linspace(0, pcb.cell_size*pcb.grid.Ny, pcb.grid.Ny+1)
    z = np.linspace(0, pcb.cell_size*pcb.grid.Nz, pcb.grid.Nz+1)

    cellData = {}

    if(not isinstance(fdtd.backend, NumpyBackend)):
        E_copy = pcb.grid.E.cpu()
        cu_mask = pcb.copper_mask.cpu().numpy()
    else:
        E_copy = pcb.grid.E
        cu_mask = pcb.copper_mask

    if(objects_dump):
        objects = np.zeros_like(E_copy[:,:,:,X])
        for obj in pcb.grid.objects:
            if(hasattr(obj.permittivity,'cpu')):
                try:
                    objects[obj.x.start:obj.x.stop, obj.y.start:obj.y.stop, obj.z.start:obj.z.stop] = obj.permittivity.cpu().numpy()
                except:
                    objects[obj.x.start:obj.x.stop, obj.y.start:obj.y.stop, obj.z.start:obj.z.stop] = obj.permittivity.cpu().numpy()[:,:,:,0]
                # objects[cu_mask] = 2
            else:
                objects[obj.x.start:obj.x.stop, obj.y.start:obj.y.stop, obj.z.start:obj.z.stop] = obj.permittivity
        # objects += cu_mask*2

        cellData['objects'] = objects


    cellData['copper'] = cu_mask*2


    if(ports_dump):
        ports = np.zeros_like(E_copy[:,:,:,X])
        for port in [i for i in pcb.component_ports if i]:
                ports[port.N_x,port.N_y,pcb.component_plane_z-1] = 4

                # ports[port.N_x+1:port.N_x+2,port.N_y:port.N_y+1,pcb.component_plane_z-3:pcb.component_plane_z-2] = 5
                # ports[port.N_x-1:port.N_x,port.N_y:port.N_y+1,pcb.component_plane_z-3:pcb.component_plane_z-2]  = 5
                # ports[port.N_x:port.N_x+1,port.N_y+1:port.N_y+2,pcb.component_plane_z-3:pcb.component_plane_z-2] = 5
                # ports[port.N_x:port.N_x+1,port.N_y-1:port.N_y,pcb.component_plane_z-3:pcb.component_plane_z-2]  = 5
        cellData['ports'] = ports


    if(Ex_dump):
        cellData['Ex'] = np.ascontiguousarray(E_copy[:,:,:,X]) / sqrt(epsilon_0)
    if(Ey_dump):
        cellData['Ey'] = np.ascontiguousarray(E_copy[:,:,:,Y]) / sqrt(epsilon_0)
    if(Ez_dump):
        cellData['Ez'] = np.ascontiguousarray(E_copy[:,:,:,Z]) / sqrt(epsilon_0)
    if(Emag_dump):
        cellData['Emag'] = np.ascontiguousarray(E_magnitude(E_copy)) # gridToVTK expects a contiguous array.


    gridToVTK(filename + str(iteration), x, y, z, cellData = cellData)
