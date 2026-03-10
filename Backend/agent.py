from groq import Groq
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
import logging, json, os, time, random

# ── SETUP ─────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("Neurotech_NOC")

GROQ_API_KEY       = "MY API KEY"   # https://console.groq.com
client             = Groq(api_key=GROQ_API_KEY)
MODEL_ID           = "llama-3.3-70b-versatile"
MEMORY_FILE        = "network_memory.json"
AUDIT_LOG          = "audit_log.txt"
MAX_EVENTS         = 6
CALL_DELAY         = 3
MAX_RETRIES        = 3
AUTO_EXEC_MIN_CONF = 80     # Tier 1 auto-executes ONLY if LLM confidence >= this
PARTIAL_OBS_RATE   = 0.20   # 20% chance any single metric is masked (sensor outage sim)

# Tier thresholds — tuned to actual Isolation Forest score clusters
TIER1_THRESHOLD = -0.072    # score > -0.072  → Tier 1 (auto)
TIER2_THRESHOLD = -0.079    # score > -0.079  → Tier 2 (human), else Tier 3 (escalate)

# Valid actions per tier — FIX 1: LLM is constrained to ONLY these
TIER_ACTIONS = {
    1: ["rate_limit", "qos_adjustment"],
    2: ["traffic_reroute", "config_rollback"],
    3: ["escalate"]
}

ACTION_OUTCOMES = {
    "rate_limit":      {"latency_reduction": "30-40%", "risk": "low",    "reversible": True,  "recovery_mins": 5},
    "qos_adjustment":  {"latency_reduction": "20-30%", "risk": "low",    "reversible": True,  "recovery_mins": 3},
    "traffic_reroute": {"latency_reduction": "60-80%", "risk": "medium", "reversible": True,  "recovery_mins": 10},
    "config_rollback": {"latency_reduction": "50-70%", "risk": "medium", "reversible": True,  "recovery_mins": 15},
    "escalate":        {"latency_reduction": "N/A",    "risk": "high",   "reversible": False, "recovery_mins": 60},
}

try:
    TOPOLOGY = json.load(open('topology.json'))
except FileNotFoundError:
    logger.error("topology.json not found!"); TOPOLOGY = {}

# ── MEMORY ────────────────────────────────────────────────────────────────────
def load_memory() -> list:
    if not os.path.exists(MEMORY_FILE): return []
    try:    return json.load(open(MEMORY_FILE))
    except: return []

def save_memory(entry: dict):
    mem = load_memory(); mem.append(entry)
    json.dump(mem[-50:], open(MEMORY_FILE, 'w'), indent=2)

def device_history(device: str) -> list:
    return [m for m in load_memory() if m.get('device') == device]

# ── PARTIAL OBSERVABILITY ─────────────────────────────────────────────────────
def apply_partial_obs(event: dict) -> dict:
    """
    Real ISPs never have 100% sensor uptime.
    Randomly masks 20% of metrics as None so the agent must reason under uncertainty.
    """
    noisy, masked = dict(event), []
    for field in ['latency', 'packet_loss', 'bgp_flaps', 'throughput_gbps']:
        if random.random() < PARTIAL_OBS_RATE:
            noisy[field] = None; masked.append(field)
    if masked:
        print(f"   ⚠️  [PARTIAL OBS] Sensor unavailable: {', '.join(masked)}")
    return noisy

# ── TIER ASSIGNMENT ───────────────────────────────────────────────────────────
def assign_tier(score: float) -> int:
    """Tier is ALWAYS set by IF score. LLM cannot override this."""
    if score > TIER1_THRESHOLD: return 1
    if score > TIER2_THRESHOLD: return 2
    return 3

# ── BLAST RADIUS (BFS over topology graph) ────────────────────────────────────
def compute_blast_radius(device: str, depth: int = 2) -> dict:
    """
    BFS traversal up to `depth` hops through topology graph.
    Returns exact affected devices + real customer impact count from topology data.
    """
    visited, queue, customers = {device: 0}, [device], 0
    while queue:
        cur = queue.pop(0)
        if visited[cur] >= depth: continue
        node = TOPOLOGY.get(cur, {})
        customers += node.get('customers_affected', 0)
        for n in node.get('connected_to', []):
            if n not in visited:
                visited[n] = visited[cur] + 1; queue.append(n)
    affected = [d for d in visited if d != device]
    return {"origin": device, "affected_devices": affected,
            "customers_at_risk": customers, "hop_map": visited}

# ── ACTION EXECUTION ──────────────────────────────────────────────────────────
def execute_action(action: str, params: list, device: str, event: dict, status="EXECUTED") -> dict:
    outcome = ACTION_OUTCOMES.get(action, {"latency_reduction":"unknown","risk":"unknown",
                                           "reversible":True,"recovery_mins":30})
    metrics = {"latency_ms": event.get('latency'), "packet_loss_pct": event.get('packet_loss'),
               "bgp_flaps":  event.get('bgp_flaps'), "throughput_gbps": event.get('throughput_gbps'),
               "severity_score": event.get('severity_score')}
    with open(AUDIT_LOG, 'a') as f:
        f.write(f"[{time.ctime()}] {status}: {action} | {device} | metrics={metrics}\n")
    return {"timestamp": time.time(), "device": device, "action": action, "params": params,
            "trigger_metrics": metrics, "predicted_outcome": outcome, "status": status}

def rollback_action(original: dict, results: list):
    """
    Simulated rollback — audit log + memory entry.
    Real rollback: swap body with Netmiko/NAPALM SSH to push inverse config.
    FIX (rollback counter): appends to results[] so session summary counts it correctly.
    """
    device, action = original['device'], original['action']
    print(f"\n🔄 [ROLLBACK] Reversing '{action}' on {device}...")
    with open(AUDIT_LOG, 'a') as f:
        f.write(f"[{time.ctime()}] ROLLBACK: reversed '{action}' on {device}\n")
    rb_entry = {"timestamp": time.time(), "device": device, "action": f"ROLLBACK:{action}",
                "trigger_metrics": original.get('trigger_metrics', {}),
                "predicted_outcome": {"latency_reduction": "restoring pre-action state"},
                "outcome_verdict": "🔄 ROLLED BACK", "outcome_correct": False,
                "learned_rule": None,
                "status": "ROLLBACK"}
    save_memory(rb_entry)
    results.append(rb_entry)   # FIX: now counted in summary
    print(f" └─ ✅ Rollback logged. '{action}' reversed in audit + memory.")

# ── ACTION EVALUATION ─────────────────────────────────────────────────────────
def evaluate_action(record: dict) -> dict:
    action, severity = record['action'], record['trigger_metrics']['severity_score']
    latency = float(record['trigger_metrics']['latency_ms'] or 0)
    issues, correct, better, confidence = [], True, None, 100

    if severity > TIER1_THRESHOLD:
        if action not in TIER_ACTIONS[1]:
            correct, better, confidence = False, 'rate_limit', 60
            issues.append(f"Over-reaction: Tier 1 event got '{action}', should be rate_limit")
    elif severity > TIER2_THRESHOLD:
        if action in TIER_ACTIONS[1]:
            correct, better, confidence = False, 'traffic_reroute', 70
            issues.append(f"Under-reaction: Tier 2 event got '{action}', should be traffic_reroute")
        elif action == 'escalate':
            correct, better, confidence = False, 'traffic_reroute', 80
            issues.append("Over-escalation: Tier 2 could be handled with traffic_reroute")
    else:
        if action != 'escalate':
            correct, better, confidence = False, 'escalate', 50
            issues.append(f"Under-reaction: Tier 3 MUST be escalated, not '{action}'")
    if latency > 500 and action == 'rate_limit':
        correct, better, confidence = False, 'traffic_reroute', min(confidence, 80)
        issues.append(f"Latency {latency:.0f}ms too high for rate_limit alone")

    return {"verdict": "✅ CORRECT" if correct else "⚠️  SUBOPTIMAL",
            "correct": correct, "confidence_pct": max(0, confidence),
            "issues":  issues or ["Action matches event severity and type"],
            "better_action": better,
            "recommendation": f"Consider '{better}' next time" if better else "No change needed"}

