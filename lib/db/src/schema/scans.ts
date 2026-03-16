import { pgTable, text, integer, jsonb, timestamp, serial } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod/v4";

export const scansTable = pgTable("scans", {
  id: serial("id").primaryKey(),
  scanId: text("scan_id").notNull().unique(),
  userId: text("user_id").notNull(),
  url: text("url").notNull(),
  violations: jsonb("violations").notNull().$type<object[]>().default([]),
  fixes: jsonb("fixes").notNull().$type<object[]>().default([]),
  complianceScoreBefore: integer("compliance_score_before").notNull().default(0),
  complianceScoreAfter: integer("compliance_score_after").notNull().default(0),
  totalViolations: integer("total_violations").notNull().default(0),
  criticalCount: integer("critical_count").notNull().default(0),
  seriousCount: integer("serious_count").notNull().default(0),
  moderateCount: integer("moderate_count").notNull().default(0),
  pageSummary: text("page_summary").notNull().default(""),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const insertScanSchema = createInsertSchema(scansTable).omit({ id: true, createdAt: true });
export type InsertScan = z.infer<typeof insertScanSchema>;
export type Scan = typeof scansTable.$inferSelect;
