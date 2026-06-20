"""CampusGrid — top-level composition root owning all BuildingZones and alerts."""

from __future__ import annotations
from typing import List

from src.building_zone import BuildingZone
from src.fault_alert import FaultAlert
from src.meters import MeterDevice
from src.tariff import TariffSchedule
from src.exceptions import OverloadError


class CampusGrid:
    """Represents the entire university campus electricity grid.

    CampusGrid OWNS its BuildingZone instances (composition): zones are
    created inside the grid and destroyed with it.  The alert queue is
    maintained here and can be queried and sorted by severity.

    generate_report() uses duck typing — it accepts any iterable of objects
    that possess a .consumption_kwh attribute or a .compute_zone_total()
    method, with no isinstance() check.
    """

    def __init__(self, campus_name: str, tariff: TariffSchedule):
        """Initialise the grid with a campus name and default tariff schedule."""
        if not isinstance(campus_name, str) or not campus_name.strip():
            raise ValueError("campus_name must be a non-empty string")
        self._campus_name = campus_name.strip()
        self._tariff = tariff
        self._zones: List[BuildingZone] = []
        self._alerts: List[FaultAlert] = []

    # --- zone management (composition) --------------------------------------

    def add_zone(self, zone: BuildingZone) -> None:
        """Add a BuildingZone to this grid (composition — grid owns zone)."""
        if not isinstance(zone, BuildingZone):
            raise TypeError("zone must be a BuildingZone instance")
        self._zones.append(zone)

    def get_zone(self, name: str) -> BuildingZone | None:
        """Return the zone with the given name, or None if not found."""
        for zone in self._zones:
            if zone.name == name:
                return zone
        return None

    # --- alert management ---------------------------------------------------

    def raise_alert(self, alert: FaultAlert) -> None:
        """Store a FaultAlert in the alert queue."""
        self._alerts.append(alert)

    @property
    def alerts(self) -> List[FaultAlert]:
        """All active alerts (unsorted)."""
        return list(self._alerts)

    def sorted_alerts(self) -> List[FaultAlert]:
        """Return alerts sorted by severity: CRITICAL first."""
        return sorted(self._alerts)

    # --- overload checking --------------------------------------------------

    def check_overloads(self) -> None:
        """Scan all meters across all zones; raise and store OverloadError alerts.

        Called after a batch of readings is taken.  Any meter whose latest
        reading is_overloaded() gets flagged and a CRITICAL alert queued.
        """
        for zone in self._zones:
            for meter in zone:
                if meter.is_overloaded():
                    meter.flag()
                    latest = meter.readings[-1]
                    alert = FaultAlert(
                        severity="CRITICAL",
                        message=(
                            f"Overload detected: {latest.current:.2f} A exceeds "
                            f"rated capacity on {meter.location}"
                        ),
                        meter_id=meter.meter_id,
                        timestamp=latest.timestamp,
                    )
                    self.raise_alert(alert)

    # --- billing ------------------------------------------------------------

    def compute_bill(self, meter: MeterDevice) -> float:
        """Compute total electricity bill in NGN for a single meter.

        Peak tariff applies 06:00–22:00; off-peak for 22:00–06:00.
        Three-phase meters are billed at 1.4× the base tariff rate.
        """
        from src.meters import ThreePhaseMeter
        multiplier = 1.4 if isinstance(meter, ThreePhaseMeter) else 1.0
        total = 0.0
        for reading in meter.readings:
            rate = self._tariff.rate_for(reading.timestamp.hour)
            total += reading.kwh * rate * multiplier
        return total

    # --- report generation (duck typing) ------------------------------------

    def generate_report(self) -> str:
        """Produce a formatted campus-wide power usage summary table.

        Accepts any iterable of objects with compute_zone_total() — pure duck
        typing, no isinstance() check.
        """
        col_zone = 28
        col_kwh = 12
        col_bill = 16
        col_alerts = 8

        header = (
            "Zone".ljust(col_zone)
            + "Total kWh".rjust(col_kwh)
            + "Bill (NGN)".rjust(col_bill)
            + "Alerts".rjust(col_alerts)
        )
        separator = "-" * (col_zone + col_kwh + col_bill + col_alerts)

        lines = [
            f"\n{'=' * len(separator)}",
            f"  CAMPUS POWER REPORT — {self._campus_name}",
            f"{'=' * len(separator)}",
            header,
            separator,
        ]

        total_kwh_all = 0.0
        total_bill_all = 0.0

        for zone in self._zones:
            zone_total = zone.compute_zone_total()
            kwh = zone_total.kwh
            # compute bill for every meter in this zone
            bill = sum(self.compute_bill(m) for m in zone)
            n_alerts = zone.active_alert_count(self._alerts)
            total_kwh_all += kwh
            total_bill_all += bill
            lines.append(
                zone.name.ljust(col_zone)
                + f"{kwh:.2f}".rjust(col_kwh)
                + f"{bill:,.2f}".rjust(col_bill)
                + str(n_alerts).rjust(col_alerts)
            )

        lines += [
            separator,
            "CAMPUS TOTAL".ljust(col_zone)
            + f"{total_kwh_all:.2f}".rjust(col_kwh)
            + f"{total_bill_all:,.2f}".rjust(col_bill)
            + str(len(self._alerts)).rjust(col_alerts),
            f"{'=' * len(separator)}\n",
        ]
        return "\n".join(lines)

    def generate_alert_report(self) -> str:
        """Print all active alerts sorted by severity (CRITICAL first)."""
        if not self._alerts:
            return "No active alerts."
        lines = ["\n--- ACTIVE ALERTS (sorted by severity) ---"]
        for alert in self.sorted_alerts():
            lines.append(str(alert))
        lines.append(f"Total alerts: {len(self._alerts)}\n")
        return "\n".join(lines)

    # --- dunder methods -----------------------------------------------------

    def __str__(self) -> str:
        return (
            f"CampusGrid({self._campus_name!r}, "
            f"zones={len(self._zones)}, alerts={len(self._alerts)})"
        )

    def __repr__(self) -> str:
        return (
            f"CampusGrid(campus_name={self._campus_name!r}, "
            f"tariff={self._tariff!r})"
        )
