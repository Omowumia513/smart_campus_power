"""Meter device class hierarchy for the Smart Campus Power Management System."""

from __future__ import annotations
import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List

from src.power_reading import PowerReading
from src.exceptions import OverloadError


class MeterDevice(ABC):
    """Abstract base class defining the shared interface for all campus meters.

    Every concrete meter must implement take_reading() and is_overloaded().
    Encapsulates meter_id, location, and voltage_rating as validated properties.
    """

    def __init__(self, meter_id: str, location: str, voltage_rating: float):
        """Initialise common meter attributes with validation."""
        self.meter_id = meter_id
        self.location = location
        self.voltage_rating = voltage_rating
        self._readings: List[PowerReading] = []
        self._flagged: bool = False

    # --- abstract properties ------------------------------------------------

    @property
    @abstractmethod
    def meter_id(self) -> str:
        """Unique identifier for this meter."""
        ...

    @meter_id.setter
    @abstractmethod
    def meter_id(self, value: str) -> None:
        ...

    @property
    @abstractmethod
    def location(self) -> str:
        """Physical location of the meter on campus."""
        ...

    @location.setter
    @abstractmethod
    def location(self, value: str) -> None:
        ...

    @property
    @abstractmethod
    def voltage_rating(self) -> float:
        """Rated operating voltage of this meter in volts."""
        ...

    @voltage_rating.setter
    @abstractmethod
    def voltage_rating(self, value: float) -> None:
        ...

    # --- abstract methods ---------------------------------------------------

    @abstractmethod
    def take_reading(self, current: float, timestamp: datetime) -> PowerReading:
        """Record a new power reading and return it."""
        ...

    @abstractmethod
    def is_overloaded(self) -> bool:
        """Return True if the latest reading exceeds 150% of rated capacity."""
        ...

    # --- concrete helpers shared by all subclasses --------------------------

    @property
    def readings(self) -> List[PowerReading]:
        """All readings recorded by this meter (read-only list)."""
        return list(self._readings)

    @property
    def flagged(self) -> bool:
        """True if this meter has been flagged for an overload fault."""
        return self._flagged

    def flag(self) -> None:
        """Mark this meter as faulted."""
        self._flagged = True

    def total_kwh(self) -> float:
        """Sum of all recorded kWh readings."""
        return sum(r.kwh for r in self._readings)

    def simulate_24h(
        self,
        base_current: float,
        start: datetime,
        overload_at_hour: int | None = None,
    ) -> List[PowerReading]:
        """Generate 15 hourly readings across a 24-hour period.

        If overload_at_hour is given, that reading's current will be set to
        2.0× rated capacity to deliberately trigger an OverloadError.
        """
        readings = []
        for i in range(15):
            ts = start + timedelta(hours=i)
            current = base_current
            if overload_at_hour is not None and ts.hour == overload_at_hour % 24:
                current = base_current * 2.0
            reading = self.take_reading(current, ts)
            readings.append(reading)
        return readings

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self._meter_id!r}, "
            f"location={self._location!r}, "
            f"rating={self._voltage_rating:.1f} V, "
            f"readings={len(self._readings)})"
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(meter_id={self._meter_id!r}, "
            f"location={self._location!r}, "
            f"voltage_rating={self._voltage_rating!r})"
        )


# ---------------------------------------------------------------------------
# Concrete meter subclasses
# ---------------------------------------------------------------------------

