"""
Pytest test suite for the Smart Campus Power Management System.
CPE 310 | Group 1 Capstone — 45 tests covering all OOP concepts.
"""

import pytest
from datetime import datetime, timedelta

from src.exceptions import MeterFaultError, OverloadError, TariffConfigError
from src.power_reading import PowerReading
from src.tariff import TariffSchedule
from src.meters import SinglePhaseMeter, ThreePhaseMeter, SolarFeedMeter, MeterDevice
from src.fault_alert import FaultAlert
from src.building_zone import BuildingZone
from src.campus_grid import CampusGrid


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ts():
    return datetime(2026, 6, 20, 10, 0)


@pytest.fixture
def reading(ts):
    return PowerReading("SPM-001", 1.5, 230.0, 6.52, ts)


@pytest.fixture
def tariff():
    return TariffSchedule(peak_rate_ngn_per_kwh=68.0, off_peak_rate_ngn_per_kwh=45.0)


@pytest.fixture
def single_meter():
    return SinglePhaseMeter("SPM-001", "Male Hostel Block A")


@pytest.fixture
def three_meter():
    return ThreePhaseMeter("TPM-001", "Physics Lab")


@pytest.fixture
def solar_meter():
    return SolarFeedMeter("SFM-001", "Rooftop Solar Array")


@pytest.fixture
def zone(single_meter, three_meter):
    z = BuildingZone("Test Zone", "HOSTEL")
    z.add_meter(single_meter)
    z.add_meter(three_meter)
    return z


@pytest.fixture
def grid(tariff):
    return CampusGrid("FUOYE", tariff)


# ===========================================================================
# 1. Exceptions
# ===========================================================================

class TestExceptions:

    def test_meter_fault_error_attributes(self):
        exc = MeterFaultError("M1", "F01", "short circuit")
        assert exc.meter_id == "M1"
        assert exc.fault_code == "F01"
        assert exc.detail == "short circuit"
        assert "M1" in str(exc)

    def test_overload_error_is_meter_fault(self):
        exc = OverloadError("M2", "OVL", "too much current")
        assert isinstance(exc, MeterFaultError)
        assert isinstance(exc, OverloadError)

    def test_tariff_config_error_attributes(self):
        exc = TariffConfigError("peak_rate", -5, "must be positive")
        assert exc.field == "peak_rate"
        assert exc.value == -5
        assert "peak_rate" in str(exc)

    def test_overload_error_raised_correctly(self):
        with pytest.raises(OverloadError):
            raise OverloadError("M3", "OVL-002", "current spike")

    def test_tariff_config_error_raised_correctly(self):
        with pytest.raises(TariffConfigError):
            TariffSchedule(peak_rate_ngn_per_kwh=-1, off_peak_rate_ngn_per_kwh=45)


# ===========================================================================
# 2. PowerReading
# ===========================================================================

