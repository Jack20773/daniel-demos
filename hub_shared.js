/* hub_shared.js — proof v4 一站式頁共用邏輯（hub_a / hub_b 共用）
   讀 ./proof.json（真資料，14 天）＋本檔內建的戰情室／等待清單示意資料（公開 demo，標題已一般化、無個資）。
*/

/* ---------------------------------------------------------------- 示意資料（戰情室／等你回，公開 repo 不放真實票內容） */
const WARROOM_DEMO = [
  {title:"把每日待辦看板的到期提醒時間改成早上八點", category:"制度/機制", state:"agreed", origin:"you",
   note:"同意，這樣比較不會漏看", note_ts:"09-12 08:41"},
  {title:"幫某個小工具補一份使用說明", category:"工具", state:"agreed", origin:"auto",
   note:"可以，順手把範例也加進去", note_ts:"09-14 21:05"},
  {title:"把重複出現的錯誤訊息整理成一份檢查清單", category:"程式專案", state:"agreed", origin:"auto",
   note:"這個做完之後記得回報一下花多久", note_ts:"09-16 11:20"},
  {title:"確認某個外部服務的免費額度快用完了，要不要換方案", category:"對外案子", state:"waiting", origin:"you", note:null},
  {title:"把某份舊測試資料清乾淨、搬進封存資料夾", category:"雜務", state:"verify", origin:"auto", note:null},
  {title:"某個功能改完了，等你點開看一次再算數", category:"程式專案", state:"verify", origin:"auto", note:null},
  {title:"某份要對外用的資料，要不要正式發布", category:"對外案子", state:"waiting", origin:"you", note:null},
];

const WAITING_DEMO = [
  {title:"某個外部服務的免費額度快見底，要續用付費版還是換方案", area:"對外案子", why:"要你決定方向，不是技術問題", today:true},
  {title:"某份要對外用的資料要不要正式發布", area:"對外案子", why:"等你點頭才送出", today:true},
  {title:"某個功能已經做完，還沒被你打開驗收", area:"程式專案", why:"AI 自己說做完了，需要你确认才算數", today:false},
  {title:"某個工具需要的外部帳號資訊還沒拿到", area:"工具", why:"卡在別人手上，不是我們能決定的", today:false},
];

/* ---------------------------------------------------------------- 分數點的真實 Discord 連結（示意：demo 只接了今天 3 筆） */
const SCORE_MSG_LINKS = {
  "2026-09-18|10:36":"https://discord.com/channels/1541147813948424225/1547587315956973588/1550334690018328729",
  "2026-09-18|14:26":"https://discord.com/channels/1541147813948424225/1547587315956973588/1550392480610910271",
  "2026-09-18|14:33":"https://discord.com/channels/1541147813948424225/1547587315956973588/1550394360842158084",
};

