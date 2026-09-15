# -*- coding: utf-8 -*-
"""
產生三份 demo 頁（A 貼在訊號旁 / B 推薦清單在最前面 / C 獨立分頁）＋ index.html。
只讀 gooaye-site 的 out/*.json 與 site/index.html（唯讀），輸出到本 repo 根目錄。
跑法：python -X utf8 _build/build.py
"""
import json, html, shutil, sys
from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
GS = Path(r"D:\All claude\300_Projects\gooaye-site")
OUT = GS / "out"

m = json.loads((OUT / "mainline.json").read_text(encoding="utf-8"))
sb = json.loads((OUT / "scoreboard.json").read_text(encoding="utf-8"))
R = m["records"]
BOARD = {b["scope"]: b for b in sb["boards"]}
COMPUTED_AT = m["computed_at"][:10]
PRICE_TO = m["market_last_date"]          # {'TW': '2026-09-08', 'US': '2026-09-09'}
PRICE_TO_MAX = max(PRICE_TO.values())
LATEST_EP = max(r["utterance"]["episode_id"] for r in R)

E = html.escape

def pct(v, digits=1):
    if v is None: return "N/A"
    return ("+" if v > 0 else "") + f"{v:.{digits}f}%"

def rate(b):
    mm = b["made_money"]
    if not b["population"]: return "無資料"
    return f"{mm['rate']*100:.1f}%"

def frac(b):
    return f"{b['made_money']['wins']}/{b['population']}"

# ── 每個 primary_tag 的 30/90 天勝率（自己從 records 算，母體＝scored 且有方向）──
tag_stat = defaultdict(lambda: {"fixed_30d": [0, 0], "fixed_90d": [0, 0]})
tk_stat = defaultdict(lambda: {"fixed_30d": [0, 0], "fixed_90d": [0, 0]})
for r in R:
    t = r["target"]["judgment"]["primary_tag"] or "（無標籤）"
    for hz in ("fixed_30d", "fixed_90d"):
        x = r["backtest"]["horizons"][hz]
        if x["status"] == "scored" and x["verdict"]["made_money"] is not None:
            for d in (tag_stat[t], tk_stat[r["target"]["ticker"]]):
                d[hz][1] += 1
                d[hz][0] += 1 if x["verdict"]["made_money"] else 0

def stat_txt(d, hz):
    w, n = d[hz]
    return "無資料" if n == 0 else f"{w/n*100:.0f}%（{w}/{n}）"

# ── 共用 CSS：從 stock-signal/report_detail.html 抄來的那一套（配色、字級、卡片）──
CSS = """
  body{margin:0;padding:0;background:#f4f6f9;font-family:Arial,Helvetica,sans-serif;color:#333;}
  *{box-sizing:border-box;}
  .wrap{max-width:920px;margin:20px auto;background:#fff;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,.07);overflow-x:clip;}
  @media(max-width:600px){.wrap{margin:0;border-radius:0;}}
  .hdr{background:#1a252f;padding:20px;text-align:center;color:#fff;border-radius:8px 8px 0 0;}
  .hdr h1{font-size:22px;font-weight:bold;margin:0;}
  .hdr .sub{color:#b3c1cd;font-size:13px;margin-top:4px;}
  @media(max-width:600px){.hdr{border-radius:0;}}
  .nav-tabs{display:flex;gap:6px;padding:8px 12px;background:#14202b;}
  .nav-tab{flex:1;text-align:center;padding:8px 4px;border-radius:6px;font-size:13px;
    color:#b3c1cd;text-decoration:none;background:rgba(255,255,255,.06);white-space:nowrap;}
  .nav-tab:hover{background:rgba(255,255,255,.12);}
  .nav-tab-active{background:#2b6cb0;color:#fff;font-weight:bold;}
  @media(max-width:600px){.nav-tab{font-size:11px;padding:7px 2px;}}
  .demo-banner{background:#fff3cd;border-bottom:2px solid #ffe08a;padding:9px 14px;font-size:12px;line-height:1.7;color:#5c4b00;}
  .demo-banner b{color:#3d3200;}
  .lead-note{padding:11px 16px;background:#fffdf3;border-bottom:1px solid #eee;font-size:12.5px;line-height:1.75;color:#5f5a45;}
  .lead-note b{color:#1a252f;}
  @media(max-width:600px){.lead-note{padding:9px 12px;font-size:12px;line-height:1.65;}}
  .stats{display:flex;text-align:center;border-bottom:1px solid #eee;}
  .stats>div{flex:1;padding:14px 4px;border-left:1px solid #eee;}
  .stats>div:first-child{border-left:none;}
  .st-l{font-size:12px;color:#999;}
  .st-v{font-size:24px;font-weight:bold;color:#2c3e50;}
  .st-v.red{color:#d9534f;}
  .st-f{font-size:11px;color:#bbb;margin-top:2px;}
  @media(max-width:600px){.st-v{font-size:20px;}.st-l{font-size:11px;}}
  .calc-note{padding:6px 20px 10px;background:#fafcff;font-size:11px;color:#aaa;border-bottom:1px solid #eee;line-height:1.6;}
  .sec-bar{padding:10px 16px;border-bottom:1px solid #eee;background:#fafafa;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
  .sec-bar .t{font-size:13px;font-weight:bold;color:#1a252f;}
  .sec-bar .d{font-size:12px;color:#999;}
  .sec-head{padding:10px 16px;border-top:1px solid #eee;border-bottom:1px solid #eee;background:#f7f8fa;cursor:pointer;font-size:13px;color:#555;font-weight:bold;}
  .adv{padding:10px 20px;border-bottom:1px solid #dce9f7;background:#eef4fb;cursor:pointer;font-size:13px;color:#2b6cb0;font-weight:bold;}
  .adv span{color:#8fb3dc;font-size:12px;margin-left:6px;font-weight:normal;}
  /* 訊號帳本卡（stock-signal 首頁同款） */
  .led{border-bottom:1px solid #eee;padding:13px 16px;cursor:pointer;}
  .led:hover{background:#fbfcfd;}
  .led-r1{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;}
  .led-nm{font-size:16px;font-weight:700;color:#1a252f;}
  .led-cd{font-size:12px;color:#9aa4ad;}
  .led-dir{margin-left:auto;font-size:13px;font-weight:700;padding:2px 8px;border-radius:10px;white-space:nowrap;}
  .led-dir.bull{color:#8a8f94;background:#f2f4f6;}
  .led-dir.bear{color:#0d5c8a;background:#e2f1fb;border:1px solid #b9dcf2;}
  .led-dir.neu{color:#7a6a00;background:#fdf6dd;border:1px solid #ecdfa0;}
  .led-r2{font-size:12.5px;color:#7b858e;margin-top:3px;}
  .led-q{margin:8px 0 6px;padding:6px 10px;border-left:3px solid #dfe3e6;background:#fafbfc;font-size:14px;line-height:1.6;color:#4a5157;}
  .led-st{font-size:16px;font-weight:700;}
  .led-st.win{color:#c0392b;} .led-st.lose{color:#2b8a3e;} .led-st.pend{color:#8a8f94;}
  .led-nums{font-size:13.5px;color:#3d4650;margin-top:2px;}
  .led-nums .sep{color:#ccc;margin:0 6px;}
  .led-hist{margin-top:7px;font-size:12.5px;color:#6c757d;}
  .led-detail{display:none;background:#f8f9fa;border:1px solid #eee;border-radius:8px;padding:10px 14px;margin-top:9px;font-size:13px;color:#555;line-height:1.75;}
  .led-detail b{color:#1a252f;}
  .led-dt-head{font-weight:bold;color:#1a252f;font-size:13.5px;margin-bottom:5px;}
  .fld-note{font-size:11px;color:#a6adb4;margin-top:2px;line-height:1.5;}
  @media(max-width:600px){.led{padding:12px 12px;}.led-nm{font-size:15px;}.led-q{font-size:13.5px;}}
  /* 新增：固定天期回測那一行（demo A 的重點） */
  .bt-line{margin-top:6px;font-size:13px;color:#3d4650;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:center;}
  .bt-line .lab{font-size:11px;font-weight:bold;color:#2b6cb0;background:#eef4fb;border:1px solid #dce9f7;border-radius:4px;padding:1px 6px;white-space:nowrap;}
  .bt-line .w{color:#c0392b;font-weight:700;} .bt-line .l{color:#2b8a3e;font-weight:700;} .bt-line .p{color:#8a8f94;}
  .empty-state{text-align:center;padding:30px 10px;color:#888;font-size:13px;}
  .foot{padding:14px 16px 28px;font-size:11px;color:#aaa;line-height:1.7;text-align:center;}
  .foot a{color:#2b6cb0;}
  .ai-box{margin-top:6px;padding:6px 10px;border-left:3px solid #c7d7ea;background:#f4f8fc;font-size:13px;line-height:1.6;color:#4a5157;}
  .ai-box .who{display:inline-block;font-size:11px;color:#2b6cb0;font-weight:bold;margin-right:6px;}
"""

