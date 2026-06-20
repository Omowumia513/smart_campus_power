"""BuildingZone — aggregates multiple MeterDevice instances in one campus zone."""

from __future__ import annotations
from typing import Iterator, List

from src.meters import MeterDevice
from src.power_reading import PowerReading
from datetime import datetime


class BuildingZone:
    """Represents a functional zone on campus that aggregates several meters.

    Examples: 'Male Hostel Block A', 'Physics Lab', 'Admin Block'.
    Meters are aggregated (not owned) — they can exist independently.

    Supports:
    - __len__: number of meters in the zone.
    - __contains__: test by meter_id string or MeterDevice object.
    - __iter__: iterate over meters.
    """

    ZONE_TYPES = frozenset({"HOSTEL", "LABORATORY", "LECTURE_THEATRE", "ADMIN", "SOLAR"})

    def __init__(self, name: str, zone_type: str):
        """Initialise a BuildingZone with a name and zone type."""
        self.name = name
        self.zone_type = zone_type
        self._meters: List[MeterDevice] = []

    # --- validated properties -----------------------------------------------

    @property
    def name(self) -> str:
        """Human-readable zone name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("name must be a non-empty string")
        self._name = value.strip()

    @property
    def zone_type(self) -> str:
        """Classification of the zone (HOSTEL, LABORATORY, etc.)."""
        return self._zone_type

    @zone_type.setter
    def zone_type(self, value: str) -> None:
        if value not in self.ZONE_TYPES:
            raise ValueError(
                f"zone_type must be one of {sorted(self.ZONE_TYPES)}, got {value!r}"
            )
        self._zone_type = value

    # --- meter management ---------------------------------------------------

    def add_meter(self, meter: MeterDevice) -> None:
        """Add a meter to this zone (aggregation — meter is not owned)."""
        if not isinstance(meter, MeterDevice):
            raise TypeError("meter must be a MeterDevice instance")
        self._meters.append(meter)

    def remove_meter(self, meter_id: str) -> None:
        """Remove a meter by its meter_id."""
        self._meters = [m for m in self._meters if m.meter_id != meter_id]

    # --- aggregate computations ---------------------------------------------

    def compute_zone_total(self) -> PowerReading:
        """Sum all readings from all meters in this zone into one PowerReading.

        Returns a synthetic PowerReading with meter_id equal to the zone name.
        If no readings exist, returns a zero-reading PowerReading.
        """
        total_kwh = sum(m.total_kwh() for m in self._meters)
        # Use current timestamp and nominal voltage for the synthetic reading
        avg_voltage = (
            sum(m.voltage_rating for m in self._meters) / len(self._meters)
            if self._meters else 230.0
        )
        return PowerReading(
            meter_id=self._name,
            kwh=total_kwh,
            voltage=avg_voltage,
            current=0.0,
            timestamp=datetime.now(),
        )

    def active_alert_count(self, campus_alerts: list) -> int:
        """Count alerts in campus_alerts that belong to meters in this zone."""
        my_ids = {m.meter_id for m in self._meters}
        return sum(1 for a in campus_alerts if a.meter_id in my_ids)

    # --- dunder methods -----------------------------------------------------

    def __len__(self) -> int:
        """Number of meters in this zone."""
        return len(self._meters)

    def __contains__(self, item: "str | MeterDevice") -> bool:
        """Test by meter_id string or MeterDevice object."""
        if isinstance(item, str):
            return any(m.meter_id == item for m in self._meters)
        if isinstance(item, MeterDevice):
            return item in self._meters
        return False

    def __iter__(self) -> Iterator[MeterDevice]:
        """Iterate over all meters in this zone."""
        return iter(self._meters)

    def __str__(self) -> str:
        return (
            f"BuildingZone({self._name!r}, type={self._zone_type}, "
            f"meters={len(self._meters)})"
        )

    def __repr__(self) -> str:
        return (
            f"BuildingZone(name={self._name!r}, zone_type={self._zone_type!r})"
        )
