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
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY      = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
ENV_URL      = "https://bfs-search-mail-checker.hf.space"
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
    print(f"[START] task={task_id}", flush=True)
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
            print(f"  Model request failed: {exc}. Using fallback.", flush=True)
            response_text = ""

        # Parse action
        action = parse_model_action(response_text)
        # print(f"  Decision: {action}")

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
            # print(f"  Step failed: {e}")
            print(f"[END] task={task_id} score=0.0 steps={steps}", flush=True)
            break

        reward = result.get("reward", 0.0)
        done   = result.get("done", False)
        total_reward += reward
        steps += 1

        # print(f"  Reward  : {reward}")
        print(f"[STEP] step={steps} reward={reward}", flush=True)

        if done:
            # print("  Episode complete.")
            break

    avg = total_reward / steps if steps > 0 else 0.0
    # print(f"\n  Score for {task_id}: {avg:.2f}")
    print(f"[END] task={task_id} score={round(avg, 4)} steps={steps}", flush=True)
    return avg


def main() -> None:
    if not API_KEY:
        raise ValueError("HF_TOKEN or API_KEY environment variable not set.")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    print(f"Model   : {MODEL_NAME}", flush=True)
    print(f"API URL : {API_BASE_URL}", flush=True)
    print(f"Server  : {ENV_URL}", flush=True)

    scores = {}
    for task in ["easy", "medium", "hard"]:
        scores[task] = run_task(client, task)

    print(f"\nFINAL SCORES", flush=True)
    for task, score in scores.items():
        bar = "█" * int(score * 20)
        print(f"  {task}: {score:.4f}", flush=True)

    overall = sum(scores.values()) / len(scores)
    print(f"  overall: {overall:.4f}", flush=True)


if __name__ == "__main__":
    main()