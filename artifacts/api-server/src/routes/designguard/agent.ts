import { randomUUID } from "crypto";
import { analyzeScreenshot, type VisionResult, type ViolationRaw } from "./gemini-vision.js";
import { generateFixAction, type AppliedFix } from "./fix-generator.js";

export interface AgentState {
  userId: string;
  url: string;
  screenshotBase64: string;
  rawViolations: ViolationRaw[];
  prioritizedViolations: ViolationRaw[];
  fixesApplied: AppliedFix[];
  scoreBefore: number;
  scoreAfter: number;
  scanId: string;
  visionResult: VisionResult | null;
}

function prioritizeViolations(violations: ViolationRaw[]): ViolationRaw[] {
  const severityOrder: Record<string, number> = {
    critical: 0,
    serious: 1,
    moderate: 2,
  };

  return [...violations]
    .sort((a, b) => {
      const aOrder = severityOrder[a.severity] ?? 3;
      const bOrder = severityOrder[b.severity] ?? 3;
      return aOrder - bOrder;
    })
    .slice(0, 10);
}

function calculateScoreAfter(scoreBefore: number, fixes: AppliedFix[]): number {
  const totalImprovement = fixes.reduce((sum, fix) => sum + fix.complianceImprovement, 0);
  return Math.min(100, scoreBefore + totalImprovement);
}

export async function runScanLoop(
  userId: string,
  url: string,
  screenshotBase64: string
): Promise<{
  scanId: string;
  violationsFound: ViolationRaw[];
  fixesApplied: AppliedFix[];
  complianceScoreBefore: number;
  complianceScoreAfter: number;
  totalViolations: number;
  criticalCount: number;
  seriousCount: number;
  moderateCount: number;
  pageSummary: string;
}> {
  const scanId = randomUUID();

  // Step 1: Observe — prepare state
  const state: AgentState = {
    userId,
    url,
    screenshotBase64,
    rawViolations: [],
    prioritizedViolations: [],
    fixesApplied: [],
    scoreBefore: 0,
    scoreAfter: 0,
    scanId,
    visionResult: null,
  };

  // Step 2: Detect — call Gemini vision
  const visionResult = await analyzeScreenshot(screenshotBase64);
  state.visionResult = visionResult;
  state.rawViolations = visionResult.violations || [];
  state.scoreBefore = visionResult.compliance_score ?? 75;

  // Step 3: Prioritize — sort by severity, take top items
  state.prioritizedViolations = prioritizeViolations(state.rawViolations);

  // Step 4: Fix — generate fix actions for each violation
  state.fixesApplied = state.prioritizedViolations.map((v) => generateFixAction(v));

  // Step 5: Verify — recalculate score after fixes
  state.scoreAfter = calculateScoreAfter(state.scoreBefore, state.fixesApplied);

  // Step 6: Report — compile final results
  const criticalCount = state.rawViolations.filter((v) => v.severity === "critical").length;
  const seriousCount = state.rawViolations.filter((v) => v.severity === "serious").length;
  const moderateCount = state.rawViolations.filter((v) => v.severity === "moderate").length;

  return {
    scanId,
    violationsFound: state.prioritizedViolations,
    fixesApplied: state.fixesApplied,
    complianceScoreBefore: state.scoreBefore,
    complianceScoreAfter: state.scoreAfter,
    totalViolations: state.rawViolations.length,
    criticalCount,
    seriousCount,
    moderateCount,
    pageSummary: visionResult.page_summary || "Accessibility scan complete.",
  };
}
