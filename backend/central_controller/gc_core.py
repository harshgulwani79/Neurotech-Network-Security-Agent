"""
Global Controller - Unified Agentic AI System
Integrates agent.py (LLM-powered) with network_simulator (real-time) and telemetry_generator

Supports two modes:
- REAL_TIME: Live simulation with AI analysis
- HISTORICAL_CSV: Batch analysis of CSV telemetry

Implements Observe → Reason → Learn → Decide → Act cycle with TIER 1-3 severity.
"""
import time
import random
import os
import json

from backend.network_simulator.metrics import get_link_metrics, get_topology_info, inject_manual_anomaly
from backend.agents.performance_agent import get_node_agents
from backend.agent import (
    load_memory,
    save_memory,
    execute_action,
    run_agent_on_simulator_metrics,
    run_agent_cycle,
    assign_tier,
    reason
)
from backend.telemetry_generator import generate_realtime_metrics

# System Modes
class SystemMode:
    REAL_TIME = "real_time"
    HISTORICAL_CSV = "historical_csv"

# Global state
CURRENT_MODE = SystemMode.REAL_TIME
LAST_ANALYSIS = {}

# Rate limiting: Track last AI call time per device (60 second delay)
LAST_AI_CALL = {}  # {device: timestamp}
AI_CALL_DELAY_SEC = 60


class GlobalController:
    def __init__(self):
        self.topology = get_topology_info()
        # Create agents using node IDs from topology
        node_ids = [node["id"] for node in self.topology.get("nodes", [])]
        self.agents = get_node_agents(node_ids)
        self.history = []
        self.learned_policies = []
        self.cycle_count = 0
        self.injections_active = {}  # Track active injections
        
    def set_mode(self, mode: str):
        """Switch between REAL_TIME and HISTORICAL_CSV modes."""
        global CURRENT_MODE
        if mode in [SystemMode.REAL_TIME, SystemMode.HISTORICAL_CSV]:
            CURRENT_MODE = mode
            return {"status": "success", "mode": CURRENT_MODE}
        return {"status": "error", "message": "Invalid mode"}
    
    def get_mode(self):
        """Get current system mode."""
        return CURRENT_MODE

    def run_cycle(self):
        """Run a single observe-reason-decide-act cycle."""
        global LAST_ANALYSIS
        self.cycle_count += 1
        
        # Refresh topology in case it changed
        self.topology = get_topology_info()
        
        # === OBSERVE ===
        if CURRENT_MODE == SystemMode.REAL_TIME:
            # Check for active injections
            current_time = time.time()
            expired_injections = [k for k, v in self.injections_active.items() 
                               if v.get('expiry', 0) < current_time]
            for k in expired_injections:
                del self.injections_active[k]
            
            # Use injected metrics if available, otherwise generate fresh
            if self.injections_active:
                metrics = self._get_injected_metrics()
            else:
                # Generate real-time metrics using telemetry_generator
                metrics = generate_realtime_metrics()
        else:
            # Historical mode - process CSV
            results = run_agent_cycle(max_anomalies=20)
            # Convert to metrics format for display
            metrics = self._convert_agent_results_to_metrics(results)
        
        all_anomalies = []
        
        # Check against thresholds directly (for real-time display)
        for metric in metrics:
            latency = metric.get('latency', 0) or 0
            loss = metric.get('loss', 0) or 0
            utilization = metric.get('utilization', 0) or 0
            
            # Determine tier based on thresholds
            tier = 0
            if latency > 50 or loss > 1 or utilization > 85:
                # Calculate approximate severity score
                severity = -0.05 - (latency / 2000) - (loss / 100)
                tier = assign_tier(severity)
                
                all_anomalies.append({
                    "type": "tier" + str(tier),
                    "value": max(latency, loss, utilization),
                    "latency": latency,
                    "loss": loss,
                    "utilization": utilization,
                    "device": metric.get('device', metric.get('link', 'unknown')),
                    "tier": tier,
                    "timestamp": time.time()
                })
        
        # === REASON with LLM ===
        # Track analyzing device for immediate UI update
        analyzing_device = None
        
        if all_anomalies or CURRENT_MODE == SystemMode.REAL_TIME:
            # Determine which devices need AI analysis (apply rate limiting)
            devices_to_analyze = []
            current_time = time.time()
            
            # Check each anomaly's device for rate limiting
            for anomaly in all_anomalies:
                device = anomaly.get('device', 'unknown')
                last_call = LAST_AI_CALL.get(device, 0)
                
                # If device hasn't been analyzed in the last 60 seconds, analyze it now
                if current_time - last_call >= AI_CALL_DELAY_SEC:
                    devices_to_analyze.append(device)
                    LAST_AI_CALL[device] = current_time  # Update last call time
            
            # If there are devices to analyze, call the AI
            if devices_to_analyze or CURRENT_MODE == SystemMode.REAL_TIME:
                # Use full LLM-powered agent analysis
                if CURRENT_MODE == SystemMode.REAL_TIME:
                    # Get analyzing device for immediate UI update (first anomaly device)
                    if all_anomalies:
                        analyzing_device = all_anomalies[0].get('device', None)
                    
                    ai_analysis = run_agent_on_simulator_metrics(metrics, max_anomalies=5)
                else:
                    # For historical, results are already processed
                    ai_analysis = {
                        "decisions": [],
                        "timestamp": time.time()
                    }
            else:
                # Skip AI call - use cached/simplified analysis
                ai_analysis = {
                    "decisions": [],
                    "analyzed_events": [],
                    "actions_taken": [],
                    "timestamp": time.time(),
                    "skipped_ai": True,
                    "reason": "Rate limited - device analyzed recently"
                }
            
            LAST_ANALYSIS = ai_analysis
            
            # Generate report with tier information
            report = self._generate_reasoning_report_enhanced(all_anomalies, ai_analysis)
            
            # === DECIDE & ACT ===
            self._execute_based_on_tier(ai_analysis)
        else:
            # No anomalies - stable network
            report = {
                "status": "Stable",
                "risk_level": "Low",
                "summary": "Network operating within normal parameters. No anomalies detected.",
                "intervention": "None",
                "timestamp": time.strftime("%H:%M:%S"),
                "tier": 0,
                "ai_reasoning": None
            }
        
        return {
            "mode": CURRENT_MODE,
            "metrics": metrics,
            "anomalies": all_anomalies,
            "report": report,
            "topology": self.topology,
            "ai_analysis": LAST_ANALYSIS,
            "cycle": self.cycle_count,
            "memory": load_memory()[-10:],  # Last 10 memory entries
            "analyzing_device": analyzing_device  # Currently analyzing device for immediate UI update
        }

    def _get_injected_metrics(self) -> list:
        """Get metrics with injected anomalies."""
        # Get base metrics
        base_metrics = generate_realtime_metrics()
        
        # Apply injections
        for injection_type, injection_data in self.injections_active.items():
            target_device = injection_data.get('device')
            
            for metric in base_metrics:
                if metric.get('device') == target_device:
                    if injection_type == "congestion":
                        metric['latency'] = random.uniform(55, 120)
                        metric['loss'] = random.uniform(1.0, 5.0)
                        metric['utilization'] = random.uniform(85, 98)
                        metric['label'] = 'tier1'
                        metric['is_anomaly'] = True
                    elif injection_type == "failure":
                        metric['latency'] = random.uniform(100, 500)
                        metric['loss'] = random.uniform(15, 50)
                        metric['utilization'] = random.uniform(5, 20)
                        metric['bgp_flaps'] = random.randint(3, 10)
                        metric['label'] = 'tier3'
                        metric['is_anomaly'] = True
        
        return base_metrics

    def _convert_agent_results_to_metrics(self, results: list) -> list:
        """Convert agent results to metrics format for display."""
        metrics = []
        for r in results:
            metrics.append({
                "device": r.get('device', 'unknown'),
                "latency": r.get('trigger_metrics', {}).get('latency_ms', 0),
                "loss": r.get('trigger_metrics', {}).get('packet_loss_pct', 0),
                "utilization": r.get('trigger_metrics', {}).get('throughput_gbps', 0),
                "bgp_flaps": r.get('trigger_metrics', {}).get('bgp_flaps', 0),
                "label": r.get('action', 'unknown'),
                "timestamp": r.get('timestamp', time.time())
            })
        return metrics

    def _generate_reasoning_report_enhanced(self, anomalies, ai_analysis):
        """Generate enhanced reasoning report with tier information."""
        if not anomalies:
            return {
                "status": "Stable",
                "risk_level": "Low",
                "summary": "Network operating within normal parameters.",
                "intervention": "None",
                "timestamp": time.strftime("%H:%M:%S"),
                "tier": 0,
                "ai_reasoning": None
            }
        
        # Get decisions from AI analysis
        decisions = ai_analysis.get("decisions", [])
        
        # Determine highest tier
        max_tier = 0
        tier_counts = {1: 0, 2: 0, 3: 0}
        
        for anomaly in anomalies:
            tier = anomaly.get('tier', 2)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            if tier > max_tier:
                max_tier = tier
        
        # Get AI reasoning
        ai_reasoning = None
        if decisions:
            best_decision = decisions[0]
            ai_reasoning = {
                "root_cause": best_decision.get("root_cause_hypothesis", "Unknown"),
                "blast_radius": best_decision.get("blast_radius_summary", "Unknown"),
                "action": best_decision.get("action", "none"),
                "confidence": best_decision.get("llm_confidence", 0),
                "learning": best_decision.get("learning_policy_update", "")
            }
        
        # Links/devices affected
        devices_affected = list(set([a.get('device', 'unknown') for a in anomalies]))
        tier_labels = {1: "✅ TIER 1 (Auto)", 2: "⚠️  TIER 2 (Human)", 3: "🚨 TIER 3 (Escalate)"}
        
        summary = f"Detected {len(anomalies)} anomalies across {len(devices_affected)} devices. "
        
        if tier_counts.get(1, 0) > 0:
            summary += f"{tier_counts[1]} Tier 1 (auto-fix), "
        if tier_counts.get(2, 0) > 0:
            summary += f"{tier_counts[2]} Tier 2 (human approval), "
        if tier_counts.get(3, 0) > 0:
            summary += f"{tier_counts[3]} Tier 3 (escalate)"
        
        if max_tier == 1:
            summary += ". TIER 1: Autonomous action taken."
        elif max_tier == 2:
            summary += ". TIER 2: Human approval recommended."
        else:
            summary += ". TIER 3: Critical - Escalation required."
        
        return {
            "status": "Anomaly Detected",
            "risk_level": {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}.get(max_tier, "High"),
            "summary": summary,
            "intervention": ai_reasoning.get("action", "monitor") if ai_reasoning else "None",
            "timestamp": time.strftime("%H:%M:%S"),
            "tier": max_tier,
            "tier_counts": tier_counts,
            "ai_reasoning": ai_reasoning,
            "devices_affected": devices_affected,
            "anomaly_count": len(anomalies)
        }

    def _execute_based_on_tier(self, ai_analysis):
        """Execute actions based on tier level."""
        decisions = ai_analysis.get("decisions", [])
        
        for decision in decisions:
            tier = decision.get("risk_tier", 2)
            action = decision.get("action", "none")
            params = decision.get("params", [])
            
            # Extract device from params (LLM typically returns [device])
            device = params[0] if params else "unknown"
            
            # Construct event dict for execute_action (for metrics/audit logging)
            event = {
                "latency": 0,
                "packet_loss": 0,
                "bgp_flaps": 0,
                "throughput_gbps": 0,
                "severity_score": -0.05 - (tier * 0.01)
            }
            
            if tier == 1:
                # TIER 1: Fully Autonomous - execute immediately
                execute_action(action, params, device, event)
                print(f"🤖 [TIER 1] Autonomous action executed: {action}")
                
            elif tier == 2:
                # TIER 2: Human Approval - auto-approve for demo
                execute_action(action, params, device, event)
                print(f"🛡️ [TIER 2] Auto-approved action: {action}")
                
            else:
                # TIER 3: Critical - escalate
                print(f"🚨 [TIER 3] ESCALATED to Level 3 Engineering: {action}")

    def inject_anomaly(self, anomaly_type):
        """Trigger a manual anomaly in the simulator."""
        import random
        from backend.telemetry_generator import DEVICES
        
        # Pick a random device for the injection
        device = random.choice(DEVICES)
        
        # Store injection (lasts for 15 seconds)
        self.injections_active[anomaly_type] = {
            "type": anomaly_type,
            "device": device,
            "expiry": time.time() + 15
        }
        
        print(f"🔧 [INJECTION] {anomaly_type} on {device}")
        
        return {
            "status": "success",
            "type": anomaly_type,
            "device": device,
            "expires_in": 15
        }

    def get_learned_policies(self):
        """Get all learned policies from memory."""
        return load_memory()
    
    def clear_memory(self):
        """Clear learned memory."""
        with open("network_memory.json", 'w') as f:
            json.dump([], f)
        return {"status": "success", "message": "Memory cleared"}


# Global instance
gc = GlobalController()