# ── POLICY VIOLATION CHECK ─────────────────────────────────────────────────────
def check_policy_violations(action: str, device: str, memory: list, tier: int) -> list:
    """
    Compares proposed action against learned rules.
    Makes the Learn loop VISIBLE — agent flags when it's about to repeat a past mistake.
    Only flags genuine violations — not false alarms when the action is already correct for tier.
    """
    violations = []
    correct_for_tier = set(TIER_ACTIONS[tier])  # actions that are valid for this tier
    for m in memory[-10:]:
        rule   = m.get('learned_rule', '')
        mdev   = m.get('device') == device
        # Only flag escalation rule mismatch if the current action is NOT the right tier action
        if mdev and 'escalat' in rule.lower() and action != 'escalate' and action not in correct_for_tier:
            violations.append(f"Past rule: '{rule}' — but proposed action is '{action}'")
        # Only flag rollback repeat if this exact action was rolled back AND it's not the correct tier action
        if mdev and f"ROLLBACK:{action}" in m.get('action', '') and action not in correct_for_tier:
            violations.append(f"'{action}' was previously rolled back on {device} — repeating it?")
    return violations

# ── LLM CALL ──────────────────────────────────────────────────────────────────
def call_llm(prompt: str) -> str:
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = client.chat.completions.create(
                model=MODEL_ID, temperature=0.1, max_tokens=512,
                messages=[
                    {"role": "system", "content": "You are a network NOC AI. Reply ONLY with valid JSON. No markdown, no explanation."},
                    {"role": "user",   "content": prompt}
                ])
            return r.choices[0].message.content.strip()
        except Exception as e:
            if ('429' in str(e) or 'rate' in str(e).lower()) and attempt < MAX_RETRIES:
                wait = 30 * (attempt + 1)
                logger.warning(f"Rate limit. Waiting {wait}s..."); time.sleep(wait)
            else: raise

# ── AGENT BRAIN ───────────────────────────────────────────────────────────────
def reason(event: dict, tier: int, blast: dict, memory: list) -> dict:
    """
    FIX 1: Tier is locked. LLM is only told valid actions for that tier.
    FIX 2: None metrics shown as UNAVAILABLE — LLM reasons conservatively.
    FIX 3 (learn loop): Past learned rules injected. LLM must apply them.
    FIX 4: LLM returns llm_confidence — used to gate auto-execution.
    FIX 5: Real BFS blast radius data passed in — LLM summarises it.
    """
    device  = event.get('device', '')
    fmt     = lambda v, s: f"{v:{s}}" if v is not None else "UNAVAILABLE"
    valid   = TIER_ACTIONS[tier]   # FIX 1: only valid actions shown to LLM

    # FIX 3 (learn loop): pull learned rules + show run-over-run learning
    past_rules   = [m['learned_rule'] for m in memory[-6:] if m.get('learned_rule')]
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
    raw    = call_llm(prompt)
    result = json.loads(raw[raw.find('{'):raw.rfind('}')+1])

    # Hard overrides — LLM cannot break these
    result['risk_tier'] = tier
    if result.get('action') not in valid:
        logger.warning(f"LLM chose invalid action '{result.get('action')}' for Tier {tier} — correcting to '{valid[0]}'")
        result['action'] = valid[0]
    return result

