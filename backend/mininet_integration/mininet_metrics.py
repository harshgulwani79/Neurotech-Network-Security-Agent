import random
import time
from backend.mininet_integration.mininet_topology import net_instance

def get_link_metrics():
    """Simulates pulling metrics from Mininet links."""
    metrics = []
    for link in net_instance.links:
        # Simulate dynamic network conditions
        latency = random.uniform(2.0, 15.0)
        loss = random.uniform(0.0, 0.5)
        utilization = random.uniform(10.0, 60.0)
        
        # Add some noise/anomalies
        if random.random() < 0.05:
            latency *= 5.0
            loss += 2.0
            utilization += 30.0
            
        metrics.append({
            "link": link["id"],
            "latency": round(latency, 2),
            "loss": round(loss, 2),
            "utilization": round(utilization, 2),
            "timestamp": time.time()
        })
    return metrics

def get_topology_info():
    """Returns the current network topology."""
    return {
        "nodes": list(net_instance.nodes.keys()),
        "links": [
            {"id": link["id"], "nodes": link["nodes"], "status": link["status"]}
            for link in net_instance.links
        ]
    }
