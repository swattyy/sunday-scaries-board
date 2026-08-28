#!/usr/bin/env python3
"""
Self-contained board builder for Draft Radar.

Runs in GitHub Actions with no secrets: both sources are public.
  - FantasyPros  -> expert consensus ranks/tiers (superflex + half-PPR positional)
  - ESPN         -> 2026 season projections, converted to this league's exact scoring

League it is tuned for: 12-team, half-PPR, 4-pt passing TD, superflex (OP), 3 bench.
Emits board_data.json consumed by the extension.
"""
import json, re, os, sys, time, unicodedata, urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/128.0 Safari/537.36')
HERE = os.path.dirname(os.path.abspath(__file__))

TEAM = {1:'ATL',2:'BUF',3:'CHI',4:'CIN',5:'CLE',6:'DAL',7:'DEN',8:'DET',9:'GB',10:'TEN',
        11:'IND',12:'KC',13:'LV',14:'LAR',15:'MIA',16:'MIN',17:'NE',18:'NO',19:'NYG',20:'NYJ',
        21:'PHI',22:'ARI',23:'PIT',24:'LAC',25:'SF',26:'SEA',27:'TB',28:'WSH',29:'CAR',30:'JAX',
        33:'BAL',34:'HOU',0:'FA'}
POS = {1:'QB',2:'RB',3:'WR',4:'TE',5:'K',16:'DST'}

# replacement levels for THIS roster: 12 teams x (1QB 2RB 2WR 1TE 1OP 1FLEX 1K 1DST)
# assuming the OP slot is ~10 QB / 2 skill and the FLEX ~5 RB / 6 WR / 1 TE
BASE = {'QB': 24, 'RB': 30, 'WR': 32, 'TE': 13, 'K': 12, 'DST': 12}