class TestPowerReading:

    def test_constructor_valid(self, ts):
        r = PowerReading("M1", 2.5, 230.0, 10.87, ts)
        assert r.meter_id == "M1"
        assert r.kwh == 2.5
        assert r.voltage == 230.0
        assert r.current == 10.87

    def test_constructor_invalid_meter_id(self, ts):
        with pytest.raises(ValueError):
            PowerReading("", 1.0, 230.0, 5.0, ts)

    def test_constructor_invalid_timestamp(self):
        with pytest.raises(TypeError):
            PowerReading("M1", 1.0, 230.0, 5.0, "2026-06-20")

    def test_equality(self, ts):
        r1 = PowerReading("M1", 3.0, 230.0, 5.0, ts)
        r2 = PowerReading("M2", 3.0, 230.0, 8.0, ts)
        assert r1 == r2

    def test_inequality(self, ts):
        r1 = PowerReading("M1", 3.0, 230.0, 5.0, ts)
        r2 = PowerReading("M1", 4.0, 230.0, 5.0, ts)
        assert r1 != r2

    def test_ordering_lt(self, ts):
        r1 = PowerReading("M1", 1.0, 230.0, 5.0, ts)
        r2 = PowerReading("M1", 2.0, 230.0, 5.0, ts)
        assert r1 < r2
        assert r2 > r1

    def test_add_two_readings(self, ts):
        r1 = PowerReading("M1", 2.0, 230.0, 5.0, ts)
        r2 = PowerReading("M1", 3.0, 230.0, 5.0, ts)
        result = r1 + r2
        assert result.kwh == 5.0

    def test_radd_with_zero(self, ts):
        r = PowerReading("M1", 4.0, 230.0, 5.0, ts)
        result = 0 + r
        assert result.kwh == 4.0

    def test_sum_list_of_readings(self, ts):
        readings = [
            PowerReading("M1", 1.0, 230.0, 5.0, ts),
            PowerReading("M1", 2.0, 230.0, 5.0, ts),
            PowerReading("M1", 3.0, 230.0, 5.0, ts),
        ]
        total = sum(readings)
        assert total.kwh == 6.0

    def test_hash_usable_in_set(self, ts):
        r1 = PowerReading("M1", 1.0, 230.0, 5.0, ts)
        r2 = PowerReading("M2", 2.0, 230.0, 5.0, ts + timedelta(hours=1))
        s = {r1, r2}
        assert len(s) == 2

    def test_sorted_readings(self, ts):
        readings = [
            PowerReading("M1", 3.0, 230.0, 5.0, ts),
            PowerReading("M1", 1.0, 230.0, 5.0, ts),
            PowerReading("M1", 2.0, 230.0, 5.0, ts),
        ]
        assert sorted(readings)[0].kwh == 1.0

    def test_str_and_repr(self, reading):
        assert "SPM-001" in str(reading)
        assert "PowerReading" in repr(reading)


# ===========================================================================
# 3. TariffSchedule
# ===========================================================================

class TestTariffSchedule:

    def test_valid_tariff(self, tariff):
        assert tariff.peak_rate_ngn_per_kwh == 68.0
        assert tariff.off_peak_rate_ngn_per_kwh == 45.0

    def test_negative_peak_rate_raises(self):
        with pytest.raises(TariffConfigError):
            TariffSchedule(peak_rate_ngn_per_kwh=-1, off_peak_rate_ngn_per_kwh=45)

    def test_zero_off_peak_rate_raises(self):
        with pytest.raises(TariffConfigError):
            TariffSchedule(peak_rate_ngn_per_kwh=68, off_peak_rate_ngn_per_kwh=0)

    def test_from_dict(self):
        t = TariffSchedule.from_dict({
            "peak_rate_ngn_per_kwh": 70.0,
            "off_peak_rate_ngn_per_kwh": 40.0,
        })
        assert t.peak_rate_ngn_per_kwh == 70.0

    def test_from_dict_missing_key(self):
        with pytest.raises(TariffConfigError):
            TariffSchedule.from_dict({"peak_rate_ngn_per_kwh": 70.0})

    def test_rate_for_peak_hour(self, tariff):
        assert tariff.rate_for(10) == 68.0   # 10:00 is peak

    def test_rate_for_off_peak_hour(self, tariff):
        assert tariff.rate_for(23) == 45.0   # 23:00 is off-peak

    def test_rate_boundary_22(self, tariff):
        assert tariff.rate_for(22) == 45.0   # 22:00 is off-peak

    def test_rate_boundary_6(self, tariff):
        assert tariff.rate_for(6) == 68.0    # 06:00 starts peak


# ===========================================================================
# 4. Meters
# ===========================================================================

