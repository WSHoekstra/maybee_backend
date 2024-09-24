#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sqlmodel import (
    Field,
    SQLModel,
    CheckConstraint,
    select,
    Relationship,
    Session,
)

import datetime
from typing import Optional, List, Tuple
import numpy as np
from enum import Enum


class EnvironmentBanditConfig(str, Enum):
    SOFTMAX = "softmax"
    EPSILON_GREEDY = "epsilon_greedy"
    UCB1 = "ucb1"


class Environment(SQLModel, table=True):
    """
    Represents the isolated environment to which one or more arms belong.
    """

    environment_id: int | None = Field(default=None, primary_key=True)
    environment_description: Optional[str]
    is_simulation_environment: bool = Field(default=False)
    bandit_type: Optional[EnvironmentBanditConfig] = Field(
        default=EnvironmentBanditConfig.EPSILON_GREEDY
    )
    environment_create_datetime: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )

    # relationships where this is the parent
    arms: List["Arm"] = Relationship(back_populates="environment", cascade_delete=True)

    actions: List["Action"] = Relationship(
        back_populates="environment", cascade_delete=True
    )

    observations: List["Observation"] = Relationship(
        back_populates="environment", cascade_delete=True
    )


class BanditState(Enum):
    TESTMODE = "TESTMODE"
    EXPLORE = "EXPLORE"
    EXPLOIT = "EXPLOIT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NO_ARMS_AVAILABLE = "NO_ARMS_AVAILABLE"
    UNDEFINED = "UNDEFINED"


class Arm(SQLModel, table=True):
    """
    Represents an arm that belongs to a particular environment.
    """

    __table_args__ = (
        CheckConstraint(
            "population_p_success IS NULL OR (population_p_success >= 0 AND population_p_success <= 1)",
            name="check_population_p_success_range",
        ),
    )

    arm_id: int | None = Field(default=None, primary_key=True)
    environment_id: int | None = Field(
        default=None,
        foreign_key="environment.environment_id",
        ondelete="CASCADE",
    )
    arm_description: Optional[str]
    create_datetime: datetime.datetime = Field(default_factory=datetime.datetime.now)
    active_start_datetime: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    population_p_success: Optional[float] = Field(
        default=None
    )  # only applicable when Environment.is_simulation_environment = True
    # active_end_datetime: datetime.datetime | None = Field(default=None)

    # relationships where this is the child
    environment: Environment | None = Relationship(back_populates="arms")

    # relationships where this  is the parent
    actions: List["Action"] = Relationship(back_populates="arm", cascade_delete=True)

    observations: List["Observation"] = Relationship(
        back_populates="arm", cascade_delete=True
    )

    def pull(
        self,
        session: Session,
        bandit_state: BanditState = BanditState.UNDEFINED,
    ) -> None:
        """
        Only available for simulation environments,
        for arms that have a defined population_p_success.

        Generate an action and a observation with a reward of 0.0 or 1.0
        with probability self.population_p_success
        """
        sql = select(Environment.is_simulation_environment).where(
            Environment.environment_id == self.environment_id
        )
        is_simulation_environment = session.exec(sql).first()
        if not is_simulation_environment:
            raise ValueError("environment is not a simulation environment")
        if not self.population_p_success:
            raise ValueError(
                f"environment is a simulation environment, but population_p_success is undefined for arm with id {self.arm_id}"
            )
        else:
            reward = int(np.random.binomial(n=1, p=self.population_p_success))

            action = Action(
                arm_id=self.arm_id,
                environment_id=self.environment_id,
                bandit_state=bandit_state.value,
            )
            session.add(action)
            session.commit()
            session.refresh(action)

            observation = Observation(
                environment_id=self.environment_id,
                arm_id=self.arm_id,
                action_id=action.action_id,
                reward=reward,
            )
            session.add(observation)
            session.commit()


class Action(SQLModel, table=True):
    """
    Represents the choice of a particular arm within a particular environment.
    """

    action_id: int | None = Field(default=None, primary_key=True)
    environment_id: int | None = Field(
        default=None, foreign_key="environment.environment_id"
    )
    arm_id: int | None = Field(default=None, foreign_key="arm.arm_id")
    event_datetime: datetime.datetime = Field(default_factory=datetime.datetime.now)
    bandit_state: str

    # relationships where this is the child
    environment: Environment | None = Relationship(back_populates="actions")
    arm: Arm | None = Relationship(back_populates="actions")

    # relationships where this is the parent
    observations: List["Observation"] = Relationship(
        back_populates="action", cascade_delete=True
    )


class Observation(SQLModel, table=True):
    """
    Represents the observation of the outcome of an action.
    May or may not come with a reward.
    """

    observation_id: int | None = Field(default=None, primary_key=True)
    environment_id: int | None = Field(
        default=None, foreign_key="environment.environment_id"
    )
    arm_id: int | None = Field(default=None, foreign_key="arm.arm_id")
    action_id: int | None = Field(default=None, foreign_key="action.action_id")
    event_datetime: datetime.datetime = Field(default_factory=datetime.datetime.now)
    reward: float

    # relationships where this is the child
    environment: Environment | None = Relationship(back_populates="observations")
    arm: Arm | None = Relationship(back_populates="observations")
    action: Action | None = Relationship(back_populates="observations")


class AvgRewardsPerArm(SQLModel, table=False):
    arm_id: int
    arm_description: Optional[str]
    n_observations: Optional[int]
    avg_reward: Optional[float]


class Bandit:
    """
    Superclass for multi armed bandit.
    """

    def __init__(self, environment_id, session: Session):
        self.environment_id = environment_id
        self.session = session

    def get_arms(self) -> List[Arm]:
        """
        Return a list of all the arms that are available
        in the bandit's environment.
        """
        sql = select(Arm.arm_id).where(Arm.environment_id == self.environment_id)
        arms = self.session.exec(sql).all()
        return arms

    def choose_arm(self) -> Tuple[BanditState, int]:
        raise NotImplementedError