/* ---------------------------------------------------------------- 今天（2026-09-18）每一件手寫白話說明（示意，索引對應 countedItems 順序，抄自 proof_v3_viz5b.html 已定案版） */
const TODAY_DATE="2026-09-18";
const TODAY_PLAIN_MAP=[
  "示意：把「AI 這週做了什麼」的自動小幫手修好，讓週報格式跟他要的對得上。為什麼做：讓每週整理不用人工東拼西湊。",
  "示意：把「AI 每天做了什麼」的日報做出來，控制在 8 行以內。為什麼做：讓他早上打開就看得懂，不用自己動手算。",
  "示意：把上次某天分數「為什麼是那個分數」的原因補寫清楚。為什麼做：以後回頭看才知道當初為什麼扣分。",
  "示意：把「藏在附件裡的訊息」也抓進來一起算分數，不然會漏算。為什麼做：分數統計才準，不會漏掉他打的分。",
  "示意：把「哪件事該用便宜的小助手做、哪件事要用貴的大助手做」的規則寫進說明書。為什麼做：以後不用每次重新判斷，照規則做就好。",
  "示意：把改好的股票篩選工具存檔並同步一份到網路備份。為什麼做：東西存好才不會不見，其他機器也拿得到最新版。",
  "示意：把股票代號資料庫裡兩檔股票的編號錯誤修正。為什麼做：抓錯代號會讓後面的分析用錯股票的資料。",
  "示意：四個小助手各自把小任務做完，順手修好一個算額度時的小漏洞。為什麼做：讓後面算額度的數字準一點。",
  "示意：把「AI 每天做了什麼」的證明頁面做出雛形給他看。為什麼做：讓他不用信我說的話，自己點連結就能查證。",
  "示意：把散在各處的紀錄（做了什麼、票、額度、分數）整合成一份「每天一份」的檔案。為什麼做：以後每天自動產生這份報表，不用手動拼湊。",
  "示意：把「小幫手自己發的系統通知」誤判成「他打的分數」這個小毛病修掉。為什麼做：不然分數統計會被雜訊污染，變得不準。",
  "示意：把頁面主角從「做了多少件事」改成「每天完成了什麼、有沒有證據」。為什麼做：他要看的是實際成果，不是數量灌水。",
  "示意：把「他打的分數」從標題那行搬到獨立一行。為什麼做：他糾正過分數是在評「AI 回答得好不好」，不是評「做出來的東西好不好」，兩者要分開看。",
  "示意：把「回覆了幾則」這個數字改成只算他親自傳的訊息，小幫手之間互傳不算進去。為什麼做：不然這個數字會被灌水，看起來比實際多。",
  "示意：跟上一件一起重新產生檔案，讓改過的算法生效。為什麼做：改了算法卻沒重新產檔，頁面看到的還是舊數字。",
  "示意：先做兩個範例版面（卡片式／表格式）給他挑。為什麼做：直接做完整版怕方向猜錯，先給他挑喜歡哪種再做細節。",
  "示意：再做兩個小版本（要不要用表情符號當圖示）給他選。為什麼做：同上，先讓他挑喜歡的風格再往下做。",
  "示意：做出「總覽在最上面」跟「每天帶小圖表」兩種版面給他比較。為什麼做：他說想要圖表、不是純文字列表，先給兩種抓感覺。",
  "示意：做出「照專案分」和「照誰交辦的分」兩種分類方式的版面。為什麼做：讓他從不同角度看同一批工作，看哪種比較好懂。",
  "示意：做出兩版新畫面（今天橫條圖放大版／數字卡加熱圖版），回應他稍早給的六點意見。為什麼做：把他提的修改意見一次做進去，讓他驗收。"
];

/* ---------------------------------------------------------------- 共用小工具 */
const NS="http://www.w3.org/2000/svg";
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML;}
function fmtDate(s){return s.slice(5).replace('-','/');}
function countedItems(day){return (day.items||[]).filter(i=>i.verified&&i.evidence_url);}
function scoreColor(s){return {1:'var(--sc1)',2:'var(--sc2)',3:'var(--sc3)',4:'var(--sc4)',5:'var(--sc5)'}[s]||'var(--zero)';}
const EXPENSIVE_MODELS=new Set(['opus','fable']);
function heatCellStyle(accountKey,modelKey,v,maxCell){
  if(modelKey==='other'){
    const alpha=v<=0?0:0.12+0.6*(v/maxCell);
    return {bg:v<=0?'transparent':`rgba(var(--neutral-rgb),${alpha.toFixed(2)})`,fg:alpha>0.55?'#fff':'var(--ink)'};
  }
  const isExpensive=EXPENSIVE_MODELS.has(modelKey);
  const good=(accountKey==='sub')?!isExpensive:isExpensive;
  const rgbVar=good?'var(--good-rgb)':'var(--bad-rgb)';
  const alpha=v<=0?0:0.12+0.78*(v/maxCell);
  const bg=v<=0?'transparent':`rgba(${rgbVar},${alpha.toFixed(2)})`;
  const fg=alpha>0.55?'#fff':'var(--ink)';
  return {bg,fg};
}
function plainText(it){
  const proj=it.project||'這個專案';
  if(it.kind==='commit')return `示意：這是「${proj}」的一次程式修改，存進版本紀錄後就正式生效，不用你再確認。`;
  if(it.kind==='ticket')return `示意：這是「${proj}」的一張工作票，你按下「同意」代表你已經驗收通過了。`;
  if(it.kind==='note')return `示意：這是當天日誌裡補記的一句說明，用來解釋那天做了什麼、為什麼做。`;
  return `示意：這是當天記錄下來的一筆工作項目。`;
}
function originBadge(by){
  // by 目前一律「未對」（第 1 階段還沒做 commit↔訊息 對應，見 proof_daily_plan.md §2）：老實顯示未對，不瞎猜。
  if(by==='你交辦的')return `<span class="origin you">你交辦的</span>`;
  if(by==='我自主的')return `<span class="origin auto">我自主的</span>`;
  return `<span class="origin">未對</span>`;
}

