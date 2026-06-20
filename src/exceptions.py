"""Custom exception hierarchy for the Smart Campus Power Management System."""

from datetime import datetime


class MeterFaultError(Exception):
    """Base exception for all meter-related faults."""

    def __init__(self, meter_id: str, fault_code: str, detail: str):
        """Initialise with structured diagnostic fields."""
        super().__init__(f"[{meter_id}] Fault {fault_code}: {detail}")
        self.meter_id = meter_id
        self.fault_code = fault_code
        self.detail = detail
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        return (
            f"MeterFaultError(meter_id={self.meter_id!r}, "
            f"fault_code={self.fault_code!r}, detail={self.detail!r})"
        )


class OverloadError(MeterFaultError):
    """Raised when a meter reading exceeds 150% of rated capacity."""

    def __repr__(self) -> str:
        return (
            f"OverloadError(meter_id={self.meter_id!r}, "
            f"fault_code={self.fault_code!r}, detail={self.detail!r})"
        )


class TariffConfigError(Exception):
    """Raised when a TariffSchedule is configured with invalid rate values."""

    def __init__(self, field: str, value, reason: str):
        """Initialise with the offending field, value, and reason."""
        super().__init__(f"TariffConfigError: {field}={value!r} — {reason}")
        self.field = field
        self.value = value
        self.reason = reason

    def __repr__(self) -> str:
        return (
            f"TariffConfigError(field={self.field!r}, "
            f"value={self.value!r}, reason={self.reason!r})"
        )
