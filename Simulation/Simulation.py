"""Deterministic kinematic simulation for AURA differential drive."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, sin
from Core.Parameters import AURAParameters, DEFAULT_PARAMETERS


@dataclass(frozen=True, slots=True)
class RobotState:
    x_mm: float = 0.0
    y_mm: float = 0.0
    yaw_rad: float = 0.0


@dataclass(frozen=True, slots=True)
class WheelCommand:
    left_mm_s: float
    right_mm_s: float


@dataclass(frozen=True, slots=True)
class SimulationStep:
    state: RobotState
    linear_velocity_mm_s: float
    angular_velocity_rad_s: float


class DifferentialDriveSimulator:
    """Small-step, deterministic differential-drive kinematic model."""

    def __init__(self, parameters: AURAParameters = DEFAULT_PARAMETERS, state: RobotState = RobotState()) -> None:
        self.parameters = parameters
        self.state = state

    def step(self, command: WheelCommand, dt_s: float) -> SimulationStep:
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")
        track = self.parameters.wheels.track_width_mm
        v = (command.left_mm_s + command.right_mm_s) / 2.0
        omega = (command.right_mm_s - command.left_mm_s) / track
        next_state = RobotState(
            x_mm=self.state.x_mm + v * cos(self.state.yaw_rad) * dt_s,
            y_mm=self.state.y_mm + v * sin(self.state.yaw_rad) * dt_s,
            yaw_rad=self.state.yaw_rad + omega * dt_s,
        )
        self.state = next_state
        return SimulationStep(next_state, v, omega)

    def reset(self, state: RobotState = RobotState()) -> None:
        self.state = state
