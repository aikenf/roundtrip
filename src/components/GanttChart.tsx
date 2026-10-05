import React from 'react';
import { StationStep } from '../types';

export type { StationStep };

interface GanttChartProps {
  stations: StationStep[];
  cronJitterMs?: number;
}

export const GanttChart: React.FC<GanttChartProps> = ({ stations, cronJitterMs = 0 }) => {
  if (!stations || stations.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400 bg-slate-900/50 rounded-xl border border-slate-800">
        No station telemetry data available for this cycle.
      </div>
    );
  }

  // Calculate global time boundaries
  const totalDuration = stations.reduce((acc, s) => {
    const queue = s.metrics?.queue_delay_ms || 0;
    const exec = s.metrics?.execution_ms || 30000;
    const dispatch = s.metrics?.dispatch_out_ms || 3000;
    return acc + queue + exec + dispatch;
  }, cronJitterMs);

  const safeTotal = Math.max(totalDuration, 10000);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <span>⏱️</span> Execution Phase Breakdown (Gantt)
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Visualizing runner queue wait, execution, Pages deployment, and relay dispatch latency.
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-amber-500"></span>
            <span className="text-slate-300">Jitter / Queue Delay</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-sky-500"></span>
            <span className="text-slate-300">Execution</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-emerald-500"></span>
            <span className="text-slate-300">Pages Deploy</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-purple-500"></span>
            <span className="text-slate-300">Dispatch Next</span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {stations.map((st, idx) => {
          const queue = st.metrics?.queue_delay_ms || (idx === 0 ? cronJitterMs : 2500);
          const exec = st.metrics?.execution_ms || 42000;
          const deployEst = Math.round(exec * 0.6); // Approximate deploy portion
          const runEst = Math.max(0, exec - deployEst);
          const dispatch = st.metrics?.dispatch_out_ms || 2800;

          const queuePct = Math.max(1, (queue / safeTotal) * 100);
          const runPct = Math.max(2, (runEst / safeTotal) * 100);
          const deployPct = Math.max(2, (deployEst / safeTotal) * 100);
          const dispatchPct = Math.max(1, (dispatch / safeTotal) * 100);

          return (
            <div key={st.station_id || idx} className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
              <div className="flex items-center justify-between text-xs font-mono mb-2">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-bold">
                    Hop #{st.sequence}
                  </span>
                  <span className="text-slate-100 font-semibold">{st.station_id}</span>
                  <span className="text-slate-500">({st.repo})</span>
                </div>
                <span className="text-slate-400">
                  Total: {Math.round((queue + exec + dispatch) / 1000)}s
                </span>
              </div>

              {/* Progress bar representing timeline */}
              <div className="h-6 w-full bg-slate-900 rounded overflow-hidden flex text-[10px] text-white font-mono select-none">
                {/* Queue / Jitter */}
                <div
                  style={{ width: `${queuePct}%` }}
                  className="bg-amber-500 hover:bg-amber-400 flex items-center justify-center transition-colors truncate px-1"
                  title={`Queue delay / Jitter: ${queue.toLocaleString()} ms`}
                >
                  {queue > 3000 ? `${(queue / 1000).toFixed(1)}s` : ''}
                </div>

                {/* Workflow Execution */}
                <div
                  style={{ width: `${runPct}%` }}
                  className="bg-sky-600 hover:bg-sky-500 flex items-center justify-center transition-colors truncate px-1"
                  title={`Execution: ${runEst.toLocaleString()} ms`}
                >
                  {runEst > 4000 ? `${(runEst / 1000).toFixed(1)}s` : ''}
                </div>

                {/* Pages Deploy */}
                <div
                  style={{ width: `${deployPct}%` }}
                  className="bg-emerald-600 hover:bg-emerald-500 flex items-center justify-center transition-colors truncate px-1"
                  title={`Pages Deploy: ${deployEst.toLocaleString()} ms`}
                >
                  {deployEst > 4000 ? `${(deployEst / 1000).toFixed(1)}s` : ''}
                </div>

                {/* Dispatch Out */}
                <div
                  style={{ width: `${dispatchPct}%` }}
                  className="bg-purple-600 hover:bg-purple-500 flex items-center justify-center transition-colors truncate px-1"
                  title={`App Dispatch: ${dispatch.toLocaleString()} ms`}
                >
                  {dispatch > 2000 ? `${(dispatch / 1000).toFixed(1)}s` : ''}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
