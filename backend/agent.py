import groq
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import logging
import json
import os
import time
import random

# ── SETUP ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Neurotech_NOC_Agent")

# API Configuration - use Groq API key
# IMPORTANT: Set GROQ_API_KEY environment variable or use .env file
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your-api-key-here")

# Initialize Groq client
groq_client = groq.Groq(api_key=GROQ_API_KEY)

# Use Groq model - llama-3.1-8b-instant is fast and supported
MODEL_ID = "llama-3.1-8b-instant"

# Configuration
MEMORY_FILE = "network_memory.json"
AUDIT_LOG = "audit_log.txt"
MAX_EVENTS = 6
CALL_DELAY = 3
MAX_RETRIES = 3
AUTO_EXEC_MIN_CONF = 80
PARTIAL_OBS_RATE = 0.20

# Tier thresholds - tuned to actual Isolation Forest score clusters
TIER1_THRESHOLD = -0.072
TIER2_THRESHOLD = -0.079

# Valid actions per tier
TIER_ACTIONS = {
    1: ["rate_limit", "qos_adjustment"],
    2: ["traffic_reroute", "config_rollback"],
    3: ["escalate"]
}

ACTION_OUTCOMES = {
    "rate_limit": {"latency_reduction": "30-40%", "risk": "low", "reversible": True, "recovery_mins": 5},
    "qos_adjustment": {"latency_reduction": "20-30%", "risk": "low", "reversible": True, "recovery_mins": 3},
    "traffic_reroute": {"latency_reduction": "60-80%", "risk": "medium", "reversible": True, "recovery_mins": 10},
    "config_rollback": {"latency_reduction": "50-70%", "risk": "medium", "reversible": True, "recovery_mins": 15},
    "escalate": {"latency_reduction": "N/A", "risk": "high", "reversible": False, "recovery_mins": 60},
}

# Load Topology
TOPOLOGY = {}
try:
    with open('backend/topology.json', 'r') as f:
        TOPOLOGY = json.load(f)
except FileNotFoundError:
    logger.error("topology.json not found!")
    TOPOLOGY = {}

# ── MEMORY FUNCTIONS ─────────────────────────────────────────────────────────
def load_memory() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_memory(entry: dict):
    mem = load_memory()
    mem.append(entry)
    with open(MEMORY_FILE, 'w') as f:
        json.dump(mem[-50:], f, indent=2)

def device_history(device: str) -> list:
    return [m for m in load_memory() if m.get('device') == device]

# ── PARTIAL OBSERVABILITY ─────────────────────────────────────────────────────
def apply_partial_obs(event: dict) -> dict:
    """Simulates 20% sensor failure rate for realistic testing."""
    noisy = dict(event)
    masked = []
    for field in ['latency', 'packet_loss', 'bgp_flaps', 'throughput_gbps']:
        if random.random() < PARTIAL_OBS_RATE:
            noisy[field] = None
            masked.append(field)
    if masked:
        logger.warning(f"⚠️  [PARTIAL OBS] Sensor unavailable: {', '.join(masked)}")
    return noisy

# ── TIER ASSIGNMENT ───────────────────────────────────────────────────────────
def assign_tier(score: float) -> int:
    """Tier is ALWAYS set by IF score. LLM cannot override this."""
    if score > TIER1_THRESHOLD:
        return 1
    if score > TIER2_THRESHOLD:
        return 2
    return 3

# ── BLAST RADIUS (BFS over topology graph) ────────────────────────────────────
def compute_blast_radius(device: str, depth: int = 2) -> dict:
    """BFS traversal to calculate affected devices & customer impact."""
    visited = {device: 0}
    queue = [device]
    customers = 0
    
    while queue:
        cur = queue.pop(0)
        if visited[cur] >= depth:
            continue
        node = TOPOLOGY.get(cur, {})
        customers += node.get('customers_affected', 0)
        for n in node.get('connected_to', []):
            if n not in visited:
                visited[n] = visited[cur] + 1
                queue.append(n)
    
    affected = [d for d in visited if d != device]
    return {
        "origin": device,
        "affected_devices": affected,
        "customers_at_risk": customers,
        "hop_map": visited
    }

# ── ACTION EXECUTION ──────────────────────────────────────────────────────────
def execute_action(action: str, params: list, device: str, event: dict, status="EXECUTED") -> dict:
    outcome = ACTION_OUTCOMES.get(action, {
        "latency_reduction": "unknown",
        "risk": "unknown",
        "reversible": True,
        "recovery_mins": 30
    })
    
    metrics = {
        "latency_ms": event.get('latency'),
        "packet_loss_pct": event.get('packet_loss'),
        "bgp_flaps": event.get('bgp_flaps'),
        "throughput_gbps": event.get('throughput_gbps'),
        "severity_score": event.get('severity_score')
    }
    
    with open(AUDIT_LOG, 'a') as f:
        f.write(f"[{time.ctime()}] {status}: {action} | {device} | metrics={metrics}\n")
    
    return {
        "timestamp": time.time(),
        "device": device,
        "action": action,
        "params": params,
        "trigger_metrics": metrics,
        "predicted_outcome": outcome,
        "status": status
    }

def rollback_action(original: dict, results: list):
    """Simulated rollback - audit log + memory entry."""
    device = original['device']
    action = original['action']
    
    logger.info(f"🔄 [ROLLBACK] Reversing '{action}' on {device}...")
    
    with open(AUDIT_LOG, 'a') as f:
        f.write(f"[{time.ctime()}] ROLLBACK: reversed '{action}' on {device}\n")
    
    rb_entry = {
        "timestamp": time.time(),
        "device": device,
        "action": f"ROLLBACK:{action}",
        "trigger_metrics": original.get('trigger_metrics', {}),
        "predicted_outcome": {"latency_reduction": "restoring pre-action state"},
        "outcome_verdict": "🔄 ROLLED BACK",
        "outcome_correct": False,
        "learned_rule": None,
        "status": "ROLLBACK"
    }
    
    save_memory(rb_entry)
    results.append(rb_entry)
    logger.info(f"✅ Rollback logged.")

# ── ACTION EVALUATION ─────────────────────────────────────────────────────────
def evaluate_action(record: dict) -> dict:
    action = record['action']
    severity = record['trigger_metrics'].get('severity_score', 0)
    latency = float(record['trigger_metrics'].get('latency_ms') or 0)
    
    issues = []
    correct = True
    better = None
    confidence = 100

    if severity > TIER1_THRESHOLD:
        if action not in TIER_ACTIONS[1]:
            correct = False
            better = 'rate_limit'
            confidence = 60
            issues.append(f"Over-reaction: Tier 1 event got '{action}', should be rate_limit")
    elif severity > TIER2_THRESHOLD:
        if action in TIER_ACTIONS[1]:
            correct = False
            better = 'traffic_reroute'
            confidence = 70
            issues.append(f"Under-reaction: Tier 2 event got '{action}', should be traffic_reroute")
        elif action == 'escalate':
            correct = False
            better = 'traffic_reroute'
            confidence = 80
            issues.append("Over-escalation: Tier 2 could be handled with traffic_reroute")
    else:
        if action != 'escalate':
            correct = False
            better = 'escalate'
            confidence = 50
            issues.append(f"Under-reaction: Tier 3 MUST be escalated, not '{action}'")
    
    if latency > 500 and action == 'rate_limit':
        correct = False
        better = 'traffic_reroute'
        confidence = min(confidence, 80)
        issues.append(f"Latency {latency:.0f}ms too high for rate_limit alone")

    return {
        "verdict": "✅ CORRECT" if correct else "⚠️  SUBOPTIMAL",
        "correct": correct,
        "confidence_pct": max(0, confidence),
        "issues": issues or ["Action matches event severity and type"],
        "better_action": better,
        "recommendation": f"Consider '{better}' next time" if better else "No change needed"
    }

# ── POLICY VIOLATION CHECK ─────────────────────────────────────────────────────
def check_policy_violations(action: str, device: str, memory: list, tier: int) -> list:
    """Compares proposed action against learned rules."""
    violations = []
    correct_for_tier = set(TIER_ACTIONS[tier])
    
    for m in memory[-10:]:
        rule = m.get('learned_rule', '')
        mdev = m.get('device') == device
        
        if mdev and 'escalat' in rule.lower() and action != 'escalate' and action not in correct_for_tier:
            violations.append(f"Past rule: '{rule}' — but proposed action is '{action}'")
        
        if mdev and f"ROLLBACK:{action}" in m.get('action', '') and action not in correct_for_tier:
            violations.append(f"'{action}' was previously rolled back on {device}")
    
    return violations

