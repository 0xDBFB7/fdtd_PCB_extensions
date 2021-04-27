import Levenshtein as lev
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

import nexusformat.nexus as nx #h5 .tree pretty-print

from math import pi, sqrt, e, log, isclose, exp
from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import h5py
from scipy.constants import epsilon_0, mu_0

from fdtd.backend import NumpyBackend
from fdtd.backend import backend as bd


import fdtd
#imports a VirtualPopulation .raw voxel file.

material_ids_file = '/home/arthurdent/covidinator/biology/FDTD/chunks/2mm_100x100x100_left_lung_5.txt'
tissue_properties_database_file = '/home/arthurdent/covidinator/biology/FDTD/itis_tissue_properties/SEMCAD_v14.8.h5'

#os.environ.get('ITIS_TISSUE_DATABASE')


def electric_field_penetration_depth(center_frequency, relative_permittivity, conductivity):
    #from Hand, 1982 and Osepchuk

    angular_frequency = 2.0*pi*center_frequency

    d = (1.0 / angular_frequency)
    mid = ((relative_permittivity*mu_0*epsilon_0)/2.0)
    mid *= (np.sqrt(1.0+((conductivity/(angular_frequency*epsilon_0*relative_permittivity))**2.0))-1)
    mid = (mid)**(-1.0/2.0)

    return d*mid


def cole_cole_4(center_frequency, ef, sigma, deltas, alphas, taus):
    '''
    See "Compilation of the dielectric properties of body tissues at RF and microwave frequencies.", Gabriel 1996
    Equation 3, page 12.
    '''
    angular_frequency = 2.0*pi*center_frequency

    complex_permittivity = complex(ef, 0)


    for n in range(0, 4):
        complex_permittivity += deltas[n] / (1.0 + ((complex(0, 1)*angular_frequency*taus[n])**(1.0-alphas[n])))

    complex_permittivity[angular_frequency > 0] += (sigma/((complex(0, 1)*angular_frequency[angular_frequency > 0]*epsilon_0)))


    return complex_permittivity

def complex_permittivity_to_er_and_sigma(complex_permittivity, center_frequency):
    angular_frequency = 2.0*pi*center_frequency

    relative_permittivity = complex_permittivity.real
    conductivity = abs(complex_permittivity.imag*((angular_frequency*epsilon_0)))

    return relative_permittivity, conductivity




def get_tissue_VirtPopTool_name(raw_id):
    '''
    The SEMCAD X virtual population tool generates a list of tissues along with the .raw voxel file.
    These IDs don't correspond to those in the It.Is Tissue Properties Database.
    '''
    ids_names = np.genfromtxt(open(material_ids_file, "r"), delimiter="\t", dtype=None, encoding='ascii', skip_footer=7)
    name = ids_names[raw_id-1][4] # tissue name
    name = name[(name.index('/')+1):] #remove duke_blah_blah/ prefix
    return name

def get_tissue_cole_cole_coefficients(id):

    #this absolutely should not be hardcoded.

    tissue_obj = 0
    f = h5py.File(tissue_properties_database_file,'r')
    #Fuzzy matching names - keep a close eye on this, errors could creep in!
    virtprop_name = get_tissue_VirtPopTool_name(id)
    matching_name = process.extractOne(virtprop_name,f['Tissues'].keys())
    print(f"Fuzzy-matched tissue {virtprop_name} to {matching_name[0]}")

    tissue_obj = f['Tissues'][matching_name[0]]

#         f = nx.nxload(tissue_properties_database_file)
#         print(f['Tissues']["SAT (Subcutaneous Fat)"].tree)
#           @HC = 2348.33
#           @HGR = 0.506566
#           @HTR = 32.7093
#           @Name = 'SAT (Subcutaneous Fat)'
#           @TC = 0.2112
#           @alf1 = 0.2
#           @alf2 = 0.1
#           @alf3 = 0.05
#           @alf4 = 0.01
#           @del1 = 9
#           @del2 = 35
#           @del3 = 33000
#           @del4 = 1e7
#           @ef = 2.5
#           @sig = 0.035
#           @tau1 = 7.958
#           @tau2 = 15.915
#           @tau3 = 159.155
#           @tau4 = 15.915

    taus = np.array([0]*4,dtype=np.float)
    alphas = np.array([0]*4,dtype=np.float)
    deltas = np.array([0]*4,dtype=np.float)

    taus[0] = tissue_obj.attrs["tau1"]
    taus[1] = tissue_obj.attrs["tau2"]
    taus[2] = tissue_obj.attrs["tau3"]
    taus[3] = tissue_obj.attrs["tau4"]

    # Tau values in the tissueprop files are normalized
    # Tau1 is normalized by 1e-12
    # tau2 1e-9
    # tau3 1e-6
    # tau4 1e-3
    tau_normalization_factors = np.array([1e-12, 1e-9, 1e-6, 1e-3])
    # all other constants are not normalized.
    taus *= tau_normalization_factors

    alphas[0] = tissue_obj.attrs["alf1"]
    alphas[1] = tissue_obj.attrs["alf2"]
    alphas[2] = tissue_obj.attrs["alf3"]
    alphas[3] = tissue_obj.attrs["alf4"]

    deltas[0] = tissue_obj.attrs["del1"]
    deltas[1] = tissue_obj.attrs["del2"]
    deltas[2] = tissue_obj.attrs["del3"]
    deltas[3] = tissue_obj.attrs["del4"]

    sigma = tissue_obj.attrs["sig"]
    ef = tissue_obj.attrs["ef"]

    return ef, sigma, deltas, alphas, taus

