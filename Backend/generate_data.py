import pandas as pd
import numpy as np
import random

# ─────────────────────────────────────────────────────────────
#  NORMAL OPERATING RANGES (what healthy traffic looks like)
#  These bounds are deliberately tight so Isolation Forest
#  never confuses normal variance with a real anomaly.
#
#  latency:        10 – 30 ms   (mean 20, std 3)
#  packet_loss:     0 – 0.3 %   (uniform)
#  bgp_flaps:       0            (never flaps during normal ops)
#  throughput:     35 – 55 Gbps (mean 45, std 4)
# ─────────────────────────────────────────────────────────────

def generate_massive_telemetry():
    print("Generating 10,000 network telemetry records...")
    devices = ["Mumbai-Core-01", "Delhi-Edge-05", "Bangalore-Core-02",
               "NYC-Peering-01", "Chennai-Link-03"]

    # ── NORMAL DATA (9,983 rows) ──────────────────────────────
    # Tight distributions — no outliers that could confuse the ML model.
    data = []
    for _ in range(9984):
        data.append({
            "device":           random.choice(devices),
            "latency":          max(5, np.random.normal(20, 3)),    # 10–30 ms, hard floor at 5
            "packet_loss":      np.random.uniform(0.0, 0.3),        # 0–0.3%
            "bgp_flaps":        0,                                   # always 0 when healthy
            "throughput_gbps":  max(20, np.random.normal(45, 4)),   # 35–55 Gbps
            "label":            "normal"
        })

    # ── TIER 1 ANOMALIES: Minor degradation (2 events) ───────
    # Auto-fix: rate limiting / QoS tweak — no human needed.
    # Values are clearly outside normal range but not catastrophic.
    #   latency:     55–70 ms   (2× normal ceiling)
    #   packet_loss: 1.0–2.0%  (3–7× normal ceiling)
    #   bgp_flaps:   0
    #   throughput:  22–28 Gbps (half of normal)
    tier1 = [
        {"device": "Delhi-Edge-05",   "latency": 55,  "packet_loss": 1.2, "bgp_flaps": 0, "throughput_gbps": 28.0, "label": "tier1"},
        {"device": "Chennai-Link-03", "latency": 65,  "packet_loss": 1.5, "bgp_flaps": 0, "throughput_gbps": 26.0, "label": "tier1"},
    ]

    # ── TIER 2 ANOMALIES: Moderate degradation (2 events) ────
    # Human approval required: traffic rerouting / config change.
    #   latency:     150–190 ms  (5–6× normal)
    #   packet_loss: 5.0–7.0%   (17–23× normal)
    #   bgp_flaps:   1           (first sign of routing instability)
    #   throughput:  10–15 Gbps  (severe drop)
    tier2 = [
        {"device": "NYC-Peering-01",  "latency": 250, "packet_loss": 10.0, "bgp_flaps": 0, "throughput_gbps": 7.0, "label": "tier2"},
        {"device": "Mumbai-Core-01",  "latency": 300, "packet_loss": 12.0, "bgp_flaps": 0, "throughput_gbps": 5.0, "label": "tier2"},
    ]

    # ── TIER 3 ANOMALIES: Severe / critical (3 events) ───────
    # Escalate to L3 engineering — do NOT auto-fix.
    #   latency:     350–600 ms  (12–20× normal)
    #   packet_loss: 12–25%      (40–83× normal)
    #   bgp_flaps:   3–6         (routing collapse)
    #   throughput:  1–6 Gbps    (near-zero)
    tier3 = [
        {"device": "Mumbai-Core-01",    "latency": 900, "packet_loss": 45.0, "bgp_flaps": 20, "throughput_gbps": 0.3, "label": "tier3"},
        {"device": "Bangalore-Core-02", "latency": 1200,"packet_loss": 60.0, "bgp_flaps": 25, "throughput_gbps": 0.1, "label": "tier3"},
    ]

    all_anomalies = tier1 + tier2 + tier3   # 7 total
    data.extend(all_anomalies)

    df = pd.DataFrame(data)
    df = df.sample(frac=1).reset_index(drop=True)   # shuffle so anomalies aren't bunched at end
    df.to_csv("telemetry_stream.csv", index=False)

    total     = len(df)
    n_normal  = len([r for r in data if r["label"] == "normal"])
    pct       = len(all_anomalies) / total * 100

    print(f"\n✅ Saved {total:,} records to telemetry_stream.csv")
    print(f"   ├─ {n_normal:,} NORMAL records  →  latency 10–30ms, loss 0–0.3%, 0 BGP flaps")
    print(f"   ├─ {len(tier1)} Tier 1 anomalies →  latency 55–70ms,  loss 1–2%,   0 BGP flaps  [auto-fix]")
    print(f"   ├─ {len(tier2)} Tier 2 anomalies →  latency 150–190ms, loss 5–7%,  1 BGP flap   [human approval]")
    print(f"   └─ {len(tier3)} Tier 3 anomalies →  latency 350–600ms, loss 12–25%, 3–6 flaps   [escalate]")
    print(f"\n   📊 Anomaly rate: {pct:.2f}%  (contamination param should match this → 0.001)")
    print(f"\n   🧪 Normal operating bands for reference:")
    normal_df = df[df["label"] == "normal"]
    print(f"      latency:        {normal_df['latency'].min():.1f} – {normal_df['latency'].max():.1f} ms")
    print(f"      packet_loss:    {normal_df['packet_loss'].min():.3f} – {normal_df['packet_loss'].max():.3f} %")
    print(f"      throughput:     {normal_df['throughput_gbps'].min():.1f} – {normal_df['throughput_gbps'].max():.1f} Gbps")

if __name__ == "__main__":
    generate_massive_telemetry()