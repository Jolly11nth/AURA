import pytest

from Simulation.Simulation import DifferentialDriveSimulator, RobotState, WheelCommand


def test_straight_motion() -> None:
    sim = DifferentialDriveSimulator(state=RobotState())
    result = sim.step(WheelCommand(100.0, 100.0), 1.0)
    assert result.state.x_mm == pytest.approx(100.0)
    assert result.state.y_mm == pytest.approx(0.0)
    assert result.angular_velocity_rad_s == pytest.approx(0.0)


def test_in_place_rotation() -> None:
    sim = DifferentialDriveSimulator(state=RobotState())
    result = sim.step(WheelCommand(-50.0, 50.0), 1.0)
    expected = 100.0 / sim.parameters.wheels.track_width_mm
    assert result.state.x_mm == pytest.approx(0.0)
    assert result.state.y_mm == pytest.approx(0.0)
    assert result.state.yaw_rad == pytest.approx(expected)


def test_non_positive_timestep_rejected() -> None:
    sim = DifferentialDriveSimulator()
    with pytest.raises(ValueError):
        sim.step(WheelCommand(1.0, 1.0), 0.0)
