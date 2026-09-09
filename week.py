#!/usr/bin/env python3
"""
Weekly expert-consensus layer for Draft Radar season mode.

Fetches FantasyPros WEEKLY rankings (the .php pages, not the draft cheatsheets)
and maps them to ESPN player ids. The extension blends these ranks with ESPN's
own weekly projections (which arrive in league scoring via the league API), by
mapping each player's expert rank onto the league's projection curve at his
position - so the output is "what the expert consensus implies in YOUR scoring".

Emits week.json: {"week": N, "updated": ..., "players": [[eid, pos, posrank], ...]}

Gracefully does nothing (keeps the old file) when weekly rankings are not
published yet - e.g. during the offseason the pages hold draft content.
"""
import json, os, sys, time
from datetime import datetime, timezone
from build import get, norm, espn_players, POS

HERE = os.path.dirname(os.path.abspath(__file__))

# weekly ranking pages per position bucket; flex covers RB/WR/TE
PAGES = {'flex': 'half-point-ppr', 'qb': 'qb', 'k': 'k', 'dst': 'dst'}


def weekly(slug):
    """ecrData blob on the weekly pages, same format as the cheatsheets."""
    html = get('https://www.fantasypros.com/nfl/rankings/%s.php' % slug).decode('utf8', 'replace')
    i = html.find('var ecrData = ')
    if i < 0:
        return None, None
    start = html.index('{', i)
    obj, _ = json.JSONDecoder().raw_decode(html[start:])
    # weekly pages carry the week number; draft pages carry type "draft"
    wk = obj.get('week') or 0
    if str(obj.get('type', '')).lower() == 'draft':
        return None, None
    return obj.get('players') or [], int(wk) if str(wk).isdigit() or isinstance(wk, int) else 0


def main():
    by_name = {}
    for e in espn_players(limit=600):
        p = e['player']
        if POS.get(p.get('defaultPositionId')):
            by_name[norm(p['fullName'])] = (p.get('id'), POS[p.get('defaultPositionId')])

    rows, week = [], 0
    skipped = []
    for tag, slug in PAGES.items():
        try:
            players, wk = weekly(slug)
        except Exception as exc:
            print('weekly page unavailable: %s: %s' % (slug, exc))
            skipped.append(slug)
            continue
        if players is None:
            print('week.json: %s page has no weekly data (offseason?) - skipping' % slug)
            continue
        if not wk or not 1 <= wk <= 18:
            skipped.append(slug)
            continue
        if week and wk != week:
            raise RuntimeError('Weekly pages disagree (%s vs %s); refusing mixed-week feed' % (week, wk))
        week = wk
        for r in players:
            k = norm(r.get('player_name'))
            hit = by_name.get(k)
            if not hit:
                continue
            eid, pos = hit
            pr = r.get('pos_rank') or ''
            n = ''.join(c for c in str(pr) if c.isdigit())
            if not n:
                continue
            rows.append([eid, pos, int(n)])

    if len(rows) < 80 or not week:
        print('week.json: only %d ranked players, week=%s - keeping the old file' % (len(rows), week))
        return

    dest = os.path.join(HERE, 'week.json')
    rows = list({r[0]: r for r in rows}.values())
    payload = {'season': 2026, 'week': week, 'updated': datetime.now(timezone.utc).isoformat(),
               'scoring': 'half-PPR', 'source': 'FantasyPros weekly ranks',
               'positions': sorted({r[1] for r in rows}), 'skipped': skipped, 'players': rows}
    # Timestamp records observation freshness, even when rankings are unchanged.
    json.dump(payload, open(dest, 'w'), separators=(',', ':'))
    print('week.json: week %d, %d ranked players' % (week, len(rows)))


if __name__ == '__main__':
    main()
