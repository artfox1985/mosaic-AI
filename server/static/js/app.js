// ── STATE ─────────────────────────────────────────────────────────────────────
let S = null;          // server state
let sel = null;        // {source, factory_id, color}
let domeModal = null;  // {pi, slot_r, slot_c, tile_id, rotation, is_start}
let tilingPi = null, tilingRow = null;

// ── API ───────────────────────────────────────────────────────────────────────
async function api(path, body=null) {
  const opts = body
    ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}
    : {method:'GET'};
  
  const r = await fetch('/api'+path, opts);
  const text = await r.text();
  
  try {
    return JSON.parse(text);
  } catch(e) {
    throw new Error(`Server-Fehler (Code ${r.status}): ${text.substring(0, 150)}...`);
  }
}

async function newGame() {
  const d = await api('/new_game', {names:['Spieler 1','Spieler 2']});
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; domeModal=null; tilingPi=null; tilingRow=null;
  render();
  const dt = await api('/scoring_tiles');
  if(dt.ok) {
    allScoringTiles = dt.tiles;
    selectedScoringIds = new Set(S.scoring_tile_ids || [0,1,2]);
    renderScoringGrid();
    document.getElementById('scoring-overlay').style.display='flex';
  }
}

async function stoneMove(source, factory_id, color, row, moon_order=[]) {
  const d = await api('/move/stone', {source, factory_id, color, row, moon_order});
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; render();
}

async function domeMove(tile_id, slot_row, slot_col, rotation) {
  const d = await api('/move/dome', {tile_id, slot_row, slot_col, rotation});
  if(!d.ok){showError(d.error);return;}
  S=d.state; closeDomeModal(); render();
}

async function startTileMove(player, tile_id, slot_row, slot_col, rotation) {
  const d = await api('/move/start_tile', {player, tile_id, slot_row, slot_col, rotation});
  if(!d.ok){showError(d.error);return;}
  S=d.state; closeDomeModal(); render();
}

async function bonusChipMove(factory_id) {
  const d = await api('/move/bonus_chip', {factory_id});
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; render();
}

async function tilingMove(player, pattern_row, slot_row, slot_col, space_index, dome_tile_id=null, rotation=0) {
  const d = await api('/tiling', {player, pattern_row, slot_row, slot_col, space_index, dome_tile_id, rotation});
  if(!d.ok){showError(d.error);return;}
  S=d.state; tilingRow=null; render();
}

async function endTiling() {
  const d = await api('/end_tiling', {});
  if(!d.ok){showError(d.error);return;}
  S=d.state; tilingPi=null; tilingRow=null; render();
}

async function passMove() {
  const d = await api('/move/pass', {});
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; render();
}

async function tilingBonusChips(pi, pattern_row, chip_uses) {
  const d = await api('/tiling/bonus_chips', {player:pi, pattern_row, chip_uses});
  if(!d.ok){showError(d.error);return;}
  S=d.state; render();
}

async function tilingMoveToFloor(pi, pattern_row) {
  const d = await api('/tiling/move_to_floor', {player:pi, pattern_row});
  if(!d.ok){showError(d.error);return;}
  S=d.state; render();
}

function showError(msg) {
  document.getElementById('info-area').innerHTML = `
    <div class="info err" style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
      <span>❌ ${msg}</span>
      <button class="btn" onclick="render()" style="padding:2px 8px; font-size:10px; flex-shrink:0; border-color:#F87171; color:#991B1B;">OK</button>
    </div>`;
}

// ── COLORS ────────────────────────────────────────────────────────────────────
const COLOR_LABELS = {blau:'B',gelb:'G',rot:'R',schwarz:'S',tuerkis:'T','türkis':'T',bunt:'★',special:'◎'};

function tileDiv(color, extra='', size='') {
  const nc=normColor(color);
  return `<div class="tile ${nc} ${size} ${extra}">${COLOR_LABELS[color]||''}</div>`;
}

function normColor(c) {
  if (!c) return '';
  const low = c.toLowerCase();
  return low === 'türkis' ? 'tuerkis' : low;
}


function spaceHTML(sp, si=-1, pi=-1, sr=-1, sc=-1, tiling=false) {
  const color = sp.color || sp.req_color || sp.color_id || '';
  const nc = normColor(color);
  
  let bg='', cls='', lbl='', tdata='';
  
  if(sp.filled) {
    bg=''; cls=`ds filled ${normColor(sp.filled)}`; lbl='';
  } else if(sp.type === 'N' || !sp.type || sp.type === 'NORMAL') {
    const hexFull={blau:'#2563EB',gelb:'#D97706',rot:'#DC2626',schwarz:'#292524',tuerkis:'#0891B2'};
    const hex = hexFull[nc] || (nc ? '#FF00FF' : '#999'); 
    bg = `background:${hex};opacity:.7;`; 
    cls = 'ds N'; 
    lbl = nc ? nc[0].toUpperCase() : '?';
  } else if(sp.type === 'WILD') {
    bg = 'background:#EDE9FE;'; cls = 'ds W'; lbl = '★';
  } else {
    bg = 'background:#E7E5E4;'; cls = `ds S${sp.locked?' locked':''}`; lbl = sp.locked ? '🔒' : '◎';
  }
  
  if(tiling && si >= 0) {
    tdata = ` data-tiling="${pi},${sr},${sc},${si}"`;
    cls += ' click';
    bg += 'cursor:pointer;';
  }
  
  return `<div class="${cls}" style="${bg}"${tdata}>${lbl}</div>`;
}

function dome2x2(spaces, pi=-1, sr=-1, sc=-1, tiling=false) {
  return `<div class="d2x2">${spaces.map((sp,si)=>spaceHTML(sp,si,pi,sr,sc,tiling)).join('')}</div>`;
}

// ── RENDER BOARD ─────────────────────────────────────────────────────────────
function estimatedRoundScore(p) {
  let est = 0;
  const penalties = [-1,-2,-3,-4];
  p.pattern_lines.forEach((row,ri)=>{
    if(!row.color || row.tiles.length < row.capacity) return;
    const domeRow = Math.floor(ri/2);
    const filledNeighbors = p.dome_grid[domeRow]
      .filter(s=>s).flatMap(s=>s.spaces).filter(sp=>sp.filled).length;
    est += Math.max(1, 1 + Math.floor(filledNeighbors/2));
  });
  est += p.floor.reduce((s,_,i)=>s+(penalties[i]||0), 0);
  if(p.marker) est -= 2;
  return est;
}

