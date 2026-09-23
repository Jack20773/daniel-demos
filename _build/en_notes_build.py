# -*- coding: utf-8 -*-
"""
en_notes_build.py

把 english_notes.html 從「資料 + 產生器」重新生出來：
  1. 讀 en_notes_data.json（10 個單字、5 則文法、4 張課本頁、inbox、seen_message_ids）
  2. 唯讀撈 Discord 英文頻道全部訊息（bot token，只讀不寫，token 絕不 print／絕不寫檔）
  3. seen_message_ids 沒收過的訊息 → 追加進 inbox；帶圖片的另外在 book 補一筆 ocr_status=pending
  4. 從資料重新產生 english_notes.html（版面/CSS/JS 一字不改，只有卡片內容是灌進去的）

跑法：
  python -X utf8 en_notes_build.py                 # 撈新訊息 + 重產 HTML + 存回 JSON
  python -X utf8 en_notes_build.py --no-fetch       # 只從現有 JSON 重產 HTML，不連 Discord
  python -X utf8 en_notes_build.py --dry-run        # 什麼都不寫，只印會做什麼

本腳本不跑 git（不 add/commit/push），也不會修改 access.json 或其他 Discord 設定。
"""

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>英文筆記</title>
<meta name="description" content="丹尼爾的英文課筆記：單字發音、文法、課本頁（文字可搜尋）">
<style>
:root{
  --bg:#f7f6f3; --card:#ffffff; --ink:#1c1b19; --ink2:#5c5852; --line:#e3dfd8;
  --accent:#a4552c; --accent-soft:#f3e7df; --hl:#ffe9a8; --shadow:0 1px 2px rgba(0,0,0,.05),0 6px 16px rgba(0,0,0,.05);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#16151a; --card:#201f26; --ink:#eeeae4; --ink2:#a6a09a; --line:#332f38;
    --accent:#e0a17a; --accent-soft:#33261e; --hl:#6b5620; --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  --bg:#16151a; --card:#201f26; --ink:#eeeae4; --ink2:#a6a09a; --line:#332f38;
  --accent:#e0a17a; --accent-soft:#33261e; --hl:#6b5620; --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  font-size:16px; line-height:1.65; overflow-x:hidden;
}
.wrap{max-width:720px; margin:0 auto; padding:0 16px 96px}

header{padding:28px 0 14px}
h1{font-size:26px; margin:0 0 4px; letter-spacing:.01em}
.sub{color:var(--ink2); font-size:13.5px; margin:0}

