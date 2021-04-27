---
title: 'Musings on an inexpensive 1500 C silicon carbide furnace'
link-citations: true
...

<!---# Musings on an inexpensive 1500 C furnace-->

<!---

pandoc --filter pandoc-citeproc --bibliography=/home/arthurdent/Projects/covidinator/documents/references.bib --standalone --highlight-style pygments Z_params.md --mathjax -o Z_params.html

?
-->

# Some notes on Z and FDTD

Note: I'm way overcomplicating this: it's an extremely basic 20-line procedure; these are also my notes from using this. I'm sure you know this already, so by putting it in this format rather than a PR,

I was using this to measure the impedance of some antenna and microstrip designs;
so I've only tried getting the complex impedance parameters (Z11 / Z22) so far. I believe it is easy to compute
S11 and S22 directly from that.

I believe computing S12 and S21 should be essentially identical; apply a pulse to each source in turn,
and just divide the complex voltages accordingly; in that case, the output will be relative to the source impedance.

In addition, this was all formulated for electrical signals on planar with ground plane,
where the kinds of sources make sense. I have no idea how to modify this for the optical domain - if modifications are indeed required.

In addition, this is nothing more than applying an input and monitoring the output;
some tools such as gprMax make response evaluation into a separate tool that just wraps around 'fdtd'.

The *impedance* of a structure over frequency can be determined easily by:

See (@Input1994), (@FDTD1992), (@Finite1991), (@FDTD1997).


### 1. Choose a source / "feed model" geometry, and terminate all ports with a soft source with the appropriate impedance.

Presumably 

'''python


'''

(I'm sure you know all this stuff already)

The type of source geometry used can apparently decisively affect the performance of this method

@simple1996

The voltage and current time histories on each port need to be saved.




### 3. Apply a broadband pulse.

You want a pulse that includes strong components across the entire frequency range of interest, but apparently you also don't want to introduce noise.





\begin{itemize}
  \item Applying a gaussian pulse to a voltage source - in our case, applied to a via connecting the path (or probe)
  \item Running the simulation until the transients have all died out below some threshold, while logging the source voltage and current at each timestep
  \item Taking the fourier transform of the (real) excitation voltage and current (producing a complex result, mind you)
  \item Taking the magnitude of the ratio of the two complex spectra.
\end{itemize}

This is the computational equivalent of dropping a piano off a balcony to see which key is stuck.


Our implementation is in \ghfile{electronics/simple_fdtd/runs/U.py}.

A similar mismatch to the SPICE exists for fourier methods - but in the other direction.  The courant limit often demands fine timesteps, but since each FFT bin is $ f_{bin} = n_{bin} / (N_{simulation} \ dt) $ , the majority of the FFT bins exist into the hundreds or thousands of GHz, leaving no resolution in the low-frequency domain of interest unless $N_{simulation}$ is extremely large - even if all the transients in the simulation have died down, you still have to keep the sim running to make the FFT happy!

There's more than enough 'information entropy' in 4000 FDTD points for most antennas. But you need some 30,000 points to get 10 bins below 20 GHz!

There are a few methods of changing the FFT bin size artificially, which [Bi 1992] reviews. You can "use a manual fourier integration over the frequency region of interest".

But, in a staggering turn of events which will presumably be familiar to statisticans and preposterous to everyone else, a far simpler method is to {\it discard} 95\% of the data, by down-sampling to 1/10th or so.

An equally simple method that seemed to produce better results in our case is to pad the voltage and current samples to the correct length. The jump discontinuity introduced by padding with zeros has a negligible effect.

It's so thumpingly unintuitive to me that adding 50,000 zeros to a 5000 value dataset can improve the resolution of a measurement by 300-fold.

It is important to remember to normalize the gaussian pulse, or else numerical noise will be introduced. The magnitude is not important - [Luebbers 1992] use 100v, others use 1v, etc.

@FDTD1992

Though uneven dt FFTs exist, the time step can be constant at the courant limit for this simulation.

A step impulse (1 first timestep, 0 otherwise) has been used in some works, though in our case performance was quite horrid.

A correction factor due to the staggered magnetic field of the Yee lattice must be introduced; [Fang 1994]. Their $Z_2$ equation (correcting for spatial inaccuracies, but not temporal) was sufficient.


This technique is equivalent to that used in electrochemistry, known as fourier impedance spectroscopy - except they seem to usually use a known impedance source rather than a hard source, presumably because ideal hard sources don't exist in reality.

Allowing the simulation to run for long enough that all transients dissipate is important for accuracy - deceptive dips in the current can cause early termination. A surprising amount of detail is contributed by even the smallest current levels. Our threshold is 1e-7 amps for 700 iterations.

[Samaras 2004] has a very useful set of experimental and FDTD data for calibration and comparison. Comparing a probe via source in the different positions, we obtained agreement of $\sim 7\%$ in impedance and $\sim 5\%$ in frequency.

The use of a hard source feed-port affects the number of timesteps required by introducing unphysical transients. Using a port with a virtual 50-ohm resistance reduces the computational requirements by a large factor; see [Luebbers 1996].

Simply monitoring the source current during the simulation is somewhat deceptive. Periodically monitoring the change in the fourier transform seems to be a better convergence metric.

The units of the FFT (unlike those of the continuous FT) remain in volts.

\rule{\linewidth}{0.2pt}

Most equations in papers on the FDTD method are supplied without making the scaling factors explicit; some need multiplying by the Courant number, For use with flaport/fdtd the H-field to current line integral in [] requires scaling by $\mu_0 * (dx/dt)$, where $\mu_0$ is the vacuum magnetic permittivity, dx the cell size, and dt the timestep - despite the equation already possessing a deceptive set of $dx$-es.

FIX THIS IT'S WRONG

Naturally, if one is competent, this discrepancy will be immediately obvious. Those not dimensionally-intuitive, such as myself, find it useful to run dimensional analysis using a unit-aware calculator such as {\it sharkdp/insect}.

\rule{\linewidth}{0.2pt}

# References:
