
from .PCB import *




def initialize_grid(pcb, N_x, N_y, N_z, courant_number=None):
    N_x += 2*(pcb.xy_margin) # wtf? Fix this
    N_y += 2*(pcb.xy_margin) # wtf? Fix this
    N_z += pcb.pml_cells+pcb.z_margin # wtf? Fix this
    grid = fdtd.Grid(
        (N_x,N_y,N_z),
        grid_spacing=pcb.cell_size,
        permittivity=1.0,
        permeability=1.0,
        courant_number = courant_number)

    fdtd.PML(1e-8, # stability factor
        None)

    pml_cells = pcb.pml_cells

    grid[0:pml_cells, :, :] = fdtd.PML(name="pml_xlow")
    grid[-pml_cells:, :, :] = fdtd.PML(name="pml_xhigh")
    grid[:, 0:pml_cells, :] = fdtd.PML(name="pml_ylow")
    grid[:, -pml_cells:, :] = fdtd.PML(name="pml_yhigh")
    grid[:, : ,0:pml_cells] = fdtd.PML(name="pml_zlow")
    grid[:, : ,-pml_cells:] = fdtd.PML(name="pml_zhigh")

    pcb.grid = grid


    if(not isinstance(fdtd.backend, NumpyBackend)):
        pcb.copper_mask = bd.zeros((N_x,N_y,N_z)).bool()
    else:
        pcb.copper_mask = np.zeros((N_x,N_y,N_z), dtype=bool)


def create_planes(pcb, ground_plane_thickness, conductor_conductivity):
    '''
    Using thick copper planes only seems to affect the impedance by about 3%.
    This should be okay, but might affect interdigital filters etc.
    '''

    N_ground_plane = ceil(ground_plane_thickness / pcb.cell_size)

    #using a copper mask is much faster than an fdtd.object
    pcb.copper_mask[pcb.xy_margin:-pcb.xy_margin, pcb.xy_margin:-pcb.xy_margin, pcb.z_margin:(pcb.z_margin+N_ground_plane)] = 1

    pcb.ground_plane_z_top = pcb.z_margin+N_ground_plane


def create_substrate(pcb, substrate_thickness, substrate_permittivity, loss_tangent, loss_tangent_frequency):

    conductivity_scaling = 1.0/(pcb.cell_size / epsilon_0)

    N_substrate = ceil(substrate_thickness / pcb.cell_size)

    substrate_conductivity = loss_tangent * (2.0*pi) * loss_tangent_frequency * epsilon_0 * substrate_permittivity * conductivity_scaling
    #conductivity = substrate_conductivity,
    #loss tangent not accounted for
    # substrate_conductivity = 0
    pcb.grid[pcb.xy_margin:-pcb.xy_margin, pcb.xy_margin:-pcb.xy_margin, pcb.ground_plane_z_top:(pcb.ground_plane_z_top+N_substrate)] \
                        = fdtd.Object(permittivity=substrate_permittivity, name="substrate")


    pcb.component_plane_z = pcb.ground_plane_z_top + N_substrate

    pcb.substrate_permittivity = substrate_permittivity

def initialize_grid_with_svg(pcb, svg_file, courant_number = None):
    '''

    xy_margin is the number of cells (including PML cells) to add around the board.
    z_margin is the same, but below the board.

    '''

    svg = etree.parse(svg_file).getroot()
    width = float(svg.attrib['width'].strip('cm')) / 100.0 #to meters
    height = float(svg.attrib['height'].strip('cm')) / 100.0 #to meters
    print("Imported {} | width: {}m | height: {}m".format(svg_file, width, height))

    N_x = math.ceil(width/pcb.cell_size)
    N_y = math.ceil(height/pcb.cell_size)
    N_z = math.ceil(pcb.z_height/pcb.cell_size)
    #margins now baked into initialize_grid

    pcb.board_N_x = math.ceil(width/pcb.cell_size)
    pcb.board_N_y = math.ceil(height/pcb.cell_size)

    print("Into a {} x {} x {} mesh".format(N_x, N_y, N_z))

    initialize_grid(pcb, N_x, N_y, N_z, courant_number=courant_number)


def construct_copper_geometry_from_svg(pcb, copper_thickness, conductor_conductivity, svg_file):
    PNG_SUPERSAMPLE_FACTOR = 10

    N_top_copper = ceil(copper_thickness / pcb.cell_size)

    z_slice = slice(pcb.component_plane_z,(pcb.component_plane_z+N_top_copper))
    image_data = io.BytesIO(svg2png(url=svg_file, output_width=pcb.board_N_x*PNG_SUPERSAMPLE_FACTOR,
                                                  output_height=pcb.board_N_y*PNG_SUPERSAMPLE_FACTOR))
    image = Image.open(image_data)
    pix = image.load()
    for x in range(0, pcb.board_N_x):
        for y in range(0, pcb.board_N_y):
            if(pix[x*PNG_SUPERSAMPLE_FACTOR,y*PNG_SUPERSAMPLE_FACTOR][3]): #alpha channel
                pcb.copper_mask[pcb.xy_margin+x:pcb.xy_margin+x+1, pcb.xy_margin+(y):pcb.xy_margin+(y)+1, z_slice] = 1
                # pcb.grid[pcb.xy_margin+x:pcb.xy_margin+x+1, pcb.xy_margin+(y):pcb.xy_margin+(y)+1, z_slice] \
                #                     = fdtd.PECObject(name=None)
