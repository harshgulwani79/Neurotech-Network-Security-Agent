import random
import time
from backend.network_simulator.topology import net_instance

# Store active manual anomalies
manual_anomalies = {}

def inject_manual_anomaly(anomaly_type):
    """Injects a manual anomaly into a random link."""
    if not net_instance.links:
        return
    
    link = random.choice(net_instance.links)
    manual_anomalies[link["id"]] = {
        "type": anomaly_type,
        "expiry": time.time() + 15  # Last for 15 seconds
    }
    return {"link": link["id"], "type": anomaly_type}

def get_link_metrics():
    """Simulates pulling metrics from network links."""
    metrics = []
    current_time = time.time()
    
    # Clean up expired anomalies
    expired = [k for k, v in manual_anomalies.items() if v["expiry"] < current_time]
    for k in expired:
        del manual_anomalies[k]

    for link in net_instance.links:
        # Simulate dynamic network conditions
        latency = random.uniform(2.0, 15.0)
        loss = random.uniform(0.0, 0.5)
        utilization = random.uniform(10.0, 60.0)
        
        # Check for manual anomalies
        if link["id"] in manual_anomalies:
            anomaly = manual_anomalies[link["id"]]
            if anomaly["type"] == "congestion":
                utilization = random.uniform(85.0, 98.0)
                latency *= 3.0
            elif anomaly["type"] == "failure":
                loss = random.uniform(5.0, 15.0)
                latency *= 10.0
        
        # Add some random noise/anomalies (natural)
        elif random.random() < 0.05:
            latency *= 5.0
            loss += 2.0
            utilization += 30.0
            
        metrics.append({
            "link": link["id"],
            "display_name": f"{link['node1']} ↔ {link['node2']}",
            "node1": link["node1"],
            "node2": link["node2"],
            "latency": round(latency, 2),
            "loss": round(loss, 2),
            "utilization": round(utilization, 2),
            "timestamp": current_time
        })
    return metrics

def get_topology_info():
    """Returns the current network topology."""
    return {
        "nodes": [
            {
                "id": node_id, 
                "type": node_data.get("type", "switch"),
                "status": node_data.get("status", "up"),
                "display_name": node_data.get("display_name", node_id)
            }
            for node_id, node_data in net_instance.nodes.items()
        ],
        "links": [
            {
                "id": link["id"], 
                "node1": link["node1"], 
                "node2": link["node2"],
                "status": link["status"]
            }
            for link in net_instance.links
        ]
    }

