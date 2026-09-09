# Draft Radar Privacy Policy

Effective September 9, 2026.

Draft Radar helps users review ESPN fantasy football drafts, lineups, matchups
and available players. This policy describes version 0.10.0.

## Data used in your browser

The extension reads fantasy league identifiers, team names, rosters, settings,
schedules, player availability and projections from ESPN. ESPN responses may
include league-member identifiers or names. League responses are processed in
browser memory to provide the requested comparisons, and are not sent to the
developer or to the public rankings repository.

Requests to ESPN use your existing signed-in session. The extension does not
read, collect or store your password or extract authentication cookies. It does
not submit lineups, trades, purchases or waiver claims on your behalf.

## Public data providers

The extension downloads public ranking data from GitHub's raw.githubusercontent.com,
player statuses and fantasy trends from api.sleeper.app, and NFL game schedules
from ESPN. Player images load from ESPN and Sleeper image services. These services
receive normal network metadata, including IP address and the resource requested,
under their own privacy policies. Private league snapshots are not sent to these
public ranking or image providers.

## Local storage and retention

Display preferences, selected fantasy team and public-data caches are stored in
ESPN-origin localStorage in your browser. Private league response snapshots are
held in runtime memory. Closing the page ends that runtime session. Clearing ESPN
site data removes the local preferences and caches; uninstalling the extension
stops its activity but may not clear existing ESPN-origin storage. This storage
is not a secure vault and may be accessible to other code running on that origin.

## Use and sharing

The extension has no developer-operated analytics or advertising. The developer
does not sell user data, use it for unrelated purposes, or use it to determine
creditworthiness or eligibility for lending. Executable code is included in the
extension package; the remote rankings feed supplies data, not executable code.

## Contact and changes

For questions or deletion assistance, open an issue at
https://github.com/swattyy/sunday-scaries-board/issues . Do not include passwords,
authentication cookies or private league exports in a public issue. This policy
will be updated when the extension's data practices materially change.