const PROJ_SLOTS=['var(--s1)','var(--s2)','var(--s3)','var(--s4)','var(--s5)','var(--s6)','var(--s7)'];
const PROJ_RGB_SLOTS=['var(--s1-rgb)','var(--s2-rgb)','var(--s3-rgb)','var(--s4-rgb)','var(--s5-rgb)','var(--s6-rgb)','var(--s7-rgb)'];
function buildProjectColorMap(days){
  const counts={};
  days.forEach(d=>countedItems(d).forEach(it=>{
    const p=it.project||'其他';
    if(p==='其他')return;
    counts[p]=(counts[p]||0)+1;
  }));
  const top=Object.keys(counts).sort((a,b)=>counts[b]-counts[a]).slice(0,7);
  const map={}, rgbMap={};
  top.forEach((p,i)=>{map[p]=PROJ_SLOTS[i];rgbMap[p]=PROJ_RGB_SLOTS[i];});
  return {map,rgbMap,top};
}
function projColor(map,p){return map[p&&p!=='其他'?p:'__x__']||'var(--zero)';}
function projKeyFor(map,p){return (p&&map[p])?p:'其他';}
function projSegBar(container,items,map){
  const n=items.length;
  container.innerHTML='';
  if(n===0){
    const seg=document.createElement('div');seg.className='seg';seg.style.background='var(--zero)';seg.style.width='100%';
    container.appendChild(seg);
    return;
  }
  const byProj={};
  items.forEach(it=>{const p=it.project||'其他';byProj[p]=(byProj[p]||0)+1;});
  const order=Object.keys(byProj).sort((a,b)=>byProj[b]-byProj[a]);
  order.forEach(p=>{
    const seg=document.createElement('div');seg.className='seg';
    seg.style.background=projColor(map,p);
    seg.style.width=(byProj[p]/n*100)+'%';
    seg.title=`${p}：${byProj[p]} 件（${Math.round(byProj[p]/n*100)}%）`;
    container.appendChild(seg);
  });
}

/* ---------------------------------------------------------------- 效率（d. 每 100 萬 token 換幾件，比前 7 天） */
function tokensWan(d){return (d.tokens_main_wan||0)+(d.tokens_sub_wan||0);}
function efficiencyOf(days){
  const items=days.reduce((s,d)=>s+countedItems(d).length,0);
  const tok=days.reduce((s,d)=>s+tokensWan(d),0); // 萬 token
  if(tok<=0)return null;
  return items/(tok/100); // 每「百萬 token」= 100 萬 token
}
function computeEfficiency(days){
  const n=days.length;
  const last7=days.slice(Math.max(0,n-7));
  const prev7=days.slice(Math.max(0,n-14),Math.max(0,n-7));
  const cur=efficiencyOf(last7);
  const prev=prev7.length?efficiencyOf(prev7):null;
  return {cur,prev,last7,prev7};
}
function renderEfficiencyCard(elId,days){
  const el=document.getElementById(elId);
  if(!el)return;
  const {cur,prev}=computeEfficiency(days);
  let arrow='', arrowClass='', deltaTxt='跟前 7 天比不出來（資料不足 14 天）';
  if(cur!=null&&prev!=null&&prev>0){
    const pct=((cur-prev)/prev*100);
    if(pct>3){arrow='↑';arrowClass='arrow-up';deltaTxt=`比前 7 天多 ${pct.toFixed(0)}%`;}
    else if(pct<-3){arrow='↓';arrowClass='arrow-down';deltaTxt=`比前 7 天少 ${Math.abs(pct).toFixed(0)}%`;}
    else {arrow='→';deltaTxt='跟前 7 天差不多';}
  }
  el.innerHTML=`
    <div class="card">
      <div class="num">${cur!=null?cur.toFixed(1):'—'}<span class="${arrowClass}" style="font-size:20px;margin-left:2px">${arrow}</span></div>
      <div class="unit">件／每 100 萬 token</div>
      <div class="lbl">效率（近 7 天）· ${esc(deltaTxt)}</div>
    </div>`;
}

