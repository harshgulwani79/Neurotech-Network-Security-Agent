"""
Telemetry Generator - Creates both historical CSV data and real-time simulated anomalies

This module generates synthetic network telemetry data that follows the same format
as required by the agent.py for consistent processing across both modes.
"""

import pandas as pd
import numpy as np
import random
import time

# Device list matching topology.json
DEVICES = [
    "Mumbai-Core-01", "Delhi-Edge-05", "Bangalore-Core-02",
    "NYC-Peering-01", "Chennai-Link-03", "London-Core-01", "Frankfurt-Core-02"
]

# ─────────────────────────────────────────────────────────────
# NORMAL OPERATING RANGES
# ─────────────────────────────────────────────────────────────
# latency:        10 – 30 ms   (mean 20, std 3)
# packet_loss:     0 – 0.3 %   (uniform)
# bgp_flaps:       0           (never flaps during normal ops)
# throughput:     35 – 55 Gbps (mean 45, std 4)


def generate_normal_telemetry(count: int = 100) -> list:
    """Generate normal (healthy) telemetry records."""
    data = []
    for _ in range(count):
        data.append({
            "device": random.choice(DEVICES),
            "latency": max(5, np.random.normal(20, 3)),
            "packet_loss": np.random.uniform(0.0, 0.3),
            "bgp_flaps": 0,
            "throughput_gbps": max(20, np.random.normal(45, 4)),
            "label": "normal"
        })
    return data


def generate_tier1_anomaly() -> dict:
    """Tier 1: Minor degradation - Auto-fix (rate limiting / QoS)"""
    return {
        "device": random.choice(DEVICES),
        "latency": random.uniform(55, 70),
        "packet_loss": random.uniform(1.0, 2.0),
        "bgp_flaps": 0,
        "throughput_gbps": random.uniform(22, 28),
        "label": "tier1"
    }


def generate_tier2_anomaly() -> dict:
    """Tier 2: Moderate degradation - Human approval required"""
    return {
        "device": random.choice(DEVICES),
        "latency": random.uniform(150, 300),
        "packet_loss": random.uniform(5.0, 12.0),
        "bgp_flaps": 1,
        "throughput_gbps": random.uniform(10, 15),
        "label": "tier2"
    }


def generate_tier3_anomaly() -> dict:
    """Tier 3: Severe / Critical - Must escalate"""
    return {
        "device": random.choice(DEVICES),
        "latency": random.uniform(350, 1200),
        "packet_loss": random.uniform(12.0, 60.0),
        "bgp_flaps": random.randint(3, 25),
        "throughput_gbps": random.uniform(0.1, 6),
        "label": "tier3"
    }


