---
title: Theory
parent: Pseudorandom Number Generator
nav_order: 1
has_children: false
---

# Theory: how an LFSR works

An LFSR costs a handful of flip-flops and a few XOR gates, which is why you find
one in almost every serial link, built-in self-test and stream cipher. There is
no multiplier and no lookup table — the whole generator is shifting and XOR.

## The recurrence

An LSFR has some fixed *length* denote `L`.  In this lab, we will take the value `L=16`.
For a given `L`, the LFSR has a state of exactly `L` bits, `b0, b1, ..., b{L-1}`.  The LFSR then generates pseudorandom bits iterativesly in steps.  In each step, it shifts the left by one (`b{i+1} <- b{i}`), and the bit shifted in at
the right `b0` is the XOR of four *tap* positions:

<div style="overflow-x:auto">
<svg viewBox="0 30 800 176" role="img" aria-labelledby="lfsr-title"
     style="width:100%;min-width:620px;height:auto;max-width:800px;color:inherit"
     xmlns="http://www.w3.org/2000/svg">
  <title id="lfsr-title">A 16-bit Fibonacci LFSR. The bits b3, b12, b14 and b15
  are XORed together and fed back into b0, while every bit shifts one place
  toward b15.</title>
  <defs>
    <marker id="lfsr-arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="5" markerHeight="5" orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" stroke="none"/>
    </marker>
  </defs>
  <g stroke="currentColor" fill="none" stroke-width="1.6"
     marker-end="url(#lfsr-arrow)">
    <!-- feedback bus, running right to left along the top -->
    <path d="M 742 157 L 742 50 L 651 50"/>
    <path d="M 629 50 L 571 50"/>
    <path d="M 549 50 L 211 50"/>
    <path d="M 189 50 L 28 50 L 28 157 L 58 157"/>
    <!-- taps rising from b3, b12 and b14 -->
    <path d="M 200 140 L 200 61"/>
    <path d="M 560 140 L 560 61"/>
    <path d="M 640 140 L 640 61"/>
    <!-- the bit shifted out of b15 -->
    <path d="M 700 157 L 790 157"/>
  </g>
  <!-- the register: b0 on the left, b15 on the right -->
  <g stroke="currentColor" stroke-width="1.6">
    <rect x="60" y="140" width="640" height="34" fill="none"/>
    <g fill="currentColor" fill-opacity="0.10">
      <rect x="180" y="140" width="40" height="34"/>
      <rect x="540" y="140" width="40" height="34"/>
      <rect x="620" y="140" width="40" height="34"/>
      <rect x="660" y="140" width="40" height="34"/>
    </g>
    <g fill="none" stroke-opacity="0.55">
      <path d="M 100 140 L 100 174"/><path d="M 140 140 L 140 174"/>
      <path d="M 180 140 L 180 174"/><path d="M 220 140 L 220 174"/>
      <path d="M 260 140 L 260 174"/><path d="M 300 140 L 300 174"/>
      <path d="M 340 140 L 340 174"/><path d="M 380 140 L 380 174"/>
      <path d="M 420 140 L 420 174"/><path d="M 460 140 L 460 174"/>
      <path d="M 500 140 L 500 174"/><path d="M 540 140 L 540 174"/>
      <path d="M 580 140 L 580 174"/><path d="M 620 140 L 620 174"/>
      <path d="M 660 140 L 660 174"/>
    </g>
    <!-- the three XOR gates on the feedback bus -->
    <g fill="none">
      <circle cx="640" cy="50" r="11"/><path d="M 629 50 L 651 50 M 640 39 L 640 61"/>
      <circle cx="560" cy="50" r="11"/><path d="M 549 50 L 571 50 M 560 39 L 560 61"/>
      <circle cx="200" cy="50" r="11"/><path d="M 189 50 L 211 50 M 200 39 L 200 61"/>
    </g>
    <circle cx="742" cy="157" r="3.5" fill="currentColor"/>
  </g>
  <g fill="currentColor" font-family="ui-monospace,SFMono-Regular,Menlo,monospace"
     font-size="11" text-anchor="middle">
    <text x="80"  y="192">b0</text>  <text x="120" y="192">b1</text>
    <text x="160" y="192">b2</text>  <text x="200" y="192">b3</text>
    <text x="240" y="192">b4</text>  <text x="280" y="192">b5</text>
    <text x="320" y="192">b6</text>  <text x="360" y="192">b7</text>
    <text x="400" y="192">b8</text>  <text x="440" y="192">b9</text>
    <text x="480" y="192">b10</text> <text x="520" y="192">b11</text>
    <text x="560" y="192">b12</text> <text x="600" y="192">b13</text>
    <text x="640" y="192">b14</text> <text x="680" y="192">b15</text>
  </g>
