from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

MEMORY_FILE = "network_memory.json"
AUDIT_LOG = "audit_log.txt"
TOPOLOGY_FILE = "topology.json"

# -------------------------------
# LOAD DATA
# -------------------------------

def load_telemetry():
    try:
        if os.path.exists('telemetry_stream.csv'):
            df = pd.read_csv('telemetry_stream.csv')
            return df.to_dict('records')
    except Exception as e:
        print("Telemetry error:", e)
    return []


def load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE) as f:
                return json.load(f)
    except:
        pass
    return []


def load_audit_log():
    try:
        if os.path.exists(AUDIT_LOG):
            with open(AUDIT_LOG) as f:
                return f.read().strip().split("\n")
    except:
        pass
    return []


def load_topology():
    try:
        if os.path.exists(TOPOLOGY_FILE):
            with open(TOPOLOGY_FILE) as f:
                data = json.load(f)
                print("[DEBUG] Topology loaded successfully:", data)  # Debug log
                return data
        else:
            print(f"[ERROR] Topology file '{TOPOLOGY_FILE}' does not exist.")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding error in topology file: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error loading topology: {e}")
    return {}


# -------------------------------
# BLAST RADIUS
# -------------------------------

def compute_blast_radius(device, topology, depth=2):

    visited = {device: 0}
    queue = [device]
    customers = 0

    while queue:

        cur = queue.pop(0)

        if visited[cur] >= depth:
            continue

        node = topology.get(cur, {})
        customers += node.get("customers_affected", 0)

        for n in node.get("connected_to", []):

            if n not in visited:
                visited[n] = visited[cur] + 1
                queue.append(n)

    return {
        "origin": device,
        "affected_devices": [d for d in visited if d != device],
        "customers_at_risk": customers,
        "hop_map": visited
    }


# -------------------------------
# FRONTEND
# -------------------------------

@app.route("/")
def index():
    return render_template("dashboard.html")


# -------------------------------
# DEVICES
# -------------------------------

@app.route("/api/devices")
def get_devices():

    telemetry = load_telemetry()
    devices = {}

    for record in telemetry:

        device = record.get("device")

        if device and device not in devices:

            devices[device] = {
                "name": device,
                "latency": float(record.get("latency", 0)),
                "packet_loss": float(record.get("packet_loss", 0)),
                "bgp_flaps": int(record.get("bgp_flaps", 0)),
                "throughput_gbps": float(record.get("throughput_gbps", 0)),
                "status": "healthy" if record.get("label") == "normal" else "anomaly"
            }

    return jsonify(list(devices.values()))


# -------------------------------
# ANOMALIES
# -------------------------------

@app.route("/api/anomalies")
def get_anomalies():

    telemetry = load_telemetry()

    anomalies = {
        "tier1": [],
        "tier2": [],
        "tier3": []
    }

    for r in telemetry:

        label = str(r.get("label", "")).lower()

        if label != "normal":

            item = {
                "device": r.get("device"),
                "latency": float(r.get("latency", 0)),
                "packet_loss": float(r.get("packet_loss", 0)),
                "bgp_flaps": int(r.get("bgp_flaps", 0)),
                "throughput_gbps": float(r.get("throughput_gbps", 0))
            }

            if "tier1" in label:
                anomalies["tier1"].append(item)

            elif "tier2" in label:
                anomalies["tier2"].append(item)

            elif "tier3" in label:
                anomalies["tier3"].append(item)

    return jsonify(anomalies)


# -------------------------------
# MEMORY STATS
# -------------------------------

@app.route("/api/memory")
def get_memory():

    telemetry = load_telemetry()
    audit = load_audit_log()

    tier1 = len([r for r in telemetry if "tier1" in str(r.get("label", "")).lower()])
    tier2 = len([r for r in telemetry if "tier2" in str(r.get("label", "")).lower()])
    tier3 = len([r for r in telemetry if "tier3" in str(r.get("label", "")).lower()])

    return jsonify({
        "total_events": len(audit),
        "tier1_auto_fix": tier1,
        "tier2_pending": tier2,
        "tier3_escalated": tier3
    })


