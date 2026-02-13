# Iron Protocol — Adaptive Resistance Training System

An intelligent workout tracker that implements **feedback-driven progressive overload**
using a double-progression model with real-time biofeedback adaptation.

> Unlike passive workout loggers, Iron Protocol continuously adapts training
> prescriptions (weight, reps, and volume) based on physiological feedback
> signals — soreness, pump quality, and perceived workload — creating a
> personalized auto-regulating training system.

## The Problem

Progressive overload — systematically increasing training demands over
time — is the foundational driver of muscular hypertrophy. However, most
trainees either:

1. **Progress too aggressively**, accumulating fatigue faster than they can
   recover, leading to stagnation or injury
2. **Progress too conservatively**, never reaching the stimulus threshold
   needed for adaptation
3. **Ignore biofeedback signals**, following rigid programs that don't
   account for individual recovery variance

## The Solution: Adaptive Progression Engine

Iron Protocol uses a **multi-signal decision matrix** to prescribe training
variables session-by-session:

### Double Progression Model (Weight & Reps)
```text
┌─────────────────────┐
│  Can weight increase │
│  by ~2.5% with       │
│  available equipment?│
└─────────┬───────────┘
╱          ╲
YES           NO
╱              ╲
┌───────▼──────┐  ┌─────▼──────────┐
│ ↑ Weight     │  │ Are reps at     │
│ Reset reps   │  │ range ceiling?  │
│ to floor     │  │ (e.g., 12)      │
└──────────────┘  └────┬────────────┘
╱     ╲
YES      NO
╱         ╲
┌────────▼──┐  ┌────▼──────┐
│Force weight│  │ ↑ Reps +1 │
│jump, reset │  │Keep weight │
│reps to 8   │  │ same       │
└────────────┘  └───────────┘

### Feedback-Driven Volume Modulation (Sets)

Three biofeedback signals are collected after each training day:

| Signal | Scale | What It Measures |
|--------|-------|------------------|
| **Soreness** | None → Severe (0-3) | Recovery status / accumulated fatigue |
| **Pump** | None → Great (0-3) | Acute mechanical tension and metabolic stress |
| **Volume Perception** | Too Little → Too Much (-1 to +1) | Perceived workload relative to capacity |

These signals are classified into a **Recovery × Stimulus** matrix:

| | Insufficient Stimulus | Optimal Stimulus | Excessive Stimulus |
|---|---|---|---|
| **Fully Recovered** | +1 set | +1 set (overload) | Hold |
| **Mostly Recovered** | +1 set | Hold | -1 set |
| **Under-Recovered** | -1 set | -1 set | -2 sets |
| **Overtrained** | -2 sets | -2 sets | -2 sets |

### Equipment-Aware Weight Rounding

The system accounts for real-world equipment constraints. For example,
dumbbells are only available in fixed increments (10kg, 12.5kg, 15kg...).
If the calculated weight increase would require a jump that exceeds 2.5×
the target percentage, the system adds a rep instead of forcing an
unrealistic weight jump.

## Architecture

text
┌──────────────┐      HTTP/JSON       ┌─────────────────────┐
│  React SPA   │ ◄──────────────────► │    FastAPI Backend   │
│  (Frontend)  │     JWT Bearer       │                     │
└──────────────┘                      │  ┌───────────────┐  │
│  │  Progression   │  │
│  │  Engine        │  │     ┌────────────┐
│  │                │  │────►│ PostgreSQL │
│  │ • Weight Calc  │  │     │            │
│  │ • Rep Calc     │  │     │ • Users    │
│  │ • Volume Calc  │  │     │ • Plans    │
│  │ • Feedback Agg │  │     │ • Mesos    │
│  └───────────────┘  │     │ • SetLogs  │
└─────────────────────┘     │ • Feedback │
└────────────┘

### Data Model

text
Plan (template)
 └── PlanDay
└── PlanDayExercise

Mesocycle (execution instance of a Plan)
 └── MesocycleWeek
└── MesocycleDay
├── MesocycleDayExercise
│    └── SetLog (weight, reps, per set)
└── Feedback (soreness, pump, volume_feeling, per muscle)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, React Router, Axios |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 |
| Database | PostgreSQL (production) / SQLite (development) |
| Auth | JWT with access/refresh token rotation (python-jose, bcrypt) |
| Testing | pytest, pytest-cov, httpx |
| DevOps | Docker, Docker Compose, GitHub Actions CI/CD |
| Migrations | Alembic |

## Quick Start

### Docker (recommended)
bash
git clone https://github.com/Homayounp/WorkoutApp.git
cd WorkoutApp
docker-compose up --build

### Manual Setup
bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm start

## API Documentation

Interactive docs available at `http://localhost:8000/docs` when running.

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | JWT authentication |
| POST | `/plans/` | Create training plan template |
| POST | `/mesocycles/` | Start a mesocycle from a plan |
| GET | `/mesocycles/{id}/current-workout` | Get today's prescribed workout |
| POST | `/mesocycle-day-exercises/{id}/log-set` | Log a completed set |
| POST | `/mesocycle-days/{id}/feedback` | Submit biofeedback |
| POST | `/mesocycle-days/{id}/complete` | Mark training day complete |
| GET | `/mesocycle-days/{id}/smart-targets` | Get AI-prescribed targets |
| POST | `/mesocycles/{id}/next-week` | Advance with auto-progression |

