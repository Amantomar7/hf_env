# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Mail Checker Environment.

The mail_checker environment is a simple test environment that echoes back messages.
"""

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


class MailCheckerAction(Action):
    """Action for the Mail Checker environment - just a message to echo."""
    
    action_type: str
    category: str
    priority: str


class MailCheckerObservation(Observation):
    email_from: str
    subject: str
    body: str
    step: int
    available_actions: list[str]
    done: bool
    reward: float          # ← was int, change to float

class MailCheckerState(State):
    pass