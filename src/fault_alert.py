"""FaultAlert — severity-tiered alert for campus power fault events."""

from __future__ import annotations
from datetime import datetime
from functools import total_ordering


# Numeric severity: lower number = higher priority (CRITICAL=0, WARNING=1, INFO=2)
_SEVERITY_ORDER = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
_VALID_SEVERITIES = frozenset(_SEVERITY_ORDER)


@total_ordering
class FaultAlert:
    """Records a fault event with severity, message, meter_id, and timestamp.

    __lt__ orders CRITICAL < WARNING < INFO so that sorted() places the most
    urgent alerts first when used in a priority queue.
    """

    def __init__(
        self,
        severity: str,
        message: str,
        meter_id: str,
        timestamp: datetime | None = None,
    ):
        """Initialise a FaultAlert with validated severity."""
        if severity not in _VALID_SEVERITIES:
            raise ValueError(
                f"severity must be one of {sorted(_VALID_SEVERITIES)}, got {severity!r}"
            )
        self._severity = severity
        self._message = message
        self._meter_id = meter_id
        self._timestamp = timestamp or datetime.now()

    @property
    def severity(self) -> str:
        """Severity level: INFO, WARNING, or CRITICAL."""
        return self._severity

    @property
    def message(self) -> str:
        """Human-readable description of the fault."""
        return self._message

    @property
    def meter_id(self) -> str:
        """ID of the meter that raised this alert."""
        return self._meter_id

    @property
    def timestamp(self) -> datetime:
        """Datetime when the fault was detected."""
        return self._timestamp

    # --- ordering -----------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """Two alerts are equal when severity, meter_id, and message match."""
        if isinstance(other, FaultAlert):
            return (
                self._severity == other._severity
                and self._meter_id == other._meter_id
                and self._message == other._message
            )
        return NotImplemented

    def __lt__(self, other: "FaultAlert") -> bool:
        """CRITICAL < WARNING < INFO for priority-queue ordering."""
        if isinstance(other, FaultAlert):
            return _SEVERITY_ORDER[self._severity] < _SEVERITY_ORDER[other._severity]
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._severity, self._meter_id, self._timestamp))

    def __str__(self) -> str:
        ts = self._timestamp.strftime("%Y-%m-%d %H:%M")
        return f"[{self._severity}] {ts} | {self._meter_id} | {self._message}"

    def __repr__(self) -> str:
        return (
            f"FaultAlert(severity={self._severity!r}, "
            f"message={self._message!r}, meter_id={self._meter_id!r}, "
            f"timestamp={self._timestamp!r})"
        )
