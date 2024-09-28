#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlmodel import Session, select, and_
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from maybee_backend.models.core_models import (
    Environment,
    EnvironmentBanditConfig,
    Action,
    Arm,
    Observation,
)
from maybee_backend.database import get_session
from maybee_backend.models.get_average_rewards_per_arm import (
    get_average_rewards_per_arm as query_average_rewards_per_arm,
)
from maybee_backend.bandits.epsilon_greedy import EpsilonGreedyBandit
from maybee_backend.api.sorting_mode import SortingMode
from maybee_backend.models.user_models import (
    User,
    Token,
    TokenData,
    UserCreationResponse,
    UserEnvironmentLink,
)


from maybee_backend.config import Config, get_config


# security settings
security_algorithm = "HS256"
access_token_expiration_time_mins = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
token_url = "/users/token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{token_url}")

router = APIRouter()


def raise_user_is_not_an_admin_exception() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User is not an admin",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_no_access_to_environment_exception(environment_id: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"User is not an admin, and does not have access to environment with id {environment_id}",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_user(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()


def authenticate_user(session: Session, username: str, password: str) -> Optional[User]:
    user = get_user(session, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    config: Config = Depends(get_config),
):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=access_token_expiration_time_mins)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=security_algorithm)
    return encoded_jwt


def raise_error_if_user_doesnt_have_link_to_environment(
    user_id, environment_id, session: Session = Depends(get_session)
):
    sql = select(UserEnvironmentLink).where(
        and_(
            UserEnvironmentLink.user_id == user_id,
            UserEnvironmentLink.environment_id == environment_id,
        )
    )
    user_environment_link = session.exec(sql).first()
    # raise an exception when user doesn't have access
    if not user_environment_link:
        raise_no_access_to_environment_exception(environment_id=environment_id)