/* ---------------------------------------------------------------- 三張大數字卡（今天） */
function renderCards(elId,today){
  const el=document.getElementById(elId);
  if(!el)return;
  const todayItems=countedItems(today);
  const todayTot=tokensWan(today);
  const todayHigh=today.score_high||0, todayLow=today.score_low||0;
  el.innerHTML=`
    <div class="card"><div class="num">${todayItems.length}</div><div class="unit">件</div><div class="lbl">今天做了幾件</div></div>
    <div class="card"><div class="num">${todayTot.toFixed(0)}</div><div class="unit">萬 token</div><div class="lbl">今天花了多少額度</div></div>
    <div class="card"><div class="num" style="color:var(--good)">${todayHigh}<span style="color:var(--ink-3);font-size:16px"> / </span><span style="color:var(--bad)">${todayLow}</span></div><div class="unit">高分 / 低分</div><div class="lbl">今天的滿意度</div></div>
  `;
}

/* ---------------------------------------------------------------- 今天按專案（橫條） */
function renderTodayBar(barId,legendId,titleId,today,projMap,projTop){
  const titleEl=document.getElementById(titleId);
  if(titleEl)titleEl.textContent=`今天（${today.date}）按專案`;
  const legendEl=document.getElementById(legendId);
  if(legendEl){
    legendEl.innerHTML=
      projTop.map((p,i)=>`<span><span class="sw" style="background:${PROJ_SLOTS[i]}"></span>${esc(p)}</span>`).join('')+
      `<span><span class="sw" style="background:var(--zero)"></span>其他</span>`;
  }
  const barEl=document.getElementById(barId);
  if(barEl)projSegBar(barEl,countedItems(today),projMap);
}

/* ---------------------------------------------------------------- 專案 × 日期格子表 */
function renderGridTable(elId,days,projMap,projRgbMap){
  const el=document.getElementById(elId);
  if(!el)return;
  const gridCounts={}, rowTotals={};
  days.forEach(d=>{
    const byProj={};
    countedItems(d).forEach(it=>{
      const p=projKeyFor(projMap,it.project);
      byProj[p]=(byProj[p]||0)+1;
    });
    Object.keys(byProj).forEach(p=>{
      gridCounts[p]=gridCounts[p]||{};
      gridCounts[p][d.date]=byProj[p];
      rowTotals[p]=(rowTotals[p]||0)+byProj[p];
    });
  });
  const gridRows=Object.keys(rowTotals).sort((a,b)=>rowTotals[b]-rowTotals[a]);
  let maxGridCell=1;
  gridRows.forEach(p=>days.forEach(d=>{maxGridCell=Math.max(maxGridCell,(gridCounts[p]&&gridCounts[p][d.date])||0);}));
  let gridHtml='<thead><tr><th>專案 ＼ 日期</th>'+days.map(d=>`<th>${fmtDate(d.date)}</th>`).join('')+'</tr></thead><tbody>';
  gridRows.forEach(p=>{
    gridHtml+=`<tr><td class="rowlbl">${esc(p)}</td>`;
    days.forEach(d=>{
      const v=(gridCounts[p]&&gridCounts[p][d.date])||0;
      const rgbVar=projRgbMap[p]||'var(--neutral-rgb)';
      const alpha=v<=0?0:0.2+0.7*(v/maxGridCell);
      const bg=v<=0?'transparent':`rgba(${rgbVar},${alpha.toFixed(2)})`;
      const fg=alpha>0.6?'#fff':'var(--ink)';
      gridHtml+=`<td class="cell" style="background:${bg};color:${fg}">${v>0?v:''}</td>`;
    });
    gridHtml+='</tr>';
  });
  gridHtml+='</tbody>';
  el.innerHTML=gridHtml;
}