# ── MAIN ──────────────────────────────────────────────────────────────────────
def run():
    # ── ML Detection ──
    logger.info("Ingesting telemetry_stream.csv...")
    df       = pd.read_csv("telemetry_stream.csv")
    features = ['latency', 'packet_loss', 'bgp_flaps', 'throughput_gbps']
    X_scaled = StandardScaler().fit_transform(df[features])
    logger.info(f"Running Isolation Forest on {len(df)} vectors...")
    clf            = IsolationForest(contamination=0.001, random_state=42)
    df['anomaly']  = clf.fit_predict(X_scaled)
    df['severity'] = clf.decision_function(X_scaled)

    # Detection quality report
    if 'label' in df.columns:
        det = df[df['anomaly'] == -1]
        tp  = det[det['label'] != 'normal']
        fp  = det[det['label'] == 'normal']
        fn  = df[(df['anomaly'] == 1) & (df['label'] != 'normal')]
        print("\n" + "="*60 + "\n 🎯 ISOLATION FOREST DETECTION QUALITY REPORT\n" + "="*60)
        print(f" ✅ True Positives: {len(tp)}  ❌ False Positives: {len(fp)}  🔍 Missed: {len(fn)}")
        if len(tp):
            print(f" 📊 Precision: {len(tp)/(len(tp)+len(fp))*100:.1f}%  Recall: {len(tp)/(len(tp)+len(fn))*100:.1f}%")
        print("="*60 + "\n")

    events = (df[df['anomaly'] == -1].sort_values('severity')
              .rename(columns={'severity': 'severity_score'})
              .head(MAX_EVENTS).to_dict('records'))

    # Cascade check
    devs = {e['device'] for e in events}
    cascades = [f"{d} ↔ {', '.join(set(TOPOLOGY.get(d,{}).get('connected_to',[])) & devs)}"
                for d in devs if set(TOPOLOGY.get(d,{}).get('connected_to',[])) & devs]
    if cascades:
        print("⚠️  [CASCADE ALERT] Connected devices failing simultaneously!")
        for c in set(cascades): print(f"   🔗 {c}")
        print("   → Blast radius is WIDER than individual scores suggest.\n")

    memory  = load_memory()
    results = []

    # FIX 4 — startup banner showing system config + memory state
    # Only show clean IF...THEN policies in banner, not rollback noise
    prior_rules = list(dict.fromkeys(
        m['learned_rule'] for m in memory
        if m.get('learned_rule') and m['learned_rule'].upper().startswith('IF')
    ))
    print("="*60)
    print(f" ⚙️  CONFIG  |  Model: {MODEL_ID}")
    print(f"            |  Confidence threshold: {AUTO_EXEC_MIN_CONF}%")
    print(f"            |  Partial obs rate:     {int(PARTIAL_OBS_RATE*100)}%")
    print(f"            |  Memory loaded:        {len(memory)} past events")
    if prior_rules:
        print(f"\n 🧠 LEARNED POLICIES FROM PREVIOUS RUNS:")
        for r in prior_rules[-4:]: print(f"    • {r}")
    else:
        print(f"\n 🧠 No prior learned policies — this is Run 1.")
    print("="*60)
    print(f"\n 🔎 Processing {len(events)} anomalies then exiting.\n" + "="*60)

    tier_labels = {1: "✅ TIER 1 (Auto)", 2: "⚠️  TIER 2 (Human)", 3: "🚨 TIER 3 (Escalate)"}

    for i, event in enumerate(events, 1):
        device = event['device']
        score  = event['severity_score']
        tier   = assign_tier(score)

        print(f"\n{'='*60}")
        print(f"🔍 [{i}/{len(events)}] {device}  score={score:.4f}  "
              f"lat={event.get('latency'):.0f}ms  loss={event.get('packet_loss'):.1f}%  "
              f"flaps={event.get('bgp_flaps')}  →  {tier_labels[tier]}")
        print("="*60)

        hist = device_history(device)
        if hist:
            print(f"\n📂 [MEMORY] {len(hist)} past action(s) for {device}:")
            for h in hist[-2:]:
                print(f"   └─ {time.ctime(h['timestamp']) if 'timestamp' in h else '?'}: "
                      f"{h.get('action','?')} → {h.get('outcome_verdict','?')}")

        noisy = apply_partial_obs(event)

        # FIX 2 — concrete blast radius with real customer numbers
        blast = compute_blast_radius(device)
        customers_fmt = f"{blast['customers_at_risk']:,}"
        print(f"\n🌐 [BLAST RADIUS] {device} → {len(blast['affected_devices'])} device(s) affected: "
              f"{', '.join(blast['affected_devices']) or 'none'}")
        print(f"   └─ 🚨 Customers at risk: {customers_fmt}")

        try:
            decision    = reason(noisy, tier, blast, memory)
            action_name = decision['action']
            llm_conf    = int(decision.get('llm_confidence', 85))
            rec         = None

            print(f"\n🧠 [AI REASONING]")
            print(f" ├─ Root Cause:     {decision['root_cause_hypothesis']}")
            print(f" ├─ Blast Summary:  {decision['blast_radius_summary']}")
            print(f" └─ LLM Confidence: {llm_conf}%")

            # FIX 3 — policy violation check (learn loop visibility)
            violations = check_policy_violations(action_name, device, memory, tier)
            if violations:
                print(f"\n🚨 [POLICY VIOLATIONS DETECTED]")
                for v in violations: print(f"   ⚠️  {v}")

            print(f"\n🛡️  [GUARDRAILS & EXECUTION]")

            if tier == 1:
                print(f" ├─ Risk Level: ✅ TIER 1 (Fully Autonomous)")
                if llm_conf >= AUTO_EXEC_MIN_CONF:
                    rec = execute_action(action_name, decision['params'], device, noisy)
                    print(f" ├─ Action:    {action_name} on {decision['params']}")
                    print(f" └─ Predicted: {rec['predicted_outcome']['latency_reduction']} reduction, "
                          f"~{rec['predicted_outcome']['recovery_mins']} min recovery")
                else:
                    print(f" ├─ ⚠️  LLM confidence {llm_conf}% < threshold {AUTO_EXEC_MIN_CONF}%")
                    print(f" └─ Escalating to human despite Tier 1.")
                    if input(f" ❓ Low-confidence — Approve '{action_name}'? (y/n): ").strip().lower() == 'y':
                        rec = execute_action(action_name, decision['params'], device, noisy)
                    else:
                        print(" └─ ❌ Rejected.")

            elif tier == 2:
                print(f" ├─ Risk Level: ⚠️  TIER 2 (Human Oversight Required)")
                print(f" ├─ Proposed:  {action_name} on {decision['params']}")
                ans = input(" ❓ Approve? (y/n/rollback): ").strip().lower()
                if ans == 'y':
                    rec = execute_action(action_name, decision['params'], device, noisy)
                    print(f" └─ Predicted: {rec['predicted_outcome']['latency_reduction']} reduction, "
                          f"~{rec['predicted_outcome']['recovery_mins']} min recovery")
                elif ans == 'rollback':
                    last = next((h for h in reversed(hist) if 'ROLLBACK' not in h.get('action','')), None)
                    if last: rollback_action(last, results)
                    else:    print(" └─ No previous action to roll back.")
                    rec = execute_action(action_name, decision['params'], device, noisy, "ROLLBACK_REQUESTED")
                else:
                    print(" └─ ❌ Rejected — logging to memory.")
                    _t = time.time()
                    rec = {"timestamp": _t, "device": device, "action": action_name,
                           "params": decision['params'],
                           "trigger_metrics": {"latency_ms": noisy.get('latency'),
                               "packet_loss_pct": noisy.get('packet_loss'),
                               "bgp_flaps": noisy.get('bgp_flaps'),
                               "throughput_gbps": noisy.get('throughput_gbps'),
                               "severity_score": score},
                           "predicted_outcome": {"latency_reduction":"N/A","risk":"N/A",
                                                 "reversible":True,"recovery_mins":0},
                           "outcome_verdict": "🚫 REJECTED", "outcome_confidence": 0,
                           "outcome_correct": False, "better_action": None,
                           "status": "REJECTED_BY_OPERATOR"}

            else:   # Tier 3 — always escalate, no human prompt
                print(f" ├─ Risk Level: 🚨 TIER 3 (Escalate Only — autonomous)")
                print(f" └─ 🚨 ESCALATING {device} to Level 3 Engineering.")
                rec = execute_action('escalate', [device], device, noisy)

            # ── Evaluate ──
            if rec:
                try:
                    ev = evaluate_action(rec)
                    rec.update(outcome_verdict=ev['verdict'], outcome_confidence=ev['confidence_pct'],
                               outcome_correct=ev['correct'], better_action=ev['better_action'])
                    print(f"\n🔬 [ACTION EVALUATION]")
                    print(f" ├─ Verdict: {ev['verdict']}  (Confidence: {ev['confidence_pct']}%)")
                    for issue in ev['issues']: print(f" ├─ {issue}")
                    print(f" └─ {ev['recommendation']}")
                    # Auto-rollback if wrong AND low confidence
                    if not ev['correct'] and ev['confidence_pct'] <= 60 and rec.get('status') == 'EXECUTED':
                        print(f"\n⚠️  Eval confidence {ev['confidence_pct']}% ≤ 60% — auto-rollback triggered.")
                        rollback_action(rec, results)
                except Exception as ee:
                    logger.warning(f"Eval failed (non-critical): {ee}")
                    rec.setdefault('outcome_verdict', 'N/A')
                    rec.setdefault('outcome_correct', False)

            # ── Save to memory ──
            if rec:
                entry = {"timestamp": rec.get('timestamp', time.time()), "device": device,
                         "action": rec.get('action', action_name),
                         "trigger_metrics": rec['trigger_metrics'],
                         "predicted_outcome": rec['predicted_outcome'],
                         "outcome_verdict": rec.get('outcome_verdict', 'N/A'),
                         "outcome_confidence": rec.get('outcome_confidence', 0),
                         "outcome_correct": rec.get('outcome_correct', False),
                         "better_action": rec.get('better_action'),
                         "learned_rule": decision['learning_policy_update'],
                         "status": rec.get('status', 'EXECUTED')}
                save_memory(entry); memory.append(entry); results.append(entry)
                print(f"\n📚 [LEARN] Policy saved: {decision['learning_policy_update']}")

        except Exception as e:
            print(f"\n❌ [ERROR] {device}: {e}")

        if i < len(events):
            print(f"\n⏳ {CALL_DELAY}s..."); time.sleep(CALL_DELAY)

    # ── Session Summary ──
    t1 = sum(1 for r in results if r.get('trigger_metrics',{}).get('severity_score', 0) > TIER1_THRESHOLD)
    t2 = sum(1 for r in results if TIER2_THRESHOLD < r.get('trigger_metrics',{}).get('severity_score', 0) <= TIER1_THRESHOLD)
    t3 = sum(1 for r in results if r.get('trigger_metrics',{}).get('severity_score', 0) <= TIER2_THRESHOLD)
    ok = sum(1 for r in results if r.get('outcome_correct'))
    rb = sum(1 for r in results if 'ROLLBACK' in r.get('action', ''))
    all_rules = list(dict.fromkeys(r['learned_rule'] for r in results if r.get('learned_rule')))

    print("\n" + "="*60 + "\n 📊 SESSION SUMMARY\n" + "="*60)
    print(f" ✅ Tier 1 (Auto):       {t1}")
    print(f" ⚠️  Tier 2 (Human):     {t2}")
    print(f" 🚨 Tier 3 (Escalated): {t3}")
    print(f" 🎯 Correct Actions:    {ok}/{len([r for r in results if 'ROLLBACK' not in r.get('action','')])} decisions")
    print(f" 🔄 Rollbacks:          {rb}")
    if all_rules:
        print(f"\n 🧠 POLICIES LEARNED THIS SESSION:")
        for r in all_rules: print(f"    • {r}")
    print(f"\n 💾 Memory: {MEMORY_FILE}   📋 Audit: {AUDIT_LOG}")
    print("="*60 + "\n 🏁 NEUROTECH AGENTIC OPS COMPLETE\n" + "="*60)

if __name__ == "__main__":
    print("="*60 + "\n 🌐 NEUROTECH ENTERPRISE AGENTIC OPS LAYER ONLINE \n" + "="*60)
    run()