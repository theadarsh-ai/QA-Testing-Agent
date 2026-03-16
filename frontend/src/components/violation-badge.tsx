import { Badge } from "@/components/ui/badge";
import { AlertOctagon, AlertTriangle, Info } from "lucide-react";
import type { ViolationSeverity } from "@workspace/api-client-react";

export function SeverityBadge({ severity }: { severity: ViolationSeverity | string }) {
  switch (severity.toLowerCase()) {
    case "critical":
      return (
        <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 gap-1.5 py-0.5 no-default-hover-elevate">
          <AlertOctagon className="w-3.5 h-3.5" />
          Critical
        </Badge>
      );
    case "serious":
      return (
        <Badge variant="outline" className="bg-warning/10 text-warning border-warning/20 gap-1.5 py-0.5 no-default-hover-elevate">
          <AlertTriangle className="w-3.5 h-3.5" />
          Serious
        </Badge>
      );
    case "moderate":
    default:
      return (
        <Badge variant="outline" className="bg-accent/10 text-accent border-accent/20 gap-1.5 py-0.5 no-default-hover-elevate">
          <Info className="w-3.5 h-3.5" />
          Moderate
        </Badge>
      );
  }
}