.tools{position:sticky; top:0; z-index:20; background:var(--bg); padding:10px 0 8px; margin:0 -16px; padding-left:16px; padding-right:16px; border-bottom:1px solid var(--line)}
.search{position:relative}
.search input{
  width:100%; padding:12px 40px 12px 40px; font-size:16px; border-radius:12px;
  border:1px solid var(--line); background:var(--card); color:var(--ink); box-shadow:var(--shadow);
}
.search input:focus{outline:2px solid var(--accent); outline-offset:1px}
.search .mag{position:absolute; left:13px; top:50%; transform:translateY(-50%); color:var(--ink2); font-size:15px}
.search .clear{position:absolute; right:8px; top:50%; transform:translateY(-50%); border:0; background:transparent; color:var(--ink2); font-size:20px; padding:6px 10px; cursor:pointer; display:none; line-height:1}
.tabs{display:flex; gap:6px; margin-top:8px; overflow-x:auto; scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{
  flex:0 0 auto; border:1px solid var(--line); background:var(--card); color:var(--ink2);
  padding:7px 14px; border-radius:999px; font-size:14px; cursor:pointer; white-space:nowrap; font-family:inherit;
}
.tab[aria-selected="true"]{background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .tab[aria-selected="true"]{color:#16151a}}
:root[data-theme="dark"] .tab[aria-selected="true"]{color:#16151a}

.hint{color:var(--ink2); font-size:12.5px; margin:10px 0 0}
section.group{margin-top:26px}
.group > h2{font-size:15px; letter-spacing:.06em; text-transform:none; color:var(--ink2); margin:0 0 10px; font-weight:600}
.day{display:inline-block; font-size:12px; color:var(--ink2); background:var(--accent-soft); border-radius:999px; padding:2px 9px; margin-left:6px; vertical-align:2px}

.card{background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px 16px; margin-bottom:10px; box-shadow:var(--shadow)}

.word{display:flex; align-items:baseline; gap:10px; flex-wrap:wrap}
.word .en{font-size:21px; font-weight:650; letter-spacing:.01em}
.word .pos{font-size:12.5px; color:var(--ink2)}
.ipa{margin:6px 0 0; display:flex; flex-wrap:wrap; gap:6px 14px; font-size:15px}
.ipa span b{font-weight:600; color:var(--ink2); font-size:12px; margin-right:5px; letter-spacing:.04em}
.ipa code{font-family:"Doulos SIL","Charis SIL","Gentium Plus",Georgia,"Times New Roman",serif; font-size:16.5px; background:transparent; color:var(--ink)}
.note{margin:8px 0 0; font-size:14.5px; color:var(--ink2); border-left:3px solid var(--accent-soft); padding-left:10px}
.note b{color:var(--accent); font-weight:600}
.say{border:1px solid var(--line); background:transparent; color:var(--ink2); border-radius:999px; font-size:13px; padding:4px 11px; cursor:pointer; font-family:inherit; margin-left:auto}
.say:active{background:var(--accent-soft)}

.g-title{font-size:17px; font-weight:650; margin:0 0 6px}
.g-body{font-size:15px; margin:0}
.g-body p{margin:0 0 8px}
.g-body p:last-child{margin-bottom:0}
.ex{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace; font-size:14.5px; background:var(--accent-soft); border-radius:8px; padding:8px 11px; margin:8px 0; overflow-x:auto}
.ex i{font-style:normal; color:var(--ink2); font-family:inherit}
.tense{margin:12px 0 2px}
.tense .row{display:flex; align-items:flex-start; gap:8px; padding:8px 0; border-top:1px solid var(--line)}
.tense .row:first-child{border-top:0; padding-top:2px}
.tense .when{flex:0 0 46px; font-weight:650; font-size:15px; padding-top:3px}
.tense .states{display:flex; flex-wrap:wrap; gap:6px}
.tense .states span{background:var(--accent-soft); border-radius:8px; padding:4px 9px; font-size:13.5px; white-space:nowrap}
.tense .legend{font-size:12.5px; color:var(--ink2); margin:8px 0 0}

figure{margin:0 0 10px}
figure img{width:100%; height:auto; display:block; border-radius:12px; border:1px solid var(--line); background:#fff}
figcaption{font-size:13px; color:var(--ink2); margin-top:8px}
details.ocr{margin-top:8px; border-top:1px dashed var(--line); padding-top:8px}
details.ocr summary{cursor:pointer; font-size:13.5px; color:var(--accent); font-weight:600; list-style:none}
details.ocr summary::-webkit-details-marker{display:none}
details.ocr summary::before{content:"▸ "; display:inline-block; transition:transform .15s}
details.ocr[open] summary::before{content:"▾ "}
details.ocr .txt{font-size:14px; white-space:pre-wrap; color:var(--ink2); margin-top:8px; line-height:1.7}

mark{background:var(--hl); color:inherit; border-radius:3px; padding:0 1px}
.empty{color:var(--ink2); font-size:14.5px; padding:26px 0; text-align:center}
footer{margin-top:34px; border-top:1px solid var(--line); padding-top:16px; color:var(--ink2); font-size:13px}
footer h3{font-size:13.5px; margin:0 0 6px; color:var(--ink)}
footer ul{margin:0 0 12px; padding-left:18px}
footer li{margin-bottom:3px}
.hidden{display:none !important}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>英文筆記</h1>
  <p class="sub">課堂筆記整理　·　素材來自英文頻道 9/09、9/16（9/23 那批是直接傳給我的）　·　共 __COUNTS__</p>
</header>

<div class="tools">
  <div class="search">
    <span class="mag">🔍</span>
    <input id="q" type="search" placeholder="搜單字、音標、中文、課本上的字…" autocomplete="off" aria-label="搜尋筆記">
    <button class="clear" id="clr" aria-label="清除">×</button>
  </div>
  <div class="tabs" role="tablist">
    <button class="tab" role="tab" data-t="all" aria-selected="true">全部</button>
    <button class="tab" role="tab" data-t="word" aria-selected="false">單字發音</button>
    <button class="tab" role="tab" data-t="gram" aria-selected="false">文法</button>
    <button class="tab" role="tab" data-t="book" aria-selected="false">課本頁</button>
__RES_TAB____INBOX_TAB__  </div>
</div>

<p class="hint" id="hint">點單字右邊的「唸」可以聽發音（手機需開聲音）。課本頁的字已經抄成文字，搜尋搜得到。</p>

<!-- ============ 單字 ============ -->
<section class="group" data-t="word">
  <h2>單字發音<span class="day">9/09 這堂：θ / ð / ʒ 這幾個音</span></h2>

__WORD_CARDS__
</section>

<!-- ============ 文法 ============ -->
<section class="group" data-t="gram">
  <h2>文法<span class="day">9/16 這堂</span></h2>

__GRAM_CARDS__
</section>

<!-- ============ 課本頁 ============ -->
<section class="group" data-t="book">
  <h2>課本頁<span class="day">字已抄成文字，搜尋搜得到</span></h2>

__BOOK_CARDS__
</section>
__RES_SECTION__

__INBOX_SECTION__<p class="empty hidden" id="empty">找不到「<span id="qshow"></span>」。換個字試試，或按上面的「全部」。</p>

<footer>
  <h3>這頁是怎麼來的</h3>
  <ul>
    <li>素材＝英文頻道 9/09（14 則）與 9/16（22 則）的訊息，加 6 張課本照片（9/23 補上兩張：練習 8.2、和上一份練習題寫完答案的版本）。</li>
    <li>照片上的字是抄出來的，所以搜尋搜得到；看不清楚的地方標成空白，沒有猜。</li>
    <li>你 9/16 貼的 Google 文件要登入才看得到，這頁沒有收進來。</li>
  </ul>
  <h3>我幫你順過的語音誤字（覺得不對就跟我說）</h3>
  <ul>
    <li>「現代簡單式」→ <b>現在簡單式</b></li>
    <li>「前面的 GO 舊式常態性的」→ <b>前面的 go 就是常態性的</b></li>
    <li>「to eat ice cream 式事情」→ <b>是事情</b></li>
    <li>「他會照照片嗎」→ <b>他會拍照嗎</b></li>
  </ul>
  <p style="margin:0">demo 版本　·　產於 __GENERATED_AT__</p>
</footer>

</div>

<script>
(function(){
  var q=document.getElementById('q'), clr=document.getElementById('clr'),
      empty=document.getElementById('empty'), qshow=document.getElementById('qshow'),
      hint=document.getElementById('hint'),
      cards=[].slice.call(document.querySelectorAll('.card')),
      groups=[].slice.call(document.querySelectorAll('section.group')),
      tabs=[].slice.call(document.querySelectorAll('.tab')),
      cur='all';

  // 記住每張卡片的原始 HTML，才能反覆上／下螢光筆
  cards.forEach(function(c){ c.dataset.html=c.innerHTML; });

  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }

  function highlight(el, term){
    if(!term){ el.innerHTML=el.dataset.html; return true; }
    el.innerHTML=el.dataset.html;
    var re=new RegExp(esc(term),'gi'), found=false;
    var walker=document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null), nodes=[], n;
    while((n=walker.nextNode())) nodes.push(n);
    nodes.forEach(function(node){
      var txt=node.nodeValue;
      if(!re.test(txt)) return;
      re.lastIndex=0; found=true;
      var frag=document.createDocumentFragment(), last=0, m;
      while((m=re.exec(txt))!==null){
        if(m.index>last) frag.appendChild(document.createTextNode(txt.slice(last,m.index)));
        var mk=document.createElement('mark'); mk.textContent=m[0]; frag.appendChild(mk);
        last=m.index+m[0].length;
        if(m[0].length===0) re.lastIndex++;
      }
      if(last<txt.length) frag.appendChild(document.createTextNode(txt.slice(last)));
      node.parentNode.replaceChild(frag,node);
    });
    return found;
  }

  function apply(){
    var term=q.value.trim(), shown=0;
    clr.style.display=term?'block':'none';
    hint.style.display=term?'none':'';
    cards.forEach(function(c){
      var okTab=(cur==='all'||c.dataset.t===cur);
      var okTerm=true;
      if(term){
        // 先用純文字判斷有沒有中，再決定要不要上螢光筆
        okTerm=(c.dataset.html.replace(/<[^>]*>/g,' ')).toLowerCase().indexOf(term.toLowerCase())>=0;
      }
      var show=okTab&&okTerm;
      c.classList.toggle('hidden',!show);
      if(show){ highlight(c, term); shown++; }
      else { c.innerHTML=c.dataset.html; }
      // 搜尋時把收合的課本文字自動打開，才看得到命中的字
      if(show&&term){ var d=c.querySelector('details.ocr'); if(d) d.open=true; }
    });
    groups.forEach(function(g){
      var any=[].slice.call(g.querySelectorAll('.card')).some(function(c){return !c.classList.contains('hidden');});
      g.classList.toggle('hidden',!any);
    });
    qshow.textContent=term;
    empty.classList.toggle('hidden', shown>0);
  }

  q.addEventListener('input', apply);
  clr.addEventListener('click', function(){ q.value=''; q.focus(); apply(); });
  tabs.forEach(function(t){
    t.addEventListener('click', function(){
      tabs.forEach(function(x){ x.setAttribute('aria-selected', x===t?'true':'false'); });
      cur=t.dataset.t; apply();
      window.scrollTo({top:0, behavior:'smooth'});
    });
  });

  // 唸單字（瀏覽器內建，不連外、不花錢）
  document.addEventListener('click', function(e){
    var b=e.target.closest('.say'); if(!b) return;
    if(!('speechSynthesis' in window)){ b.textContent='此裝置不支援'; return; }
    try{
      speechSynthesis.cancel();
      var u=new SpeechSynthesisUtterance(b.dataset.say);
      u.lang='en-US'; u.rate=0.85;
      speechSynthesis.speak(u);
      var old=b.textContent; b.textContent='♪';
      u.onend=function(){ b.textContent=old; };
      setTimeout(function(){ b.textContent=old; }, 2500);
    }catch(err){ b.textContent='放不出來'; }
  });

  apply();
})();
</script>
</body>
</html>
"""

# ============================================================
# 以下為產生器邏輯。token 只在本程序記憶體內用，絕不 print、絕不寫檔。
# ============================================================
import os, re, sys, json, argparse, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)  # daniel-demos/
DATA_PATH = os.path.join(HERE, "en_notes_data.json")
HTML_PATH = os.path.join(PROJECT_DIR, "english_notes.html")
IMG_DIR = os.path.join(PROJECT_DIR, "english_notes_img")
CHANNEL_ID = "1547231069923713084"


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_data(data, dry_run):
    if dry_run:
        return
    with open(DATA_PATH, "w", encoding="utf-8", newline=chr(10)) as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def get_token():
    # 唯讀 bot token；只在本函式回傳值、呼叫端絕不 print 它。
    envp = os.path.join(os.path.expanduser("~"), ".claude", "channels", "discord", "." + "env")
    tok = None
    with open(envp, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*([A-Za-z_]+)\s*=\s*(.+?)\s*$", line)
            if m and "TOKEN" in m.group(1).upper():
                tok = m.group(2).strip().strip('"').strip("'")
    if not tok:
        raise SystemExit("NO_TOKEN_VAR_FOUND")
    return tok


def fetch_channel_messages():
    tok = get_token()
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=100",
        headers={"Authorization": "Bot " + tok, "User-Agent": "en-notes-build/1.0"},
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        msgs = json.loads(r.read().decode())
    return list(reversed(msgs))  # 舊到新


def download_attachment(url, dest_path):
    req = urllib.request.Request(url, headers={"User-Agent": "en-notes-build/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    with open(dest_path, "wb") as fh:
        fh.write(data)
    return len(data)


def sync_inbox(data, dry_run):
    """撈頻道全部訊息，把 seen_message_ids 沒有的追加進 inbox；
    帶圖片附件的新訊息另外在 book 加一筆 ocr_status=pending，圖存到 english_notes_img/。
    回傳 (新增文字則數, 新增圖片張數)。"""
    seen = set(data.get("seen_message_ids", []))
    msgs = fetch_channel_messages()
    new_text = 0
    new_imgs = 0
    for m in msgs:
        mid = m["id"]
        if mid in seen:
            continue
        seen.add(mid)
        data.setdefault("seen_message_ids", []).append(mid)
        atts = m.get("attachments", [])
        img_atts = [a for a in atts if (a.get("content_type") or "").startswith("image")]
        text = m.get("content") or ""
        data.setdefault("inbox", []).append({
            "id": mid,
            "ts": m["timestamp"],
            "text": text,
            "attachments": [a.get("filename") for a in atts],
        })
        new_text += 1
        for a in img_atts:
            new_imgs += 1
            ext = os.path.splitext(a.get("filename", "x.jpg"))[1] or ".jpg"
            fname = f"inbox_{mid}{ext}"
            dest = os.path.join(IMG_DIR, fname)
            if not dry_run:
                os.makedirs(IMG_DIR, exist_ok=True)
                download_attachment(a["url"], dest)
            data.setdefault("book", []).append({
                "img": "english_notes_img/" + fname,
                "alt": "新貼的課本照片，還沒抄字",
                "caption": "（新貼，還沒整理）",
                "date": m["timestamp"][:10],
                "ocr_status": "pending",
                "ocr": "",
            })
    return new_text, new_imgs


# ---------- HTML 產生 ----------

def esc(s):
    return (s or "")


def render_word_card(w):
    pos_html = f'<span class="pos">{esc(w.get("pos"))}</span>' if w.get("pos") else ""
    return (
        '  <article class="card" data-t="word">\n'
        f'    <div class="word"><span class="en">{esc(w["en"])}</span>{pos_html}\n'
        f'      <button class="say" data-say="{esc(w.get("say") or w["en"])}">唸</button></div>\n'
        f'    <div class="ipa"><span><b>UK</b><code>{esc(w["uk"])}</code></span>'
        f'<span><b>US</b><code>{esc(w["us"])}</code></span></div>\n'
        f'    <p class="note">{w["note"]}</p>\n'
        '  </article>'
    )


def render_gram_block(b):
    t = b["type"]
    if t == "p":
        style_attr = f' style="{b["style"]}"' if b.get("style") else ""
        return f'      <p{style_attr}>{b["html"]}</p>'
    if t == "ex":
        return f'      <div class="ex">{b["html"]}</div>'
    if t == "tense":
        rows = []
        for row in b["rows"]:
            states = "".join(f"<span>{s}</span>" for s in row["states"])
            rows.append(f'        <div class="row"><div class="when">{row["when"]}</div>'
                         f'<div class="states">{states}</div></div>')
        lines = ['      <div class="tense">'] + rows
        lines.append(f'        <p class="legend">{b["legend"]}</p>')
        lines.append('      </div>')
        return "\n".join(lines)
    raise ValueError("unknown grammar block type: " + t)


def render_gram_card(g):
    body = "\n".join(render_gram_block(b) for b in g["blocks"])
    return (
        '  <article class="card" data-t="gram">\n'
        f'    <p class="g-title">{g["title"]}</p>\n'
        '    <div class="g-body">\n'
        f'{body}\n'
        '    </div>\n'
        '  </article>'
    )


def render_book_card(b):
    if b.get("ocr_status") == "pending":
        ocr_block = '    <p class="note" style="margin-top:8px">這張的字還沒抄，等下次整理</p>'
    else:
        ocr_block = f'    <details class="ocr"><summary>看這張圖上的文字</summary><div class="txt">{b.get("ocr", "")}</div></details>'
    return (
        '  <article class="card" data-t="book">\n'
        '    <figure>\n'
        f'      <img src="{b["img"]}" alt="{b.get("alt", "")}">\n'
        f'      <figcaption>{b["caption"]}　<span style="color:var(--accent)">{b["date"]}</span></figcaption>\n'
        '    </figure>\n'
        f'{ocr_block}\n'
        '  </article>'
    )


def render_resource_card(r):
    return (
        '  <article class="card" data-t="res">\n'
        f'    <p class="g-title"><a href="{r["url"]}" target="_blank" rel="noopener">{esc(r["name"])}</a>'
        f'　<span style="color:var(--accent);font-size:13px;font-weight:400">{esc(r.get("date", ""))}</span></p>\n'
        f'    <p class="note" style="margin-top:6px">{r.get("note", "")}</p>\n'
        '  </article>'
    )


def render_inbox_card(it):
    date = (it.get("ts") or "")[:10]
    text = it.get("text") or "（無文字，附件見下）"
    atts = it.get("attachments") or []
    att_html = ""
    if atts:
        att_html = f'\n    <p class="note" style="margin-top:6px">附件：{", ".join(a for a in atts if a)}</p>'
    return (
        '  <article class="card" data-t="inbox">\n'
        f'    <p class="note" style="margin:0 0 6px">{date}</p>\n'
        f'    <p class="g-body" style="margin:0;white-space:pre-wrap">{text}</p>{att_html}\n'
        '  </article>'
    )


def render_html(data):
    words = data.get("words", [])
    grammar = data.get("grammar", [])
    book = data.get("book", [])
    inbox = data.get("inbox", [])
    resources = data.get("resources", [])

    counts = f'{len(words)} 個單字、{len(grammar)} 則文法、{len(book)} 張課本頁'
    if resources:
        counts += f'、{len(resources)} 個推薦資源'
    word_cards = "\n\n".join(render_word_card(w) for w in words)
    gram_cards = "\n\n".join(render_gram_card(g) for g in grammar)
    book_cards = "\n\n".join(render_book_card(b) for b in book)

    if resources:
        res_tab = '    <button class="tab" role="tab" data-t="res" aria-selected="false">資源</button>\n'
        res_cards = "\n\n".join(render_resource_card(r) for r in resources)
        res_section = (
            "\n<!-- ============ 老師推薦的資源 ============ -->\n"
            '<section class="group" data-t="res">\n'
            "  <h2>老師推薦的資源</h2>\n\n"
            f"{res_cards}\n"
            "</section>\n\n"
        )
    else:
        res_tab = ""
        res_section = "\n"

    if inbox:
        inbox_tab = '    <button class="tab" role="tab" data-t="inbox" aria-selected="false">新貼的</button>\n'
        inbox_cards = "\n\n".join(render_inbox_card(it) for it in inbox)
        inbox_section = (
            "\n<!-- ============ 新貼的 ============ -->\n"
            '<section class="group" data-t="inbox">\n'
            "  <h2>新貼的，還沒整理</h2>\n\n"
            f"{inbox_cards}\n"
            "</section>\n\n"
        )
    else:
        inbox_tab = ""
        inbox_section = "\n"

    generated_at = data.get("meta", {}).get("generated_at", "")

    html = TEMPLATE
    html = html.replace("__COUNTS__", counts)
    html = html.replace("__RES_TAB__", res_tab)
    html = html.replace("__INBOX_TAB__", inbox_tab)
    html = html.replace("__WORD_CARDS__", word_cards)
    html = html.replace("__GRAM_CARDS__", gram_cards)
    html = html.replace("__BOOK_CARDS__", book_cards)
    html = html.replace("__RES_SECTION__", res_section)
    html = html.replace("__INBOX_SECTION__", inbox_section)
    html = html.replace("__GENERATED_AT__", generated_at)
    return html


def main():
    ap = argparse.ArgumentParser(description="從 en_notes_data.json 重新產生 english_notes.html，可選擇先撈頻道新訊息。")
    ap.add_argument("--no-fetch", action="store_true", help="只從 JSON 重產 HTML，不連 Discord")
    ap.add_argument("--dry-run", action="store_true", help="什麼都不寫，只印會做什麼")
    args = ap.parse_args()

    data = load_data()
    before_words, before_gram, before_book, before_inbox = (
        len(data.get("words", [])), len(data.get("grammar", [])),
        len(data.get("book", [])), len(data.get("inbox", [])),
    )

    new_text = new_imgs = 0
    if not args.no_fetch:
        new_text, new_imgs = sync_inbox(data, args.dry_run)

    html = render_html(data)

    wrote = []
    if not args.dry_run:
        if not args.no_fetch:
            save_data(data, args.dry_run)
            wrote.append(DATA_PATH)
        with open(HTML_PATH, "w", encoding="utf-8", newline=chr(10)) as f:
            f.write(html)
        wrote.append(HTML_PATH)

    print("=== en_notes_build 摘要 ===")
    print(f"新增文字則數: {new_text}")
    print(f"新增圖片張數: {new_imgs}")
    print(f"目前 words={len(data.get('words', []))} grammar={len(data.get('grammar', []))} "
          f"book={len(data.get('book', []))} inbox={len(data.get('inbox', []))}")
    print(f"(執行前 words={before_words} grammar={before_gram} book={before_book} inbox={before_inbox})")
    if args.dry_run:
        print("DRY-RUN：以上為模擬結果，未寫入任何檔案。")
    else:
        print("寫入檔案：")
        for p in wrote:
            print(" -", p)


if __name__ == "__main__":
    main()