class SinglePhaseMeter(MeterDevice):
    """Meters hostels and offices using single-phase power formula P = V × I.

    Inherits from MeterDevice and provides concrete property implementations
    along with single-phase power calculations.
    """

    def __init__(self, meter_id: str, location: str, voltage_rating: float = 230.0):
        """Initialise a single-phase meter (default 230 V)."""
        super().__init__(meter_id, location, voltage_rating)

    # --- property implementations -------------------------------------------

    @property
    def meter_id(self) -> str:
        """Unique identifier for this meter."""
        return self._meter_id

    @meter_id.setter
    def meter_id(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("meter_id must be a non-empty string")
        self._meter_id = value.strip()

    @property
    def location(self) -> str:
        """Physical location of the meter on campus."""
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("location must be a non-empty string")
        self._location = value.strip()

    @property
    def voltage_rating(self) -> float:
        """Rated voltage in volts."""
        return self._voltage_rating

    @voltage_rating.setter
    def voltage_rating(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("voltage_rating must be a positive number")
        self._voltage_rating = float(value)

    # --- core methods -------------------------------------------------------

    def take_reading(self, current: float, timestamp: datetime) -> PowerReading:
        """Record a single-phase reading: power = V × I (converted to kWh per hour)."""
        if not isinstance(current, (int, float)) or current < 0:
            raise ValueError("current must be a non-negative number")
        power_w = self._voltage_rating * current          # watts
        kwh = power_w / 1000.0                            # 1-hour period
        reading = PowerReading(
            self._meter_id, kwh, self._voltage_rating, current, timestamp
        )
        self._readings.append(reading)
        return reading

    def is_overloaded(self) -> bool:
        """True if the latest reading's current exceeds 150% of rated capacity.

        Rated capacity in amps is derived from voltage_rating assuming nominal
        power of voltage_rating × 10 A as the design limit.
        """
        if not self._readings:
            return False
        latest = self._readings[-1]
        rated_current = 10.0  # nominal 10 A design limit for single-phase
        return latest.current > rated_current * 1.5


class ThreePhaseMeter(MeterDevice):
    """Meters laboratories and workshops using three-phase power: P = √3 × V × I × PF.

    Power factor (PF) defaults to 0.85, a typical inductive load value.
    """

    def __init__(
        self,
        meter_id: str,
        location: str,
        voltage_rating: float = 415.0,
        power_factor: float = 0.85,
    ):
        """Initialise a three-phase meter (default 415 V line voltage)."""
        self._power_factor = power_factor
        super().__init__(meter_id, location, voltage_rating)

    # --- property implementations -------------------------------------------

    @property
    def meter_id(self) -> str:
        """Unique identifier for this meter."""
        return self._meter_id

    @meter_id.setter
    def meter_id(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("meter_id must be a non-empty string")
        self._meter_id = value.strip()

    @property
    def location(self) -> str:
        """Physical location of the meter."""
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("location must be a non-empty string")
        self._location = value.strip()

    @property
    def voltage_rating(self) -> float:
        """Rated line-to-line voltage in volts."""
        return self._voltage_rating

    @voltage_rating.setter
    def voltage_rating(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("voltage_rating must be a positive number")
        self._voltage_rating = float(value)

    @property
    def power_factor(self) -> float:
        """Power factor (0 < PF ≤ 1)."""
        return self._power_factor

    # --- core methods -------------------------------------------------------

    def take_reading(self, current: float, timestamp: datetime) -> PowerReading:
        """Record a three-phase reading: P = √3 × V × I × PF (kWh per hour)."""
        if not isinstance(current, (int, float)) or current < 0:
            raise ValueError("current must be a non-negative number")
        power_w = math.sqrt(3) * self._voltage_rating * current * self._power_factor
        kwh = power_w / 1000.0
        reading = PowerReading(
            self._meter_id, kwh, self._voltage_rating, current, timestamp
        )
        self._readings.append(reading)
        return reading

    def is_overloaded(self) -> bool:
        """True if the latest current exceeds 150% of the 20 A rated limit."""
        if not self._readings:
            return False
        latest = self._readings[-1]
        rated_current = 20.0  # nominal design limit for three-phase
        return latest.current > rated_current * 1.5


class SolarFeedMeter(MeterDevice):
    """Tracks energy fed back into the campus grid by solar installations.

    kWh readings may be negative when generation exceeds local consumption.
    """

    def __init__(self, meter_id: str, location: str, voltage_rating: float = 230.0):
        """Initialise a solar feed meter."""
        super().__init__(meter_id, location, voltage_rating)

    # --- property implementations -------------------------------------------

    @property
    def meter_id(self) -> str:
        """Unique identifier for this meter."""
        return self._meter_id

    @meter_id.setter
    def meter_id(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("meter_id must be a non-empty string")
        self._meter_id = value.strip()

    @property
    def location(self) -> str:
        """Physical location of the solar panel cluster."""
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("location must be a non-empty string")
        self._location = value.strip()

    @property
    def voltage_rating(self) -> float:
        """Rated voltage in volts."""
        return self._voltage_rating

    @voltage_rating.setter
    def voltage_rating(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("voltage_rating must be a positive number")
        self._voltage_rating = float(value)

    # --- core methods -------------------------------------------------------

    def take_reading(self, current: float, timestamp: datetime) -> PowerReading:
        """Record a solar feed reading; negative current means net generation.

        kwh = V × |I| / 1000, sign follows the current sign.
        """
        if not isinstance(current, (int, float)):
            raise ValueError("current must be a number")
        kwh = (self._voltage_rating * current) / 1000.0
        reading = PowerReading(
            self._meter_id, kwh, self._voltage_rating, current, timestamp
        )
        self._readings.append(reading)
        return reading

    def is_overloaded(self) -> bool:
        """Solar feed meters cannot be overloaded in this model."""
        return False

    def net_export_kwh(self) -> float:
        """Total net energy exported to the grid (positive = net export)."""
        return -sum(r.kwh for r in self._readings)