function renderBoard(pi) {
  const p = S.players[pi];
  const isActive = S.current_player===pi && S.phase==='drafting';
  const isTiling = S.phase==='tiling';

  const tokHTML = S.round<5
    ? `<div class="tokens">${[0,1].map(i=>`<div class="tok ${i<p.tokens_used?'used':''}"></div>`).join('')}<span>${p.tokens_used}/2 Spielerplättchen</span></div>`
    : '';

  const plHTML = p.pattern_lines.map((row,ri)=>{
    let cls='';
    const domeRow = Math.floor(ri/2);
    if(isActive && sel) {
      const ok = row.tiles.length < row.capacity && (!row.color || row.color===sel.color);
      cls = ok ? 'drop' : 'nodrop';
    }
    const allEarlierDone = !isTiling || p.pattern_lines
      .slice(0, ri)
      .every(r => r.tiles.length < r.capacity);
    if(isTiling && tilingRow===null && row.tiles.length===row.capacity && allEarlierDone) cls='drop';
    else if(isTiling && tilingRow===null && row.tiles.length===row.capacity && !allEarlierDone) cls='nodrop';
    const hasChips = isTiling && p.bonus_chips.some(c=>c) && row.tiles.length>0 && row.tiles.length<row.capacity;
    const onclick = cls==='drop'
      ? `onclick="${isActive&&sel ? `onRowClick(${ri})` : `onTilingRowClick(${pi},${ri})`}"`
      : '';
    const chipBtn = hasChips
      ? `<button onclick="event.stopPropagation();openChipModal(${pi},${ri})" style="font-size:9px;padding:1px 4px;border:1px solid var(--border);border-radius:3px;cursor:pointer;background:var(--bg);margin-left:2px" title="Bonusplättchen nutzen">🎫</button>`
      : '';
    const cells = Array.from({length:row.capacity},(_,ci)=>{
      const tileIdx = ci - (row.capacity - row.tiles.length);
      return tileIdx >= 0
        ? `<div class="tile sm ${normColor(row.color)}"></div>`
        : `<div class="tile sm empty"></div>`;
    }).join('');
    return `<div class="prow ${cls}" ${onclick}>
      <span class="rownum">${ri+1}</span>${cells}
      <span class="rowlabel" style="color:var(--text3)">→${domeRow}</span>${chipBtn}
    </div>`;
  }).join('');

  const domeHTML = p.dome_grid.map((row,sr)=>row.map((slot,sc)=>{
    const needsStart = !p.start_placed;
    const canNormal  = !slot && p.can_place_dome && isActive;
    const canStart   = !slot && needsStart;
    let cls = slot ? 'occ' : (canStart ? 'start' : (canNormal ? 'cando' : ''));
    let ddata = (canStart||canNormal) ? ` data-dome="${pi},${sr},${sc}"` : '';
    const isTilingTarget = isTiling && tilingPi===pi && tilingRow!==null;
    const inner = slot
      ? dome2x2(slot.spaces, pi, sr, sc, isTilingTarget)
      : `<div style="font-size:9px;color:var(--text3);text-align:center;width:100%">${canStart?'▼ Start':'+'}</div>`;
    return `<div class="dslot ${cls}"${ddata}>${inner}</div>`;
  }).join('')).join('');

  const floorHTML = [...Array(4)].map((_,i)=>{
    const t = p.floor[i];
    return `<div class="fslot">${t?`<div class="tile sm ${normColor(t)}"></div>`:`<span>${[-1,-2,-3,-4][i]}</span>`}</div>`;
  }).join('');
  const markerHTML = p.marker ? `<div class="tile sm marker">1</div>` : '';

  const est = p.estimated_score || 0;
  const estStr = (est >= 0 ? '+' : '') + est;
  const estColor = est > 0 ? '#059669' : est < 0 ? '#DC2626' : 'var(--text3)';

  document.getElementById(`board${pi}`).className = `panel${isActive?' active':''}`;
  document.getElementById(`board${pi}`).innerHTML = `
    <div class="phead">
      <span class="pname">${isActive?'▶ ':''}${p.name}${p.start_placed?'':' ⚠ Erste Kuppelplatte legen!'}</span>
      <span style="display:flex;align-items:baseline;gap:5px">
        <span class="pscore">${p.score}</span>
        <span style="font-size:11px;color:${estColor}" title="Geschätzte Punkte diese Runde">(${estStr})</span>
      </span>
    </div>
    ${tokHTML}
    <div class="sep"></div>
    <div class="board-inner">
      <div>
        <div class="lbl">Musterreihen</div>
        <div id="plines${pi}">${plHTML}</div>
        <div class="sep"></div>
        <div class="lbl">Zerbrochene Fliesen ${markerHTML}</div>
        <div class="floor">${floorHTML}
          ${sel&&isActive?`<button class="btn danger" style="padding:2px 8px;font-size:10px" onclick="onFloorDirect()">→ Boden</button>`:''}
        </div>
        
        <div style="margin-top:6px;font-size:9px;color:var(--text3)">
          Chips (${p.chips_taken}/10):
          <div class="chips-grid">
            ${Array.from({length: 10}, (_, i) => {
              const c = p.bonus_chips[i];
              if (c && c.colors && c.colors.length > 0) {
                const c1 = normColor(c.colors[0]);
                const c2 = c.colors.length > 1 ? normColor(c.colors[1]) : 'empty';
                return `<div class="bchip" title="${c.colors.join('+')}">
                  <div class="bchip-half ${c1}"></div>
                  <div class="bchip-half ${c2}"></div>
                </div>`;
              } else {
                return `<div class="bchip placeholder"></div>`;
              }
            }).join('')}
          </div>
        </div>
        </div>
      <div>
        <div class="lbl" style="display:flex;justify-content:space-between">
          <span>Kuppel</span><span>${p.dome_grid.flat().filter(Boolean).length}/9</span>
        </div>
        <div class="dome-grid" id="dome${pi}">${domeHTML}</div>
      </div>
    </div>`;
  syncDomeHeight(pi);
}

function syncDomeHeight(pi) {
  const dgrid = document.getElementById('dome'+pi);
  if (!dgrid) return;
  dgrid.querySelectorAll('.dslot').forEach(slot => {
    slot.style.height = '58px';
    const d2 = slot.querySelector('.d2x2');
    if(d2) {
      d2.style.height = '46px';
      d2.style.width = '46px';
    }
  });
}

