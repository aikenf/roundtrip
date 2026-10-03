import React from 'react';

interface StationStep {
  sequence: number;
  station_id: string;
  repo: string;
}

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
  const count = Math.max(stations.length, 2);
  const radius = 110;
  const center = 150;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col items-center">
      <div className="w-full flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <span>🔄</span> Ring Topology
        </h3>
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

          {/* Directed Hop Arrows */}
          {stations.map((_, i) => {
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
                strokeOpacity="0.6"
              />
            );
          })}

          {/* Node circles */}
          {stations.map((st, i) => {
            const angle = (i / count) * 2 * Math.PI - Math.PI / 2;
            const x = center + radius * Math.cos(angle);
            const y = center + radius * Math.sin(angle);
            const isCurrent = st.station_id === currentStationId;

            return (
              <g key={st.station_id || i}>
                <circle
                  cx={x}
                  cy={y}
                  r={isCurrent ? 20 : 16}
                  fill={isCurrent ? '#3b82f6' : '#0f172a'}
                  stroke={isCurrent ? '#93c5fd' : '#38bdf8'}
                  strokeWidth={isCurrent ? '3' : '2'}
                  className="transition-all duration-300"
                />
                <text
                  x={x}
                  y={y + 4}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize="10"
                  fontWeight="bold"
                  fontFamily="monospace"
                >
                  #{st.sequence}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="w-full mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
        {stations.map((st) => (
          <div
            key={st.station_id}
            className={`p-2 rounded border flex items-center justify-between ${
              st.station_id === currentStationId
                ? 'bg-blue-950/40 border-blue-500/50 text-blue-200'
                : 'bg-slate-950/40 border-slate-800 text-slate-400'
            }`}
          >
            <span className="font-semibold truncate">#{st.sequence} {st.station_id}</span>
            <span className="text-[10px] text-slate-500 truncate ml-2">{st.repo}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
