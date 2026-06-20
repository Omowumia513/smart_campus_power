# Design Notes — Smart Campus Power Management System

## Composition vs Aggregation Decisions

### CampusGrid ◆── BuildingZone (Composition)

`CampusGrid` creates and owns its `BuildingZone` instances.  A building zone
only exists in the context of a specific campus grid; if the grid is
destroyed the zones have no independent meaning.  This is a "whole owns its
parts" relationship — the canonical definition of **composition** (filled
diamond, `1` to `1..*`).

### BuildingZone ◇── MeterDevice (Aggregation)

`BuildingZone` holds *references* to `MeterDevice` objects, but it does not
create them.  In the main demo the meters are instantiated before the zones
and passed in via `add_meter()`.  This means a meter can be moved to another
zone without being destroyed, and the meter's `readings` list persists
independently of zone membership.  This is the distinguishing feature of
**aggregation** (hollow diamond, `0..*`).

### MeterDevice ◆── PowerReading (Composition)

Each `MeterDevice` creates `PowerReading` objects inside `take_reading()` and
stores them in its private `_readings` list.  A `PowerReading` only makes
sense in the context of the meter that produced it; it carries the
`meter_id` as a first-class field precisely because it was created by that
meter.  This lifecycle dependency makes it **composition**.

---

## Abstract Base Class Strategy

`MeterDevice` is declared abstract (`ABC`) with three abstract properties
(`meter_id`, `location`, `voltage_rating`) and two abstract methods
(`take_reading`, `is_overloaded`).  All three concrete subclasses
(`SinglePhaseMeter`, `ThreePhaseMeter`, `SolarFeedMeter`) must implement
every abstract member — Python raises `TypeError` at instantiation time if
any are missing.

The `super().__init__()` chain is used correctly in all three subclasses.
`ThreePhaseMeter` stores its `_power_factor` *before* calling `super().__init__()`
because the parent `__init__` calls the `voltage_rating` setter, which is
concrete and does not depend on `_power_factor`.

---

## Duck Typing in generate_report()

`CampusGrid.generate_report()` calls `zone.compute_zone_total()` on each
object in `self._zones` without any `isinstance()` check.  Any object that
exposes a `compute_zone_total()` method returning a `PowerReading`-compatible
object will work correctly.  This satisfies the duck-typing requirement from
Week 4.

---

## `@total_ordering` Usage

Both `PowerReading` and `FaultAlert` use `@total_ordering`.  Only `__eq__`
and `__lt__` are defined manually; the decorator synthesises `__le__`,
`__gt__`, and `__ge__` automatically.  This keeps the code DRY while
satisfying the full ordering contract required for `sorted()` and `min()`/`max()`.

---

## Tariff Boundary Logic

The peak-hour boundary is: `6 <= hour < 22`.
- Hour 6 (06:00) is **peak** — the boundary is inclusive at the start.
- Hour 22 (22:00) is **off-peak** — the boundary is exclusive at the end.

This matches the project specification and is covered explicitly by two
boundary-value tests (`test_rate_boundary_22`, `test_rate_boundary_6`).
