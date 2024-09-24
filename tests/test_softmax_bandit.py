#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from fastapi import Depends
from sqlmodel import Session
from maybee_backend.database import get_session
from unittest.mock import patch
from maybee_backend.bandits.softmax import SoftmaxBandit
from maybee_backend.models.core_models import BanditState, AvgRewardsPerArm


def test_softmax_bandit_initialization(session: Session = Depends(get_session)):
    bandit = SoftmaxBandit(session=session, environment_id=1, tau=0.1)
    assert isinstance(bandit, SoftmaxBandit)
    assert bandit.environment_id == 1
    assert bandit.tau == 0.1


def test_softmax_bandit_choose_arm(session: Session = Depends(get_session)):
    bandit = SoftmaxBandit(session=session, environment_id=1, tau=0.1)

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
        "maybee_backend.bandits.softmax.get_average_rewards_per_arm",
        return_value=mock_rewards,
    ):
        with patch(
            "numpy.random.choice", return_value=1
        ):  # Always choose the second arm
            bandit_state, arm_id = bandit.choose_arm()

    assert bandit_state == BanditState.NOT_APPLICABLE
    assert arm_id == 2  # The arm with index 1 (second arm)


def test_softmax_bandit_probability_distribution(
    session: Session = Depends(get_session),
):
    bandit = SoftmaxBandit(session=session, environment_id=1, tau=0.1)

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
        "maybee_backend.bandits.softmax.get_average_rewards_per_arm",
        return_value=mock_rewards,
    ):
        with patch("numpy.random.choice") as mock_choice:
            bandit.choose_arm()
            _, kwargs = mock_choice.call_args
            probs = kwargs["p"]

    assert len(probs) == 3
    assert sum(probs) == pytest.approx(1.0)
    assert (
        probs[1] > probs[0] > probs[2]
    )  # Probability should be highest for the arm with highest reward


def test_softmax_bandit_tau_effect(session: Session = Depends(get_session)):
    bandit_low_tau = SoftmaxBandit(session=session, environment_id=1, tau=0.01)
    bandit_high_tau = SoftmaxBandit(session=session, environment_id=1, tau=1.0)

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

    def get_probs(bandit):
        with patch(
            "maybee_backend.bandits.softmax.get_average_rewards_per_arm",
            return_value=mock_rewards,
        ):
            with patch("numpy.random.choice") as mock_choice:
                bandit.choose_arm()
                _, kwargs = mock_choice.call_args
                return kwargs["p"]

    probs_low_tau = get_probs(bandit_low_tau)
    probs_high_tau = get_probs(bandit_high_tau)

    assert max(probs_low_tau) > max(
        probs_high_tau
    )  # Lower tau should lead to more extreme probabilities


def test_softmax_bandit_no_rewards(session: Session = Depends(get_session)):
    bandit = SoftmaxBandit(session=session, environment_id=1, tau=0.1)

    with patch(
        "maybee_backend.bandits.softmax.get_average_rewards_per_arm", return_value=[]
    ):
        bandit_state, arm_id = bandit.choose_arm()

    assert bandit_state == BanditState.NO_ARMS_AVAILABLE
    assert arm_id is None
