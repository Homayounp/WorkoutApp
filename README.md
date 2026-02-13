# 🏋️ Progressive Overload Workout Tracker

A full-stack web application for tracking workouts with progressive overload 
analysis, built with **FastAPI** (Python) and **React** (JavaScript).

## 🎯 Project Motivation

Progressive overload is the foundational principle of strength training — 
systematically increasing training stimulus over time. Most workout apps 
treat logging as a passive record. This application actively analyzes 
workout history to provide actionable progression recommendations using 
a simple algorithm based on volume load (sets × reps × weight) trends.

## 🏗️ Architecture
```text
┌─────────────┐     HTTP/JSON      ┌──────────────┐     SQLAlchemy     ┌────────────┐
│   React SPA  │ ◄──────────────► │  FastAPI API   │ ◄───────────────► │  PostgreSQL │
│  (Port 3000) │    JWT Bearer     │  (Port 8000)   │     ORM          │  (Port 5432)│
└─────────────┘                    └──────────────┘                    └────────────┘

## ✨ Key Features

- **JWT Authentication** with access/refresh token rotation
- **RESTful API** with OpenAPI/Swagger documentation
- **Progressive Overload Analysis** — compares current vs. historical 
  volume load per exercise
- **Database migrations** with Alembic
- **Containerized** with Docker Compose
- **CI/CD pipeline** with GitHub Actions (lint + test)
- **85%+ test coverage** with pytest

## 🛠️ Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | React 18, React Router, Axios       |
| Backend    | FastAPI, Pydantic, SQLAlchemy 2.0   |
| Database   | PostgreSQL (prod) / SQLite (dev)    |
| Auth       | JWT (python-jose), bcrypt           |
| Testing    | pytest, pytest-cov, httpx           |
| DevOps     | Docker, Docker Compose, GitHub Actions |
| Migrations | Alembic                             |

## 🚀 Quick Start

### With Docker (recommended):
bash
git clone https://github.com/YOUR_USERNAME/workout-tracker.git
cd workout-tracker
docker-compose up --build

### Manual Setup:
bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm start

## 📊 API Documentation

Once running, visit: `http://localhost:8000/docs`

### Key Endpoints:

| Method | Endpoint              | Description            | Auth |
|--------|-----------------------|------------------------|------|
| POST   | `/auth/register`      | Create new account     | ❌   |
| POST   | `/auth/login`         | Get JWT tokens         | ❌   |
| GET    | `/workouts/`          | List user workouts     | ✅   |
| POST   | `/workouts/`          | Create workout         | ✅   |
| POST   | `/logs/`              | Log a workout session  | ✅   |
| GET    | `/logs/`              | Get workout history    | ✅   |
| GET    | `/analytics/progress` | Progressive overload data | ✅ |

## 📸 Screenshots

<screenshots go here>

## 🧪 Testing

bash
cd backend
pytest --cov=app --cov-report=html
# Coverage: 85%+

## 📁 Project Structure

<paste the tree from above>

## 🔮 Future Improvements

- [ ] Workout templates and routine scheduling
- [ ] Exercise library with muscle group categorization
- [ ] Data export (CSV/PDF)
- [ ] Mobile-responsive PWA
- [ ] Rate limiting and request throttling

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.


---

### Day 3: Add the "Progressive Overload Analysis" Feature

This is what transforms your project from "tutorial clone" to "I actually think about problems." Add this to your backend:

**New file: `backend/app/analytics.py`**

```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import UserLog, Workout
from datetime import datetime, timedelta, timezone


def calculate_volume_load(sets: int, reps: int, load: float) -> float:
    """Volume Load = Sets × Reps × Load (kg)"""
    return sets * reps * load


def get_exercise_progression(db: Session, user_id: int, workout_id: int, weeks: int = 4):
    """
    Analyze progressive overload for a specific exercise over N weeks.
    Returns weekly volume load trend and recommendation.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(weeks=weeks)
    
    logs = (
        db.query(UserLog)
        .filter(
            UserLog.user_id == user_id,
            UserLog.workout_id == workout_id,
            UserLog.date >= cutoff
        )
        .order_by(UserLog.date.asc())
        .all()
    )
    
    if not logs:
        return {"status": "no_data", "message": "No logs found for this exercise."}
    
    # Group by week
    weekly_volumes = {}
    for log in logs:
        week_key = log.date.isocalendar()[1]  # ISO week number
        volume = calculate_volume_load(log.sets, log.reps, log.load)
        if week_key not in weekly_volumes:
            weekly_volumes[week_key] = []
        weekly_volumes[week_key].append(volume)
    
    # Calculate weekly averages
    weekly_avg = {
        week: sum(vols) / len(vols) 
        for week, vols in weekly_volumes.items()
    }
    
    weeks_sorted = sorted(weekly_avg.keys())
    trend = [{"week": w, "avg_volume_load": round(weekly_avg[w], 1)} for w in weeks_sorted]
    
    # Determine progression status
    if len(weeks_sorted) >= 2:
        first_week_vol = weekly_avg[weeks_sorted[0]]
        last_week_vol = weekly_avg[weeks_sorted[-1]]
        change_pct = ((last_week_vol - first_week_vol) / first_week_vol) * 100
        
        if change_pct > 5:
            status = "progressing"
            recommendation = "Great progress! Continue current trajectory."
        elif change_pct > -5:
            status = "plateau"
            recommendation = (
                "Volume is stagnant. Consider: increase load by 2.5kg, "
                "add 1 rep per set, or add 1 extra set."
            )
        else:
            status = "regressing"
            recommendation = (
                "Volume is declining. Check recovery, sleep, and nutrition. "
                "Consider a deload week."
            )
    else:
        status = "insufficient_data"
        change_pct = 0.0
        recommendation = "Log more sessions for trend analysis."
    
    return {
        "workout_id": workout_id,
        "period_weeks": weeks,
        "total_sessions": len(logs),
        "weekly_trend": trend,
        "change_percentage": round(change_pct, 1),
        "status": status,
        "recommendation": recommendation,
    }


def get_user_summary(db: Session, user_id: int):
    """Overall training summary for a user."""
    total_logs = db.query(func.count(UserLog.id)).filter(
        UserLog.user_id == user_id
    ).scalar()
    
    total_volume = db.query(
        func.sum(UserLog.sets * UserLog.reps * UserLog.load)
    ).filter(UserLog.user_id == user_id).scalar() or 0
    
    unique_exercises = db.query(
        func.count(func.distinct(UserLog.workout_id))
    ).filter(UserLog.user_id == user_id).scalar()
    
    # Training frequency (sessions per week, last 4 weeks)
    four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
    recent_sessions = db.query(func.count(UserLog.id)).filter(
        UserLog.user_id == user_id,
        UserLog.date >= four_weeks_ago
    ).scalar()
    avg_frequency = round(recent_sessions / 4, 1)
    
    return {
        "total_sessions": total_logs,
        "total_volume_load": round(total_volume, 1),
        "unique_exercises": unique_exercises,
        "avg_sessions_per_week": avg_frequency,
    }