# ── LLM CALL ──────────────────────────────────────────────────────────────────
def call_llm(prompt: str) -> str:
    """Use Groq API for LLM reasoning."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = groq_client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "You are a network operations AI assistant. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=512
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM call error: {e}")
            if attempt < MAX_RETRIES:
                wait = 30 * (attempt + 1)
                logger.warning(f"Rate limit. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise

# ── AGENT BRAIN ───────────────────────────────────────────────────────────────
def reason(event: dict, tier: int, blast: dict, memory: list) -> dict:
    """Analyzes event and recommends action using LLM."""
    device = event.get('device', '')
    fmt = lambda v, s: f"{v:{s}}" if v is not None else "UNAVAILABLE"
    valid = TIER_ACTIONS[tier]

    # Get learned rules
    past_rules = [m['learned_rule'] for m in memory[-6:] if m.get('learned_rule')]
    device_rules = [m['learned_rule'] for m in memory if m.get('device') == device and m.get('learned_rule')]
    applied_rules = device_rules[-3:] if device_rules else past_rules[-3:]

    tier_instruction = {
        1: f"TIER 1 LOCKED. You MUST choose action from: {valid}. No other action allowed.",
        2: f"TIER 2 LOCKED. You MUST choose action from: {valid}. Human will approve before execution.",
        3: f"TIER 3 LOCKED. You MUST use action: escalate. No other action allowed."
    }

    prompt = (
        f"Device={device} | "
        f"lat={fmt(event.get('latency'),'.0f')}ms | "
        f"loss={fmt(event.get('packet_loss'),'.1f')}% | "
        f"bgp_flaps={event.get('bgp_flaps') if event.get('bgp_flaps') is not None else 'UNAVAILABLE'} | "
        f"tput={fmt(event.get('throughput_gbps'),'.1f')}Gbps\n"
        f"Topology: {json.dumps({device: TOPOLOGY.get(device, {})})}\n"
        f"Blast radius (BFS): affected={blast['affected_devices']}, customers_at_risk={blast['customers_at_risk']}\n"
        f"Recent device actions: {json.dumps([m for m in memory[-3:] if m.get('device')==device])}\n\n"
        f"=== LEARNED POLICIES (apply these to your decision) ===\n"
        + ("\n".join(f"- {r}" for r in applied_rules) if applied_rules else "- No policies yet — this is run 1.") + "\n\n"
        f"=== {tier_instruction[tier]} ===\n"
        f"If any metric is UNAVAILABLE, reason conservatively.\n"
        f"Return ONLY this JSON:\n"
        '{"root_cause_hypothesis":"one sentence","blast_radius_summary":"one sentence with customer impact",'
        f'"risk_tier":{tier},"action":"your_chosen_action_from_valid_list","params":["{device}"],'
        '"llm_confidence":90,"learning_policy_update":"IF condition THEN action — one concrete rule"}'
    )
    
    try:
        raw = call_llm(prompt)
        result = json.loads(raw[raw.find('{'):raw.rfind('}')+1])
    except Exception as e:
        logger.error(f"LLM call failed: {e}, using fallback")
        result = {
            "root_cause_hypothesis": "Network anomaly detected",
            "blast_radius_summary": "Single device affected",
            "risk_tier": tier,
            "action": valid[0],
            "params": [device],
            "llm_confidence": 50,
            "learning_policy_update": "Monitor device closely"
        }

    # Hard overrides
    result['risk_tier'] = tier
    if result.get('action') not in valid:
        logger.warning(f"LLM chose invalid action '{result.get('action')}' for Tier {tier} — correcting to '{valid[0]}'")
        result['action'] = valid[0]
    
    return result

# ── MAIN AGENT RUNNER (for historical mode) ─────────────────────────────────
def run_agent_cycle(max_anomalies: int = 6) -> dict:
    """Run a single agent cycle and return results."""
    logger.info("="*60)
    logger.info("  NEUROTECH ENTERPRISE AGENTIC OPS LAYER CYCLE")
    logger.info("="*60)

    # Load and process telemetry
    df = pd.read_csv("backend/telemetry_stream.csv")
    features = ['latency', 'packet_loss', 'bgp_flaps', 'throughput_gbps']
    
    X_scaled = StandardScaler().fit_transform(df[features])
    clf = IsolationForest(contamination=0.001, random_state=42)
    df['anomaly'] = clf.fit_predict(df[features])
    df['severity'] = clf.decision_function(df[features])

    events = (
        df[df['anomaly'] == -1]
        .sort_values('severity')
        .rename(columns={'severity': 'severity_score'})
        .head(max_anomalies)
        .to_dict('records')
    )

    memory = load_memory()
    results = []

    logger.info(f"🔎 Processing {len(events)} anomalies...")

    tier_labels = {1: "✅ TIER 1 (Auto)", 2: "⚠️  TIER 2 (Human)", 3: "🚨 TIER 3 (Escalate)"}

    for i, event in enumerate(events, 1):
        device = event['device']
        score = event['severity_score']
        tier = assign_tier(score)

        logger.info(f"🔍 [{i}/{len(events)}] {device} score={score:.4f} → {tier_labels[tier]}")

        noisy = apply_partial_obs(event)
        blast = compute_blast_radius(device)

        try:
            decision = reason(noisy, tier, blast, memory)
            action_name = decision['action']
            llm_conf = int(decision.get('llm_confidence', 85))
            rec = None

            logger.info(f"🧠 Root Cause: {decision.get('root_cause_hypothesis')}")
            logger.info(f"🛡️ Action: {action_name} (confidence: {llm_conf}%)")

            # Tier 1 - Auto execute
            if tier == 1:
                if llm_conf >= AUTO_EXEC_MIN_CONF:
                    rec = execute_action(action_name, decision['params'], device, noisy)
                    logger.info(f"✅ Auto-executed: {action_name}")
                else:
                    logger.warning(f"⚠️ Low confidence - skipping")

            # Tier 2 - Human approval (auto-approve for demo)
            elif tier == 2:
                rec = execute_action(action_name, decision['params'], device, noisy)
                logger.info(f"⚠️ Tier 2 - Auto-approved: {action_name}")

            # Tier 3 - Escalate
            else:
                rec = execute_action('escalate', [device], device, noisy)
                logger.info(f"🚨 Tier 3 - Escalated: {device}")

            # Evaluate
            if rec:
                ev = evaluate_action(rec)
                rec.update(
                    outcome_verdict=ev['verdict'],
                    outcome_confidence=ev['confidence_pct'],
                    outcome_correct=ev['correct'],
                    better_action=ev['better_action']
                )

            # Save to memory
            if rec:
                entry = {
                    "timestamp": rec.get('timestamp', time.time()),
                    "device": device,
                    "action": rec.get('action', action_name),
                    "trigger_metrics": rec['trigger_metrics'],
                    "predicted_outcome": rec['predicted_outcome'],
                    "outcome_verdict": rec.get('outcome_verdict', 'N/A'),
                    "outcome_confidence": rec.get('outcome_confidence', 0),
                    "outcome_correct": rec.get('outcome_correct', False),
                    "better_action": rec.get('better_action'),
                    "learned_rule": decision.get('learning_policy_update'),
                    "status": rec.get('status', 'EXECUTED')
                }
                save_memory(entry)
                memory.append(entry)
                results.append(entry)
                logger.info(f"📚 Learned: {decision.get('learning_policy_update')}")

        except Exception as e:
            logger.error(f"❌ Error processing {device}: {e}")

    return results

# ── PROCESS SIMULATOR METRICS (for real-time mode) ───────────────────────────
def run_agent_on_simulator_metrics(metrics: list, max_anomalies: int = 5) -> dict:
    """Analyze metrics from the real-time simulator."""
    if not metrics:
        return {"analyzed_events": [], "decisions": [], "actions_taken": [], "timestamp": time.time()}

    logger.info(f"🤖 AI Agent analyzing {len(metrics)} metrics from simulator...")

    # Convert to DataFrame for ML analysis
    df = pd.DataFrame(metrics)
    
    features = ['latency', 'loss', 'utilization']
    feature_map = {'latency': 'latency', 'loss': 'packet_loss', 'utilization': 'throughput_gbps'}
    
    # Map simulator fields to expected fields
    if all(f in df.columns for f in features):
        df['packet_loss'] = df['loss']
        df['throughput_gbps'] = df['utilization']
        df['bgp_flaps'] = 0  # Simulator doesn't have BGP flaps
        
        X = df[['latency', 'packet_loss', 'throughput_gbps', 'bgp_flaps']]
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        ml_model = IsolationForest(contamination=0.1, random_state=42)
        df['anomaly'] = ml_model.fit_predict(X_scaled)
        df['severity_score'] = ml_model.decision_function(X_scaled)
        
        anomalies_df = df[df['anomaly'] == -1].sort_values(by='severity_score')
        critical_events = anomalies_df.head(max_anomalies).to_dict('records')
    else:
        # Fallback: use high values as anomalies
        critical_events = [
            m for m in metrics 
            if m.get('latency', 0) > 50 or m.get('loss', 0) > 5 or m.get('utilization', 0) > 90
        ][:max_anomalies]

    if not critical_events:
        logger.info("✅ No anomalies detected in simulator metrics")
        return {"analyzed_events": [], "decisions": [], "actions_taken": [], "timestamp": time.time()}

    logger.warning(f"🔴 Detected {len(critical_events)} anomalies in simulator data")

    memory = load_memory()
    
    results = {
        "analyzed_events": [],
        "decisions": [],
        "actions_taken": [],
        "timestamp": time.time()
    }

    for event in critical_events:
        # Convert simulator format to agent format
        # Device should be extracted from the 'device' field directly
        device = event.get('device', 'unknown')
        
        # Fallback: try other fields if device is still unknown
        if device == 'unknown' or not device:
            device = event.get('link', event.get('node1', event.get('node2', 'unknown')))
        
        score = event.get('severity_score', -0.08)
        tier = assign_tier(score)
        
        # Map fields
        agent_event = {
            'device': device,
            'latency': event.get('latency', 0),
            'packet_loss': event.get('loss', 0),
            'bgp_flaps': event.get('bgp_flaps', 0),
            'throughput_gbps': event.get('utilization', 0),
            'severity_score': score
        }

        logger.info(f"🔍 ANALYZING: {device} | lat={agent_event.get('latency', 0):.1f}ms | loss={agent_event.get('packet_loss', 0):.1f}%")

        blast = compute_blast_radius(device)
        noisy = apply_partial_obs(agent_event)

        try:
            decision = reason(noisy, tier, blast, memory)
            action_name = decision['action']
            llm_conf = int(decision.get('llm_confidence', 85))

            logger.info(f"🧠 Root Cause: {decision.get('root_cause_hypothesis')}")
            logger.info(f"🛡️ Action: {action_name} (Tier {tier}, conf: {llm_conf}%)")

            # Execute based on tier
            rec = execute_action(action_name, decision.get('params', [device]), device, noisy)

            # Evaluate
            if rec:
                ev = evaluate_action(rec)
                rec.update(
                    outcome_verdict=ev['verdict'],
                    outcome_confidence=ev['confidence_pct'],
                    outcome_correct=ev['correct'],
                    better_action=ev['better_action']
                )

            results["analyzed_events"].append(agent_event)
            results["decisions"].append(decision)
            results["actions_taken"].append(True)

            # Save to memory
            entry = {
                "timestamp": rec.get('timestamp', time.time()),
                "device": device,
                "action": action_name,
                "trigger_metrics": rec['trigger_metrics'],
                "predicted_outcome": rec['predicted_outcome'],
                "outcome_verdict": rec.get('outcome_verdict', 'N/A'),
                "outcome_confidence": rec.get('outcome_confidence', 0),
                "outcome_correct": rec.get('outcome_correct', False),
                "better_action": rec.get('better_action'),
                "learned_rule": decision.get('learning_policy_update'),
                "status": rec.get('status', 'EXECUTED')
            }
            save_memory(entry)
            memory.append(entry)
            logger.info(f"📚 Learned: {decision.get('learning_policy_update')}")

        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            results["analyzed_events"].append({"error": str(e), "link": device})

    return results

# ── STANDALONE RUNNER ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*60)
    print(" 🌐 NEUROTECH ENTERPRISE AGENTIC OPS LAYER ONLINE")
    print("="*60)
    run_agent_cycle()

