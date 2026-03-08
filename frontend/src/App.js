import React, { useEffect, useState, useCallback } from "react";
import { Activity, Zap, AlertCircle, Cpu, BrainCircuit, Terminal, Play, History, Shield, Network } from "lucide-react";
import { connectWebSocket } from "./services/websocketService";
import { fetchHistory, injectAnomaly, getMode, setMode, getPolicies } from "./services/apiService";
import CentralControllerDashboard from "./components/CentralControllerDashboard";
import TelemetryVisualizer from "./components/TelemetryVisualizer";
import ActionApprovalQueue from "./components/ActionApprovalQueue";
import NodeDashboard from "./components/NodeDashboard";
import NetworkTopology from "./components/NetworkTopology";
import PredictiveAnalytics from "./components/PredictiveAnalytics";
import LearnedPolicies from "./components/LearnedPolicies";
import { AnimatePresence, motion } from "motion/react";

// Backend AI (Groq) is used - no frontend Gemini AI needed

const App = () => {
  const [metrics, setMetrics] = useState([]);
  const [history, setHistory] = useState([]);
  const [topology, setTopology] = useState({ nodes: [], links: [] });
  const [logs, setLogs] = useState([]);
  const [pendingActions, setPendingActions] = useState([]);
  const [isReasoning, setIsReasoning] = useState(false);
  const [activeAnomalies, setActiveAnomalies] = useState([]);
  const [systemMode, setSystemMode] = useState("real_time");
  const [currentTier, setCurrentTier] = useState(0);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [networkStats, setNetworkStats] = useState({ routes: 29, density: 65 });
  const [prevRoutes, setPrevRoutes] = useState(29);
  const [currentDevice, setCurrentDevice] = useState(null);

  // Derived nodes for topology visualization using city names
  const topologyNodes = React.useMemo(() => {
    return topology.nodes.map(node => ({
      id: node.id || node,
      name: node.name || node.id || node,
      type: node.type === 'core' ? 'server' : node.type === 'edge' ? 'workstation' : 'router'
    }));
  }, [topology.nodes]);

  useEffect(() => {
    const ws = connectWebSocket((data) => {
      setMetrics(data.metrics);
      setHistory(prev => [
        ...prev, 
        ...data.metrics.map(m => ({ ...m, timestamp: data.report?.timestamp }))
      ].slice(-100));
      setTopology(data.topology);
      
      // Update network stats - stable calculation based on actual metrics
      if (data.metrics && data.metrics.length > 0) {
        const totalUtil = data.metrics.reduce((acc, m) => acc + (m.utilization || 0), 0);
        const density = Math.round(totalUtil / data.metrics.length);
        
        // Calculate routes based on metrics - more stable
        const anomalyCount = data.anomalies?.length || 0;
        const baseRoutes = 29;
        const reduction = anomalyCount * 3;
        const newRoutes = Math.max(12, baseRoutes - reduction);
        
        setNetworkStats({
          density: density,
          routes: newRoutes
        });
        setPrevRoutes(newRoutes);
        
        setIsReasoning(true);
        setTimeout(() => setIsReasoning(false), 1000);
      }
      
      // Extract tier and AI analysis from the report
      if (data.report) {
        setCurrentTier(data.report.tier || 0);
        
        // Update logs with AI reasoning
        setLogs(prev => [data.report, ...prev].slice(0, 50));
      }
      
      // Get AI analysis from data
      if (data.ai_analysis) {
        setAiAnalysis(data.ai_analysis);
      }
      
      // Update current device immediately when analyzing (before AI response)
      // This makes the UI dynamic - shows the device being analyzed right away
      if (data.analyzing_device) {
        setCurrentDevice(data.analyzing_device);
      } else if (data.ai_analysis) {
        // Fallback: extract current device from the first analyzed event
        const analyzedEvents = data.ai_analysis?.analyzed_events || [];
        if (analyzedEvents.length > 0) {
          setCurrentDevice(analyzedEvents[0].device || null);
        }
      }
      
      // Load policies from memory in the response
      if (data.memory) {
        setPolicies(data.memory);
      }
      
      // If there are anomalies
      if (data.anomalies && data.anomalies.length > 0) {
        setActiveAnomalies(data.anomalies);
        
        // Tier 2 actions need human approval (show in queue)
        if (data.report && data.report.tier === 2) {
          setPendingActions(prev => [
            {
              id: Date.now(),
              title: `⚠️ TIER 2 Approval Required: ${data.report.intervention}`,
              description: data.report.summary,
              type: "approval",
              tier: 2,
              device: data.anomalies[0]?.device || 'Unknown'
            },
            ...prev
          ]);
        }
        
        // Tier 3 - Critical escalation (show in queue)
        if (data.report && data.report.tier === 3) {
          setPendingActions(prev => [
            {
              id: Date.now(),
              title: `🚨 TIER 3 CRITICAL: ${data.report.intervention}`,
              description: data.report.summary,
              type: "critical",
              tier: 3,
              device: data.anomalies[0]?.device || 'Unknown'
            },
            ...prev
          ]);
        }
      } else {
        setActiveAnomalies([]);
      }
    });

    fetchHistory().then(setLogs);

    return () => ws.close();
  }, []);

  const handleInject = (type) => {
    injectAnomaly(type).then(console.log);
  };

  const handleApprove = (id) => {
    setPendingActions(prev => prev.filter(a => a.id !== id));
  };

  const handleReject = (id) => {
    setPendingActions(prev => prev.filter(a => a.id !== id));
  };

  const handleModeChange = async (newMode) => {
    try {
      await setMode(newMode);
      setSystemMode(newMode);
    } catch (error) {
      console.error("Failed to change mode:", error);
    }
  };

  const loadPolicies = async () => {
    try {
      const result = await getPolicies();
      setPolicies(result.policies || []);
    } catch (error) {
      console.error("Failed to load policies:", error);
    }
  };

  // Load initial data
  useEffect(() => {
    getMode().then(data => setSystemMode(data.mode)).catch(console.error);
    loadPolicies();
  }, []);

  const avgLatency = metrics.reduce((acc, m) => acc + m.latency, 0) / (metrics.length || 1);
  const avgLoss = metrics.reduce((acc, m) => acc + m.loss, 0) / (metrics.length || 1);
  const totalThroughput = metrics.reduce((acc, m) => acc + m.utilization, 0);

  // Get core link for charts - use device field now
  const coreLinks = metrics.filter(m => 
    m.device && (
      m.device.includes('Core') || 
      m.device.includes('Mumbai') || 
      m.device.includes('Bangalore') ||
      m.device.includes('London') ||
      m.device.includes('Frankfurt')
    )
  );

  // Get edge nodes for dashboard
  const edgeNodes = topology.nodes.filter(n => 
    n.type === 'edge' || n.id?.includes('Edge') || n.name?.includes('Edge')
  ).slice(0, 2);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-indigo-100">
      <header className="bg-white border-b border-black/5 px-8 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
              <BrainCircuit className="text-white w-6 h-6" />
            </div>
            <div>
<h1 className="text-xl font-bold tracking-tight">Neurotech NOC Agent</h1>
              <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Autonomous Network Operations</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            {/* Mode Toggle */}
            <div className="flex items-center gap-2 bg-slate-100 rounded-lg p-1">
              <button
                onClick={() => handleModeChange("real_time")}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  systemMode === "real_time" 
                    ? "bg-indigo-600 text-white shadow-sm" 
                    : "text-slate-600 hover:bg-slate-200"
                }`}
              >
                <Play className="w-3 h-3" /> Real-time
              </button>
              <button
                onClick={() => handleModeChange("historical_csv")}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  systemMode === "historical_csv" 
                    ? "bg-indigo-600 text-white shadow-sm" 
                    : "text-slate-600 hover:bg-slate-200"
                }`}
              >
                <History className="w-3 h-3" /> Historical
              </button>
            </div>
            
            {/* Tier Display */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-bold ${
              currentTier === 0 ? "bg-emerald-50 text-emerald-600 border-emerald-100" :
              currentTier === 1 ? "bg-amber-50 text-amber-600 border-amber-100" :
              currentTier === 2 ? "bg-orange-50 text-orange-600 border-orange-100" :
              "bg-rose-50 text-rose-600 border-rose-100"
            }`}>
              <Shield className="w-3 h-3" />
              TIER {currentTier}
            </div>
            
            <AnimatePresence>
              {isReasoning && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-full border border-indigo-100"
                >
                  <Terminal className="w-3 h-3 animate-pulse" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">AI Reasoning...</span>
                </motion.div>
              )}
            </AnimatePresence>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 text-emerald-600 rounded-full border border-emerald-100">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-xs font-medium">System Online</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-8 space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard icon={<Activity className="w-5 h-5 text-indigo-500" />} label="Avg Latency" value={`${avgLatency.toFixed(1)}ms`} trend={avgLatency > 30 ? "high" : "normal"} />
          <StatCard icon={<AlertCircle className="w-5 h-5 text-rose-500" />} label="Packet Loss" value={`${avgLoss.toFixed(2)}%`} trend={avgLoss > 1 ? "high" : "normal"} />
          <StatCard icon={<Zap className="w-5 h-5 text-amber-500" />} label="Utilization" value={`${(totalThroughput / metrics.length || 0).toFixed(1)}%`} trend="normal" />
          <StatCard icon={<Cpu className="w-5 h-5 text-emerald-500" />} label="Nodes Active" value={topology.nodes.length.toString()} trend="normal" />
        </div>

        {/* Network Stats Bar */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-black/5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-50 rounded-lg">
                <Network className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Traffic Density</p>
                <p className="text-xl font-bold text-slate-900">{networkStats.density}%</p>
              </div>
            </div>
            <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-emerald-400 to-amber-400 rounded-full" 
                style={{ width: `${networkStats.density}%` }}
              />
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-black/5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-50 rounded-lg">
                <Activity className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Active Routes</p>
                <p className="text-xl font-bold text-slate-900">{networkStats.routes} Paths</p>
              </div>
            </div>
          </div>
        </div>

        {/* Learned Policies Display */}
        {policies.length > 0 && (
          <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-100">
            <div className="flex items-center gap-2 mb-3">
              <BrainCircuit className="w-4 h-4 text-indigo-600" />
              <h3 className="text-sm font-bold text-indigo-900">Learned Policies</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {policies.slice(-5).map((policy, idx) => (
                <span key={idx} className="px-2 py-1 bg-white text-indigo-700 text-xs rounded-md border border-indigo-200">
                  {policy.action}: {policy.learned_rule?.substring(0, 30) || 'No rule'}...
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <NetworkTopology nodes={topologyNodes} activeAnomalies={activeAnomalies} />
            
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5">
              <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-4">Network Control Panel</h3>
              <div className="grid grid-cols-2 gap-4">
                <button onClick={() => handleInject("congestion")} className="flex items-center justify-center gap-2 px-4 py-3 bg-amber-50 text-amber-700 rounded-xl border border-amber-200 hover:bg-amber-100 transition-colors font-medium text-sm">
                  <Zap className="w-4 h-4" /> Inject Congestion
                </button>
                <button onClick={() => handleInject("failure")} className="flex items-center justify-center gap-2 px-4 py-3 bg-rose-50 text-rose-700 rounded-xl border border-rose-200 hover:bg-rose-100 transition-colors font-medium text-sm">
                  <AlertCircle className="w-4 h-4" /> Simulate Link Failure
                </button>
              </div>
            </div>
            
            {/* Charts with city-named links */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <TelemetryVisualizer 
                data={coreLinks.length > 0 ? coreLinks : history.filter(h => h.link && h.link.includes('Core'))} 
                title="Core Link Latency (ms)" 
                dataKey="latency" 
                color="#6366f1" 
              />
              <TelemetryVisualizer 
                data={coreLinks.length > 0 ? coreLinks : history.filter(h => h.link && h.link.includes('Core'))} 
                title="Core Link Utilization (%)" 
                dataKey="utilization" 
                color="#10b981" 
              />
            </div>



            {/* Dynamic Node Dashboard - shows currently analyzed device */}
            {currentDevice && (
              <NodeDashboard 
                node={currentDevice} 
                metrics={metrics} 
              />
            )}

            <PredictiveAnalytics telemetryData={history} />
          </div>

<div className="lg:col-span-1 space-y-8">
            <LearnedPolicies policies={policies} />
            <div className="min-h-[200px]">
              <ActionApprovalQueue 
                actions={pendingActions} 
                onApprove={handleApprove} 
                onReject={handleReject} 
              />
            </div>
            <CentralControllerDashboard logs={logs} />
          </div>
        </div>
      </main>
    </div>
  );
};

const StatCard = ({ icon, label, value, trend }) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-black/5 flex items-center gap-4">
    <div className="p-3 bg-slate-50 rounded-xl">{icon}</div>
    <div>
      <p className="text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${trend === "high" ? "text-rose-600" : "text-slate-900"}`}>{value}</p>
    </div>
  </div>
);

export default App;

