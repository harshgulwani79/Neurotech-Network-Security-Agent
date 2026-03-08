import { ShieldCheck, XCircle, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const ActionApprovalQueue = ({ actions, onApprove, onReject }) => {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">Human-in-the-Loop Approval</h3>
        <span className="px-2 py-1 bg-amber-50 text-amber-600 text-[10px] font-bold rounded-full border border-amber-100 uppercase tracking-wider">
          {actions.length} Pending
        </span>
      </div>

      <div className="space-y-4">
        <AnimatePresence>
          {actions.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-8 text-slate-400 text-sm italic"
            >
              No actions pending approval.
            </motion.div>
          ) : (
            actions.map((action) => (
              <motion.div
                key={action.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="p-4 bg-slate-50 rounded-xl border border-slate-100"
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="p-2 bg-amber-100 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{action.title}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{action.description}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onApprove(action.id)}
                    className="flex-1 flex items-center justify-center gap-2 py-2 bg-indigo-600 text-white rounded-lg text-xs font-medium hover:bg-indigo-700 transition-colors"
                  >
                    <ShieldCheck className="w-3 h-3" /> Approve
                  </button>
                  <button
                    onClick={() => onReject(action.id)}
                    className="flex-1 flex items-center justify-center gap-2 py-2 bg-white text-slate-600 border border-slate-200 rounded-lg text-xs font-medium hover:bg-slate-50 transition-colors"
                  >
                    <XCircle className="w-3 h-3" /> Reject
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ActionApprovalQueue;
