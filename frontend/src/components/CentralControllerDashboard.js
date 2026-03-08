import { Brain, Activity, Terminal, ShieldAlert } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const CentralControllerDashboard = ({ logs }) => {
  return (
    <div className="bg-slate-900 rounded-2xl p-6 shadow-xl border border-white/10 h-[400px] flex flex-col">
      <div className="flex items-center gap-2 mb-4 border-b border-white/10 pb-4 flex-shrink-0">
        <Terminal className="w-5 h-5 text-emerald-400" />
        <h3 className="text-sm font-medium text-emerald-400 uppercase tracking-wider">Global Controller Reasoning</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3">
        <AnimatePresence initial={false}>
          {logs && logs.length > 0 ? logs.slice(0, 30).map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="border-l-2 border-emerald-500/30 pl-4 py-2"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-mono text-slate-500">
                  {log.timestamp || 'N/A'}
                </span>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                  log.risk_level === 'High' ? 'bg-rose-500/10 text-rose-400' : 
                  log.risk_level === 'Medium' ? 'bg-amber-500/10 text-amber-400' :
                  'bg-emerald-500/10 text-emerald-400'
                }`}>
                  {log.status || 'Status Unknown'}
                </span>
              </div>
              
              <div className="flex items-start gap-3">
                <Brain className="w-4 h-4 text-indigo-400 mt-1 flex-shrink-0" />
                <p className="text-sm text-slate-300 italic">
                  "{log.summary || log.intervention || 'No details available'}"
                </p>
              </div>
              
              {log.intervention && log.intervention !== 'None' && (
                <div className="mt-2 flex items-center gap-3">
                  <Activity className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  <p className="text-xs font-medium text-amber-400">
                    Intervention: {log.intervention}
                  </p>
                </div>
              )}
              
              {log.risk_level === 'High' && (
                <div className="mt-2 flex items-center gap-2 text-[10px] text-rose-400 font-bold uppercase tracking-widest">
                  <ShieldAlert className="w-3 h-3" /> SLA Breach Risk
                </div>
              )}
            </motion.div>
          )) : (
            <div className="text-center py-8 text-slate-500 text-sm italic">
              Waiting for network events...
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default CentralControllerDashboard;

