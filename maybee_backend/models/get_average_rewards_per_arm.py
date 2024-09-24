#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlmodel import select, Session
from sqlalchemy import func
from maybee_backend.models.core_models import (
    Arm,
    Observation,
    AvgRewardsPerArm,
)


def get_average_rewards_per_arm(
    session: Session,
    environment_id: int,
    replace_null_rewards_with_zeros=False,
):
    sql = (
        select(
            Arm.arm_id,
            Arm.arm_description,
            func.count(Observation.observation_id).label("n_observations"),
            func.coalesce(
                func.avg(Observation.reward),
                0.0 if replace_null_rewards_with_zeros else None,
            ).label("avg_reward"),
        )
        .join(
            Observation,
            Arm.arm_id == Observation.arm_id,
            isouter=True,
        )
        .where(Arm.environment_id == environment_id)
        .group_by(Arm.arm_id)
    )
    results = session.exec(sql).all()
    return [
        AvgRewardsPerArm(
            arm_id=row.arm_id,
            arm_description=row.arm_description,
            n_observations=row.n_observations,
            avg_reward=row.avg_reward,
        )
        for row in results
    ]