def get(url, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
    return urllib.request.urlopen(req, timeout=90).read()


def norm(n):
    n = unicodedata.normalize('NFKD', str(n)).encode('ascii', 'ignore').decode().lower()
    n = n.replace("'", '').replace('.', '')
    n = re.sub(r'\b(jr|sr|ii|iii|iv|v)\b', '', n)
    return ' '.join(re.sub(r'[^a-z ]', '', n).split())


def fantasypros(slug):
    """Rankings live in a `var ecrData = {...}` blob in the page HTML."""
    html = get('https://www.fantasypros.com/nfl/rankings/%s-cheatsheets.php' % slug).decode(
        'utf8', 'replace')
    i = html.find('var ecrData = ')
    if i < 0:
        raise RuntimeError('no ecrData for ' + slug)
    start = html.index('{', i)
    obj, _ = json.JSONDecoder().raw_decode(html[start:])
    return obj['players']


def espn_players(limit=400):
    filt = json.dumps({'players': {'limit': limit,
                                   'sortDraftRanks': {'sortPriority': 100, 'sortAsc': True,
                                                      'value': 'STANDARD'}}})
    raw = get('https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/2026/'
              'segments/0/leaguedefaults/3?view=kona_player_info',
              {'x-fantasy-filter': filt, 'Accept': 'application/json'})
    return json.loads(raw)['players']


def build():
    board = {}

    # --- ESPN projections, converted to half-PPR (PPR minus 0.5/reception) ---
    for e in espn_players():
        p = e['player']
        pos = POS.get(p.get('defaultPositionId'))
        if not pos:
            continue
        proj = rec = prior = None
        for s in p.get('stats', []):
            if s.get('id') == '102026':
                proj = s.get('appliedTotal')
                rec = (s.get('stats') or {}).get('53', 0.0)
            elif s.get('id') == '002025':
                prior = s.get('appliedTotal')
        if proj is None:
            continue
        own = p.get('ownership') or {}
        board[norm(p['fullName'])] = {
            'eid': p.get('id'), 'name': p['fullName'],
            'tm': TEAM.get(p.get('proTeamId'), '?'), 'pos': pos,
            'proj': round(proj - 0.5 * (rec or 0.0), 1),
            'adp': own.get('averageDraftPosition'),
            'last': round(prior) if prior else 0,
        }

    # --- FantasyPros superflex consensus ---
    for r in fantasypros('superflex'):
        k = norm(r.get('player_name'))
        d = board.setdefault(k, {'eid': None, 'name': r.get('player_name'),
                                 'tm': r.get('player_team_id'), 'pos': '',
                                 'proj': 0, 'adp': None, 'last': 0})
        d['ecr'] = r.get('rank_ecr')
        d['tier'] = r.get('tier')
        d['posrank'] = r.get('pos_rank') or ''
        d['bye'] = r.get('player_bye_week')
        d['best'] = r.get('rank_min')
        d['worst'] = r.get('rank_max')
        d['std'] = r.get('rank_std')
        if not d.get('pos'):
            d['pos'] = re.sub(r'\d+$', '', d['posrank'] or '')

    rows = list(board.values())

    # --- VOR against this league's replacement levels ---
    repl = {}
    for pos, n in BASE.items():
        pool = sorted([r['proj'] for r in rows if r.get('pos') == pos and r.get('proj')],
                      reverse=True)
        repl[pos] = pool[n - 1] if len(pool) >= n else (pool[-1] if pool else 0)
    for r in rows:
        # NB: test for None, not truthiness - a genuine 0-point projection (a player
        # buried on the depth chart) must produce a very negative VOR, not a neutral one.
        r['vor'] = (round(r['proj'] - repl[r['pos']])
                    if r.get('pos') in repl and r.get('proj') is not None else None)

    # --- expected pick in this room, and how far a player falls vs consensus ---
    for r in rows:
        ecr, adp = r.get('ecr'), r.get('adp')
        r['exp'] = round(2/3*ecr + 1/3*adp, 1) if (ecr and adp) else (float(ecr) if ecr else adp)
        r['fall'] = round(r['exp'] - ecr) if (ecr and r.get('exp')) else 0

    def i(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    skill = sorted([r for r in rows if r.get('exp') and r.get('pos') not in ('K', 'DST')],
                   key=lambda r: r['exp'])[:210]
    kd = []
    for pos in ('K', 'DST'):
        kd += sorted([r for r in rows if r.get('pos') == pos and r.get('proj')],
                     key=lambda r: -r['proj'])[:14]

    out = []
    for r in skill + kd:
        try:
            std = round(float(r.get('std') or 0), 1)
        except (TypeError, ValueError):
            std = 0.0
        out.append([r.get('eid'), r['name'], r.get('tm', 'FA'), r.get('pos'),
                    round(r.get('proj') or 0), round(r.get('vor') or 0), round(r.get('fall') or 0),
                    i(r.get('bye')), std, i(r.get('ecr')), r.get('posrank') or '',
                    i(r.get('tier')), i(r.get('best')), i(r.get('worst')), i(r.get('last'))])

    payload = {'v': 1, 'updated': time.strftime('%Y-%m-%dT%H:%M:%S'), 'players': out}

    notes_path = os.path.join(HERE, 'notes.json')
    if os.path.exists(notes_path):
        notes = json.load(open(notes_path, encoding='utf8'))
        payload['notes'] = {k: v for k, v in notes.items() if not k.startswith('_')}

    # sanity gate: never publish a board that would degrade what clients already have
    if len(out) < 200:
        sys.exit('refusing to publish: only %d players' % len(out))
    if len(out[0]) != 15:
        sys.exit('refusing to publish: schema is %d fields, expected 15' % len(out[0]))
    if not any(r[5] and r[5] > 100 for r in out[:30]):
        sys.exit('refusing to publish: VOR looks wrong at the top of the board')

    # The file is a single compact line, so git cannot tell a timestamp bump from a real
    # data change. Decide here instead: if the payload is identical apart from `updated`,
    # keep the old timestamp so the file is byte-identical and git sees nothing to commit.
    dest = os.path.join(HERE, 'board_data.json')
    changed = True
    if os.path.exists(dest):
        try:
            prev = json.load(open(dest, encoding='utf8'))
            if (prev.get('players') == payload['players']
                    and prev.get('notes') == payload.get('notes')):
                payload['updated'] = prev.get('updated', payload['updated'])
                changed = False
        except Exception:
            pass

    json.dump(payload, open(dest, 'w'), separators=(',', ':'))
    print('board_data.json: %d players, %d notes, updated %s (%s)'
          % (len(out), len(payload.get('notes', {})), payload['updated'],
             'changed' if changed else 'no change'))


if __name__ == '__main__':
    build()
