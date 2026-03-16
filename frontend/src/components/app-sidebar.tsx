import { Link, useLocation } from "wouter";
import {
  ScanLine,
  LayoutDashboard,
  Wrench,
  History,
  ShieldCheck,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { useScan } from "@/context/scan-context";

const navigation = [
  { name: "New Scan",     href: "/",              icon: ScanLine },
  { name: "Results",      href: "/results",        icon: LayoutDashboard },
  { name: "Fix Executor", href: "/fix-executor",   icon: Wrench },
  { name: "History",      href: "/history",        icon: History },
];

export function AppSidebar() {
  const [location] = useLocation();
  const { currentScan } = useScan();

  return (
    <Sidebar className="border-r border-border bg-sidebar">
      {/* Logo */}
      <SidebarHeader className="px-5 py-6 border-b border-border">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-primary shadow-sm">
            <ShieldCheck className="h-5 w-5 text-white" />
          </div>
          <div>
            <span className="font-display font-bold text-base leading-tight text-foreground tracking-tight">
              Design<span className="text-primary">Guard</span>
            </span>
            <p className="text-[10px] uppercase tracking-[0.12em] text-muted-foreground font-semibold mt-0.5">
              QA Agent
            </p>
          </div>
        </Link>
      </SidebarHeader>

      {/* Nav */}
      <SidebarContent className="px-3 py-5">
        <SidebarGroup>
          <SidebarGroupLabel className="section-label px-2 mb-3">
            Navigation
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-0.5">
              {navigation.map((item) => {
                const isActive = location === item.href;
                return (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      tooltip={item.name}
                      className={`h-10 rounded-lg px-3 text-sm transition-all duration-150 ${
                        isActive
                          ? "bg-primary text-white font-semibold shadow-sm"
                          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                      }`}
                    >
                      <Link href={item.href} className="flex items-center gap-3 w-full">
                        <item.icon className={`h-4 w-4 ${isActive ? "text-white" : "text-muted-foreground"}`} />
                        <span>{item.name}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Footer */}
      <SidebarFooter className="p-4 border-t border-border">
        {currentScan ? (
          <div className="rounded-lg bg-primary/5 border border-primary/15 p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-muted-foreground">Active Scan</span>
              <span className={`text-sm font-bold font-display ${
                currentScan.qualityScore >= 80 ? "text-green-600" :
                currentScan.qualityScore >= 60 ? "text-amber-500" : "text-red-500"
              }`}>
                {currentScan.qualityScore}/100
              </span>
            </div>
            <p className="text-xs text-muted-foreground truncate">{currentScan.url}</p>
            <div className="mt-2 h-1 rounded-full bg-border overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-primary transition-all"
                style={{ width: `${currentScan.qualityScore}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-border p-4 text-center">
            <ScanLine className="h-5 w-5 text-muted-foreground/40 mx-auto mb-2" />
            <p className="text-xs text-muted-foreground">No active scan.</p>
            <p className="text-[10px] text-muted-foreground/60 mt-0.5">Start a scan to see metrics.</p>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
