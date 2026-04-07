import os
import re
import json
import requests
from openai import OpenAI
import base64
import textwrap
from io import BytesIO
from typing import List, Optional, Dict
import numpy as np
from PIL import Image

# ── required env vars ───────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME   = os.getenv("MODEL_NAME")
ENV_URL      = os.getenv("ENV_URL", "https://bfs-search-mail-checker.hf.space")
MAX_STEPS    = 10
TEMPERATURE  = 0.0
MAX_TOKENS   = 200
MAX_DOM_CHARS = 3500
FALLBACK_ACTION = {
    "action_type": "archive",
    "category": "general",
    "priority": "low"
}

SYSTEM_PROMPT = """
You are an expert email triage assistant.
Given an email, you must classify it and decide what to do.
Reply with ONLY a JSON object, no explanation, no markdown fences.

Rules:
- spam or newsletters → archive, low priority
- billing disputes or double charges → escalate, high priority
- simple questions → respond, medium priority
- angry customers or legal threats → escalate, high priority
- enterprise or sales leads → escalate, high priority
- cannot log in or account issues → respond, high priority

Valid values:
- action_type: respond, escalate, archive
- category: spam, billing, support, sales, general
- priority: high, medium, low
""".strip()


def build_user_prompt(observation: dict) -> str:
    return f"""
From: {observation.get('email_from', '')}
Subject: {observation.get('subject', '')}
Body: {observation.get('body', '')}

Reply with exactly this JSON format:
{{"action_type": "...", "category": "...", "priority": "..."}}
""".strip()


def parse_model_action(response_text: str) -> dict:
    if not response_text:
        return FALLBACK_ACTION

    # Strip markdown fences if present
    clean = response_text.strip()
    clean = re.sub(r"```json|```", "", clean).strip()

    try:
        parsed = json.loads(clean)
        # Validate required fields exist
        if all(k in parsed for k in ["action_type", "category", "priority"]):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    return FALLBACK_ACTION


def run_task(client: OpenAI, task_id: str) -> float:
    print(f"\n{'='*45}")
    print(f"  TASK: {task_id.upper()}")
    print(f"{'='*45}")

    # Reset environment
    try:
        r = requests.post(
            f"{ENV_URL}/reset",
            params={"task_id": task_id},
            timeout=30
        )
        r.raise_for_status()
    except Exception as e:
        print(f"  Reset failed: {e}")
        return 0.0

    result = r.json()
    total_reward = 0.0
    steps = 0
    done = False

    while not done and steps < MAX_STEPS:
        observation = result["observation"]
        done = result.get("done", False)

        if done:
            break

        print(f"\n  Email {steps + 1}:")
        print(f"  From    : {observation.get('email_from', '')}")
        print(f"  Subject : {observation.get('subject', '')}")

        # Build prompt
        user_prompt = build_user_prompt(observation)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ]

        # Call LLM
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"  Model request failed: {exc}. Using fallback.")
            response_text = ""

        # Parse action
        action = parse_model_action(response_text)
        print(f"  Decision: {action}")

        # Send to environment
        try:
            r = requests.post(
                f"{ENV_URL}/step",
                json={"action": action},
                timeout=30
            )
            r.raise_for_status()
            result = r.json()
        except Exception as e:
            print(f"  Step failed: {e}")
            break

        reward = result.get("reward", 0.0)
        done   = result.get("done", False)
        total_reward += reward
        steps += 1

        print(f"  Reward  : {reward}")

        if done:
            print("  Episode complete.")
            break

    avg = total_reward / steps if steps > 0 else 0.0
    print(f"\n  Score for {task_id}: {avg:.2f}")
    return avg


def main() -> None:
    if not API_KEY:
        raise ValueError("HF_TOKEN or API_KEY environment variable not set.")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    print("Mail Checker — Inference Evaluation")
    print(f"Model   : {MODEL_NAME}")
    print(f"API URL : {API_BASE_URL}")
    print(f"Server  : {ENV_URL}")

    scores = {}
    for task in ["easy", "medium", "hard"]:
        scores[task] = run_task(client, task)

    print(f"\n{'='*45}")
    print("  FINAL SCORES")
    print(f"{'='*45}")
    for task, score in scores.items():
        bar = "█" * int(score * 20)
        print(f"  {task:<8}: {score:.2f}  {bar}")

    overall = sum(scores.values()) / len(scores)
    print(f"\n  Overall : {overall:.2f}")
    print(f"{'='*45}")


if __name__ == "__main__":
    main()