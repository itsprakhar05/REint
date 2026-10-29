# REint - Wind Forecast Accuracy Dashboard

This repository contains a first-version product for the UK day-ahead procurement use case described in the challenge brief. The application helps a utility team:

- understand the latest available wind forecast data,
- compare forecast generation against actual wind generation,
- quantify forecast error using MAE, RMSE, and bias,
- inspect a forecast-vs-actual time-series chart for the selected date window.

This project was developed with a Python FastAPI backend and a React + Vite frontend. It uses national-level wind generation actuals and forecasts from the Elexon datasets, filtered to the January 2026 decision window described in the brief.

## AI usage

This project was developed with AI assistance, including GitHub Copilot and LLM-supported implementation help during the build and debugging process.

## Repository structure

- backend/app/ - FastAPI application and analytics logic
- backend/test/ - backend regression tests
- frontend/ - React dashboard and Vite build configuration
- docker-compose.yml - local multi-container orchestration for the app
- render.yaml - deployment config for a Render-based deployment setup

## Local development

### 1) Backend

```bash
cd REint/backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2) Frontend

```bash
cd REint/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

The frontend reads the backend base URL from the VITE_API_URL environment variable. If it is not set, it defaults to http://127.0.0.1:8000.

## Docker

Start both services together using Docker Compose:

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/api/v1/health

## Deployment

The app is prepared for deployment using a Render configuration in this repo. The project is also compatible with a Vercel + separate API deployment pattern if you prefer to split the frontend and backend into different services.

### Render setup

1. Push this repository to a public GitHub repository.
2. Create a new Render Web Service for the backend from the backend directory.
3. Create a static site for the frontend from the frontend directory.
4. Set the frontend VITE_API_URL environment variable to the public backend URL.
5. Deploy and copy the generated live URL into the final submission form.

Suggested placeholder structure:

- Frontend: https://your-reint-frontend.onrender.com
- Backend: https://your-reint-backend.onrender.com

## Product summary

The app helps utility trading teams understand the latest wind forecast for the day-ahead market, compare forecast generation against actual wind output, and quantify forecast error. This is aligned to the challenge brief’s decision-support requirement for wind-based renewable procurement planning.

## Submission checklist

- [x] Backend analytics API implemented
- [x] Forecast-vs-actual chart included
- [x] React frontend added
- [x] Docker configuration prepared
- [x] Deployment config prepared
- [ ] Public GitHub repository URL
- [ ] Final deployed URL
- [ ] YouTube demo video
- [ ] Challenge submission form completed