/* ---------------------------------------------------------------- 每天清單（收合） */
function renderDaysList(elId,days,projMap,todayDate,todayPlainMap){
  const daysDiv=document.getElementById(elId);
  if(!daysDiv)return;
  daysDiv.innerHTML='';
  const rev=[...days].reverse();
  rev.forEach(d=>{
    const items=countedItems(d);
    const n=items.length;
    const byProj={};
    items.forEach(it=>{const p=it.project||'其他';byProj[p]=(byProj[p]||0)+1;});
    const order=Object.keys(byProj).sort((a,b)=>byProj[b]-byProj[a]);
    const headline=n===0?`做了 0 件：—`:`做了 ${n} 件：`+order.map(p=>`${esc(p)} ${byProj[p]}`).join('、');
    const isToday=d.date===todayDate;

    const card=document.createElement('div');card.className='day';
    const head=document.createElement('div');head.className='day-head';
    head.innerHTML=`<span class="headline">${esc(d.date)}${isToday?'（今天）':''}　${headline}</span><span class="rule">規則 v3</span>`;
    card.appendChild(head);

    const bar=document.createElement('div');bar.className='segbar';
    projSegBar(bar,items,projMap);
    card.appendChild(bar);

    const det=document.createElement('details');det.className='toggle';
    const sum=document.createElement('summary');sum.textContent='看每一件';
    det.appendChild(sum);
    if(n===0){
      const e=document.createElement('div');e.className='empty';e.textContent='這天沒有算進來的項目。';
      det.appendChild(e);
    }else{
      const ul=document.createElement('ul');ul.className='items';
      items.forEach((it,idx)=>{
        const li=document.createElement('li');
        const row1=document.createElement('div');row1.className='row1';
        const t=document.createElement('span');t.className='t';t.textContent=it.time||'';
        const dot=document.createElement('span');dot.className='dot';dot.style.background=projColor(projMap,it.project);
        const cont=document.createElement('div');
        const kd=document.createElement('span');kd.className='kind';
        kd.textContent={commit:'commit',ticket:'票',note:'日誌'}[it.kind]||it.kind;
        cont.appendChild(kd);
        const orig=document.createElement('span');orig.innerHTML=originBadge(it.by);
        cont.appendChild(orig.firstChild);
        cont.appendChild(document.createTextNode(it.text||''));
        const ev=document.createElement('span');ev.className='ev';
        if(it.evidence_url){const a=document.createElement('a');a.href=it.evidence_url;a.target='_blank';a.rel='noopener';a.textContent='證據：'+(it.evidence_label||'連結');ev.appendChild(a);}
        else{ev.textContent=it.evidence_label||'';}
        cont.appendChild(ev);
        row1.appendChild(t);row1.appendChild(dot);row1.appendChild(cont);
        li.appendChild(row1);
        const plain=document.createElement('div');plain.className='plain';
        plain.textContent=(d.date===todayDate&&todayPlainMap&&todayPlainMap[idx])?todayPlainMap[idx]:plainText(it);
        li.appendChild(plain);
        ul.appendChild(li);
      });
      det.appendChild(ul);
    }
    card.appendChild(det);
    daysDiv.appendChild(card);
  });
}

