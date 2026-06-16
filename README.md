# Heallio — AI-Powered Personal Health Companion

[![CI](https://github.com/Ishita-coder27/healilleo/actions/workflows/ci.yml/badge.svg)](https://github.com/Ishita-coder27/healilleo/actions/workflows/ci.yml)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.126-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Heallio is a full-stack health management platform that combines AI-driven medical report analysis, an intelligent health chatbot, vitals tracking, and personalised wellness tools — all in a single, clean interface.

---

## Live Demo

> **Demo credentials:** `demo@heallio.in` / `Demo@1234`

<!-- Add your live URL here once deployed -->
<!-- [View Live App](https://heallio.vercel.app) -->

---

## Screenshots

<!-- Replace the placeholders below with your actual screenshots -->

**Dashboard**

![Dashboard](docs/screenshots/dashboard.png)

**Medical Reports & AI Analysis**

![Medical Reports](docs/screenshots/medical-reports.png)

**Health Analytics**

![Analytics](docs/screenshots/analytics.png)

**AI Health Assistant**

![AI Assistant](docs/screenshots/ai-assistant.png)

**Appointments**

![Appointments](docs/screenshots/appointments.png)

---

## Features

| Category | Details |
|---|---|
| **AI Medical Analysis** | Upload any PDF lab report — AI extracts vitals (BP, glucose, heart rate, cholesterol) automatically |
| **Health AI Chatbot** | Context-aware conversations with Groq LLM, grounded in your uploaded reports |
| **Health Score** | Algorithmic score card calculated from your real vitals, displayed as an animated ring |
| **PDF Health Export** | One-click export of your vitals and medications as a formatted PDF report |
| **Appointments** | Book, view, and delete doctor appointments with upcoming/past split view |
| **Medication Tracker** | Schedule medications with dosage, frequency, and reminder times |
| **Health Analytics** | Line and bar charts for vitals trends, sleep, water intake over time |
| **Sleep & Water Trackers** | Log daily sleep hours and water intake from the sidebar |
| **BMI Calculator** | Inline modal calculator with instant result |
| **Voice Input** | Speak health questions directly — uses browser-native Web Speech API |
| **Dark Mode** | Fully themed dark/light mode, persisted across sessions |
| **Google OAuth** | Sign in with Google or email/password — JWT-secured sessions |
| **Diet & Exercise Plans** | AI-generated personalised plans based on your goals and fitness level |
| **Docker Support** | One `docker-compose up` to run the full stack |
| **CI/CD** | GitHub Actions pipeline runs on every push |

---

## Architecture

```
Browser (React 18 + Vite)
  Dashboard  Analytics  Medical Reports  AI Chat  Appointments
       |
       |  REST API + JWT
       |
FastAPI Backend (Python 3.12)
  Auth  Vitals  Reports  Medications  Appointments  Chat  Export
       |                    |
  PostgreSQL            AI Engine
  (SQLAlchemy)          Groq LLM  +  RAG over uploaded reports
                        PDF extraction (pdfplumber)
                        PDF generation (ReportLab)
```

---

## Tech Stack

**Frontend**
- React 18 + Vite 6
- React Router 7
- Recharts (analytics charts)
- Custom CSS design tokens — no UI framework dependency
- Web Speech API (voice input)

**Backend**
- FastAPI 0.126 (async, auto-documented at `/docs`)
- SQLAlchemy 2 ORM + psycopg2
- ReportLab (PDF report generation)
- APScheduler (medication reminders)
- python-jose + bcrypt (JWT authentication)

**AI / ML**
- Groq API — primary inference (ultra-fast)
- RAG pipeline over user-uploaded medical PDFs
- pdfplumber + pdfminer.six (PDF text extraction)

**DevOps**
- Docker + docker-compose
- GitHub Actions CI

---

## Quick Start (Docker)

Requires Docker Desktop.

```bash
git clone https://github.com/Ishita-coder27/healilleo.git
cd healilleo
cp .env.example .env        # fill in GROQ_API_KEY and GOOGLE_CLIENT_ID
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Local Development

### Prerequisites

| Tool | Version |
|---|---|
| Node.js | >= 22 |
| Python | >= 3.12 |
| PostgreSQL | >= 16 |

### 1. Clone the repo

```bash
git clone https://github.com/Ishita-coder27/healilleo.git
cd healilleo
```

### 2. Database setup

```sql
-- Run in psql as superuser
CREATE USER hellio_user WITH PASSWORD 'hellio123';
CREATE DATABASE hellio_db OWNER hellio_user;
```

```bash
cd backend
python create_tables.py
```

### 3. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd Frontend
npm install
npm run dev
# Runs at http://localhost:5174
```

### 5. Environment variables

Create `backend/.env`:

```
DATABASE_URL=postgresql://hellio_user:hellio123@localhost:5432/hellio_db
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
```

Get a free Groq API key at https://console.groq.com

### 6. Seed demo data (optional)

```bash
cd backend
python seed_demo.py
# Creates demo@heallio.in / Demo@1234 with medications and appointments
```

---

## Project Structure

```
healilleo/
├── Frontend/
│   └── src/
│       ├── pages/          # Dashboard, Analytics, MedicalReports, AIAssistant,
│       │                   # MedicineSchedule, Appointments, DietPlan, Exercise,
│       │                   # Profile, Settings, Login, Register
│       ├── components/     # Navbar, Sidebar, PageLayout, BMICalculator,
│       │                   # SleepTracker, WaterTracker, ExportButton
│       ├── context/        # AuthContext, ThemeContext
│       └── hooks/          # useVoiceInput
│
├── backend/
│   └── app/
│       ├── api/routes/     # auth, vitals, medical_reports, appointments,
│       │                   # medications, chat, export, report_vitals
│       ├── models/         # SQLAlchemy ORM models
│       ├── schemas/        # Pydantic validators
│       ├── crud/           # Database operations
│       └── services/       # AI pipeline, vital extraction
│
├── docker-compose.yml
├── backend/Procfile        # Railway deployment
├── Frontend/.env.example   # Vercel deployment
└── .github/workflows/ci.yml
```

---

## Deployment

**Frontend — Vercel**

1. Connect the repo on vercel.com, set root directory to `Frontend`
2. Add environment variable: `VITE_API_URL=https://your-railway-backend.up.railway.app`

**Backend — Railway**

1. New project from the `backend/` folder
2. Add PostgreSQL addon
3. Set env vars: `DATABASE_URL`, `GROQ_API_KEY`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`
4. Railway uses `Procfile` automatically

---

## License

MIT © [Ishita](https://github.com/Ishita-coder27)