// ── RENDER CENTER ─────────────────────────────────────────────────────────────
function renderCenter() {
  const badge = document.getElementById('phase-badge');
  badge.className = 'phase-badge'+(S.phase==='tiling'?' tiling':S.phase==='end'?' end':'');
  const tilingStatus = S.phase==='tiling'
    ? (tilingRow!==null ? `TILING — Reihe ${tilingRow+1} legen` : 'PHASE 2: Reihe anklicken')
    : '';
  badge.textContent = S.phase==='drafting'?`Phase 1 — ${S.players[S.current_player].name}`
    :S.phase==='tiling'? tilingStatus
    :S.phase==='end'?'SPIELENDE':'—';

  const info = document.getElementById('info-area');
  if(sel) {
    info.innerHTML=`<div class="info sel">🎨 <strong>${sel.color}</strong> ausgewählt — Musterreihe wählen oder → Boden</div>`;
  } else if(S.phase==='tiling') {
    const placeableRows = (S.valid_tiling_rows||[]); 
    const allComplete = S.players.flatMap((p,pi)=>
      p.pattern_lines
        .filter(r=>r.tiles.length===r.capacity)
        .map(r=>({pi, ri:r.index, color:r.color, pname:p.name}))
    );
    const pending = allComplete.filter(x=>{
      if(!S.valid_tiling_rows) return true; 
      return placeableRows.some(pr=>pr.pi===x.pi && pr.ri===x.ri);
    }).filter(x=>{
      const p = S.players[x.pi];
      return !p.pattern_lines.slice(0,x.ri).some(r=>
        r.tiles.length===r.capacity &&
        (!S.valid_tiling_rows || placeableRows.some(pr=>pr.pi===x.pi&&pr.ri===p.pattern_lines.indexOf(r)))
      );
    });
    const hasPending = pending.length > 0;

    const chippable = S.players.flatMap((p,pi)=>
      p.pattern_lines
        .filter(r=>r.tiles.length>0 && r.tiles.length<r.capacity && p.bonus_chips.some(c=>c))
        .map(r=>({pi, ri:r.index, color:r.color, need:r.capacity-r.tiles.length, pname:p.name}))
    );

    let infoHTML = '';
    if(tilingRow!==null) {
      const col = S.players[tilingPi].pattern_lines[tilingRow].color;
      infoHTML = `<div class="info tiling" style="display:flex;align-items:center;justify-content:space-between">
        <span>→ <strong>${S.players[tilingPi].name}</strong> Reihe ${tilingRow+1}
          <span class="tile sm ${normColor(col)}" style="vertical-align:middle;margin:0 2px">${normColor(col)[0].toUpperCase()}</span>
          — passendes Kuppelfeld anklicken
        </span>
        <button class="btn" onclick="tilingPi=null;tilingRow=null;render()" style="font-size:10px;flex-shrink:0">✕</button>
      </div>`;
    } else if(hasPending) {
      const rows = pending.map(x=>
        `<span style="cursor:pointer;display:inline-flex;align-items:center;gap:2px;padding:1px 4px;border-radius:4px;background:#D1FAE5;border:1px solid #34D399"
          onclick="tilingPi=${x.pi};tilingRow=${x.ri};render()">
          <span class="tile sm ${normColor(x.color)}">${normColor(x.color)[0].toUpperCase()}</span>
          R${x.ri+1} ${x.pname}
        </span>`
      ).join(' ');
      infoHTML = `<div class="info tiling">
        <div style="font-size:10px;margin-bottom:5px;font-weight:600">Vollständige Reihen — anklicken zum Legen:</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap">${rows}</div>
      </div>`;
    } else if(chippable.length>0) {
      infoHTML = `<div class="info warn" style="font-size:10px">
        💡 Reihen mit 🎫-Button können mit Bonusplättchen vervollständigt werden<br>
        <span style="color:var(--text2)">2 gleichfarbige oder 3 beliebige Chips = 1 fehlende Fliese</span>
      </div>`;
    } else {
      infoHTML = `<div class="info tiling">✓ Alle Reihen abgeschlossen</div>`;
    }

    info.innerHTML = infoHTML + (!hasPending ? `
      <button class="btn pri" onclick="endTiling()" style="width:100%;margin-top:6px">
        Runde ${S.round} beenden ✓
      </button>` : '');
  } else if(S.phase==='end' || S.phase==='final') {
    const [p0,p1]=S.players;
    const w=p0.score>p1.score?p0.name:p1.score>p0.score?p1.name:p0.marker?p0.name:p1.marker?p1.name:'Unentschieden';
    if(S.phase==='end') {
      info.innerHTML=`<div class="info tiling" style="text-align:center">
        🏁 Runde 5 beendet!<br>
        <button class="btn pri" onclick="calculateEndScoring()" style="margin-top:6px;width:100%">🏆 Endwertung berechnen</button>
        <button class="btn" onclick="openScoringModal()" style="margin-top:4px;width:100%;font-size:10px">⚙️ Wertungsplatten ändern</button>
      </div>`;
    } else {
      info.innerHTML=`<div class="info tiling">🏁 <strong>${w}</strong> — ${p0.name}: ${p0.score} | ${p1.name}: ${p1.score}</div>`;
    }
  } else {
    const pending = S.players.filter(p=>!p.start_placed);
    if(pending.length > 0) {
      const names = pending.map(p=>p.name).join(' und ');
      info.innerHTML = `<div class="info warn">
        ⚠ <strong>Vorbereitung:</strong> ${names} ${pending.length>1?'müssen':'muss'} noch die erste Kuppelplatte legen.<br>
        <span style="font-size:10px;color:var(--text2)">Ein gelbes Feld aus der Kuppel selektieren und Kuppelplatte wählen</span>
      </div>`;
    } else {
      if(S.can_pass) {
        info.innerHTML = `<div class="info warn" style="display:flex;align-items:center;justify-content:space-between;gap:8px">
          <span>⏸ Keine Aktion möglich</span>
          <button class="btn danger" onclick="passMove()" style="white-space:nowrap">Passen</button>
        </div>`;
      } else {
        info.innerHTML = '';
      }
    }
  }

  const displayHTML = S.dome_display.map(t=>{
    const spaces = t.spaces.map(sp=>spaceHTML(sp)).join('');
    return `<div class="dgtile" data-tile-id="${t.id}" title="Kachel #${t.id}">
      <div class="d2x2" style="width:46px; height:46px;">${spaces}</div>
      <div class="dglabel">#${t.id}</div>
    </div>`;
  }).join('');

  const facsHTML = S.factories.map(f=>{
    const sunColors = [...new Set(f.sun)];
    const moonTops  = [...new Set(f.moon.map(s=>s[s.length-1]).filter(Boolean))];
    
    let chipContent = '🔒';
    if (f.chip_revealed && f.bonus_chip && f.bonus_chip.colors) {
      const c1 = normColor(f.bonus_chip.colors[0]);
      const c2 = f.bonus_chip.colors.length > 1 ? normColor(f.bonus_chip.colors[1]) : 'empty';
      
      chipContent = `<div class="bchip" style="cursor: pointer;">
        <div class="bchip-half ${c1}"></div>
        <div class="bchip-half ${c2}"></div>
      </div>`;
    }
    
    const chipHTML = f.bonus_chip
      ? `<span style="cursor:${f.chip_revealed?'pointer':'default'}" onclick="${f.chip_revealed?`bonusChipMove(${f.id})`:''}" title="Bonusplättchen">${chipContent}</span>`
      : '';
      
    const sunTiles = sunColors.map(c=>{
      const cnt = f.sun.filter(x=>x===c).length;
      return `<div class="cgroup" data-src="SMALL_FACTORY_SUN" data-fid="${f.id}" data-color="${c}">
        <div class="tile ${normColor(c)} click ${sel?.color===c&&sel?.factory_id===f.id?'sel':''}"></div>
        <span class="cnt">×${cnt}</span>
      </div>`;
    }).join('');
    
    const moonTopTiles = f.moon.map(stack => stack[stack.length-1]).filter(Boolean);
    const moonTiles = moonTopTiles.length
      ? `<div style="display:flex;gap:2px;align-items:center;margin-top:3px;flex-wrap:wrap">
          <span style="font-size:8px;color:var(--text3)">Moon:</span>
          ${moonTopTiles.map(c=>`<div class="tile sm ${normColor(c)}" title="Oben: ${c}">${normColor(c)[0].toUpperCase()}</div>`).join('')}
         </div>` : '';
    return `<div class="fcard">
      <div class="fhead"><span>Kleine Manufaktur ${f.id}</span>${chipHTML}</div>
      <div class="ftiles">${f.sun.length?sunTiles:'<span style="font-size:9px;color:var(--text3)">leer</span>'}</div>
      ${moonTiles}
    </div>`;
  }).join('');

  const lf = S.large_factory;
  const lSun = [...new Set(lf.sun)].map(c=>{
    const cnt=lf.sun.filter(x=>x===c).length;
    return `<div class="cgroup" data-src="LARGE_FACTORY_SUN" data-fid="null" data-color="${c}">
      <div class="tile ${normColor(c)} click"></div><span class="cnt">×${cnt}</span>
    </div>`;
  }).join('');
  const lMoon = [...new Set(lf.moon)].map(c=>{
    const cnt=lf.moon.filter(x=>x===c).length;
    return `<div class="cgroup" data-src="LARGE_FACTORY_MOON" data-fid="null" data-color="${c}">
      <div class="tile ${normColor(c)} click"></div><span class="cnt">×${cnt}</span>
    </div>`;
  }).join('');

  const moonTopCounts = S.moon_top_counts || {};
  const moonTopEntries = Object.entries(moonTopCounts);
  
  const moonActionHTML = moonTopEntries.length
    ? `<div style="margin-bottom:6px">
        <div class="lbl">Mondbereich (alle Manufakturen)</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap">
          ${moonTopEntries.map(([c, count]) => `
            <div class="cgroup" data-src="SMALL_FACTORY_MOON" data-fid="ALL" data-color="${c}"
              title="${count} oberste ${c}-Fliesen vom Moon aller Manufakturen">
              <div class="tile ${normColor(c)} click ${sel?.source==='SMALL_FACTORY_MOON'&&sel?.color===c?'sel':''}"></div>
              <span class="cnt">×${count}</span>
            </div>`).join('')}
        </div>
       </div>` : '';

document.getElementById('factories-area').innerHTML = `
    <div class="lbl" style="display:flex;justify-content:space-between">
      <span>Kuppelplatten (${S.dome_display.length}/3)</span>
      <span style="color:var(--text3)">Stapel: ${S.dome_stack_count}</span>
    </div>
    <div class="display-g">${displayHTML||'<span style="font-size:9px;color:var(--text3)">leer</span>'}</div>
    ${(() => {
      const cp = S.players[S.current_player];
      const canStack = S.phase==='drafting'
        && cp.start_placed
        && cp.tokens_used < 2
        && S.round < 5
        && S.dome_stack_count > 0
        && cp.dome_grid.flat().filter(Boolean).length < 9;
      return canStack ? `<button class="btn" onclick="openStackPicker()" style="width:100%;margin-bottom:6px;font-size:11px">
        📦 Vom Stapel ziehen (−1 Pkt/Karte) · ${S.dome_stack_count} verfügbar
      </button>` : '';
    })()}
    <div class="sep"></div>
    ${moonActionHTML}
    <div class="lbl" style="${!S.players.every(p=>p.start_placed)?'opacity:.35;pointer-events:none':''}">Sonnenbereich</div>
    <div style="${!S.players.every(p=>p.start_placed)?'opacity:.35;pointer-events:none':''}">
    ${facsHTML}
    <div class="fcard">
      <div class="fhead"><span>Große Manufaktur</span>${lf.marker?'<span style="color:#F59E0B">★</span>':''}</div>
      <div class="ftiles" style="margin-bottom:2px"><span style="font-size:8px;color:var(--text3)">Sun:</span>${lSun||'—'}</div>
      <div class="ftiles"><span style="font-size:8px;color:var(--text3)">Moon:</span>${lMoon||'—'}</div>
    </div>
    </div>`;

  document.getElementById('log').innerHTML = [...S.log].reverse().map(e=>{
    let cls='le';
    let style='';
    if(e.includes('🟡')||e.includes('+')&&e.includes('Pkt')&&!e.includes('−')){
      style='color:#D97706;font-weight:600'; 
    } else if(e.includes('🔴')||e.includes('Strafe')||e.includes('⚠️')){
      style='color:#DC2626'; 
    } else if(e.includes('⭐')){
      style='color:#7C3AED;font-weight:600'; 
    } else if(e.includes('🏁')){
      style='color:#F59E0B'; 
    } else if(e.includes('📦')){
      style='color:#DC2626'; 
    } else if(e.includes('✅')){
      style='color:#059669'; 
    } else if(e.includes('☀️')||e.includes('🌙')){
      style='color:var(--text2)';
    } else if(e.includes('🎫')){
      style='color:#7C3AED';
    }
    return `<div class="le" style="${style}">${e}</div>`;
  }).join('');
  
  const sdiv = document.getElementById('scoring-display');
  const editBtn = document.getElementById('scoring-edit-btn');
  const canEditScoring = S && !S.players.every(p=>p.start_placed);
  if(editBtn) editBtn.innerHTML = canEditScoring
    ? `<button class="btn" onclick="openScoringModal()" style="font-size:9px;padding:2px 6px">✏️</button>`
    : `<span style="font-size:9px;color:var(--text3)">🔒</span>`;
  if(sdiv && allScoringTiles.length) {
    sdiv.innerHTML = (S.scoring_tile_ids||[]).map(id=>{
      const t=allScoringTiles.find(t=>t.id===id);
      return t?`<span style="margin-right:6px">${t.emoji} ${t.name}</span>`:'';
    }).join('');
  }

  const vmDiv = document.getElementById('valid-moves');
  if(!vmDiv) return;

  if(S.phase === 'tiling') {
    const rows = (S.valid_tiling_rows||[]);
    if(rows.length === 0) {
      vmDiv.innerHTML = `<div class="le" style="color:var(--text3);font-style:italic">Alle platzierbaren Reihen gelegt ✓</div>`;
    } else {
      vmDiv.innerHTML = rows.map(x=>{
        const p = S.players[x.pi];
        const row = p.pattern_lines[x.ri];
        const nc = normColor(row.color);
        return `<div class="le" style="display:flex;align-items:center;gap:4px;padding:2px 0">
          <span style="color:var(--text3)">${p.name}</span>
          Reihe ${x.ri+1}
          <div class="tile sm ${nc}" style="flex-shrink:0">${nc[0].toUpperCase()}</div>
          <span style="color:var(--text3)">→ Kuppelreihe ${Math.floor(x.ri/2)}</span>
        </div>`;
      }).join('');
    }
    return;
  }

  if(!S.valid_moves || S.valid_moves.length === 0) {
    vmDiv.innerHTML = `<div class="le" style="color:var(--text3);font-style:italic">Keine Aktionen — Passen möglich</div>`;
    return;
  }

  const byType = {};
  for(const m of S.valid_moves) {
    if(!byType[m.type]) byType[m.type] = [];
    byType[m.type].push(m);
  }

  const lines = [];

  if(byType['start_tile_pending']) {
    lines.push(`<div class="le" style="color:#F59E0B;font-weight:600">⚠️ Startkachel legen (gelbe Felder anklicken)</div>`);
  }

  if(byType['stone']) {
    const sunColors = [...new Set(byType['stone']
      .filter(m=>m.source==='SMALL_FACTORY_SUN')
      .map(m=>m.color))];
    const moonColors = [...new Set(byType['stone']
      .filter(m=>m.source==='SMALL_FACTORY_MOON')
      .map(m=>m.color))];
    const lSunColors = [...new Set(byType['stone']
      .filter(m=>m.source==='LARGE_FACTORY_SUN')
      .map(m=>m.color))];
    const lMoonColors = [...new Set(byType['stone']
      .filter(m=>m.source==='LARGE_FACTORY_MOON')
      .map(m=>m.color))];

    if(sunColors.length)
      lines.push(`<div class="le" style="display:flex;align-items:center;gap:3px;padding:2px 0">
        ☀️ Sonne:
        ${sunColors.map(c=>`<div class="tile sm ${normColor(c)}">${normColor(c)[0].toUpperCase()}</div>`).join('')}
      </div>`);
    if(moonColors.length)
      lines.push(`<div class="le" style="display:flex;align-items:center;gap:3px;padding:2px 0">
        🌙 Mond (alle):
        ${moonColors.map(c=>`<div class="tile sm ${normColor(c)}">${normColor(c)[0].toUpperCase()}</div>`).join('')}
      </div>`);
    if(lSunColors.length)
      lines.push(`<div class="le" style="display:flex;align-items:center;gap:3px;padding:2px 0">
        ☀️ Gr. Fabrik:
        ${lSunColors.map(c=>`<div class="tile sm ${normColor(c)}">${normColor(c)[0].toUpperCase()}</div>`).join('')}
      </div>`);
    if(lMoonColors.length)
      lines.push(`<div class="le" style="display:flex;align-items:center;gap:3px;padding:2px 0">
        🌙 Gr. Fabrik Mond:
        ${lMoonColors.map(c=>`<div class="tile sm ${normColor(c)}">${normColor(c)[0].toUpperCase()}</div>`).join('')}
      </div>`);
  }

  if(byType['dome_display']) {
    const ids = [...new Set(byType['dome_display'].map(m=>m.tile_id))];
    lines.push(`<div class="le" style="padding:2px 0">🧩 Kuppelplatte aus Display: ${ids.map(id=>'#'+id).join(', ')}</div>`);
  }

  if(byType['dome_stack']) {
    lines.push(`<div class="le" style="padding:2px 0">📦 Kuppelplatte vom Stapel (−1 Pkt/Karte)</div>`);
  }

  if(byType['bonus_chip']) {
    const fids = byType['bonus_chip'].map(m=>'Fabrik '+m.factory_id).join(', ');
    lines.push(`<div class="le" style="padding:2px 0">🎫 Bonusplättchen: ${fids}</div>`);
  }

  vmDiv.innerHTML = lines.join('') || `<div class="le" style="color:var(--text3)">—</div>`;
}

