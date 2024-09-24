#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from maybee_backend.models.core_models import Bandit, BanditState
from maybee_backend.models.get_average_rewards_per_arm import (
    get_average_rewards_per_arm,
)
from typing import Tuple
import math
import numpy as np
from maybee_backend.logging import log


class SoftmaxBandit(Bandit):
    def __init__(self, tau=0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tau = tau

    def choose_arm(self) -> Tuple[BanditState, int]:
        """
        Choose an arm
        """
        avg_rewards_per_arm = get_average_rewards_per_arm(
            session=self.session,
            environment_id=self.environment_id,
            replace_null_rewards_with_zeros=True,
        )

        if avg_rewards_per_arm == []:
            arm_id = None
            bandit_state = BanditState.NO_ARMS_AVAILABLE
            log.warning(
                f"Failed to choose arm with softmax bandit: {self.environment_id=} (no arms available)"
            )
            return bandit_state, arm_id

        exp_values = [
            math.exp((arm.avg_reward) / self.tau) for arm in avg_rewards_per_arm
        ]
        z = sum(exp_values)
        probs = [exp_val / z for exp_val in exp_values]

        chosen_arm_index = np.random.choice(range(len(probs)), p=probs)
        arm_id = avg_rewards_per_arm[chosen_arm_index].arm_id
        bandit_state = BanditState.NOT_APPLICABLE
        log.debug(f"Chose arm with softmax bandit: {arm_id=} from {probs=}")
        return bandit_state, arm_id
