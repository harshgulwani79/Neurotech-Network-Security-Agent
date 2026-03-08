"""
AI Agent that integrates with the network simulator.
Analyzes telemetry from the simulation and provides AI-powered insights.
"""
import os
import json
import time
import random
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from backend.config import LATENCY_THRESHOLD_MS, LOSS_THRESHOLD_PERCENT, UTILIZATION_THRESHOLD_PERCENT

# Agent memory for learning
AGENT_MEMORY = []
MEMORY_FILE = "backend/agent_memory.json"

# Node name mapping for display - now uses actual city/location names
NODE_DISPLAY_NAMES = {
    'Mumbai-Core-01': 'Mumbai Core',
    'Bangalore-Core-02': 'Bangalore Core', 
    'Delhi-Edge-05': 'Delhi Edge',
    'NYC-Peering-01': 'NYC Peering',
    'Chennai-Link-03': 'Chennai Link',
    'London-Core-01': 'London Core',
    'Frankfurt-Core-02': 'Frankfurt Core',
    'Host-Mumbai-01': 'Mumbai Host',
    'Host-Delhi-01': 'Delhi Host',
    'Host-Bangalore-01': 'Bangalore Host',
    'Host-NYC-01': 'NYC Host'
}

def load_memory():
    """Load agent memory from file."""
    global AGENT_MEMORY
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                AGENT_MEMORY = json.load(f)
        except:
            AGENT_MEMORY = []
    return AGENT_MEMORY

def save_memory():
    """Save agent memory to file."""
    with open(MEMORY_FILE, 'w') as f:
        json.dump(AGENT_MEMORY, f)

def get_display_name(node_id):
    """Get human-readable name for a node."""
    return NODE_DISPLAY_NAMES.get(node_id, node_id)

def analyze_with_ai(metrics):
    """
    Analyze network metrics using AI (Isolation Forest + optional LLM).
    Returns enriched anomaly data with AI reasoning.
    """
    if not metrics or len(metrics) < 5:
        return []
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(metrics)
    
    # Features for anomaly detection
    features = ['latency', 'loss', 'utilization']
    if not all(f in df.columns for f in features):
        return []
        
    X = df[features].values
    
    # Run Isolation Forest
    clf = IsolationForest(contamination=0.1, random_state=42)
    preds = clf.fit_predict(X)
    scores = clf.decision_function(X)
    
    # Add anomaly predictions to metrics
    results = []
    for i, row in df.iterrows():
        anomaly_score = scores[i]
        is_anomaly = preds[i] == -1
        
        # Get node info
        node1 = row.get('node1', row.get('link', 'unknown').split('-')[0])
        node2 = row.get('node2', row.get('link', 'unknown').split('-')[-1])
        
        # Check if it exceeds thresholds
        exceeds_threshold = (
            row['latency'] > LATENCY_THRESHOLD_MS or
            row['loss'] > LOSS_THRESHOLD_PERCENT or
            row['utilization'] > UTILIZATION_THRESHOLD_PERCENT
        )
        
        if is_anomaly or exceeds_threshold:
            # Calculate severity score (more negative = more anomalous)
            severity = anomaly_score
            
            # Determine root cause
            if row['latency'] > LATENCY_THRESHOLD_MS * 2:
                root_cause = "High Latency"
            elif row['loss'] > LOSS_THRESHOLD_PERCENT * 2:
                root_cause = "Packet Loss"
            elif row['utilization'] > UTILIZATION_THRESHOLD_PERCENT:
                root_cause = "Network Congestion"
            else:
                root_cause = "Anomaly Detected"
            
            results.append({
                'link': row['link'],
                'node1': node1,
                'node2': node2,
                'display_name': row.get('display_name', f"{node1} ↔ {node2}"),
                'latency': row['latency'],
                'loss': row['loss'],
                'utilization': row['utilization'],
                'anomaly': anomaly_score,
                'severity_score': severity,
                'root_cause': root_cause,
                'timestamp': row.get('timestamp', time.time())
            })
    
    return results

def run_ai_agent_cycle(metrics):
    """
    Main AI agent cycle - analyze metrics and provide insights.
    This is called from the simulation loop.
    """
    load_memory()
    
    # Analyze metrics with AI
    anomalies = analyze_with_ai(metrics)
    
    # Sort by severity (most anomalous first)
    anomalies.sort(key=lambda x: x['severity_score'])
    
    # Generate recommendations
    recommendations = []
    for anomaly in anomalies[:5]:  # Top 5
        if anomaly['root_cause'] == "Network Congestion":
            action = "reroute_traffic"
            risk = "TIER 2"
        elif anomaly['root_cause'] == "High Latency":
            action = "adjust_qos"
            risk = "TIER 2"
        elif anomaly['root_cause'] == "Packet Loss":
            action = "enable_fec"
            risk = "TIER 3"
        else:
            action = "monitor"
            risk = "TIER 1"
        
        recommendations.append({
            'device': anomaly.get('display_name', anomaly['link']),
            'link': anomaly['link'],
            'node1': anomaly.get('node1'),
            'node2': anomaly.get('node2'),
            'root_cause': anomaly['root_cause'],
            'severity': anomaly['severity_score'],
            'action': action,
            'risk_level': risk,
            'auto_approved': risk == "TIER 1"
        })
    
    # Add to memory
    if anomalies:
        AGENT_MEMORY.append({
            'timestamp': time.strftime("%H:%M:%S"),
            'anomalies_detected': len(anomalies),
            'top_anomaly': anomalies[0].get('display_name', anomalies[0]['link']) if anomalies else None,
            'actions_taken': [r['action'] for r in recommendations]
        })
        save_memory()
    
    return {
        'analyzed': len(metrics),
        'anomalies': anomalies,
        'recommendations': recommendations,
        'memory_size': len(AGENT_MEMORY)
    }

# Standalone function for API calls
def run_agent_cycle(max_anomalies=3):
    """Run the AI agent on the current simulation metrics."""
    from backend.network_simulator.metrics import get_link_metrics
    
    metrics = get_link_metrics()
    result = run_ai_agent_cycle(metrics)
    
    return {
        'analyzed_events': result['anomalies'][:max_anomalies],
        'recommendations': result['recommendations'][:max_anomalies],
        'summary': f"Analyzed {result['analyzed']} metrics, found {len(result['anomalies'])} anomalies"
    }

