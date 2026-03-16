import { Link } from "wouter";
import { ShieldAlert, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-background text-foreground p-6">
      <div className="text-center max-w-md">
        <div className="w-24 h-24 bg-destructive/10 text-destructive rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_50px_-10px_rgba(255,76,76,0.3)]">
          <ShieldAlert className="w-12 h-12" />
        </div>
        <h1 className="text-4xl font-display font-bold mb-4">404 - Not Found</h1>
        <p className="text-muted-foreground mb-8">
          The page you are looking for doesn't exist or has been moved.
        </p>
        <Button asChild size="lg" className="bg-primary text-primary-foreground hover-elevate">
          <Link href="/">
            <ArrowLeft className="w-4 h-4 mr-2" /> Return to Scanner
          </Link>
        </Button>
      </div>
    </div>
  );
}
