# M7: a knee-density flag for the twin, tested on new loggers (saul)

Fixed before any M7 run. The flag is the one in `ope/twin.py` as committed with this
file (KNEE_WIDTH, KNEE_MIX, FLAG_KNEE). The estimator is still `twin_v2`, unchanged
since M6. Analysis: `real/m7_report.py`.

## Why

In M6 the twin was accurate from the behaviour's own logs. From the logs of other
behaviour policies on W1 it missed by 7-29 SLA points on 6 targets. The
distance-only diagnostic (`far_share`) did not catch them, so criterion L2 failed.
- HPA-50 logs rarely visit the knee.
- HPA-85 logs sit mostly in saturation.
In both cases the twin interpolates across the knee, where the SLA flips, from
sparse donors.

## Flag (development: `real/m7_dev.py`, `real/runs/m7_dev_cells.csv`, 48 cells)

`knee_share` is the share of rollout steps where both hold:
- the K = 10 matched donors disagree on the SLA outcome (between 10% and 90% of
  them meet it);
- they span more than 0.15 in the matching metric.

An estimate is flagged when `knee_share` > 0.20.

On the development cells, the flag catches every error above 6.5 points (6 cells,
all from the other-logger runs). It flags none of the 32 own-logger cells and
raises 2 false alarms (errors 2.2 and 2.5). Deep-saturation targets (SLA 0) are not
flagged, because their donors agree, which is correct. `far_share` flagged those
targets and missed the knee cases.

## Runs (`real/m7.sh`, 8 x about 52 min = about 7 h)

Logs from dithered HPA-85 x 2 and HPA-50 x 2 (eps 0.1), on W3 and W4. Truth runs for
the 8 targets already exist (W3: two runs per target, W4: one), so all 32 cells are
new combinations of logs and truth.

## Criteria (32 cells; large error = |SLA error| > 6, about 2.5 x the run-to-run SD)

- **D1:** every cell with a large error is flagged.
- **D2:** the unflagged cells' median |SLA error| is <= 3 points.

Also reported: the false-alarm count (flagged with error <= 3), the twin and
baseline accuracy per logger, and `far_share` for comparison.