async def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
    config: Config = Depends(get_config),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[security_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@router.get("/health", tags=[])
async def get_health():
    """
    Return a heartbeat.
    """
    return JSONResponse(content={"status": "ok"})


@router.post(
    "/users/register",
    response_model=UserCreationResponse,
    tags=[],
)
def register_user(
    username: str = Body(examples=["example_username"]),
    password: str = Body(examples=["example_password"]),
    session: Session = Depends(get_session),
):
    sql = select(User).where(User.username == username)
    existing_user = session.exec(sql).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this username already exists.",
        )

    password_hash = get_password_hash(password)
    user = User(
        username=username,
        password_hash=password_hash,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    user_creation_response = UserCreationResponse(
        user_id=user.user_id, username=user.username
    )
    return user_creation_response


@router.post(token_url, response_model=Token, tags=[])
def login_for_access_token(
    config: Config = Depends(get_config),
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username}, config=config)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/environments", tags=[])
async def create_environment(
    environment_description=None,
    is_simulation_environment: Optional[bool] = False,
    bandit_type: Optional[
        EnvironmentBanditConfig
    ] = EnvironmentBanditConfig.EPSILON_GREEDY,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Creates a new environment
    """

    def _create_environment(session: Session = session):
        environment = Environment(
            environment_description=environment_description,
            is_simulation_environment=is_simulation_environment,
            bandit_type=bandit_type,
        )

        session.add(environment)
        session.commit()
        session.refresh(environment)
        user_environment_link = UserEnvironmentLink(
            environment_id=environment.environment_id,
            user_id=current_user.user_id,
        )
        session.add(user_environment_link)
        session.commit()
        session.refresh(user_environment_link)
        return environment

    if current_user.is_admin:
        return _create_environment()
    raise_user_is_not_an_admin_exception()


@router.get("/environments", tags=[])
async def get_environments(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return a list of environments
    """
    sql = select(Environment)

    if not current_user.is_admin:
        sql = sql.join(
            UserEnvironmentLink,
            UserEnvironmentLink.environment_id == Environment.environment_id,
        ).where(UserEnvironmentLink.user_id == current_user.user_id)
    return session.exec(sql).all()


@router.put("/environments/{environment_id}", tags=[])
async def update_environment(
    environment_id: int,
    environment_description: Optional[str] = Body(None),
    bandit_type: Optional[EnvironmentBanditConfig] = Body(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Update an existing environment
    """
    if not current_user.is_admin:
        raise_user_is_not_an_admin_exception()

    sql = select(Environment).where(Environment.environment_id == environment_id)
    environment = session.exec(sql).first()

    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment with id {environment_id} not found",
        )

    if environment_description is not None:
        environment.environment_description = environment_description
    if bandit_type is not None:
        environment.bandit_type = bandit_type

    session.add(environment)
    session.commit()
    session.refresh(environment)
    return environment


@router.delete("/environments/{environment_id}", tags=[])
async def delete_environment(
    environment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Delete an environment
    """

    def _delete_environment():
        sql = select(Environment).where(Environment.environment_id == environment_id)
        environment = session.exec(sql).first()
        session.delete(environment)
        session.commit()

    if current_user.is_admin:
        return _delete_environment()
    raise_user_is_not_an_admin_exception()


@router.get("/environments/{environment_id}/arms", tags=[])
async def get_arms(
    environment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return a list of arms associated with a given environment.
    """
    if current_user.is_admin:
        sql = select(Arm).where(Arm.environment_id == environment_id)
        return session.exec(sql).all()
    else:
        sql = (
            select(Arm)
            .join(
                UserEnvironmentLink,
                UserEnvironmentLink.environment_id == Arm.environment_id,
            )
            .where(UserEnvironmentLink.user_id == current_user.user_id)
        )
        return session.exec(sql).all()


@router.get("/environments/{environment_id}/arms/{arm_id}", tags=[])
async def get_arm(
    environment_id: int,
    arm_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return a list of arms associated with a given environment.
    """
    if current_user.is_admin:
        sql = select(Arm).where(Arm.environment_id == environment_id).where(Arm.arm_id == arm_id)
        return session.exec(sql).first()
    else:
        sql = (
            select(Arm)
            .join(
                UserEnvironmentLink,
                UserEnvironmentLink.environment_id == Arm.environment_id,
            )
            .where(UserEnvironmentLink.user_id == current_user.user_id)
            .where(Arm.arm_id == arm_id)
        )
        return session.exec(sql).first()


@router.post("/environments/{environment_id}/arms", tags=[])
async def create_arm(
    environment_id: int,
    arm_description: Optional[str] = None,
    population_p_success: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Return a list of arms associated with a given environment.
    """

    def _create_arm():
        """
        Create the arm in the db
        """
        arm = Arm(
            environment_id=environment_id,
            arm_description=arm_description,
            population_p_success=population_p_success,
        )
        session.add(arm)
        session.commit()
        session.refresh(arm)
        return arm

    if current_user.is_admin:
        _create_arm()
    else:
        raise_error_if_user_doesnt_have_link_to_environment(
            user_id=current_user.user_id, environment_id=environment_id
        )
        _create_arm()


@router.delete("/environments/{environment_id}/arms/{arm_id}", tags=[])
async def delete_arm(
    arm_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Delete an arm
    """

    def _delete_arm():
        """
        Delete the arm in the db
        """
        sql = select(Arm).where(Arm.arm_id == arm_id)
        arm = session.exec(sql).first()
        session.delete(arm)
        session.commit()
        return arm

    if current_user.is_admin:
        _delete_arm()

    sql = select(Arm).where(Arm.arm_id == arm_id)
    arm = session.exec(sql).first()
    raise_error_if_user_doesnt_have_link_to_environment(
        user_id=current_user.user_id, environment_id=arm.environment_id
    )
    _delete_arm()


@router.get(
    "/environments/{environment_id}/observations",
    tags=[],
)
async def get_observations(
    environment_id: int,
    sorting_mode: Optional[SortingMode] = None,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    For a given environment, get the observations
    """

    def _get_observations():
        sql = select(Observation).where(Observation.environment_id == environment_id)
        if sorting_mode == SortingMode.EARLIEST:
            sql = sql.order_by(Observation.event_datetime.asc())
        elif sorting_mode == SortingMode.LATEST:
            sql = sql.order_by(Observation.event_datetime.desc())
        if limit:
            sql = sql.limit(limit)
        results = session.exec(sql).all()
        return results

    if current_user.is_admin:
        _get_observations()

    raise_error_if_user_doesnt_have_link_to_environment(
        user_id=current_user.user_id, environment_id=environment_id
    )
    return _get_observations()


@router.get(
    "/environments/{environment_id}/arms/average_rewards",
    tags=[],
)
async def get_average_rewards_per_arm(
    environment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    For a given environment, get the average rewards for each arm
    """
    if current_user.is_admin:
        return query_average_rewards_per_arm(environment_id=environment_id)
    raise_error_if_user_doesnt_have_link_to_environment(
        user_id=current_user.user_id, environment_id=environment_id
    )
    return query_average_rewards_per_arm(environment_id=environment_id)


@router.get(
    "/environments/{environment_id}/actions",
    tags=[],
)
async def get_actions(
    environment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get a list of actions in the given environment
    """

    def _get_actions():
        sql = select(Action).where(Action.environment_id == environment_id)
        results = session.exec(sql).all()
        return results

    if current_user.is_admin:
        return _get_actions()
    raise_error_if_user_doesnt_have_link_to_environment(
        user_id=current_user.user_id, environment_id=environment_id
    )
    return _get_actions()


@router.post(
    "/environments/{environment_id}/actions",
    tags=[],
)
async def act(
    environment_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Choose an arm for a given environment.
    Produces an action.
    """

    def _act():
        sql = select(Environment).where(Environment.environment_id == environment_id)
        environment = session.exec(sql).first()

        bandit_classes = {"epsilon_greedy": EpsilonGreedyBandit}
        bandit_class = bandit_classes.get(environment.bandit_type, EpsilonGreedyBandit)

        bandit = bandit_class(environment_id=environment_id, session=session)
        bandit_state, arm_id = bandit.choose_arm()
        action = Action(
            environment_id=environment_id,
            arm_id=arm_id,
            bandit_state=bandit_state.value,
        )
        session.add(action)
        session.commit()
        session.refresh(action)
        return action

    if current_user.is_admin:
        return _act()
    raise_error_if_user_doesnt_have_link_to_environment(
        user_id=current_user.user_id, environment_id=environment_id
    )
    return _act()


@router.post(
    "/environments/{environment_id}/observations",
    tags=[],
)
async def create_observation(
    environment_id: int,
    action_id: str,
    action_id: int,
    reward: float,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Create an observation of the outcome of a given action.
    """

    def _create_observation():
        observation = Observation(
            environment_id=environment_id, action_id=action_id, reward=reward
        )
        session.add(observation)
        session.commit()
        session.refresh(observation)
        return observation

    if current_user.is_admin:
        return _create_observation()
    raise_error_if_user_doesnt_have_link_to_environment(
        user_id=current_user.user_id, environment_id=environment_id
    )
    return _create_observation()
