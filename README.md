# Sunday Scaries — live draft board data

Hosted data feed for the [Sunday Scaries fantasy football Chrome extension].
The extension fetches `board_data.json` from this repo's raw URL on page load,
so rankings updates reach every install with no reinstall or reload.

- `board_data.json` — player board: `[espn_id, name, team, pos, proj, vor, fall, bye, std]`
  - `proj` — 2026 season projection in half-PPR / 4-pt-pass-TD scoring
  - `vor` — points above replacement for a 12-team superflex roster
  - `std` — expert-consensus disagreement (volatility proxy)
- Updated by the project's `data/refresh.py` pipeline (FantasyPros ECR + ESPN projections)

Not affiliated with ESPN, FantasyPros, or Sleeper.
