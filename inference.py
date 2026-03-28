import os
import sys
import json
import requests
from openai import OpenAI

# ── required env vars ───────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "")
MODEL_NAME   = os.environ.get("MODEL_NAME", "")
HF_TOKEN     = os.environ.get("HF_TOKEN")
ENV_URL      = os.environ.get("ENV_URL", "")

if not HF_TOKEN:
    print("Error: HF_TOKEN environment variable not set.")
    sys.exit(1)

# ── OpenAI client using API_BASE_URL ────
client = OpenAI(
    api_key=HF_TOKEN,
    base_url=API_BASE_URL,
)

# ── LLM decision ────────────────────────
def ask_llm(obs: dict) -> dict:
    prompt = f"""You are an expert email triage assistant.

Read this email and classify it.

From: {obs['email_from']}
Subject: {obs['subject']}
Body: {obs['body']}

Respond ONLY with JSON, no explanation, no markdown:
{{
    "action_type": "respond or escalate or archive",
    "category": "spam or billing or support or sales or general",
    "priority": "high or medium or low"
}}

Rules:
- spam/newsletters → archive, low priority
- billing disputes → escalate, high priority
- simple questions → respond, medium priority
- angry customers → escalate, high priority
- enterprise/sales → escalate, high priority"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

# ── run one task ────────────────────────
def run_task(task_id: str) -> float:
    print(f"\n{'='*45}")
    print(f"  TASK: {task_id.upper()}")
    print(f"{'='*45}")

    r = requests.post(f"{ENV_URL}/reset", params={"task_id": task_id})
    if r.status_code != 200:
        print(f"Reset failed: {r.text}")
        return 0.0

    total_reward = 0.0
    steps = 0
    done = False
    result = r.json()

    while not done:
        obs = result["observation"]

        print(f"\n  Email {steps+1}:")
        print(f"  From    : {obs['email_from']}")
        print(f"  Subject : {obs['subject']}")

        try:
            decision = ask_llm(obs)
        except Exception as e:
            print(f"  LLM error: {e}, using fallback")
            decision = {
                "action_type": "archive",
                "category": "general",
                "priority": "low"
            }

        print(f"  Decision: {decision}")

        r = requests.post(f"{ENV_URL}/step", json={"action": decision})
        result = r.json()

        reward = result["reward"]
        done   = result["done"]
        total_reward += reward
        steps += 1

        print(f"  Reward  : {reward}")

    avg = total_reward / steps if steps > 0 else 0.0
    print(f"\n  Score for {task_id}: {avg:.2f}")
    return avg

# ── main ────────────────────────────────
if __name__ == "__main__":
    print("Mail Checker — Inference Evaluation")
    print(f"Model   : {MODEL_NAME}")
    print(f"API URL : {API_BASE_URL}")
    print(f"Server  : {ENV_URL}")

    scores = {}
    for task in ["easy", "medium", "hard"]:
        scores[task] = run_task(task)

    print(f"\n{'='*45}")
    print("  FINAL SCORES")
    print(f"{'='*45}")
    for task, score in scores.items():
        bar = "█" * int(score * 20)
        print(f"  {task:<8}: {score:.2f}  {bar}")

    overall = sum(scores.values()) / len(scores)
    print(f"\n  Overall : {overall:.2f}")
    print(f"{'='*45}")