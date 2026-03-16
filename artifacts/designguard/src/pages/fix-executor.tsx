import { useState } from "react";
import { useLocation } from "wouter";
import { motion } from "framer-motion";
import {
  Wrench, Copy, Check, ArrowLeft, Terminal, Globe,
  ChevronDown, ChevronUp, FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useScan } from "@/context/scan-context";
import { useToast } from "@/hooks/use-toast";
import { getReportUrl } from "@/lib/api";

const SEV_CLASSES: Record<string, string> = {
  critical: "bg-[#f28b82]/12 text-[#f28b82] border-[#f28b82]/25",
  serious:  "bg-[#fdd663]/10 text-[#fdd663] border-[#fdd663]/25",
  moderate: "bg-[#fdd663]/8 text-[#fdd663]/80 border-[#fdd663]/20",
  minor:    "bg-[#81c995]/10 text-[#81c995] border-[#81c995]/25",
};

export default function FixExecutorPage() {
  const [, setLocation] = useLocation();
  const { currentScan } = useScan();
  const { toast } = useToast();
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  if (!currentScan) {
    return (
      <div className="min-h-full flex items-center justify-center p-10 text-center">
        <div className="space-y-4">
          <div className="w-16 h-16 rounded-2xl border-2 border-dashed border-white/12 flex items-center justify-center mx-auto">
            <Wrench className="w-7 h-7 text-white/20" />
          </div>
          <h2 className="text-xl font-medium text-white/70">No active scan</h2>
          <p className="text-white/35 text-sm">Run a scan first to generate executable fixes.</p>
          <Button
            onClick={() => setLocation("/")}
            className="mt-2 text-[#131314] hover:opacity-90"
            style={{ background: "#8ab4f8" }}
          >
            <ArrowLeft className="w-4 h-4 mr-2" /> New Scan
          </Button>
        </div>
      </div>
    );
  }

  const fixes = currentScan.fixes || [];
  const copyFix = (id: string, cmd: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedId(id);
    toast({ title: "Copied!", description: "Paste in browser DevTools console (F12 → Console)" });
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="min-h-[calc(100vh-4.5rem)]">
      {/* Header */}
      <div className="page-glass-header px-6 lg:px-12 py-7">
        <div className="max-w-screen-xl mx-auto flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <span className="section-label block mb-2">DevTools</span>
            <h1 className="text-2xl font-medium text-white">Fix Executor</h1>
            <p className="text-white/35 text-sm mt-1 font-light">
              {fixes.length} executable fix{fixes.length !== 1 ? "es" : ""} — run directly in your browser console
            </p>
          </div>
          <div className="flex gap-2.5">
            <Button
              variant="outline"
              size="sm"
              className="border-white/30 text-white bg-white/8 hover:bg-white/15 hover:border-white/50"
              onClick={() => window.open(getReportUrl(currentScan.scanId), "_blank")}
            >
              <FileText className="w-4 h-4 mr-2" /> PDF Report
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="border-white/30 text-white bg-white/8 hover:bg-white/15 hover:border-white/50"
              onClick={() => setLocation("/results")}
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back to Report
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 lg:px-12 py-8 space-y-6">
        {/* Instructions */}
        <div className="rounded-xl border border-[#8ab4f8]/15 p-5 text-sm space-y-2" style={{ background: "rgba(138,180,248,0.06)" }}>
          <p className="font-medium text-white/80 flex items-center gap-2">
            <Terminal className="w-4 h-4" style={{ color: "#8ab4f8" }} /> How to apply fixes
          </p>
          <ol className="list-decimal list-inside space-y-1 text-white/40 ml-0.5">
            <li>Open the target website in Chrome or Edge</li>
            <li>Press <kbd className="px-1.5 py-0.5 rounded text-xs font-mono border border-white/15 bg-white/8 text-white/60">F12</kbd> to open DevTools</li>
            <li>Click the <b className="text-white/65">Console</b> tab</li>
            <li>Copy a fix command below and paste it, then press Enter</li>
          </ol>
          <p className="text-xs text-white/30 pt-1">
            Fixes are temporary (reset on page refresh) — verify before applying permanently to your source code.
          </p>
        </div>

        {fixes.length === 0 ? (
          <div className="text-center py-20 text-white/30">
            <Wrench className="w-10 h-10 mx-auto mb-3 opacity-30" />
            No executable fixes were generated for this scan.
          </div>
        ) : (
          <div className="space-y-3">
            {fixes.map((fix, idx) => {
              const key        = `${fix.bugId}-${idx}`;
              const isExpanded = expanded[key] ?? false;
              return (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="rounded-xl overflow-hidden border border-white/8 hover:border-white/15 transition-all"
                  style={{ background: "#1e1f20" }}
                >
                  <div className="p-5 space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge
                          variant="outline"
                          className={`${SEV_CLASSES[fix.severity?.toLowerCase()] ?? SEV_CLASSES.moderate} capitalize font-medium text-xs`}
                        >
                          {fix.severity}
                        </Badge>
                        <Badge variant="secondary" className="font-mono text-xs bg-white/8 text-white/60 border-white/10">
                          {fix.category}
                        </Badge>
                        {fix.label && (
                          <Badge variant="outline" className="text-xs flex items-center gap-1 border-white/12 text-white/40">
                            <Globe className="w-3 h-3" /> {fix.label}
                          </Badge>
                        )}
                      </div>
                      <button
                        onClick={() => setExpanded(prev => ({ ...prev, [key]: !isExpanded }))}
                        className="text-white/30 hover:text-white/60 transition-colors shrink-0 p-0.5"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>

                    <p className="text-sm text-white/75 leading-relaxed">{fix.description}</p>

                    {isExpanded && fix.element && (
                      <p className="text-xs text-white/40 font-mono px-3 py-2 rounded-lg border border-white/8" style={{ background: "rgba(255,255,255,0.03)" }}>
                        {fix.element}
                      </p>
                    )}

                    <div className="rounded-xl p-4 border border-[#34A853]/20" style={{ background: "rgba(52,168,83,0.07)" }}>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-medium flex items-center gap-1.5" style={{ color: "#81c995" }}>
                          <Terminal className="w-3.5 h-3.5" /> Console Command
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-xs gap-1.5 border-white/12 bg-white/5 hover:bg-white/10 text-white/60"
                          onClick={() => copyFix(key, fix.devtoolsCommand)}
                        >
                          {copiedId === key
                            ? <Check className="w-3 h-3" style={{ color: "#81c995" }} />
                            : <Copy className="w-3 h-3" />}
                          {copiedId === key ? "Copied!" : "Copy"}
                        </Button>
                      </div>
                      <code className="text-xs font-mono break-all leading-relaxed" style={{ color: "#81c995" }}>
                        {fix.devtoolsCommand}
                      </code>
                    </div>

                    {isExpanded && fix.cssFix && (
                      <div className="rounded-lg p-3 border border-[#8ab4f8]/20" style={{ background: "rgba(138,180,248,0.07)" }}>
                        <span className="text-xs font-medium" style={{ color: "#8ab4f8" }}>CSS: </span>
                        <code className="text-xs font-mono" style={{ color: "#8ab4f8" }}>{fix.cssFix}</code>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
