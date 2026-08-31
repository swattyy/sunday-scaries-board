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
    for tag, slug in PAGES.items():
        players, wk = weekly(slug)
        if players is None:
            print('week.json: %s page has no weekly data (offseason?) - skipping' % slug)
            continue
        week = max(week, wk or 0)
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
    payload = {'week': week, 'updated': time.strftime('%Y-%m-%dT%H:%M:%S'), 'players': rows}
    # same idempotency trick as the boards: identical data keeps the old timestamp
    if os.path.exists(dest):
        try:
            prev = json.load(open(dest, encoding='utf8'))
            if prev.get('players') == rows and prev.get('week') == week:
                payload['updated'] = prev.get('updated', payload['updated'])
        except Exception:
            pass
    json.dump(payload, open(dest, 'w'), separators=(',', ':'))
    print('week.json: week %d, %d ranked players' % (week, len(rows)))


if __name__ == '__main__':
    main()
