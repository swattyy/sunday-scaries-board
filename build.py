#!/usr/bin/env python3
"""
Self-contained board builder for Draft Radar.

Runs in GitHub Actions with no secrets: both sources are public.
  - FantasyPros  -> expert consensus ranks/tiers (superflex + half-PPR positional)
  - ESPN         -> 2026 season projections, converted to each board's scoring

Emits TWO boards, consumed by the extension depending on league type:
  board_data.json  -> the Legacy League: 12-team, half-PPR, 4-pt pass TD, superflex (OP)
  board_1qb.json   -> a generic ESPN default league: 12-team, full PPR, 1 QB, no OP

When run locally (the extension/ folder exists next to repo/) it also bakes
extension/board_1qb.js, the offline fallback for 1-QB mode. In CI that folder
does not exist and the step is skipped.
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

BOARDS = {
    # replacement levels: 12 teams x (1QB 2RB 2WR 1TE 1OP 1FLEX 1K 1DST),
    # assuming the OP slot is ~10 QB / 2 skill and the FLEX ~5 RB / 6 WR / 1 TE
    'sf': {
        'file': 'board_data.json',
        'fp_slug': 'superflex',
        'half_ppr': True,                     # league scoring = ESPN PPR - 0.5/rec
        'base': {'QB': 24, 'RB': 30, 'WR': 32, 'TE': 13, 'K': 12, 'DST': 12},
        # ECR is the superflex-aware source; ESPN ADP is 1-QB-flavored noise here
        'ecr_weight': 2/3,
    },
    # replacement levels: 12 teams x (1QB 2RB 2WR 1TE 1FLEX 1K 1DST) with a
    # deep bench; QB14 because streaming covers the position in a 1-QB room
    '1qb': {
        'file': 'board_1qb.json',
        'fp_slug': 'ppr',
        'half_ppr': False,                    # ESPN default scoring IS full PPR
        'base': {'QB': 14, 'RB': 32, 'WR': 36, 'TE': 14, 'K': 12, 'DST': 12},
        # ESPN ADP is measured from real rooms just like this one - trust it more
        'ecr_weight': 1/3,
    },
}


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


def assemble(espn, fp, cfg):
    """Merge one FantasyPros consensus over the shared ESPN pull into a board."""
    board = {}

    for e in espn:
        p = e['player']
        pos = POS.get(p.get('defaultPositionId'))
        if not pos:
            continue
        proj = rec = prior = None
        for s in p.get('stats', []):
            if s.get('id') == '102026':
                proj = s.get('appliedTotal')     # ESPN default scoring = full PPR
                rec = (s.get('stats') or {}).get('53', 0.0)
            elif s.get('id') == '002025':
                prior = s.get('appliedTotal')
        if proj is None:
            continue
        if cfg['half_ppr']:
            proj = proj - 0.5 * (rec or 0.0)
        own = p.get('ownership') or {}
        board[norm(p['fullName'])] = {
            'eid': p.get('id'), 'name': p['fullName'],
            'tm': TEAM.get(p.get('proTeamId'), '?'), 'pos': pos,
            'proj': round(proj, 1),
            'adp': own.get('averageDraftPosition'),
            'last': round(prior) if prior else 0,
        }

    for r in fp:
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

    # --- VOR against this board's replacement levels ---
    repl = {}
    for pos, n in cfg['base'].items():
        pool = sorted([r['proj'] for r in rows if r.get('pos') == pos and r.get('proj')],
                      reverse=True)
        repl[pos] = pool[n - 1] if len(pool) >= n else (pool[-1] if pool else 0)
    for r in rows:
        # NB: test for None, not truthiness - a genuine 0-point projection (a player
        # buried on the depth chart) must produce a very negative VOR, not a neutral one.
        r['vor'] = (round(r['proj'] - repl[r['pos']])
                    if r.get('pos') in repl and r.get('proj') is not None else None)

    # --- expected pick in this room, and how far a player falls vs consensus ---
    w = cfg['ecr_weight']
    for r in rows:
        ecr, adp = r.get('ecr'), r.get('adp')
        r['exp'] = round(w*ecr + (1-w)*adp, 1) if (ecr and adp) else (float(ecr) if ecr else adp)
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
    return out


def publish(out, cfg, notes):
    payload = {'v': 1, 'updated': time.strftime('%Y-%m-%dT%H:%M:%S'), 'players': out}
    if notes:
        payload['notes'] = notes

    # sanity gate: never publish a board that would degrade what clients already have
    if len(out) < 200:
        sys.exit('%s: refusing to publish: only %d players' % (cfg['file'], len(out)))
    if len(out[0]) != 15:
        sys.exit('%s: refusing to publish: schema is %d fields, expected 15'
                 % (cfg['file'], len(out[0])))
    if not any(r[5] and r[5] > 100 for r in out[:30]):
        sys.exit('%s: refusing to publish: VOR looks wrong at the top' % cfg['file'])

    # The file is a single compact line, so git cannot tell a timestamp bump from a real
    # data change. Decide here instead: if the payload is identical apart from `updated`,
    # keep the old timestamp so the file is byte-identical and git sees nothing to commit.
    dest = os.path.join(HERE, cfg['file'])
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
    print('%s: %d players, %d notes, updated %s (%s)'
          % (cfg['file'], len(out), len(payload.get('notes', {})), payload['updated'],
             'changed' if changed else 'no change'))


def build():
    espn = espn_players()

    notes = {}
    notes_path = os.path.join(HERE, 'notes.json')
    if os.path.exists(notes_path):
        notes = json.load(open(notes_path, encoding='utf8'))
        notes = {k: v for k, v in notes.items() if not k.startswith('_')}

    for mode, cfg in BOARDS.items():
        out = assemble(espn, fantasypros(cfg['fp_slug']), cfg)
        publish(out, cfg, notes)

        # local run only: bake the 1-QB offline fallback into the extension.
        # (The superflex fallback, board_data.js, is baked by data/make_ext.py.)
        ext = os.path.join(os.path.dirname(HERE), 'extension')
        if mode == '1qb' and os.path.isdir(ext):
            js = 'window.SS_BOARD_1QB=' + json.dumps(out, separators=(',', ':')) + ';\n'
            open(os.path.join(ext, 'board_1qb.js'), 'w', encoding='utf8').write(js)
            print('extension/board_1qb.js: %d players (baked fallback)' % len(out))


if __name__ == '__main__':
    build()
