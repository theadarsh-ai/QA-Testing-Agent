import express, { type Express, type Request, type Response } from "express";
import cors from "cors";
import { createProxyMiddleware } from "http-proxy-middleware";

const app: Express = express();

app.use(cors());

// Proxy all /api requests to the Python FastAPI backend on port 5000
// The Python server handles: /health, /scan, /apply-fix, /history/{user_id}
// We strip the /api prefix so Python receives: /health, /scan, etc.
app.use(
  "/api",
  createProxyMiddleware({
    target: "http://localhost:5000",
    changeOrigin: true,
    pathRewrite: { "^/api": "" },
    on: {
      error: (err, req, res) => {
        console.error("Proxy error:", err.message);
        (res as Response).status(502).json({
          error: "backend_unavailable",
          message: "Python FastAPI backend is starting up. Please retry in a moment.",
        });
      },
    },
  })
);

export default app;
