# BAQI AI - Invest Your Leftover Money

AI-powered investment assistant that analyzes spending patterns, identifies "baqi" (leftover) money, and recommends personalized halal PSX/mutual fund investments.

**Hackathon:** JS Bank PROCOM '26 - AI in Banking

## Tech Stack

- **Backend:** FastAPI + Supabase (PostgreSQL)
- **AI:** CrewAI (6 specialized agents) + Claude API
- **Frontend:** React + Vite + Tailwind + shadcn/ui
- **Charts:** Recharts

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your keys
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Architecture

6 AI agents work together:
1. **Spending Analyzer** - Categorizes transactions (fixed/discretionary/watery)
2. **Risk Profiler** - Assesses investment risk tolerance
3. **Halal Compliance** - Screens stocks for Shariah compliance (KMI-30)
4. **Investment Agent** - Selects PSX stocks and mutual funds
5. **Market Sentiment** - Analyzes market conditions
6. **Orchestrator** - Coordinates all agents for final recommendation