class TestMeters:

    def test_single_phase_is_meter_device(self, single_meter):
        assert isinstance(single_meter, MeterDevice)

    def test_three_phase_is_meter_device(self, three_meter):
        assert isinstance(three_meter, MeterDevice)

    def test_solar_is_meter_device(self, solar_meter):
        assert isinstance(solar_meter, MeterDevice)

    def test_single_phase_take_reading(self, single_meter, ts):
        r = single_meter.take_reading(5.0, ts)
        assert isinstance(r, PowerReading)
        assert r.kwh == pytest.approx(230.0 * 5.0 / 1000.0, rel=1e-6)

    def test_three_phase_take_reading(self, three_meter, ts):
        import math
        r = three_meter.take_reading(10.0, ts)
        expected = math.sqrt(3) * 415.0 * 10.0 * 0.85 / 1000.0
        assert r.kwh == pytest.approx(expected, rel=1e-6)

    def test_solar_negative_kwh(self, solar_meter, ts):
        r = solar_meter.take_reading(-5.0, ts)
        assert r.kwh < 0

    def test_overload_detection_single(self, single_meter, ts):
        single_meter.take_reading(16.0, ts)   # 16 A > 10 A × 1.5 = 15 A
        assert single_meter.is_overloaded()

    def test_no_overload_normal(self, single_meter, ts):
        single_meter.take_reading(5.0, ts)
        assert not single_meter.is_overloaded()

    def test_overload_detection_three_phase(self, three_meter, ts):
        three_meter.take_reading(35.0, ts)    # 35 A > 20 A × 1.5 = 30 A
        assert three_meter.is_overloaded()

    def test_solar_never_overloaded(self, solar_meter, ts):
        solar_meter.take_reading(100.0, ts)
        assert not solar_meter.is_overloaded()

    def test_meter_flagging(self, single_meter, ts):
        single_meter.take_reading(16.0, ts)
        single_meter.flag()
        assert single_meter.flagged

    def test_invalid_meter_id_raises(self):
        with pytest.raises(ValueError):
            SinglePhaseMeter("", "Location")

    def test_invalid_voltage_raises(self):
        with pytest.raises(ValueError):
            SinglePhaseMeter("M1", "Location", voltage_rating=-10)

    def test_simulate_24h_produces_15_readings(self, single_meter):
        start = datetime(2026, 6, 20, 0, 0)
        readings = single_meter.simulate_24h(5.0, start)
        assert len(readings) == 15

    def test_total_kwh(self, single_meter, ts):
        single_meter.take_reading(5.0, ts)
        single_meter.take_reading(5.0, ts + timedelta(hours=1))
        assert single_meter.total_kwh() == pytest.approx(2 * 230.0 * 5.0 / 1000.0)

    def test_meter_str_and_repr(self, single_meter):
        assert "SPM-001" in str(single_meter)
        assert "SinglePhaseMeter" in repr(single_meter)


# ===========================================================================
# 5. FaultAlert
# ===========================================================================

class TestFaultAlert:

    def test_valid_alert(self, ts):
        a = FaultAlert("WARNING", "voltage sag", "SPM-001", ts)
        assert a.severity == "WARNING"
        assert a.meter_id == "SPM-001"

    def test_invalid_severity(self, ts):
        with pytest.raises(ValueError):
            FaultAlert("DISASTER", "bad", "M1", ts)

    def test_ordering_critical_lt_warning(self, ts):
        a_crit = FaultAlert("CRITICAL", "overload", "M1", ts)
        a_warn = FaultAlert("WARNING", "sag",      "M2", ts)
        assert a_crit < a_warn

    def test_ordering_warning_lt_info(self, ts):
        a_warn = FaultAlert("WARNING", "sag",      "M1", ts)
        a_info = FaultAlert("INFO",    "scheduled", "M2", ts)
        assert a_warn < a_info

    def test_sorted_alerts_critical_first(self, ts):
        alerts = [
            FaultAlert("INFO",     "routine",  "M1", ts),
            FaultAlert("CRITICAL", "overload", "M2", ts),
            FaultAlert("WARNING",  "sag",      "M3", ts),
        ]
        result = sorted(alerts)
        assert result[0].severity == "CRITICAL"
        assert result[1].severity == "WARNING"
        assert result[2].severity == "INFO"

    def test_alert_str(self, ts):
        a = FaultAlert("CRITICAL", "overload", "SPM-001", ts)
        assert "CRITICAL" in str(a)
        assert "SPM-001" in str(a)


