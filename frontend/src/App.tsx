import { useMemo } from "react";
import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";

import { ScanProvider } from "@/context/scan-context";
import { TopNav } from "@/components/top-nav";

import ScanPage from "@/pages/scan";
import ResultsPage from "@/pages/results";
import FixExecutorPage from "@/pages/fix-executor";
import HistoryPage from "@/pages/history";
import NotFound from "@/pages/not-found";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

function AnimatedBackground() {
  const particles = useMemo(
    () =>
      Array.from({ length: 22 }, (_, i) => ({
        id: i,
        left: `${(i * 4.7) % 100}%`,
        bottom: `${(i * 3.9) % 40}%`,
        duration: 5 + (i % 7),
        delay: (i * 0.6) % 8,
        size: 2 + (i % 2),
      })),
    [],
  );

  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />
      <div className="orb-4" />
      <div className="dot-grid" />
      <div className="scan-sweep" />
      {particles.map((p) => (
        <div
          key={p.id}
          className="particle"
          style={{
            left: p.left,
            bottom: p.bottom,
            width: p.size,
            height: p.size,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/"             component={ScanPage} />
      <Route path="/results"      component={ResultsPage} />
      <Route path="/fix-executor" component={FixExecutorPage} />
      <Route path="/history"      component={HistoryPage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <ScanProvider>
            <div className="min-h-screen flex flex-col text-foreground selection:bg-primary/20" style={{ background: "#131314" }}>
              <AnimatedBackground />
              <TopNav />
              <main className="flex-1 relative z-10 pl-32">
                <Router />
              </main>
            </div>
          </ScanProvider>
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