def generate_csv_dataset(count: int = 10000) -> pd.DataFrame:
    """Generate a complete CSV dataset with normal data and anomalies."""
    print(f"Generating {count:,} network telemetry records...")
    
    # Calculate anomaly count based on 0.1% contamination
    anomaly_count = max(7, int(count * 0.001))
    normal_count = count - anomaly_count
    
    # Generate normal data
    data = generate_normal_telemetry(normal_count)
    
    # Distribute anomalies across tiers
    tier1_count = max(2, anomaly_count // 4)
    tier2_count = max(2, anomaly_count // 4)
    tier3_count = anomaly_count - tier1_count - tier2_count
    
    # Generate anomalies
    for _ in range(tier1_count):
        data.append(generate_tier1_anomaly())
    
    for _ in range(tier2_count):
        data.append(generate_tier2_anomaly())
    
    for _ in range(tier3_count):
        data.append(generate_tier3_anomaly())
    
    # Create DataFrame and shuffle
    df = pd.DataFrame(data)
    df = df.sample(frac=1).reset_index(drop=True)
    
    return df


def save_csv(df: pd.DataFrame, filepath: str = "backend/telemetry_stream.csv"):
    """Save DataFrame to CSV."""
    df.to_csv(filepath, index=False)
    print(f"✅ Saved {len(df):,} records to {filepath}")
    
    # Print summary
    normal_count = len(df[df["label"] == "normal"])
    tier1 = len(df[df["label"] == "tier1"])
    tier2 = len(df[df["label"] == "tier2"])
    tier3 = len(df[df["label"] == "tier3"])
    
    print(f"   ├─ {normal_count:,} NORMAL records")
    print(f"   ├─ {tier1} Tier 1 anomalies → auto-fix")
    print(f"   ├─ {tier2} Tier 2 anomalies → human approval")
    print(f"   └─ {tier3} Tier 3 anomalies → escalate")


def generate_realtime_metrics() -> list:
    """
    Generate real-time metrics for the simulator.
    Returns a list of metrics in the format expected by the network simulator.
    """
    metrics = []
    
    # 10% chance of generating an anomaly
    anomaly_chance = 0.10
    
    for device in DEVICES:
        if random.random() < anomaly_chance:
            # Generate an anomaly
            tier = random.choice([1, 1, 1, 2, 2, 3])  # Weighted towards lower tiers
            
            if tier == 1:
                anomaly = generate_tier1_anomaly()
                anomaly["device"] = device
            elif tier == 2:
                anomaly = generate_tier2_anomaly()
                anomaly["device"] = device
            else:
                anomaly = generate_tier3_anomaly()
                anomaly["device"] = device
            
            metrics.append({
                "device": device,
                "latency": anomaly["latency"],
                "loss": anomaly["packet_loss"],
                "utilization": anomaly["throughput_gbps"],
                "bgp_flaps": anomaly["bgp_flaps"],
                "label": anomaly["label"],
                "is_anomaly": True,
                "timestamp": time.time()
            })
        else:
            # Normal metrics
            metrics.append({
                "device": device,
                "latency": max(5, np.random.normal(20, 3)),
                "loss": np.random.uniform(0.0, 0.3),
                "utilization": max(20, np.random.normal(45, 4)),
                "bgp_flaps": 0,
                "label": "normal",
                "is_anomaly": False,
                "timestamp": time.time()
            })
    
    return metrics


def get_anomaly_injection_metrics(anomaly_type: str = "congestion") -> list:
    """
    Generate metrics with a specific injected anomaly.
    Used when user clicks "Inject Congestion" or "Inject Failure" buttons.
    """
    metrics = []
    
    # Pick a random device for the anomaly
    target_device = random.choice(DEVICES)
    
    for device in DEVICES:
        if device == target_device:
            if anomaly_type == "congestion":
                # High utilization, elevated latency and loss
                metrics.append({
                    "device": device,
                    "latency": np.random.uniform(55, 120),
                    "loss": np.random.uniform(1.0, 5.0),
                    "utilization": np.random.uniform(85, 98),
                    "bgp_flaps": 0,
                    "label": "tier1",
                    "is_anomaly": True,
                    "injected": True,
                    "anomaly_type": "congestion",
                    "timestamp": time.time()
                })
            elif anomaly_type == "failure":
                # Link failure - very high loss, possible latency
                metrics.append({
                    "device": device,
                    "latency": np.random.uniform(100, 500),
                    "loss": np.random.uniform(15, 50),
                    "utilization": np.random.uniform(5, 20),
                    "bgp_flaps": random.randint(3, 10),
                    "label": "tier3",
                    "is_anomaly": True,
                    "injected": True,
                    "anomaly_type": "failure",
                    "timestamp": time.time()
                })
            else:
                # Unknown type, treat as tier2
                metrics.append({
                    "device": device,
                    "latency": np.random.uniform(150, 300),
                    "loss": np.random.uniform(5, 12),
                    "utilization": np.random.uniform(10, 30),
                    "bgp_flaps": 1,
                    "label": "tier2",
                    "is_anomaly": True,
                    "injected": True,
                    "anomaly_type": anomaly_type,
                    "timestamp": time.time()
                })
        else:
            # Normal metrics for other devices
            metrics.append({
                "device": device,
                "latency": max(5, np.random.normal(20, 3)),
                "loss": np.random.uniform(0.0, 0.3),
                "utilization": max(20, np.random.normal(45, 4)),
                "bgp_flaps": 0,
                "label": "normal",
                "is_anomaly": False,
                "injected": False,
                "timestamp": time.time()
            })
    
    return metrics


# ── STANDALONE RUNNER ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Generate CSV dataset
    df = generate_csv_dataset(10000)
    save_csv(df)
    
    print("\n" + "="*60)
    print("Testing real-time generation...")
    print("="*60)
    
    # Test real-time metrics
    rt_metrics = generate_realtime_metrics()
    anomalies = [m for m in rt_metrics if m["is_anomaly"]]
    print(f"Generated {len(rt_metrics)} real-time metrics")
    print(f"Anomalies: {len(anomalies)}")
    for a in anomalies:
        print(f"  - {a['device']}: {a['label']} (lat={a['latency']:.1f}ms, loss={a['loss']:.1f}%)")

