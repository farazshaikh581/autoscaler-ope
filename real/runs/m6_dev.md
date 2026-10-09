# M6 development: twin variants on W1-W3 (24 cells, hpa70 excluded)

| variant | donors | median SLA err | max SLA err | median cost err % | within 3 pts & 15% | in sens. interval | in interval + run noise |
|---|---|---|---|---|---|---|---|
| M5 twin | all 4 logs | 1.8 | 6.8 | 3.7 | 11/24 | 71% | 92% |
| no lag | all 4 logs | 2.6 | 14.9 | 10.2 | 9/24 | 50% | 71% |
| no change flag | all 4 logs | 1.6 | 6.7 | 3.4 | 11/24 | 75% | 96% |
| no rescale | all 4 logs | 1.7 | 6.5 | 2.7 | 11/24 | 67% | 83% |
| K=5 | all 4 logs | 2.3 | 7.5 | 3.3 | 11/24 | 62% | 83% |
| K=20 | all 4 logs | 1.8 | 5.5 | 4.1 | 12/24 | 62% | 88% |
| log-only scale (m=1.51, lin<0.66) | all 4 logs | 0.7 | 6.6 | 2.0 | 6/8 | 75% | 88% |
| M5 twin | eps 0 only | 1.5 | 6.2 | 4.5 | 14/24 | 67% | 88% |
| M5 twin | eps 0.1 only | 1.5 | 6.5 | 2.6 | 13/24 | 67% | 88% |
| M5 twin | 1 log (eps 0 r1) | 1.5 | 6.3 | 3.6 | 14/24 | 67% | 88% |
| log-only scale (m=1.68, lin<0.57) | all 4 logs | 1.6 | 5.7 | 5.5 | 5/8 | 75% | 88% |
| log-only scale (m=1.76, lin<0.01) | all 4 logs | 3.7 | 5.1 | 4.0 | 2/8 | 50% | 88% |