def nav(active, extra_tab=False):
    tabs = [("📊 訊號報告", "signal"), ("🔥 目前關注度", "attn"), ("📄 逐字稿", "tx")]
    if extra_tab: tabs.append(("🧪 回測", "bt"))
    out = []
    for lbl, key in tabs:
        cls = "nav-tab nav-tab-active" if key == active else "nav-tab"
        out.append(f'<a href="#" class="{cls}" onclick="return false" title="demo：導覽連結不會動">{lbl}</a>')
    return '<div class="nav-tabs">' + "".join(out) + "</div>"

def header(sub):
    return f'<div class="hdr"><h1>股癌訊號勝率追蹤</h1><div class="sub">{sub}</div></div>'

def banner(ver, real, fake):
    return (f'<div class="demo-banner"><b>🧪 這是 demo（版本 {ver}）</b>，給丹尼爾比較「回測要怎麼併進原本網站」用，不是正式頁。'
            f'<br><b>真的：</b>{real}'
            f'<br><b>假的／暫定：</b>{fake}</div>')

def page(title, body, extra_css="", extra_js=""):
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<style>{CSS}{extra_css}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
<script>
function toggleLed(i, el){{var b=document.getElementById('lgd-'+i);if(!b)return;var o=b.style.display!=='block';b.style.display=o?'block':'none';if(el)el.setAttribute('aria-expanded',o?'true':'false');}}
function toggleSec(id, el){{var b=document.getElementById(id);var o=b.style.display==='none';b.style.display=o?'block':'none';var a=el.querySelector('.arrow');if(a)a.textContent=o?'▾':'▸';}}
{extra_js}
</script>
</body>
</html>
"""

# ── 記錄 → 卡片 ─────────────────────────────────────────────
def days_ago(d):
    if not d: return None
    y, mo, dd = map(int, d.split("-"))
    return (date.fromisoformat(PRICE_TO_MAX) - date(y, mo, dd)).days

def hz_cell(x, dir_):
    """30/90 天那一格的文字"""
    if x["status"] == "scored" and x["verdict"]["made_money"] is not None:
        cls = "w" if x["verdict"]["made_money"] else "l"
        mark = "✓" if x["verdict"]["made_money"] else "✕"
        return f'<span class="{cls}">{pct(x["return_pct"])} {mark}</span>'
    if x["status"] == "pending":
        return '<span class="p">未滿期</span>'
    if x["reason"] == "direction_neutral":
        return '<span class="p">沒方向不計</span>'
    return '<span class="p">算不出</span>'

def led_card(r, i, show_bt=True):
    u, t, b = r["utterance"], r["target"], r["backtest"]
    H = b["horizons"]
    d = t["direction"]
    dirCls = {"long": "bull", "short": "bear"}.get(d, "neu")
    dirLbl = {"long": "↑ 看多", "short": "↓ 看空"}.get(d, "— 中性")
    mkt = "台股" if t["market"] == "TW" else "美股"
    ago = days_ago(b["entry_date"])
    agoTxt = f"（{ago} 天前）" if ago is not None else ""
    q = u["exact_quote"] or ""
    qShort = q if len(q) <= 80 else q[:80] + "…"
    td = H["to_date"]
    if td["status"] == "scored" and td["verdict"]["beat_benchmark"] is not None:
        stCls = "win" if td["verdict"]["beat_benchmark"] else "lose"
        stLbl = "✓ 跑贏大盤" if td["verdict"]["beat_benchmark"] else "✕ 落後大盤"
    else:
        stCls, stLbl = "pend", "○ 待觀察"
    bm = td["benchmark"]["ticker"] or ("0050" if t["market"] == "TW" else "SPY")
    h30, h90 = H["fixed_30d"], H["fixed_90d"]
    hist = tk_stat[t["ticker"]]
    histTxt = (f"本檔歷史：講完 30 天賺錢 <b>{hist['fixed_30d'][0]}/{hist['fixed_30d'][1]}</b> · 90 天 <b>{hist['fixed_90d'][0]}/{hist['fixed_90d'][1]}</b>"
               if hist["fixed_30d"][1] or hist["fixed_90d"][1] else "本檔歷史：尚無可計分訊號")
    bt_line = ""
    if show_bt:
        bt_line = (f'<div class="bt-line"><span class="lab">講完之後</span>'
                   f'<span>30 天 {hz_cell(h30, d)}</span><span>90 天 {hz_cell(h90, d)}</span></div>')
    def hz_detail(x, lab):
        if x["status"] == "scored":
            return (f"<div><b>{lab}</b>：{x['entry_date_used']} 進 {x['entry_price']:.2f} → {x['exit_date']} 出 {x['exit_price']:.2f}，"
                    f"報酬 {pct(x['return_pct'], 2)}；同期 {x['benchmark']['ticker']} {pct(x['benchmark']['return_pct'], 2)}"
                    f"（實跨 {x['trading_days']} 個交易日）</div>")
        if x["status"] == "pending":
            since = days_ago(x.get("entry_date_used") or b["entry_date"])
            return f"<div><b>{lab}</b>：未滿期（講出來到 {PRICE_TO_MAX} 才 {since} 天，未滿 {x['nominal_days']} 天），不進勝率分母</div>"
        return f"<div><b>{lab}</b>：無法計分（{x['reason']}）</div>"
    ai = f'<div class="ai-box"><span class="who">AI 解讀</span>{E(u["ai_reasoning"])}</div>' if u["ai_reasoning"] else \
         '<div class="fld-note">這筆來源資料沒有 AI 解讀欄（992 筆裡有 700 筆有）</div>'
    nums = (f'<div class="led-nums">個股 <b>{pct(td["return_pct"], 2)}</b><span class="sep">｜</span>同期 {E(bm)} <b>{pct(td["benchmark"]["return_pct"], 2)}</b>'
            f' <span style="color:#aaa;font-size:11px;">（播出日→{td["as_of"] or PRICE_TO_MAX}）</span></div>') if td["status"] == "scored" else \
           '<div class="led-nums" style="color:#999;">抱到今天：沒方向，不計分</div>'
    return f"""<div class="led" role="button" tabindex="0" aria-expanded="false" onclick="toggleLed({i}, this)">
  <div class="led-r1"><span class="led-nm">{E(t["stock_name"] or t["ticker"])}</span><span class="led-cd">{E(t["ticker"])}</span><span class="led-dir {dirCls}">{dirLbl}</span></div>
  <div class="led-r2">{E(u["episode_id"])} · 上架於 {b["entry_date"] or "日期不詳"}{agoTxt} · {mkt} · {E(t["judgment"]["primary_tag"] or "")}</div>
  <blockquote class="led-q">「{E(qShort)}」</blockquote>
  {bt_line}
  <div class="led-st {stCls}" style="margin-top:6px;">{stLbl}</div>
  {nums}
  <div class="led-hist">{histTxt}</div>
  <div class="led-detail" id="lgd-{i}">
    <div class="led-dt-head">{E(t["stock_name"] or t["ticker"])}（{E(t["ticker"])}）· {E(u["episode_id"])}</div>
    <div>原話（逐字，來源聽打稿、未經人工核對）：「{E(q)}」</div>
    {ai}
    {hz_detail(h30, "30 天")}{hz_detail(h90, "90 天")}
    <div>信心等級 {E(t["confidence"] or "N/A")} · 第 1 層（產業結構）{E(", ".join(t["judgment"]["l1_industry_structure"]) or "未判")} · 第 2 層（心法）{E(", ".join(t["judgment"]["l2_mindset"]) or "還沒判")} · 第 3 層（何時停）{E(", ".join(t["judgment"]["l3_when_to_stop"]) or "還沒判")}</div>
    <div class="fld-note">來源列：{E(r["provenance"]["source"])} #{r["provenance"]["source_row_id"]} · 算於 {E(r["provenance"]["computed_at"][:16])}</div>
  </div>
