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

/* ===== 速查側欄（2026-11-08 加：練習用的主版面不動，速查另開一欄） ===== */
article.card[id]{scroll-margin-top:150px}
.card{overflow-wrap:anywhere}  /* 頻道貼的長網址會把手機版面撐寬 */
.card.flash{outline:3px solid var(--accent); outline-offset:2px; transition:outline-color 1.2s}
.qbtn{position:fixed; right:16px; bottom:calc(18px + env(safe-area-inset-bottom)); z-index:40; border:0; border-radius:999px;
  background:var(--accent); color:#fff; font-family:inherit; font-size:15px; font-weight:600; line-height:1; padding:13px 18px; box-shadow:0 4px 14px rgba(0,0,0,.25); cursor:pointer}
:root[data-theme="dark"] .qbtn{color:#16151a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .qbtn{color:#16151a}}
.qback{position:fixed; inset:0; background:rgba(0,0,0,.38); z-index:45; display:none}
.qback.open{display:block}
.quick{position:fixed; top:0; bottom:0; right:0; width:min(90vw,380px); z-index:50; background:var(--bg); border-left:1px solid var(--line);
  display:none; flex-direction:column; box-shadow:-8px 0 24px rgba(0,0,0,.18)}
/* 關著時用 display:none，不用 translateX 藏在右邊：手機上藏在畫面外的固定元素會把版面撐寬 */
.quick.open{display:flex; animation:qin .2s ease}
@keyframes qin{from{transform:translateX(40px); opacity:.4} to{transform:none; opacity:1}}
.qhead{padding:14px 14px 10px; border-bottom:1px solid var(--line)}
.qtitle{display:flex; align-items:center; justify-content:space-between; margin-bottom:8px}
.qtitle b{font-size:18px}
.qtitle small{color:var(--ink2); font-size:12px; font-weight:400; margin-left:6px}
.qclose{border:0; background:transparent; color:var(--ink2); font-size:26px; line-height:1; padding:2px 8px; cursor:pointer}
.quick .search input{padding:10px 36px 10px 36px; font-size:16px; border-radius:10px}
.quick .search .mag{left:11px; font-size:14px}
.qtabs{display:flex; gap:6px; margin-top:8px}
.qtabs button{flex:1; border:1px solid var(--line); background:var(--card); color:var(--ink2); border-radius:10px; padding:8px 6px; font:inherit; font-size:14.5px; cursor:pointer}
.qtabs button[aria-selected="true"]{background:var(--accent); border-color:var(--accent); color:#fff; font-weight:600}
:root[data-theme="dark"] .qtabs button[aria-selected="true"]{color:#16151a}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .qtabs button[aria-selected="true"]{color:#16151a}}
.qtabs button span{font-size:12px; opacity:.85; margin-left:3px}
.qbody{flex:1; overflow-y:auto; padding:6px 14px 90px; -webkit-overflow-scrolling:touch}
.qsec h3{font-size:13px; color:var(--ink2); letter-spacing:.04em; margin:16px 0 6px; font-weight:600}
.qsec h3 .qh-n{font-weight:400}
.qi{background:var(--card); border:1px solid var(--line); border-radius:10px; padding:9px 11px; margin-bottom:6px; font-size:14.5px; line-height:1.55}
.qi .no{display:inline-block; min-width:22px; height:22px; border-radius:6px; background:var(--accent-soft); color:var(--accent); font-weight:700; font-size:12.5px; text-align:center; line-height:22px; margin-right:6px; padding:0 4px}
.qi .pat{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-weight:700; color:var(--ink); margin-right:6px}
.qi .en{font-weight:700; font-size:16px; margin-right:6px}
.qi .ipa2{font-family:"Doulos SIL","Charis SIL",Georgia,serif; color:var(--ink2); margin-right:6px}
.qi .zh{color:var(--ink2)}
.qi .meta{display:flex; flex-wrap:wrap; gap:4px 10px; align-items:center; margin-top:3px; font-size:12px; color:var(--ink2)}
.qi .meta a{color:var(--accent); text-decoration:none; margin-left:auto; font-weight:600}
.qi .eg{background:var(--accent-soft); border-radius:6px; padding:0 6px; color:var(--ink)}
.qi .weak{background:#c0392b; color:#fff; border-radius:6px; padding:0 6px; font-size:11.5px; font-weight:600}
.qchips{display:flex; gap:6px; margin:12px 0 2px}
.qchips button{border:1px solid var(--line); background:var(--card); color:var(--ink2); border-radius:999px; padding:5px 12px; font:inherit; font-size:13px; cursor:pointer}
.qchips button[aria-pressed="true"]{border-color:var(--accent); color:var(--accent); font-weight:600}
.qempty{color:var(--ink2); font-size:14px; text-align:center; padding:20px 0}
.qhow{font-size:12px; color:var(--ink2); margin:18px 0 0; line-height:1.6}
@media (min-width:1100px){
  body{padding-left:360px}
  .quick{display:flex; left:0; right:auto; width:360px; animation:none; border-left:0; border-right:1px solid var(--line); box-shadow:none}
  .qbtn,.qclose,.qback{display:none !important}
}
</style>
</head>
<body>
<div class="wrap">

<header>
  <h1>英文筆記</h1>
  <p class="sub">課堂筆記整理　·　素材來自英文頻道（最新一堂 __LATEST__）　·　共 __COUNTS__</p>
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

__QUICK__

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
<script>
// ===== 速查側欄：只管側欄自己，主版面的搜尋/分頁不動 =====
(function(){
  var box=document.getElementById('quick'); if(!box) return;
  var btn=document.getElementById('qbtn'), back=document.getElementById('qback'), cls=document.getElementById('qclose'),
      qq=document.getElementById('qq'), qempty=document.getElementById('qempty'),
      tabs=[].slice.call(box.querySelectorAll('.qtabs button')),
      chips=[].slice.call(box.querySelectorAll('.qchips button')),
      secs=[].slice.call(box.querySelectorAll('.qsec')),
      items=[].slice.call(box.querySelectorAll('.qi')),
      cur='f', wf='all';
  items.forEach(function(it){ it.dataset.html=it.innerHTML; it.dataset.txt=it.textContent.toLowerCase(); });
  function open(v){ box.classList.toggle('open',v); back.classList.toggle('open',v); btn.setAttribute('aria-expanded',v?'true':'false'); if(v&&window.innerWidth>=700) setTimeout(function(){qq.focus();},230); }
  btn.addEventListener('click',function(){ open(true); });
  back.addEventListener('click',function(){ open(false); });
  cls.addEventListener('click',function(){ open(false); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape') open(false); });
  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }
  function mark(el,term){
    el.innerHTML=el.dataset.html; if(!term) return;
    var re=new RegExp(esc(term),'gi'), w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null), ns=[], n;
    while((n=w.nextNode())) ns.push(n);
    ns.forEach(function(node){
      var t=node.nodeValue; re.lastIndex=0; if(!re.test(t)) return; re.lastIndex=0;
      var f=document.createDocumentFragment(), last=0, m;
      while((m=re.exec(t))!==null){ if(m.index>last) f.appendChild(document.createTextNode(t.slice(last,m.index)));
        var k=document.createElement('mark'); k.textContent=m[0]; f.appendChild(k); last=m.index+m[0].length; if(!m[0].length) re.lastIndex++; }
      if(last<t.length) f.appendChild(document.createTextNode(t.slice(last)));
      node.parentNode.replaceChild(f,node);
    });
  }
  function apply(){
    var term=qq.value.trim().toLowerCase(), shown=0;
    secs.forEach(function(s){
      // 有打字：公式＋單字一起搜；沒打字：只看選中的那一頁
      var onTab=term? true : s.dataset.q===cur, any=false;
      [].slice.call(s.querySelectorAll('.qi')).forEach(function(it){
        var ok=onTab && (!term || it.dataset.txt.indexOf(term)>=0) && (term || it.dataset.q!=='w' || wf==='all' || it.dataset.weak==='1');
        it.classList.toggle('hidden',!ok); if(ok){ mark(it,term); any=true; shown++; }
      });
      s.classList.toggle('hidden',!any && !(onTab && !term && s.dataset.always));
      [].slice.call(s.querySelectorAll('.qgrp')).forEach(function(g){
        var vis=[].slice.call(g.querySelectorAll('.qi')).some(function(i){return !i.classList.contains('hidden');});
        g.classList.toggle('hidden',!vis);
      });
    });
    qempty.classList.toggle('hidden',shown>0);
  }
  qq.addEventListener('input',apply);
  tabs.forEach(function(t){ t.addEventListener('click',function(){
    tabs.forEach(function(x){ x.setAttribute('aria-selected',x===t?'true':'false'); }); cur=t.dataset.q;
    if(qq.value){ qq.value=''; } apply(); box.querySelector('.qbody').scrollTop=0; }); });
  chips.forEach(function(c){ c.addEventListener('click',function(){
    chips.forEach(function(x){ x.setAttribute('aria-pressed',x===c?'true':'false'); }); wf=c.dataset.wf; apply(); }); });
  // 「看原筆記」：主版面切回「全部」、清掉主搜尋，捲到那張卡並閃一下
  box.addEventListener('click',function(e){
    var a=e.target.closest('a.go'); if(!a) return;
    var el=document.getElementById(a.getAttribute('href').slice(1)); if(!el) return;
    e.preventDefault();
    var mq=document.getElementById('q'); if(mq&&mq.value){ mq.value=''; mq.dispatchEvent(new Event('input')); }
    var all=document.querySelector('.tabs .tab[data-t="all"]'), needTab=all&&all.getAttribute('aria-selected')!=='true';
    if(needTab) all.click();
    open(false);
    setTimeout(function(){
      var d=el.querySelector('details.ocr'); if(d) d.open=true;
      el.scrollIntoView({behavior:'smooth',block:'start'}); el.classList.add('flash');
      setTimeout(function(){ el.classList.remove('flash'); },1800);
    },needTab?450:60);
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
import os, re, sys, json, argparse, urllib.request, urllib.error, datetime
import html as html_mod

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
        for i, a in enumerate(img_atts):
            new_imgs += 1
            ext = os.path.splitext(a.get("filename", "x.jpg"))[1] or ".jpg"
            # 一則訊息多張圖：第 2 張起加 _2、_3，否則會互相覆蓋（2026-10-12 踩過）
            fname = f"inbox_{mid}{ext}" if i == 0 else f"inbox_{mid}_{i + 1}{ext}"
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
        f'  <article class="card" data-t="word" id="{word_anchor(w["en"])}">\n'
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


def render_gram_card(g, idx=0):
    body = "\n".join(render_gram_block(b) for b in g["blocks"])
    return (
        f'  <article class="card" data-t="gram" id="g-{idx}">\n'
        f'    <p class="g-title">{g["title"]}</p>\n'
        '    <div class="g-body">\n'
        f'{body}\n'
        '    </div>\n'
        '  </article>'
    )


def render_book_card(b, idx=0):
    if b.get("ocr_status") == "pending":
        ocr_block = '    <p class="note" style="margin-top:8px">這張的字還沒抄，等下次整理</p>'
    else:
        ocr_block = f'    <details class="ocr"><summary>看這張圖上的文字</summary><div class="txt">{b.get("ocr", "")}</div></details>'
    return (
        f'  <article class="card" data-t="book" id="b-{idx}">\n'
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
    date = tw_date(it.get("ts"), full=True)
    # Discord 原文是純文字，要跳脫（例如 <@&角色> 不能被當成 HTML 標籤吃掉）
    text = html_mod.escape(it.get("text") or "") or "（無文字，附件見下）"
    atts = it.get("attachments") or []
    att_html = ""
    if atts:
        att_html = f'\n    <p class="note" style="margin-top:6px">附件：{html_mod.escape(", ".join(a for a in atts if a))}</p>'
    return (
        f'  <article class="card" data-t="inbox" id="m-{it["id"]}">\n'
        f'    <p class="note" style="margin:0 0 6px">{date}</p>\n'
        f'    <p class="g-body" style="margin:0;white-space:pre-wrap">{text}</p>{att_html}\n'
        '  </article>'
    )


# ---------- 速查側欄：從資料用規則抽「核心公式」和「單字」（不呼叫任何 LLM） ----------

TW = datetime.timezone(datetime.timedelta(hours=8))
CJK = re.compile(r"[㄀-ㄯ㐀-鿿！-～]")   # 中文、注音、全形符號
RULE_LINE = re.compile(r"^\s*(\d{1,2})\s*[.．、]\s*(\S.*?)\s*$")
VOWEL_LINE = re.compile(r"^\s*([aeiou])\s*[:：]\s*(.+?)\s*$")
XREF = re.compile(r"^\s*([A-Za-z][A-Za-z'\-]+)\s*\n\s*[A-Za-z]+\s*→\s*第\s*(\d+)\s*條", re.M)
WORD_LINE = re.compile(r"^([A-Za-z][A-Za-z'\-]*(?: [A-Za-z][A-Za-z'\-]*)?)(.*)$")
IPA_ONLY = re.compile(r"^\s*([\[/][^\[\]/]{2,40}[\]/])\s*$")
WEAK_WORDS = re.compile(r"念錯|唸錯|沒有念對|沒有唸對|沒有唸出來|沒有念出來|念成|唸成|不熟|解釋不出來")
WORD_STOP = {"ving", "be", "have", "do", "does", "is", "am", "are"}


def tw_date(ts, full=False):
    """Discord 的 UTC 時間 → 台灣日期（M/DD；full=True 給 YYYY-MM-DD）。舊資料只有 '9/16' 這種就原樣回傳。"""
    if not ts:
        return ""
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return ts[:10]
        d = dt.astimezone(TW)
        return d.strftime("%Y-%m-%d") if full else f"{d.month}/{d.day:02d}"
    except ValueError:
        return ts


def word_anchor(en):
    return "w-" + re.sub(r"[^a-z0-9]+", "-", (en or "").lower()).strip("-")


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "")


def split_rule(body):
    """'r:母音前發若' → ('r', '母音前發若')；'be,re,de，e在第二個字…' → ('be,re,de', 'e在第二個字…')；其餘 ('', 原句)。"""
    m = re.match(r"^([^:：]{1,24}?)\s*[:：]\s*(.+)$", body)
    if m and not CJK.search(m.group(1)):
        return m.group(1).strip(), m.group(2).strip()
    m = re.match(r"^([A-Za-z][A-Za-z ,/+]*)\s*，\s*(.*[㐀-鿿].*)$", body)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", body


def extract_formulas(data):
    """回傳 dict：rules（發音規則，依編號）、vowels（母音字母念法）、grammar（文法公式）。
    規則：
      發音規則＝頻道訊息裡「數字. 內容」的行，內容有英文字母、且有中文/注音或冒號，且（有冒號 或 在同一則訊息裡連號 ≥5 條）。
               同編號以較新的訊息為準；「poured / ou → 第 15 條」這種交叉引用會把 poured 掛到第 15 條當例字。
      母音字母＝「a:ㄟ」這種單一母音字母開頭＋冒號的行。
      文法公式＝課堂整理過的 6 則文法標題 ＋ 頻道訊息裡含 + 或 = 的短行（不是編號行、不是網址）。"""
    rules, vowels, gram = {}, [], []
    egs = {}
    inbox = sorted(data.get("inbox", []), key=lambda x: x.get("ts", ""))
    for it in inbox:
        text = it.get("text") or ""
        for w, n in XREF.findall(text):
            egs.setdefault(int(n), [])
            if w.lower() not in [e.lower() for e in egs[int(n)]]:
                egs[int(n)].append(w)
    for it in inbox:
        text = it.get("text") or ""
        lines = text.splitlines()
        nums = [(i, RULE_LINE.match(l)) for i, l in enumerate(lines)]
        # 連號段：相鄰行編號 +1
        run_len = {}
        i = 0
        while i < len(nums):
            j = i
            while (j + 1 < len(nums) and nums[j][1] and nums[j + 1][1]
                   and int(nums[j + 1][1].group(1)) == int(nums[j][1].group(1)) + 1):
                j += 1
            for k in range(i, j + 1):
                run_len[k] = j - i + 1
            i = j + 1
        for idx, (i, m) in enumerate(nums):
            line = lines[i]
            if m:
                no, body = int(m.group(1)), m.group(2)
                has_colon = bool(re.search(r"[:：]", body))
                if "http" in body or not re.search(r"[A-Za-z]", body) or not (CJK.search(body) or has_colon):
                    continue
                if not (re.search(r"[:：]", body) or run_len.get(idx, 1) >= 5):
                    continue
                pat, exp = split_rule(body)
                rules[no] = {"no": no, "pat": pat, "exp": exp, "date": tw_date(it.get("ts")), "src": "m-" + it["id"]}
                continue
            vm = VOWEL_LINE.match(line)
            if vm:
                vowels.append({"pat": vm.group(1), "exp": vm.group(2), "date": tw_date(it.get("ts")), "src": "m-" + it["id"]})
                continue
            s = line.strip()
            if (re.search(r"[+＋=＝]", s) and len(s) <= 60 and "http" not in s and "→" not in s
                    and (CJK.search(s) or re.search(r"[A-Za-z]{2,}", s))):
                gram.append({"pat": s, "exp": "", "date": tw_date(it.get("ts")), "src": "m-" + it["id"]})
    for no, eg in egs.items():
        if no in rules:
            rules[no]["eg"] = eg
    curated = []
    for i, g in enumerate(data.get("grammar", [])):
        t = re.sub(r"^\s*\d+\s*[.．]\s*", "", strip_tags(g.get("title", "")))
        curated.append({"pat": t, "exp": "", "date": "9/16–9/23", "src": f"g-{i}"})
    return {"rules": [rules[k] for k in sorted(rules)], "vowels": vowels, "grammar": curated + gram}


def extract_words(data):
    """回傳單字清單（新到舊）。來源：
      1) 課堂整理過的單字卡（有 UK/US 音標）
      2) 頻道訊息：12 行以內的訊息，逐行看「開頭是 1~2 個英文字、後面接中文/括號/音標或什麼都沒有」的行。
         同一則訊息裡緊接的 [音標] 行、純中文行會併進上一個字。整句英文（3 個字以上）不算單字。
         註記含「念錯／不熟／念成…」或前一則 15 分鐘內說「不熟」→ 標成「不熟」。
      同一個字出現多次就合併。"""
    words = {}
    order = []

    def add(en, date, src, ipa="", note="", weak=False, rank=""):
        k = en.lower()
        if k not in words:
            words[k] = {"en": en, "ipa": "", "notes": [], "weak": False, "dates": [], "src": src, "rank": rank}
            order.append(k)
        w = words[k]
        if ipa and not w["ipa"]:
            w["ipa"] = ipa
        if note and note not in w["notes"]:
            w["notes"].append(note)
        w["weak"] = w["weak"] or weak
        if date and date not in w["dates"]:
            w["dates"].append(date)
        if rank > w["rank"]:
            w["rank"] = rank
            w["src"] = src
        return w

    for w in data.get("words", []):
        add(w["en"], "9/09", word_anchor(w["en"]), ipa=w.get("us") or w.get("uk", ""),
            note=strip_tags(w.get("note", "")).split("。")[0], rank="2026-09-09")

    inbox = sorted(data.get("inbox", []), key=lambda x: x.get("ts", ""))
    prev = None
    for it in inbox:
        text = (it.get("text") or "").strip()
        ts = it.get("ts", "")
        date = tw_date(ts)
        lines = [l.rstrip() for l in text.splitlines()]
        flag_all = False
        if prev and "不熟" in (prev.get("text") or ""):
            try:
                gap = (datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                       - datetime.datetime.fromisoformat(prev["ts"].replace("Z", "+00:00"))).total_seconds()
                flag_all = 0 <= gap <= 15 * 60
            except ValueError:
                pass
        prev = it
        if not text or len(lines) > 12:
            continue
        last = None
        for line in lines:
            s = line.strip()
            if not s:
                continue
            im = IPA_ONLY.match(s)
            if im:
                if last:
                    if not last["ipa"]:
                        last["ipa"] = im.group(1)
                elif len(lines) == 1:
                    add(im.group(1), date, "m-" + it["id"], note="只記了音標，沒寫是哪個字", rank=ts)
                continue
            m = WORD_LINE.match(s)
            if m:
                en, rest = m.group(1).strip(), m.group(2).strip()
                if (len(en.replace(" ", "")) < 3 or en.lower() in WORD_STOP
                        or (rest and not re.match(r"^[㄀-ㄯ㐀-鿿(（\[/]", rest))
                        or re.search(r"動詞|問句|三單", rest)):
                    last = None
                    continue
                note = re.sub(r"^(就是|是)", "", rest).strip()
                ipa = ""
                pm = re.match(r"^([\[/][^\[\]/]{2,40}[\]/])\s*(.*)$", note)
                if pm:
                    ipa, note = pm.group(1), pm.group(2)
                last = add(en, date, "m-" + it["id"], ipa=ipa, note=note,
                           weak=flag_all or bool(WEAK_WORDS.search(note)), rank=ts)
                continue
            if last and CJK.search(s) and not re.search(r"[A-Za-z]", s) and len(s) <= 20:
                if s not in last["notes"]:
                    last["notes"].insert(0, s)     # 純中文短行＝上一個字的意思，放最前面
                continue
            last = None
    res = [words[k] for k in order]
    res.sort(key=lambda w: w["rank"], reverse=True)
    return res


def render_quick(data):
    e = html_mod.escape
    F = extract_formulas(data)
    W = extract_words(data)
    nf = len(F["rules"]) + (1 if F["vowels"] else 0) + len(F["grammar"])
    nw = len(W)
    nweak = sum(1 for w in W if w["weak"])

    def go(src):
        return f'<a class="go" href="#{e(src)}">看原筆記 ›</a>'

    out = []
    out.append('<button class="qbtn" id="qbtn" aria-controls="quick" aria-expanded="false">☰ 速查公式／單字</button>')
    out.append('<div class="qback" id="qback"></div>')
    out.append('<aside class="quick" id="quick" aria-label="速查">')
    out.append('<div class="qhead">')
    out.append('  <div class="qtitle"><b>速查<small>快速翻重點用</small></b><button class="qclose" id="qclose" aria-label="關閉速查">×</button></div>')
    out.append('  <div class="search"><span class="mag">🔍</span><input id="qq" type="search" placeholder="查公式或單字，例：ou、poured、does" autocomplete="off" aria-label="速查搜尋"></div>')
    out.append(f'  <div class="qtabs" role="tablist"><button role="tab" data-q="f" aria-selected="true">核心公式<span>{nf}</span></button>'
               f'<button role="tab" data-q="w" aria-selected="false">單字<span>{nw}</span></button></div>')
    out.append('</div>')
    out.append('<div class="qbody">')

    # 公式
    out.append('<section class="qsec" data-q="f">')
    if F["rules"]:
        out.append('<div class="qgrp"><h3>發音規則（看拼字 → 怎麼念）<span class="qh-n">　共 %d 條</span></h3>' % len(F["rules"]))
        for r in F["rules"]:
            pat = f'<span class="pat">{e(r["pat"])}</span>' if r["pat"] else ""
            eg = ""
            if r.get("eg"):
                eg = "".join(f'<span class="eg">例 {e(x)}</span>' for x in r["eg"])
            out.append(f'<div class="qi" data-q="f"><span class="no">{r["no"]}</span>{pat}<span>{e(r["exp"])}</span>'
                       f'<div class="meta">{eg}<span>{e(r["date"])}</span>{go(r["src"])}</div></div>')
        out.append('</div>')
    if F["vowels"]:
        v = F["vowels"]
        body = "　".join(f'<span class="pat">{e(x["pat"])}</span>{e(x["exp"])}' for x in v)
        out.append('<div class="qgrp"><h3>母音字母單獨念</h3>')
        out.append(f'<div class="qi" data-q="f">{body}<div class="meta"><span>{e(v[0]["date"])}</span>{go(v[0]["src"])}</div></div></div>')
    if F["grammar"]:
        out.append('<div class="qgrp"><h3>文法句型公式</h3>')
        for g in F["grammar"]:
            out.append(f'<div class="qi" data-q="f"><span class="pat" style="font-family:inherit">{e(g["pat"])}</span>'
                       f'<div class="meta"><span>{e(g["date"])}</span>{go(g["src"])}</div></div>')
        out.append('</div>')
    out.append('</section>')

    # 單字
    out.append('<section class="qsec hidden" data-q="w">')
    out.append(f'<div class="qchips"><button data-wf="all" aria-pressed="true">全部 {nw}</button>'
               f'<button data-wf="weak" aria-pressed="false">不熟的 {nweak}</button></div>')
    out.append('<div class="qgrp"><h3>新 → 舊</h3>')
    for w in W:
        weak = '<span class="weak">不熟</span>' if w["weak"] else ""
        ipa = f'<span class="ipa2">{e(w["ipa"])}</span>' if w["ipa"] else ""
        notes = "；".join(w["notes"])
        out.append(f'<div class="qi" data-q="w" data-weak="{1 if w["weak"] else 0}"><span class="en">{e(w["en"])}</span>{ipa}'
                   f'<span class="zh">{e(notes)}</span>'
                   f'<div class="meta">{weak}<span>{e("、".join(w["dates"]))}</span>{go(w["src"])}</div></div>')
    out.append('</div></section>')

    out.append('<p class="qempty hidden" id="qempty">速查裡沒有這個字。主畫面上方的搜尋會連課本頁的字一起找。</p>')
    out.append('<p class="qhow">這一欄是從你的英文頻道筆記用規則自動抽的：編號的「拼字：念法」算發音規則；有 + 或 = 的短句算文法公式；'
               '開頭是一兩個英文字、後面接中文或音標的算單字。抽漏或抽錯的，按「看原筆記」看原文。</p>')
    out.append('</div></aside>')
    return "\n".join(out)


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
    gram_cards = "\n\n".join(render_gram_card(g, i) for i, g in enumerate(grammar))
    book_cards = "\n\n".join(render_book_card(b, i) for i, b in enumerate(book))

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
    latest = max((it.get("ts") or "" for it in inbox), default="")
    html = html.replace("__LATEST__", tw_date(latest) if latest else "9/23")
    html = html.replace("__QUICK__", render_quick(data))
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
