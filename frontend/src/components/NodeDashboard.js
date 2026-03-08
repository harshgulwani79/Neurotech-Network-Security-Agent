import { Cpu, Activity, Zap, AlertCircle } from "lucide-react";

const NodeDashboard = ({ node, metrics }) => {
  // Filter metrics for this node - check device, node1, node2, or link
  const nodeMetrics = metrics.filter(m => 
    m.device === node || 
    m.node1 === node || 
    m.node2 === node || 
    (m.link && m.link.includes(node))
  );
  
  // If no matching metrics found for this node, use first metric or show N/A
  let avgLatency = 0;
  let avgLoss = 0;
  let avgUtil = 0;
  
  if (nodeMetrics.length > 0) {
    avgLatency = nodeMetrics.reduce((acc, m) => acc + (m.latency || 0), 0) / nodeMetrics.length;
    avgLoss = nodeMetrics.reduce((acc, m) => acc + (m.loss || 0), 0) / nodeMetrics.length;
    avgUtil = nodeMetrics.reduce((acc, m) => acc + (m.utilization || 0), 0) / nodeMetrics.length;
  } else if (metrics.length > 0) {
    // Fallback: show average of all metrics if no specific match
    avgLatency = metrics.reduce((acc, m) => acc + (m.latency || 0), 0) / metrics.length;
    avgLoss = metrics.reduce((acc, m) => acc + (m.loss || 0), 0) / metrics.length;
    avgUtil = metrics.reduce((acc, m) => acc + (m.utilization || 0), 0) / metrics.length;
  }

  // Get display name from node (could be city name)
  const displayName = typeof node === 'object' ? node.name || node.id : node;

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-slate-100 rounded-lg">
          <Cpu className="w-5 h-5 text-slate-600" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-slate-900">{displayName}</h3>
          <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Router Status</p>
        </div>
      </div>

      <div className="space-y-4">
        <MetricRow 
          icon={<Activity className="w-4 h-4 text-indigo-500" />} 
          label="Latency" 
          value={`${avgLatency.toFixed(1)}ms`} 
          status={avgLatency > 30 ? "warning" : "good"}
        />
        <MetricRow 
          icon={<AlertCircle className="w-4 h-4 text-rose-500" />} 
          label="Packet Loss" 
          value={`${avgLoss.toFixed(2)}%`} 
          status={avgLoss > 1 ? "critical" : "good"}
        />
        <MetricRow 
          icon={<Zap className="w-4 h-4 text-amber-500" />} 
          label="Utilization" 
          value={`${avgUtil.toFixed(1)}%`} 
          status={avgUtil > 85 ? "critical" : avgUtil > 70 ? "warning" : "good"}
        />
      </div>
    </div>
  );
};

const MetricRow = ({ icon, label, value, status }) => (
  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-100">
    <div className="flex items-center gap-3">
      {icon}
      <span className="text-xs font-medium text-slate-600">{label}</span>
    </div>
    <div className="flex items-center gap-3">
      <span className="text-sm font-bold text-slate-900">{value}</span>
      <div className={`w-2 h-2 rounded-full ${
        status === "good" ? "bg-emerald-500" : 
        status === "warning" ? "bg-amber-500" : "bg-rose-500"
      }`} />
    </div>
  </div>
);

export default NodeDashboard;

