---
title: Mail Checker Environment Server
emoji: 📯
colorFrom: red
colorTo: red
sdk: docker
pinned: false
app_port: 7860
base_path: /web
tags:
  - openenv
---

# Mail Checker — Email Triage Environment

An OpenEnv environment where an AI agent triages emails by classifying,
prioritizing, and routing them — just like a real email assistant would.
Built for RL training and agent evaluation using the OpenEnv framework.

## Why This Environment?

Email triage is one of the most common real-world tasks for AI assistants.
This environment provides a standardized benchmark for training and evaluating
agents on email classification, priority assignment, and routing decisions.

## Quick Start
```python
from mail_checker import MailCheckerAction, MailCheckerEnv

with MailCheckerEnv(base_url="https://bfs-search-mail-checker.hf.space") as env:
    # Reset with a task
    result = env.reset()
    
    # Agent reads the email and decides
    result = env.step(MailCheckerAction(
        action_type="escalate",
        category="billing",
        priority="high"
    ))
    print(f"Reward: {result.reward}")
```

## Tasks

| Task | Emails | Difficulty | Description |
|------|--------|------------|-------------|
| `easy` | 2 | Easy | Clear spam and simple billing query — unambiguous signals |
| `medium` | 3 | Medium | Mixed categories with urgency signals requiring reasoning |
| `hard` | 3 | Hard | Ambiguous emails needing careful multi-signal reasoning |

## Observation Space

What the agent sees at each step:

| Field | Type | Description |
|-------|------|-------------|
| `email_from` | str | Sender email address |
| `subject` | str | Email subject line |
| `body` | str | Full email body text |
| `step` | int | Current step number in episode |
| `available_actions` | list[str] | Valid actions for this step |
| `done` | bool | Whether episode is complete |
| `reward` | float | Reward from previous action |

## Action Space

What the agent must decide for each email:

| Field | Type | Valid Values |
|-------|------|-------------|
| `action_type` | str | `respond`, `escalate`, `archive` |
| `category` | str | `spam`, `billing`, `support`, `sales`, `general` |
| `priority` | str | `high`, `medium`, `low` |

## Reward Function

Each email is scored 0.0 – 1.0 with partial credit:

| Decision | Weight | Scoring |
|----------|--------|---------|
| Category correct | 40% | +0.4 exact match |
| Priority correct | 30% | +0.3 exact, +0.15 if one level off |
| Action correct | 30% | +0.3 exact match |

Episode score = average reward across all emails in the task.

A random agent scores ~0.15 – 0.25. A strong LLM agent scores ~0.75 – 0.95.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start new episode, returns first email |
| `/step` | POST | Submit action, returns next email + reward |
| `/state` | GET | Current episode state |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive Swagger UI |
| `/web` | GET | Web interface for manual testing |

## Running Inference

Set environment variables and run:
```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=your-key-here
export ENV_URL=https://bfs-search-mail-checker.hf.space

python inference.py
```

## Baseline Scores

Scores achieved by `gpt-4o-mini` on the default dataset:

| Task | Score |
|------|-------|
| easy | 0.90 |
| medium | 0.75 |
| hard | 0.60 |
| **Overall** | **0.75** |

## Local Development
```bash
# Install
pip install openenv-core
pip install -e .

# Run server
uvicorn mail_checker.server.app:app --host 0.0.0.0 --port 7860

# Test
curl -X POST http://localhost:7860/reset
curl http://localhost:7860/health
```

## Docker
```bash
# Build
docker build -t mail-checker -f server/Dockerfile .

# Run
docker run -p 7860:7860 mail-checker

# Test
curl -X POST http://localhost:7860/reset
```

## Deploy to Hugging Face
```bash
cd mail_checker
openenv push
```

Space will be live at:
`https://huggingface.co/spaces/BFS-Search/mail_checker`

## Project Structure
```
mail_checker/
├── __init__.py
├── README.md
├── openenv.yaml              # OpenEnv manifest
├── pyproject.toml
├── models.py                 # Action + Observation Pydantic models
├── client.py                 # MailCheckerEnv client
├── data/
│   └── emails.py             # Email dataset + answer keys
└── server/
    ├── mail_checker_environment.py  # Core env logic, grader, rewards
    ├── app.py                       # FastAPI endpoints
    └── Dockerfile
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model identifier | `gpt-4o-mini` |
| `HF_TOKEN` | Hugging Face / API key | required |
| `ENV_URL` | Environment server URL | `https://bfs-search-mail-checker.hf.space` |
