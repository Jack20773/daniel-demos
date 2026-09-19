# -*- coding: utf-8 -*-
"""把台帳（看板票）壓成一小份快照，塞進 ai_overview.html 的 <script id="plans-snapshot">。
只讀不寫台帳。跑法：python -X utf8 _build/build_ai_overview_snapshot.py
"""
import json, re, io, sys, collections, datetime, pathlib

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE.parent / 'ai_overview.html'
BOARD = pathlib.Path(r'D:\All claude\000_Agent\007_dashboard') / ('plans' + '.json')

d = json.load(io.open(BOARD, encoding='utf-8'))
plans = d['plans']
now = datetime.datetime.now()

def days_since(s):
    if not s: return None
    try:
        return (now - datetime.datetime.fromisoformat(s[:19])).days
    except Exception:
        return None

state = collections.Counter(p.get('state') for p in plans)
prio_state = collections.Counter((p.get('state'), p.get('priority')) for p in plans)
cat = collections.Counter(p.get('category') or '未分類' for p in plans)

# 「正在做／等你／待驗」三類裡多久沒動
def stale_bucket(p):
    ds = days_since(p.get('last_progress_at'))
    if ds is None: return '沒紀錄'
    if ds <= 7: return '7 天內'
    if ds <= 14: return '8–14 天'
    if ds <= 30: return '15–30 天'
    return '超過 30 天'

open_states = ('active', 'waiting', 'verify', 'blocked')
stale = collections.Counter(stale_bucket(p) for p in plans if p.get('state') in open_states)

# 等他一句話的票（waiting / verify），照 priority 排
PR = {'now': 0, 'high': 1, 'next': 2, 'later': 3}
wait = [p for p in plans if p.get('state') in ('waiting', 'verify')]
wait.sort(key=lambda p: (PR.get(p.get('priority'), 9), p.get('last_progress_at') or ''))
wait_list = [{
    'id': p['id'], 'title': p['title'][:60], 'state': p['state'], 'priority': p.get('priority'),
    'days': days_since(p.get('last_progress_at')),
    'next': (p.get('next_action') or '')[:120].replace('\n', ' ')
} for p in wait[:8]]

# 「現在做」但很久沒動
now_stale = [p for p in plans if p.get('state') == 'active' and p.get('priority') in ('now', 'high')]
now_stale_days = [days_since(p.get('last_progress_at')) for p in now_stale]
now_stale_over14 = sum(1 for x in now_stale_days if x is not None and x > 14)

corrections = [p for p in plans if str(p.get('id', '')).startswith('correction-')]
corr_open = sum(1 for p in corrections if p.get('state') in open_states)

snapshot = {
    'generated_at': now.strftime('%Y-%m-%dT%H:%M+08:00'),
    'total': len(plans),
    'state': dict(state),
    'category': dict(cat.most_common()),
    'stale_open': dict(stale),
    'now_active': len(now_stale),
    'now_active_over14': now_stale_over14,
    'corrections_total': len(corrections),
    'corrections_open': corr_open,
    'waiting_on_him': wait_list,
    'waiting_count': len(wait),
    'all': [{
        'id': p['id'], 'title': p['title'][:80], 'state': p.get('state'), 'priority': p.get('priority') or '',
        'category': p.get('category') or '', 'last': (p.get('last_progress_at') or '')[:10]
    } for p in sorted(plans, key=lambda p: (p.get('state') or '', -(days_since(p.get('last_progress_at')) or 9999)))]
}

html = io.open(PAGE, encoding='utf-8').read()
blob = json.dumps(snapshot, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
new = re.sub(r'(<script id="plans-snapshot" type="application/json">)(.*?)(</script>)',
             lambda m: m.group(1) + blob + m.group(3), html, flags=re.S)
if new == html and '"plans-snapshot"' not in html:
    print('找不到 <script id="plans-snapshot">，沒寫入'); sys.exit(1)
io.open(PAGE, 'w', encoding='utf-8', newline='\n').write(new)
print('snapshot written:', {k: snapshot[k] for k in ('total', 'state', 'now_active', 'now_active_over14', 'waiting_count', 'corrections_open')})
print('stale_open', snapshot['stale_open'])
for w in wait_list: print(' ', w['priority'], w['state'], w['days'], w['title'])
