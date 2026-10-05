import React, { useState } from 'react';
import initialRunsData from '../data/runs.json';
import { TelemetryDatabase, BenchmarkRun } from './types';
import { GanttChart } from './components/GanttChart';
import { RingTopology } from './components/RingTopology';

export const App: React.FC = () => {
  const [db] = useState<TelemetryDatabase>(initialRunsData as unknown as TelemetryDatabase);
  const [selectedRoundIndex, setSelectedRoundIndex] = useState(0);

  const activeRun: BenchmarkRun | null = db.runs && db.runs.length > 0 ? db.runs[selectedRoundIndex] : null;
  const isLoopCompleted = activeRun?.status === 'COMPLETED';
  const jitterMs = activeRun?.initiator?.cron_jitter_ms || 0;
  const totalMs = activeRun?.summary?.total_roundtrip_ms;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Navigation & Header */}
        <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-3xl">🔄</span>
              <h1 className="text-2xl font-bold tracking-tight text-white">Roundtrip Benchmark</h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
                v0.1.0
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Decentralized multi-account GitHub Actions execution latency & relay benchmark.
            </p>
          </div>

          <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 p-2 rounded-xl text-xs font-mono">
            <span className="text-slate-400">Current Station:</span>
            <span className="px-2 py-1 rounded bg-slate-800 text-blue-400 font-semibold">
              {db.station_id || 'kreier-station-0'}
            </span>
          </div>
        </header>

        {/* Top Summary Cards */}
        {activeRun ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Active Round</div>
              <div className="text-xl font-bold font-mono text-slate-100 mt-2 truncate">
                {activeRun.round_id}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Started {activeRun.initiator?.scheduled_time_utc?.slice(0, 10) || 'N/A'}
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Loop Status</div>
              <div className="flex items-center gap-2 mt-2">
                <span
                  className={`w-3 h-3 rounded-full ${
                    isLoopCompleted ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                  }`}
                />
                <span className="text-xl font-bold font-mono text-slate-100">
                  {activeRun.status}
                </span>
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {activeRun.summary?.stations_count || activeRun.stations.length} stations traversed
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Cron Jitter (03:14 UTC)</div>
              <div className="text-xl font-bold font-mono text-amber-400 mt-2">
                {jitterMs ? `+${(jitterMs / 1000).toFixed(2)}s` : '0.00s'}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {jitterMs.toLocaleString()} ms runner startup delay
              </div>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Total Roundtrip</div>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-2">
                {totalMs ? `${(totalMs / 1000).toFixed(1)}s` : 'In Progress...'}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {totalMs ? `${totalMs.toLocaleString()} ms cycle latency` : 'Awaiting return signal'}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400 bg-slate-900 rounded-xl border border-slate-800">
            No rounds recorded yet. The first round will initiate on the scheduled date at 03:14 AM UTC.
          </div>
        )}

        {/* Visualizers: Gantt Chart and Ring Topology */}
        {activeRun && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <GanttChart stations={activeRun.stations} cronJitterMs={jitterMs} />
            </div>
            <div>
              <RingTopology
                stations={activeRun.stations}
                currentStationId={db.station_id}
                isLoopCompleted={isLoopCompleted}
              />
            </div>
          </div>
        )}

        {/* Historical Rounds Selector */}
        {db.runs && db.runs.length > 1 && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h3 className="text-md font-semibold text-slate-200 mb-4">Historical Benchmark Runs</h3>
            <div className="flex flex-wrap gap-2">
              {db.runs.map((r, i) => (
                <button
                  key={r.round_id}
                  onClick={() => setSelectedRoundIndex(i)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                    i === selectedRoundIndex
                      ? 'bg-blue-600 text-white font-bold'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {r.round_id} ({r.status})
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <div>
            Built with Vite, React & TypeScript • Powered by GitHub Actions & GitHub App
          </div>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/kreier/roundtrip"
              target="_blank"
              rel="noreferrer"
              className="text-blue-400 hover:underline"
            >
              GitHub Repository
            </a>
            <span>•</span>
            <a
              href="https://github.com/kreier/roundtrip/blob/main/docs/ARCHITECTURE.md"
              target="_blank"
              rel="noreferrer"
              className="text-blue-400 hover:underline"
            >
              Architecture Docs
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;
