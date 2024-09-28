#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlmodel import select, Session
from sqlalchemy import func
from maybee_backend.models.core_models import (
    Arm,
    AvgRewardsPerArm,
)


def get_average_rewards_per_arm(
    session: Session,
    environment_id: int,
    replace_null_rewards_with_zeros=False,
):
    sql = (
        select( 
               AvgRewardsPerArm.avg_rewards_per_arm_id,
               AvgRewardsPerArm.environment_id,
               AvgRewardsPerArm.arm_id, 
               Arm.arm_description,
               func.coalesce(
                AvgRewardsPerArm.avg_reward,
                0.0 if replace_null_rewards_with_zeros else None,
            ).label("avg_reward"),
               AvgRewardsPerArm.avg_reward,
               ).join(
            Arm,
            Arm.arm_id == AvgRewardsPerArm.arm_id,
            isouter=False,
        ).where(AvgRewardsPerArm.environment_id == environment_id)
    )
    results = session.exec(sql).all()
    return results
