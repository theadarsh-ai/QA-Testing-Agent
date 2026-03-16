import { Router, type IRouter, type Request, type Response } from "express";
import { db, scansTable } from "@workspace/db";
import { desc, eq } from "drizzle-orm";
import { runScanLoop } from "./agent.js";
import {
  CreateScanBody,
  ApplyFixBody,
} from "@workspace/api-zod";

const router: IRouter = Router();

// POST /scan
router.post("/scan", async (req: Request, res: Response) => {
  try {
    const body = CreateScanBody.parse(req.body);
    const { userId, url, screenshotBase64 } = body;

    const result = await runScanLoop(userId, url, screenshotBase64);

    // Save to database
    await db.insert(scansTable).values({
      scanId: result.scanId,
      userId,
      url,
      violations: result.violationsFound as object[],
      fixes: result.fixesApplied as object[],
      complianceScoreBefore: result.complianceScoreBefore,
      complianceScoreAfter: result.complianceScoreAfter,
      totalViolations: result.totalViolations,
      criticalCount: result.criticalCount,
      seriousCount: result.seriousCount,
      moderateCount: result.moderateCount,
      pageSummary: result.pageSummary,
    });

    res.json(result);
  } catch (error) {
    console.error("Scan error:", error);
    res.status(500).json({
      error: "scan_failed",
      message: error instanceof Error ? error.message : "Scan failed",
    });
  }
});

// POST /apply-fix
router.post("/apply-fix", async (req: Request, res: Response) => {
  try {
    const body = ApplyFixBody.parse(req.body);
    const { scanId, violationId } = body;

    const scan = await db
      .select()
      .from(scansTable)
      .where(eq(scansTable.scanId, scanId))
      .limit(1);

    if (!scan.length) {
      res.status(404).json({ error: "not_found", message: "Scan not found" });
      return;
    }

    const fixes = scan[0].fixes as Array<{
      violationId: string;
      devtoolsCommand: string;
      explanation: string;
      wcagCriterionMet: string;
    }>;

    const fix = fixes.find((f) => f.violationId === violationId);

    if (!fix) {
      res.status(404).json({ error: "not_found", message: "Fix not found for violation" });
      return;
    }

    res.json({
      actionType: "devtools_command",
      targetElement: violationId,
      fixCode: fix.devtoolsCommand,
      explanation: fix.explanation,
    });
  } catch (error) {
    console.error("Apply fix error:", error);
    res.status(500).json({
      error: "apply_fix_failed",
      message: error instanceof Error ? error.message : "Apply fix failed",
    });
  }
});

// GET /history/:userId
router.get("/history/:userId", async (req: Request, res: Response) => {
  try {
    const { userId } = req.params;

    const scans = await db
      .select({
        scanId: scansTable.scanId,
        url: scansTable.url,
        createdAt: scansTable.createdAt,
        complianceScoreBefore: scansTable.complianceScoreBefore,
        complianceScoreAfter: scansTable.complianceScoreAfter,
        totalViolations: scansTable.totalViolations,
        criticalCount: scansTable.criticalCount,
        seriousCount: scansTable.seriousCount,
        moderateCount: scansTable.moderateCount,
        pageSummary: scansTable.pageSummary,
      })
      .from(scansTable)
      .where(eq(scansTable.userId, userId))
      .orderBy(desc(scansTable.createdAt))
      .limit(10);

    res.json({
      scans: scans.map((s) => ({
        ...s,
        createdAt: s.createdAt.toISOString(),
      })),
    });
  } catch (error) {
    console.error("History error:", error);
    res.status(500).json({
      error: "history_failed",
      message: error instanceof Error ? error.message : "History fetch failed",
    });
  }
});

export default router;
