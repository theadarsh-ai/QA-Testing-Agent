import { useState, useEffect } from "react";
import { format } from "date-fns";
import {
  Target, Globe, AlertTriangle, TrendingUp,
  TrendingDown, Shield, Clock, Wifi,
} from "lucide-react";
import { getHistory, type HistoryScan } from "@/lib/api";

export default function HistoryPage() {
  const [scans, setScans] = useState<HistoryScan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getHistory()
      .then((d) => setScans(d.scans || []))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const scoreColor = (s: number) =>
    s >= 80 ? "#81c995" : s >= 60 ? "#fdd663" : "#f28b82";

  const scoreBg = (s: number) =>
    s >= 80
      ? { background: "rgba(129,201,149,0.08)", borderColor: "rgba(129,201,149,0.25)" }
      : s >= 60
      ? { background: "rgba(253,214,99,0.08)", borderColor: "rgba(253,214,99,0.25)" }
      : { background: "rgba(242,139,130,0.08)", borderColor: "rgba(242,139,130,0.25)" };

  return (
    <div className="min-h-[calc(100vh-4.5rem)]">
      {/* Page header */}
      <div className="page-glass-header px-6 lg:px-12 py-8">
        <div className="max-w-screen-xl mx-auto">
          <span className="section-label block mb-3">Regression Tracking</span>
          <h1 className="text-3xl font-medium text-white">Scan History</h1>
          <p className="text-white/35 mt-1.5 text-sm max-w-xl font-light">
            Every scan is saved. QA Testing Tool automatically highlights new bugs that appeared since the last scan.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-screen-xl mx-auto px-6 lg:px-12 py-8">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-28 rounded-xl animate-pulse border border-white/8" style={{ background: "#1e1f20" }} />
            ))}
          </div>
        ) : error || !scans.length ? (
          <div className="flex flex-col items-center justify-center py-28 text-center gap-5">
            <div className="w-16 h-16 rounded-2xl border-2 border-dashed border-white/12 flex items-center justify-center">
              <Shield className="w-7 h-7 text-white/20" />
            </div>
            <div>
              <h3 className="text-lg font-medium text-white/70">No scans yet</h3>
              <p className="text-sm text-white/35 mt-1">Run your first autonomous QA scan to see results here.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {scans.map((scan, idx) => {
              const prevScan  = scans[idx + 1];
              const scoreDiff = prevScan ? scan.qualityScore - prevScan.qualityScore : null;
              const isRegression = scoreDiff !== null && scoreDiff < 0;

              return (
                <div
                  key={scan.scanId}
                  className="rounded-xl overflow-hidden border border-white/8 hover:border-white/15 transition-all"
                  style={{ background: "#1e1f20" }}
                >
                  <div className="flex flex-col lg:flex-row">
                    {/* Main info */}
                    <div className="p-5 flex-1 border-b lg:border-b-0 lg:border-r border-white/8">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2 text-xs text-white/35">
                          <Clock className="w-3 h-3" />
                          {format(new Date(scan.createdAt), "MMM d, yyyy · h:mm a")}
                        </div>
                        <div className="flex gap-1.5 flex-wrap justify-end">
                          {scan.newBugsCount > 0 && (
                            <span className="pill border" style={{ background: "rgba(253,214,99,0.1)", color: "#fdd663", borderColor: "rgba(253,214,99,0.25)" }}>
                              +{scan.newBugsCount} new
                            </span>
                          )}
                          <span className="pill border" style={{ background: "rgba(138,180,248,0.1)", color: "#8ab4f8", borderColor: "rgba(138,180,248,0.25)" }}>
                            {scan.totalBugs} bugs
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 mb-3">
                        <Target className="w-3.5 h-3.5 text-white/30 shrink-0" />
                        <h3 className="text-sm font-medium text-white/75 truncate">{scan.url}</h3>
                      </div>

                      <div className="flex flex-wrap gap-4 text-xs text-white/35">
                        <span className="flex items-center gap-1.5">
                          <Globe className="w-3 h-3" />
                          {scan.pagesScanned} pages
                        </span>
                        <span className="flex items-center gap-1.5" style={{ color: "#f28b82" }}>
                          <AlertTriangle className="w-3 h-3" />
                          {scan.criticalCount} critical
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Wifi className="w-3 h-3" />
                          {scan.networkIssues} network issues
                        </span>
                        {scan.performanceMetrics?.initialLoadMs && (
                          <span className="flex items-center gap-1.5">
                            <Clock className="w-3 h-3" />
                            {scan.performanceMetrics.initialLoadMs}ms load
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Score panel */}
                    <div
                      className="p-5 flex items-center justify-center gap-8 lg:w-56 border"
                      style={{ ...scoreBg(scan.qualityScore) }}
                    >
                      <div className="text-center">
                        <p className="section-label mb-1.5">Quality Score</p>
                        <p className="text-4xl font-medium" style={{ color: scoreColor(scan.qualityScore) }}>
                          {scan.qualityScore}
                          <span className="text-sm font-normal text-white/30">/100</span>
                        </p>
                        {scoreDiff !== null && (
                          <div className={`flex items-center justify-center gap-1 text-xs mt-1.5 font-medium`}
                            style={{ color: isRegression ? "#f28b82" : "#81c995" }}>
                            {isRegression
                              ? <TrendingDown className="w-3 h-3" />
                              : <TrendingUp className="w-3 h-3" />}
                            {scoreDiff >= 0 ? "+" : ""}{scoreDiff} vs prev
                          </div>
                        )}
                      </div>
                      {scan.figmaMatchScore < 100 && (
                        <div className="text-center">
                          <p className="section-label mb-1.5">Design Match</p>
                          <p className="text-3xl font-medium" style={{ color: scoreColor(scan.figmaMatchScore) }}>
                            {scan.figmaMatchScore}%
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