/* ---------------------------------------------------------------- 額度熱圖（帳號 × 模型） */
function renderHeatTable(elId,days){
  const el=document.getElementById(elId);
  if(!el)return;
  const MODEL_KEYS=['opus','sonnet','haiku','fable','other'];
  const MODEL_LABEL={opus:'Opus',sonnet:'Sonnet',haiku:'Haiku',fable:'Fable',other:'其他'};
  const sumByAccount={main:{},sub:{}};
  MODEL_KEYS.forEach(k=>{sumByAccount.main[k]=0;sumByAccount.sub[k]=0;});
  days.forEach(d=>{
    const m=d.tokens_by_model_main||{}, s=d.tokens_by_model_sub||{};
    MODEL_KEYS.forEach(k=>{sumByAccount.main[k]+=(m[k]||0);sumByAccount.sub[k]+=(s[k]||0);});
  });
  const maxCell=Math.max(...MODEL_KEYS.map(k=>Math.max(sumByAccount.main[k],sumByAccount.sub[k])),1);
  let heatHtml='<thead><tr><th>帳號 ＼ 模型</th>'+MODEL_KEYS.map(k=>`<th>${MODEL_LABEL[k]}</th>`).join('')+'<th>合計</th></tr></thead><tbody>';
  [['主帳號','main'],['分身','sub']].forEach(([label,key])=>{
    const vals=sumByAccount[key];
    const tot=MODEL_KEYS.reduce((s,k)=>s+vals[k],0);
    heatHtml+=`<tr><td class="rowlbl">${label}</td>`;
    MODEL_KEYS.forEach(k=>{
      const v=vals[k];
      const {bg,fg}=heatCellStyle(key,k,v,maxCell);
      heatHtml+=`<td class="cell" style="background:${bg};color:${fg}">${v>0?v.toFixed(0):'0'}</td>`;
    });
    heatHtml+=`<td class="cell">${tot.toFixed(0)}</td></tr>`;
  });
  heatHtml+='</tbody>';
  el.innerHTML=heatHtml;
}

/* ---------------------------------------------------------------- 分數點陣（五色，低分可點回 Discord） */
function renderScoreLegend(elId){
  const el=document.getElementById(elId);
  if(!el)return;
  el.innerHTML=[1,2,3,4,5].map(s=>`<span><span class="sw round" style="background:${scoreColor(s)}"></span>${s} 分</span>`).join('');
}
function renderScoreGrid(elId,days,todayDate){
  const scoreGrid=document.getElementById(elId);
  if(!scoreGrid)return;
  scoreGrid.innerHTML='';
  const rev=[...days].reverse();
  rev.forEach(d=>{
    const scores=d.scores||[];
    const row=document.createElement('div');row.className='scorerow';
    const lbl=document.createElement('span');lbl.textContent=fmtDate(d.date)+(d.date===todayDate?' 今天':'');
    row.appendChild(lbl);
    const dotsWrap=document.createElement('div');dotsWrap.className='dots';
    if(scores.length===0){
      const none=document.createElement('span');none.className='none';none.textContent='沒有打分紀錄';
      dotsWrap.appendChild(none);
    }else{
      scores.forEach(sc=>{
        const key=d.date+'|'+(sc.time||'').slice(11,16);
        const link=SCORE_MSG_LINKS[key];
        if(link){
          const a=document.createElement('a');a.className='d-link';a.href=link;a.target='_blank';a.rel='noopener';
          a.title=`${sc.score} 分　${sc.time||''}　點開看當時那則訊息`;
          const dot=document.createElement('span');dot.className='d';dot.style.background=scoreColor(sc.score);
          a.appendChild(dot);
          dotsWrap.appendChild(a);
        }else{
          const s=document.createElement('span');s.className='d';
          s.style.background=scoreColor(sc.score);
          s.title=`${sc.score} 分　${sc.time||''}`;
          dotsWrap.appendChild(s);
        }
      });
    }
    row.appendChild(dotsWrap);
    scoreGrid.appendChild(row);
  });
}

