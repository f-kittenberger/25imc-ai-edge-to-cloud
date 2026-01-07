
#!/usr/bin/env python3
"""
Choose the greenest deployment region based on carbon intensity from Prometheus.
- Queries Prometheus for `carbon_intensity_gco2_per_kwh{zone=...}`.
- Ranks candidate zones by lowest gCO2/kWh.
- Outputs the recommended cloud region and CI value.
- Optional threshold: fail/skip if CI is above a maximum.

Usage:
    python choose_green_region.py \
        --prom-url http://prometheus:9090 \
        --zones AT DE FR \
        --metric carbon_intensity_gco2_per_kwh \
        --max-ci 250 \
        --format text

Exit codes:
    0 on success
    1 if no valid data or all zones exceed max-ci (when provided)
"""

import argparse
import sys
import time
import os
import json
from typing import Dict, List, Optional, Tuple
import requests
from dotenv import load_dotenv

# Load .env file into environment
load_dotenv(dotenv_path="../docker")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Choose the greenest deployment region.")

    p.add_argument(
        "--prom-url",
        default=os.getenv("PROM_URL"),
        help="Prometheus base URL (e.g., http://prometheus:9090). Defaults to PROM_URL from .env if set."
    )

    p.add_argument(
        "--zones",
        nargs="+",
        default=os.getenv("ELECTRICITYMAP_ZONES").replace(',', ' ').split() if os.getenv("ELECTRICITYMAP_ZONES") else None,
        help="Candidate zones (e.g., AT DE FR). Defaults to ELECTRICITYMAP_ZONES from .env if set."
    )

    p.add_argument(
        "--metric",
        default=os.getenv("METRIC", "carbon_intensity_gCo2perkWh"),
        help="Metric name in Prometheus. Defaults to METRIC from .env or carbon_intensity_gco2_per_kwh."
    )

    p.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "5")),
        help="HTTP timeout in seconds (default: 5)."
    )

    p.add_argument(
        "--max-ci",
        type=float,
        default=float(os.getenv("MAX_CI")) if os.getenv("MAX_CI") else None,
        help="Optional maximum acceptable carbon intensity in gCO2/kWh."
    )

    p.add_argument(
        "--format",
        choices=["text", "json"],
        default=os.getenv("FORMAT", "text"),
        help="Output format (text/json). Default: text."
    )

    p.add_argument(
        "--region-map",
        default=os.getenv("REGION_MAP"),
        help="Path to JSON file mapping zones to cloud regions. Defaults to REGION_MAP from .env."
    )

    return p.parse_args()


def load_region_map(path: Optional[str]) -> Dict[str, str]:
    if not path:
        # Default map: adjust to your cloud/provider
        return {
            "AT": "europe-west3",  # Frankfurt
            "DE": "europe-west3",
            "FR": "europe-west1",  # Belgium
            "NL": "europe-west4",
            "DK-DK1": "europe-north1",
            "SE-SE3": "europe-north1",
            "NO-NO2": "europe-north1",
            "IE": "europe-west1",
            "US-CENT-SPP": "us-central1",
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def query_prometheus_instant(prom_url: str, metric: str, zone: str, timeout: int = 5) -> Optional[float]:
    query = f'{metric}{{zone="{zone}"}}'
    url = f"{prom_url.rstrip('/')}:9090/api/v1/query"
    try:
        resp = requests.get(url, params={"query": query}, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "success":
            return None
        results = payload.get("data", {}).get("result", [])
        if not results:
            return None
        value_str = results[0]["value"][1]
        return float(value_str)
    except Exception:
        return None


def pick_greenest_zone(prom_url: str, metric: str, zones: List[str], timeout: int, max_ci: Optional[float]) -> Tuple[Optional[str], Dict[str, Optional[float]]]:
    ci_by_zone: Dict[str, Optional[float]] = {}
    for z in zones:
        ci = query_prometheus_instant(prom_url, metric, z, timeout=timeout)
        ci_by_zone[z] = ci
    valid = {z: ci for z, ci in ci_by_zone.items() if ci is not None}
    if not valid:
        return None, ci_by_zone
    best_zone = min(valid, key=valid.get)
    best_ci = valid[best_zone]
    if max_ci is not None and best_ci is not None and best_ci > max_ci:
        return None, ci_by_zone
    return best_zone, ci_by_zone


def main():
    args = parse_args()

    if not args.prom_url or not args.zones:
        print("Error: PROM_URL and ZONES must be provided either via .env or CLI.")
        sys.exit(1)

    region_map = load_region_map(args.region_map)
    start = time.time()
    best_zone, ci_by_zone = pick_greenest_zone(
        prom_url=args.prom_url,
        metric=args.metric,
        zones=args.zones,
        timeout=args.timeout,
        max_ci=args.max_ci,
    )
    duration_ms = int((time.time() - start) * 1000)

    def zone_to_region(z: str) -> Optional[str]:
        return region_map.get(z)
    
    # --- RESTORE LOGGING HERE (Print to stderr) ---
    print(f"[prometheus] {args.prom_url} metric={args.metric} duration={duration_ms}ms", file=sys.stderr)
    for z in args.zones:
        ci = ci_by_zone[z]
        region = zone_to_region(z)
        if ci is None:
            print(f" - {z:<12} CI=NA region={region}", file=sys.stderr)
        else:
            print(f" - {z:<12} CI={ci:>7.1f} gCO2/kWh region={region}", file=sys.stderr)
    print("", file=sys.stderr) # Add a newline for spacing
    # ----------------------------------------------

    if args.format == "json":
        out = {
            "metric": args.metric,
            "prometheus": args.prom_url,
            "duration_ms": duration_ms,
            "zones": [
                {"zone": z, "ci_gco2_per_kwh": ci_by_zone[z], "region": zone_to_region(z)}
                for z in args.zones
            ],
            "best": (
                {
                    "zone": best_zone,
                    "ci_gco2_per_kwh": None if best_zone is None else ci_by_zone[best_zone],
                    "region": None if best_zone is None else zone_to_region(best_zone),
                }
                if best_zone is not None
                else None
            ),
            "max_ci": args.max_ci,
        }
        print(json.dumps(out, indent=2))
        sys.exit(0 if best_zone else 1)

    if best_zone is None:
        if args.max_ci is not None:
            print(f"\nNo zone under threshold (max_ci={args.max_ci} gCO2/kWh).")
        else:
            print("\nNo valid CI data found.")
        sys.exit(1)



if __name__ == "__main__":
    main()