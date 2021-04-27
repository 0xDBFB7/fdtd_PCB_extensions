
This is a simple Python wrapper for flaport/fdtd and ngspice that supports KiCAD PCB import.

flaport's pytorch CUDA integrations make this pleasantly fast. Good on ya, flaport!

Better alternatives are

1. OpenEMS (which supports some lumped elements), especially with Dan Harmon's pyopenems bindings. Supports mesh refinement, which is neat.
2. gprMax. also amazing, the api isn't quite right for this sort of application.
3. MEEP - great, very mature, but seems a bit more optimized for optical.
4. fdtd++? haven't evaluated.


S-expression-S-parameter


# Background

Coupling SPICE and FDTD is a mature, erm, field.

There are numerous subtly different methods of coupling; either voltage integrated from the grid is injected into SPICE, then the computed current is put back onto the grid with a H-field source, or the other way around [Mix 1999].

[Thomas 1994] fields a method of represents the source cell's capacitance in SPICE, and lets SPICE integrate the voltage on the capacitor before directly putting that voltage on the grid.

~~We do the same, except the cell capacitance is integrated in the FDTD loop. This is a dumbass way to do it, since the timestep must be horrifically small to resolve the voltage properly.
We couldn't make the other methods work in short order.~~

The

We use a simple current source, a la equation 4, 5 in [Toland 1993], and https://www.eecs.wsu.edu/~schneidj/ufdtd/chap3.pdf, eq. 3.28

There are also many different source geometries, each introducing their own distortion; Ampere's law current contours around each conductor [Mix 1999], voltage via staircases
from the ground plane [Luebbers 1996], current sources in the plane of the trace, with vias to the ground plane, etc.

We again choose the worst possible one, a simple via. This has the advantage of not needing the current direction or source polarization to be manually specified,
but probably distorts the signal significantly.

Conductors are represented by zeroing all components of the electric field within. They're supposed to have zero thickness - I think only one edge-layer of E components are zeroed, but that's worth double-checking.

Each pad on the board gets a Port object and a corresponding voltage source in SPICE, with a new unique net name.

It should be noted that flaport/fdtd uses different units.

# class LumpedComponent(object):
# """
#
# See "The use of SPICE lumped circuits as sub-grid models for FDTD analysis", doi:10.1109/75.289516
# which deals with lumped elements of a single-cell size, and

# "Incorporating non-linear lumped elements in FDTD: the equivalent source method", Jason Mix
# http://ecee.colorado.edu/microwave/docs/publications/1999/IJNM_JMjdMPM_99.pdf
# which deals with objects of arbitrary size.
#
# You can use this 'equivalent source method' either by line-integrating the currents around a conductor
# and setting the electric field, or by line-integrating the voltage and setting the magnetic field.
#
# I chose the latter because it seems to make more sense to set a voltage initial-condition in SPICE than a current.
#
# 1. Normal electric field update.
# 2. Obtain terminal voltages by an electric field line integration from one port to another.
# 3. Normal magnetic field update.
# 4. Obtain the lumped currents from the voltages - either via SPICE or via analytic expressions for each component
# 5. Set H along a contour enclosing the conductor to net_current / Lc
# 6. ...
# 7. Profit!
#
#
# """




# Usage

Install 'fdtd'

https://fdtd.readthedocs.io/en/latest/

version used is that in Programs/flaport

pip install cairosvg

Export SVG from freecad - hidden text can make the svg's size weird

if in conda, tests have to be run with

'python -m pytest'

with -s perhaps for console output

pip install pyevtk



1. Design your schematic and PCB normally. Set the SPICE models in KiCAD.
2. Set the aux axis origin precisely on the top left corner of the board geometry.
2. Export an SVG in KiCAD. Check "Only board area".
3. Disable any SPICE components not participating in the simulation.
4. Export a SPICE netlist.
5. Add sources in append.cir


The timestep SPICE requires to properly resolve circuits can sometimes drop below 1e-20s, far lower than the speed-of-light Courant limit that FDTD requires for most reasonable mesh sizes.

For this reason, the adaptive timestep method described by [Ciampolini 1995] is used.


TODO: fix spice timestep


profile with


The port current used is different in sign from the convention usually used in FDTD codes. Positive port current induces a positive voltage difference on the port.

python setup.py develop

definitely need the github version of /fdtd.


The method for determining antenna impedance is [Luebbers 1992], particularly eq. 2, and applied in [Penney 1994].
Penney uses a derivative gaussian function - a Gaussian multiplied by the n-th Hermite polynomial. No idea why.
they use a pulse width of 32 timesteps.