</svg>
</div>

The shaded cells are the four taps. Their values are XORed together on the way
around the top and fed back into `b0`, while every bit slides one place toward
`b15` and the old `b15` drops off the right-hand end:

```
new_bit = b15 ^ b14 ^ b12 ^ b3
state   = (state << 1) | new_bit          keeping 16 bits
```

{: .note }
> The diagram puts `b0` on the left, so the bits travel left to right — the value
> in `b0` moves to `b1`, `b1` to `b2`, and so on. That *is* a left shift: every
> bit moves to the next **higher** position. It only looks like a right shift
> because a binary number is normally written with `b15` on the left.

## Why these taps

The XOR combination describing the update for `b0` is sometimes described by a *polynomial*.  In the `L=16` case above, the polynomial is x<sup>16</sup> + x<sup>15</sup> +
x<sup>13</sup> + x<sup>4</sup> + 1, which is **primitive**: the state visits all
65535 nonzero values before it repeats.

That is not a property you get for free. Most tap sets give much shorter periods,
and some give dramatically shorter ones — a generator that cycles after a few
hundred values will still look plausible in a histogram while being useless. Tap
sets for each width are tabulated rather than derived by hand; this one is a
standard choice for 16 bits.

## Zero is a fixed point

Shift zero left and XOR it with nothing, and it is still zero. A seed of 0
therefore produces an infinite stream of zeros, forever.

This is why the seed is nonzero, and it is the first thing to check if your
generator produces nothing but 0. It is also why the maximum period is 65535
rather than 65536: the all-zero state is not part of the cycle, because nothing
can ever enter or leave it.

## Getting multi-bit samples

Each step above produces exactly **one** new bit.  So, if you want samples that are `NBITS` bits, you need to run the LFSR `NBITS` times.  In this lab, we will take `NBITS=8`, so each sample is an 8-bit number.  You can then think of the pseudo-random number generator (PRNG) as producing a sequence of random values from 0 to `2^{NBITS}-1=255`.  We often scale the values by `2^{NBITS}` so the value is between 0 and 1.

Note that taking a sample after every single step instead would leave consecutive samples
sharing seven of their eight bits. The histogram would still look flat — every
value would still occur about equally often — and the numbers would be nothing
like independent. That failure is invisible to the eye and obvious to a
correlation measurement, which is the subject of
[Evaluating before you build](./evaluate.md).

You write that eight-step loop **twice**: once in Python as `prng_sample`, and
once in SystemVerilog inside the testbench. It is the same loop both times, and
writing it in two languages that look nothing alike is much of the point of the
lab.

## A closing note on "random"

Your generator will pass every check in this lab, and it is still not secure. An
LFSR is completely linear: given 32 consecutive output bits, anyone can solve for
the state and predict the entire rest of the sequence, forwards and backwards.

That is fine for the jobs LFSRs actually do — test patterns, scrambling,
dithering — and fatal for anything protecting a secret. That gap is where stream
ciphers begin, and it is worth remembering the next time something is described
as "random".

----

Go to [the Python model](./python.md)
