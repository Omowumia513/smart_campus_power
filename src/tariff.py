"""TariffSchedule — configurable peak and off-peak electricity tariff."""

from __future__ import annotations
from src.exceptions import TariffConfigError


class TariffSchedule:
    """Holds peak and off-peak tariff rates in NGN per kWh.

    Peak hours:    06:00 – 22:00 daily.
    Off-peak hours: 22:00 – 06:00 daily.
    """

    def __init__(
        self,
        peak_rate_ngn_per_kwh: float,
        off_peak_rate_ngn_per_kwh: float,
    ):
        """Initialise with validated tariff rates."""
        self.peak_rate_ngn_per_kwh = peak_rate_ngn_per_kwh
        self.off_peak_rate_ngn_per_kwh = off_peak_rate_ngn_per_kwh

    # --- validated properties -----------------------------------------------

    @property
    def peak_rate_ngn_per_kwh(self) -> float:
        """Peak-hour tariff rate in NGN per kWh (must be positive)."""
        return self._peak_rate

    @peak_rate_ngn_per_kwh.setter
    def peak_rate_ngn_per_kwh(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value <= 0:
            raise TariffConfigError(
                "peak_rate_ngn_per_kwh", value, "must be a positive number"
            )
        self._peak_rate = float(value)

    @property
    def off_peak_rate_ngn_per_kwh(self) -> float:
        """Off-peak tariff rate in NGN per kWh (must be positive)."""
        return self._off_peak_rate

    @off_peak_rate_ngn_per_kwh.setter
    def off_peak_rate_ngn_per_kwh(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value <= 0:
            raise TariffConfigError(
                "off_peak_rate_ngn_per_kwh", value, "must be a positive number"
            )
        self._off_peak_rate = float(value)

    # --- class method -------------------------------------------------------

    @classmethod
    def from_dict(cls, config: dict) -> "TariffSchedule":
        """Create a TariffSchedule from a configuration dictionary.

        Expected keys: 'peak_rate_ngn_per_kwh', 'off_peak_rate_ngn_per_kwh'.
        """
        try:
            return cls(
                peak_rate_ngn_per_kwh=config["peak_rate_ngn_per_kwh"],
                off_peak_rate_ngn_per_kwh=config["off_peak_rate_ngn_per_kwh"],
            )
        except KeyError as exc:
            raise TariffConfigError(
                str(exc), None, "required key missing from config dict"
            ) from exc

    def rate_for(self, hour: int) -> float:
        """Return the applicable rate for the given hour (0-23)."""
        if 6 <= hour < 22:
            return self._peak_rate
        return self._off_peak_rate

    def __str__(self) -> str:
        return (
            f"TariffSchedule(peak=NGN {self._peak_rate:.2f}/kWh, "
            f"off-peak=NGN {self._off_peak_rate:.2f}/kWh)"
        )

    def __repr__(self) -> str:
        return (
            f"TariffSchedule(peak_rate_ngn_per_kwh={self._peak_rate!r}, "
            f"off_peak_rate_ngn_per_kwh={self._off_peak_rate!r})"
        )