## Theoretical Foundation

The progression algorithms are grounded in established exercise science
principles:

- **Progressive Overload Principle**: Systematic increase of training
  demands is required to drive continued adaptation (Schoenfeld, 2010)
- **Stimulus-Recovery-Adaptation (SRA) Curve**: Training volume must be
  calibrated to individual recovery capacity (Verkhoshansky & Siff, 2009)
- **Double Progression**: When equipment constraints prevent linear weight
  increases, adding reps serves as an intermediate progression step
  (Helms et al., 2015)
- **Auto-regulation**: Using subjective biofeedback (RPE, soreness,
  perceived effort) to modify training in real-time produces superior
  outcomes vs. rigid programming (Helms et al., 2018)

## Future Roadmap

- [ ] Muscle group recovery time modeling (48h vs 72h based on volume)
- [ ] Periodization support (accumulation → intensification → deload cycles)
- [ ] Exercise substitution recommendations based on equipment availability
- [ ] Data export (CSV/PDF) for coach review
- [ ] Mobile-responsive PWA

## License

MIT


---

## Phase 5: Architecture Diagram for Your CV

Here's a proper system architecture diagram you can render with any diagramming tool (draw.io, Mermaid, etc.):

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        IRON PROTOCOL — SYSTEM ARCHITECTURE              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐                              ┌──────────────────────┐ │
│  │   CLIENT     │                              │     DATABASE         │ │
│  │   (React)    │                              │    (PostgreSQL)      │ │
│  │              │         ┌──────────────┐     │                      │ │
│  │ • Workout UI │────────►│              │     │  ┌────────────────┐  │ │
│  │ • Feedback   │  JSON   │   FastAPI    │     │  │ users          │  │ │
│  │   Forms      │◄────────│   Backend    │     │  ├────────────────┤  │ │
│  │ • Progress   │  JWT    │              │────►│  │ exercises      │  │ │
│  │   Charts     │         │ ┌──────────┐ │ SQL │  ├────────────────┤  │ │
│  │ • History    │         │ │  Auth    │ │     │  │ plans          │  │ │
│  └─────────────┘         │ │  Layer   │ │     │  │ plan_days      │  │ │
│                           │ ├──────────┤ │     │  │ plan_day_exers │  │ │
│                           │ │  CRUD    │ │     │  ├────────────────┤  │ │
│                           │ │  Layer   │ │     │  │ mesocycles     │  │ │
│                           │ ├──────────┤ │     │  │ meso_weeks     │  │ │
│                           │ │PROGRESSION│ │     │  │ meso_days      │  │ │
│                           │ │ ENGINE   │ │     │  │ meso_day_exers │  │ │
│                           │ │          │ │     │  ├────────────────┤  │ │
│                           │ │• Weight  │ │     │  │ set_logs       │  │ │
│                           │ │  Calc    │ │     │  │ feedbacks      │  │ │
│                           │ │• Rep     │ │     │  └────────────────┘  │ │
│                           │ │  Calc    │ │     │                      │ │
│                           │ │• Volume  │ │     └──────────────────────┘ │
│                           │ │  Calc    │ │                              │
│                           │ │• Feedback│ │     ┌──────────────────────┐ │
│                           │ │  Matrix  │ │     │      CI/CD           │ │
│                           │ └──────────┘ │     │   GitHub Actions     │ │
│                           └──────────────┘     │  • Lint (flake8)     │ │
│                                                │  • Test (pytest)     │ │
│                                                │  • Build (Docker)    │ │
│                                                └──────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
