# Honesty box

> The sample projects are synthetic and sized for a demo. Absolute numbers depend on your project's
> module graph, change patterns and machines. Treat the showcase as a demonstration of
> **mechanisms and symptoms**, not as a promise of a specific speed-up. For a realistic estimate,
> benchmark on your own commit history starting from an empty cache.

This note appears in `README.md`, every rendered report (`tools/report/render.py`), and here. It is
load-bearing, not boilerplate: see `docs/concepts/metrics.md` for why a single hit-rate or ratio
number is easy to misread, and `docs/concepts/isolation.md` for the test-harness device that makes
seed/measure comparisons honest within one pipeline run.
