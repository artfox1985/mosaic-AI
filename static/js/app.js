// -- STATE ---------------------------------------------------------------------
let S = null;          // server state
let sel = null;        // {source, factory_id, color}
let domeModal = null;  // {pi, slot_r, slot_c, tile_id, rotation, is_start}
// Schwebende Kuppelplatzierung: Karte ist gewählt (Display ODER Stapel),
// der Slot folgt per Board-Klick. source: 'display' | 'stack'.
// display: {source:'display', pi, tile_id, rotation, tile}
// stack:   {source:'stack',   pi, tile_id, rotation, tile, num, chosen_id}
let pendingStackPlacement = null;
let tilingPi = null, tilingRow = null;
let humanTilingDone = false;
// Nutzer-Feedback (2026-07-29, Folgeauftrag): Reihenfolge-Regel gilt nur fuer
// die PLATZIERUNG voller Reihen -- eine nur-per-Chips-komplettierbare Reihe
// darf der Mensch bewusst ueberspringen, um eine SPAETERE chip-faehige Reihe
// zu bedienen (engine/src/round_end.rs::chippable_rows filtert nur `ri <
// tiled_max`, nicht "nur die oberste"). Rein clientseitige Session-Sets pro
// Spieler -- s. getTilingRowState()/render(). Key = Spielerindex (0/1).
let skippedChipRows = {0: new Set(), 1: new Set()};

// -- API -----------------------------------------------------------------------
// KI-State
let AI_ENABLED  = false;
let AI_PLAYER   = 1;   // KI ist immer Spieler 2 (Index 1)
let AI_THINKING = false;

// Lehrer-Modus (Task #97): 0=aus, 1=Kandidaten, 2=+Bewertungen, 3=+Coach-Feedback.
let TEACHER_LEVEL   = 0;
let TEACHER_SIMS    = 800;
let hintCandidates  = null;   // zuletzt vom Server geholte Top-Kandidaten (fürs Brett-Marker)

function setAIThinking(on) {
  AI_THINKING = on;
  let overlay = document.getElementById('ai-thinking-overlay');
  if (!overlay) return;
  overlay.style.display = on ? 'flex' : 'none';
}

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

let CURRENT_CHAMPION = null;   // vom Server geladener amtierender Champion (models/champion.txt)

// Spielerprofile / Elo (Nutzer-Feature 2026-08-02). RATING_INFO haelt die
// vom Server bei /new_game aufgeloesten Profile + KI-Anker fuer die LAUFENDE
// Partie (Rating-Anzeige am Spielernamen, s. renderBoard/render()).
let RATING_INFO = {p0: null, p1: null, ai: null, unrated: false};

// Rating-Badge-HTML neben dem Spielernamen in renderBoard(pi) -- "~" markiert
// einen Schaetzwert (KI-Anker ohne direkte Arena-Kante bei dieser Sims-Zahl,
// siehe player_profiles.py::estimate_ai_anchor). Leerer String, wenn fuer
// diesen Spielerindex weder Profil noch KI-Anker bekannt ist (Gast-Spiel).
//
// User-Entscheid 2026-08-02: sobald in der Partie KI-Tipps genutzt wurden
// (RATING_INFO.unrated, gesetzt bei Coach-Stufe 3 ab Spielstart bzw. beim
// ersten bestaetigten Tipp-Klick, s. requestHint()) zeigt JEDE Profil-Seite
// dauerhaft ein "ungewertet"-Badge statt der Zahl -- die KI-Seite bleibt
// unveraendert (ihr Anker aendert sich ohnehin nie).
function _ratingBadgeHTML(pi) {
  if (AI_ENABLED && pi === AI_PLAYER) {
    const ai = RATING_INFO.ai;
    if (!ai || ai.elo == null) return '';
    const val = Math.round(ai.elo);
    const title = `KI-Elo-Anker ${ai.node}${ai.is_estimate ? ' (geschätzt -- keine direkte Arena-Kante bei dieser Sims-Zahl)' : ''}`;
    return ` <span class="rating-badge" title="${title}">${ai.is_estimate ? '~' : ''}${val}</span>`;
  }
  const prof = pi === 0 ? RATING_INFO.p0 : RATING_INFO.p1;
  if (!prof) return '';
  if (RATING_INFO.unrated) {
    return ` <span class="rating-badge unrated" title="KI-Tipps genutzt — diese Partie zählt nicht fürs Rating">ungewertet</span>`;
  }
  return ` <span class="rating-badge" title="Profil-Rating (Elo)">${Math.round(prof.rating)}</span>`;
}

function openNewGameModal() {
  document.getElementById('newgame-overlay').style.display = 'flex';
  // Modell-Feld beim Öffnen IMMER auf den aktuellen Champion setzen (Nutzer-
  // Anstoss 2026-07-27) -- statt eines im HTML hart kodierten Versionsnamens,
  // der bei jedem Champion-Wechsel veraltet waere.
  api('/champion').then(d => {
    if (d.ok && d.model) {
      CURRENT_CHAMPION = d.model;
      const el = document.getElementById('ng-model');
      if (el) el.value = d.model;
    }
  }).catch(() => {});
  ngLoadProfiles();
}

// Laedt die Profil-Liste vom Server und befuellt beide Auswahl-Dropdowns
// (P1 immer, P2 nur relevant bei Mensch-gegen-Mensch, s. #ng-p2-block).
// `keepSelection`: aktuell gewaehlte IDs behalten, falls noch vorhanden
// (z.B. nach dem Anlegen eines neuen Profils via ngCreateProfile).
async function ngLoadProfiles(keepSelection = true) {
  const selP0 = document.getElementById('ng-profile-p0');
  const selP1 = document.getElementById('ng-profile-p1');
  if (!selP0 || !selP1) return;
  const prevP0 = keepSelection ? selP0.value : '';
  const prevP1 = keepSelection ? selP1.value : '';
  const d = await api('/profiles');
  if (!d.ok) return;
  const opts = ['<option value="">Gast (ungewertet)</option>']
    .concat(d.profiles.map(p => `<option value="${p.id}">${_escapeHtml(p.name)} (${Math.round(p.rating)})</option>`))
    .join('');
  selP0.innerHTML = opts;
  selP1.innerHTML = opts;
  if (d.profiles.some(p => p.id === prevP0)) selP0.value = prevP0;
  if (d.profiles.some(p => p.id === prevP1)) selP1.value = prevP1;
}

// "+ Neu"-Button neben den Profil-Dropdowns: legt per einfachem Prompt ein
// neues Profil an (Start-Rating 1000) und waehlt es sofort aus.
async function ngCreateProfile(which) {
  const name = (prompt('Name für das neue Profil:') || '').trim();
  if (!name) return;
  const d = await api('/profiles', {name});
  if (!d.ok) { showError(d.error || 'Profil konnte nicht angelegt werden.'); return; }
  await ngLoadProfiles(false);
  const sel = document.getElementById(which === 'p1' ? 'ng-profile-p1' : 'ng-profile-p0');
  if (sel) sel.value = d.profile.id;
}

function ngToggleAI() {
  const on = document.getElementById('ng-ai-toggle').checked;
  document.getElementById('ng-ai-settings').style.display = on ? 'block' : 'none';
  // Spieler-2-Block (Name + Profil) nur bei Mensch-gegen-Mensch relevant --
  // gegen die KI hat "Spieler 2" kein eigenes Profil (die KI ist der Anker).
  const p2block = document.getElementById('ng-p2-block');
  if (p2block) p2block.style.display = on ? 'none' : 'block';
  const track = document.getElementById('ng-toggle-track');
  const thumb = document.getElementById('ng-toggle-thumb');
  track.style.background = on ? 'var(--blau, #3b82f6)' : 'var(--border)';
  thumb.style.transform   = on ? 'translateX(18px)' : 'translateX(0)';
  ngUpdateStartLabels();
}

function ngUpdateStartLabels() {
  const aiOn    = document.getElementById('ng-ai-toggle').checked;
  const p1name  = document.getElementById('ng-name').value.trim() || 'Spieler 1';
  const p2nameEl = document.getElementById('ng-name-p2');
  const p2name  = (p2nameEl && p2nameEl.value.trim()) || 'Spieler 2';
  const p2label = document.getElementById('ng-start-p2-text');
  if (p2label) p2label.textContent = aiOn ? 'KI' : p2name;
  const p1label = document.getElementById('ng-start-p1-text');
  if (p1label) p1label.textContent = p1name;
}

async function startNewGame() {
  document.getElementById('newgame-overlay').style.display = 'none';

  const playerName = document.getElementById('ng-name').value.trim() || 'Spieler 1';
  const aiEnabled  = document.getElementById('ng-ai-toggle').checked;
  const p2NameEl   = document.getElementById('ng-name-p2');
  const player2Name = aiEnabled ? 'KI' : ((p2NameEl && p2NameEl.value.trim()) || 'Spieler 2');
  const model      = document.getElementById('ng-model').value.trim() || CURRENT_CHAMPION || 'v16_best';
  const sims       = parseInt(document.getElementById('ng-sims').value) || 400;
  const seedRaw    = document.getElementById('ng-seed').value.trim();
  const seed       = seedRaw === '' ? null : parseInt(seedRaw);
  const teacherLevel = aiEnabled ? parseInt(document.getElementById('ng-teacher-level').value) || 0 : 0;
  const teacherSims  = parseInt(document.getElementById('ng-teacher-sims').value) || 800;
  const debugBtnOn   = document.getElementById('ng-debug-toggle').checked;
  const debugBtn     = document.getElementById('ki-debugger-btn');
  if (debugBtn) debugBtn.style.display = debugBtnOn ? '' : 'none';

  // Spielerprofile (Nutzer-Feature 2026-08-02): P1 immer moeglich, P2 nur
  // bei Mensch-gegen-Mensch (gegen die KI hat "Spieler 2" kein Profil).
  const profileP0 = document.getElementById('ng-profile-p0')?.value || null;
  const profileP1 = aiEnabled ? null : (document.getElementById('ng-profile-p1')?.value || null);

  AI_ENABLED = aiEnabled;
  AI_PLAYER  = 1;
  TEACHER_LEVEL = teacherLevel;
  TEACHER_SIMS  = teacherSims;
  hintCandidates = null;

  // Startspieler aus Radio-Button lesen
  const startVal = document.querySelector('input[name="ng-start"]:checked')?.value || '0';
  let firstPlayer;
  if (startVal === 'random') {
    firstPlayer = Math.random() < 0.5 ? 0 : 1;
  } else {
    firstPlayer = parseInt(startVal);
  }

  const body = {
    names:        [playerName, player2Name],
    ai_enabled:   aiEnabled,
    ai_side:      1,
    model:        model,
    sims:         sims,
    first_player: firstPlayer,
    teacher_level: teacherLevel,
    teacher_sims:  teacherSims,
    profile_p0:   profileP0,
    profile_p1:   profileP1,
  };
  if (seed !== null && !Number.isNaN(seed)) {
    body.seed = seed;
  }

  const d = await api('/new_game', body);
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; domeModal=null; tilingPi=null; tilingRow=null;
  window._gameEndLogged = false;
  _chipGhosts = {0: [], 1: []}; _prevBonusChips = {0: null, 1: null};
  // Spielerprofile: vom Server aufgeloeste Profil-/KI-Rating-Info fuer die
  // laufende Partie merken (Rating-Anzeige am Spielernamen, s. renderBoard()).
  // hints_used=true kommt vom Server schon HIER, wenn Coach-Stufe 3 gewaehlt
  // wurde (automatisches Zug-Feedback nach jedem Zug) -- die Partie ist dann
  // von Anfang an ungewertet, kein Warten auf einen Tipp-Klick noetig.
  RATING_INFO = {p0: d.profile_p0 || null, p1: d.profile_p1 || null, ai: d.ai_rating || null, unrated: !!d.hints_used};
  if (d.teacher_level !== undefined) TEACHER_LEVEL = d.teacher_level;
  if (d.teacher_sims !== undefined) TEACHER_SIMS = d.teacher_sims;
  if (d.seed !== undefined) {
    window._gameSeed    = d.seed;
    window._gameLogFile = d.log_file;
    console.log(`🎲 Spiel gestartet | Seed: ${d.seed} | Log: ${d.log_file}`);
  }
  render();
  const dt = await api('/scoring_tiles');
  if(dt.ok) {
    allScoringTiles = dt.tiles;
    selectedScoringIds = new Set(S.scoring_tile_ids || [0,1,2]);
    renderScoringGrid();
    document.getElementById('scoring-overlay').style.display='flex';
  }
}

async function newGame() {
  // Direkt-Start ohne Modal (z.B. nach Spielende)
  await startNewGame();
}

function aiIsDue() {
  // Ist die KI gerade dran?
  if (!AI_ENABLED || !S) return false;
  if (S.phase === 'end' || S.phase === 'final') return false;
  if (S.phase === 'drafting') return S.current_player === AI_PLAYER;
  if (S.phase === 'tiling') {
	return humanTilingDone;
  }
  return false;
}

async function triggerAIMove() {
  if (!aiIsDue()) return;
  if (AI_THINKING) return;

  setAIThinking(true);
  try {
    await new Promise(r => setTimeout(r, 600));

    // Loop: KI zieht solange sie dran ist (max 20 Züge gegen Endlosloop)
    let safety = 0;
    while (aiIsDue() && safety++ < 20) {
      const d = await api('/ai/move');
      if (!d.ok) {
        // Kein Fehler anzeigen wenn KI einfach nicht dran ist
        if (d.error !== 'Nicht der Zug der KI'
            && d.error !== 'KI hat keine Tiling-Züge mehr'
            && d.error !== 'Mensch ist noch am Tilen') {
          showError('KI-Fehler: ' + d.error);
        }
        break;
      }
      S = d.state;
      render();
      if (aiIsDue()) await new Promise(r => setTimeout(r, 350));
    }
  } finally {
    setAIThinking(false);
  }
}

// -- AGGRESSIVITAETS-REGLER (Task #28): ENTFERNT 2026-08-05 --------------------
// Nutzer-Entscheid nach Engine-Audit F1 (opp_points las den ownership-Head):
// alle Blend-Messungen waren ungueltig, der Blend bleibt engine-weit auf
// 0/inaktiv (Env-Defaults), bis er im v20-Zyklus mit korrektem Signal neu
// kartiert ist. Der Engine-Knopf (set_aggression_params, POST /api/aggression)
// existiert weiter -- er wird nur von nichts mehr aufgerufen.

