"""prng_model — a linear-feedback shift register, in Python.

This is the golden model.  You will write the same thing in SystemVerilog, and
the lab checks that the two agree exactly, sample for sample.

The generator is a 16-bit Fibonacci LFSR.  The state shifts left by one bit each
step, and the bit shifted in at the bottom is the XOR of four *tap* positions:

    state:   b15 b14 b13 b12 b11 b10 b9 b8 b7 b6 b5 b4 b3 b2 b1 b0
    taps:     ^   ^       ^                          ^
              15  14      12                         3

    new_bit = b15 ^ b14 ^ b12 ^ b3
    state   = (state << 1) | new_bit          (keeping 16 bits)

Those particular taps are the polynomial x^16 + x^15 + x^13 + x^4 + 1, which is
*primitive* — the state visits all 65535 nonzero values before repeating.  Other
tap sets give shorter periods, and the wrong ones give very short periods.

Zero is a fixed point: 0 shifted and XORed with nothing is still 0.  A seed of 0
produces an infinite stream of zeros, which is why ``SEED`` is nonzero and why
``lfsr_stream`` rejects a zero seed rather than silently generating nothing.
"""
from __future__ import annotations

import numpy as np

WIDTH = 16                  # bits of LFSR state
MASK = (1 << WIDTH) - 1     # 0xFFFF — what "keeping 16 bits" means
TAPS = 0xD008               # bits 15, 14, 12 and 3
BITS = 8                    # bits per output sample
SEED = 0xB0BA               # nonzero, and fixed so results are reproducible
NSAMP = 1000                # samples to generate


def prng_next(state: int) -> int:
    """Advance the LFSR by one bit and return the new 16-bit state.

    Parameters
    ----------
    state : int
        The current 16-bit state.  Must be nonzero.

    Returns
    -------
    int
        The next state, in ``0 .. 0xFFFF``.
    """
    # TODO:  Advance the LFSR by one bit, and delete the `return 0` below.
    #
    #     feedback = ...      the XOR of the four tapped bits
    #     return ...          state shifted left, with feedback at the bottom
    #
    # Two things worth knowing:
    #
    #   * `state & TAPS` keeps only the tapped bits.  The XOR of all the bits
    #     in a number is the low bit of its population count, and
    #     `bin(w).count("1")` is that count.
    #
    #   * Do not forget to mask the result to WIDTH bits.  Python integers are
    #     unbounded, so an unmasked state grows a bit longer on every call
    #     instead of wrapping at 16 bits.
    return 0


def prng_sample(state: int) -> tuple[int, int]:
    """Advance the LFSR by ``BITS`` steps and return ``(new_state, sample)``.

    One step produces one new bit, so ``BITS`` steps are needed before the low
    ``BITS`` bits of the state are all fresh.  Taking a sample every *single*
    step instead would make consecutive samples share all but one of their bits
    — the histogram would still look flat, and the numbers would be anything but
    independent.

    Parameters
    ----------
    state : int
        The state to start from.

    Returns
    -------
    tuple[int, int]
        The state after ``BITS`` steps, and the sample taken from it.
    """
    # TODO:  Advance the LFSR BITS times, then return the new state together
    # with the sample taken from it.  Delete the `return state, 0` below.
    #
    #     for ...:
    #         state = ...
    #     return state, ...
    #
    # The sample is the low BITS bits of the state.  `(1 << BITS) - 1` is a
    # mask of BITS ones, which is how you keep just those bits.
    #
    # Return the state as well as the sample: the caller has to carry it into
    # the next call, or every sample would start from the same place.
    return state, 0


def lfsr_stream(seed: int = SEED, nsamp: int = NSAMP) -> np.ndarray:
    """Generate *nsamp* samples of ``BITS`` bits each, starting from *seed*.

    This is what the build script calls, and it is given.
    """
    if seed == 0:
        raise ValueError(
            "The LFSR seed must be nonzero — zero is a fixed point, and the "
            "generator would emit nothing but zeros forever.")

    state = seed & MASK
    out = np.zeros(nsamp, dtype=np.int64)
    for i in range(nsamp):
        state, out[i] = prng_sample(state)
    return out


if __name__ == "__main__":
    # Handy while you are working: run this file directly to see the first few
    # samples without going through the build.
    for i, value in enumerate(lfsr_stream(SEED, 10)):
        print(f"  {i}  {value}")
