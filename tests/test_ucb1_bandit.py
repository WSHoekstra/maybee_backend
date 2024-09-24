#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from unittest.mock import patch
from fastapi import Depends
from sqlmodel import Session
from maybee_backend.database import get_session
import math
from maybee_backend.bandits.ucb1 import UCB1Bandit
from maybee_backend.models.core_models import BanditState, AvgRewardsPerArm


def test_ucb1_bandit_initialization(session: Session = Depends(get_session)):
    bandit = UCB1Bandit(session=session, environment_id=1, epsilon=0.05)
    assert isinstance(bandit, UCB1Bandit)
    assert bandit.environment_id == 1
    assert bandit.epsilon == 0.05


def test_ucb1_bandit_choose_arm_not_applicable(session: Session = Depends(get_session)):
    bandit = UCB1Bandit(session=session, environment_id=1, epsilon=0.05)

    mock_rewards = [
        AvgRewardsPerArm(
            arm_id=1, avg_reward=0.5, arm_description="", n_observations=10
        ),
        AvgRewardsPerArm(
            arm_id=2, avg_reward=0.7, arm_description="", n_observations=10
        ),
        AvgRewardsPerArm(
            arm_id=3, avg_reward=0.3, arm_description="", n_observations=10
        ),
    ]

    with patch(
        "maybee_backend.bandits.ucb1.get_average_rewards_per_arm",
        return_value=mock_rewards,
    ):
        bandit_state, arm_id = bandit.choose_arm()

    assert bandit_state == BanditState.NOT_APPLICABLE
    assert arm_id == 2  # The arm with the highest UCB value


def test_ucb1_bandit_ucb_calculation(session: Session = Depends(get_session)):
    bandit = UCB1Bandit(session=session, environment_id=1, epsilon=0.05)

    mock_rewards = [
        AvgRewardsPerArm(
            arm_id=1, avg_reward=0.5, arm_description="", n_observations=10
        ),
        AvgRewardsPerArm(
            arm_id=2, avg_reward=0.7, arm_description="", n_observations=10
        ),
        AvgRewardsPerArm(
            arm_id=3, avg_reward=0.3, arm_description="", n_observations=10
        ),
    ]

    with patch(
        "maybee_backend.bandits.ucb1.get_average_rewards_per_arm",
        return_value=mock_rewards,
    ):
        bandit_state, arm_id = bandit.choose_arm()

    total_observations = sum(arm.n_observations for arm in mock_rewards)
    expected_ucb = [
        arm.avg_reward
        + math.sqrt((2 * math.log(total_observations)) / arm.n_observations)
        for arm in mock_rewards
    ]

    assert arm_id == mock_rewards[expected_ucb.index(max(expected_ucb))].arm_id


def test_ucb1_bandit_no_rewards(session: Session = Depends(get_session)):
    bandit = UCB1Bandit(session=session, environment_id=1, epsilon=0.05)

    with patch(
        "maybee_backend.bandits.ucb1.get_average_rewards_per_arm", return_value=[]
    ):
        bandit_state, arm_id = bandit.choose_arm()

    assert bandit_state == BanditState.NO_ARMS_AVAILABLE
    assert arm_id is None