</div>"""

def scoreboard_row():
    a30, a90, atd = BOARD["mainline/fixed_30d/ALL"], BOARD["mainline/fixed_90d/ALL"], BOARD["mainline/to_date/ALL"]
    return f"""
  <div class="stats">
    <div><div class="st-l">講完 30 天準度</div><div class="st-v red">{rate(a30)}</div><div class="st-f">{frac(a30)} · 另 {a30['pending']} 筆未滿期</div></div>
    <div><div class="st-l">講完 90 天準度</div><div class="st-v red">{rate(a90)}</div><div class="st-f">{frac(a90)} · 另 {a90['pending']} 筆未滿期</div></div>
    <div><div class="st-l">最後更新</div><div class="st-v" style="font-size:17px;padding-top:6px;">{COMPUTED_AT}</div><div class="st-f">股價至 {PRICE_TO_MAX}</div></div>
  </div>
  <div class="calc-note">準度＝「有賺錢就算贏」：看多要漲、看空要跌，講出來後抱固定 30／90 個自然日；沒方向的 {a30['excluded'].get('direction_neutral',0)} 筆不計、未滿期不進分母。
  對照：抱到今天有賺錢 {rate(atd)}（{frac(atd)}），持有期不固定、僅供參考。</div>"""

# ══════════════════════════════════════════════════════════════
# Demo A：貼在訊號旁
# ══════════════════════════════════════════════════════════════
recs_sorted = sorted([r for r in R if r["backtest"]["entry_date"]], key=lambda r: (r["backtest"]["entry_date"], r["utterance"]["episode_id"]), reverse=True)
A_MAX = 80
cards = "".join(led_card(r, i) for i, r in enumerate(recs_sorted[:A_MAX]))
bodyA = f"""
{header(f"全集匯總 · {COMPUTED_AT} · 最新分析至 {LATEST_EP}")}
{nav("signal")}
{banner("A：貼在訊號旁",
        f"每筆的 30／90 天報酬、勝率計分板、原話、AI 解讀（gooaye-site {COMPUTED_AT} 算的，股價到 {PRICE_TO_MAX}）。",
        f"導覽列三個分頁點不動；頁面只列最新 {A_MAX} 筆（正式版會有篩選）；「跑贏／落後大盤」沿用原站抱到今天那把尺，只是對照。")}
