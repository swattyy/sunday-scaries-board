# Draft Radar Privacy Policy

Effective September 13, 2026.

Draft Radar helps users review ESPN fantasy football drafts, lineups, matchups,
available players and optional AI summaries. This policy describes version 0.13.1.

## Data used in your browser

The extension reads fantasy league identifiers, team names, rosters, settings,
schedules, player availability and projections from ESPN. ESPN responses may
include league-member identifiers or names. League responses are processed in
browser memory to provide comparisons. They are not sent to the public rankings
repository. A filtered football snapshot is sent to the Draft Radar AI service
only when the user requests an AI summary, as described below.

Requests to ESPN use your existing signed-in session. The extension does not
read, collect or store your password or extract authentication cookies. It does
not submit lineups, trades, purchases or waiver claims on your behalf.

## Public data providers

The extension downloads public ranking data from GitHub's raw.githubusercontent.com,
player statuses and fantasy trends from api.sleeper.app, and NFL game schedules,
player news headlines and regular-season game logs from ESPN. Opening a player
card requests that public player ID from ESPN; player-detail responses are cached
in page memory for up to 15 minutes. Player images load from ESPN and Sleeper image
services. These services receive normal network metadata, including IP address
and the resource requested, under their own privacy policies. Private league
snapshots are not sent to these public ranking or image providers.

## Optional AI summaries

AI summaries run only after the user clicks Generate or Ask in the Next tab.
Draft Radar sends a filtered fantasy-football snapshot to the developer-operated
Draft Radar AI service. It may include player names, league scoring and roster
settings, anonymous league rosters, projections, injury designations, byes,
opponents, kickoff times, available players, the locally calculated legal lineup,
and the user's typed fantasy-football question. Team and owner names, league-member
names, emails, ESPN passwords, authentication cookies and session tokens are not
included.

The Draft Radar AI service validates and filters the snapshot again, then sends it
to a third-party AI provider to generate the requested explanation. The provider
receives the filtered football context and a one-way pseudonymous identifier, not
the user's ESPN or Sleeper identity, and processes the request under its own
privacy terms. Draft Radar does not use AI summaries to make roster transactions.
The service and its network security provider may process ordinary connection
metadata, including IP address, to deliver the request and apply short-term abuse
and rate-limit protection. Draft Radar does not store raw IP addresses in its
application database.

If you optionally connect Sleeper during setup, the extension sends the username
you enter to Sleeper's public API to retrieve that user's public NFL leagues. The
selected Sleeper username, user ID, league ID, league name and season are stored
locally in the extension. Draft Radar does not request a Sleeper password or API
token.

## Local storage and retention

Display preferences, selected fantasy team and public-data caches are stored in
ESPN-origin localStorage in your browser. Private league response snapshots are
held in runtime memory. Closing the page ends that runtime session. Clearing ESPN
site data removes the local preferences and caches; uninstalling the extension
stops its activity but may not clear existing ESPN-origin storage. This storage
is not a secure vault and may be accessible to other code running on that origin.

First-run completion and optional Sleeper identifiers are stored in extension
local storage. The extension also stores a random installation identifier used
only for AI rate limiting. The AI service stores a one-way hash of that identifier,
the UTC date and a request count. It also stores an aggregate daily request count
that is not tied to a user. Rate-limit records older than 31 days are deleted.
The service does not persist AI request bodies, roster snapshots, questions or
generated summaries. Uninstalling Draft Radar removes extension-owned storage.

## Use and sharing

The extension has no developer-operated analytics or advertising. The developer
uses the filtered AI snapshot only to provide the requested summary and enforce
service limits. The developer does not sell user data, use it for unrelated
purposes, or use it to determine creditworthiness or eligibility for lending.
Executable code is included in the extension package; remote ranking and AI
responses supply data, not executable code.

## Contact and changes

For questions or deletion assistance, email swatyy.dev@pm.me or open an issue at
https://github.com/swattyy/sunday-scaries-board/issues . Do not include passwords,
authentication cookies or private league exports in a public issue. This policy
will be updated when the extension's data practices materially change.