def tissue_properties(center_frequency, ef, sigma, deltas, alphas, taus):
    cole_cole_properties = cole_cole_4(center_frequency, ef, sigma, deltas, alphas, taus)
    dielectric_constant, conductivity = complex_permittivity_to_er_and_sigma(cole_cole_properties, center_frequency)
    penetration_depth = electric_field_penetration_depth(center_frequency, dielectric_constant, conductivity)

    return dielectric_constant, penetration_depth


def lookup_tissue_properties(id, center_frequency):


    ef, sigma, deltas, alphas, taus = get_tissue_cole_cole_coefficients(id)
#     print(ef, sigma, deltas, alphas, taus)
    cole_cole_properties = cole_cole_4(center_frequency, ef, sigma, deltas, alphas, taus)
    dielectric_constant, conductivity = complex_permittivity_to_er_and_sigma(cole_cole_properties, center_frequency)
    penetration_depth = electric_field_penetration_depth(center_frequency, dielectric_constant, conductivity)

    return dielectric_constant, conductivity, penetration_depth


def import_raw_voxel_file(raw_filename, cell_sizes):
    raw = np.fromfile(raw_filename, dtype=np.uint8)
    raw = np.reshape(raw, cell_sizes)
    return raw

def voxel_to_fdtd_grid_import(grid, raw, import_offset, voxel_file_cell_size, fdtd_grid_cell_size, center_frequency, exclude):
    '''
    fdtd_grid_cell_size must be < and an integer divisor of voxel_file_cell_size
    '''
    # upsample = int(voxel_file_cell_size/fdtd_grid_cell_size)
    # a.repeat(upsample, axis=0).repeat(upsample, axis=1)
    #just shift array by some to offset

    #
    # if(not isinstance(fdtd.backend, NumpyBackend)):
    #     active_tissue = bd.zeros((grid.Nx-2*pml_,grid.Ny,grid.Nz,3)).bool()
    #     inverse_permittivity = bd.ones((grid.Nx,grid.Ny,grid.Nz,3))
    #     absorption_factor = bd.zeros((grid.Nx,grid.Ny,grid.Nz,3))
    # else:
    #     active_tissue = np.zeros((grid.Nx,grid.Ny,grid.Nz,3), dtype=bool)
    #     inverse_permittivity = np.ones((grid.Nx,grid.Ny,grid.Nz,3), dtype=fdtd.backend.float)
    #     absorption_factor = np.zeros((grid.Nx,grid.Ny,grid.Nz,3), dtype=fdtd.backend.float)
    #
    #

    conductivity = bd.zeros((100,100,100,3))
    permittivity = bd.ones((100,100,100,3))

    for i in np.unique(raw):
        if(i in exclude):
            continue
        #
        # i = int(i)
        dielectric_constant_, conductivity_, penetration_depth = lookup_tissue_properties(i, center_frequency)


        conductivity_ /= (fdtd_grid_cell_size / epsilon_0) #flaport's units
        # conductivity = conductivity
        # # print(conductivity)
        # # print(dielectric_constant)
        cell_indices = np.where(raw == i)
        print(conductivity_)
        conductivity[cell_indices] = conductivity_
        permittivity[cell_indices] = dielectric_constant_

        #
        # inverse_permittivity[cell_indices] /= dielectric_constant
        #
        # absorption_factor[cell_indices] = (
        #     0.5
        #     * grid.courant_number
        #     * inverse_permittivity[cell_indices]
        #     * conductivity
        #     * grid.grid_spacing
        #     / fdtd.grid.VACUUM_PERMITTIVITY
        # )
        #
        # active_tissue[cell_indices] = 1
        #

    grid[10:-10,10:-10,10:-10] = fdtd.AbsorbingObject(permittivity=permittivity, conductivity=conductivity, name=f"t{i}")

    # return inverse_permittivity, absorption_factor, active_tissue


if(__name__ == '__main__'):
    #unit test!
    lookup_tissue_properties(5, 2.990e9)

    blood = cole_cole_4(2.99e9, 4.0, 7e-1, [5.6e+1, 5.2e+3, 0, 0], [1e-1, 1e-1, 2e-1, 0], \
                               [8.37e-12, 1.32e-7,1.59e-4,1.592e-2])
    blood_perm, blood_cond = complex_permittivity_to_er_and_sigma(blood, 2.99e9)

    assert(isclose(blood_perm, 5.74E+1, rel_tol=0.1)) #Blood!
    assert(isclose(blood_cond, 3.04E+0, rel_tol=0.1)) #Blood!


    depth = electric_field_penetration_depth(2.99e9, 57.37, 3.04)

    #Blood penetration depth from
    #http://niremf.ifac.cnr.it/tissprop/htmlclie/htmlclie.php
    assert(isclose(depth, 0.01339, rel_tol=0.001))