# -------------------------------
# AUDIT LOG
# -------------------------------

@app.route("/api/audit-log")
def audit_log():

    entries = load_audit_log()
    return jsonify({"entries": entries})


# -------------------------------
# APPROVAL SYSTEM
# -------------------------------

@app.route("/api/approve-action", methods=["POST"])
def approve_action():

    data = request.json

    device = data.get("device")
    action = data.get("action")
    user = data.get("user", "operator")
    approved = data.get("approved", True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"[{timestamp}] {action} on {device} - {'APPROVED' if approved else 'DENIED'} by {user}"

    with open(AUDIT_LOG, "a") as f:
        f.write(entry + "\n")

    return jsonify({"status": "logged"})


# -------------------------------
# TOPOLOGY API
# -------------------------------

@app.route("/api/topology")
def topology():
    try:
        raw = load_topology()

        # Support both flat dict AND the {topology: {nodes:[], links:[]}} format
        if "topology" in raw and "nodes" in raw["topology"]:
            topo_data = raw["topology"]
            nodes_list = topo_data.get("nodes", [])
            links_list = topo_data.get("links", [])

            # Build adjacency map from links for connection info
            adjacency = {}
            for link in links_list:
                n1, n2 = link["node1"], link["node2"]
                adjacency.setdefault(n1, []).append(n2)
                adjacency.setdefault(n2, []).append(n1)

            nodes = []
            for node in nodes_list:
                nid = node["id"]
                connections = adjacency.get(nid, [])
                nodes.append({
                    "device": nid,
                    "display_name": node.get("display_name", nid),
                    "type": node.get("type", "unknown"),
                    "status": node.get("status", "up"),
                    "customers": node.get("customers_affected", 0),
                    "connections": connections
                })

            return jsonify({
                "nodes": nodes,
                "links": links_list
            })
        else:
            # Legacy flat format
            nodes = []
            for device, data in raw.items():
                blast = compute_blast_radius(device, raw)
                nodes.append({
                    "device": device,
                    "display_name": device,
                    "type": data.get("type"),
                    "status": "up",
                    "customers": data.get("customers_affected", 0),
                    "connections": data.get("connected_to", []),
                    "blast_radius_devices": len(blast["affected_devices"]),
                    "blast_radius_customers": blast["customers_at_risk"]
                })
            return jsonify({"nodes": nodes, "links": []})

    except Exception as e:
        print("[ERROR] Failed to process topology:", e)
        return jsonify({"error": "Failed to load topology"}), 500


# -------------------------------
# LEARNING API (original, kept for compatibility)
# -------------------------------

@app.route("/api/learning")
def learning():

    memory = load_memory()

    rules = list(set([
        m["learned_rule"]
        for m in memory
        if m.get("learned_rule")
    ]))

    device_stats = {}

    for m in memory:

        d = m["device"]

        if d not in device_stats:
            device_stats[d] = {"correct": 0, "wrong": 0}

        if m.get("outcome_correct"):
            device_stats[d]["correct"] += 1
        else:
            device_stats[d]["wrong"] += 1

    return jsonify({
        "rules": rules[-10:],
        "device_accuracy": device_stats,
        "recent_decisions": memory[-15:]
    })


# -------------------------------
# LEARNING SUMMARY API (rich, for dashboard tab)
# -------------------------------

@app.route("/api/learning-summary")
def learning_summary():
    import time as _time
    memory = load_memory()

    if not memory:
        return jsonify({
            "total_decisions": 0,
            "correct": 0,
            "suboptimal": 0,
            "rolled_back": 0,
            "accuracy_pct": 0,
            "learned_rules": [],
            "device_stats": [],
            "recent_decisions": [],
            "action_distribution": {}
        })

    # ── Overall stats ──────────────────────────────────────────
    total      = len(memory)
    correct    = sum(1 for m in memory if m.get("outcome_correct"))
    rolled     = sum(1 for m in memory if "ROLLBACK" in m.get("action", ""))
    suboptimal = sum(1 for m in memory if m.get("outcome_verdict", "").startswith("⚠"))
    accuracy   = round(correct / total * 100, 1) if total else 0

    # ── Unique IF...THEN rules only (no rollback noise) ────────
    seen_rules = set()
    clean_rules = []
    for m in memory:
        rule = m.get("learned_rule", "")
        if rule and rule.upper().startswith("IF") and rule not in seen_rules:
            seen_rules.add(rule)
            # Count how many times this rule was applied
            count = sum(1 for x in memory if x.get("learned_rule") == rule)
            clean_rules.append({"rule": rule, "times_applied": count})
    # Sort by usage
    clean_rules.sort(key=lambda r: r["times_applied"], reverse=True)

    # ── Per-device accuracy ─────────────────────────────────────
    device_map = {}
    for m in memory:
        d = m.get("device", "unknown")
        if d not in device_map:
            device_map[d] = {"device": d, "total": 0, "correct": 0,
                             "actions": {}, "worst_action": None}
        device_map[d]["total"] += 1
        if m.get("outcome_correct"):
            device_map[d]["correct"] += 1
        act = m.get("action", "unknown")
        device_map[d]["actions"][act] = device_map[d]["actions"].get(act, 0) + 1

    device_stats = []
    for d, s in device_map.items():
        acc = round(s["correct"] / s["total"] * 100, 1) if s["total"] else 0
        top_action = max(s["actions"], key=s["actions"].get)
        device_stats.append({
            "device": d, "total": s["total"],
            "correct": s["correct"], "accuracy_pct": acc,
            "most_frequent_action": top_action
        })
    device_stats.sort(key=lambda x: x["total"], reverse=True)

    # ── Recent 10 decisions (exclude rollback noise) ────────────
    recent = [
        {
            "device":  m.get("device"),
            "action":  m.get("action"),
            "verdict": m.get("outcome_verdict", "N/A"),
            "confidence": m.get("outcome_confidence", 0),
            "rule":    m.get("learned_rule", ""),
            "latency": m.get("trigger_metrics", {}).get("latency_ms"),
            "ts":      _time.strftime("%Y-%m-%d %H:%M", _time.localtime(m.get("timestamp", 0)))
        }
        for m in memory if "ROLLBACK" not in m.get("action", "")
    ][-10:]
    recent.reverse()   # newest first

    # ── Action distribution ─────────────────────────────────────
    action_dist = {}
    for m in memory:
        a = m.get("action", "unknown")
        if "ROLLBACK" not in a:
            action_dist[a] = action_dist.get(a, 0) + 1

    return jsonify({
        "total_decisions": total,
        "correct": correct,
        "suboptimal": suboptimal,
        "rolled_back": rolled,
        "accuracy_pct": accuracy,
        "learned_rules": clean_rules,
        "device_stats": device_stats,
        "recent_decisions": recent,
        "action_distribution": action_dist
    })


# -------------------------------
# DECISIONS API
# -------------------------------

@app.route("/api/decisions")
def decisions():

    memory = load_memory()
    decisions = []

    for m in memory[-20:]:

        decisions.append({
            "device": m["device"],
            "action": m["action"],
            "confidence": m.get("outcome_confidence"),
            "verdict": m.get("outcome_verdict"),
            "rule": m.get("learned_rule"),
            "latency": m["trigger_metrics"].get("latency_ms"),
            "severity": m["trigger_metrics"].get("severity_score")
        })

    return jsonify(decisions)


# -------------------------------
# HEALTH CHECK
# -------------------------------

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


# -------------------------------
# RUN SERVER
# -------------------------------

if __name__ == "__main__":
    print("Server running at http://localhost:5000")
    app.run(debug=True)