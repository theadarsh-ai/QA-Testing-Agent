import { useState, useRef, useEffect } from "react";
import { useLocation } from "wouter";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight, Shield, Mic, MicOff, Upload,
  Figma, Globe, Zap, Eye, CheckCircle2, Link as LinkIcon,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { useScan } from "@/context/scan-context";
import { startScan } from "@/lib/api";

const STEPS = [
  { id: "observe", label: "Observe", icon: Eye, desc: "Initialising agent" },
  { id: "navigate", label: "Navigate", icon: Globe, desc: "Browsing all pages" },
  { id: "detect", label: "Detect", icon: Shield, desc: "AI visual analysis" },
  { id: "fix", label: "Fix", icon: Zap, desc: "Generating fixes" },
  { id: "verify", label: "Verify", icon: CheckCircle2, desc: "Calculating scores" },
  { id: "report", label: "Report", icon: ArrowRight, desc: "Compiling report" },
];

const GOOGLE_COLORS = ["#4285F4", "#EA4335", "#FBBC04", "#34A853", "#4285F4", "#EA4335"];

export default function ScanPage() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const { setCurrentScan } = useScan();
  const figmaRef = useRef<HTMLInputElement>(null);

  const [url, setUrl] = useState("");
  const [figmaFile, setFigmaFile] = useState<File | null>(null);
  const [figmaB64, setFigmaB64] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const [stepIndex, setStepIndex] = useState(-1);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (!isPending) return;
    let i = 0;
    const tick = () => {
      setStepIndex(i);
      i++;
      if (i < STEPS.length) setTimeout(tick, 4000);
    };
    tick();
  }, [isPending]);

  const handleFigma = (file: File) => {
    setFigmaFile(file);
    const reader = new FileReader();
    reader.onload = () => setFigmaB64((reader.result as string).split(",")[1]);
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      toast({ variant: "destructive", title: "URL required", description: "Enter a website URL to scan." });
      return;
    }
    setIsPending(true);
    setStepIndex(0);
    try {
      const data = await startScan(url.trim(), figmaB64 || undefined);
      setCurrentScan(data);
      toast({ title: "Scan complete", description: `Found ${data.allBugs.length} issues across ${data.pagesVisited.length} pages.` });
      setLocation("/results");
    } catch (err: any) {
      toast({ variant: "destructive", title: "Scan failed", description: err.message || "Something went wrong." });
    } finally {
      setIsPending(false);
      setStepIndex(-1);
    }
  };

  const toggleVoice = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      toast({ variant: "destructive", title: "Not supported", description: "Voice input requires Chrome or Edge." });
      return;
    }
    if (listening) { recognitionRef.current?.stop(); setListening(false); return; }
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = "en-US";
    rec.onresult = (e: any) => {
      const t = e.results[0][0].transcript.toLowerCase();
      const m = t.match(/(?:scan|check|test|go to|open|analyze)\s+(https?:\/\/\S+|\S+\.\S+)/i);
      if (m) {
        let u = m[1]; if (!u.startsWith("http")) u = "https://" + u;
        setUrl(u);
        toast({ title: "Voice captured", description: `URL set to: ${u}` });
      } else {
        toast({ title: "Voice received", description: `"${t}" — try "scan example.com"` });
      }
      setListening(false);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    rec.start();
    recognitionRef.current = rec;
    setListening(true);
  };

  const currentStep = STEPS[stepIndex];

  return (
    <>
      {/* ════════════════════════════════════════
          SLEEK DARK SCAN LOADING OVERLAY
      ════════════════════════════════════════ */}
      <AnimatePresence>
        {isPending && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-[100] flex items-center justify-center"
            style={{ background: "rgba(9,10,11,0.92)", backdropFilter: "blur(24px)" }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.97, opacity: 0, y: -10 }}
              transition={{ duration: 0.38, ease: [0.16, 1, 0.3, 1] }}
              className="w-full max-w-lg mx-4"
              style={{
                background: "rgba(18,18,20,0.95)",
                border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: "20px",
                boxShadow: "0 32px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04) inset",
                overflow: "hidden",
              }}
            >
              {/* Top terminal bar */}
              <div className="flex items-center gap-2 px-5 py-3.5 border-b border-white/[0.05]">
                <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
                <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
                <div className="w-2.5 h-2.5 rounded-full bg-white/10" />
                <span className="ml-2 text-[11px] font-mono text-white/25 tracking-widest">qa testing tool — agent</span>
              </div>

              <div className="px-8 py-10 flex flex-col items-center gap-8">
                {/* Central orb with single clean spinner */}
                <div className="relative w-20 h-20 flex items-center justify-center">
                  {/* Outer glow ring */}
                  <div className="absolute inset-0 rounded-full"
                    style={{ background: "radial-gradient(circle, rgba(138,180,248,0.08) 0%, transparent 70%)" }}
                  />
                  {/* Single clean spinner arc */}
                  <svg className="absolute inset-0 w-full h-full animate-spin" style={{ animationDuration: "1.4s" }} viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1.5" />
                    <circle cx="40" cy="40" r="36" fill="none" stroke="#8ab4f8" strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeDasharray="40 186"
                      strokeDashoffset="0"
                    />
                  </svg>
                  {/* Counter-rotation */}
                  <svg className="absolute inset-3 w-[56px] h-[56px] animate-spin" style={{ animationDuration: "2s", animationDirection: "reverse" }} viewBox="0 0 56 56">
                    <circle cx="28" cy="28" r="24" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
                    <circle cx="28" cy="28" r="24" fill="none" stroke="rgba(138,180,248,0.3)" strokeWidth="1"
                      strokeLinecap="round"
                      strokeDasharray="15 136"
                    />
                  </svg>
                  {/* Icon */}
                  <Shield className="w-6 h-6 relative z-10" style={{ color: "#8ab4f8" }} />
                </div>

                {/* Step label — single color, no rainbow */}
                <div className="text-center space-y-1.5">
                  <motion.h2
                    key={currentStep?.label}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="font-medium text-xl text-white tracking-tight"
                  >
                    {currentStep?.label || "Processing"}
                  </motion.h2>
                  <motion.p
                    key={currentStep?.desc}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4, delay: 0.1 }}
                    className="text-sm font-mono"
                    style={{ color: "rgba(255,255,255,0.3)" }}
                  >
                    → {currentStep?.desc}
                  </motion.p>
                </div>

                {/* Step row — monochrome */}
                <div className="w-full flex items-center justify-between">
                  {STEPS.map((step, i) => {
                    const Icon = step.icon;
                    const isDone = i < stepIndex;
                    const isCurrent = i === stepIndex;
                    return (
                      <div key={step.id} className="flex flex-col items-center gap-2">
                        <div
                          className="w-7 h-7 rounded-full flex items-center justify-center transition-all duration-500"
                          style={{
                            background: isCurrent
                              ? "rgba(138,180,248,0.15)"
                              : isDone
                                ? "rgba(255,255,255,0.06)"
                                : "rgba(255,255,255,0.03)",
                            border: isCurrent
                              ? "1px solid rgba(138,180,248,0.5)"
                              : isDone
                                ? "1px solid rgba(255,255,255,0.12)"
                                : "1px solid rgba(255,255,255,0.05)",
                            boxShadow: isCurrent ? "0 0 12px rgba(138,180,248,0.2)" : "none",
                          }}
                        >
                          <Icon
                            className="w-3.5 h-3.5 transition-colors duration-500"
                            style={{
                              color: isCurrent
                                ? "#8ab4f8"
                                : isDone
                                  ? "rgba(255,255,255,0.5)"
                                  : "rgba(255,255,255,0.15)",
                            }}
                          />
                        </div>
                        <span
                          className="text-[10px] font-mono transition-colors duration-300"
                          style={{
                            color: isCurrent
                              ? "#8ab4f8"
                              : isDone
                                ? "rgba(255,255,255,0.4)"
                                : "rgba(255,255,255,0.15)",
                          }}
                        >
                          {step.label}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Slim clean progress bar */}
                <div className="w-full h-px rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: "rgba(138,180,248,0.7)" }}
                    initial={{ width: "0%" }}
                    animate={{ width: `${((stepIndex + 1) / STEPS.length) * 100}%` }}
                    transition={{ duration: 0.8, ease: "easeInOut" }}
                  />
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>


      {/* ════════════════════════════════════════
          HERO
      ════════════════════════════════════════ */}
      <section className="min-h-[calc(100vh-4.5rem)] flex flex-col relative overflow-hidden">
        <div className="relative z-10 flex-1 flex items-center justify-center px-6 lg:px-12 py-12 w-full">
          <div className="w-full max-w-2xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="flex flex-col gap-7"
            >
              {/* Badge — Google blue */}
              <div>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium tracking-wider uppercase"
                  style={{ border: "1px solid rgba(138,180,248,0.3)", background: "rgba(138,180,248,0.08)", color: "#8ab4f8" }}>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#8ab4f8] animate-pulse" />
                  Autonomous QA Agent
                </span>
              </div>

              {/* Headline — Google Gemini style */}
              <div>
                <h1 className="font-medium text-[clamp(2.4rem,5.5vw,4.2rem)] leading-[1.06] text-white">
                  Find every bug.
                </h1>
                <h1 className="font-medium text-[clamp(2.4rem,5.5vw,4.2rem)] leading-[1.06] text-gradient">
                  Before your users do.
                </h1>
                <p className="text-white/40 text-base mt-4 leading-relaxed max-w-md font-light">
                  One URL. AI navigates your entire app, catches every visual issue & backend failure using Gemini vision, and generates fixes automatically.

                </p>
              </div>

              {/* Stats */}
              <div className="flex gap-6 flex-wrap">
                {[
                  { v: "60s", l: "Full scan", c: "#8ab4f8" },
                  { v: "17+", l: "Bug types", c: "#f28b82" },
                  { v: "4", l: "Pages", c: "#81c995" },
                ].map((s) => (
                  <div key={s.v} className="flex items-baseline gap-1.5">
                    <span className="font-medium text-xl" style={{ color: s.c }}>{s.v}</span>
                    <span className="text-xs text-white/30 font-normal">{s.l}</span>
                  </div>
                ))}
              </div>

              {/* ── Form card — Google rainbow border ── */}
              <div className="google-card">
                <form onSubmit={handleSubmit} className="p-6 space-y-4">

                  {/* URL input */}
                  <div className="space-y-1.5">
                    <label className="flex items-center gap-1.5 text-[10px] font-medium text-white/40 uppercase tracking-widest">
                      <LinkIcon className="w-3 h-3" style={{ color: "#8ab4f8" }} /> Website URL
                    </label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="https://your-app.com"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        className="h-11 border-white/10 focus-visible:ring-[#4285F4]/30 focus-visible:border-[#4285F4]/50 text-sm px-4 rounded-xl flex-1 placeholder:text-white/20 font-normal text-white"
                        style={{ background: "rgba(255,255,255,0.05)" }}
                        disabled={isPending}
                      />
                      <button
                        type="button"
                        onClick={toggleVoice}
                        className={`h-11 w-11 rounded-xl shrink-0 border flex items-center justify-center transition-all ${listening
                          ? "border-[#f28b82]/50 bg-[#f28b82]/10 text-[#f28b82]"
                          : "border-white/10 bg-white/5 text-white/35 hover:border-[#8ab4f8]/40 hover:text-[#8ab4f8]"
                          }`}
                      >
                        {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                      </button>
                    </div>
                    {listening && <p className="text-xs animate-pulse" style={{ color: "#f28b82" }}>Listening… say "scan example.com"</p>}
                  </div>

                  {/* Figma upload */}
                  <div className="space-y-1.5">
                    <label className="flex items-center gap-1.5 text-[10px] font-medium text-white/40 uppercase tracking-widest">
                      <Figma className="w-3 h-3" style={{ color: "#8ab4f8" }} /> Design File
                      <span className="normal-case text-[10px] font-normal text-white/25 tracking-normal">optional</span>
                    </label>
                    <div
                      className={`border-2 border-dashed rounded-xl h-14 flex items-center justify-center gap-2.5 cursor-pointer transition-all ${figmaFile
                        ? "border-[#34A853]/40 bg-[#34A853]/5 text-[#81c995]"
                        : "border-white/10 hover:border-[#8ab4f8]/30 hover:bg-[#8ab4f8]/5 text-white/30"
                        }`}
                      onClick={() => figmaRef.current?.click()}
                    >
                      <input type="file" ref={figmaRef} className="hidden" accept="image/png,image/jpeg,image/webp"
                        onChange={(e) => e.target.files?.[0] && handleFigma(e.target.files[0])} />
                      {figmaFile ? (
                        <><CheckCircle2 className="w-3.5 h-3.5 shrink-0" /><span className="text-sm font-medium truncate">{figmaFile.name}</span></>
                      ) : (
                        <><Upload className="w-3.5 h-3.5" /><span className="text-sm font-light">Upload Figma export for pixel comparison</span></>
                      )}
                    </div>
                  </div>

                  {/* Feature chips — Google colored dots */}
                  <div className="flex gap-2">
                    {[
                      { l: "Playwright", c: "#4285F4" },
                      { l: "Gemini 2.5 Pro", c: "#EA4335" },
                      { l: "PDF Report", c: "#34A853" },
                    ].map(({ l, c }) => (
                      <div key={l} className="flex-1 text-center rounded-lg py-1.5 flex items-center justify-center gap-1.5"
                        style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
                        <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: c }} />
                        <span className="text-[10px] font-medium text-white/50">{l}</span>
                      </div>
                    ))}
                  </div>

                  {/* CTA — Google blue pill */}
                  <button
                    type="submit"
                    disabled={isPending || !url.trim()}
                    className="w-full h-11 rounded-full font-medium text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:-translate-y-0.5 active:translate-y-0"
                    style={{
                      background: isPending ? "rgba(138,180,248,0.6)" : "#8ab4f8",
                      color: "#131314",
                      boxShadow: "0 1px 8px rgba(138,180,248,0.35)",
                    }}
                  >
                    {isPending ? (
                      <><span className="w-3.5 h-3.5 rounded-full border-2 border-[#131314]/30 border-t-[#131314] animate-spin" /> Agent running…</>
                    ) : (
                      <>Run Autonomous QA Scan <ArrowRight className="w-4 h-4" /></>
                    )}
                  </button>
                </form>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════
          FEATURE STRIP — dark, Google colors
      ════════════════════════════════════════ */}
      <section className="border-t border-white/5 px-6 lg:px-12 py-12" style={{ background: "rgba(255,255,255,0.02)" }}>
        <div className="max-w-screen-xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { icon: Globe, title: "Playwright Crawler", desc: "Autonomously navigates up to 4 pages, capturing screenshots on desktop and mobile.", color: "#4285F4" },
            { icon: Shield, title: "Gemini 2.5 Pro", desc: "17 bug categories: layout, colour contrast, API errors, auth failures, CORS, JS exceptions.", color: "#EA4335" },
            { icon: Zap, title: "Instant PDF Report", desc: "Every bug ships with a DevTools fix command, CSS fix, and severity rating — ready to share.", color: "#34A853" },
          ].map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="flex gap-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg shrink-0"
                style={{ background: `${color}22`, border: `1px solid ${color}44` }}>
                <Icon className="w-4 h-4" style={{ color }} />
              </div>
              <div>
                <h3 className="font-medium text-sm text-white/80 mb-1">{title}</h3>
                <p className="text-sm text-white/35 leading-relaxed font-light">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