// -- LEHRER-MODUS (Task #97) ---------------------------------------------------

// Ist gerade ein Tipp-Abruf sinnvoll (Mensch dran, Drafting-Phase, Stufe>=1)?
function teacherHintEligible() {
  return TEACHER_LEVEL >= 1 && AI_ENABLED && S && S.phase === 'drafting' && S.current_player !== AI_PLAYER;
}

// Aktualisiert Sichtbarkeit/Enabled-Status des "💡 Tipp"-Buttons -- von render() aufgerufen.
function updateTeacherUI() {
  const btn = document.getElementById('teacher-hint-btn');
  if (!btn) return;
  const showBtn = TEACHER_LEVEL >= 1 && AI_ENABLED;
  btn.style.display = showBtn ? 'inline-block' : 'none';
  const eligible = teacherHintEligible();
  btn.disabled = !eligible;
  if (!eligible) {
    clearHintHighlights();
  } else if (hintCandidates) {
    renderHintHighlights();  // nach jedem Re-Render (innerHTML wird neu gebaut) erneut anwenden
  }
}

// User-Entscheid 2026-08-02: KI-Tipps machen die Partie ungewertet (Server
// setzt hints_used bei /api/ai/hint, s. dortige Doku). Vor dem ERSTEN Klick
// in einer bislang gewerteten Partie (mind. ein Profil ausgewaehlt, noch
// nicht ungewertet) wird das per Bestaetigungsdialog transparent gemacht --
// bricht der Nutzer ab, wird kein Tipp abgerufen und nichts markiert.
function _confirmHintWillUnrate() {
  const hasProfile = !!(RATING_INFO.p0 || RATING_INFO.p1);
  if (!hasProfile || RATING_INFO.unrated) return true;  // nichts zu gewinnen/verlieren
  return confirm('Tipp nutzen? Die Partie wird dadurch ungewertet.');
}

async function requestHint() {
  if (!teacherHintEligible()) return;
  if (!_confirmHintWillUnrate()) return;
  const btn = document.getElementById('teacher-hint-btn');
  if (btn) btn.disabled = true;
  try {
    const d = await api('/ai/hint');
    if (!d.ok) { showError(d.error); return; }
    hintCandidates = d.candidates;
    // Server hat hints_used serverseitig gesetzt (bei Erfolg immer) --
    // Client spiegelt das sofort fuers dauerhafte "ungewertet"-Badge, ohne
    // auf render() aus einem spaeteren API-Call zu warten.
    if (RATING_INFO.p0 || RATING_INFO.p1) {
      RATING_INFO.unrated = true;
      render();
    }
    renderHintHighlights();
  } finally {
    if (btn) btn.disabled = false;
  }
}

function clearHintHighlights() {
  hintCandidates = null;
  document.querySelectorAll('.hint-mark').forEach(el => {
    el.classList.remove('hint-mark', 'hint-1', 'hint-2', 'hint-3', 'hint-4', 'hint-5');
    delete el.dataset.hintBestRank;
  });
  document.querySelectorAll('.hint-badge').forEach(el => el.remove());
  const panel = document.getElementById('teacher-hint-panel');
  if (panel) panel.remove();
}

// Markiert die Top-Kandidaten aus `hintCandidates` auf dem Brett (Quell-Fabrik/
// Kuppelplatte + Zielreihe/-slot des MENSCHLICHEN Spielers). Wird nach jedem
// render() erneut aufgerufen (die Boards werden per innerHTML neu gebaut,
// alte Marker-Klassen gehen dabei verloren).
function renderHintHighlights() {
  document.querySelectorAll('.hint-mark').forEach(el => {
    el.classList.remove('hint-mark', 'hint-1', 'hint-2', 'hint-3', 'hint-4', 'hint-5');
    delete el.dataset.hintBestRank;
  });
  document.querySelectorAll('.hint-badge').forEach(el => el.remove());
  if (!hintCandidates || !S) return;
  const humanPi = AI_ENABLED ? (1 - AI_PLAYER) : S.current_player;

  // Mehrere Kandidaten können auf dasselbe Element zeigen (z.B. mehrere
  // Farben derselben Zielreihe) -- pro Element gewinnt NUR der beste
  // (niedrigste rank-Zahl) Marker/Badge, statt Klassen/Badges zu stapeln.
  const mark = (el, cand) => {
    if (!el) return;
    const prevRank = el.dataset.hintBestRank ? parseInt(el.dataset.hintBestRank, 10) : null;
    if (prevRank !== null && prevRank <= cand.rank) return;
    if (prevRank !== null) el.classList.remove(`hint-${prevRank}`);
    const oldBadge = el.querySelector('.hint-badge');
    if (oldBadge) oldBadge.remove();
    el.dataset.hintBestRank = String(cand.rank);
    el.classList.add('hint-mark', `hint-${cand.rank}`);
    if (TEACHER_LEVEL >= 2 && cand.win_pct != null) {
      const badge = document.createElement('div');
      badge.className = `hint-badge hint-${cand.rank}`;
      badge.textContent = `#${cand.rank} ${cand.win_pct.toFixed(0)}%`;
      el.appendChild(badge);
    }
  };

  hintCandidates.forEach(cand => {
    const a = cand.action;
    if (!a) return;
    if (cand.type === 'stone') {
      // Nutzer-Feedback: nicht die ganze Fabrik-Karte hervorheben, sondern
      // GENAU die Farbgruppe (Fliesen + Stückzahl) der empfohlenen Farbe --
      // eindeutiger als "irgendwo in dieser Fabrik". Bei GF (factory_id=null)
      // ist die Farbe evtl. sowohl im Sonnen- als auch im Mondbereich der
      // Großfabrik vorhanden (Regeltext parst nur Farbe+Ziel, keine Sonne/
      // Mond-Unterscheidung) -- Fallback markiert dann die erste passende
      // Gruppe (Sonne zuerst), zusätzlich den globalen Mondbereich-Pool.
      let srcEl;
      if (a.factory_id !== null) {
        srcEl = document.querySelector(`#factories-list-area .fcard[data-fid="${a.factory_id}"] .cgroup[data-color="${a.color}"]`);
      } else {
        srcEl = document.querySelector(`#factories-list-area .fcard[data-fid="GF"] .cgroup[data-color="${a.color}"]`)
             || document.querySelector(`#auslage-area .cgroup[data-src="SMALL_FACTORY_MOON"][data-fid="ALL"][data-color="${a.color}"]`);
      }
      mark(srcEl, cand);
      mark(document.querySelector(`#board${humanPi} .prow[data-ri="${a.row}"]`), cand);
    } else if (cand.type === 'choose_dome_slot') {
      mark(document.querySelector(`.dgtile[data-tile-id="${a.tile_id}"]`), cand);
      mark(document.querySelector(`#board${humanPi} .dslot[data-row="${a.slot_row}"][data-col="${a.slot_col}"]`), cand);
    } else if (cand.type === 'choose_draw_stack_slot' || cand.type === 'dome_stack_peek') {
      mark(document.getElementById('stack-picker-btn'), cand);
    } else if (cand.type === 'bonus_chip') {
      mark(document.querySelector(`#factories-list-area [data-chip-fid="${a.factory_id}"]`), cand);
    }
  });

  renderHintPanel();
}

function _escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

// Kompaktes Klartext-Panel mit den Top-Kandidaten (Nutzer-Feedback: die
// Brett-Markierung allein ist nicht immer eindeutig deutbar) -- ergänzt die
// Brett-Highlights, ersetzt sie nicht. Rang 1 kräftig, Rang 3 dezent (per CSS
// .hint-1/.hint-2/.hint-3 -- dieselbe Rang-Farbskala wie die Brett-Marker).
function renderHintPanel() {
  let el = document.getElementById('teacher-hint-panel');
  if (!hintCandidates || !hintCandidates.length) {
    if (el) el.remove();
    return;
  }
  if (!el) {
    el = document.createElement('div');
    el.id = 'teacher-hint-panel';
    document.body.appendChild(el);
  }
  const rows = hintCandidates.map(c => {
    const winTxt = (TEACHER_LEVEL >= 2 && c.win_pct != null)
      ? `<span class="thp-win">${c.win_pct.toFixed(0)}%</span>` : '';
    return `<div class="thp-row">
      <span class="thp-rank hint-${c.rank}">${c.rank}</span>${_escapeHtml(mapFactoryNamesInText(stripTileIdsInText(c.description)))}${winTxt}
    </div>`;
  }).join('');
  el.innerHTML = `<div class="thp-title">💡 Top-${hintCandidates.length}</div>${rows}`;
}

// Coach-Feedback (Stufe 3): kurzer Toast nach jedem eigenen Zug.
function showTeacherFeedback(fb) {
  if (!fb) return;
  let el = document.getElementById('teacher-toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'teacher-toast';
    el.onclick = () => el.classList.remove('show');
    document.body.appendChild(el);
  }
  const isTop1 = fb.rang === 1;
  const head = isTop1 ? '✅ Bester Zug!' : `Rang ${fb.rang} · −${fb.delta_win_pp.toFixed(1)} Prozentpunkte`;
  const sub = isTop1
    ? 'Genau das hätte die KI auch gespielt.'
    : `Stärker gewesen wäre: ${mapFactoryNamesInText(stripTileIdsInText(fb.bester_zug_description))}`;
  el.innerHTML = `<div class="tt-head">${head}</div><div class="tt-sub">${sub}</div>`;
  el.classList.add('show');
  clearTimeout(window._teacherToastTimer);
  window._teacherToastTimer = setTimeout(() => el.classList.remove('show'), 6000);
}

async function stoneMove(source, factory_id, color, row, moon_order=[]) {
  if (AI_THINKING) return;
  if (AI_ENABLED && S.current_player === AI_PLAYER) return;
  const d = await api('/move/stone', {source, factory_id, color, row, moon_order});
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; clearHintHighlights(); render();
  showTeacherFeedback(d.teacher_feedback);
  if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
}

async function domeMove(tile_id, slot_row, slot_col, rotation) {
  const d = await api('/move/dome', {tile_id, slot_row, slot_col, rotation});
  if(!d.ok){showError(d.error);return;}
  S=d.state; closeDomeModal(); clearHintHighlights(); render();
  showTeacherFeedback(d.teacher_feedback);
  if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
}

async function startTileMove(player, tile_id, slot_row, slot_col, rotation) {
  const d = await api('/move/start_tile', {player, tile_id, slot_row, slot_col, rotation});
  if(!d.ok){showError(d.error);return;}
  S=d.state; closeDomeModal(); render();
  // Nachdem der Mensch gelegt hat: ist jetzt die KI mit ihrer Startkuppel dran?
  if (AI_ENABLED) {
    await aiDoStartTile();
  }
}

async function bonusChipMove(factory_id) {
  if (AI_THINKING) return;
  // Nur wenn Mensch dran ist
  if (AI_ENABLED && S.current_player === AI_PLAYER) return;
  const d = await api('/move/bonus_chip', {factory_id});
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; clearHintHighlights(); render();
  showTeacherFeedback(d.teacher_feedback);
	if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
}

async function tilingMove(player, pattern_row, slot_row, slot_col, space_index) {
  const d = await api('/tiling', {player, pattern_row, slot_row, slot_col, space_index});
  if(!d.ok){showError(d.error);return;}
  S=d.state; tilingRow=null; render();
  if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
}

async function endTiling() {
  const d = await api('/end_tiling', {});
  if(!d.ok){showError(d.error);return;}
  S=d.state; tilingPi=null; tilingRow=null; render();
  if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
}

async function finishHumanTiling() {
  if (!AI_ENABLED) {
    // Normales Rundenende, wenn zwei Menschen spielen
    endTiling();
  } else {
    // Mensch ist fertig, wir übergeben an die KI!
    humanTilingDone = true;
	endTiling();
  }
}