// ── INTERACTION ───────────────────────────────────────────────────────────────
function onRowClick(ri) {
  if(!sel) return;
  const row = S.players[S.current_player].pattern_lines[ri];
  if(row.tiles.length >= row.capacity) return;
  if(row.color && row.color !== sel.color) return;
  if(sel.source === 'SMALL_FACTORY_SUN' && sel.moon_order && sel.moon_order.length > 0) {
    openMoonOrderModal(sel.moon_order, (ordered) => {
      stoneMove(sel.source, sel.factory_id, sel.color, ri, ordered);
    });
  } else {
    stoneMove(sel.source, sel.factory_id, sel.color, ri, sel.moon_order||[]);
  }
}

function onFloorDirect() {
  if(!sel) return;
  if(sel.source === 'SMALL_FACTORY_SUN' && sel.moon_order && sel.moon_order.length > 0) {
    openMoonOrderModal(sel.moon_order, (ordered) => {
      stoneMove(sel.source, sel.factory_id, sel.color, -1, ordered);
    });
  } else {
    stoneMove(sel.source, sel.factory_id, sel.color, -1, sel.moon_order||[]);
  }
}

function onTilingRowClick(pi, ri) {
  const row = S.players[pi].pattern_lines[ri];
  if(row.tiles.length !== row.capacity) return;
  tilingPi=pi; tilingRow=ri;
  render();
}

