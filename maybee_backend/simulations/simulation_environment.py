#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlmodel import select, Session
import random
from maybee_backend.models.core_models import (
    Environment,
    Arm,
    EnvironmentBanditConfig,
)
from maybee_backend.bandits.get_bandit import get_bandit
from maybee_backend.logging import log


def add_simulation_environment(
    session: Session,
    n_arms=3,
    n_observations=2500,
    bandit_type: EnvironmentBanditConfig = EnvironmentBanditConfig.EPSILON_GREEDY,
):
    """
    Create an simulation environment, populate it with some arms, actions and observations
    """
    log.info(
        f"Start adding simulation environment with {bandit_type=}, {n_arms=}, {n_observations=}"
    )
    random.seed(1)

    # create the simulation environment
    environment = Environment(
        environment_description=f"Simulation environment with {bandit_type=}",
        bandit_type=bandit_type,
        is_simulation_environment=True,
    )
    session.add(environment)
    session.commit()
    session.refresh(environment)
    arms = [
        Arm(
            environment_id=environment.environment_id,
            arm_description=f"example arm {i}",
            population_p_success=random.uniform(0, 1),
        )
        for i in range(n_arms)
    ]

    # add the arms
    for arm in arms:
        session.add(arm)
    session.commit()
    for arm in arms:
        session.refresh(arm)
        log.info(f"Created new arm {arm=}")

    # have the bandit select and pull an arm n_observations amount of times
    bandit = get_bandit(session=session, environment_id=environment.environment_id)
    for i in range(n_observations):
        bandit_state, arm_id = bandit.choose_arm()
        sql = select(Arm).where(Arm.arm_id == arm_id)
        arm = session.exec(sql).first()

        arm.pull(
            session=session, bandit_state=bandit_state
        )  # this method sinks the Actions and Oberservations into the db
    log.info("Finished setting up simulation environment with {environment.id=}")
