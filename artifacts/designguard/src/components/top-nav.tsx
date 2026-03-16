import { Link, useLocation } from "wouter";
import { useScan } from "@/context/scan-context";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  PlusCircle, 
  BarChart3, 
  PlayCircle, 
  History, 
  Layout,
  Settings
} from "lucide-react";

const NAV_LINKS = [
  { href: "/",             label: "New Scan", id: "scan",      icon: PlusCircle },
  { href: "/results",      label: "Results", id: "results",   icon: BarChart3 },
  { href: "/fix-executor", label: "Executor", id: "executor", icon: PlayCircle },
  { href: "/history",      label: "History", id: "history",   icon: History },
];

export function TopNav() {
  const [location] = useLocation();
  const { currentScan } = useScan();
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const scoreColor = !currentScan ? "" :
    currentScan.qualityScore >= 80 ? "bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.4)]" :
    currentScan.qualityScore >= 60 ? "bg-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.4)]" :
    "bg-rose-500 shadow-[0_0_15px_rgba(244,63,94,0.4)]";

  return (
    <div className="fixed left-6 top-1/2 -translate-y-1/2 z-50 pointer-events-none">
      <motion.nav 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 25 }}
        className="relative pointer-events-auto flex flex-col items-center py-8 gap-8 bg-[#131314]/80 backdrop-blur-3xl border border-white/10 shadow-[20px_0_50px_rgba(0,0,0,0.5)] rounded-[3rem] w-20"
      >
        {/* Top Logo */}
        <div className="relative group cursor-pointer mb-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg group-hover:shadow-indigo-500/20 transition-all duration-500 group-hover:rotate-12">
            <Layout className="w-6 h-6 text-white" />
          </div>
          {/* Tooltip */}
          <div className="absolute left-16 top-1/2 -translate-y-1/2 px-3 py-1.5 rounded-lg bg-white text-black text-[10px] font-black uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none shadow-xl">
            QA Testing Tool
          </div>
        </div>

        {/* Navigation Section */}
        <div 
          className="flex flex-col gap-4"
          onMouseLeave={() => setHoveredId(null)}
        >
          {NAV_LINKS.map((link) => {
            const isActive = location === link.href;
            const isHovered = hoveredId === link.id;

            return (
              <Link key={link.id} href={link.href}>
                <motion.div 
                  className="relative group p-3 cursor-pointer"
                  onMouseEnter={() => setHoveredId(link.id)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <link.icon 
                    className={`w-6 h-6 transition-colors duration-300 relative z-10 ${
                      isActive ? "text-white" : "text-white/30 group-hover:text-white/70"
                    }`} 
                  />

                  {/* Hover/Active Pill Background */}
                  {(isActive || isHovered) && (
                    <motion.div 
                      layoutId="sidebar-pill"
                      className={`absolute inset-0 rounded-2xl ${
                        isActive ? "bg-white/10" : "bg-white/5"
                      }`}
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}

                  {/* Active Sidebar Indicator */}
                  {isActive && (
                    <motion.div 
                      layoutId="sidebar-indicator"
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-indigo-500 rounded-r-full shadow-[4px_0_12px_rgba(99,102,241,0.6)]"
                    />
                  )}

                  {/* Floating Link Label Tooltip */}
                  <div className={`absolute left-16 top-1/2 -translate-y-1/2 p-2 px-3 rounded-lg bg-[#1A1A1C] border border-white/10 text-white text-[11px] font-bold uppercase tracking-widest transition-all duration-300 pointer-events-none shadow-2xl ${
                    isHovered ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-4"
                  }`}>
                    {link.label}
                  </div>
                </motion.div>
              </Link>
            );
          })}
        </div>

        {/* Bottom Section - Score & Settings */}
        <div className="mt-auto flex flex-col gap-6 items-center">
          {/* Quality Score Dot */}
          <AnimatePresence>
            {currentScan && (
              <motion.div 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                exit={{ scale: 0 }}
                className="relative group cursor-pointer"
              >
                <div className={`w-3 h-3 rounded-full ${scoreColor} animate-pulse`} />
                <div className="absolute left-12 top-1/2 -translate-y-1/2 px-3 py-2 rounded-xl bg-black/90 border border-white/10 backdrop-blur-xl opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap shadow-2xl">
                  <div className="text-[10px] font-black text-white/40 uppercase tracking-tighter leading-none mb-1">Health Score</div>
                  <div className="text-xl font-black text-white leading-none">{currentScan.qualityScore}</div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="p-3 cursor-pointer group hover:rotate-90 transition-transform duration-500 text-white/20 hover:text-white/60">
            <Settings className="w-6 h-6" />
          </div>
        </div>

      </motion.nav>
    </div>
  );
}
