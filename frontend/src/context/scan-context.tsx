import React, { createContext, useContext, useState, ReactNode } from "react";
import type { ScanData } from "@/lib/api";

interface ScanContextType {
  currentScan: ScanData | null;
  setCurrentScan: (scan: ScanData | null) => void;
  clearScan: () => void;
}

const ScanContext = createContext<ScanContextType | undefined>(undefined);

export function ScanProvider({ children }: { children: ReactNode }) {
  const [currentScan, setCurrentScan] = useState<ScanData | null>(null);

  const clearScan = () => setCurrentScan(null);

  return (
    <ScanContext.Provider value={{ currentScan, setCurrentScan, clearScan }}>
      {children}
    </ScanContext.Provider>
  );
}

export function useScan() {
  const context = useContext(ScanContext);
  if (context === undefined) {
    throw new Error("useScan must be used within a ScanProvider");
  }
  return context;
}