// ── CHIP MODAL ────────────────────────────────────────────────────────────────
let chipModal = null;

function openChipModal(pi, ri) {
  const p = S.players[pi];
  const row = p.pattern_lines[ri];
  const chips = p.bonus_chips.filter(c=>c);
  if(!chips.length){showError('Keine Bonusplättchen verfügbar');return;}
  chipModal = {
    pi, ri,
    color: row.color,
    missing: row.capacity - row.tiles.length,
    availableChips: chips.map(c=>({...c, colors:[...c.colors]})),
    selectionIds: [],
    confirmedGroups: [],
  };
  document.getElementById('chip-title').textContent =
    `Reihe ${ri+1} (${row.color}) — fehlen ${chipModal.missing} Fliese(n)`;
  document.getElementById('chip-info').textContent =
    `Wähle je Gruppe: 2 gleichfarbige ODER 3 beliebige Plättchen = 1 Fliese ersetzen`;
  renderChipModal();
  document.getElementById('chip-overlay').style.display='flex';
}

function renderChipModal() {
  if(!chipModal) return;
  const {pi,ri,color,missing,availableChips,selectionIds,confirmedGroups} = chipModal;
  const usedInGroups = confirmedGroups.flatMap(g=>g.chip_ids);

  const pool = document.getElementById('chip-pool');
  pool.innerHTML='';
  availableChips.forEach(chip=>{
    const inGroup = usedInGroups.includes(chip.id);
    const inSel = selectionIds.includes(chip.id);
    const div=document.createElement('div');
    div.className='chip-pill'+(inSel?' in-sel':'');
    div.style.opacity=inGroup?'0.3':'1';
    div.style.cursor=inGroup?'not-allowed':'pointer';
    chip.colors.forEach(c=>{
      const s=document.createElement('div');
      s.className=`tile sm ${normColor(c)}`;
      s.textContent=normColor(c)[0].toUpperCase();
      div.appendChild(s);
    });
    const id=document.createElement('span');
    id.style.cssText='font-size:8px;color:var(--text3);margin-left:2px';
    id.textContent='#'+chip.id;
    div.appendChild(id);
    if(!inGroup) div.addEventListener('click',()=>{toggleChipInSelection(chip.id);});
    pool.appendChild(div);
  });

  const selDiv=document.getElementById('chip-selection');
  const selEmpty=document.getElementById('chip-sel-empty');
  selDiv.querySelectorAll('.chip-pill').forEach(e=>e.remove());
  if(!selectionIds.length){ selEmpty.style.display='inline'; }
  else {
    selEmpty.style.display='none';
    selectionIds.forEach(id=>{
      const chip=availableChips.find(c=>c.id===id); if(!chip) return;
      const div=document.createElement('div');
      div.className='chip-pill in-sel';
      chip.colors.forEach(c=>{
        const s=document.createElement('div');
        s.className=`tile sm ${normColor(c)}`;
        s.textContent=normColor(c)[0].toUpperCase();
        div.appendChild(s);
      });
      div.addEventListener('click',()=>toggleChipInSelection(id));
      selDiv.appendChild(div);
    });
  }

  const same2 = selectionIds.length===2 &&
    selectionIds.every(id=>availableChips.find(c=>c.id===id)?.colors.includes(color));
  const any3 = selectionIds.length===3;
  const valid = same2||any3;
  const addBtn=document.getElementById('chip-add-btn');
  addBtn.disabled=!valid;
  addBtn.textContent= same2?'→ 2 gleichfarbige = 1 Fliese hinzufügen'
    :any3?'→ 3 beliebige = 1 Fliese hinzufügen'
    :`Auswahl (${selectionIds.length}) — 2 gleiche oder 3 beliebige`;

  const gArea=document.getElementById('chip-groups-area');
  const gDiv=document.getElementById('chip-groups');
  if(confirmedGroups.length){
    gArea.style.display='block';
    gDiv.innerHTML=confirmedGroups.map((g,gi)=>{
      const cchips=g.chip_ids.map(id=>availableChips.find(c=>c.id===id)).filter(Boolean);
      return `<div style="display:inline-flex;align-items:center;gap:2px;padding:3px 7px;background:#D1FAE5;border:1px solid #34D399;border-radius:5px;font-size:10px">
        ${cchips.map(c=>c.colors.map(col=>`<div class="tile sm ${normColor(col)}">${normColor(col)[0].toUpperCase()}</div>`).join('')).join('<span style="color:var(--text3)">+</span>')}
        <span style="color:#065F46;margin-left:3px">→ 1 Fliese</span>
        <span onclick="removeChipGroup(${gi})" style="cursor:pointer;color:var(--rot);margin-left:4px">✕</span>
      </div>`;
    }).join('');
  } else { gArea.style.display='none'; }

  const row=S.players[pi].pattern_lines[ri];
  const have=row.tiles.length+confirmedGroups.length;
  const cap=row.capacity;
  const preview=document.getElementById('chip-row-preview');
  preview.innerHTML=Array.from({length:cap},(_,i)=>
    i>=cap-have
      ?`<div class="tile sm ${normColor(color)}">${normColor(color)[0].toUpperCase()}</div>`
      :`<div class="tile sm empty"></div>`
  ).join('')+`<span style="font-size:10px;color:var(--text2);margin-left:6px">${have}/${cap}${have===cap?' ✓':''}</span>`;

  document.getElementById('chip-confirm').disabled = confirmedGroups.length!==missing;
}

