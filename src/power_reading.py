"""PowerReading — immutable snapshot of a single meter measurement."""

from __future__ import annotations
from datetime import datetime
from functools import total_ordering


@total_ordering
class PowerReading:
    """Immutable snapshot: meter_id, kwh, voltage, current, timestamp.

    Supports full dunder suite so readings can be summed and sorted.
    __add__ and __radd__ allow sum(meter.readings) to accumulate kWh totals.
    """

    def __init__(
        self,
        meter_id: str,
        kwh: float,
        voltage: float,
        current: float,
        timestamp: datetime,
    ):
        """Initialise a PowerReading snapshot."""
        if not isinstance(meter_id, str) or not meter_id.strip():
            raise ValueError("meter_id must be a non-empty string")
        if not isinstance(timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")
        # Store as private to enforce immutability
        self._meter_id = meter_id
        self._kwh = float(kwh)
        self._voltage = float(voltage)
        self._current = float(current)
        self._timestamp = timestamp

    @property
    def meter_id(self) -> str:
        """Unique meter identifier."""
        return self._meter_id

    @property
    def kwh(self) -> float:
        """Energy consumed in kilowatt-hours."""
        return self._kwh

    @property
    def voltage(self) -> float:
        """Voltage at time of reading in volts."""
        return self._voltage

    @property
    def current(self) -> float:
        """Current at time of reading in amperes."""
        return self._current

    @property
    def timestamp(self) -> datetime:
        """UTC datetime of the reading."""
        return self._timestamp

    # --- dunder suite -------------------------------------------------------

    def __add__(self, other: "PowerReading | int | float") -> "PowerReading":
        """Add two readings; the result inherits this reading's metadata."""
        if isinstance(other, (int, float)):
            return PowerReading(
                self._meter_id, self._kwh + other,
                self._voltage, self._current, self._timestamp,
            )
        if isinstance(other, PowerReading):
            return PowerReading(
                self._meter_id, self._kwh + other._kwh,
                self._voltage, self._current, self._timestamp,
            )
        return NotImplemented

    def __radd__(self, other: "PowerReading | int | float") -> "PowerReading":
        """Support sum() which starts with integer 0."""
        if isinstance(other, (int, float)):
            return PowerReading(
                self._meter_id, self._kwh + other,
                self._voltage, self._current, self._timestamp,
            )
        return self.__add__(other)

    def __eq__(self, other: object) -> bool:
        """Two readings are equal if they have the same kwh value."""
        if isinstance(other, PowerReading):
            return self._kwh == other._kwh
        return NotImplemented

    def __lt__(self, other: "PowerReading") -> bool:
        """Ordering is by kwh value."""
        if isinstance(other, PowerReading):
            return self._kwh < other._kwh
        return NotImplemented

    def __hash__(self) -> int:
        """Hash based on meter_id and timestamp for use in sets/dicts."""
        return hash((self._meter_id, self._timestamp))

    def __str__(self) -> str:
        return (
            f"PowerReading({self._meter_id} | {self._kwh:.3f} kWh | "
            f"{self._voltage:.1f} V | {self._current:.2f} A | "
            f"{self._timestamp.strftime('%Y-%m-%d %H:%M')})"
        )

    def __repr__(self) -> str:
        return (
            f"PowerReading(meter_id={self._meter_id!r}, kwh={self._kwh!r}, "
            f"voltage={self._voltage!r}, current={self._current!r}, "
            f"timestamp={self._timestamp!r})"
        )
