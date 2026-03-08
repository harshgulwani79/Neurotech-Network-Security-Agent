import React from 'react';

const LearnedPolicies = ({ policies = [] }) => {
  // Extract unique learned rules
  const uniqueRules = [];
  const seenRules = new Set();
  
  policies.forEach(p => {
    const rule = p.learned_rule;
    if (rule && !seenRules.has(rule)) {
      seenRules.add(rule);
      uniqueRules.push({
        rule,
        device: p.device,
        action: p.action,
        timestamp: p.timestamp,
        outcome: p.outcome_verdict,
        status: p.status
      });
    }
  });

  const getTierFromAction = (action) => {
    if (action === 'rate_limit' || action === 'qos_adjustment') return 1;
    if (action === 'traffic_reroute' || action === 'config_rollback') return 2;
    if (action === 'escalate') return 3;
    return 0;
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 1: return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      case 2: return 'bg-amber-100 text-amber-700 border-amber-200';
      case 3: return 'bg-rose-100 text-rose-700 border-rose-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getTierLabel = (tier) => {
    switch (tier) {
      case 1: return 'T1 Auto';
      case 2: return 'T2 Human';
      case 3: return 'T3 Escalate';
      default: return 'Unknown';
    }
  };

  const getOutcomeColor = (outcome) => {
    if (!outcome) return 'text-slate-500';
    if (outcome.includes('CORRECT')) return 'text-emerald-600';
    if (outcome.includes('SUBOPTIMAL')) return 'text-amber-600';
    if (outcome.includes('ROLLED BACK')) return 'text-rose-600';
    if (outcome.includes('REJECTED')) return 'text-slate-500';
    return 'text-slate-600';
  };

  const formatTimestamp = (ts) => {
    if (!ts) return '';
    const date = new Date(ts * 1000);
    return date.toLocaleTimeString();
  };

  const formatRule = (rule) => {
    if (!rule) return 'No rule';
    // Make IF...THEN more readable
    return rule
      .replace(/IF /gi, 'IF ')
      .replace(/ THEN /gi, ' → ');
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 rounded-lg">
            <svg className="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">AI Learned Policies</h3>
            <p className="text-xs text-slate-500">{uniqueRules.length} unique policies</p>
          </div>
        </div>
        
        {/* Summary badges */}
        <div className="flex gap-2">
          {['rate_limit', 'traffic_reroute', 'escalate'].map(action => {
            const count = policies.filter(p => p.action === action).length;
            if (count === 0) return null;
            const tier = getTierFromAction(action);
            return (
              <span key={action} className={`px-2 py-1 rounded-full text-xs font-medium border ${getTierColor(tier)}`}>
                {getTierLabel(tier)}: {count}
              </span>
            );
          })}
        </div>
      </div>

      {/* Unique Rules */}
      {uniqueRules.length > 0 ? (
        <div className="space-y-3 mb-6">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Policy Rules</h4>
          {uniqueRules.slice(0, 5).map((item, idx) => (
            <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-100">
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs font-medium text-slate-700 font-mono">
                  {formatRule(item.rule)}
                </span>
                <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${getTierColor(getTierFromAction(item.action))}`}>
                  {getTierLabel(getTierFromAction(item.action))}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-slate-400">{item.device}</span>
                <span className="text-xs text-slate-300">•</span>
                <span className={`text-xs ${getOutcomeColor(item.outcome)}`}>{item.outcome || 'N/A'}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-slate-400">
          <p className="text-sm">No learned policies yet</p>
          <p className="text-xs mt-1">Policies will appear after the first anomaly</p>
        </div>
      )}

      {/* Recent Actions Timeline */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Recent Actions</h4>
        <div className="max-h-48 overflow-y-auto space-y-2">
          {policies.slice(0, 10).map((p, idx) => (
            <div key={idx} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50">
              <div className={`w-2 h-2 rounded-full ${
                p.status === 'EXECUTED' ? 'bg-emerald-500' :
                p.status === 'ROLLBACK' ? 'bg-rose-500' :
                p.status === 'REJECTED_BY_OPERATOR' ? 'bg-slate-400' :
                'bg-amber-500'
              }`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-slate-900 truncate">{p.device}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${getTierColor(getTierFromAction(p.action))}`}>
                    {p.action}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs ${getOutcomeColor(p.outcome_verdict)}`}>
                    {p.outcome_verdict || p.status}
                  </span>
                  {p.outcome_confidence > 0 && (
                    <span className="text-xs text-slate-400">
                      ({p.outcome_confidence}% conf)
                    </span>
                  )}
                </div>
              </div>
              <span className="text-xs text-slate-400 whitespace-nowrap">
                {formatTimestamp(p.timestamp)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LearnedPolicies;

