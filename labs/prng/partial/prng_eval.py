"""prng_eval — measuring whether your generator is any good.

You have a stream of numbers.  Are they random?

You cannot answer that by looking at the code, and you certainly cannot answer
it by looking at a waveform.  You answer it by *measuring* the stream, in
Python, where measuring is cheap — and you do it **before** you write a line of
SystemVerilog.  A flaw you find here costs you an edit.  The same flaw found
after synthesis costs you a day.

That is the whole point of this stage, and it is the habit worth taking away
from this lab: a golden model is not just something to compare hardware
against, it is where you find out whether the design is worth building.

Two measurements, and they answer different questions:

**The histogram** asks whether every value happens about equally often.

**The lag-1 correlation** asks whether each sample tells you anything about the
next one.

You need both.  The sequence 0, 1, 2, … 255, 0, 1, … has a *perfectly* flat
histogram and is completely predictable — the histogram cannot tell that apart
from a good generator and the correlation can.  Uniform is not the same as
random.

The definitions, and what the finished figure should look like, are on the lab's
`Evaluating before you build` page.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

#: Bins for the histogram.  Sixteen over 256 values puts about 62 samples in
#: each at n=1000 — enough that a real bias shows, where one bin per value
#: would average four and drown in noise.
NBINS = 16


def lag1_correlation(samples: np.ndarray) -> float:
    """Return the lag-1 autocorrelation of *samples*.

    The definition is on the lab's `Evaluating before you build` page.

    Parameters
    ----------
    samples : np.ndarray
        The generated stream.

    Returns
    -------
    float
        A value in ``-1.0 .. 1.0``.  Near zero means each sample tells you
        nothing about the next.
    """
    # TODO:  Compute the lag-1 correlation, and delete the `return 0.0` below.
    #
    # `np.corrcoef` will do the arithmetic for you.  Read its documentation for
    # what it takes and what it gives back — it does not return a single number.
    #
    # Return a plain float.
    return 0.0


def histogram(samples: np.ndarray, nbins: int = NBINS, nvalues: int = 256) -> np.ndarray:
    """Count how many samples fall into each of *nbins* equal-width bins.

    The bins tile ``0 .. nvalues`` — with the defaults, bin 0 holds values 0-15,
    bin 1 holds 16-31, and so on up to bin 15 holding 240-255.

    Parameters
    ----------
    samples : np.ndarray
        The generated stream.
    nbins : int
        How many bins to split the range into.
    nvalues : int
        One past the largest possible sample, so ``2**BITS``.

    Returns
    -------
    np.ndarray
        An integer array of length *nbins*.  It must sum to ``len(samples)``.
    """
    # TODO:  Count the samples in each bin, and delete the `return` below.
    #
    # `np.histogram` will do the counting.  Read its documentation, and look
    # carefully at what it returns and at its `range` argument — the default
    # for `range` is not what this function's docstring promises.
    return np.zeros(nbins, dtype=int)


def plot_evaluation(samples: np.ndarray, counts: np.ndarray, corr: float,
                    bits: int, out_path: Path) -> Path:
    """Draw the histogram *you* computed, and save it to *out_path*.

    Plot ``counts`` rather than recomputing them from ``samples``: the picture
    is then a picture of your :func:`histogram`, and a mistake in it is
    something you can see rather than only something you are told.

    The target is on the lab's `Evaluating before you build` page.

    Parameters
    ----------
    samples : np.ndarray
        The generated stream, for the sample count.
    counts : np.ndarray
        The bin counts from :func:`histogram`.
    corr : float
        The value from :func:`lag1_correlation`, for the title.
    bits : int
        Bits per sample, so the x-axis can run 0 to 1.
    out_path : Path
        Where to write the PNG.
    """
    # The backend is set up for you; writing to a file rather than opening a
    # window is what `Agg` is for.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    nbins = len(counts)
    expected = len(samples) / nbins

    # TODO:  Draw the histogram and save it to `out_path`.
    #
    # `plt.subplots()` gives you a figure and an axis.  On the axis, `bar`
    # draws bars and `axhline` draws a horizontal line — which is how you show
    # the flat line at `expected` that the bars are measured against.  Label
    # both axes, and put the sample count and `corr` in the title so the
    # picture says what it is showing.
    #
    # Scale the x-axis to run 0 to 1 rather than 0 to 255 — the samples then
    # read as fractions, which is how a uniform random number is usually
    # wanted.  Compare what you get against the figure on the lab page.
    #
    # Finish with `fig.savefig(out_path)`.  The file is part of what you submit,
    # and the lab checks that you produced it.
    return out_path