function toggleChipInSelection(id) {
  const idx=chipModal.selectionIds.indexOf(id);
  if(idx>=0) chipModal.selectionIds.splice(idx,1);
  else chipModal.selectionIds.push(id);
  renderChipModal();
}

function addChipGroup() {
  const {selectionIds,confirmedGroups,color,availableChips}=chipModal;
  const same2=selectionIds.length===2&&selectionIds.every(id=>availableChips.find(c=>c.id===id)?.colors.includes(color));
  const any3=selectionIds.length===3;
  if(!same2&&!any3) return;
  confirmedGroups.push({chip_ids:[...selectionIds]});
  chipModal.selectionIds=[];
  renderChipModal();
}

function removeChipGroup(gi) {
  chipModal.confirmedGroups.splice(gi,1);
  renderChipModal();
}

function clearChipSelection() {
  chipModal.selectionIds=[];
  renderChipModal();
}

function confirmChips() {
  if(!chipModal) return;
  const {pi,ri,confirmedGroups}=chipModal;
  closeChipModal();
  tilingBonusChips(pi,ri,confirmedGroups);
}

function closeChipModal() {
  document.getElementById('chip-overlay').style.display='none';
  chipModal=null;
}

// ── DOME MODAL ────────────────────────────────────────────────────────────────
function openStackPicker() {
  const pi = S.current_player;
  const p = S.players[pi];
  const emptySlot = p.dome_grid.flatMap((row,sr)=>
    row.map((s,sc)=>s?null:{sr,sc}).filter(Boolean))[0];
  if(!emptySlot){showError('Keine freien Kuppelfelder!');return;}
  openDomeModal(pi, emptySlot.sr, emptySlot.sc);
  setTimeout(()=>{
    const sec=document.getElementById('dome-stack-section');
    if(sec) sec.style.display='flex';
  }, 100);
}

function openDomeModal(pi, sr, sc) {
  const p = S.players[pi];
  const isStart = !p.start_placed;
  if(!isStart && pi !== S.current_player) return;
  if(!isStart && !p.can_place_dome) return;

  domeModal = {pi, slot_r:sr, slot_c:sc, tile_id:null, rotation:0, is_start:isStart};
  const notice = document.getElementById('dome-notice');
  if(isStart) {
    notice.textContent='Eine Kuppelplatte wählen und Rotation setzen';
    notice.style.display='block';
  } else notice.style.display='none';

  document.getElementById('dome-title').textContent = isStart ? 'Erste Kuppelplatte legen' : 'Kuppelplatte legen';

  const grid = document.getElementById('dome-pool');
  grid.innerHTML = '';
  S.dome_display.forEach(t=>{
    const div = document.createElement('div');
    div.className='ptile'; div.dataset.id=t.id;
    div.innerHTML=`<div class="d2x2" style="width:46px; height:46px;">${t.spaces.map(sp=>spaceHTML(sp)).join('')}</div>
      <div class="plabel">#${t.id}</div>`;
    div.addEventListener('click',()=>{
      domeModal.tile_id=t.id;
      grid.querySelectorAll('.ptile').forEach(e=>e.classList.remove('sel'));
      div.classList.add('sel');
      document.getElementById('dome-confirm').disabled=false;
      buildPreview();
    });
    grid.appendChild(div);
  });

  document.getElementById('dome-confirm').disabled=true;
  document.getElementById('rotbtns').querySelectorAll('.rotbtn').forEach((b,i)=>b.classList.toggle('act',i===0));
  buildPreview();

  const stackSec = document.getElementById('dome-stack-section');
  if (!isStart && S.dome_stack_count > 0) {
    stackSec.style.display = 'flex';
    document.getElementById('stack-n').max = S.dome_stack_count;
    document.getElementById('stack-n').value = 1;
  } else {
    stackSec.style.display = 'none';
  }

  document.getElementById('dome-overlay').style.display='flex';
}

function buildPreview() {
  const prev = document.getElementById('dome-preview');
  
  if (domeModal?.tile_id === null || domeModal?.tile_id === undefined) { 
    prev.innerHTML = ''; 
    return; 
  }
  
  let tile = S.dome_display.find(t => t.id === domeModal.tile_id);
  if (!tile && domeModal.stack_tiles) {
    tile = domeModal.stack_tiles.find(t => t.id === domeModal.tile_id);
  }
  
  if (!tile) { prev.innerHTML = ''; return; }
  
  const ROT = {0:[0,1,2,3], 90:[2,0,3,1], 180:[3,2,1,0], 270:[1,3,0,2]};
  const rotated = ROT[domeModal.rotation||0].map(i => tile.spaces[i]);
  
  prev.innerHTML = `<div class="d2x2" style="width:46px; height:46px;">${rotated.map(sp => spaceHTML(sp)).join('')}</div>`;
}

async function doStackDraw() {
  const n = +document.getElementById('stack-n').value;
  if(!n || n < 1) return;
  const pi = domeModal.pi;
  
  const d = await api('/stack/peek', {num: n, player: pi});
  if(!d.ok){ showError(d.error); return; }
  
  domeModal.stack_tiles = d.tiles;
  
  const stackSec = document.getElementById('dome-stack-section');
  if(stackSec) stackSec.style.display = 'none';

  const notice = document.getElementById('dome-notice');
  notice.innerHTML = `<strong>Gezogene Platten:</strong> Such dir 1 Platte aus, der Rest kommt unter den Stapel. (Kosten: −${n} Pkt)<br>
                      <span style="font-size:10px; font-weight:normal;">Wähle danach unten deine Rotation und bestätige.</span>`;
  notice.style.display = 'block';

  const pool = document.getElementById('dome-pool');
  pool.innerHTML = ''; 
  
  d.tiles.forEach(t => {
    const div = document.createElement('div');
    div.className = 'ptile'; 
    div.dataset.id = t.id;
    
    div.innerHTML = `
      <div class="d2x2" style="width:46px; height:46px;">${t.spaces.map(sp=>spaceHTML(sp)).join('')}</div>
      <div class="plabel">#${t.id}</div>`;
      
    div.addEventListener('click', () => {
      domeModal.tile_id = t.id; 
      domeModal.stack_draw = {num: n, chosen_id: t.id, player: pi};
      
      pool.querySelectorAll('.ptile').forEach(e => e.classList.remove('sel'));
      div.classList.add('sel');
      
      document.getElementById('dome-confirm').disabled = false;
      buildPreview(); 
    });
    
    pool.appendChild(div);
  });
}

