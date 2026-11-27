# Features Overview

- **Multi-Year GraphQL Retrieval**: Fetches `contributionCalendar` year-by-year, handling leap years and partial boundary weeks.
- **Mandatory Activity Protection**: Dates with `existing_contributions > 0` are always marked `ACTIVE` and protected.
- **Gap Analysis**: Identifies empty days, consecutive inactive streaks, completely empty weeks, and partially active weeks.
- **9 Activity Patterns**: `consistent`, `random`, `weekday_focused`, `weekend_focused`, `increasing`, `decreasing`, `sprint`, `break_based`, `custom`.
- **Simulation vs Real Git**: Simulation is strictly decoupled from Git. Real Git commits use the current system time, modify only `activity.txt`, show diffs, and require explicit confirmation.
- **Exports**: CSV, JSON, text reports, SVG, and PNG graphs.
