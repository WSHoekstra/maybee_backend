#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Tuple
import math
from maybee_backend.logging import log

from maybee_backend.models.core_models import Bandit, BanditState
from maybee_backend.models.get_average_rewards_per_arm import (
    get_average_rewards_per_arm,
)


class UCB1Bandit(Bandit):
    def __init__(self, epsilon=0.05, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epsilon = epsilon

    def choose_arm(self) -> Tuple[BanditState, int]:
        avg_rewards_per_arm = get_average_rewards_per_arm(
            session=self.session,
            environment_id=self.environment_id, 
            replace_null_rewards_with_zeros=True
        )

        if avg_rewards_per_arm == []:
            arm_id = None
            bandit_state = BanditState.NO_ARMS_AVAILABLE
            log.warning(
                f"Failed to choose arm with UCB1 bandit: {self.environment_id=} (no arms available)"
            )
            return bandit_state, arm_id

        # UCB1 requires at least 1 observation per arm, so if there are any arms with 0 observations, we explore
        for arm in avg_rewards_per_arm:
            if arm.n_observations == 0:
                bandit_state = BanditState.EXPLORE
                log.info(
                    f"Chose arm with UCB1 bandit: {arm.arm_id=}, {bandit_state=} (0 observations)"
                )
                return bandit_state, arm.arm_id

        ucb_values = []
        total_observations = sum(arm.n_observations for arm in avg_rewards_per_arm)
        for arm in avg_rewards_per_arm:
            bonus = math.sqrt(
                (2 * math.log(total_observations)) / float(arm.n_observations)
            )
            ucb_value = arm.avg_reward + bonus
            ucb_values.append(ucb_value)
        maximum_reward_arm_index = ucb_values.index(max(ucb_values))
        arm_id = avg_rewards_per_arm[maximum_reward_arm_index].arm_id

        return BanditState.NOT_APPLICABLE, arm_id
