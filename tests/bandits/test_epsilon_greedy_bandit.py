#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from sqlmodel import Session
from unittest.mock import patch
from maybee_backend.bandits.epsilon_greedy import EpsilonGreedyBandit
from maybee_backend.models.core_models import BanditState, AvgRewardsPerArm


def test_epsilon_greedy_bandit_initialization(session: Session):
    bandit = EpsilonGreedyBandit(session=session, environment_id=1)
    assert isinstance(bandit, EpsilonGreedyBandit)
    assert bandit.environment_id == 1


def test_epsilon_greedy_bandit_choose_arm_exploit(
    session: Session,
):
    bandit = EpsilonGreedyBandit(session=session, environment_id=1, epsilon=0.1)

    # Mock random.uniform to always return a value greater than epsilon
    with patch("random.uniform", return_value=0.2):
        # Mock get_average_rewards_per_arm to return predetermined values
        mock_rewards = [
            AvgRewardsPerArm(
                arm_id=1, avg_reward=0.5, arm_description="", n_observations=20
            ),
            AvgRewardsPerArm(
                arm_id=2, avg_reward=0.7, arm_description="", n_observations=20
            ),
            AvgRewardsPerArm(
                arm_id=3, avg_reward=0.3, arm_description="", n_observations=20
            ),
        ]
        with patch(
            "maybee_backend.bandits.epsilon_greedy.get_average_rewards_per_arm",
            return_value=mock_rewards,
        ):
            bandit_state, arm_id = bandit.choose_arm()

    assert bandit_state == BanditState.EXPLOIT
    assert arm_id == 2  # The arm with the highest average reward


def test_epsilon_greedy_bandit_choose_arm_explore(
    session: Session,
):
    bandit = EpsilonGreedyBandit(session=session, environment_id=1, epsilon=0.05)

    # Mock random.uniform to always return a value less than epsilon
    with patch("random.uniform", return_value=0.01):
        # Mock get_average_rewards_per_arm to return predetermined values
        mock_rewards = [
            AvgRewardsPerArm(
                arm_id=1, avg_reward=0.5, arm_description="", n_observations=20
            ),
            AvgRewardsPerArm(
                arm_id=2, avg_reward=0.7, arm_description="", n_observations=20
            ),
            AvgRewardsPerArm(
                arm_id=3, avg_reward=0.3, arm_description="", n_observations=20
            ),
        ]
        with patch(
            "maybee_backend.bandits.epsilon_greedy.get_average_rewards_per_arm",
            return_value=mock_rewards,
        ):
            with patch(
                "random.choice", return_value=mock_rewards[1]
            ):  # Always choose the second arm
                bandit_state, arm_id = bandit.choose_arm()

    print(f"{bandit_state=} {arm_id=}")
    assert bandit_state == BanditState.EXPLORE
    assert arm_id == 1  # The randomly chosen arm


# def test_epsilon_greedy_bandit_epsilon_boundary():
#     bandit = EpsilonGreedyBandit(environment_id=1, epsilon=0.5)

#     # Test exactly at the epsilon boundary
#     with patch('random.uniform', return_value=0.5):
#         with patch('maybee_backend.bandits.epsilon_greedy.get_average_rewards_per_arm', return_value=[AvgRewardsPerArm(arm_id=1, avg_reward=0.5)]):
#             bandit_state, _ = bandit.choose_arm()

#     assert bandit_state == BanditState.EXPLOIT


def test_epsilon_greedy_bandit_no_rewards(session: Session):
    bandit = EpsilonGreedyBandit(session=session, environment_id=1, epsilon=0.1)

    # Mock get_average_rewards_per_arm to return empty list
    with patch("random.uniform", return_value=0.2):
        with patch(
            "maybee_backend.bandits.epsilon_greedy.get_average_rewards_per_arm",
            return_value=[],
        ):
            with pytest.raises(IndexError):
                bandit.choose_arm()
