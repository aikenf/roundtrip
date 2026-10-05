import React from 'react';
import { StationStep } from '../types';

interface RingTopologyProps {
  stations: StationStep[];
  currentStationId?: string;
  isLoopCompleted?: boolean;
}

export const RingTopology: React.FC<RingTopologyProps> = ({
  stations,
  currentStationId,
  isLoopCompleted = false,
}) => {
  // Extract unique stations to represent the physical ring topology
  const uniqueStations = React.useMemo(() => {
    const seen = new Set<string>();
    const list: StationStep[] = [];
    for (const st of stations) {
      const key = st.station_id || st.repo;
      if (!seen.has(key)) {
        seen.add(key);
        list.push(st);
      }
    }
    return list.length > 0 ? list : stations;
  }, [stations]);

  const count = Math.max(uniqueStations.length, 2);
  const radius = 110;
  const center = 150;
  const totalHops = stations.length;
  const lastActiveHop = stations[stations.length - 1];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col items-center">
      <div className="w-full flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <span>🔄</span> Ring Topology
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {uniqueStations.length} participating stations • {totalHops} hops recorded
          </p>
        </div>
        <span
          className={`text-xs px-2.5 py-1 rounded-full font-medium ${
            isLoopCompleted
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
          }`}
        >
          {isLoopCompleted ? 'Loop Closed' : 'Relay Active'}
        </span>
      </div>

      <div className="relative w-[300px] h-[300px]">
        <svg className="w-full h-full" viewBox="0 0 300 300">
          <defs>
            <marker
              id="arrowhead"
              markerWidth="6"
              markerHeight="6"
              refX="16"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 6 3, 0 6" fill="#3b82f6" />
            </marker>
          </defs>

          {/* Ring Guide Path */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#1e293b"
            strokeWidth="3"
            strokeDasharray="4 4"
          />

          {/* Directed Hop Connections between unique stations */}
          {uniqueStations.map((_, i) => {
            const angle1 = (i / count) * 2 * Math.PI - Math.PI / 2;
            const angle2 = (((i + 1) % count) / count) * 2 * Math.PI - Math.PI / 2;

            const x1 = center + radius * Math.cos(angle1);
            const y1 = center + radius * Math.sin(angle1);
            const x2 = center + radius * Math.cos(angle2);
            const y2 = center + radius * Math.sin(angle2);

            return (
              <line
                key={`line-${i}`}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="#3b82f6"
                strokeWidth="2"
                strokeOpacity="0.7"
                markerEnd="url(#arrowhead)"
              />
            );
          })}

          {/* Unique Station Nodes */}
          {uniqueStations.map((st, i) => {
            const angle = (i / count) * 2 * Math.PI - Math.PI / 2;
            const x = center + radius * Math.cos(angle);
            const y = center + radius * Math.sin(angle);
            const isCurrent = st.station_id === currentStationId;
            const isLastHop = lastActiveHop?.station_id === st.station_id;

            return (
              <g key={st.station_id ? `${st.station_id}-${i}` : i}>
                <circle
                  cx={x}
                  cy={y}
                  r={isCurrent ? 22 : 18}
                  fill={isCurrent ? '#2563eb' : isLastHop ? '#1e293b' : '#0f172a'}
                  stroke={isCurrent ? '#60a5fa' : isLastHop ? '#38bdf8' : '#334155'}
                  strokeWidth={isCurrent || isLastHop ? '3' : '2'}
                  className="transition-all duration-300"
                />
                <text
                  x={x}
                  y={y + 4}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="11"
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  S{i}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Unique Station Legend List */}
      <div className="w-full mt-4 flex flex-col gap-2 text-xs font-mono">
        {uniqueStations.map((st, i) => {
          const isCurrent = st.station_id === currentStationId;
          const isLastHop = lastActiveHop?.station_id === st.station_id;

          return (
            <div
              key={st.station_id ? `${st.station_id}-${i}` : i}
              className={`p-2.5 rounded-lg border flex items-center justify-between ${
                isCurrent
                  ? 'bg-blue-950/50 border-blue-500/60 text-blue-200'
                  : 'bg-slate-950/40 border-slate-800 text-slate-400'
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <span className="w-6 h-6 rounded bg-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-300 shrink-0">
                  S{i}
                </span>
                <span className="font-semibold text-slate-200 truncate">{st.station_id}</span>
                {isCurrent && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-500/20 text-blue-300">
                    You
                  </span>
                )}
                {isLastHop && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-sky-500/20 text-sky-300">
                    Latest
                  </span>
                )}
              </div>
              <span className="text-[11px] text-slate-500 truncate ml-2">{st.repo}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