# ===========================================================================
# 6. BuildingZone
# ===========================================================================

class TestBuildingZone:

    def test_len(self, zone):
        assert len(zone) == 2

    def test_contains_by_id(self, zone):
        assert "SPM-001" in zone

    def test_contains_by_object(self, zone, single_meter):
        assert single_meter in zone

    def test_not_contains(self, zone):
        assert "XYZ-999" not in zone

    def test_iter(self, zone):
        ids = [m.meter_id for m in zone]
        assert "SPM-001" in ids
        assert "TPM-001" in ids

    def test_compute_zone_total(self, zone, ts):
        for m in zone:
            m.take_reading(5.0, ts)
        total = zone.compute_zone_total()
        assert isinstance(total, PowerReading)
        assert total.kwh > 0

    def test_invalid_zone_type(self):
        with pytest.raises(ValueError):
            BuildingZone("Zone", "AIRPORT")

    def test_invalid_zone_name(self):
        with pytest.raises(ValueError):
            BuildingZone("", "HOSTEL")

    def test_add_non_meter_raises(self):
        z = BuildingZone("Z", "HOSTEL")
        with pytest.raises(TypeError):
            z.add_meter("not a meter")


# ===========================================================================
# 7. CampusGrid
# ===========================================================================

class TestCampusGrid:

    def test_str_contains_campus_name(self, grid):
        assert "FUOYE" in str(grid)

    def test_add_zone_and_report(self, grid, tariff, ts):
        m = SinglePhaseMeter("SPM-T1", "Test Block")
        m.take_reading(5.0, ts)
        z = BuildingZone("Test Zone", "ADMIN")
        z.add_meter(m)
        grid.add_zone(z)
        report = grid.generate_report()
        assert "Test Zone" in report
        assert "FUOYE" in report

    def test_check_overloads_raises_alert(self, grid, ts):
        m = SinglePhaseMeter("SPM-OVL", "Overload Block")
        m.take_reading(18.0, ts)   # triggers overload
        z = BuildingZone("Overload Zone", "HOSTEL")
        z.add_meter(m)
        grid.add_zone(z)
        grid.check_overloads()
        assert len(grid.alerts) == 1
        assert grid.alerts[0].severity == "CRITICAL"

    def test_sorted_alerts(self, grid, ts):
        grid.raise_alert(FaultAlert("INFO",     "info",    "M1", ts))
        grid.raise_alert(FaultAlert("CRITICAL", "overload","M2", ts))
        result = grid.sorted_alerts()
        assert result[0].severity == "CRITICAL"

    def test_bill_three_phase_multiplier(self, grid, ts):
        m = ThreePhaseMeter("TPM-BIL", "Lab")
        m.take_reading(10.0, ts)       # peak hour (10:00)
        z = BuildingZone("Lab Zone", "LABORATORY")
        z.add_meter(m)
        grid.add_zone(z)
        bill = grid.compute_bill(m)
        # bill = kwh × peak_rate × 1.4
        import math
        kwh = math.sqrt(3) * 415.0 * 10.0 * 0.85 / 1000.0
        expected = kwh * 68.0 * 1.4
        assert bill == pytest.approx(expected, rel=1e-6)

    def test_invalid_campus_name(self, tariff):
        with pytest.raises(ValueError):
            CampusGrid("", tariff)

    def test_add_invalid_zone_raises(self, grid):
        with pytest.raises(TypeError):
            grid.add_zone("not a zone")

    def test_generate_alert_report_no_alerts(self, grid):
        assert "No active alerts" in grid.generate_alert_report()
