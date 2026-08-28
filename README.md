# Draft Radar — board data feed

Live data feed for the **Draft Radar** Chrome extension (ESPN fantasy football).
`board_data.json` is fetched by the extension on page load, so rankings updates
reach every install without a reinstall or reload.

**This rebuilds itself.** A GitHub Action runs `build.py` twice a day (1am / 1pm
Mountain) and commits only when the underlying data actually changes.
Trigger one manually from the Actions tab → *refresh board* → *Run workflow*.

## Files

| File | What |
|---|---|
| `board_data.json` | the feed — `{v, updated, players[], notes{}}` |
| `build.py` | self-contained builder; no secrets, both sources public |
| `notes.json` | hand-researched per-player draft notes, keyed by ESPN id |

Each player row is:

```
[espn_id, name, team, pos, proj, vor, fall, bye, std, ecr, posrank, tier, best, worst, last]
```

- `proj` — 2026 season projection in half-PPR with 4-pt passing TDs
- `vor` — points above replacement for a 12-team superflex roster
- `fall` — how far he slips past his true superflex consensus price
- `std` / `best` / `worst` — how much the expert panel disagrees

Sources: [FantasyPros](https://www.fantasypros.com/) consensus ranks, ESPN projections,
and [Sleeper](https://docs.sleeper.com/) for live injuries (fetched client-side).
Not affiliated with any of them.