async function passMove() {
  if (AI_THINKING) return;
  if (AI_ENABLED && S.current_player === AI_PLAYER) return;
  const d = await api('/move/pass', {});
  if(!d.ok){showError(d.error);return;}
  S=d.state; sel=null; render();
	if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
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

// -- FABRIK-ANZEIGENAMEN ---------------------------------------------------------
// Nutzer-Anstoss: die 4 kleinen Fabriken + die grosse Fabrik bekommen in der
// Anzeige Stadtnamen statt F1..F4/GF. NUR Anzeige -- interne IDs, data-fid-
// Attribute, factory_id in API-Calls etc. bleiben unveraendert F1..F4/GF/null,
// diese Map betrifft ausschliesslich Text, den der Nutzer sieht.
const FACTORY_CITY = {1:'Wien', 2:'Triest', 3:'Athen', 4:'Paris'};
const GF_CITY = 'Frankfurt';

// Reiner Stadtname fuer direkt aus JS gebaute UI-Elemente (Fabrikkarten-Kopf,
// Gueltige-Zuege-Liste etc.) -- fid: Zahl/String 1-4, oder null/'GF' fuer die
// grosse Fabrik.
function factoryCityName(fid) {
  if (fid === null || fid === undefined || fid === 'GF') return GF_CITY;
  return FACTORY_CITY[Number(fid)] || `F${fid}`;
}

// Ergaenzt Server-Rohtext (Log-Zeilen, Lehrer-Kandidaten-Beschreibungen), der
// die engine-seitigen Kurzformen "F1".."F4"/"GF" enthaelt, um den Stadtnamen
// in Klammern -- z.B. "F1" -> "F1 (Wien)". Die F-Nummer bleibt sichtbar
// (Rueckwaertslesbarkeit alter Logs/Screenshots), der Stadtname wird nur
// ergaenzt. Die ROHEN Strings (S.log, mv.description) bleiben unveraendert,
// diese Funktion wird ausschliesslich beim Rendern auf eine Kopie angewendet.
function mapFactoryNamesInText(text) {
  if (!text) return text;
  return text
    .replace(/\bF([1-4])\b/g, (m, n) => `F${n} (${FACTORY_CITY[n]})`)
    .replace(/\bGF\b/g, `GF (${GF_CITY})`);
}

// Punkt 8 (Nutzer-Anstoss): Platten-IDs sind fuer den Spieler irrelevant (die
// Platte ist an ihrem Farbmuster erkennbar) -- server-seitige Lehrer-
// Beschreibungen wie "Kuppel #13 → (2,3)" (siehe server.py::_teacher_describe_move,
// Format durch _T_DOME_DISPLAY_DESC_RE vorgegeben) bekommen die Kachel-ID beim
// ANZEIGEN entfernt. NUR fuers Hint-Panel/Coach-Feedback -- NICHT fuers Log
// (dort bleiben IDs fuer Forensik/Replays, siehe mapFactoryNamesInText-Aufruf
// beim Log-Rendering, der diese Funktion bewusst NICHT mit aufruft). Die rohe
// `description` (fuer server-seitiges Move-Matching) bleibt unveraendert.
function stripTileIdsInText(text) {
  if (!text) return text;
  return text.replace(/Kuppel #\d+/g, 'Kuppel');
}

// -- COLORS --------------------------------------------------------------------
const COLOR_LABELS = {blau:'B',gelb:'G',rot:'R',schwarz:'S',tuerkis:'T','türkis':'T',bunt:'★',special:'◎'};

function tileDiv(color, extra='', size='') {
  const nc=normColor(color);
  return `<div class="tile ${nc} ${size} ${extra}">${COLOR_LABELS[color]||''}</div>`;
}

// Farbenblinden-Symbole (Nutzer 2026-08-07): jede Fliesenfarbe traegt
// ueberall ein weisses Form-Symbol -- Rot ✦, Blau ✢, Schwarz ▣,
// Tuerkis ◈, Gelb ❂. Fuer .tile-Elemente rendert das CSS (::after auf
// der Farbklasse, style.css), fuer Kuppelfelder setzt spaceHTML das
// Symbol als Label.
const TILE_SYMBOL = {rot:'✦', blau:'✢', schwarz:'▣', tuerkis:'◈', gelb:'❂'};

function normColor(c) {
  if (!c) return '';
  const low = c.toLowerCase();
  return low === 'türkis' ? 'tuerkis' : low;
}

// Wild-Rueckseiten-Icon. Historie: 🃏 -> 🤡 (beide bei 10-11px schlecht
// erkennbar). Nutzer-Feedback 2026-08-07: 🌀 als einheitliches Wild-Symbol --
// identisch auf Kuppel-Wildfeldern (.ds.W, s. spaceHTML) und den
// Rueckseiten im Stapel-Zieh-Dialog/Stapel-Button.
const WILD_BACK_ICON = '🌀';

// Rückseite der obersten Kuppelstapel-Platte -- an einem physischen Tisch
// für ALLE Spieler jederzeit sichtbar (Nutzer-Anstoss), nicht erst beim
// Ziehen. `S.dome_stack_top_type` kommt direkt vom Server (state.dome_tile_pool[0]),
// ist also fuer beide Spieler gleichermassen Teil des gemeinsamen Zustands.
function stackTopTypeIcon() {
  if (S.dome_stack_top_type === 'special') return '⭐';
  if (S.dome_stack_top_type === 'wild') return WILD_BACK_ICON;
  return '📦';
}
function stackTopTypeLabel() {
  if (S.dome_stack_top_type === 'special') return ' (⭐ Special oben)';
  if (S.dome_stack_top_type === 'wild') return ` (${WILD_BACK_ICON} Wild oben)`;
  return '';
}


function spaceHTML(sp, si=-1, pi=-1, sr=-1, sc=-1, tiling=false) {
  const color = sp.color || sp.req_color || sp.color_id || '';
  const nc = normColor(color);
  
  let bg='', cls='', lbl='', tdata='';
  
  if(sp.filled) {
    // Nutzer-Feedback 2026-08-07: gelegte Spezialfliese zeigt den gelben
    // Stern (wie die Spezial-Rueckseite im Stapel-Dialog), statt ohne Label.
    bg=''; cls=`ds filled ${normColor(sp.filled)}`;
    lbl = normColor(sp.filled) === 'special' ? '⭐' : '';
  } else if(sp.type === 'N' || !sp.type || sp.type === 'NORMAL') {
    const hexFull={blau:'#2563EB',gelb:'#D97706',rot:'#DC2626',schwarz:'#292524',tuerkis:'#0891B2'};
    const hex = hexFull[nc] || (nc ? '#FF00FF' : '#999');
    // Nutzer-Design (2026-08-06): unbelegte Farbfelder deutlich von belegten
    // unterscheiden -- helle Zelle mit gestricheltem Rahmen, die Sollfarbe
    // nur noch als VERKLEINERTE Kachel in der Mitte (CSS .ds.N zeichnet sie
    // aus --slot), statt vollflaechig halbtransparent.
    bg = `--slot:${hex};`;
    cls = 'ds N';
    lbl = TILE_SYMBOL[nc] || '?';
  } else if(sp.type === 'WILD') {
    // Nutzer-Feedback 2026-08-07: 🌀 statt ★ -- konsistent mit der
    // Wild-Rueckseite im Stapel-Dialog (WILD_BACK_ICON).
    bg = 'background:#EDE9FE;'; cls = 'ds W'; lbl = '🌀';
  } else {
    // Nutzer-Feedback 2026-08-07: gesperrtes Spezialfeld zeigt den gelben
    // Stern der Spezial-Rueckseite (⭐, s. stackTopTypeIcon) statt 🔒.
    bg = 'background:#E7E5E4;'; cls = `ds S${sp.locked?' locked':''}`; lbl = sp.locked ? '⭐' : '◎';
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

// -- RENDER BOARD -------------------------------------------------------------
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

// Nutzer-Feedback: verbrauchte Bonuschips sollen nicht aus der Uebersicht
// verschwinden, sondern als "umgedreht" (Ghost) sichtbar bleiben. Die
// Engine haelt in p.bonus_chips nur noch die AKTUELL gehaltenen Chips vor
// (verbrauchte werden entfernt) -- ohne Backend-Aenderung erkennen wir das
// rein clientseitig per Diff zum vorherigen Render: was frueher da war und
// jetzt fehlt, ist gerade verbraucht worden und wandert dauerhaft (bis zum
// naechsten Spielstart, siehe startNewGame) in _chipGhosts.
let _chipGhosts = {0: [], 1: []};
let _prevBonusChips = {0: null, 1: null};
function trackChipGhosts(pi, chips) {
  const prev = _prevBonusChips[pi];
  if (prev) {
    const stillHeld = new Set(chips.map(c => c.id));
    prev.filter(c => !stillHeld.has(c.id)).forEach(c => _chipGhosts[pi].push(c));
  }
  _prevBonusChips[pi] = chips;
}

// Nutzer-Feedback (2026-07-29, Bugfix + Folgeauftrag): EIN Ort, der die
// "aktuelle Tiling-Reihe" eines Spielers bestimmt -- von renderBoard() (Punkt
// + Kasten + Reihen-Markierung) UND renderCenter() (Skip-Button-Liste)
// genutzt, damit beide Stellen nie auseinanderlaufen koennen.
//
// Bugfix (Screenshot 1): der Bonuschips-Kasten leuchtete fuer "irgendeine"
// chippable Reihe des Spielers auf, unabhaengig davon, ob das ueberhaupt die
// AKTUELLE (von oben nach unten naechste) Reihe war -- und der blaue "aktuelle
// Reihe"-Punkt wurde NIE fuer eine nur-per-Chips-komplettierbare Reihe
// gesetzt, weil er ausschliesslich `S.valid_tiling_rows` (volle Reihen mit
// direkter Platzierung) auswertete. `chippable_tiling_rows` (serialize.rs)
// schliesst volle Reihen aus (`row.is_complete() -> continue`),
// `valid_tiling_rows` enthaelt nur volle Reihen (`get_pending_tiling_rows`) --
// die Ri-Mengen beider Listen sind also je Spieler disjunkt, daher reicht das
// Minimum ueber beide als korrekte "von oben nach unten"-Reihenfolge.
//
// Folgeauftrag (Screenshot 2): die Oben-nach-unten-Regel gilt laut Engine nur
// fuer die PLATZIERUNG voller Reihen (round_end.rs::validate_tiling_action
// blockiert nur auf frueheren VOLLEN+platzierbaren Reihen). Eine nur-per-Chips
// komplettierbare Reihe darf der Mensch bewusst ueberspringen (`skippedChipRows`),
// um eine spaetere chip-faehige Reihe zu bedienen -- `chippable_tiling_rows`
// listet ohnehin ALLE ab `tiled_max_row` in Frage kommenden Reihen, nicht nur
// die oberste (engine/src/round_end.rs::chippable_rows). Eine volle
// platzierbare Reihe bleibt NICHT ueberspringbar (die Engine erzwingt deren
// Reihenfolge zwingend, s.o.).
function getTilingRowState(pi) {
  const playerPlaceableRis = (S.valid_tiling_rows || [])
    .filter(vr => vr.pi === pi && vr.placeable === true)
    .map(vr => vr.ri);
  const playerChippableRis = (S.chippable_tiling_rows || [])
    .filter(cr => cr.pi === pi)
    .map(cr => cr.ri);
  // Stale uebersprungene Reihen bereinigen: faellt eine Reihe aus
  // chippable_tiling_rows heraus (weil inzwischen eine spaetere Reihe
  // platziert wurde, s. tiled_max_row), ist sie endgueltig raus -- der
  // Skip-Eintrag wird dann automatisch entfernt statt einen toten Zustand
  // vorzugaukeln.
  const skipSet = skippedChipRows[pi] || (skippedChipRows[pi] = new Set());
  for (const ri of [...skipSet]) {
    if (!playerChippableRis.includes(ri)) skipSet.delete(ri);
  }
  const activeChippableRis = playerChippableRis.filter(ri => !skipSet.has(ri));
  const combined = [...playerPlaceableRis, ...activeChippableRis];
  const currentTilingRi = combined.length ? Math.min(...combined) : null;
  const isChipOnly = currentTilingRi !== null && activeChippableRis.includes(currentTilingRi);
  return { playerPlaceableRis, playerChippableRis, activeChippableRis, currentTilingRi, isChipOnly, skipSet };
}

function renderBoard(pi) {
  const p = S.players[pi];
  const isActive = S.current_player===pi && S.phase==='drafting';
  const isTiling = S.phase==='tiling';
  // Nutzer-Feedback: einfach "genommen/Limit" zeigen -- Regel-Limit
  // BONUS_CHIPS_PER_ROUND=2 (engine/src/board.rs), Stand ueber state_json
  // p.chips_taken (= bonus_chips_used_this_round).
  const chipsTakenThisRound = p.chips_taken || 0;
  // Nutzer-Feedback (2026-07-27): kein Reihen-Button mehr fuer die
  // Bonusplaettchen-Nutzung -- statt dessen wird der Bonuschips-Bereich
  // selbst hervorgehoben/klickbar, sobald die AKTUELLE Reihe chip-vervoll-
  // staendigbar ist (Modal oeffnet sich fuer genau diese Reihe).
  const {
    playerPlaceableRis, playerChippableRis, activeChippableRis,
    currentTilingRi, isChipOnly: chipAreaClickable, skipSet,
  } = getTilingRowState(pi);
  // Nutzer-Feedback (2026-07-30): Skip-/Reset-Steuerung aus der zentralen
  // Info-Spalte (renderCenter) in die Spieler-Sidebar verschoben, direkt
  // unterhalb des Bonuschips-Kastens -- s. Markup weiter unten. Bedingungen
  // unveraendert (nur menschlicher Spieler, nur bei aktuell chip-only Reihe
  // bzw. nicht-leerem Skip-Set); da renderBoard(pi) je Spielerpanel separat
  // aufgerufen wird, landet der Button im Hotseat-Fall automatisch im
  // richtigen Spielerbereich.
  const showSkipControls = !AI_ENABLED || pi !== AI_PLAYER;

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
    // Reihe klickbar (direkte Platzierung) wenn sie voll, platzierbar UND die
    // aktuelle Reihe ist. `currentTilingRi` (oben in renderBoard berechnet)
    // beruecksichtigt bereits beide Wege ("von oben nach unten" ueber volle
    // UND chip-komplettierbare Reihen hinweg), keine separate earlier-Prüfung
    // hier mehr noetig.
    const isPlaceable = playerPlaceableRis.includes(ri);
    if(isTiling && tilingRow===null && row.tiles.length===row.capacity && ri===currentTilingRi && isPlaceable) cls='drop';
    else if(isTiling && tilingRow===null && row.tiles.length===row.capacity) cls='nodrop';
    const onclick = cls==='drop'
      ? `onclick="${isActive&&sel ? `onRowClick(${ri})` : `onTilingRowClick(${pi},${ri})`}"`
      : '';
    const phantomCount = row.phantom_count || 0;
    const cells = Array.from({length:row.capacity},(_,ci)=>{
      const emptyCount = row.capacity - row.tiles.length;
      if (ci < emptyCount) return `<div class="tile sm empty"></div>`;
      // Musterreihen füllen sich von rechts (an der Kuppel/Wand) nach links --
      // die zuerst gezogene Fliese liegt also ganz rechts, die zuletzt
      // hinzugefügte ganz links. Phantom-Fliesen (per Bonuschip ergänzt)
      // sitzen am Ende von `tiles` (zuletzt gepusht) und damit visuell GANZ
      // LINKS -- weiß mit farbigem Rand statt voll gefüllt. tileIdx zählt
      // daher von rechts nach links (ci=capacity-1 → tileIdx=0).
      const tileIdx = row.capacity - 1 - ci;
      const isPhantom = tileIdx >= row.tiles.length - phantomCount;
      return `<div class="tile sm ${normColor(row.color)}${isPhantom ? ' phantom' : ''}"></div>`;
    }).join('');
    // Naechste faellige Tiling-Reihe: `isNextTiling` bleibt fuer die
    // Chip-Ziel-Markierung unten noetig. Bugfix (2026-07-29): gilt auch, wenn
    // die einzige offene Aktion eine Chip-Komplettierung ist (Reihe also noch
    // nicht voll ist) -- vorher war `isNextTiling` durch
    // `row.tiles.length===row.capacity` fest an volle Reihen gekoppelt, eine
    // nur-per-Chips-komplettierbare Reihe wurde nie erkannt.
    //
    // Nutzer-Feedback (2026-08-02): der frueher hier gerenderte blaue Punkt
    // (visueller Zusatzindikator "diese Reihe ist dran") ist ERSATZLOS
    // entfernt -- er verursachte beim Erscheinen einen Layout-Sprung
    // (Musterreihen ruckten ein) und war ohnehin redundant zur bereits
    // vorhandenen blauen Reihen-Hervorhebung (.prow.drop Hintergrund, siehe
    // style.css) bzw. der gestrichelten Chip-Ziel-Markierung (.prow.chip-target).
    const isNextTiling = isTiling && ri === currentTilingRi;
    // Dezente Zusatzmarkierung: wenn die aktuelle Reihe nur per Bonuschips
    // komplettierbar ist, bekommt die Reihe selbst denselben Hinweis-Ton wie
    // der Bonuschips-Kasten (.chips-usable), damit der Bezug Kasten->Reihe
    // sichtbar ist (Nutzer-Anforderung 2026-07-29).
    const chipTargetCls = (isNextTiling && activeChippableRis.includes(ri)) ? ' chip-target' : '';
    return `<div class="prow ${cls}${chipTargetCls}" data-ri="${ri}" ${onclick}>
      <span class="rownum">${ri+1}</span>${cells}
      <span class="rowlabel" style="color:var(--text3)">→</span>
    </div>`;
  }).join('');

const domeHTML = p.dome_grid.map((row,sr)=>row.map((slot,sc)=>{
    // Prüfe: Gibt es einen aktiven Platzierungsprozess (Start, Display oder Stapel) für diesen Spieler?
    const isPending = pendingStackPlacement && pendingStackPlacement.pi === pi;
    
    // Hervorhebung (cando) nur, wenn eine Karte zum Legen bereit liegt.
    // In der Vorbereitungsphase bleibt isPending hier false, solange keine Karte gewählt ist.
    let cls = slot ? 'occ' : (isPending ? 'cando' : '');
    let ddata = isPending ? ` data-dome="${pi},${sr},${sc}"` : '';

    const isTilingTarget = isTiling && tilingPi===pi && tilingRow!==null;
    const inner = slot
      ? dome2x2(slot.spaces, pi, sr, sc, isTilingTarget)
      : `<div style="font-size:9px;color:var(--text3);text-align:center;width:100%">+</div>`;

    return `<div class="dslot ${cls}" data-row="${sr}" data-col="${sc}"${ddata}>${inner}</div>`;
}).join('')).join('');

  // Nutzer-Feedback 2026-08-07: die Farbenblinden-Symbole kollidierten mit
  // dem Straf-Label AUF der Fliese -- Labels wandern in eine eigene Zeile
  // UNTER die Slots. Der Startspielerstein fuegt sich homogen ein: statt
  // weisser Fliese das ❖-Symbol (wie an der grossen Fabrik), Label -2
  // ebenfalls in der Zeile darunter.
  const floorHTML = [...Array(4)].map((_,i)=>{
    const t = p.floor[i];
    const label = [-1,-2,-3,-4][i];
    return `<div style="display:flex;flex-direction:column;align-items:center;gap:1px">
      <div class="fslot">${t?`<div class="tile sm ${normColor(t)}"></div>`:''}</div>
      <span style="font-size:8px;font-weight:700;color:var(--text3);line-height:1">${label}</span>
    </div>`;
  }).join('');
  const markerHTML = `<div style="display:flex;flex-direction:column;align-items:center;gap:1px">
    <div class="fslot ${p.marker ? 'marker-taken' : 'marker-empty'}" title="Startspielerstein">❖</div>
    <span style="font-size:8px;font-weight:700;color:var(--text3);line-height:1">-2</span>
  </div>`;

  const est = p.estimated_score || 0;
  const estStr = (est >= 0 ? '+' : '') + est;
  const estColor = est > 0 ? '#059669' : est < 0 ? '#DC2626' : 'var(--text3)';

  document.getElementById(`board${pi}`).className = `panel${isActive?' active':''}`;
  document.getElementById(`board${pi}`).innerHTML = `
    <div class="phead">
      <span class="pname">${isActive?'▶ ':''}${p.name}${_ratingBadgeHTML(pi)}${p.start_placed?'':' ⚠ Erste Kuppelplatte legen!'}</span>
      <span style="display:flex;align-items:baseline;gap:5px">
        <span class="pscore">${p.score}</span>
        <span style="font-size:11px;color:${estColor}" title="Geschätzte Punkte diese Runde">(${estStr})</span>
      </span>
    </div>
    ${tokHTML}
    <div class="sep"></div>
    <div class="board-inner">
      <div>
        <div class="lbl">Zerbrochene Fliesen</div>
        <div class="floor">${markerHTML}${floorHTML}
          ${sel&&isActive?`<button class="btn danger" style="padding:2px 8px;font-size:10px" onclick="onFloorDirect()">→ Boden</button>`:''}
        </div>

        ${(() => { trackChipGhosts(pi, p.bonus_chips || []); return ''; })()}
        <div class="${chipAreaClickable ? 'chips-usable' : ''}"
             style="margin-top:6px;font-size:9px;color:var(--text3);padding:4px;border-radius:6px;
                    ${chipAreaClickable ? 'cursor:pointer' : ''}"
             ${chipAreaClickable ? `onclick="openChipModal(${pi},${currentTilingRi})" title="Bonusplättchen einsetzen"` : ''}>
          Bonuschips (${chipsTakenThisRound}/2):
          <div class="chips-grid">
            ${(() => {
              const slots = [
                ..._chipGhosts[pi].map(c => ({...c, ghost: true})),
                ...(p.bonus_chips || []).map(c => ({...c, ghost: false})),
              ];
              return Array.from({length: 10}, (_, i) => {
                const c = slots[i];
                if (c && c.colors && c.colors.length > 0) {
                  if (c.ghost) {
                    return `<div class="bchip ghost" title="${c.colors.join('+')} (verbraucht)"></div>`;
                  }
                  const c1 = normColor(c.colors[0]);
                  const c2 = c.colors.length > 1 ? normColor(c.colors[1]) : 'empty';
                  return `<div class="bchip" title="${c.colors.join('+')}">
                    <div class="bchip-half ${c1}"></div>
                    <div class="bchip-half ${c2}"></div>
                  </div>`;
                } else {
                  return `<div class="bchip placeholder"></div>`;
                }
              }).join('');
            })()}
          </div>
        </div>
        ${(() => {
          // Nutzer-Feedback (2026-07-30): direkt unter dem Bonuschips-Kasten,
          // kompakter als die frueheren Center-Pills, aber weiterhin klar als
          // Aktion erkennbar (Button-Look statt reinem Text-Link). Gleiche
          // Anzeige-Bedingungen wie zuvor in renderCenter: nur menschlicher
          // Spieler, Skip-Button nur bei aktuell chip-only Reihe, Reset-Link
          // nur bei nicht-leerem Skip-Set (bereits stale-bereinigt durch
          // getTilingRowState()).
          if (!showSkipControls) return '';
          const parts = [];
          if (chipAreaClickable) {
            const rowLabel = `Reihe ${currentTilingRi+1}`;
            parts.push(`<button class="btn" style="font-size:9px;padding:2px 5px;width:100%;text-align:left"
              onclick="skipChipRow(${pi},${currentTilingRi})"
              title="${rowLabel} bleibt vorerst liegen -- die Chip-Option verfällt endgültig, sobald danach eine SPÄTERE Reihe platziert wird.">
              ⏭ ${rowLabel} für Bonuschips ignorieren
            </button>`);
          }
          if (skipSet.size > 0) {
            parts.push(`<span style="cursor:pointer;color:var(--text3);text-decoration:underline;font-size:9px" onclick="resetSkippedChipRows(${pi})">↺ übersprungene Reihen zurücksetzen</span>`);
          }
          return parts.length
            ? `<div style="display:flex;flex-direction:column;align-items:flex-start;gap:3px;margin-top:4px">${parts.join('')}</div>`
            : '';
        })()}
      </div>
      <div>
        <div id="plines${pi}">${plHTML}</div>
      </div>
      <div>
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

// -- LOG EINKLAPPBAR ------------------------------------------------------------
function applyLogCollapsed(collapsed) {
  const logEl = document.getElementById('log');
  const arrowEl = document.getElementById('log-toggle-arrow');
  if (!logEl || !arrowEl) return;
  logEl.style.display = collapsed ? 'none' : '';
  arrowEl.textContent = collapsed ? '▸' : '▾';
}
function toggleLogCollapsed() {
  const collapsed = document.getElementById('log').style.display !== 'none';
  localStorage.setItem('mosaic-log-collapsed', collapsed ? '1' : '0');
  applyLogCollapsed(collapsed);
}
applyLogCollapsed(localStorage.getItem('mosaic-log-collapsed') !== '0');

// -- GÜLTIGE ZÜGE EINKLAPPBAR (Nutzer-Auftrag 2026-07-29) -----------------------
// Exakt dasselbe Muster wie das Log oben: eine Toggle-Funktion setzt
// display+Pfeil, render()/renderCenter() fasst das beim Neu-Aufbau der
// Zug-Liste NICHT an -- der Auf/Zu-Zustand ueberlebt also State-Updates
// waehrend der Session unveraendert (wie beim Log). Einziger Unterschied zum
// Log (Nutzer-Vorgabe: Persistenz nicht noetig): kein localStorage, reine
// In-Memory-Variable -- Default nach jedem Seitenaufruf daher immer
// eingeklappt (deckt sich mit dem Log-Default beim ALLERERSTEN Besuch ohne
// gespeicherten Wert, s.o. `!== '0'`-Fallback).
let validMovesCollapsed = true;
function applyValidMovesCollapsed(collapsed) {
  const vmEl = document.getElementById('valid-moves');
  const arrowEl = document.getElementById('valid-moves-toggle-arrow');
  if (!vmEl || !arrowEl) return;
  vmEl.style.display = collapsed ? 'none' : '';
  arrowEl.textContent = collapsed ? '▸' : '▾';
}
function toggleValidMovesCollapsed() {
  validMovesCollapsed = !validMovesCollapsed;
  applyValidMovesCollapsed(validMovesCollapsed);
}
applyValidMovesCollapsed(validMovesCollapsed);

// -- RENDER CENTER -------------------------------------------------------------
function renderCenter() {
  const badge = document.getElementById('phase-badge');
  badge.className = 'phase-badge'+(S.phase==='tiling'?' tiling':S.phase==='end'?' end':'');
  // Seed anzeigen (klickbar zum Kopieren)
  const seedEl = document.getElementById('game-seed-display');
  if (seedEl && window._gameSeed !== undefined) {
    seedEl.textContent = `🎲 Seed: ${window._gameSeed} (klicken zum Kopieren)`;
    seedEl.style.display = '';
    seedEl.style.cursor = 'pointer';
    seedEl.title = 'Seed in Zwischenablage kopieren';
    seedEl.onclick = () => {
      navigator.clipboard?.writeText(String(window._gameSeed));
      seedEl.textContent = `🎲 Seed: ${window._gameSeed} ✓ kopiert`;
      setTimeout(() => { seedEl.textContent = `🎲 Seed: ${window._gameSeed} (klicken zum Kopieren)`; }, 1500);
    };
  }
  // Spielende loggen
  if ((S.phase === 'end' || S.phase === 'final') && !window._gameEndLogged) {
    window._gameEndLogged = true;
    _notifyGameEnd();
  }
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
    // pending: nur Reihen die tatsächlich platzierbar sind (placeable !== false)
    // und keine frühere platzierbare Reihe noch offen haben
    const placeableOnly = placeableRows.filter(pr => pr.placeable === true);
    const pending = placeableOnly
      .filter(pr => !AI_ENABLED || pr.pi !== AI_PLAYER)
      .filter(pr => {
        // Keine frühere platzierbare Reihe desselben Spielers noch offen
        return !placeableOnly.some(other => other.pi===pr.pi && other.ri<pr.ri);
      })
      .map(pr => {
        const p = S.players[pr.pi];
        const row = p.pattern_lines[pr.ri];
        return {pi: pr.pi, ri: pr.ri, color: row.color, pname: p.name};
      });

    // Unplatzierbare volle Reihen (alle 3 Slots belegt, keine Farbe passend)
    const unplaceable = placeableRows
      .filter(pr => pr.placeable === false)
      .map(pr => {
        const p = S.players[pr.pi];
        const row = p.pattern_lines[pr.ri];
        return {pi: pr.pi, ri: pr.ri, color: row.color, pname: p.name};
      });

    const hasPending = pending.length > 0;

    // Nur Reihen die der Server als chippable markiert hat
    const chippableRows2 = S.chippable_tiling_rows || [];
    const chippable = chippableRows2
      .filter(cr => !AI_ENABLED || cr.pi !== AI_PLAYER)
        .map(cr => {
        const p = S.players[cr.pi];
        const row = p.pattern_lines[cr.ri];
        return {pi: cr.pi, ri: cr.ri, color: row.color,
                need: row.capacity - row.tiles.length, pname: p.name};
      });

    // Nutzer-Feedback (2026-07-30): Skip-/Reset-Steuerung fuer chip-only
    // Reihen lebt jetzt in renderBoard() direkt unter dem Bonuschips-Kasten
    // der Spieler-Sidebar (nicht mehr hier in der zentralen Info-Spalte).

    let infoHTML = '';
    if(tilingRow!==null) {
      const col = S.players[tilingPi].pattern_lines[tilingRow].color;
      infoHTML = `<div class="info tiling" style="display:flex;align-items:center;justify-content:space-between">
        <span>→ <strong>${S.players[tilingPi].name}</strong> Reihe ${tilingRow+1}
          <span class="tile sm ${normColor(col)}" style="vertical-align:middle;margin:0 2px"></span>
          — passendes Kuppelfeld anklicken
        </span>
        <button class="btn" onclick="tilingPi=null;tilingRow=null;render()" style="font-size:10px;flex-shrink:0">✕</button>
      </div>`;
    } else if(hasPending) {
      const rows = pending.map(x=>
        `<span style="cursor:pointer;display:inline-flex;align-items:center;gap:2px;padding:1px 4px;border-radius:4px;background:#D1FAE5;border:1px solid #34D399"
          onclick="tilingPi=${x.pi};tilingRow=${x.ri};render()">
          <span class="tile sm ${normColor(x.color)}"></span>
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

    const btnText = AI_ENABLED ? "Mein Tiling abschließen → KI ist dran" : `Runde ${S.round} beenden ✓`;
    info.innerHTML = infoHTML + (!hasPending ? `
      <button class="btn pri" onclick="finishHumanTiling()" style="width:100%;margin-top:6px">
        ${btnText}
      </button>` : '');
  } else if(S.phase==='end' || S.phase==='final') {
    const [p0,p1]=S.players;
    // Bei Punktegleichstand gewinnt, wer die Startspielerfliese haelt --
    // `p.marker` taugt hier NICHT (wird bei JEDER Rundenwertung geloescht,
    // siehe game.rs::determine_winner-Kommentar), daher `first_player_next_round`
    // (ueberlebt die Wertung) statt der Marker-Flags.
    const w=p0.score>p1.score?p0.name:p1.score>p0.score?p1.name:(S.first_player_next_round===0?p0.name:S.first_player_next_round===1?p1.name:'Unentschieden');
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
        <span style="font-size:10px;color:var(--text2)">Eine Kuppelplatte unten anklicken, Rotation wählen, dann ein violett markiertes Kuppelfeld anklicken.</span>
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
    // Nutzer-Anstoss (Punkt 8): die technische Platten-ID ist fuer den
    // Spieler irrelevant (die Platte ist an ihrem Farbmuster erkennbar) --
    // weder Tooltip noch Label zeigen sie mehr. `data-tile-id` bleibt (interne
    // Zuordnung fuer den Klick-Handler, kein sichtbarer Text).
    return `<div class="dgtile" data-tile-id="${t.id}" title="Kuppelplatte – anklicken zum Legen" onclick="openDisplayPicker(${t.id})" style="cursor:pointer">
      <div class="d2x2" style="width:46px; height:46px;">${spaces}</div>
    </div>`;
  }).join('');

  const facsHTML = S.factories.map(f=>{
    const sunColors = [...new Set(f.sun)];
    const moonTops  = [...new Set(f.moon.map(s=>s[s.length-1]).filter(Boolean))];
    
    // Nutzer-Feedback 2026-08-07: verdeckter Bonuschip (Schloss) in
    // Bonuschip-Groesse (.icon-chip ~ .bchip 20px) statt winzig.
    let chipContent = '<span class="icon-chip">🔒</span>';
    if (f.chip_revealed && f.bonus_chip && f.bonus_chip.colors) {
      const c1 = normColor(f.bonus_chip.colors[0]);
      const c2 = f.bonus_chip.colors.length > 1 ? normColor(f.bonus_chip.colors[1]) : 'empty';
      
      chipContent = `<div class="bchip" style="cursor: pointer;">
        <div class="bchip-half ${c1}"></div>
        <div class="bchip-half ${c2}"></div>
      </div>`;
    }
    
    const chipHTML = f.bonus_chip
      ? `<span data-chip-fid="${f.id}" style="cursor:${f.chip_revealed?'pointer':'default'}" onclick="${f.chip_revealed?`bonusChipMove(${f.id})`:''}" title="Bonusplättchen">${chipContent}</span>`
      : '';
      
    const sunTiles = sunColors.map(c=>{
      const cnt = f.sun.filter(x=>x===c).length;
      return `<div class="cgroup" data-src="SMALL_FACTORY_SUN" data-fid="${f.id}" data-color="${c}">
        <div class="tile ${normColor(c)} click ${sel?.color===c&&sel?.factory_id===f.id?'sel':''}"></div>
        <span class="cnt">×${cnt}</span>
      </div>`;
    }).join('');
    
    // Task (Nutzer-Feedback): ALLE Fliesen jedes Mond-Stapels in korrekter
    // Reihenfolge zeigen (nicht nur die oberste) -- state_json liefert je
    // Fabrik eine Liste von Stapeln, jeweils Index 0 = unten ... letzter =
    // oben/sichtbar (siehe engine/src/factory.rs::place_on_moon/take_from_moon).
    // Darstellung: pro Stapel eine leicht ueberlappende Mini-Kachel-Kolonne,
    // unterste Fliese zuerst, oberste (ziehbare) zuletzt/oben + hervorgehoben.
    const nonEmptyStacks = f.moon.filter(stack => stack && stack.length);
    const moonTiles = nonEmptyStacks.length
      ? `<div class="moon-area" style="display:flex;gap:6px;align-items:flex-start;flex-wrap:wrap">
          <span style="font-size:8px;color:var(--text3)">Stapel:</span>
          ${nonEmptyStacks.map(stack => {
            const topDown = [...stack].reverse(); // topDown[0] = oben/ziehbar ... letzter = unten
            return `<div style="display:flex;flex-direction:column" title="Stapel (oben→unten): ${topDown.join(' → ')}">
              ${topDown.map((c,i)=>`<div class="tile sm ${normColor(c)}" style="margin-top:${i===0?'0':'-9px'};z-index:${topDown.length-i};${i===0?'outline:1.5px solid var(--text)':'opacity:.85'}"></div>`).join('')}
            </div>`;
          }).join('')}
         </div>` : '';
    // Nutzer-Feedback 2026-08-07: 🏭 neben dem Stadtnamen (Bonuschip-Groesse).
    return `<div class="fcard" data-fid="${f.id}">
      <div class="fhead"><span style="display:inline-flex;align-items:center;gap:4px"><span class="icon-chip">🏗️</span>${factoryCityName(f.id)}</span>${chipHTML}</div>
      <div class="ftiles sun-area">${f.sun.length?sunTiles:(nonEmptyStacks.length?'':'<span style="font-size:9px;color:var(--text3)">leer</span>')}</div>
      ${moonTiles}
    </div>`;
  }).join('');

  const lf = S.large_factory;
  const lSun = [...new Set(lf.sun)].map(c=>{
    const cnt=lf.sun.filter(x=>x===c).length;
    return `<div class="cgroup" data-src="LARGE_FACTORY_SUN" data-fid="null" data-color="${c}">
      <div class="tile ${normColor(c)} click ${sel?.source==='LARGE_FACTORY_SUN'&&sel?.color===c?'sel':''}"></div><span class="cnt">×${cnt}</span>
    </div>`;
  }).join('');
  const lMoon = [...new Set(lf.moon)].map(c=>{
    const cnt=lf.moon.filter(x=>x===c).length;
    return `<div class="cgroup" data-src="LARGE_FACTORY_MOON" data-fid="null" data-color="${c}">
      <div class="tile ${normColor(c)} click ${sel?.source==='LARGE_FACTORY_MOON'&&sel?.color===c?'sel':''}"></div><span class="cnt">×${cnt}</span>
    </div>`;
  }).join('');

  const moonTopCounts = S.moon_top_counts || {};
  const moonTopEntries = Object.entries(moonTopCounts);
  
  const moonActionHTML = moonTopEntries.length
    ? `<div style="margin-bottom:6px">
        <div class="lbl">Geteilte Mondfliesen</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap">
          ${moonTopEntries.map(([c, count]) => `
            <div class="cgroup" data-src="SMALL_FACTORY_MOON" data-fid="ALL" data-color="${c}"
              title="${count} oberste ${c}-Fliesen vom Moon aller Manufakturen">
              <div class="tile ${normColor(c)} click ${sel?.source==='SMALL_FACTORY_MOON'&&sel?.color===c?'sel':''}"></div>
              <span class="cnt">×${count}</span>
            </div>`).join('')}
        </div>
       </div>` : '';

  const towerTotal = (S.tower_colors || []).reduce((a,b)=>a+b, 0);

document.getElementById('auslage-area').innerHTML = `
    <div style="display:flex;justify-content:space-between;margin-bottom:5px">
      <span style="font-size:15px;font-weight:600">🎒 ${S.bag_count} · 🗼 ${towerTotal}</span>
      <span></span>
    </div>
    <div class="lbl">Auslage (${S.dome_display.length}/3)</div>
    <div class="display-g">${displayHTML || '<span style="font-size:9px;color:var(--text3)">leer</span>'}</div>
    ${(() => {
      const cp = S.players[S.current_player];
      const canStack = S.phase==='drafting'
        && cp.start_placed
        && cp.can_place_dome
        && S.dome_stack_count > 0;
      if (!canStack) return '';
      return `<div class="lbl" style="color:var(--text3);margin-bottom:2px">Stapel: ${S.dome_stack_count}</div>
      <button id="stack-picker-btn" class="btn" onclick="openStackPicker()" style="width:100%;margin-bottom:6px;font-size:11px">
        ${stackTopTypeIcon()} Ziehen (−1 Pkt/Karte)
      </button>`;
    })()}
    `;

  // Nutzer-Anstoss (Layout): "Geteilte Mondfliesen" liegt jetzt direkt ueber
  // der Fabrikliste im linken Fabriken-Panel statt im mittleren Auslage-Panel
  // -- inhaltlich/funktional unveraendert (gleiche moonTopEntries-Logik).
  document.getElementById('moon-shared-area').innerHTML = moonActionHTML;

  document.getElementById('factories-list-area').innerHTML = `
    <div class="lbl" style="${!S.players.every(p=>p.start_placed)?'opacity:.35;pointer-events:none':''}">Fabriken</div>
    <div style="${!S.players.every(p=>p.start_placed)?'opacity:.35;pointer-events:none':''}">
    ${facsHTML}
    <!-- Nutzer-Feedback 2026-08-07: .gf = eigener Hintergrund (Musterreihen-
         Flaechenfarbe); 🏭 neben dem Namen (kleine: 🏗️); Startspielerstein als ❖ (Nutzer 2026-08-07)
         (konsistent mit dem Log) in Bonuschip-Groesse statt kleinem ★;
         "leer" nur, wenn Sonne UND Moon-Pool leer sind. -->
    <div class="fcard gf" data-fid="GF">
      <div class="fhead"><span style="display:inline-flex;align-items:center;gap:4px"><span class="icon-chip">🏭</span>${factoryCityName(null)}</span>${lf.marker?'<span class="icon-chip" title="Startspielerstein" style="color:#F59E0B">❖</span>':''}</div>
      <div class="ftiles sun-area" style="margin-bottom:2px">${lSun || (lMoon ? '' : '<span style="font-size:9px;color:var(--text3)">leer</span>')}</div>
      ${lMoon ? `<div class="ftiles moon-area"><span style="font-size:8px;color:var(--text3)">Pool:</span>${lMoon}</div>` : ''}
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
    } else if(e.includes('❖') || e.includes('🏁')){
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
    return `<div class="le" style="${style}">${mapFactoryNamesInText(e)}</div>`;
  }).join('');
  
const sdiv = document.getElementById('scoring-display');
  const editBtn = document.getElementById('scoring-edit-btn');
  // Wertungsplatten nur editierbar solange noch keine Startkacheln gelegt wurden
  // Nach Bestätigung (beide start_placed=true) nicht mehr änderbar
  const scoringConfirmed = S && S.scoring_confirmed;
  const canEditScoring = S && !scoringConfirmed && !S.players.every(p=>p.start_placed);
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
  // Nutzer-Auftrag (2026-07-29): eingeklappter Kopf zeigt die Anzahl, damit
  // man ohne Aufklappen sieht, dass es etwas zu tun gibt -- s.
  // applyValidMovesCollapsed()/toggleValidMovesCollapsed() oben (gleiches
  // Klapp-Muster wie das Log).
  const vmCountEl = document.getElementById('valid-moves-count');

  if(S.phase === 'tiling') {
    let rows = (S.valid_tiling_rows||[]);
    if (AI_ENABLED) {
        rows = rows.filter(x => x.pi !== AI_PLAYER);
    }
    if (vmCountEl) vmCountEl.textContent = rows.length ? `(${rows.length})` : '';

    if(rows.length === 0) {
      vmDiv.innerHTML = `<div class="le" style="color:var(--text3);font-style:italic">Alle regulären Reihen gelegt ✓ (Nutze Chips oder beende das Tiling)</div>`;
    } else {
      vmDiv.innerHTML = rows.map(x=>{
        const p = S.players[x.pi];
        const row = p.pattern_lines[x.ri];
        const nc = normColor(row.color);
        return `<div class="le" style="display:flex;align-items:center;gap:4px;padding:2px 0">
          <span style="color:var(--text3)">${p.name}</span>
          Reihe ${x.ri+1}
          <div class="tile sm ${nc}" style="flex-shrink:0"></div>
          <span style="color:var(--text3)">→ Kuppelreihe ${Math.floor(x.ri/2)}</span>
        </div>`;
      }).join('');
    }
    return;
  }

  if(!S.valid_moves || S.valid_moves.length === 0) {
    if (vmCountEl) vmCountEl.textContent = '';
    vmDiv.innerHTML = `<div class="le" style="color:var(--text3);font-style:italic">Keine Aktionen — Passen möglich</div>`;
    return;
  }
  if (vmCountEl) vmCountEl.textContent = `(${S.valid_moves.length})`;

  const byType = {};
  for(const m of S.valid_moves) {
    if(!byType[m.type]) byType[m.type] = [];
    byType[m.type].push(m);
  }

  const lines = [];

  if(byType['start_tile_pending']) {
    const sp = byType['start_tile_pending'][0];
    const who = (sp && sp.player != null && S.players[sp.player])
      ? S.players[sp.player].name + ': ' : '';
    lines.push(`<div class="le" style="color:#F59E0B;font-weight:600">⚠️ ${who}Startkachel legen (violett markierte Felder anklicken)</div>`);
  }

  if(byType['stone']) {
    // Nutzer-Feedback 2026-08-07: die grosse Fabrik ist spielerisch KEINE
    // eigene Zug-Kategorie -- die getrennten Frankfurt-Zeilen spiegelten nur
    // die Quellen-Enums der Engine. Sonne = Union aller Fabriken; Mond ist
    // ohnehin ein globaler Sammelzug (Aktion C).
    const sunColors = [...new Set(byType['stone']
      .filter(m=>m.source==='SMALL_FACTORY_SUN'||m.source==='LARGE_FACTORY_SUN')
      .map(m=>m.color))];
    const moonColors = [...new Set(byType['stone']
      .filter(m=>m.source==='SMALL_FACTORY_MOON'||m.source==='LARGE_FACTORY_MOON')
      .map(m=>m.color))];

    if(sunColors.length)
      lines.push(`<div class="le" style="display:flex;align-items:center;gap:3px;padding:2px 0">
        ☀️ Sonne:
        ${sunColors.map(c=>`<div class="tile sm ${normColor(c)}"></div>`).join('')}
      </div>`);
    if(moonColors.length)
      lines.push(`<div class="le" style="display:flex;align-items:center;gap:3px;padding:2px 0">
        🌙 Mond:
        ${moonColors.map(c=>`<div class="tile sm ${normColor(c)}"></div>`).join('')}
      </div>`);
  }

  if(byType['dome_display']) {
    lines.push(`<div class="le" style="padding:2px 0">🧩 Kuppelplatte aus Ablage legbar</div>`);
  }

  if(byType['dome_stack_peek']) {
    lines.push(`<div class="le" style="padding:2px 0">📦 Vom Stapel ziehen</div>`);
  }

  if(byType['dome_stack']) {
    lines.push(`<div class="le" style="padding:2px 0">📦 Kuppelplatte vom Stapel wählen</div>`);
  }

  if(byType['bonus_chip']) {
    const fnames = byType['bonus_chip'].map(m=>factoryCityName(m.factory_id)).join(', ');
    lines.push(`<div class="le" style="padding:2px 0">🎴 Bonusplättchen: ${fnames}</div>`);
  }

  vmDiv.innerHTML = lines.join('') || `<div class="le" style="color:var(--text3)">—</div>`;
}

// -- INTERACTION ---------------------------------------------------------------
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
  if (AI_THINKING) return;
  // Mensch darf nicht für KI tilen
  if (AI_ENABLED && pi === AI_PLAYER) return;
  const row = S.players[pi].pattern_lines[ri];
  if(row.tiles.length !== row.capacity) return;
  tilingPi=pi; tilingRow=ri;
  render();
}

// -- CHIP-REIHE UEBERSPRINGEN (Nutzer-Folgeauftrag 2026-07-29) -----------------
// Rein clientseitig -- die Engine erzwingt die "von oben nach unten"-Regel nur
// beim Platzieren VOLLER Reihen (round_end.rs::validate_tiling_action), nicht
// beim Chip-Komplettieren nicht-voller Reihen (round_end.rs::chippable_rows
// filtert nur `ri < tiled_max_row`, listet also ALLE ab dort in Frage
// kommenden Reihen). Ueberspringen heisst daher nur "diese Reihe fuer die
// UI-Vorauswahl ignorieren, bis zurueckgesetzt oder bis eine spaetere Reihe
// tatsaechlich platziert wird" -- kein Server-Aufruf noetig.
function skipChipRow(pi, ri) {
  if (AI_ENABLED && pi === AI_PLAYER) return;
  if (!skippedChipRows[pi]) skippedChipRows[pi] = new Set();
  skippedChipRows[pi].add(ri);
  render();
}

function resetSkippedChipRows(pi) {
  if (skippedChipRows[pi]) skippedChipRows[pi].clear();
  render();
}

// -- CHIP MODAL ----------------------------------------------------------------
let chipModal = null;

function openChipModal(pi, ri) {
  if (AI_THINKING) return;
  if (AI_ENABLED && pi === AI_PLAYER) return;
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
    // Nutzer-Feedback 2026-08-07: Farbe spricht fuer sich -- keine
    // Buchstaben-Kuerzel, keine Chip-ID.
    chip.colors.forEach(c=>{
      const s=document.createElement('div');
      s.className=`tile sm ${normColor(c)}`;
      div.appendChild(s);
    });
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
        ${cchips.map(c=>c.colors.map(col=>`<div class="tile sm ${normColor(col)}"></div>`).join('')).join('<span style="color:var(--text3)">+</span>')}
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
      ?`<div class="tile sm ${normColor(color)}"></div>`
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

// -- DOME MODAL ----------------------------------------------------------------

// Bestimmt den Spieler, der gerade legen/auswählen darf.
// In der Startplatzierungs-Phase (noch nicht beide gelegt) gilt die Engine-Regel:
// Nicht-Startspieler ZUERST, dann Startspieler. Sonst der normale current_player.
function activePlacingPlayer() {
  const first = S.current_player;          // Startspieler
  const nonStarter = 1 - first;
  if (!S.players[nonStarter].start_placed) return nonStarter;  // muss zuerst
  if (!S.players[first].start_placed)      return first;        // dann Startspieler
  return S.current_player;                  // beide gelegt → normaler Zug
}

function openDisplayPicker(tileId) {
  if (AI_THINKING) return;
  const pi = activePlacingPlayer();
  const p = S.players[pi];

  if(AI_ENABLED && pi === AI_PLAYER){ showError('Die KI ist am Zug.'); return; }
  // Normale Runde braucht can_place_dome; Startkuppel (noch nicht gelegt) nicht.
  if(p.start_placed && !p.can_place_dome){
    showError('Du kannst diese Runde keine Kuppelplatte mehr legen (max. 2 pro Runde, in Runde 5 keine, oder Raster voll).');
    return;
  }
  const hasEmpty = p.dome_grid.flat().some(s => !s);
  if(!hasEmpty){ showError('Keine freien Kuppelfelder!'); return; }

  // Modal ohne Slot öffnen, die angeklickte Display-Karte direkt vorwählen.
  openDomeModal(pi, -1, -1);
  // Vorauswahl setzen + im Pool markieren.
  domeModal.tile_id = tileId;
  const pool = document.getElementById('dome-pool');
  pool.querySelectorAll('.ptile').forEach(e=>{
    e.classList.toggle('sel', Number(e.dataset.id) === tileId);
  });
  document.getElementById('dome-confirm').disabled = false;
  buildPreview();
}

function openStackPicker() {
  if (AI_THINKING) return;
  const pi = S.current_player;
  const p = S.players[pi];

  // Klare Fehlermeldungen statt stillem Abbruch in openDomeModal.
  if(AI_ENABLED && pi === AI_PLAYER){ showError('Die KI ist am Zug.'); return; }
  if(!p.start_placed){ showError('Erst die Startkuppelplatte legen.'); return; }
  if(!p.can_place_dome){
    showError('Du kannst diese Runde keine Kuppelplatte mehr legen (max. 2 pro Runde, in Runde 5 keine, oder Raster voll).');
    return;
  }
  const hasEmpty = p.dome_grid.flat().some(s => !s);
  if(!hasEmpty){ showError('Keine freien Kuppelfelder!'); return; }
  if(!(S.dome_stack_count > 0)){ showError('Der Kuppelstapel ist leer.'); return; }

  // Slot wird NICHT vorab gewählt (-1,-1). Modal im reinen Stapel-Modus öffnen
  // (ohne Display-Auswahl) und den ersten (Pflicht-)Zug sofort ziehen -- laut
  // Regelwerk muss mind. 1x gezogen werden, sobald man sich fürs Ziehen
  // entschieden hat.
  openDomeModal(pi, -1, -1, /*stackOnly=*/true);
  setTimeout(()=>{ stackPeekMore(); }, 50);
}

function openDomeModal(pi, sr, sc, stackOnly=false) {
  if (AI_THINKING) return;  // KI denkt noch
  const p = S.players[pi];
  const isStart = !p.start_placed;
  // KI-Board sperren: Mensch darf nicht für KI legen
  if(AI_ENABLED && pi === AI_PLAYER) return;
  if(!isStart && pi !== S.current_player) return;
  if(!isStart && !p.can_place_dome) return;

  // Falls ein vorheriger Stapelzug noch auf einen Slot wartete, verwerfen:
  // ein bewusst geöffnetes Dome-Modal mit echtem Slot ersetzt ihn. (Beim
  // Stapelziehen-Start ist sr/sc = -1, da gibt es noch nichts zu verwerfen.)
  if(pendingStackPlacement && sr !== -1) {
    pendingStackPlacement = null;
  }

  domeModal = {pi, slot_r:sr, slot_c:sc, tile_id:null, rotation:0, is_start:isStart, stack_only:stackOnly};
  const notice = document.getElementById('dome-notice');
  if(isStart) {
    notice.textContent='Rotation für die Kuppelplatte wählen, dann ein violett markiertes Kuppelfeld anklicken.';
    notice.style.display='block';
  } else notice.style.display='none';

  document.getElementById('dome-title').textContent =
    isStart ? 'Erste Kuppelplatte legen'
    : stackOnly ? 'Kuppelplatte vom Stapel ziehen'
    : 'Kuppelplatte legen';

  const grid = document.getElementById('dome-pool');
  grid.innerHTML = '';
  // Im reinen Stapel-Modus KEINE Display-Auswahl zeigen — der Spieler hat sich
  // bewusst fürs Ziehen entschieden. Die gezogenen Karten füllt stackStopAndChoose ein.
  // Start UND normale Runde wählen aus dem Display.
  if(!stackOnly) {
    S.dome_display.forEach(t=>{
      const div = document.createElement('div');
      div.className='ptile'; div.dataset.id=t.id;
      // Punkt 8: keine Platten-ID mehr anzeigen (nur intern per data-id).
      div.innerHTML=`<div class="d2x2" style="width:46px; height:46px;">${t.spaces.map(sp=>spaceHTML(sp)).join('')}</div>`;
      div.addEventListener('click',()=>{
        domeModal.tile_id=t.id;
        grid.querySelectorAll('.ptile').forEach(e=>e.classList.remove('sel'));
        div.classList.add('sel');
        document.getElementById('dome-confirm').disabled=false;
        buildPreview();
      });
      grid.appendChild(div);
    });
  }

  document.getElementById('dome-confirm').disabled=true;
  document.getElementById('rotbtns').querySelectorAll('.rotbtn').forEach((b,i)=>b.classList.toggle('act',i===0));
  buildPreview();

  const stackSec = document.getElementById('dome-stack-section');
  const pendingN = (S.pending_stack_draw || []).length;
  if (!isStart && (S.dome_stack_count > 0 || pendingN > 0)) {
    stackSec.style.display = 'flex';
    if(pendingN > 0) {
      renderStackPeekState();
    } else {
      const statusEl = document.getElementById('stack-peek-status');
      if(statusEl) statusEl.textContent = '';
      const moreBtn = document.getElementById('stack-peek-more-btn');
      if(moreBtn) moreBtn.style.display = '';
      const stopBtn = document.getElementById('stack-stop-btn');
      if(stopBtn) stopBtn.disabled = true;
    }
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
  if (!tile && S.pending_stack_draw) {
    tile = S.pending_stack_draw.find(t => t.id === domeModal.tile_id);
  }
  
  if (!tile) { prev.innerHTML = ''; return; }
  
  const ROT = {0:[0,1,2,3], 90:[2,0,3,1], 180:[3,2,1,0], 270:[1,3,0,2]};
  const rotated = ROT[domeModal.rotation||0].map(i => tile.spaces[i]);
  
  prev.innerHTML = `<div class="d2x2 lg">${rotated.map(sp => spaceHTML(sp)).join('')}</div>`;
}

// Aktion A (Stapel-Variante), Schritt 1: eine weitere verdeckte Platte ziehen
// (−1 Pkt). Rückseite zeigt nur den TYP (Special/Wild), nicht die
// Farbanordnung -- die sieht man laut Regelwerk erst beim Aufhören
// (stackStopAndChoose). Beliebig oft wiederholbar, solange der Stapel reicht.
async function stackPeekMore() {
  if(!domeModal) return;
  const d = await api('/move/dome_stack_peek', {});
  if(!d.ok){ showError(d.error); return; }
  S = d.state;
  clearHintHighlights();
  showTeacherFeedback(d.teacher_feedback);
  renderStackPeekState();
}

function renderStackPeekState() {
  const pending = S.pending_stack_draw || [];
  const n = pending.length;
  // Alle bisher gezogenen Rückseiten zeigen, nicht nur die zuletzt gezogene
  // (Nutzer-Anstoss) -- Teil des gemeinsamen `S`-Zustands, also gleichermassen
  // für den Gegenspieler sichtbar, sobald der bzw. die Modal/Anzeige offen ist.
  const typeIcons = pending.map(t => t.bonus > 0 ? '⭐' : WILD_BACK_ICON).join(' ');
  const statusEl = document.getElementById('stack-peek-status');
  if(statusEl) {
    statusEl.innerHTML = `${n}. Platte gezogen. Rückseiten bisher: ${typeIcons} — bisher −${n} Pkt.<br>
      <span style="font-size:9px">Vorderseiten siehst du erst, wenn du aufhörst.</span>`;
  }
  const moreBtn = document.getElementById('stack-peek-more-btn');
  const stopBtn = document.getElementById('stack-stop-btn');
  // Weiterziehen ist beliebig oft moeglich, solange nur der Stapel reicht --
  // die fruehere Hausregel "max. so viele Platten wie Punkte vorhanden" wurde
  // per Nutzer-Entscheidung (Vollaudit 2026-07-21) aus dem Regelwerk entfernt,
  // siehe validate_draw_stack_peek in engine/src/game.rs: bei 0 Punkten ist
  // jede weitere Ziehung wirklich gratis (Score klemmt bei 0), nicht nur die
  // erste. Die GUI darf hier also NICHT zusaetzlich auf Punktestand pruefen.
  if(moreBtn) moreBtn.style.display = (S.dome_stack_count > 0) ? '' : 'none';
  if(stopBtn) stopBtn.disabled = n === 0;
  // Sobald mind. 1 Punkt bezahlt wurde, ist der Zug nicht mehr abbrechbar
  // (das Regelwerk kennt kein Zurück, sobald gezogen wurde).
  const cancelBtn = document.querySelector('#dome-overlay .cancel-btn');
  if(cancelBtn) cancelBtn.style.display = n > 0 ? 'none' : '';
}

// Aktion A, Schritt 2: aufhören -- alle bisher gezogenen Platten (bereits in
// S.pending_stack_draw enthalten) werden jetzt sichtbar, 1 wählen + Rotation,
// dann Ziel-Kuppelfeld anklicken (submitDomePlacement).
function stackStopAndChoose() {
  if(!domeModal) return;
  const n = (S.pending_stack_draw || []).length;
  if(n === 0) return;
  // Nutzer-Feedback 2026-08-07: in der Waehl-Phase gibt es kein Zurueck in
  // den freien Zugmodus mehr (Kosten bezahlt) -- Abbrechen-Button aus.
  const cbtn = document.querySelector('#dome-overlay .cancel-btn');
  if(cbtn) cbtn.style.display = 'none';
  domeModal.slot_r = -1;
  domeModal.slot_c = -1;

  const stackSec = document.getElementById('dome-stack-section');
  if(stackSec) stackSec.style.display = 'none';

  const notice = document.getElementById('dome-notice');
  notice.innerHTML = `<strong>Gezogene Platten:</strong> Such dir 1 Platte aus, dann Rotation wählen. Der Rest kommt unter den Stapel. (Kosten bereits bezahlt: −${n} Pkt)<br>
                      <span style="font-size:10px; font-weight:normal;">Nach dem Bestätigen klickst du das Ziel-Kuppelfeld auf deinem Board an.</span>`;
  notice.style.display = 'block';

  const pool = document.getElementById('dome-pool');
  pool.innerHTML = '';

  (S.pending_stack_draw || []).forEach(t => {
    const div = document.createElement('div');
    div.className = 'ptile';
    div.dataset.id = t.id;

    // Punkt 8: keine Platten-ID mehr anzeigen (nur intern per data-id).
    div.innerHTML = `
      <div class="d2x2" style="width:46px; height:46px;">${t.spaces.map(sp=>spaceHTML(sp)).join('')}</div>`;

    div.addEventListener('click', () => {
      domeModal.tile_id = t.id;
      domeModal.stack_draw = {chosen_id: t.id};

      pool.querySelectorAll('.ptile').forEach(e => e.classList.remove('sel'));
      div.classList.add('sel');
      buildPreview();

      // Regelwerk-Zitat: die NICHT gewählten Platten legst du "in beliebiger
      // Reihenfolge zurück unter den Stapel" -- bei 2+ Restplatten ist das
      // eine echte Wahl, bei ≤1 gibt es nur eine mögliche (leere/einwertige)
      // Reihenfolge, kein extra Schritt nötig.
      const rest = (S.pending_stack_draw || []).filter(x => x.id !== t.id);
      if(rest.length >= 2) {
        openReturnOrderPicker(rest);
      } else {
        domeModal.stack_draw.return_order = rest.map(x => x.id);
        document.getElementById('dome-confirm').disabled = false;
      }
    });

    pool.appendChild(div);
  });
}

// Zwischenschritt von stackStopAndChoose, nur bei 2+ Restplatten: Reihenfolge
// per Klick festlegen, zuerst geklickt = zuerst zurückgelegt = liegt näher
// an der Ziehseite (wird tendenziell früher wieder gezogen, siehe
// DrawFromStackMove-Kommentar im Rust-Code). `rest` wird auf domeModal
// gemerkt, damit renderReturnOrderPicker() (Reset-Link) neu zeichnen kann.
function openReturnOrderPicker(rest) {
  domeModal.stack_draw.return_order = [];
  domeModal.stack_draw.return_rest = rest;
  renderReturnOrderPicker();
}

// Analog zu renderMoonModal/resetMoonStack (Mondstapel-Reset-Link, gleiches
// Styling/Muster): zeichnet den Reihenfolge-Picker samt "↺ Zurücksetzen"-Link
// neu. Nur relevant bei ≥2 Restplatten (also >2 gezogenen Kuppelplatten
// insgesamt) -- bei ≤1 Restplatte wird openReturnOrderPicker gar nicht erst
// aufgerufen (siehe stackStopAndChoose).
function renderReturnOrderPicker() {
  document.getElementById('dome-confirm').disabled = true;
  const rest = domeModal.stack_draw.return_rest;
  const order = domeModal.stack_draw.return_order;

  const notice = document.getElementById('dome-notice');
  notice.innerHTML = `<strong>Reihenfolge der übrigen Platten:</strong> Klicke sie in der Reihenfolge an, in der sie zurück unter den Stapel gelegt werden sollen (zuerst geklickt = zuerst zurückgelegt).<br>
                      <span style="display:flex;align-items:center;justify-content:space-between;margin-top:2px">
                        <span id="return-order-status" style="font-size:10px; font-weight:normal;">${order.length}/${rest.length} platziert</span>
                        <span id="return-order-reset-btn" onclick="resetReturnOrder()" style="font-size:10px;color:var(--text2);cursor:pointer;text-decoration:underline;white-space:nowrap;margin-left:6px">↺ Zurücksetzen</span>
                      </span>`;
  notice.style.display = 'block';

  const pool = document.getElementById('dome-pool');
  pool.innerHTML = '';

  rest.forEach(t => {
    const div = document.createElement('div');
    const placedAt = order.indexOf(t.id);
    div.className = 'ptile' + (placedAt !== -1 ? ' sel' : '');
    div.dataset.id = t.id;
    // Punkt 8: keine Platten-ID mehr anzeigen -- der Order-Badge ("#1", "#2", ...)
    // ist keine Platten-ID, sondern die vom Spieler gewaehlte Rueckleg-Position.
    div.innerHTML = `
      <div class="d2x2" style="width:46px; height:46px;">${t.spaces.map(sp=>spaceHTML(sp)).join('')}</div>
      <div class="order-badge" style="font-size:10px; font-weight:bold;">${placedAt !== -1 ? '#' + (placedAt + 1) : ''}</div>`;

    div.addEventListener('click', () => {
      if(order.includes(t.id)) return; // schon plaziert, ignorieren
      order.push(t.id);
      renderReturnOrderPicker();
    });

    pool.appendChild(div);
  });

  if(order.length === rest.length) {
    document.getElementById('dome-confirm').disabled = false;
  }
}

// Reset-Link (Nutzer-Anstoss, Muster von resetMoonStack übernommen): komplette
// Reihenfolge verwerfen, alle Restplatten wieder unplatziert -- ohne die
// ganze Stapel-Ziehung per "Abbrechen" aufzugeben (die Kosten sind ja schon
// real bezahlt, siehe renderStackPeekState-Kommentar zum Cancel-Button).
function resetReturnOrder() {
  if(!domeModal || !domeModal.stack_draw) return;
  domeModal.stack_draw.return_order = [];
  renderReturnOrderPicker();
}

function closeDomeModal() {
  // Abbrechen-Button wieder anzeigen für nächstes Mal
  const cancelBtn = document.querySelector('#dome-overlay .cancel-btn');
  if(cancelBtn) cancelBtn.style.display = '';
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

  // Einheitlicher Flow für Start, Display UND Stapel: Karte ist gewählt → Modal
  // schließen, Slot per Board-Klick wählen lassen. Kein sofortiger Server-Call.
  if(is_start) {
    const chosenTile = (S.dome_display || []).find(t => t.id === tile_id);
    pendingStackPlacement = { source: 'start', pi, tile_id, rotation, tile: chosenTile };
  } else if(stack_draw) {
    const chosenTile = (S.pending_stack_draw || []).find(t => t.id === stack_draw.chosen_id);
    pendingStackPlacement = {
      source: 'stack', pi, tile_id: stack_draw.chosen_id, rotation,
      tile: chosenTile, chosen_id: stack_draw.chosen_id,
      return_order: stack_draw.return_order || []
    };
  } else {
    const chosenTile = (S.dome_display || []).find(t => t.id === tile_id);
    pendingStackPlacement = {
      source: 'display', pi, tile_id, rotation, tile: chosenTile
    };
  }
  closeDomeModal();
  render();  // Board neu zeichnen (markiert freie Slots, zeigt Hinweis)
}

async function submitDomePlacement(sr, sc) {
  // Legt die schwebende Karte (Start, Display oder Stapel) auf den Slot.
  const pend = pendingStackPlacement;
  if(!pend) return;
  if(sr < 0 || sr > 2 || sc < 0 || sc > 2) {
    showError('Bitte ein freies Kuppelfeld auf deinem Board anklicken.');
    return;
  }
  if(pend.source === 'stack') {
    await submitStackDraw(pend.chosen_id, sr, sc, pend.rotation, pend.return_order);
  } else if(pend.source === 'start') {
    await submitStartTile(pend.pi, pend.tile_id, sr, sc, pend.rotation);
  } else {
    await submitDisplayDome(pend.tile_id, sr, sc, pend.rotation);
  }
}

async function submitStartTile(pi, tile_id, sr, sc, rotation) {
  const d = await api('/move/start_tile', {player: pi, tile_id, slot_row: sr, slot_col: sc, rotation});
  if(!d.ok){ showError(d.error || 'Zug abgelehnt (unbekannter Fehler).'); return; }
  S=d.state; pendingStackPlacement=null; closeDomeModal(); render();
  // Nachdem der Mensch gelegt hat: ist jetzt die KI mit ihrer Startkuppel dran?
  if (AI_ENABLED) {
    await aiDoStartTile();
  }
}

async function submitDisplayDome(tile_id, sr, sc, rotation) {
  const d = await api('/move/dome', {tile_id, slot_row: sr, slot_col: sc, rotation});
  if(!d.ok){ showError(d.error || 'Zug abgelehnt (unbekannter Fehler).'); return; }
  S=d.state; pendingStackPlacement=null; closeDomeModal(); clearHintHighlights(); render();
  showTeacherFeedback(d.teacher_feedback);
  if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
}

async function submitStackDraw(chosen_id, sr, sc, rotation, return_order) {
  // Schutz: ein ungültiger Slot (-1) würde serverseitig eine leere
  // AssertionError auslösen → leere Fehlermeldung. Hier klar abfangen.
  if(sr < 0 || sr > 2 || sc < 0 || sc > 2) {
    showError('Bitte zuerst ein freies Kuppelfeld auf deinem Board anklicken.');
    return;
  }
  const d = await api('/move/dome_stack_choose', {
    chosen_id, slot_row: sr, slot_col: sc, rotation, return_order
  });
  if(!d.ok){showError(d.error || 'Zug abgelehnt (unbekannter Fehler).');return;}
  S=d.state; pendingStackPlacement=null; closeDomeModal(); clearHintHighlights(); render();
  showTeacherFeedback(d.teacher_feedback);
  // KI-Check erzwingen, egal in welcher Phase
  if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
}

// -- MOON ORDER MODAL ---------------------------------------------------------
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
    div.addEventListener('click', () => addToMoonStack(item.uid));
    tilesDiv.appendChild(div);
  });

  stackDiv.querySelectorAll('.tile').forEach(e => e.remove());
  if(moonModal.ordered.length === 0) {
    empty.style.display = 'inline';
  } else {
    empty.style.display = 'none';
    // Nutzer-Feedback: dieselbe vertikale Ueberlapp-Darstellung wie der
    // spaetere Mondstapel auf dem Spielbrett (siehe renderBoard/moonTiles) --
    // oberste (zuletzt geklickte) Fliese oben, restliche darunter versetzt.
    const n = moonModal.ordered.length;
    const topDown = [...moonModal.ordered].reverse(); // topDown[0] = oben/zuletzt geklickt
    topDown.forEach((item, i) => {
      const origIndex = n - 1 - i; // Index in moonModal.ordered fuer removeFromMoonStack
      const div = document.createElement('div');
      div.className = `tile ${normColor(item.color)} click`;
      const isTop = i === 0;
      div.style.marginTop = isTop ? '0' : '-9px';
      div.style.zIndex = String(topDown.length - i);
      div.style.outline = isTop ? '2.5px solid var(--text)' : '';
      div.style.opacity = isTop ? '1' : '.85';
      div.style.cursor = 'pointer';
      div.title = (isTop ? 'Oben (sichtbar im Mondbereich)' : `${origIndex+1}. von unten`)
        + ' — klicken zum Entfernen (auch alle Fliesen darüber)';
      div.addEventListener('click', () => removeFromMoonStack(origIndex));
      stackDiv.insertBefore(div, empty);
    });
  }
}

// Nutzer-Feedback: Reihenfolge innerhalb des Modals korrigierbar machen, ohne
// die ganze Aktion per "Abbrechen" abzubrechen. Klick auf eine gestapelte
// Fliese wirft SIE UND ALLE DARUEBER (spaeter geklickten) zurueck in den Pool
// -- "zurueckspulen bis hierher", Reihenfolge der Uebrigen bleibt erhalten.
function removeFromMoonStack(index) {
  if(!moonModal) return;
  const removed = moonModal.ordered.splice(index);
  moonModal.items.push(...removed);
  document.getElementById('moon-confirm').disabled = true;
  renderMoonModal();
}

function resetMoonStack() {
  if(!moonModal) return;
  moonModal.items.push(...moonModal.ordered.splice(0));
  document.getElementById('moon-confirm').disabled = true;
  renderMoonModal();
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

// -- STACK BUY MODAL ----------------------------------------------------------
function openStackBuyModal() {
  const pi = activePlacingPlayer();
  openDomeModal(pi, -1, -1);
}

// -- SCORING TILES -------------------------------------------------------------
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
    const locked = !sel && _isScoringLocked(t.id);
    const partner = _scoringPartnerOf(t.id);
    const partnerTile = partner !== null ? allScoringTiles.find(x => x.id === partner) : null;
    const exclNote = partnerTile
      ? `<div style="font-size:8px;color:var(--text3);margin-top:3px">schließt „${partnerTile.name}" aus</div>`
      : '';
    return `<div data-stid="${t.id}" onclick="toggleScoringTile(${t.id})"
      style="border:1.5px solid ${sel?'var(--blau)':'var(--border)'};
             background:${sel?'#EFF6FF':(locked?'#F3F4F6':'var(--surface)')};
             opacity:${locked?0.45:1};
             border-radius:8px;padding:8px;
             cursor:${locked?'not-allowed':'pointer'};transition:all .1s">
      <div style="font-size:16px;margin-bottom:4px">${t.emoji}</div>
      <div style="font-size:11px;font-weight:600">${t.name}</div>
      <div style="font-size:9px;color:var(--text2);margin-top:2px">${t.description}</div>
      ${exclNote}
    </div>`;
  }).join('');
  const count = selectedScoringIds.size;
  const countEl = document.getElementById('scoring-count');
  if(countEl) countEl.textContent = count;
  const btn = document.getElementById('scoring-confirm');
  if(btn) btn.disabled = count !== 3;
}

