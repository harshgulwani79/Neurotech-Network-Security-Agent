import random
import time
from backend.config import LATENCY_THRESHOLD_MS, LOSS_THRESHOLD_PERCENT, UTILIZATION_THRESHOLD_PERCENT

class PerformanceAgent:
    def __init__(self, node_id):
        self.node_id = node_id
        self.history = []

    def analyze_telemetry(self, metrics):
        """Analyze telemetry for a specific node/link."""
        anomalies = []
        for metric in metrics:
            if metric["latency"] > LATENCY_THRESHOLD_MS:
                anomalies.append({
                    "type": "latency",
                    "value": metric["latency"],
                    "threshold": LATENCY_THRESHOLD_MS,
                    "link": metric["link"],
                    "timestamp": time.time()
                })
            if metric["loss"] > LOSS_THRESHOLD_PERCENT:
                anomalies.append({
                    "type": "loss",
                    "value": metric["loss"],
                    "threshold": LOSS_THRESHOLD_PERCENT,
                    "link": metric["link"],
                    "timestamp": time.time()
                })
            if metric["utilization"] > UTILIZATION_THRESHOLD_PERCENT:
                anomalies.append({
                    "type": "utilization",
                    "value": metric["utilization"],
                    "threshold": UTILIZATION_THRESHOLD_PERCENT,
                    "link": metric["link"],
                    "timestamp": time.time()
                })
        return anomalies

def get_node_agents(nodes):
    """Factory to create agents for each node."""
    return {node: PerformanceAgent(node) for node in nodes}
