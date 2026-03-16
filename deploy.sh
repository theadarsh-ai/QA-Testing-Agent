#!/bin/bash

# Configuration
PROJECT_ID="gemini-integration-452515"
SERVICE_NAME="qa-testing-agent"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Starting redeployment for ${SERVICE_NAME}..."

# 1. Build Frontend
echo "📦 Building frontend..."
cd artifacts/designguard
pnpm install
pnpm build
cd ../..

# 2. Build and Push Docker Image
echo "🐳 Building Docker image..."
# Note: We need a Dockerfile in the root or backend. 
# Since I couldn't find one, I'll generate a standard one for this FastAPI + Static Frontend setup.
cat <<EOF > Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \\
    chromium \\
    libnss3 \\
    libatk1.0-0 \\
    libatk-bridge2.0-0 \\
    libcups2 \\
    libdrm2 \\
    libxkbcommon0 \\
    libxcomposite1 \\
    libxdamage1 \\
    libxrandr2 \\
    libgbm1 \\
    libasound2 \\
    libpango-1.0-0 \\
    libcairo2 \\
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY designguard/backend /app/backend
WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy frontend build
COPY artifacts/designguard/dist/public /app/frontend_dist

# Set environment variables
ENV PORT=8080
ENV FRONTEND_DIST=/app/frontend_dist

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

echo "📤 Pushing to Container Registry..."
gcloud builds submit --tag ${IMAGE_NAME} --project ${PROJECT_ID}

# 3. Deploy to Cloud Run
echo "🌍 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \\
  --image ${IMAGE_NAME} \\
  --platform managed \\
  --region ${REGION} \\
  --project ${PROJECT_ID} \\
  --allow-unauthenticated \\
  --memory 2Gi \\
  --cpu 1 \\
  --timeout 3000

echo "✅ Redeployment complete! Service URL: https://qa-testing-agent-1026977097516.us-central1.run.app/"