function _scoringPartnerOf(id) {
  // Partner aus der vom Server gelieferten 'excludes'-Info
  const t = allScoringTiles.find(x => x.id === id);
  return (t && t.excludes !== null && t.excludes !== undefined) ? t.excludes : null;
}

function _isScoringLocked(id) {
  // Gesperrt, wenn der Ausschluss-Partner bereits gewählt ist
  const partner = _scoringPartnerOf(id);
  return partner !== null && selectedScoringIds.has(partner);
}

function toggleScoringTile(id) {
  if(selectedScoringIds.has(id)) {
    selectedScoringIds.delete(id);
  } else if(_isScoringLocked(id)) {
    // Partner ist gewählt → diese Karte ist gesperrt, nichts tun
    return;
  } else if(selectedScoringIds.size < 3) {
    selectedScoringIds.add(id);
  }
  renderScoringGrid();
}

async function _notifyGameEnd() {
  try { await api('/end_game_log', {}); } catch(e) {}
}

async function downloadGameLog() {
  // Lädt das Log der aktuellen Partie herunter (Dateiname vom Server erfragen,
  // damit auch nach einem Seitenreload der aktuelle Stand bekannt ist).
  let file = null;
  try {
    const d = await api('/log_info');
    if (d && d.ok) file = d.log_file;
  } catch(e) { /* Server evtl. nicht erreichbar -- Fallback unten */ }
  if (!file) file = window._gameLogFile;
  if (!file) { showError('Noch kein Spiel-Log vorhanden — zuerst ein Spiel starten.'); return; }
  const a = document.createElement('a');
  a.href = `/static/log/${file}`;
  a.download = file;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

async function confirmScoringTiles() {
  const ids = [...selectedScoringIds];
  const d = await api('/scoring_tiles/select', {ids});
  if(!d.ok){showError(d.error);return;}
  S = d.state;
  document.getElementById('scoring-overlay').style.display='none';
  render();
  // KI legt ihre Startkuppelplatte automatisch
  if (AI_ENABLED) {
    await aiDoStartTile();
  }
}

async function aiDoStartTile() {
  // start_placed=true → bereits gelegt, nichts tun
  const aiPlayer = S.players[AI_PLAYER];
  if (!aiPlayer || aiPlayer.start_placed === true) return;

  // Reihenfolge: Nicht-Startspieler legt ZUERST. Wenn die KI Startspieler ist,
  // muss erst der Mensch (Nicht-Startspieler) legen. Sonst lehnt die Engine ab
  // ("Nicht-Startspieler muss zuerst...") und es entsteht ein Deadlock.
  const starter = S.current_player;          // Startspieler dieser Runde
  const human = 1 - AI_PLAYER;
  const aiIsStarter = (AI_PLAYER === starter);
  if (aiIsStarter && S.players[human].start_placed !== true) {
    // KI ist Startspieler, Mensch hat noch nicht gelegt → KI wartet
    return;
  }

  await new Promise(r => setTimeout(r, 600));
  const d = await api('/ai/start_tile');
  if (!d.ok) { showError('KI Startkachel Fehler: ' + d.error); return; }
  S = d.state;
  render();
  
  if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
  
}

async function calculateEndScoring() {
  const d = await api('/end_scoring', {});
  if(!d.ok){showError(d.error);return;}
  S = d.state;
  console.log(d)
  await showEndResults(d.end_scoring, d.rating_updates);
  render();
}

// Spielerprofile: baut die Rating-Zeile "Rating: 1000 -> 1016 (+16) vs
// v19_2d_best@400 (1326)" aus EINEM Historien-Eintrag (s.
// player_profiles.py::apply_result). `~` vor der Gegner-Elo markiert einen
// Schaetzwert (opponent_is_estimate). User-Entscheid 2026-08-02: bei
// `rated===false` (KI-Tipps genutzt, s. player_profiles.py::record_unrated)
// wird STATT der Rating-Aenderung ein erklaerender Hinweis gezeigt --
// rating_before===rating_after in diesem Fall ohnehin (keine echte Aenderung).
function _ratingUpdateLineHTML(name, entry) {
  if (!entry) return '';
  if (entry.rated === false) {
    return `<div style="font-size:11px;margin-top:4px">
      <strong>${_escapeHtml(name)}</strong>:
      <span style="color:#B45309">ungewertet (KI-Tipps genutzt)</span>
      <span style="color:var(--text3)">— Rating bleibt bei ${Math.round(entry.rating_before)}</span>
    </div>`;
  }
  const sign = entry.delta >= 0 ? '+' : '';
  const deltaColor = entry.delta > 0 ? '#059669' : entry.delta < 0 ? '#DC2626' : 'var(--text2)';
  const oppRating = `${entry.opponent_is_estimate ? '~' : ''}${Math.round(entry.opponent_rating)}`;
  return `<div style="font-size:11px;margin-top:4px">
    <strong>${_escapeHtml(name)}</strong>: Rating: ${Math.round(entry.rating_before)}
    → ${Math.round(entry.rating_after)}
    (<span style="color:${deltaColor};font-weight:600">${sign}${entry.delta}</span>)
    vs ${_escapeHtml(entry.opponent)} (${oppRating})
  </div>`;
}

async function showEndResults(results, ratingUpdates) {
  if (!S || !S.players) return;
  const p0 = S.players[0], p1 = S.players[1];
  // Tie-Break wie oben in render(): first_player_next_round statt der (bei
  // Rundenwertung geloeschten) Marker-Flags.
  const winner = p0.score > p1.score ? p0.name
    : p1.score > p0.score ? p1.name
    : S.first_player_next_round === 0 ? p0.name
    : S.first_player_next_round === 1 ? p1.name : 'Unentschieden';

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

  // Spielerprofile: Rating-Aenderung(en) dieser Partie (s. _apply_elo_for_
  // finished_game in server.py) -- ein Eintrag je gewertetem Profil, oder
  // ein erklaerender Hinweis, wieso NICHT gewertet wurde (z.B. kein Profil
  // ausgewaehlt, kein Elo-Anker fuer die KI-Stufe bekannt).
  let ratingHTML = '';
  if (ratingUpdates) {
    const line0 = _ratingUpdateLineHTML(p0.name, ratingUpdates['0']);
    const line1 = _ratingUpdateLineHTML(p1.name, ratingUpdates['1']);
    if (line0 || line1) {
      ratingHTML = `<div class="sep" style="margin:10px 0"></div>
        <div class="lbl" style="margin-bottom:4px">📈 Elo-Wertung</div>
        ${line0}${line1}`;
    } else if (ratingUpdates.note) {
      ratingHTML = `<div class="sep" style="margin:10px 0"></div>
        <div style="font-size:10px;color:var(--text3)">📈 ${_escapeHtml(ratingUpdates.note)}</div>`;
    }
  }

  // Lehrer-Endbilanz (Stufe 3): optionaler Zusatzblock im selben Modal.
  let teacherHTML = '';
  if (TEACHER_LEVEL === 3) {
    try {
      const sum = await api('/teacher/summary');
      if (sum.ok && sum.count > 0) {
        const worstHTML = sum.worst.map(w => `
          <li style="font-size:10px;margin-bottom:2px">
            Runde ${w.round}: −${w.delta_win_pp.toFixed(1)} pp (Rang ${w.rang}) — besser: ${w.top_desc}
          </li>`).join('');
        teacherHTML = `
          <div class="sep" style="margin:10px 0"></div>
          <div class="lbl">🎓 Lehrer-Bilanz</div>
          <div style="font-size:11px;margin-bottom:6px">
            ${sum.count} bewertete Züge · Ø Abweichung vom Bestzug:
            <strong>${sum.avg_delta_win_pp.toFixed(1)} pp</strong> ·
            Top-1: <strong>${(sum.top1_rate*100).toFixed(0)}%</strong> ·
            Top-3: <strong>${(sum.top3_rate*100).toFixed(0)}%</strong>
          </div>
          ${worstHTML ? `<div style="font-size:10px;color:var(--text2);margin-bottom:4px">Größte Abweichungen:</div>
            <ul style="padding-left:16px;margin-bottom:4px">${worstHTML}</ul>` : ''}
        `;
      }
    } catch (e) {
      // Bilanz ist ein Zusatzfeature -- ein Fehler hier darf die Endwertung nicht blockieren.
    }
  }

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
    ${ratingHTML}
    ${teacherHTML}
    <button style="width:100%;padding:9px;background:var(--text);color:#fff;border:none;border-radius:7px;cursor:pointer;font-family:inherit;font-size:12px;margin-top:8px" onclick="document.getElementById('end-overlay').style.display='none';newGame()">Neues Spiel</button>
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

// -- EVENT DELEGATION ----------------------------------------------------------
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
    // Wartet eine gewählte Karte (Start, Display oder Stapel) auf ihren Slot?
    if(pendingStackPlacement && pendingStackPlacement.pi===pi) {
      submitDomePlacement(sr, sc);
      return;
    }
    // Keine Karte gewählt: Hinweis je nach Phase.
    const p = S.players[pi];
    if(p && !p.start_placed) {
      showError('Wähle zuerst eine Kuppelplatte unten im Display, dann Rotation.');
    } else {
      showError('Wähle zuerst eine Kuppelplatte (Display anklicken oder „Vom Stapel ziehen").');
    }
    return;
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

// -- RENDER --------------------------------------------------------------------
function render() {
  if(!S) return;

  if (S.phase === 'drafting') humanTilingDone = false;
  // Nutzer-Feedback (2026-07-29): uebersprungene Chip-Reihen leben nur fuer
  // die Dauer EINER Tiling-Phase -- verlassen wir sie (naechste Runde,
  // Rundenende, neues Spiel), muss der Session-Zustand weg statt in die
  // naechste Runde durchzuschlagen.
  if (S.phase !== 'tiling') {
    skippedChipRows = {0: new Set(), 1: new Set()};
  }

  document.getElementById('round-lbl').textContent=`Runde ${S.round}/5`;
  renderBoard(0);
  renderBoard(1);
  renderCenter();
  updateTeacherUI();

  // Platzierungs-Modus: gewählte Karte (Display oder Stapel) wartet auf Slot-Klick.
  if(pendingStackPlacement) {
    const {tile_id, rotation, tile, source, num} = pendingStackPlacement;
    const ROT = {0:[0,1,2,3], 90:[2,0,3,1], 180:[3,2,1,0], 270:[1,3,0,2]};
    const previewHTML = tile
      ? `<div class="d2x2" style="width:38px;height:38px;">${ROT[rotation||0].map(i=>spaceHTML(tile.spaces[i])).join('')}</div>`
      : '';
    // Punkt 8: keine Platten-ID mehr im Hinweistext -- previewHTML zeigt das
    // tatsaechliche Farbmuster ohnehin bereits an.
    const msg = source === 'stack'
      ? `📦 Platte gezogen — klick auf ein freies Kuppelfeld zum Legen (−${num} Pkt)`
      : source === 'start'
      ? `🏁 Startplatte gewählt — klick auf ein freies Kuppelfeld zum Legen`
      : `🧩 Platte gewählt — klick auf ein freies Kuppelfeld zum Legen`;
      
    document.getElementById('info-area').innerHTML = `
      <div class="info warn" style="display:flex; flex-direction:column; gap:8px;">
        <div style="align-self:center">${previewHTML}</div>
        <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
          <span>${msg}</span>
          <button class="btn" onclick="cancelStackPlacement()" style="padding:2px 8px; font-size:10px; flex-shrink:0;">Abbrechen</button>
        </div>
      </div>`;
  }
}

function cancelStackPlacement() {
  // Nutzer-Feedback 2026-08-07: der Stapel-Zug (Aktion A) ist ein
  // VERBINDLICHER, durchgaengiger Zug -- die Kosten sind bezahlt, die
  // Engine haelt pending_stack_draw. "Abbrechen" in der Slot-Phase fuehrt
  // deshalb ZURUECK zur Platten-/Rotationswahl, nicht in den freien
  // Zugmodus (dort waeren andere Aktionen ohnehin engine-seitig gesperrt).
  const wasStack = pendingStackPlacement && pendingStackPlacement.source === 'stack';
  pendingStackPlacement = null;
  document.getElementById('info-area').innerHTML = '';
  if (wasStack && (S.pending_stack_draw || []).length > 0) {
    openDomeModal(S.current_player, -1, -1, true);
    stackStopAndChoose();
    return;
  }
  render();
}

// -- DRAG & DROP FÜR MODALS --------------------------------------------------
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

// -- START ---------------------------------------------------------------------
makeDraggable('dome-overlay');
makeDraggable('moon-overlay');
makeDraggable('chip-overlay');
makeDraggable('scoring-overlay');

// Task #28: Aggressivitäts-Regler-Zustand laden (unabhängig vom Spielzustand,
// engine-weiter Parameter) -- auch bei fehlendem/altem Wheel ungefährlich

// Beim Laden: State synchronisieren und lokales Gedächtnis wiederherstellen
(async () => {
  const d = await api('/state');
  if (d.ok && d.state && d.state.phase && d.state.phase !== 'final') {
    S = d.state;

    // 1. Wertungsplatten (Metadaten) wieder in den Speicher laden
    const dt = await api('/scoring_tiles');
    if(dt.ok) {
      allScoringTiles = dt.tiles;
      selectedScoringIds = new Set(S.scoring_tile_ids || [0,1,2]);
    }

    // 2. KI-Status vom Server abfragen (Gedächtnis auffrischen!)
    const aiData = await api('/ai/config');
    if (aiData.ok && aiData.ai_enabled) {
      AI_ENABLED = true;
      AI_PLAYER = aiData.ai_player;
    } else {
      AI_ENABLED = false;
    }

    // 3. UI zeichnen
    render();
    
    // 4. Stupser für die KI: Falls sie vor dem Reload dran war, muss sie jetzt ziehen!
	if (AI_ENABLED && aiIsDue()) {
    await triggerAIMove();
  }
    
  } else {
    // Kein aktives Spiel gefunden
    openNewGameModal();
  }
})();