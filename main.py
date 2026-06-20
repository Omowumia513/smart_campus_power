"""
Smart Campus Power Management System — Full Demo
CPE 310 | Group 1 Capstone Project

Run:  python main.py
"""

from datetime import datetime, timedelta

from src.exceptions import MeterFaultError, OverloadError, TariffConfigError
from src.power_reading import PowerReading
from src.tariff import TariffSchedule
from src.meters import SinglePhaseMeter, ThreePhaseMeter, SolarFeedMeter
from src.fault_alert import FaultAlert
from src.building_zone import BuildingZone
from src.campus_grid import CampusGrid


def main() -> None:
    print("=" * 60)
    print("  SMART CAMPUS POWER MANAGEMENT SYSTEM")
    print("  Federal University Oye-Ekiti — Campus Grid Demo")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Set up tariff schedule
    # ------------------------------------------------------------------
    tariff = TariffSchedule.from_dict({
        "peak_rate_ngn_per_kwh": 68.0,
        "off_peak_rate_ngn_per_kwh": 45.0,
    })
    print(f"\nTariff loaded: {tariff}")

    # ------------------------------------------------------------------
    # 2. Initialise the campus grid (owns zones — composition)
    # ------------------------------------------------------------------
    grid = CampusGrid("Federal University Oye-Ekiti", tariff)

    # ------------------------------------------------------------------
    # 3. Create meters
    # ------------------------------------------------------------------
    # Hostel Zone — single-phase meters
    m_hostel_a = SinglePhaseMeter("SPM-001", "Male Hostel Block A")
    m_hostel_b = SinglePhaseMeter("SPM-002", "Female Hostel Block B")

    # Lab Zone — three-phase meters
    m_phys_lab  = ThreePhaseMeter("TPM-001", "Physics Laboratory")
    m_comp_lab  = ThreePhaseMeter("TPM-002", "Computer Lab Annex")

    # Admin Zone — single-phase
    m_admin     = SinglePhaseMeter("SPM-003", "Admin Block", voltage_rating=230.0)

    # Lecture Zone — three-phase (large hall)
    m_lecture   = ThreePhaseMeter("TPM-003", "LT-1 Lecture Theatre")

    # Solar feed meter
    m_solar     = SolarFeedMeter("SFM-001", "Rooftop Solar Array")

    # ------------------------------------------------------------------
    # 4. Build zones and attach meters (aggregation)
    # ------------------------------------------------------------------
    hostel_zone  = BuildingZone("Male & Female Hostels", "HOSTEL")
    hostel_zone.add_meter(m_hostel_a)
    hostel_zone.add_meter(m_hostel_b)

    lab_zone = BuildingZone("Science Laboratories", "LABORATORY")
    lab_zone.add_meter(m_phys_lab)
    lab_zone.add_meter(m_comp_lab)

    admin_zone = BuildingZone("Administration Block", "ADMIN")
    admin_zone.add_meter(m_admin)

    lecture_zone = BuildingZone("Lecture Theatres", "LECTURE_THEATRE")
    lecture_zone.add_meter(m_lecture)

    solar_zone = BuildingZone("Solar Generation", "SOLAR")
    solar_zone.add_meter(m_solar)

    # Register zones with campus grid (composition)
    for zone in [hostel_zone, lab_zone, admin_zone, lecture_zone, solar_zone]:
        grid.add_zone(zone)

    # ------------------------------------------------------------------
    # 5. Simulate 15 readings per meter across a 24-hour period
    # ------------------------------------------------------------------
    start = datetime(2026, 6, 20, 0, 0)   # midnight

    print("\n[Simulating 15 hourly readings per meter ...]")

    # Hostels — moderate steady load; trigger overload on meter A at hour 14
    for i in range(15):
        ts = start + timedelta(hours=i)
        current_a = 18.0 if i == 14 else 6.0    # 18 A at 14:00 → 180% rated = overload
        current_b = 4.5
        m_hostel_a.take_reading(current_a, ts)
        m_hostel_b.take_reading(current_b, ts)

    # Labs — higher load, trigger overload on physics lab at hour 10
    for i in range(15):
        ts = start + timedelta(hours=i)
        current_p = 35.0 if i == 10 else 12.0   # 35 A at 10:00 → 175% rated = overload
        current_c = 14.0
        m_phys_lab.take_reading(current_p, ts)
        m_comp_lab.take_reading(current_c, ts)

    # Admin & lecture — normal operation
    for i in range(15):
        ts = start + timedelta(hours=i)
        m_admin.take_reading(3.0, ts)
        m_lecture.take_reading(16.0, ts)

    # Solar — negative current during daylight hours (generation > consumption)
    for i in range(15):
        ts = start + timedelta(hours=i)
        if 8 <= i <= 14:
            m_solar.take_reading(-8.0, ts)   # net export to grid
        else:
            m_solar.take_reading(1.5, ts)

    # ------------------------------------------------------------------
    # 6. Check for overloads — raises & stores CRITICAL alerts
    # ------------------------------------------------------------------
    print("[Checking for overloads ...]")
    grid.check_overloads()

    # Manual anomaly alert for demo
    grid.raise_alert(FaultAlert(
        "WARNING",
        "Voltage sag detected — possible supply instability",
        "SPM-003",
        timestamp=start + timedelta(hours=8),
    ))
    grid.raise_alert(FaultAlert(
        "INFO",
        "Routine maintenance scheduled 22:00–00:00",
        "TPM-003",
        timestamp=start + timedelta(hours=6),
    ))

    # ------------------------------------------------------------------
    # 7. Campus-wide power report
    # ------------------------------------------------------------------
    print(grid.generate_report())

    # ------------------------------------------------------------------
    # 8. Alert priority report (CRITICAL first via __lt__)
    # ------------------------------------------------------------------
    print(grid.generate_alert_report())

    # ------------------------------------------------------------------
    # 9. Solar net export summary
    # ------------------------------------------------------------------
    net = m_solar.net_export_kwh()
    print(f"Solar net export to grid: {net:.3f} kWh")

    # ------------------------------------------------------------------
    # 10. Demonstrate sorted readings (__lt__ on PowerReading)
    # ------------------------------------------------------------------
    print("\nTop 3 highest readings from Physics Lab:")
    top3 = sorted(m_phys_lab.readings, reverse=True)[:3]
    for r in top3:
        print(f"  {r}")

    # ------------------------------------------------------------------
    # 11. sum() on readings (__add__ / __radd__ demo)
    # ------------------------------------------------------------------
    total_hostel_a = sum(m_hostel_a.readings)
    print(f"\nTotal kWh for Male Hostel Block A: {total_hostel_a.kwh:.3f} kWh")

    # ------------------------------------------------------------------
    # 12. Custom exception demo
    # ------------------------------------------------------------------
    print("\n--- Exception demos ---")
    try:
        bad_tariff = TariffSchedule(peak_rate_ngn_per_kwh=-10, off_peak_rate_ngn_per_kwh=30)
    except TariffConfigError as exc:
        print(f"Caught: {exc}")

    try:
        raise OverloadError("SPM-001", "OVL-001", "Current 18 A exceeds 150% of 10 A rating")
    except OverloadError as exc:
        print(f"Caught: {exc}")

    print("\nDemo complete.")


if __name__ == "__main__":
    main()
