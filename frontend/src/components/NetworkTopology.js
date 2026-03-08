import React, { useState, useEffect } from 'react';
import { Server, Laptop, Router, Globe, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

const NetworkTopology = ({ nodes, activeAnomalies, networkStats }) => {
  const [packets, setPackets] = useState([]);
  
  // Use provided networkStats or fall back to defaults
  const stats = networkStats || { density: 65, routes: 12 };

  // Simulate packets moving between nodes
  useEffect(() => {
    const interval = setInterval(() => {
      if (nodes.length < 2) return;
      
      const sourceIdx = Math.floor(Math.random() * nodes.length);
      let destIdx = Math.floor(Math.random() * nodes.length);
      while (destIdx === sourceIdx) {
        destIdx = Math.floor(Math.random() * nodes.length);
      }

      const newPacket = {
        id: Date.now(),
        from: nodes[sourceIdx].id,
        to: nodes[destIdx].id,
        type: Math.random() > 0.8 ? 'critical' : 'normal'
      };

      setPackets(prev => [...prev.slice(-10), newPacket]);
    }, 2000);

    return () => clearInterval(interval);
  }, [nodes]);

  const getNodeIcon = (type) => {
    switch (type) {
      case 'gateway': return <Globe className="w-6 h-6" />;
      case 'server': return <Server className="w-6 h-6" />;
      case 'workstation': return <Laptop className="w-6 h-6" />;
      default: return <Router className="w-6 h-6" />;
    }
  };

  const getNodePosition = (index, total) => {
    const radius = 150;
    const centerX = 250;
    const centerY = 200;
    const angle = (index / total) * 2 * Math.PI;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  };

  return (
    <div className="bg-white rounded-2xl border border-black/5 p-6 shadow-sm overflow-hidden relative min-h-[450px]">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Network Topology</h3>
          <p className="text-sm text-slate-500 italic serif">Real-time packet flow simulation</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => {
              // Simulate re-optimization
              setPackets([]);
            }}
            className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-indigo-100 hover:bg-indigo-100 transition-colors"
          >
            Re-optimize
          </button>
          <div className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-emerald-500">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Active
          </div>
        </div>
      </div>

      <div className="relative w-full h-[350px] flex items-center justify-center">
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {/* Connections */}
          {nodes.map((node, i) => {
            const pos = getNodePosition(i, nodes.length);
            return nodes.slice(i + 1).map((target, j) => {
              const targetPos = getNodePosition(i + j + 1, nodes.length);
              return (
                <line
                  key={`${node.id}-${target.id}`}
                  x1={pos.x}
                  y1={pos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke="currentColor"
                  className="text-slate-100"
                  strokeWidth="1"
                />
              );
            });
          })}

          {/* Animated Packets */}
          <AnimatePresence>
            {packets.map(packet => {
              const fromNode = nodes.find(n => n.id === packet.from);
              const toNode = nodes.find(n => n.id === packet.to);
              if (!fromNode || !toNode) return null;

              const fromIdx = nodes.indexOf(fromNode);
              const toIdx = nodes.indexOf(toNode);
              const start = getNodePosition(fromIdx, nodes.length);
              const end = getNodePosition(toIdx, nodes.length);

              return (
                <motion.circle
                  key={packet.id}
                  initial={{ cx: start.x, cy: start.y, r: 0, opacity: 0 }}
                  animate={{ 
                    cx: end.x, 
                    cy: end.y, 
                    r: 3, 
                    opacity: [0, 1, 1, 0] 
                  }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 1.5, ease: "linear" }}
                  fill={packet.type === 'critical' ? '#ef4444' : '#10b981'}
                />
              );
            })}
          </AnimatePresence>
        </svg>

        {/* Nodes */}
        {nodes.map((node, i) => {
          const pos = getNodePosition(i, nodes.length);
          const hasAnomaly = activeAnomalies && activeAnomalies.some(a => 
            a.nodeId === node.id || 
            a.link?.includes(node.id) ||
            a.link?.includes(node.name)
          );
          
          return (
            <motion.div
              key={node.id}
              className="absolute"
              style={{ left: pos.x - 24, top: pos.y - 24 }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              whileHover={{ scale: 1.1 }}
            >
              <div className={`
                w-12 h-12 rounded-xl flex items-center justify-center shadow-lg
                ${hasAnomaly ? 'bg-red-500 text-white animate-bounce' : 'bg-white border border-slate-200 text-slate-600'}
                transition-colors duration-300
              `}>
                {getNodeIcon(node.type)}
              </div>
              <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-tighter">
                  {node.name}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Dynamic Stats */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="p-3 bg-slate-50 rounded-xl border border-black/5">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Traffic Density</div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-emerald-500"
                animate={{ width: `${stats.density}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <span className="text-xs font-mono font-bold">{stats.density}%</span>
          </div>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-black/5">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Active Routes</div>
          <div className="flex items-center gap-2 text-slate-900">
            <Zap className="w-3 h-3 text-amber-500" />
            <span className="text-xs font-mono font-bold">{stats.routes} Paths</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkTopology;

