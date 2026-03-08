import os
from dotenv import load_dotenv

load_dotenv()

# Network Thresholds
LATENCY_THRESHOLD_MS = 50.0
LOSS_THRESHOLD_PERCENT = 1.0
UTILIZATION_THRESHOLD_PERCENT = 85.0

# Server Configuration
PORT = 3001
HOST = "0.0.0.0"

# Simulation Settings
SIMULATION_INTERVAL_SEC = 5.0
NODE_COUNT = 8
LINK_FAILURE_PROBABILITY = 0.05