/* ---------------------------------------------------------------- 戰情室：他按同意的票＋他留的話（示意） */
function renderWarroom(elId,{onlyAgreed=false}={}){
  const el=document.getElementById(elId);
  if(!el)return;
  const list=onlyAgreed?WARROOM_DEMO.filter(t=>t.state==='agreed'):WARROOM_DEMO;
  if(list.length===0){el.innerHTML='<div class="empty">目前沒有票。</div>';return;}
  const STATE_LABEL={agreed:'已同意',waiting:'等你回',active:'進行中',verify:'等你驗收'};
  el.innerHTML=list.map(t=>`
    <div class="ticket st-${t.state}">
      <div class="tt">${esc(t.title)}<span class="demo-tag">示意</span></div>
      <div class="meta">
        <span class="badge ${t.state}">${STATE_LABEL[t.state]||t.state}</span>
        <span>${esc(t.category)}</span>
        <span class="origin ${t.origin==='you'?'you':'auto'}">${t.origin==='you'?'你交辦的':'我自主的'}</span>
      </div>
      ${t.note?`<div class="note"><b>他留的話（${esc(t.note_ts||'')}）</b>${esc(t.note)}</div>`:''}
    </div>
  `).join('');
}

/* ---------------------------------------------------------------- 還在等你回／卡住的事（示意） */
function renderWaiting(elId,{todayOnly=false}={}){
  const el=document.getElementById(elId);
  if(!el)return;
  const list=todayOnly?WAITING_DEMO.filter(w=>w.today):WAITING_DEMO;
  if(list.length===0){el.innerHTML='<div class="empty">目前沒有卡住的事。</div>';return;}
  el.innerHTML=list.map(w=>`
    <div class="wa">
      <div class="tt">${esc(w.title)}<span class="demo-tag">示意</span></div>
      <div class="why">${esc(w.area)}・${esc(w.why)}</div>
    </div>
  `).join('');
}

/* ---------------------------------------------------------------- 入口：載入 proof.json 後跑一個 render 函式 */
function loadProofAndRun(renderFn){
  fetch('./proof.json').then(r=>r.json()).then(data=>{
    const days=[...data.days].sort((a,b)=>a.date<b.date?-1:1);
    const today=days[days.length-1];
    const {map:projMap,rgbMap:projRgbMap,top:projTop}=buildProjectColorMap(days);
    renderFn({data,days,today,projMap,projRgbMap,projTop});
  }).catch(err=>{
    document.body.insertAdjacentHTML('afterbegin',`<div style="background:#fee;color:#a00;padding:10px;font-size:13px">proof.json 讀取失敗：${esc(err.message||String(err))}</div>`);
    console.error(err);
  });
}

/* ---------------------------------------------------------------- 頁籤切換（共用） */
function setupTabs(tabbarSel,onSwitch){
  const bar=document.querySelector(tabbarSel);
  if(!bar)return;
  const buttons=[...bar.querySelectorAll('button[data-tab]')];
  function activate(name){
    buttons.forEach(b=>b.setAttribute('aria-selected',b.dataset.tab===name?'true':'false'));
    document.querySelectorAll('.tabpanel').forEach(p=>p.classList.toggle('active',p.id==='panel-'+name));
    if(typeof onSwitch==='function')onSwitch(name);
    try{history.replaceState(null,'','#'+name);}catch(e){}
  }
  buttons.forEach(b=>b.addEventListener('click',()=>activate(b.dataset.tab)));
  const initial=(location.hash||'').replace('#','')||buttons[0].dataset.tab;
  activate(buttons.some(b=>b.dataset.tab===initial)?initial:buttons[0].dataset.tab);
}

/* ---------------------------------------------------------------- 頂部一行：更新時間＋規則版本 */
function renderTopbar(elId,data){
  const el=document.getElementById(elId);
  if(!el)return;
  const gen=data.generated_at||'—';
  el.innerHTML=`<span>更新時間：<b>${esc(gen)}</b></span><span>規則 v${esc(String(data.rules_version||3))}</span>`;
}
