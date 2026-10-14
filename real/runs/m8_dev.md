# M8 development: queueing-model baseline on W1-W4

| window | fit | a (ms) | b (ms) | median SLA err | max SLA err | median cost err % |
|---|---|---|---|---|---|---|
| w1 | unconstrained (frozen) | -25.35 | 13.36 | 3.5 | 18.6 | 3.4 |
| w1 | non-negative | 0.00 | 4.84 | 5.3 | 35.7 | 3.4 |
| w2 | unconstrained (frozen) | 1.01 | 1.83 | 7.8 | 34.9 | 19.5 |
| w2 | non-negative | 1.01 | 1.83 | 7.8 | 34.9 | 19.5 |
| w3 | unconstrained (frozen) | -11.14 | 5.98 | 8.0 | 54.5 | 3.9 |
| w3 | non-negative | 0.00 | 3.10 | 11.1 | 59.5 | 3.9 |
| w4 | unconstrained (frozen) | 1.12 | 1.13 | 7.5 | 33.7 | 8.8 |
| w4 | non-negative | 1.12 | 1.13 | 7.5 | 33.7 | 8.8 |

All 32 cells, unconstrained (frozen) fit: median 6.7, max 54.5

All 32 cells, non-negative fit: median 8.9, max 59.5
