# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Mail Checker Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MailCheckerAction, MailCheckerObservation
    from ..data.emails import EMAILS
except ImportError:
    from models import MailCheckerAction, MailCheckerObservation
    from data.emails import EMAILS


class MailCheckerEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task = "easy"
        self._email_index = 0
        self._current_email = EMAILS["easy"][0]
        self._episode_actions = []
        self._reset_count = 0        # ← make sure this is here
        

    def reset(self) -> MailCheckerObservation:
        """Reset cycles through easy → medium → hard automatically."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        # Cycle tasks: first reset = easy, second = medium, third = hard
        tasks = ["easy", "medium", "hard"]
        self._current_task = tasks[self._reset_count % 3]
        self._reset_count += 1
        
        self._email_index = 0
        self._episode_actions = []
        self._current_email = EMAILS[self._current_task][0]

        return MailCheckerObservation(
            done=False,
            reward=0.0,
            email_from=self._current_email["email_from"],
            subject=self._current_email["subject"],
            body=self._current_email["body"],
            step=0,
            available_actions=["classify", "escalate", "archive", "respond"]
        )

    def step(self, action: MailCheckerAction) -> MailCheckerObservation:
        """Grade the action against the answer key and move to next email."""
        self._state.step_count += 1

        # Grade this action
        reward = self._grade_action(action)
        self._episode_actions.append({
            "action": action,
            "reward": reward
        })

        # Move to next email
        self._email_index += 1
        task_emails = EMAILS[self._current_task]

        # Check if episode is done
        done = self._email_index >= len(task_emails)

        if done:
            return MailCheckerObservation(
                done=True,
                reward=reward,
                email_from="",
                subject="Episode complete",
                body=f"Finished {len(task_emails)} emails. Final avg reward: {self._avg_reward():.2f}",
                step=self._state.step_count,
                available_actions=[]
            )

        # Load next email
        self._current_email = task_emails[self._email_index]

        return MailCheckerObservation(
            done=False,
            reward=reward,
            email_from=self._current_email["email_from"],
            subject=self._current_email["subject"],
            body=self._current_email["body"],
            step=self._state.step_count,
            available_actions=["classify", "escalate", "archive", "respond"]
        )

    def _grade_action(self, action: MailCheckerAction) -> float:

        if self._current_email is None:
            return 0.0

        answer = self._current_email["answer"]
        
        score = 0.0
        if action.category == answer["category"]:
            score += 0.4
        if action.priority == answer["priority"]:
            score += 0.3
        if action.action_type == answer["action_type"]:
            score += 0.3

        return round(score, 2)

    def _avg_reward(self) -> float:
        """Average reward across all actions in episode."""
        if not self._episode_actions:
            return 0.0
        return sum(a["reward"] for a in self._episode_actions) / len(self._episode_actions)

    @property
    def state(self) -> State:
        return self._state