<div class="lead-note">本頁整理 Podcast 逐字稿中<b>由 AI 萃取</b>的歷史訊號：主持人<b>在哪一集、哪一天</b>提到什麼標的、當時方向——
<b>現在每一筆旁邊多了一行「講完之後 30 天／90 天」</b>，看他講完固定天數後到底有沒有賺。這是歷史追蹤紀錄，不是投資建議；原話可展開查證。</div>
{scoreboard_row()}
<div class="adv" onclick="toggleSec('adv-a', this)"><span class="arrow">▸</span> 進階統計 <span>台股／美股 · 看多／看空 分開算</span></div>
<div id="adv-a" style="display:none;padding:10px 16px;border-bottom:1px solid #eee;font-size:13px;line-height:1.9;">
{"".join(f'<div>{lbl}：30 天 <b>{rate(BOARD["mainline/fixed_30d/"+k])}</b>（{frac(BOARD["mainline/fixed_30d/"+k])}）｜90 天 <b>{rate(BOARD["mainline/fixed_90d/"+k])}</b>（{frac(BOARD["mainline/fixed_90d/"+k])}）</div>' for lbl,k in [("台股","TW"),("美股","US"),("看多","long"),("看空","short")])}
<div class="fld-note">看空只有 50 幾筆，只能當觀察，不能讀成「他看空不準」。</div>
</div>
<div class="sec-bar"><span class="t">最近訊號</span><span class="d">依上架日倒序，最新 {A_MAX} 筆（共 {len(recs_sorted)} 筆有日期）；點任一筆展開原話、AI 解讀與進出場價</span></div>
<div id="ledger-list">{cards}</div>
<div class="empty-state">已顯示最新 {A_MAX} 筆，全部共 {m['record_count']} 筆（其中 {len(R)-len(recs_sorted)} 筆沒有上架日）</div>
<div class="foot">demo A · 資料：gooaye-site out/mainline.json、scoreboard.json（computed_at {E(m['computed_at'])}）· <a href="index.html">← 回三版入口</a></div>
"""
(ROOT / "demo-a-inline.html").write_text(page("股癌訊號勝率追蹤（demo A 貼在訊號旁）", bodyA), encoding="utf-8")

# ══════════════════════════════════════════════════════════════
# Demo B：AI 從他的話裡找出來的「隱藏勝率規律」→ 名單
# （00:55 需求更正：挑法不是丹尼爾定，是 AI 從資料裡找規律；每條規律附 n）
# ══════════════════════════════════════════════════════════════
import re
def epn(e): return int(e[2:])
def scored(x): return x["status"] == "scored" and x["verdict"]["made_money"] is not None
def wr(rs, hz):
    xs = [r for r in rs if scored(r["backtest"]["horizons"][hz])]
    w = sum(1 for r in xs if r["backtest"]["horizons"][hz]["verdict"]["made_money"])
    return (w, len(xs))
def wr_txt(rs, hz):
    w, n = wr(rs, hz)
    return "無資料" if n == 0 else f"{w/n*100:.1f}%（{w}/{n}）"
DIRECTED = [r for r in R if r["target"]["direction"] != "neutral"]
by_ticker = defaultdict(list)
for r in R: by_ticker[r["target"]["ticker"]].append(r)
def prev_within(r, k=2):
    e = epn(r["utterance"]["episode_id"])
    return any(0 < e - epn(o["utterance"]["episode_id"]) <= k for o in by_ticker[r["target"]["ticker"]] if o is not r)
def cnt_before(r):
    e = epn(r["utterance"]["episode_id"])
    return sum(1 for o in by_ticker[r["target"]["ticker"]] if epn(o["utterance"]["episode_id"]) < e)
STRUCT_TAGS = {"#產能擴充", "#籌碼面", "#估值過低"}
def is_struct(r): return r["target"]["judgment"]["primary_tag"] in STRUCT_TAGS
def is_combo(r): return r["target"]["direction"] == "long" and r["target"]["confidence"] == "High" and prev_within(r, 2)

RULES = [
    {"id": "R1", "name": "兩集內連著講同一檔", "test": lambda r: prev_within(r, 2),
     "yes": [r for r in DIRECTED if prev_within(r, 2)], "no": [r for r in DIRECTED if not prev_within(r, 2)],
     "no_lbl": "只講一次沒再提", "how": "同一檔在前 1～2 集也出現過（依 episode_id 差距算）"},
    {"id": "R2", "name": "講過 6 次以上的老面孔", "test": lambda r: cnt_before(r) >= 6,
     "yes": [r for r in DIRECTED if cnt_before(r) >= 6], "no": [r for r in DIRECTED if cnt_before(r) == 0],
     "no_lbl": "第一次講的股票", "how": "這句之前，同一檔已經被講過幾次（不分方向）"},
    {"id": "R3", "name": "講的是結構（產能／籌碼／估值），不是講財報數字", "test": is_struct,
     "yes": [r for r in DIRECTED if is_struct(r)], "no": [r for r in DIRECTED if r["target"]["judgment"]["primary_tag"] in ("#營收動能", "#熱度結束")],
     "no_lbl": "講營收動能／熱度結束", "how": "用來源資料的 primary_tag 分：#產能擴充 #籌碼面 #估值過低 算「結構」"},
    {"id": "R4", "name": "看多＋信心 High＋兩集內連講（最強組合）", "test": is_combo,
     "yes": [r for r in DIRECTED if is_combo(r)], "no": [r for r in DIRECTED if r["target"]["direction"] == "long" and not is_combo(r)],
     "no_lbl": "其他看多", "how": "R1 再加上信心等級 High"},
]
SHORT = [r for r in DIRECTED if r["target"]["direction"] == "short"]
SHORT_TW = [r for r in SHORT if r["target"]["market"] == "TW"]
KW_CHEAP = [r for r in DIRECTED if re.search(r"便宜|估值|本益比|低估", r["utterance"]["exact_quote"] or "")]
KW_EARN = [r for r in DIRECTED if re.search(r"財報|guidance|Guidance|上修|earnings|Earnings", r["utterance"]["exact_quote"] or "")]
base30, base90 = wr(DIRECTED, "fixed_30d"), wr(DIRECTED, "fixed_90d")

def rule_row(ru):
    return (f'<div class="rule-row"><div class="rule-h"><span class="rid">{ru["id"]}</span><b>規律：{E(ru["name"])}</b></div>'
            f'<div class="rule-n">→ 90 天有賺 <b class="hi">{wr_txt(ru["yes"],"fixed_90d")}</b>、30 天 <b>{wr_txt(ru["yes"],"fixed_30d")}</b>'
            f'　<span class="vs">對照「{E(ru["no_lbl"])}」：90 天 {wr_txt(ru["no"],"fixed_90d")}、30 天 {wr_txt(ru["no"],"fixed_30d")}</span></div>'
            f'<div class="fld-note">怎麼算：{E(ru["how"])}；母體＝有方向＋已滿期＋查得到價</div></div>')
rules_html = "".join(rule_row(ru) for ru in RULES)
rules_html += (f'<div class="rule-row"><div class="rule-h"><span class="rid">R5</span><b>規律：他唱衰的不要跟著看空</b></div>'
               f'<div class="rule-n">→ 看空 90 天只有 <b class="hi">{wr_txt(SHORT,"fixed_90d")}</b>、台股看空 {wr_txt(SHORT_TW,"fixed_90d")}（30 天 {wr_txt(SHORT,"fixed_30d")}）'
               f'　<span class="vs">對照看多：90 天 {wr_txt([r for r in DIRECTED if r["target"]["direction"]=="long"],"fixed_90d")}</span></div>'
               f'<div class="fld-note">母體只有 50 幾筆，只能當觀察；名單因此只收看多。來源的「看空」＝他唱衰，不是他真的放空</div></div>')
rules_html += (f'<div class="rule-row weak"><div class="rule-h"><span class="rid">R6</span><b>規律（關鍵字粗配對，n 小）：原話出現「便宜／估值／本益比」</b></div>'
               f'<div class="rule-n">→ 30 天 <b>{wr_txt(KW_CHEAP,"fixed_30d")}</b>、90 天 {wr_txt(KW_CHEAP,"fixed_90d")}；反過來原話講「財報／guidance」只有 30 天 {wr_txt(KW_EARN,"fixed_30d")}</div>'
               f'<div class="fld-note">只是字串比對，沒有讀語意；母體 30 筆上下，先當線索不當結論</div></div>')
rules_html += ('<div class="rule-row weak"><div class="rule-h"><span class="rid">R7</span><b>示意（未驗證）：他說「盤面不對、降主動部位」之後那幾集，看多訊號準度會掉</b></div>'
               '<div class="rule-n">→ 算不出來：第 3 層「何時該停」目前 992 筆幾乎全空（還沒做語意配對），這條只是示意正式版要驗的方向</div></div>')

WINDOW = 30
cutoff = (date.fromisoformat(PRICE_TO_MAX) - timedelta(days=WINDOW)).isoformat()
recent = sorted([r for r in R if (r["backtest"]["entry_date"] or "") >= cutoff], key=lambda r: r["backtest"]["entry_date"], reverse=True)
picks, excluded = {}, []
for r in recent:
    t = r["target"]
    if t["direction"] == "short":
        excluded.append((r, "看空（R5：他唱衰的不跟）")); continue
    if t["direction"] == "neutral":
        excluded.append((r, "沒方向")); continue
    hits = [ru["id"] for ru in RULES if ru["test"](r)]
    if not hits:
        excluded.append((r, "看多但沒觸發任何規律（不連講、非老面孔、講的是營收／熱度）")); continue
    if t["ticker"] in picks:
        picks[t["ticker"]]["hits"] = sorted(set(picks[t["ticker"]]["hits"]) | set(hits))
        excluded.append((r, "同一檔已有更新一句（規律已併入）")); continue
    picks[t["ticker"]] = {"r": r, "hits": hits}
# 觸發最強規律的排前面：R4 > R1 > R3 > R2
def pick_score(p): return (("R4" in p["hits"]) * 8 + ("R1" in p["hits"]) * 4 + ("R3" in p["hits"]) * 2 + ("R2" in p["hits"]), p["r"]["backtest"]["entry_date"])
picks_sorted = sorted(picks.values(), key=pick_score, reverse=True)
RULE_NAME = {ru["id"]: ru["name"] for ru in RULES}

def pick_card(p, n):
    r = p["r"]; u, t, b = r["utterance"], r["target"], r["backtest"]
    tag = t["judgment"]["primary_tag"] or "（無標籤）"
    td = b["horizons"]["to_date"]
    cur = td["return_pct"] if td["status"] == "scored" else None
    curCls = "w" if (cur or 0) > 0 else "l" if (cur or 0) < 0 else "p"
    hist = tk_stat[t["ticker"]]
    chips = "".join(f'<span class="chip">{hid}</span>{E(RULE_NAME[hid])}' + ("、" if i < len(p["hits"]) - 1 else "") for i, hid in enumerate(p["hits"]))
    best = max(p["hits"], key=lambda h: {"R4": 4, "R1": 3, "R3": 2, "R2": 1}[h])
    best_rate = wr_txt(next(ru for ru in RULES if ru["id"] == best)["yes"], "fixed_90d")
    q = u["exact_quote"] or ""
    return f"""<div class="pick">
  <div class="pk-r1"><span class="pk-n">{n}</span><span class="led-nm">{E(t["stock_name"] or t["ticker"])}</span><span class="led-cd">{E(t["ticker"])} · {"台股" if t["market"]=="TW" else "美股"}</span><span class="led-dir bull">↑ 看多</span></div>
  <div class="led-r2">{E(u["episode_id"])} · {b["entry_date"]}（{days_ago(b["entry_date"])} 天前）· 信心 {E(t["confidence"])} · {E(tag)} · 之前講過 {cnt_before(r)} 次</div>
  <div class="hits">觸發：{chips}<span class="hit-rate">→ 最強那條 90 天 {best_rate}</span></div>
  <blockquote class="led-q">「{E(q)}」</blockquote>
  <div class="pk-grid">
    <div><div class="k">這檔本身過去準度</div><div class="v">30 天 {stat_txt(hist,"fixed_30d")}<br>90 天 {stat_txt(hist,"fixed_90d")}</div></div>
    <div><div class="k">講完到現在漲跌</div><div class="v big {curCls}">{pct(cur, 2) if cur is not None else "無資料"}</div><div class="fld-note">至 {td["as_of"] or PRICE_TO_MAX} 收盤</div></div>
  </div>