function closeDomeModal() {
  document.getElementById('dome-overlay').style.display='none';
  domeModal=null;
}

async function showActiveScoringTiles() {
  if (typeof S === 'undefined' || !S) {
    alert("Das Spiel hat noch nicht begonnen.");
    return;
  }

  try {
    const res = await api('/scoring_tiles');
    if (!res.ok) {
      alert("Fehler beim Laden der Ziele.");
      return;
    }

    const activeIds = S.scoring_tile_ids || [0, 1, 2];
    const activeTiles = res.tiles.filter(t => activeIds.includes(t.id));

    let infoText = "🏆 AKTIVE WERTUNGSPLÄTTCHEN 🏆\n\n";
    activeTiles.forEach(t => {
      infoText += `${t.emoji} ${t.name.toUpperCase()}\n    ${t.description}\n\n`;
    });

    alert(infoText);

  } catch (error) {
    console.error("Fehler beim Abrufen der Ziele:", error);
  }
}

async function confirmDome() {
  if(!domeModal||domeModal.tile_id===null) return;
  const {pi,slot_r,slot_c,tile_id,rotation,is_start,stack_draw} = domeModal;
  if(is_start) { startTileMove(pi, tile_id, slot_r, slot_c, rotation); return; }
  if(stack_draw) {
    let sr=slot_r, sc=slot_c;
    if(sr===-1){
      const p=S.players[pi];
      const empty=p.dome_grid.flatMap((row,r)=>row.map((s,c)=>s?null:{r,c}).filter(Boolean));
      if(!empty.length){showError('Keine freien Slots!');return;}
      sr=empty[0].r; sc=empty[0].c;
    }
    const d = await api('/move/dome_stack', {
      num_drawn: stack_draw.num, chosen_id: stack_draw.chosen_id,
      slot_row: sr, slot_col: sc, rotation
    });
    if(!d.ok){showError(d.error);return;}
    S=d.state; closeDomeModal(); render();
  } else {
    domeMove(tile_id, slot_r, slot_c, rotation);
  }
}

// ── MOON ORDER MODAL ─────────────────────────────────────────────────────────
let moonModal = null; 

function openMoonOrderModal(remaining, callback) {
  if(remaining.length <= 1) { callback(remaining); return; }
  const items = remaining.map((color, i) => ({uid: i, color}));
  moonModal = {items, ordered: [], callback};
  renderMoonModal();
  document.getElementById('moon-confirm').disabled = true;
  document.getElementById('moon-overlay').style.display = 'flex';
}

function renderMoonModal() {
  const tilesDiv = document.getElementById('moon-tiles');
  const stackDiv = document.getElementById('moon-stack');
  const empty    = document.getElementById('moon-stack-empty');

  tilesDiv.innerHTML = '';
  moonModal.items.forEach(item => {
    const div = document.createElement('div');
    div.className = `tile ${normColor(item.color)} click`;
    div.style.cursor = 'pointer';
    div.title = `${item.color} — klicken zum Stapeln`;
    div.textContent = normColor(item.color)[0].toUpperCase();
    div.addEventListener('click', () => addToMoonStack(item.uid));
    tilesDiv.appendChild(div);
  });

  stackDiv.querySelectorAll('.tile').forEach(e => e.remove());
  if(moonModal.ordered.length === 0) {
    empty.style.display = 'inline';
  } else {
    empty.style.display = 'none';
    moonModal.ordered.forEach((item, i) => {
      const div = document.createElement('div');
      div.className = `tile ${normColor(item.color)}`;
      div.textContent = normColor(item.color)[0].toUpperCase();
      const isTop = i === moonModal.ordered.length - 1;
      div.style.outline = isTop ? '2.5px solid var(--text)' : '';
      div.title = isTop ? 'Oben (sichtbar im Mondbereich)' : `${i+1}. von unten`;
      stackDiv.insertBefore(div, empty);
    });
  }
}

function addToMoonStack(uid) {
  const idx = moonModal.items.findIndex(item => item.uid === uid);
  if(idx === -1) return;
  const item = moonModal.items.splice(idx, 1)[0];
  moonModal.ordered.push(item);
  renderMoonModal();
  if(moonModal.items.length === 0) {
    document.getElementById('moon-confirm').disabled = false;
  }
}

function confirmMoonOrder() {
  if(!moonModal) return;
  const cb = moonModal.callback;
  const ordered = moonModal.ordered.map(item => item.color);
  closeMoonModal();
  cb(ordered);
}

function closeMoonModal() {
  document.getElementById('moon-overlay').style.display = 'none';
  moonModal = null;
}

// ── STACK BUY MODAL ──────────────────────────────────────────────────────────
function openStackBuyModal() {
  const pi = S.current_player;
  openDomeModal(pi, -1, -1);
}

// ── SCORING TILES ─────────────────────────────────────────────────────────────
let allScoringTiles = [];
let selectedScoringIds = new Set([0,1,2]);

async function openScoringModal() {
  if(S && S.players.every(p=>p.start_placed)) {
    showError('Wertungsplatten können nach dem Legen der Startfliesen nicht mehr geändert werden.');
    return;
  }
  if(!allScoringTiles.length) {
    const d = await api('/scoring_tiles');
    if(!d.ok) return;
    allScoringTiles = d.tiles;
  }
  selectedScoringIds = new Set(S.scoring_tile_ids || [0,1,2]);
  renderScoringGrid();
  document.getElementById('scoring-overlay').style.display='flex';
}

function renderScoringGrid() {
  const grid = document.getElementById('scoring-grid');
  if(!grid) return;
  grid.innerHTML = allScoringTiles.map(t => {
    const sel = selectedScoringIds.has(t.id);
    return `<div data-stid="${t.id}" onclick="toggleScoringTile(${t.id})"
      style="border:1.5px solid ${sel?'var(--blau)':'var(--border)'};
             background:${sel?'#EFF6FF':'var(--surface)'};
             border-radius:8px;padding:8px;cursor:pointer;transition:all .1s">
      <div style="font-size:16px;margin-bottom:4px">${t.emoji}</div>
      <div style="font-size:11px;font-weight:600">${t.name}</div>
      <div style="font-size:9px;color:var(--text2);margin-top:2px">${t.description}</div>
    </div>`;
  }).join('');
  const count = selectedScoringIds.size;
  const countEl = document.getElementById('scoring-count');
  if(countEl) countEl.textContent = count;
  const btn = document.getElementById('scoring-confirm');
  if(btn) btn.disabled = count !== 3;
}

function toggleScoringTile(id) {
  if(selectedScoringIds.has(id)) {
    selectedScoringIds.delete(id);
  } else if(selectedScoringIds.size < 3) {
    selectedScoringIds.add(id);
  }
  renderScoringGrid();
}

