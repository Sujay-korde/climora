"""CLIMORA Phase 2B Performance & Zonal Query Benchmarking Script.

Measures cold vs warm latency, response sizes, serialization times, and cache hit rates
across the core analytical endpoints, comparing Phase 2B against the Phase 2A baseline.
"""

from __future__ import annotations

import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Dict, List

# Ensure workspace root is in sys.path
workspace_root = Path(__file__).resolve().parent.parent
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

import pandas as pd

from api.app import create_app
from services.project_service import CANONICAL_PROJECT_ID


# Baseline numbers recorded prior to Phase 2B optimizations
PHASE_2A_BASELINES = {
    "/projects": {"cold_ms": 0.615, "warm_avg_ms": 0.191, "size_bytes": 1519},
    f"/projects/{CANONICAL_PROJECT_ID}": {"cold_ms": 0.349, "warm_avg_ms": 0.202, "size_bytes": 5220},
    f"/projects/{CANONICAL_PROJECT_ID}/allocation": {"cold_ms": 2.861, "warm_avg_ms": 2.272, "size_bytes": 12872},
    f"/projects/{CANONICAL_PROJECT_ID}/baseline": {"cold_ms": 5.491, "warm_avg_ms": 4.912, "size_bytes": 38333},
    f"/projects/{CANONICAL_PROJECT_ID}/mrv": {"cold_ms": 0.421, "warm_avg_ms": 0.324, "size_bytes": 888},
}


def benchmark_suite(n_warm_rounds: int = 50) -> Dict[str, Any]:
    print("=" * 80)
    print("CLIMORA PHASE 2B PERFORMANCE & QUERY BENCHMARK")
    print("=" * 80)

    # 1. Measure Application & ZonalQueryEngine Initialization
    t0 = time.perf_counter()
    app = create_app()
    app.config["TESTING"] = True
    init_time_ms = round((time.perf_counter() - t0) * 1000, 3)
    print(f"[*] Application + ZonalQueryEngine Init Time: {init_time_ms:.3f} ms")

    client = app.test_client()

    endpoints = [
        "/projects",
        f"/projects/{CANONICAL_PROJECT_ID}",
        f"/projects/{CANONICAL_PROJECT_ID}/allocation",
        f"/projects/{CANONICAL_PROJECT_ID}/baseline",
        f"/projects/{CANONICAL_PROJECT_ID}/mrv",
    ]

    results = {}

    for ep in endpoints:
        # Cold request (fresh cache)
        t_cold_0 = time.perf_counter()
        resp_cold = client.get(ep)
        t_cold_ms = round((time.perf_counter() - t_cold_0) * 1000, 3)
        assert resp_cold.status_code == 200, f"Endpoint {ep} failed with {resp_cold.status_code}"
        size_bytes = len(resp_cold.data)

        # Warm requests
        warm_times = []
        for _ in range(n_warm_rounds):
            t_warm_0 = time.perf_counter()
            resp_warm = client.get(ep)
            warm_times.append((time.perf_counter() - t_warm_0) * 1000)

        warm_avg_ms = round(statistics.mean(warm_times), 3)
        warm_p50_ms = round(statistics.median(warm_times), 3)
        warm_p95_ms = round(statistics.quantiles(warm_times, n=20)[18], 3)
        warm_min_ms = round(min(warm_times), 3)
        warm_max_ms = round(max(warm_times), 3)

        b2a = PHASE_2A_BASELINES.get(ep, {})
        b2a_warm = b2a.get("warm_avg_ms", 1.0)
        speedup = round((b2a_warm / warm_avg_ms), 2) if warm_avg_ms > 0 else 1.0

        results[ep] = {
            "endpoint": ep,
            "cold_ms": t_cold_ms,
            "warm_avg_ms": warm_avg_ms,
            "warm_p50_ms": warm_p50_ms,
            "warm_p95_ms": warm_p95_ms,
            "warm_min_ms": warm_min_ms,
            "warm_max_ms": warm_max_ms,
            "size_bytes": size_bytes,
            "baseline_2a_warm_ms": b2a_warm,
            "speedup_vs_phase_2a": f"{speedup}x",
        }

    # 2. Cache Telemetry
    engine = app.config.get("QUERY_ENGINE")
    cache_stats = engine.cache.stats if engine else {}

    print("\nBENCHMARK RESULTS SUMMARY:")
    print("-" * 100)
    fmt = "{:<45} | {:<9} | {:<11} | {:<11} | {:<10} | {:<10} | {:<8}"
    print(fmt.format("Endpoint", "Cold (ms)", "WarmAvg(ms)", "Phase2A(ms)", "Speedup", "Size(bytes)", "p95 (ms)"))
    print("-" * 100)
    for ep, r in results.items():
        print(fmt.format(
            ep,
            f"{r['cold_ms']:.2f}",
            f"{r['warm_avg_ms']:.3f}",
            f"{r['baseline_2a_warm_ms']:.3f}",
            r["speedup_vs_phase_2a"],
            r["size_bytes"],
            f"{r['warm_p95_ms']:.3f}",
        ))
    print("-" * 100)
    print("\nCACHE TELEMETRY:")
    for k, v in cache_stats.items():
        print(f"  {k}: {v}")
    print("=" * 80)

    return {"results": results, "cache_stats": cache_stats, "init_time_ms": init_time_ms}


if __name__ == "__main__":
    benchmark_suite()
