# ATC Conflict Detection & Resolution Report (Simulation)

> [!CAUTION]
> Simulated academic result. **Not a real ATC clearance.**

## 1. Run summary

| Item | Value |
| --- | --- |
| Analysis status | `NO_CONFLICTS_DETECTED` |
| Inputs valid | yes |
| Conflicts detected | 0 |
| Aircraft analysed | AC1, AC2 |
| Airspace file | `sample_airspace.graphml` (`data\input\sample_airspace.graphml`) |
| Aircraft file | `sample_aircraft.json` (`data\input\sample_aircraft.json`) |
| Flight-plan file | `sample_no_conflict_flight_plans.json` (`data\input\sample_no_conflict_flight_plans.json`) |
| Generated (UTC) | 2026-10-17 11:16:02 |

## 2. Input validation

All inputs passed validation.

## 3. Airspace and aircraft overview

**Waypoints (2)**

| ID | Latitude | Longitude |
| --- | ---: | ---: |
| A | 41 | 2 |
| B | 41 | 2.5 |

**Directed edges (2)**

| From | To | Distance (NM) |
| --- | --- | ---: |
| A | B | 30 |
| B | A | 30 |

**Aircraft and flight plans (2 plans)**

| Aircraft | Speed (kt) | Route | Departure (s) | Cruise altitude (ft) |
| --- | ---: | --- | ---: | ---: |
| AC1 | 480 | A → B | 0 | 30000 |
| AC2 | 480 | B → A | 0 | 32000 |

## 4. Separation thresholds and model assumptions

- Horizontal (lateral) separation minimum: **5 NM**
- Vertical separation minimum: **1000 ft**
- A conflict requires *both* minima to be infringed at the same closest-approach time.

- Constant speed (`speed_kt`) along the whole route.
- Constant altitude (`cruise_altitude_ft`) for each flight plan; no climb/descent.
- Straight-line segments in a local equirectangular projection centred on the mean node position.
- Segment travel time uses edge `distance_nm`; positions use projected node coordinates (these distances are not reconciled).
- Each time-overlapping segment pair is evaluated at its closest horizontal approach.
- No wind, weather, aircraft performance limits, or surveillance uncertainty is modelled.

## 5. Detected conflicts

No conflicts detected.

## 6. Proposed resolutions

Not applicable (no conflicts to resolve).

## 7. Final analysis status and limitations

**Status: `NO_CONFLICTS_DETECTED`**

No separation conflicts were detected for the validated inputs under the stated model assumptions and thresholds.

**Clearance status:** No clearance is issued. This is a simulation result.

- Academic batch simulation only; not a certified or operational ATC system.
- This report is **not an ATC clearance** and must not be used for real-world operations.
- Tactical maneuver planning is a placeholder (`NOT_IMPLEMENTED`).
- Conflicts are reported per overlapping segment pair, so one encounter can appear more than once.
