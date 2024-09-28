#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from maybee_backend.models.get_average_rewards_per_arm import (
    get_average_rewards_per_arm,
)
from maybee_backend.models.core_models import Bandit, BanditState
from typing import Tuple
from maybee_backend.logging import log
import random


class EpsilonGreedyBandit(Bandit):
    def __init__(self, epsilon=0.05, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epsilon = epsilon

    def choose_arm(self) -> Tuple[BanditState, int]:
        """
        Generate a random float p between 0 and 1.
        If p > epsilon,
        exploit by serving the id of the arm with the highest avg reward.
        Otherwise, explore by serving a random arm_id.
        """
        p = round(random.uniform(0, 1), 2)
        if p >= self.epsilon:
            bandit_state = BanditState.EXPLOIT

            avg_rewards_per_arm = get_average_rewards_per_arm(
                session=self.session,
                environment_id=self.environment_id,
                replace_null_rewards_with_zeros=True
            )
            arm = sorted(
                avg_rewards_per_arm,
                key=lambda x: x.avg_reward,
                reverse=True,
            )[0]
            arm_id = arm.arm_id

        else:
            bandit_state = BanditState.EXPLORE
            avg_rewards_per_arm = get_average_rewards_per_arm(
                self.environment_id, replace_null_rewards_with_zeros=True
            )
            arm = sorted(
                avg_rewards_per_arm,
                key=lambda x: random.uniform(0, 1),
                reverse=True,
            )[0]
            arm_id = arm.arm_id
        log.debug(
            f"Chose arm with epsilon greedy bandit: {arm_id=}  {p=}, {self.epsilon=}, {bandit_state=}"
        )
        return bandit_state, arm_id
