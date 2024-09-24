#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlmodel import select, Session

from maybee_backend.models.core_models import (
    Environment,
    EnvironmentBanditConfig,
    Bandit,
)
from maybee_backend.bandits.epsilon_greedy import EpsilonGreedyBandit
from maybee_backend.bandits.softmax import SoftmaxBandit
from maybee_backend.bandits.ucb1 import UCB1Bandit
from maybee_backend.logging import log


environment_bandit_config_to_bandit_mapping = {
    EnvironmentBanditConfig.EPSILON_GREEDY: EpsilonGreedyBandit,
    EnvironmentBanditConfig.SOFTMAX: SoftmaxBandit,
    EnvironmentBanditConfig.UCB1: UCB1Bandit,
}


def get_bandit(environment_id: int, session: Session) -> Bandit:
    """
    Create the bandit configured for the given environment.
    """

    sql = select(Environment.bandit_type).where(
        Environment.environment_id == environment_id
    )
    bandit_type = session.exec(sql).first()

    log.debug(f"retrieved {bandit_type=} from {environment_id=}")

    bandit = environment_bandit_config_to_bandit_mapping.get(
        bandit_type, EpsilonGreedyBandit
    )
    return bandit(session=session, environment_id=environment_id)
