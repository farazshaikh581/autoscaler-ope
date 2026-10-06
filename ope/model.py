"""Outcome models learned from logs only.

Inputs are what an operator records after each decision: offered load (exogenous),
serving replicas, CPU request, steps until a pending scale lands, and pending
replicas. Outputs are the observed metrics the controllers and the SLA check use:
latency, success, CPU utilisation and rho (demand / capacity).

  TreeModel  gradient-boosted trees on the raw features (generic, no structure)
  KneeModel  latency/success as a sigmoid knee in load per vCPU, rho linear in it

KneeModel's functional form is generic queueing intuition (latency flat, then a
knee once load per unit of capacity passes a threshold). It also happens to match
the simulator's own family, which the author had read, so its results are an
optimistic case.
"""
import os
import sys
import warnings

import numpy as np

_DEPS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".deps")
if _DEPS not in sys.path:
    sys.path.append(_DEPS)          # after site-packages, so numpy stays the venv's

from scipy.optimize import curve_fit  # noqa: E402
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: E402

OUTPUTS = ("latency", "success", "cpu_util", "rho")


def features(load, replicas, cpu_req, steps_to_ready, pending):
    return np.column_stack([load, replicas, cpu_req, steps_to_ready, pending]).astype(float)


def training_data(log: dict):
    o = log["out"].reshape(-1)
    x = features(log["load"].reshape(-1), o["replicas"], o["cpu_req"], o["steps_to_ready"],
                 o["target_replicas"] - o["replicas"])
    y = {k: o[k].astype(float) for k in OUTPUTS}
    return x, y


class TreeModel:
    """Gradient-boosted trees. The trees only split on the per-feature bin edges
    learned at fit time, so the prediction is constant within each cell of the bin
    grid. After fitting, every grid cell is predicted once into a lookup table and
    predict() just bins the query: identical output, about 1000x faster."""
    name = "trees"

    def fit(self, x, y):
        self.m = {}
        for k in OUTPUTS:
            target = np.log(y[k]) if k == "latency" else y[k]
            self.m[k] = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.1,
                                                      random_state=0).fit(x, target)
        self._build_table()
        return self

    def _build_table(self):
        mappers = [self.m[k]._bin_mapper.bin_thresholds_ for k in OUTPUTS]
        for other in mappers[1:]:                 # same X and seed -> same bins
            assert all(np.array_equal(a, b) for a, b in zip(mappers[0], other))
        self.edges = mappers[0]
        reps = []
        for th in self.edges:                     # one representative value per bin
            th = np.asarray(th, float)
            if len(th) == 0:
                reps.append(np.array([0.0]))
                continue
            inner = (th[:-1] + th[1:]) / 2
            reps.append(np.concatenate([[th[0] - 1.0], inner, [th[-1] + 1.0]]))
        grid = np.stack(np.meshgrid(*reps, indexing="ij"), axis=-1).reshape(-1, len(reps))
        self.shape = tuple(len(r) for r in reps)
        self.table = {k: self.m[k].predict(grid).reshape(self.shape) for k in OUTPUTS}

    def _bins(self, x):
        # HistGB bins a value v into the first bin whose threshold is >= v
        return tuple(np.searchsorted(np.asarray(th, float), x[:, f], side="left") if len(th)
                     else np.zeros(len(x), int) for f, th in enumerate(self.edges))

    def predict(self, x):
        b = self._bins(x)
        out = {k: self.table[k][b] for k in OUTPUTS}
        out["latency"] = np.exp(out["latency"])
        return out

    def predict_direct(self, x):
        out = {k: self.m[k].predict(x) for k in OUTPUTS}
        out["latency"] = np.exp(out["latency"])
        return out


def _sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60, 60)))


class KneeModel:
    name = "knee"

    @staticmethod
    def load_per_vcpu(x):
        return x[:, 0] / np.maximum(x[:, 1] * x[:, 2] / 1000.0, 1e-6)

    def fit(self, x, y):
        u = self.load_per_vcpu(x)
        lat, suc = y["latency"], y["success"]
        lo, hi = np.percentile(lat, 5), lat.max()
        above = u[lat > (lo + hi) / 2]
        c0 = float(above.min()) if len(above) else float(u.max()) * 1.2
        self.fit_ok = True
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.lat_p, _ = curve_fit(lambda u, a, b, c, d: a + b * _sig((u - c) / d), u, lat,
                                          p0=[lo, max(hi - lo, 1e-3), c0, 0.05 * c0],
                                          bounds=([0, 0, 0, 1e-4], [np.inf, np.inf, np.inf, np.inf]),
                                          maxfev=20000)
        except Exception:
            self.fit_ok = False
            self.lat_p = np.array([lat.mean(), 0.0, c0, 1.0])
        c, d = self.lat_p[2], self.lat_p[3]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.suc_p, _ = curve_fit(
                    lambda u, e, f, g: 1 - e * _sig((u - c) / d) - f * np.maximum(u - g, 0), u, suc,
                    p0=[max(1 - suc.min(), 1e-3), 0.0, float(u.max())],
                    bounds=([0, 0, 0], [1, np.inf, np.inf]), maxfev=20000)
        except Exception:
            self.fit_ok = False
            self.suc_p = np.array([1 - suc.mean(), 0.0, float(u.max())])
        rho = y["rho"]
        self.h = float((u * rho).sum() / max((u * u).sum(), 1e-12))     # rho = h * u
        self.util_cap = float(y["cpu_util"].max())
        return self

    def predict(self, x):
        u = self.load_per_vcpu(x)
        a, b, c, d = self.lat_p
        e, f, g = self.suc_p
        rho = self.h * u
        return {"latency": a + b * _sig((u - c) / d),
                "success": np.clip(1 - e * _sig((u - c) / d) - f * np.maximum(u - g, 0), 0, 1),
                "rho": rho, "cpu_util": np.minimum(rho, self.util_cap)}


MODELS = {"trees": TreeModel, "knee": KneeModel}