</div>"""

pick_cards = "".join(pick_card(p, i + 1) for i, p in enumerate(picks_sorted))
excl_rows = "".join(f'<div>{E(r["target"]["stock_name"] or r["target"]["ticker"])} {E(r["target"]["ticker"])}（{E(r["utterance"]["episode_id"])} {r["backtest"]["entry_date"]}）— {E(why)}</div>' for r, why in excluded)
B_MAX = 40
cardsB = "".join(led_card(r, i) for i, r in enumerate(recs_sorted[:B_MAX]))
extra_css_B = """
  .pick{border-bottom:1px solid #eee;padding:13px 16px;}
  .pk-r1{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;}
  .pk-n{font-size:12px;font-weight:bold;color:#fff;background:#2b6cb0;border-radius:50%;width:20px;height:20px;line-height:20px;text-align:center;flex:none;}
  .pk-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px;}
  .pk-grid>div{background:#f8f9fa;border:1px solid #eee;border-radius:6px;padding:7px 8px;}
  .pk-grid .k{font-size:11px;color:#999;margin-bottom:2px;}
  .pk-grid .v{font-size:12.5px;color:#3d4650;line-height:1.6;}
  .pk-grid .v.big{font-size:20px;font-weight:800;}
  .pk-grid .w{color:#c0392b;} .pk-grid .l{color:#2b8a3e;} .pk-grid .p{color:#8a8f94;}
  @media(max-width:600px){.pick{padding:12px 12px;}}
  .hits{margin-top:6px;font-size:12.5px;color:#3d4650;line-height:1.9;}
  .chip{display:inline-block;font-size:11px;font-weight:bold;color:#fff;background:#2b6cb0;border-radius:4px;padding:0 5px;margin-right:3px;}
  .hit-rate{display:inline-block;margin-left:6px;color:#c0392b;font-weight:700;}
  .rule-row{padding:9px 16px;border-bottom:1px solid #eee;font-size:13px;line-height:1.7;}
  .rule-row.weak{background:#fafafa;color:#777;}
  .rule-h{color:#1a252f;}
  .rid{display:inline-block;font-size:11px;font-weight:bold;color:#fff;background:#1a252f;border-radius:4px;padding:0 5px;margin-right:6px;}
  .rule-row.weak .rid{background:#999;}
  .rule-n{color:#3d4650;margin-top:2px;}
  .rule-n .hi{color:#c0392b;font-size:15px;}
  .rule-n .vs{color:#8a8f94;font-size:12px;}
  @media(max-width:600px){.rule-row{padding:9px 12px;}}
  .rule{padding:8px 16px;background:#fffdf3;border-bottom:1px solid #eee;font-size:12px;color:#7a6a00;line-height:1.7;}
  .rule b{color:#5c4b00;}
"""
bodyB = f"""
{header(f"全集匯總 · {COMPUTED_AT} · 最新分析至 {LATEST_EP}")}
{nav("signal")}
{banner("B：規律與名單在最前面",
        f"每條規律的百分比與 n、名單裡每檔的原話、日期、這檔過去準度、講完到現在的漲跌，以及下方計分板與每筆回測，都是從 gooaye-site {COMPUTED_AT} 的 992 筆真算的（股價到 {PRICE_TO_MAX}）。",
        "規律 R1～R5 是 AI 從資料裡挖的、還沒經丹尼爾看過；R6 是關鍵字粗配對、R7 是示意（算不出來）；「名單」＝規律自動生出來的，不是投資建議；導覽列點不動；原本報告內容用連結代替。")}

<div class="sec-bar" style="background:#1a252f;border-bottom:none;"><span class="t" style="color:#fff;font-size:15px;">🔍 AI 從他的話裡找到的規律</span><span class="d" style="color:#b3c1cd;">全站基準：30 天 {base30[0]/base30[1]*100:.1f}%（{base30[0]}/{base30[1]}）· 90 天 {base90[0]/base90[1]*100:.1f}%（{base90[0]}/{base90[1]}）</span></div>
<div class="rule"><b>怎麼讀：</b>每條規律＝「他講話時有某個特徵 → 之後 30／90 天有賺錢的比例」，後面括號是分子／分母；比全站基準高的才算規律。<b>這些是 AI 挖的，不是丹尼爾定的；他要做的是看這些規律像不像真的。</b></div>
{rules_html}

<div class="sec-bar" style="background:#1a252f;border-bottom:none;margin-top:6px;"><span class="t" style="color:#fff;font-size:15px;">👀 由規律生出的名單（{len(picks_sorted)} 檔）</span><span class="d" style="color:#b3c1cd;">最近 {WINDOW} 天（{cutoff} 起）講看多、且至少觸發 R1～R4 一條</span></div>
<div class="rule"><b>名單怎麼生：</b>最近 {WINDOW} 天講過 → 只留看多（R5）→ 至少觸發 R1～R4 其中一條 → 同一檔只留最新一句、規律合併 → 觸發越強的排越前（R4＞R1＞R3＞R2）。</div>
{pick_cards if picks_sorted else '<div class="empty-state">最近 30 天沒有觸發任何規律的看多訊號</div>'}
<div class="sec-head" onclick="toggleSec('excl', this)"><span class="arrow">▸</span> 最近 {WINDOW} 天講過但沒進名單的 {len(excluded)} 筆（為什麼）</div>
<div id="excl" style="display:none;padding:8px 16px;font-size:12.5px;color:#666;line-height:1.8;border-bottom:1px solid #eee;">{excl_rows or "無"}</div>

<div class="sec-bar" style="margin-top:6px;"><span class="t">證據 1：他準不準</span><span class="d">全部 {m['record_count']} 筆訊號的計分板</span></div>
{scoreboard_row()}
<div style="padding:10px 16px;border-bottom:1px solid #eee;font-size:13px;line-height:1.9;">
{"".join(f'<div>{lbl}：30 天 <b>{rate(BOARD["mainline/fixed_30d/"+k])}</b>（{frac(BOARD["mainline/fixed_30d/"+k])}）｜90 天 <b>{rate(BOARD["mainline/fixed_90d/"+k])}</b>（{frac(BOARD["mainline/fixed_90d/"+k])}）</div>' for lbl,k in [("台股","TW"),("美股","US"),("看多","long"),("看空","short")])}
<div style="margin-top:6px;"><b>依類型（90 天）</b>：{"　".join(f"{E(t)} {stat_txt(v,'fixed_90d')}" for t,v in sorted(tag_stat.items(), key=lambda kv:-(kv[1]['fixed_90d'][1])))}</div>
<div class="fld-note">看空只有 50 幾筆，只能當觀察。類型準度是 demo 自己從 992 筆算的，母體＝有方向＋已滿期＋查得到價。</div>
</div>

<div class="sec-bar"><span class="t">證據 2：每一筆回測</span><span class="d">最新 {B_MAX} 筆，點開看原話與 AI 解讀</span></div>
<div>{cardsB}</div>
<div class="empty-state">已顯示最新 {B_MAX} 筆，全部共 {m['record_count']} 筆</div>

<div class="sec-head" style="text-align:center;cursor:default;">📊 原本的每日訊號報告、🔥 關注度、📄 逐字稿 → <a href="https://jack20773.github.io/stock-signal/" style="color:#2b6cb0;">放在原站（開新頁）</a>　<span style="font-weight:normal;color:#999;">（正式版會是同一站的分頁；demo 先用連結代替）</span></div>
<div class="foot">demo B · 資料：gooaye-site out/mainline.json、scoreboard.json（computed_at {E(m['computed_at'])}）· <a href="index.html">← 回三版入口</a></div>
"""
(ROOT / "demo-b-picks-first.html").write_text(page("股癌訊號勝率追蹤（demo B 規律與名單在最前面）", bodyB, extra_css_B), encoding="utf-8")

# ══════════════════════════════════════════════════════════════
# Demo C：獨立分頁（嵌入 gooaye-site 現有整頁）
# ══════════════════════════════════════════════════════════════
(ROOT / "_embed").mkdir(exist_ok=True)
shutil.copyfile(GS / "site" / "index.html", ROOT / "_embed" / "backtest.html")
extra_css_C = """
  .back{display:block;padding:9px 16px;background:#eef4fb;border-bottom:1px solid #dce9f7;font-size:13px;color:#2b6cb0;font-weight:bold;text-decoration:none;}
  .back:hover{background:#e2ecf8;}
  iframe#bt{display:block;width:100%;border:0;min-height:600px;}
  .open-new{padding:8px 16px;font-size:12px;color:#999;text-align:center;border-top:1px solid #eee;}
  .open-new a{color:#2b6cb0;}
"""
extra_js_C = """
(function(){var f=document.getElementById('bt');function fit(){try{var d=f.contentDocument||f.contentWindow.document;if(d&&d.body){f.style.height=(d.documentElement.scrollHeight+20)+'px';}}catch(e){}}
f.addEventListener('load',function(){fit();setTimeout(fit,300);setTimeout(fit,1500);});window.addEventListener('resize',fit);})();
"""
bodyC = f"""
{header(f"全集匯總 · {COMPUTED_AT} · 最新分析至 {LATEST_EP}")}
{nav("bt", extra_tab=True)}
{banner("C：獨立分頁",
        f"「回測」分頁裡的整頁內容＝gooaye-site 現在真的產出的那一頁（{COMPUTED_AT} 算的，一字未改，直接嵌入）。",
        "導覽列另外三個分頁點不動；「← 回股癌報告」在 demo 裡只回到入口頁；嵌入頁本身有自己的字型與配色，正式版要不要統一成原站那套，等丹尼爾定。")}
<a class="back" href="index.html">← 回股癌報告（demo 裡＝回入口頁）</a>
<iframe id="bt" src="_embed/backtest.html" title="股癌回測站（嵌入）"></iframe>
<div class="open-new">嵌入頁若顯示不全，<a href="_embed/backtest.html" target="_blank" rel="noopener">在新分頁單獨打開</a></div>
<div class="foot">demo C · 嵌入來源：gooaye-site site/index.html（原樣複製）· <a href="index.html">← 回三版入口</a></div>
"""
(ROOT / "demo-c-tab.html").write_text(page("股癌訊號勝率追蹤（demo C 回測獨立分頁）", bodyC, extra_css_C, extra_js_C), encoding="utf-8")

# ══════════════════════════════════════════════════════════════
# index.html：三版入口
# ══════════════════════════════════════════════════════════════
extra_css_I = """
  .opt{display:block;margin:12px 16px;padding:14px 16px;border:1px solid #dce9f7;border-radius:8px;text-decoration:none;color:#333;background:#fafcff;}
  .opt:hover{background:#eef4fb;}
  .opt .t{font-size:16px;font-weight:bold;color:#1a252f;}
  .opt .g{font-size:13px;color:#555;margin-top:6px;line-height:1.7;}
  .opt .g b{color:#2b6cb0;}
  .opt .u{font-size:11px;color:#aaa;margin-top:4px;word-break:break-all;}
"""
bodyI = f"""
{header("三種「回測併進原站」的長相 · demo 入口")}
<div class="demo-banner"><b>🧪 這裡是 demo 入口</b>。三個版本用的都是同一批真資料（gooaye-site {COMPUTED_AT} 算的 {m['record_count']} 筆、股價到 {PRICE_TO_MAX}），差別只在「回測放在哪裡」。手機直接點開看，選一個順眼的，或講哪裡不對。</div>
<a class="opt" href="demo-a-inline.html"><div class="t">A · 貼在訊號旁</div><div class="g"><b>這版猜的是：</b>你不想多一個地方看——回測要出現在你本來就在看的那一行旁邊。長得就是原本首頁，每筆訊號多一行「講完 30 天／90 天」，頁首多一條準度計分板。</div><div class="u">demo-a-inline.html</div></a>
<a class="opt" href="demo-b-picks-first.html"><div class="t">B · 規律與名單在最前面</div><div class="g"><b>這版猜的是：</b>你要的是「AI 從他的話裡挖出的隱藏勝率規律」＋由規律生出的「接下來看哪些」，其餘都是證據。第一屏上段是規律（每條附 n）、下段是名單（每支標觸發了哪條規律＋原話），往下才是計分板與每筆回測，原本報告放最下面。</div><div class="u">demo-b-picks-first.html</div></a>
<a class="opt" href="demo-c-tab.html"><div class="t">C · 獨立分頁</div><div class="g"><b>這版猜的是：</b>回測是另一種看法，跟每日報告分開、各看各的。導覽列多一個「回測」分頁，內容就是現在 gooaye-site 那整頁，加一個「← 回股癌報告」。</div><div class="u">demo-c-tab.html</div></a>
<a class="opt" href="backtest_reasoning.html"><div class="t">D · 規律第二輪：AI 讀「理由」（2026-09-16）</div><div class="g"><b>這版是什麼：</b>AI 讀他每一句的<b>理由</b>（產業結構／估值／財報／政策／情緒……＋語氣、時間框架、本人有沒有持有）當特徵再挖一次規律，頁面多一張「理由分布」表。<b>誠實結果：</b>第二輪 147 條候選、通過 0——但不是「試過不成立」，是留出組 75 筆只有 17 筆有 AI 判讀（最後幾批判讀撞錯誤），根本判不了；頁面紅框寫明。第一輪那條通過的規律負對照 p≈0.40，仍只能當線索。</div><div class="u">backtest_reasoning.html</div></a>
<div class="foot">三版共用資料：gooaye-site out/mainline.json、scoreboard.json · 建於 {date.today().isoformat()} · 挑法／導覽皆暫定，頁首黃條有寫哪些是真的哪些是假的</div>
"""
(ROOT / "index.html").write_text(page("股癌回測併站 demo 入口", bodyI, extra_css_I), encoding="utf-8")

print("picks:", [(p["r"]["target"]["ticker"], p["hits"]) for p in picks_sorted])
print("excluded:", [(r["target"]["ticker"], why) for r, why in excluded])
print("wrote:", [p.name for p in ROOT.glob("*.html")], "embed:", (ROOT / "_embed" / "backtest.html").stat().st_size)