async function confirmScoringTiles() {
  const ids = [...selectedScoringIds];
  const d = await api('/scoring_tiles/select', {ids});
  if(!d.ok){showError(d.error);return;}
  S = d.state;
  document.getElementById('scoring-overlay').style.display='none';
  render();
}

async function calculateEndScoring() {
  const d = await api('/end_scoring', {});
  if(!d.ok){showError(d.error);return;}
  S = d.state;
  showEndResults(d.results);
  render();
}

function showEndResults(results) {
  const p0 = S.players[0], p1 = S.players[1];
  const winner = p0.score > p1.score ? p0.name
    : p1.score > p0.score ? p1.name
    : p0.marker ? p0.name : p1.marker ? p1.name : 'Unentschieden';
  const tileRows = (S.scoring_tile_ids||[]).map(tid=>{
    const t = allScoringTiles.find(t=>t.id===tid);
    const r0 = results['0']?.[tid], r1 = results['1']?.[tid];
    if(!t) return '';
    const pts = (r,sign='')=> r?`<span style="font-weight:600;color:${r.score>=0?'#059669':'#DC2626'}">${r.score>=0?'+':''}${r.score}</span>`:'—';
    return `<tr style="border-bottom:1px solid var(--border)">
      <td style="padding:4px 6px;font-size:10px">${t.emoji} ${t.name}</td>
      <td style="padding:4px 8px;text-align:right">${pts(r0)}</td>
      <td style="padding:4px 8px;text-align:right">${pts(r1)}</td>
    </tr>`;
  }).join('');

  // HIER WIRD DAS MODAL MIT DER .modal KLASSE ERSTELLT
  const html = `<div class="modal">
    <h3 style="font-size:16px;font-weight:700;margin-bottom:12px;text-align:center">🏆 Endwertung</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:10px">
      <thead><tr style="background:var(--bg)">
        <th style="padding:4px 6px;text-align:left;font-size:10px;color:var(--text2)">Kriterium</th>
        <th style="padding:4px 8px;text-align:right;font-size:10px;color:var(--text2)">${p0.name}</th>
        <th style="padding:4px 8px;text-align:right;font-size:10px;color:var(--text2)">${p1.name}</th>
      </tr></thead>
      <tbody>${tileRows}</tbody>
      <tfoot><tr style="background:var(--bg);font-weight:700">
        <td style="padding:5px 6px;font-size:11px">Gesamt</td>
        <td style="padding:5px 8px;text-align:right;font-size:14px">${p0.score}</td>
        <td style="padding:5px 8px;text-align:right;font-size:14px">${p1.score}</td>
      </tr></tfoot>
    </table>
    <div style="text-align:center;font-size:18px;font-weight:700;color:var(--blau);margin:10px 0">
      🥇 ${winner} gewinnt!
    </div>
    <button style="width:100%;padding:9px;background:var(--text);color:#fff;border:none;border-radius:7px;cursor:pointer;font-family:inherit;font-size:12px" onclick="document.getElementById('end-overlay').style.display='none';newGame()">Neues Spiel</button>
  </div>`;

  let ov = document.getElementById('end-overlay');
  if(!ov){
    ov = document.createElement('div');
    ov.className = 'overlay';
    ov.id = 'end-overlay';
    document.body.appendChild(ov);
  }
  ov.innerHTML = html; 
  ov.style.display = 'block'; // block ist hier besser wegen der absoluten Positionierung
  
  // WICHTIG: Das Endwertungs-Fenster verschiebbar machen!
  makeDraggable('end-overlay');
}

// ── EVENT DELEGATION ──────────────────────────────────────────────────────────
document.addEventListener('click', e=>{
  const cg = e.target.closest('[data-src]');
  if(cg && S?.phase==='drafting') {
    const src=cg.dataset.src, fidRaw=cg.dataset.fid, color=cg.dataset.color;
    const fid = (fidRaw==='null'||fidRaw==='ALL') ? null : +fidRaw;
    let moon_order=[];
    if(src==='SMALL_FACTORY_SUN' && fid) {
      const f=S.factories.find(f=>f.id===fid);
      if(f) moon_order=f.sun.filter(c=>c!==color);
    }
    sel={source:src, factory_id:fid, color, moon_order};
    render(); return;
  }

  const dslot = e.target.closest('[data-dome]');
  if(dslot) {
    const [pi,sr,sc]=dslot.dataset.dome.split(',').map(Number);
    openDomeModal(pi,sr,sc); return;
  }

  const ts = e.target.closest('[data-tiling]');
  if(ts) {
    const [pi,sr,sc,si]=ts.dataset.tiling.split(',').map(Number);
    if(tilingPi===pi && tilingRow!==null) {
      const expectedDomeRow = Math.floor(tilingRow/2);
      if(sr !== expectedDomeRow) {
        showError(`Reihe ${tilingRow+1} gehört zur Kuppelreihe ${expectedDomeRow}, nicht ${sr}`);
        return;
      }
      tilingMove(pi, tilingRow, sr, sc, si);
    }
    return;
  }

  const rb = e.target.closest('.rotbtn');
  if(rb && domeModal) {
    domeModal.rotation=+rb.dataset.rot;
    document.querySelectorAll('.rotbtn').forEach(b=>b.classList.toggle('act',b===rb));
    buildPreview(); return;
  }

  const dgt = e.target.closest('[data-tile-id]');
  if(dgt && domeModal) {
    const id=+dgt.dataset.tileId;
    domeModal.tile_id=id;
    document.querySelectorAll('.dgtile').forEach(e=>e.classList.toggle('sel',+e.dataset.tileId===id));
    document.getElementById('dome-confirm').disabled=false;
    buildPreview(); return;
  }
});

// ── RENDER ────────────────────────────────────────────────────────────────────
function render() {
  if(!S) return;
  document.getElementById('round-lbl').textContent=`Runde ${S.round}/5`;
  renderBoard(0);
  renderBoard(1);
  renderCenter();
}

// ── DRAG & DROP FÜR MODALS ──────────────────────────────────────────────────
function makeDraggable(overlayId) {
  const overlay = document.getElementById(overlayId);
  if (!overlay) return;
  const modal = overlay.querySelector('.modal');
  if (!modal) return;
  const handle = modal.querySelector('h3');
  if (!handle) return;
  
  let isDown = false, startX, startY, startLeft, startTop;

  handle.addEventListener('mousedown', (e) => {
    isDown = true;
    startX = e.clientX;
    startY = e.clientY;
    
    const rect = modal.getBoundingClientRect();
    if (!modal.style.left || modal.style.left.includes('%')) {
      modal.style.transform = 'none';
      modal.style.left = rect.left + 'px';
      modal.style.top = rect.top + 'px';
    }
    startLeft = parseFloat(modal.style.left);
    startTop = parseFloat(modal.style.top);
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault(); 
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    modal.style.left = (startLeft + dx) + 'px';
    modal.style.top = (startTop + dy) + 'px';
  });

  document.addEventListener('mouseup', () => {
    isDown = false;
  });
}

// ── START ─────────────────────────────────────────────────────────────────────
makeDraggable('dome-overlay');
makeDraggable('moon-overlay');
makeDraggable('chip-overlay');      // <-- Jetzt alle verschiebbar
makeDraggable('scoring-overlay');   // <-- Jetzt alle verschiebbar
newGame();