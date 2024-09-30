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

    avg_rewards_per_arm: List["AvgRewardsPerArm"] = Relationship(
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

    avg_rewards_per_arm: List["AvgRewardsPerArm"] = Relationship(
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

        update_average_rewards_per_arm(session=session, environment_id=self.environment_id, arm_id=self.arm_id, n_new_observations=1, avg_reward_of_new_observations=reward)


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
    

class ObservationCreate(SQLModel, table=False):
    environment_id: int | None = Field(
        default=None, foreign_key="environment.environment_id"
    )
    arm_id: int | None = Field(default=None, foreign_key="arm.arm_id")
    action_id: int | None = Field(default=None, foreign_key="action.action_id")
    event_datetime: datetime.datetime = Field(default_factory=datetime.datetime.now)
    reward: float


class AvgRewardsPerArm(SQLModel, table=True):
    avg_rewards_per_arm_id: int | None = Field(default=None, primary_key=True)
    environment_id: int | None = Field(default=None, foreign_key="environment.environment_id")
    arm_id: int | None = Field(default=None, foreign_key="arm.arm_id")
    n_observations: Optional[int]
    avg_reward: Optional[float]

    # relationships where this is the child
    environment: Environment | None = Relationship(back_populates="avg_rewards_per_arm")
    arm: Arm | None = Relationship(back_populates="avg_rewards_per_arm")


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


def update_average_rewards_per_arm(
    session: Session,
    environment_id: int,
    arm_id: int,
    n_new_observations: int,
    avg_reward_of_new_observations: float
) -> AvgRewardsPerArm:
    """
    Given some amount of new observations with an average reward,
    update the n_observations and average reward in AvgRewardsPerArm table
    """
    if not isinstance(n_new_observations, int):
        raise ValueError(f"n_new_observations must be of type int, received type {type(n_new_observations)}")

    if not n_new_observations > 0:
        raise ValueError(f"n_new_observations must be > 0, received value {n_new_observations}")

    if not isinstance(avg_reward_of_new_observations, float):
        raise ValueError(f"avg_reward_of_new_observations has to be of type float, received type {type(avg_reward_of_new_observations)}")
    
    sql = select(AvgRewardsPerArm).where(AvgRewardsPerArm.environment_id == environment_id).where(AvgRewardsPerArm.arm_id == arm_id)
    avg_rewards_per_arm = session.exec(sql).first()

    # if the object doesnt exist in the db yet, create a new one
    if not avg_rewards_per_arm:
        avg_rewards_per_arm = AvgRewardsPerArm(environment_id=environment_id,
                                               arm_id=arm_id,
                                            n_observations=n_new_observations, 
                                            avg_reward=avg_reward_of_new_observations)
    else: # the object already exists
        avg_rewards_per_arm.n_observations += n_new_observations
        avg_rewards_per_arm.avg_reward = (
            (avg_rewards_per_arm.avg_reward * (avg_rewards_per_arm.n_observations - n_new_observations)) + 
            (avg_reward_of_new_observations * n_new_observations)
        ) / avg_rewards_per_arm.n_observations
    
    session.add(avg_rewards_per_arm)
    session.commit()
    session.refresh(avg_rewards_per_arm)
    return avg_rewards_per_arm
