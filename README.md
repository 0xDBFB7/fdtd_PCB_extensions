---
bibliography: /home/arthurdent/Projects/covidinator/documents/references.bib
link-citations: true
title: Musings on an inexpensive 1500 C silicon carbide furnace
---

```{=html}
<!---# Musings on an inexpensive 1500 C furnace-->
```
```{=html}
<!---

pandoc --filter pandoc-citeproc --bibliography=references.bib -s furnace_quick.md -o paper.html -H style.css

-->
```
NGSPICE's KSPICE coupled transmission lines require the capacitance and
inductance per unit length in Maxwell matrix form, rather than the
physical $C_{even}$/$L_{even}$ (each line's capacitance and inductance
to ground) and $_{odd}$ (between elements) form provided by tools like
wcalc. "matrix not positive definite". \[Schutt-Aine\] discusses this;
we reproduce here for convienience.

\[ L\_{11} = L\_{22} = L\_{even} \] \[ L\_{12} = L\_{21} = L\_{odd} \]
\[ C\_{11} = C\_{22} = C\_{even}+C\_{odd} \] \[ C\_{12} = C\_{21}
{`\it{(unused)}`{=tex}} = -C\_{odd} \]

In practice, the timestep required to obtain convergence in particularly
tight corners of the SPICE simulation can drop to 1e-20, which is far
below the Courant limit of the FDTD simulation. To eek out a bit more
performance, a simple adaptive-timestep technique from \[ a \] is used;
we simply set the timestep so that the maximum change in voltage per
timestep from the SPICE portion is less than some threshold.

Conductors are represented by zeroing all components of the electric
field in those regions.

There are many different possible source geometries, each introducing
their own distortions.

There are many ways of linking SPICE and FDTD.

```{=tex}
\clearpage
\PRLsep{ Wherein antennas are characterized}
```
Method-of-moments solvers like NEC-2 are the standard for simulating
these sorts of antennas. However, most commonly-available packages don't
seem to handle multiple dielectric constants, such as the air and
substrate of a patch antenna.

The impedance of a structure over frequency can be determined in FDTD
by:

```{=tex}
\begin{itemize}
  \item Applying a gaussian pulse to a voltage source - in our case, applied to a via connecting the path (or probe)
  \item Running the simulation until the transients have all died out below some threshold, while logging the source voltage and current at each timestep
  \item Taking the fourier transform of the (real) excitation voltage and current (producing a complex result, mind you)
  \item Taking the magnitude of the ratio of the two complex spectra.
\end{itemize}
```
This is the computational equivalent of dropping a piano off a balcony
to see which key is stuck.

See \[Penney 1994\], \[Luebbers 1992\], \[Luebbers 1991\], \[Luk 1997\].

Our implementation is in
`\ghfile{electronics/simple_fdtd/runs/U.py}`{=tex}.

A similar mismatch to the SPICE exists for fourier methods - but in the
other direction. The courant limit often demands fine timesteps, but
since each FFT bin is \$ f\_{bin} = n\_{bin} / (N\_{simulation}  dt) \$
, the majority of the FFT bins exist into the hundreds or thousands of
GHz, leaving no resolution in the low-frequency domain of interest
unless $N_{simulation}$ is extremely large - even if all the transients
in the simulation have died down, you still have to keep the sim running
to make the FFT happy!

There's more than enough 'information entropy' in 4000 FDTD points for
most antennas. But you need some 30,000 points to get 10 bins below 20
GHz!

There are a few methods of changing the FFT bin size artificially, which
\[Bi 1992\] reviews. You can "use a manual fourier integration over the
frequency region of interest".

But, in a staggering turn of events which will presumably be familiar to
statisticans and preposterous to everyone else, a far simpler method is
to {`\it discard`{=tex}} 95% of the data, by down-sampling to 1/10th or
so.

An equally simple method that seemed to produce better results in our
case is to pad the voltage and current samples to the correct length.
The jump discontinuity introduced by padding with zeros has a negligible
effect.

It's so thumpingly unintuitive to me that adding 50,000 zeros to a 5000
value dataset can improve the resolution of a measurement by 300-fold.

It is important to remember to normalize the gaussian pulse, or else
numerical noise will be introduced. The magnitude is not important -
\[Luebbers 1992\] use 100v, others use 1v, etc.

Though uneven dt FFTs exist, the time step can be constant at the
courant limit for this simulation.

A step impulse (1 first timestep, 0 otherwise) has been used in some
works, though in our case performance was quite horrid.

A correction factor due to the staggered magnetic field of the Yee
lattice must be introduced; \[Fang 1994\]. Their $Z_2$ equation
(correcting for spatial inaccuracies, but not temporal) was sufficient.

This technique is equivalent to that used in electrochemistry, known as
fourier impedance spectroscopy - except they seem to usually use a known
impedance source rather than a hard source, presumably because ideal
hard sources don't exist in reality.

Allowing the simulation to run for long enough that all transients
dissipate is important for accuracy - deceptive dips in the current can
cause early termination. A surprising amount of detail is contributed by
even the smallest current levels. Our threshold is 1e-7 amps for 700
iterations.

\[Samaras 2004\] has a very useful set of experimental and FDTD data for
calibration and comparison. Comparing a probe via source in the
different positions, we obtained agreement of $\sim 7\%$ in impedance
and $\sim 5\%$ in frequency.

The use of a hard source feed-port affects the number of timesteps
required by introducing unphysical transients. Using a port with a
virtual 50-ohm resistance reduces the computational requirements by a
large factor; see \[Luebbers 1996\].

Simply monitoring the source current during the simulation is somewhat
deceptive. Periodically monitoring the change in the fourier transform
seems to be a better convergence metric.

The units of the FFT (unlike those of the continuous FT) remain in
volts.

```{=tex}
\rule{\linewidth}{0.2pt}
```
Most equations in papers on the FDTD method are supplied without making
the scaling factors explicit; some need multiplying by the Courant
number, For use with flaport/fdtd the H-field to current line integral
in \[\] requires scaling by $\mu_0 * (dx/dt)$, where $\mu_0$ is the
vacuum magnetic permittivity, dx the cell size, and dt the timestep -
despite the equation already possessing a deceptive set of $dx$-es.

FIX THIS IT'S WRONG

Naturally, if one is competent, this discrepancy will be immediately
obvious. Those not dimensionally-intuitive, such as myself, find it
useful to run dimensional analysis using a unit-aware calculator such as
{`\it sharkdp/insect`{=tex}}.

```{=tex}
\rule{\linewidth}{0.2pt}
```
