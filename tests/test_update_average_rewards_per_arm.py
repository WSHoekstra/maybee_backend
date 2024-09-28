#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from sqlmodel import select, Session
from maybee_backend.models.core_models import update_average_rewards_per_arm
from maybee_backend.models.core_models import AvgRewardsPerArm
from tests.statics import TEST_ENVIRONMENT_ID, TEST_ARM_ID


@pytest.mark.usefixtures("environment", "arm", "avgrewardsperarm")
def test_update_average_rewards_per_arm(session: Session):
    """
    Tests that the n_observations and avg_reward get updated correctly
    """
    # starting point: 1 observation, avg reward 1.0
    update_average_rewards_per_arm(session=session, environment_id=TEST_ENVIRONMENT_ID, arm_id=TEST_ARM_ID, n_new_observations=10, avg_reward_of_new_observations=0.8)    
    sql = select(AvgRewardsPerArm).where(AvgRewardsPerArm.environment_id==TEST_ENVIRONMENT_ID).where(AvgRewardsPerArm.arm_id==TEST_ARM_ID)
    avg_rewards_per_arm = session.exec(sql).first()
    assert avg_rewards_per_arm.n_observations == 11
    assert avg_rewards_per_arm.avg_reward == (9 / 11)
    
