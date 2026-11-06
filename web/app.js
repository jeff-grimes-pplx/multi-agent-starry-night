/**
 * THE MULTI-AGENT ATELIER — WATCHING ORCHESTRATED SUBAGENTS REPAINT VAN GOGH'S STARRY NIGHT IN CODE
 * Interactive Observatory Application (HTML5 Canvas 3D-Lit Impasto Renderer + Synchronized Git Ledger)
 */

(function () {
  'use strict';

  const GITHUB_REPO_URL = 'https://github.com/jeff-grimes-pplx/multi-agent-starry-night';
  const TOTAL_SIM_SECONDS = 1200; // 20:00 orchestration timeline
  const TOTAL_STROKES = 19922;

  // Application State
  const state = {
    data: null,
    agentMap: {},
    refImage: null,
    refLoaded: false,

    mode: 'painting', // 'painting' | 'curtain' | 'rework' | 'xray'
    soloAgent: 0, // 0 = All 5 agents, 1..5 = solo agent
    showCursors: true,
    showRegions: false,
    impastoRelief: true,
    rakingAzimuthDeg: 135,

    curtainPos: 0.50,
    curtainPair: 'ref_vs_v2', // 'ref_vs_v2' | 'v1_vs_v2'
    selectedReworkAgent: 1,
    streamFilter: 'all', // 'all' | 'critique' | 'commit'

    // Playback & Timeline State (strokeIndex from 0 to 19,922)
    // Start at stroke 15,800 (~79% through orchestration, right in the middle of Act III v2 Rework)
    // and actively playing so the opening visual shows a rich, luminous Starry Night canvas
    // with all 5 subagent cursors actively laying down impasto strokes in parallel!
    strokeCursor: 15800,
    isPlaying: true,
    speed: 4, // 1, 4, 10, 25
    lastFrameTime: performance.now(),

    // Hover / Pinned Brushstroke Inspector
    hoveredStroke: null,
    lockedStroke: null,

    // Baked Offscreen Canvases for ultra-fast 60fps compositing
    bakedV1All: null,
    bakedV2All: null,
    progressiveCanvas: null,
    progressiveCtx: null,
    lastRenderedKey: '',

    // Smoothly animated subagent brush cursor coordinates
    agentCursors: {
      1: { x: 445, y: 235, tx: 445, ty: 235, activeStroke: null, pass: 2 },
      2: { x: 882, y: 138, tx: 882, ty: 138, activeStroke: null, pass: 2 },
      3: { x: 215, y: 465, tx: 215, ty: 465, activeStroke: null, pass: 2 },
      4: { x: 562, y: 585, tx: 562, ty: 585, activeStroke: null, pass: 2 },
      5: { x: 760, y: 485, tx: 760, ty: 485, activeStroke: null, pass: 2 },
    },
  };

  // DOM Element References matching web/index.html
  const dom = {
    canvas: document.getElementById('atelier-canvas'),
    overlay: document.getElementById('overlay-canvas'),
    canvasWrapper: document.getElementById('canvas-frame-wrapper'),
    reworkView: document.getElementById('rework-inspector-view'),
    curtainOverlay: document.getElementById('curtain-overlay'),
    curtainHandle: document.getElementById('curtain-handle'),
    curtainLeftLabel: document.getElementById('curtain-left-label'),
    curtainRightLabel: document.getElementById('curtain-right-label'),
    phasePill: document.getElementById('canvas-phase-pill'),
    phaseIndicator: document.getElementById('phase-indicator'),
    phaseText: document.getElementById('phase-text'),

    // Header Telemetry
    hudStrokes: document.getElementById('hud-strokes'),
    hudSsim: document.getElementById('hud-ssim'),
    hudDeltaE: document.getElementById('hud-delta-e'),
    hudPsnr: document.getElementById('hud-psnr'),

    // Stage Toolbar Toggles
    btnToggleCursors: document.getElementById('btn-toggle-cursors'),
    btnToggleRegions: document.getElementById('btn-toggle-regions'),
    btnToggleImpasto: document.getElementById('btn-toggle-impasto'),
    inputRakingAngle: document.getElementById('input-raking-angle'),
    rakingDegVal: document.getElementById('raking-deg-val'),

    // Hover Inspector
    inspSwatch: document.getElementById('insp-swatch'),
    inspStrokeId: document.getElementById('insp-stroke-id'),
    inspAgentBadge: document.getElementById('insp-agent-badge'),
    inspPassBadge: document.getElementById('insp-pass-badge'),
    inspCommitLink: document.getElementById('insp-commit-link'),
    inspGeomLine: document.getElementById('insp-geom-line'),
    inspCodeSnippet: document.getElementById('insp-code-snippet'),

    // Transport Controls
    btnPlayPause: document.getElementById('btn-play-pause'),
    playIcon: document.getElementById('play-icon'),
    playLabel: document.getElementById('play-label'),
    btnRestart: document.getElementById('btn-restart'),
    btnJumpCritique: document.getElementById('btn-jump-critique'),
    btnJumpFinal: document.getElementById('btn-jump-final'),
    scrubber: document.getElementById('timeline-scrubber'),
    clockCurrent: document.getElementById('clock-current'),
    commitTicksRow: document.getElementById('commit-ticks-row'),

    // Right Sidebar
    swimlaneList: document.getElementById('swimlane-list'),
    activityStreamList: document.getElementById('activity-stream-list'),

    // Rework Diff Inspector
    reworkV1Stat: document.getElementById('rework-v1-stat'),
    reworkV2Stat: document.getElementById('rework-v2-stat'),
    reworkRefStat: document.getElementById('rework-ref-stat'),
    reworkImgV1: document.getElementById('rework-img-v1'),
    reworkImgV2: document.getElementById('rework-img-v2'),
    reworkImgRef: document.getElementById('rework-img-ref'),
    reworkV1Flaw: document.getElementById('rework-v1-flaw'),
    reworkV2Fix: document.getElementById('rework-v2-fix'),
    reworkCritiqueNote: document.getElementById('rework-critique-note'),
    reworkCodeTitle: document.getElementById('rework-code-title'),
    reworkCommitLink: document.getElementById('rework-commit-link'),
    reworkCodeV1: document.getElementById('rework-code-v1'),
    reworkCodeV2: document.getElementById('rework-code-v2'),
  };

  const ctx = dom.canvas.getContext('2d', { alpha: false });
  const overlayCtx = dom.overlay.getContext('2d');

  // ==========================================================================
  // 1. INITIALIZATION & DATA BUNDLE LOADING
  // ==========================================================================

  async function init() {
    try {
      const [dataResp] = await Promise.all([
        fetch('assets/atelier_data.json'),
        loadReferenceImage('assets/reference_1000x792.jpg'),
      ]);
      state.data = await dataResp.json();

      for (const ag of state.data.agents) {
        state.agentMap[ag.id] = ag;
      }

      // Pre-bake offscreen canvases for instantaneous comparisons and fast scrubbing
      bakeOffscreenCanvases();

      // Build UI panels
      buildCommitTicks();
      buildSwimlaneRows();
      buildActivityStream();
      selectReworkAgent(state.selectedReworkAgent);
      bindEvents();

      // Sync play button and render initial state
      syncPlayButtonUI();
      updateSimulationByStrokeCursor(state.strokeCursor, true);
      requestAnimationFrame(animationLoop);
    } catch (err) {
      console.error('Failed to initialize Multi-Agent Atelier:', err);
    }
  }

  function loadReferenceImage(src) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        state.refImage = img;
        state.refLoaded = true;
        resolve();
      };
      img.onerror = () => resolve();
      img.src = src;
    });
  }

  // ==========================================================================
  // 2. 3D RAKING-LIGHT IMPASTO BRUSHSTROKE RENDERER
  // ==========================================================================
  // Packed stroke tuple in atelier_data.json:
  // [0:x0, 1:y0, 2:cx, 3:cy, 4:x1, 5:y1, 6:w, 7:r, 8:g, 9:b, 10:agent, 11:pass_num, 12:commit_num, 13:t_sec, 14:theta]

  function clampByte(v) {
    return v < 0 ? 0 : v > 255 ? 255 : v | 0;
  }

  function rgbToHex(r, g, b) {
    return (
      '#' +
      [r, g, b]
        .map((c) => clampByte(c).toString(16).padStart(2, '0'))
        .join('')
        .toUpperCase()
    );
  }

  function getLightVector() {
    const rad = (state.rakingAzimuthDeg * Math.PI) / 180;
    return { lx: Math.cos(rad), ly: -Math.sin(rad) };
  }

  function drawImpastoStroke(targetCtx, s, reliefEnabled, lightVec) {
    const x0 = s[0];
    const y0 = s[1];
    const cx = s[2];
    const cy = s[3];
    const x1 = s[4];
    const y1 = s[5];
    const w = s[6];
    const r = s[7];
    const g = s[8];
    const b = s[9];

    targetCtx.lineCap = 'round';
    targetCtx.lineJoin = 'round';

    if (!reliefEnabled) {
      targetCtx.strokeStyle = `rgb(${r},${g},${b})`;
      targetCtx.lineWidth = w;
      targetCtx.beginPath();
      targetCtx.moveTo(x0, y0);
      targetCtx.quadraticCurveTo(cx, cy, x1, y1);
      targetCtx.stroke();
      return;
    }

    const dx = x1 - x0;
    const dy = y1 - y0;
    const len = Math.hypot(dx, dy) + 1e-5;
    const nx = -dy / len;
    const ny = dx / len;
    const dot = nx * lightVec.lx + ny * lightVec.ly;

    const shOffX = -lightVec.lx * 0.85;
    const shOffY = -lightVec.ly * 0.85;
    const hiOffX = lightVec.lx * 0.65;
    const hiOffY = lightVec.ly * 0.65;

    // 1. Raking-light shadow bevel on leeward edge of paint ridge
    if (w >= 2.2) {
      const shDrop = 22;
      targetCtx.strokeStyle = `rgb(${clampByte(r - shDrop)},${clampByte(g - shDrop)},${clampByte(b - shDrop)})`;
      targetCtx.lineWidth = w;
      targetCtx.beginPath();
      targetCtx.moveTo(x0 + shOffX, y0 + shOffY);
      targetCtx.quadraticCurveTo(cx + shOffX, cy + shOffY, x1 + shOffX, y1 + shOffY);
      targetCtx.stroke();
    }

    // 2. Main oil-pigment stroke body
    targetCtx.strokeStyle = `rgb(${r},${g},${b})`;
    targetCtx.lineWidth = w;
    targetCtx.beginPath();
    targetCtx.moveTo(x0, y0);
    targetCtx.quadraticCurveTo(cx, cy, x1, y1);
    targetCtx.stroke();

    // 3. 3D Impasto specular bristle ridge on windward edge
    const specBoost = Math.round(18 + 14 * Math.max(0, dot));
    const hiW = Math.max(1.0, w * 0.35);
    targetCtx.strokeStyle = `rgb(${clampByte(r + specBoost)},${clampByte(g + specBoost)},${clampByte(b + specBoost)})`;
    targetCtx.lineWidth = hiW;
    targetCtx.beginPath();
    targetCtx.moveTo(x0 + hiOffX, y0 + hiOffY);
    targetCtx.quadraticCurveTo(cx + hiOffX, cy + hiOffY, x1 + hiOffX, y1 + hiOffY);
    targetCtx.stroke();
  }

  function createOffscreenCanvas(w = 1000, h = 792) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    return c;
  }

  function fillPrimedLinen(targetCtx, w = 1000, h = 792) {
    targetCtx.fillStyle = '#141926';
    targetCtx.fillRect(0, 0, w, h);
  }

  function bakeOffscreenCanvases() {
    const strokesV1 = state.data.strokesV1;
    const strokesV2 = state.data.strokesV2;
    const lightVec = getLightVector();

    // 1. Baked Pre-Critique v1 canvas (4,697 strokes)
    state.bakedV1All = createOffscreenCanvas();
    const v1Ctx = state.bakedV1All.getContext('2d', { alpha: false });
    fillPrimedLinen(v1Ctx);
    for (let i = 0; i < strokesV1.length; i++) {
      drawImpastoStroke(v1Ctx, strokesV1[i], state.impastoRelief, lightVec);
    }

    // 2. Baked Post-Critique v2 master canvas (19,922 strokes)
    state.bakedV2All = createOffscreenCanvas();
    const v2Ctx = state.bakedV2All.getContext('2d', { alpha: false });
    fillPrimedLinen(v2Ctx);
    for (let i = 0; i < strokesV2.length; i++) {
      drawImpastoStroke(v2Ctx, strokesV2[i], state.impastoRelief, lightVec);
    }

    if (!state.progressiveCanvas) {
      state.progressiveCanvas = createOffscreenCanvas();
      state.progressiveCtx = state.progressiveCanvas.getContext('2d', { alpha: false });
    }
    state.lastRenderedKey = '';
  }

  // ==========================================================================
  // 3. TIMELINE PHASE ENGINE & PROGRESSIVE CANVAS RENDERER
  // ==========================================================================
  // Note: state.data.strokesV2 has 19,922 strokes ordered chronologically:
  // - Indices 0 .. 4,696 (pass1Count = 4,697) are Pass 1 (00:00 -> 08:15)
  // - At 4,697 (08:15 -> 09:35), Computer pauses for QA Critique
  // - Indices 4,697 .. 19,921 are Pass 2 Critique Rework (09:35 -> 20:00)

  function getPhaseDescriptor(strokeIdx) {
    const p1Count = state.data ? state.data.pass1Count : 4697;
    if (strokeIdx < p1Count) {
      const frac1 = strokeIdx / Math.max(1, p1Count);
      return {
        act: 'v1',
        frac1,
        frac2: 0,
        simSec: Math.round(frac1 * 495), // 00:00 -> 08:15
        label: `Pass 1 (v1) In Progress — 5 Subagents Painting Initial Regional Strokes (${strokeIdx.toLocaleString()} / ${p1Count.toLocaleString()})`,
        dotColor: '#58A6FF',
      };
    } else if (strokeIdx === p1Count) {
      return {
        act: 'critique',
        frac1: 1,
        frac2: 0,
        simSec: 535, // 08:55 QA Critique Pause
        label: 'QA Critique Gate (08:35–09:25) — Perplexity Computer (Gemini 4 Argon) Auditing Regional ΔE & Issuing 5 Rework Specs',
        dotColor: '#FB923C',
      };
    } else if (strokeIdx < TOTAL_STROKES) {
      const frac2 = (strokeIdx - p1Count) / Math.max(1, TOTAL_STROKES - p1Count);
      return {
        act: 'v2',
        frac1: 1,
        frac2,
        simSec: Math.round(570 + frac2 * 600), // 09:30 -> 19:30
        label: `Pass 2 (v2) Critique Rework — Subagents Applying Impasto & Flow Corrections (${strokeIdx.toLocaleString()} / ${TOTAL_STROKES.toLocaleString()})`,
        dotColor: '#4ADE80',
      };
    } else {
      return {
        act: 'merged',
        frac1: 1,
        frac2: 1,
        simSec: 1200, // 20:00
        label: 'Pass 2 Complete — All 5 Subagent Reworks Merged to Master (19,922 Strokes · SSIM 0.9138 · ΔE 3.16)',
        dotColor: '#F5C438',
      };
    }
  }

  function renderMainStage() {
    if (!state.data) return;

    const strokeIdx = Math.min(TOTAL_STROKES, Math.max(0, Math.round(state.strokeCursor)));
    const phase = getPhaseDescriptor(strokeIdx);
    const solo = state.soloAgent;
    const strokesV1 = state.data.strokesV1;
    const strokesV2 = state.data.strokesV2;
    const p1Count = state.data.pass1Count;
    const lightVec = getLightVector();

    const stateKey = `${strokeIdx}_${solo}_${state.impastoRelief}_${state.rakingAzimuthDeg}_${state.mode}`;
    if (stateKey !== state.lastRenderedKey) {
      const pCtx = state.progressiveCtx;

      // Fast path when all agents visible, default raking angle, and painting/curtain mode
      if (
        solo === 0 &&
        state.impastoRelief &&
        state.rakingAzimuthDeg === 135 &&
        state.mode !== 'xray' &&
        strokeIdx === TOTAL_STROKES
      ) {
        pCtx.drawImage(state.bakedV2All, 0, 0);
      } else if (
        solo === 0 &&
        state.impastoRelief &&
        state.rakingAzimuthDeg === 135 &&
        state.mode !== 'xray' &&
        strokeIdx === p1Count
      ) {
        pCtx.drawImage(state.bakedV1All, 0, 0);
      } else if (state.mode === 'xray') {
        renderXRayMode(pCtx, strokesV2, strokeIdx, solo);
      } else {
        fillPrimedLinen(pCtx);

        // Faint ground-truth context when soloing a single subagent
        if (solo !== 0 && state.refLoaded) {
          pCtx.save();
          pCtx.globalAlpha = 0.14;
          pCtx.drawImage(state.refImage, 0, 0, 1000, 792);
          pCtx.restore();
        }

        // During Pass 1 (0 .. p1Count), draw from strokesV1 so the user sees the authentic v1 initial strokes!
        // During Pass 2 (> p1Count), draw the v2 strokes up to strokeIdx!
        const activePool = strokeIdx <= p1Count ? strokesV1 : strokesV2;
        const limit = Math.min(activePool.length, strokeIdx);

        for (let i = 0; i < limit; i++) {
          const s = activePool[i];
          if (solo === 0 || s[10] === solo) {
            drawImpastoStroke(pCtx, s, state.impastoRelief, lightVec);
            updateAgentCursorTarget(s);
          }
        }
      }

      state.lastRenderedKey = stateKey;
    }

    // Draw progressive canvas onto visible stage
    ctx.drawImage(state.progressiveCanvas, 0, 0);

    // If Split-Curtain Loupe mode is active, composite left/right comparison
    if (state.mode === 'curtain') {
      const splitX = Math.round(state.curtainPos * 1000);
      // Left side of curtain shows either 1889 MoMA Reference or Pre-Critique v1
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, splitX, 792);
      ctx.clip();

      if (state.curtainPair === 'ref_vs_v2' && state.refLoaded) {
        ctx.drawImage(state.refImage, 0, 0, 1000, 792);
      } else if (state.bakedV1All) {
        ctx.drawImage(state.bakedV1All, 0, 0);
      }
      ctx.restore();
    }

    // Render interactive overlay (Agent cursors, anatomical polygons, hovered stroke)
    renderStageOverlay(phase);
  }

  function updateAgentCursorTarget(s) {
    const agId = s[10];
    const c = state.agentCursors[agId];
    if (c) {
      c.tx = s[4];
      c.ty = s[5];
      c.activeStroke = s;
      c.pass = s[11];
    }
  }

  function renderXRayMode(targetCtx, strokesV2, strokeIdx, solo) {
    targetCtx.fillStyle = '#070a10';
    targetCtx.fillRect(0, 0, 1000, 792);

    const limit = Math.min(strokesV2.length, Math.max(1500, strokeIdx));
    for (let i = 0; i < limit; i++) {
      const s = strokesV2[i];
      if (solo !== 0 && s[10] !== solo) continue;
      const ag = state.agentMap[s[10]];
      const col = ag ? ag.color : '#58A6FF';

      // Translucent pigment footprint
      targetCtx.strokeStyle = `rgba(${s[7]},${s[8]},${s[9]},0.22)`;
      targetCtx.lineWidth = s[6];
      targetCtx.beginPath();
      targetCtx.moveTo(s[0], s[1]);
      targetCtx.quadraticCurveTo(s[2], s[3], s[4], s[5]);
      targetCtx.stroke();

      // Crisp quadratic Bézier centerline spine
      targetCtx.strokeStyle = col;
      targetCtx.lineWidth = 1.1;
      targetCtx.beginPath();
      targetCtx.moveTo(s[0], s[1]);
      targetCtx.quadraticCurveTo(s[2], s[3], s[4], s[5]);
      targetCtx.stroke();
    }
  }

  // ==========================================================================
  // 4. OVERLAY RENDERER (POLYGONS, CURSORS, HOVER BRUSHSTROKE X-RAY)
  // ==========================================================================

  function renderStageOverlay(phase) {
    overlayCtx.clearRect(0, 0, 1000, 792);

    // 1. Anatomical Region Polygons & Celestial Corona Rings
    if (state.showRegions || phase.act === 'critique') {
      drawAnatomicalRegions(overlayCtx, phase);
    }

    // 2. Simultaneous Multi-Agent Brush Cursors
    if (state.showCursors && state.mode !== 'curtain') {
      drawAgentCursors(overlayCtx, phase);
    }

    // 3. Hovered or Pinned Brushstroke Vector Inspector
    const inspStroke = state.lockedStroke || state.hoveredStroke;
    if (inspStroke) {
      drawInspectedStrokeHighlight(overlayCtx, inspStroke);
    }
  }

  function drawPolygonContour(oCtx, pts, strokeColor, fillColor) {
    if (!pts || !pts.length) return;
    oCtx.beginPath();
    oCtx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) {
      oCtx.lineTo(pts[i][0], pts[i][1]);
    }
    oCtx.closePath();
    if (fillColor) {
      oCtx.fillStyle = fillColor;
      oCtx.fill();
    }
    oCtx.strokeStyle = strokeColor;
    oCtx.stroke();
  }

  function drawAnatomicalRegions(oCtx, phase) {
    const reg = state.data.regions;
    if (!reg) return;

    const isCritique = phase.act === 'critique';
    oCtx.save();
    oCtx.lineWidth = 2.0;
    oCtx.setLineDash([6, 4]);

    // Agent 02 Celestial Corona Rings (Moon, Venus, 11 Stars)
    if (state.soloAgent === 0 || state.soloAgent === 2) {
      oCtx.strokeStyle = isCritique ? '#FB923C' : '#F5C438';
      for (const body of reg.celestial) {
        oCtx.beginPath();
        oCtx.arc(body.x, body.y, body.r_outer, 0, Math.PI * 2);
        oCtx.stroke();
      }
    }

    // Agent 03 Cypress Polygon
    if (state.soloAgent === 0 || state.soloAgent === 3) {
      drawPolygonContour(
        oCtx,
        reg.cypress,
        isCritique ? '#FB923C' : '#4ADE80',
        isCritique ? 'rgba(251, 146, 60, 0.12)' : 'rgba(74, 222, 128, 0.06)'
      );
    }

    // Agent 04 Village Polygon
    if (state.soloAgent === 0 || state.soloAgent === 4) {
      drawPolygonContour(
        oCtx,
        reg.village,
        '#FB923C',
        isCritique ? 'rgba(251, 146, 60, 0.14)' : 'rgba(251, 146, 60, 0.06)'
      );
    }

    // Agent 05 Alpilles Mountain Ridge Polygon
    if (state.soloAgent === 0 || state.soloAgent === 5) {
      drawPolygonContour(
        oCtx,
        reg.mountain,
        isCritique ? '#FB923C' : '#C084FC',
        isCritique ? 'rgba(251, 146, 60, 0.12)' : 'rgba(192, 132, 252, 0.06)'
      );
    }

    // Region Callout Labels
    oCtx.setLineDash([]);
    const labels = [
      { id: 1, x: 390, y: 205, text: 'AG-01 · Opus 4.6 Sky Vortex (ΔE 10.66 → 3.14)' },
      { id: 2, x: 730, y: 42, text: 'AG-02 · Argon Moon & 11 Stars (ΔE 18.08 → 3.33)' },
      { id: 3, x: 120, y: 280, text: 'AG-03 · GPT-6.1 Sol Cypress (SSIM 0.941)' },
      { id: 4, x: 465, y: 660, text: 'AG-04 · Sonnet 4.6 Village & Spire (+37.9% SSIM)' },
      { id: 5, x: 675, y: 475, text: 'AG-05 · DeepSeek V4 Alpilles Hills (SSIM 0.909)' },
    ];

    oCtx.font = '600 12px "Satoshi", sans-serif';
    for (const lb of labels) {
      if (state.soloAgent !== 0 && state.soloAgent !== lb.id) continue;
      const ag = state.agentMap[lb.id];
      const tw = oCtx.measureText(lb.text).width + 16;
      oCtx.fillStyle = 'rgba(10, 13, 20, 0.9)';
      oCtx.strokeStyle = isCritique ? '#FB923C' : ag.color;
      oCtx.lineWidth = 1.4;
      oCtx.beginPath();
      oCtx.roundRect(lb.x, lb.y, tw, 24, 5);
      oCtx.fill();
      oCtx.stroke();

      oCtx.fillStyle = isCritique ? '#FB923C' : '#F3F1EA';
      oCtx.fillText(lb.text, lb.x + 8, lb.y + 16);
    }

    oCtx.restore();
  }

  function drawAgentCursors(oCtx, phase) {
    const isCritique = phase.act === 'critique';
    for (const ag of state.data.agents) {
      const id = ag.id;
      if (state.soloAgent !== 0 && state.soloAgent !== id) continue;
      const cur = state.agentCursors[id];
      if (!cur) continue;

      cur.x += (cur.tx - cur.x) * 0.28;
      cur.y += (cur.ty - cur.y) * 0.28;

      const ringColor = isCritique ? '#FB923C' : ag.color;
      oCtx.save();
      oCtx.translate(cur.x, cur.y);

      // Outer glowing ring
      oCtx.beginPath();
      oCtx.arc(0, 0, isCritique ? 13 : 9.5, 0, Math.PI * 2);
      oCtx.strokeStyle = ringColor;
      oCtx.lineWidth = 2.2;
      oCtx.stroke();

      // Inner brush tip
      oCtx.beginPath();
      oCtx.arc(0, 0, 3.8, 0, Math.PI * 2);
      oCtx.fillStyle = '#FFFFFF';
      oCtx.fill();

      // Agent floating pill
      const tagText = isCritique
        ? `${ag.code} · QA REWORK SPEC`
        : `${ag.code} · ${ag.model} (v${cur.pass})`;
      oCtx.font = '600 11.5px "JetBrains Mono", monospace';
      const tw = oCtx.measureText(tagText).width + 12;
      const boxX = cur.x > 780 ? -tw - 10 : 12;
      const boxY = cur.y < 36 ? 6 : -24;

      oCtx.fillStyle = 'rgba(10, 13, 20, 0.9)';
      oCtx.strokeStyle = ringColor;
      oCtx.lineWidth = 1.25;
      oCtx.beginPath();
      oCtx.roundRect(boxX, boxY, tw, 20, 4);
      oCtx.fill();
      oCtx.stroke();

      oCtx.fillStyle = isCritique ? '#FB923C' : '#F3F1EA';
      oCtx.fillText(tagText, boxX + 6, boxY + 14);
      oCtx.restore();
    }
  }

  function drawInspectedStrokeHighlight(oCtx, s) {
    oCtx.save();
    oCtx.lineCap = 'round';

    // Gold selection halo
    oCtx.strokeStyle = '#F5C438';
    oCtx.lineWidth = s[6] + 4.5;
    oCtx.beginPath();
    oCtx.moveTo(s[0], s[1]);
    oCtx.quadraticCurveTo(s[2], s[3], s[4], s[5]);
    oCtx.stroke();

    // True stroke pigment core
    oCtx.strokeStyle = `rgb(${s[7]},${s[8]},${s[9]})`;
    oCtx.lineWidth = s[6];
    oCtx.beginPath();
    oCtx.moveTo(s[0], s[1]);
    oCtx.quadraticCurveTo(s[2], s[3], s[4], s[5]);
    oCtx.stroke();

    // Quadratic Bézier control polygon (x0,y0) -> (cx,cy) -> (x1,y1)
    oCtx.strokeStyle = '#58A6FF';
    oCtx.lineWidth = 1.3;
    oCtx.setLineDash([3, 3]);
    oCtx.beginPath();
    oCtx.moveTo(s[0], s[1]);
    oCtx.lineTo(s[2], s[3]);
    oCtx.lineTo(s[4], s[5]);
    oCtx.stroke();

    oCtx.setLineDash([]);
    for (const [px, py, col] of [
      [s[0], s[1], '#4ADE80'],
      [s[2], s[3], '#F5C438'],
      [s[4], s[5], '#58A6FF'],
    ]) {
      oCtx.fillStyle = col;
      oCtx.beginPath();
      oCtx.arc(px, py, 3.6, 0, Math.PI * 2);
      oCtx.fill();
    }
    oCtx.restore();
  }

  // ==========================================================================
  // 5. SYNCHRONIZED HUD TELEMETRY, SWIMLANES & GIT COMMIT STREAM
  // ==========================================================================

  function updateSimulationByStrokeCursor(newCursor, forceRender = false) {
    state.strokeCursor = Math.min(TOTAL_STROKES, Math.max(0, newCursor));
    const strokeIdx = Math.round(state.strokeCursor);
    const phase = getPhaseDescriptor(strokeIdx);

    // 1. Update Scrubber & Clock
    dom.scrubber.value = strokeIdx;
    const mm = String(Math.floor(phase.simSec / 60)).padStart(2, '0');
    const ss = String(phase.simSec % 60).padStart(2, '0');
    dom.clockCurrent.textContent = `${mm}:${ss}`;

    // 2. Update Canvas Phase Pill
    dom.phaseText.textContent = phase.label;
    dom.phaseIndicator.style.background = phase.dotColor;
    dom.phaseIndicator.style.boxShadow = `0 0 8px ${phase.dotColor}`;

    // 3. Compute Live Telemetry (Strokes, SSIM, Mean DeltaE, PSNR)
    let curSsim = 0.6951;
    let curDeltaE = 11.83;
    let curPsnr = 20.95;

    if (phase.act === 'v1') {
      curSsim = 0.14 + (0.6951 - 0.14) * phase.frac1;
      curDeltaE = 24.5 - (24.5 - 11.83) * phase.frac1;
      curPsnr = 14.2 + (20.95 - 14.2) * phase.frac1;
    } else if (phase.act === 'critique') {
      curSsim = 0.6951;
      curDeltaE = 11.83;
      curPsnr = 20.95;
    } else {
      curSsim = 0.6951 + (0.9138 - 0.6951) * phase.frac2;
      curDeltaE = 11.83 - (11.83 - 3.16) * phase.frac2;
      curPsnr = 20.95 + (30.79 - 20.95) * phase.frac2;
    }

    dom.hudStrokes.textContent = `${strokeIdx.toLocaleString()} / ${TOTAL_STROKES.toLocaleString()}`;
    dom.hudSsim.textContent = curSsim.toFixed(4);
    dom.hudDeltaE.textContent = curDeltaE.toFixed(2);
    dom.hudPsnr.textContent = `${curPsnr.toFixed(2)} dB`;

    // 4. Highlight Active Commit Tick & Stream Card
    const activeCommitNum = getActiveCommitNum(phase.simSec);
    dom.commitTicksRow.querySelectorAll('.commit-tick-btn').forEach((btn) => {
      btn.classList.toggle('active', Number(btn.dataset.commit) === activeCommitNum);
    });
    dom.activityStreamList.querySelectorAll('.stream-card').forEach((card) => {
      card.classList.toggle('active-event', Number(card.dataset.commitNum) === activeCommitNum);
    });

    // 5. Update Subagent Swimlanes
    updateSwimlaneRows(phase);

    // 6. Keep bottom Stroke Inspector populated if user is not hovering
    if (!state.hoveredStroke && !state.lockedStroke) {
      const sampleStroke =
        state.agentCursors[1]?.activeStroke ||
        state.data.strokesV2[Math.min(state.data.strokesV2.length - 1, Math.max(0, strokeIdx - 1))];
      if (sampleStroke) {
        sampleStroke._displayIndex = Math.max(1, strokeIdx);
        updateInspectorBar(sampleStroke, false);
      }
    }

    // 7. Render Stage Canvas
    if (state.mode !== 'rework' || forceRender) {
      renderMainStage();
    }
  }

  function getActiveCommitNum(simSec) {
    let active = 1;
    for (const c of state.data.commits) {
      if (simSec >= c.timeSec) {
        active = c.num;
      }
    }
    return active;
  }

  function simSecToStrokeCursor(simSec) {
    const p1Count = state.data.pass1Count; // 4697
    if (simSec <= 495) {
      return Math.round((simSec / 495) * p1Count);
    } else if (simSec <= 565) {
      return p1Count;
    } else {
      const frac2 = Math.min(1, (simSec - 565) / (1200 - 565));
      return Math.round(p1Count + frac2 * (TOTAL_STROKES - p1Count));
    }
  }

  // ==========================================================================
  // 6. UI BUILDERS (COMMIT TICKS, SWIMLANES, GIT STREAM, REWORK DIFF)
  // ==========================================================================

  function buildCommitTicks() {
    dom.commitTicksRow.innerHTML = '';
    for (const c of state.data.commits) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'commit-tick-btn';
      if (c.type === 'qa_critique') btn.classList.add('tick-critique');
      if (c.type === 'v2_rework' || c.type === 'merge' || c.type === 'release') {
        btn.classList.add('tick-rework');
      }
      btn.dataset.commit = c.num;
      btn.title = `Commit #${String(c.num).padStart(2, '0')} (${c.time}) · ${c.short}: ${c.title}`;
      btn.textContent = `#${String(c.num).padStart(2, '0')}`;
      btn.addEventListener('click', () => {
        state.isPlaying = false;
        syncPlayButtonUI();
        updateSimulationByStrokeCursor(simSecToStrokeCursor(c.timeSec + 5), true);
      });
      dom.commitTicksRow.appendChild(btn);
    }
  }

  function buildSwimlaneRows() {
    dom.swimlaneList.innerHTML = '';
    for (const ag of state.data.agents) {
      const row = document.createElement('div');
      row.className = 'swimlane-row';
      row.id = `swim-row-${ag.id}`;
      row.style.setProperty('--ag-color', ag.color);

      row.innerHTML = `
        <div class="swim-agent-info">
          <span class="ag-dot" style="--ag-color: ${ag.color}"></span>
          <div class="swim-agent-text">
            <span class="swim-agent-title">${ag.code} · ${ag.shortName}</span>
            <span class="swim-agent-model">${ag.model}</span>
          </div>
        </div>
        <div class="swim-progress-col">
          <div class="swim-status-line">
            <span class="swim-status-badge" id="swim-status-${ag.id}">v2 Merged</span>
            <span class="pill-num" id="swim-metrics-${ag.id}">ΔE ${ag.deltaEV2.toFixed(2)} · ${ag.strokesV2.toLocaleString()}</span>
          </div>
          <div class="swim-bar-track">
            <div class="swim-bar-fill" id="swim-bar-${ag.id}" style="width: 100%; --ag-color: ${ag.color}"></div>
          </div>
        </div>
        <div class="swim-actions-col">
          <button type="button" class="swim-mini-btn" data-solo-btn="${ag.id}" title="Solo this subagent layer on canvas">Solo</button>
          <button type="button" class="swim-mini-btn" data-diff-btn="${ag.id}" title="Inspect Before vs. After Computer Critique">Diff</button>
        </div>
      `;
      dom.swimlaneList.appendChild(row);
    }

    dom.swimlaneList.querySelectorAll('[data-solo-btn]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const agId = Number(btn.dataset.soloBtn);
        setSoloAgent(state.soloAgent === agId ? 0 : agId);
      });
    });

    dom.swimlaneList.querySelectorAll('[data-diff-btn]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const agId = Number(btn.dataset.diffBtn);
        selectReworkAgent(agId);
        setMode('rework');
      });
    });
  }

  function updateSwimlaneRows(phase) {
    for (const ag of state.data.agents) {
      const id = ag.id;
      const row = document.getElementById(`swim-row-${id}`);
      const statusEl = document.getElementById(`swim-status-${id}`);
      const metricsEl = document.getElementById(`swim-metrics-${id}`);
      const barEl = document.getElementById(`swim-bar-${id}`);
      if (!row || !statusEl || !metricsEl || !barEl) continue;

      row.classList.remove('state-critique', 'state-merged');
      statusEl.className = 'swim-status-badge';

      if (phase.act === 'v1') {
        const cnt = Math.round(ag.strokesV1 * phase.frac1);
        statusEl.textContent = 'Pass 1 (v1)';
        statusEl.classList.add('status-blue');
        metricsEl.textContent = `ΔE ${ag.deltaEV1.toFixed(1)} · ${cnt.toLocaleString()} strk`;
        barEl.style.width = `${Math.round(phase.frac1 * 40)}%`;
      } else if (phase.act === 'critique') {
        row.classList.add('state-critique');
        statusEl.textContent = 'QA Critique: Rework';
        statusEl.classList.add('status-amber');
        metricsEl.textContent = `ΔE ${ag.deltaEV1.toFixed(1)} → Target <4.0`;
        barEl.style.width = '42%';
      } else if (phase.act === 'v2') {
        const cnt = Math.round(ag.strokesV1 + (ag.strokesV2 - ag.strokesV1) * phase.frac2);
        const de = ag.deltaEV1 - (ag.deltaEV1 - ag.deltaEV2) * phase.frac2;
        statusEl.textContent = `Rework (${ag.reworkGainLabel})`;
        statusEl.classList.add('status-emerald');
        metricsEl.textContent = `ΔE ${de.toFixed(2)} · ${cnt.toLocaleString()}`;
        barEl.style.width = `${Math.round(42 + phase.frac2 * 58)}%`;
      } else {
        row.classList.add('state-merged');
        statusEl.textContent = `Merged (${ag.reworkGainLabel})`;
        statusEl.classList.add('status-emerald');
        metricsEl.textContent = `ΔE ${ag.deltaEV2.toFixed(2)} · ${ag.strokesV2.toLocaleString()}`;
        barEl.style.width = '100%';
      }
    }
  }

  function buildActivityStream() {
    dom.activityStreamList.innerHTML = '';

    for (const c of state.data.commits) {
      if (state.streamFilter === 'critique' && c.type !== 'qa_critique') continue;

      const card = document.createElement('article');
      card.className = 'stream-card';
      if (c.type === 'qa_critique') card.classList.add('card-critique');
      card.dataset.commitNum = c.num;

      // Match agent for commits #02..#16
      let ag = null;
      if (c.num >= 2 && c.num <= 6) ag = state.agentMap[c.num - 1];
      else if (c.num >= 7 && c.num <= 11) ag = state.agentMap[c.num - 6];
      else if (c.num >= 12 && c.num <= 16) ag = state.agentMap[c.num - 11];

      const dotColor =
        c.type === 'qa_critique' ? '#FB923C' : ag ? ag.color : '#F5C438';
      const actorHeader = ag
        ? `${ag.code} · ${ag.shortName} (${ag.model})`
        : `Orchestrator · Perplexity Computer (${c.model})`;

      let bodyText = c.title;
      let diffHtml = '';

      if (c.type === 'qa_critique' && ag) {
        bodyText = `QA REJECTION (v1 SSIM ${ag.ssimV1.toFixed(3)}, ΔE ${ag.deltaEV1.toFixed(2)}): "${ag.computerCritique}"`;
      } else if (c.type === 'v2_rework' && ag) {
        bodyText = ag.v2Fix;
        diffHtml = `
          <div class="stream-diff-thumbs">
            <div class="thumb-pair-item">
              <img src="assets/diffs/agent0${ag.id}_v1.jpg" alt="${ag.code} v1 crop" loading="lazy" />
              <span class="thumb-tag thumb-v1">v1 · ΔE ${ag.deltaEV1.toFixed(1)}</span>
            </div>
            <div class="thumb-pair-item">
              <img src="assets/diffs/agent0${ag.id}_v2.jpg" alt="${ag.code} v2 crop" loading="lazy" />
              <span class="thumb-tag thumb-v2">v2 · ΔE ${ag.deltaEV2.toFixed(1)}</span>
            </div>
            <button type="button" class="btn-open-diff" data-open-rework="${ag.id}">Inspect Diff</button>
          </div>
        `;
      }

      const commitHref =
        c.short === 'v1.0.0'
          ? `${GITHUB_REPO_URL}/releases/tag/v1.0.0`
          : `${GITHUB_REPO_URL}/commit/${c.short}`;

      card.innerHTML = `
        <div class="stream-card-top">
          <span class="stream-actor">
            <span class="ag-dot" style="--ag-color: ${dotColor}"></span>
            <span>#${String(c.num).padStart(2, '0')} · ${actorHeader}</span>
          </span>
          <span style="display: inline-flex; align-items: center; gap: 6px;">
            <span class="stream-time">${c.time}</span>
            <a class="commit-sha-pill" href="${commitHref}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">${c.short} ↗</a>
          </span>
        </div>
        <p class="stream-msg">${bodyText}</p>
        ${diffHtml}
      `;

      card.addEventListener('click', () => {
        state.isPlaying = false;
        syncPlayButtonUI();
        updateSimulationByStrokeCursor(simSecToStrokeCursor(c.timeSec + 5), true);
      });

      dom.activityStreamList.appendChild(card);
    }

    dom.activityStreamList.querySelectorAll('[data-open-rework]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const agId = Number(btn.dataset.openRework);
        selectReworkAgent(agId);
        setMode('rework');
      });
    });
  }

  // ==========================================================================
  // 7. REWORK DIFF INSPECTOR (BEFORE vs. AFTER COMPUTER'S CRITIQUE)
  // ==========================================================================

  function selectReworkAgent(agentId) {
    state.selectedReworkAgent = agentId;
    const ag = state.agentMap[agentId];
    if (!ag) return;

    document.querySelectorAll('.rework-agent-btn').forEach((btn) => {
      btn.classList.toggle('active', Number(btn.dataset.reworkAgent) === agentId);
    });

    dom.reworkV1Stat.textContent = `${ag.strokesV1.toLocaleString()} strokes · SSIM ${ag.ssimV1.toFixed(4)} · ΔE ${ag.deltaEV1.toFixed(2)}`;
    dom.reworkV2Stat.textContent = `${ag.strokesV2.toLocaleString()} strokes · SSIM ${ag.ssimV2.toFixed(4)} · ΔE ${ag.deltaEV2.toFixed(2)}`;
    dom.reworkRefStat.textContent = ag.cropTitle;

    dom.reworkImgV1.src = `assets/diffs/agent0${ag.id}_v1.jpg`;
    dom.reworkImgV2.src = `assets/diffs/agent0${ag.id}_v2.jpg`;
    dom.reworkImgRef.src = `assets/diffs/agent0${ag.id}_ref.jpg`;

    dom.reworkV1Flaw.textContent = `Pass 1 (v1) Flaw: ${ag.v1Flaw}`;
    dom.reworkV2Fix.textContent = `Pass 2 (v2) Rework: ${ag.v2Fix}`;
    dom.reworkCritiqueNote.textContent = `Computer Critique (${ag.commitReview}): "${ag.computerCritique}"`;

    const reworkCommitNum = 11 + ag.id;
    dom.reworkCodeTitle.textContent = `${ag.code} (${ag.model}) — Brushstroke Synthesizer Parameter Diff (v1 → v2)`;
    dom.reworkCommitLink.textContent = `Commit #${reworkCommitNum} · ${ag.commitV2} ↗`;
    dom.reworkCommitLink.href = `${GITHUB_REPO_URL}/commit/${ag.commitV2}`;

    dom.reworkCodeV1.textContent = ag.codeDiff.v1;
    dom.reworkCodeV2.textContent = ag.codeDiff.v2;
  }

  // ==========================================================================
  // 8. HOVER ANY BRUSHSTROKE -> VIEW CODE & GIT COMMIT INSPECTOR
  // ==========================================================================

  function findNearestStroke(mx, my) {
    if (!state.data) return null;
    const strokeIdx = Math.round(state.strokeCursor);
    const p1Count = state.data.pass1Count;
    const pool = strokeIdx <= p1Count ? state.data.strokesV1 : state.data.strokesV2;
    const maxIdx = Math.min(pool.length, Math.max(200, strokeIdx));

    let bestStroke = null;
    let bestDistSq = 900; // within 30px
    let bestIndex = -1;

    for (let i = maxIdx - 1; i >= 0; i--) {
      const s = pool[i];
      if (state.soloAgent !== 0 && s[10] !== state.soloAgent) continue;

      const midX = 0.25 * s[0] + 0.5 * s[2] + 0.25 * s[4];
      const midY = 0.25 * s[1] + 0.5 * s[3] + 0.25 * s[5];
      const dx = mx - midX;
      const dy = my - midY;
      const dSq = dx * dx + dy * dy;
      if (dSq < bestDistSq) {
        bestDistSq = dSq;
        bestStroke = s;
        bestIndex = i + 1;
        if (dSq < 16) break;
      }
    }

    if (!bestStroke) return null;
    bestStroke._displayIndex = bestIndex;
    return bestStroke;
  }

  function updateInspectorBar(s, isPinned) {
    if (!s || !state.data) return;
    const ag = state.agentMap[s[10]] || state.data.agents[0];
    const passNum = s[11];
    const commitNum = Math.min(18, Math.max(1, s[12]));
    const commitObj = state.data.commits[commitNum - 1] || state.data.commits[11];
    const hex = rgbToHex(s[7], s[8], s[9]);
    const deg = ((s[14] * 180) / Math.PI).toFixed(1);

    dom.inspSwatch.style.background = `rgb(${s[7]}, ${s[8]}, ${s[9]})`;
    dom.inspStrokeId.textContent = `${isPinned ? 'Pinned ' : ''}Stroke #${(s._displayIndex || 14820).toLocaleString()}`;
    dom.inspAgentBadge.textContent = `${ag.code} · ${ag.model}`;
    dom.inspAgentBadge.style.setProperty('--ag-color', ag.color);
    dom.inspPassBadge.textContent =
      passNum === 2 ? 'Pass 2 · Critique Rework' : 'Pass 1 · Initial v1';

    dom.inspCommitLink.textContent = `Commit #${String(commitObj.num).padStart(2, '0')} · ${commitObj.short} ↗`;
    dom.inspCommitLink.href = `${GITHUB_REPO_URL}/commit/${commitObj.short}`;

    dom.inspGeomLine.textContent = `Quadratic Bézier (${s[0].toFixed(1)}, ${s[1].toFixed(1)}) → (${s[2].toFixed(1)}, ${s[3].toFixed(1)}) → (${s[4].toFixed(1)}, ${s[5].toFixed(1)}) · Width: ${s[6].toFixed(1)}px · Angle: ${deg}° · Hex: ${hex}`;
    dom.inspCodeSnippet.textContent = `ctx.moveTo(${s[0].toFixed(1)}, ${s[1].toFixed(1)}); ctx.quadraticCurveTo(${s[2].toFixed(1)}, ${s[3].toFixed(1)}, ${s[4].toFixed(1)}, ${s[5].toFixed(1)}); // w=${s[6].toFixed(1)}px ${hex}`;
  }

  // ==========================================================================
  // 9. INTERACTION & EVENT BINDINGS
  // ==========================================================================

  function setMode(newMode) {
    state.mode = newMode;
    document.querySelectorAll('.mode-tab').forEach((tab) => {
      const isMatch = tab.dataset.mode === newMode;
      tab.classList.toggle('active', isMatch);
      tab.setAttribute('aria-selected', isMatch ? 'true' : 'false');
    });

    const isRework = newMode === 'rework';
    dom.canvasWrapper.hidden = isRework;
    dom.reworkView.hidden = !isRework;
    dom.curtainOverlay.hidden = newMode !== 'curtain';

    state.lastRenderedKey = '';
    if (!isRework) {
      renderMainStage();
    }
  }

  function setSoloAgent(agentId) {
    state.soloAgent = agentId;
    document.querySelectorAll('.solo-pill').forEach((pill) => {
      pill.classList.toggle('active', Number(pill.dataset.solo) === agentId);
    });
    document.querySelectorAll('[data-solo-btn]').forEach((btn) => {
      btn.classList.toggle('active', Number(btn.dataset.soloBtn) === agentId);
    });
    state.lastRenderedKey = '';
    renderMainStage();
  }

  function syncPlayButtonUI() {
    if (state.isPlaying) {
      dom.playIcon.textContent = '⏸';
      dom.playLabel.textContent = 'Pause';
    } else {
      dom.playIcon.textContent = '▶';
      dom.playLabel.textContent = 'Play';
    }
  }

  function bindEvents() {
    // 1. Mode Tabs
    document.querySelectorAll('.mode-tab').forEach((tab) => {
      tab.addEventListener('click', () => setMode(tab.dataset.mode));
    });

    // 2. Per-Agent Layer Solo Pills
    document.querySelectorAll('.solo-pill').forEach((pill) => {
      pill.addEventListener('click', () => setSoloAgent(Number(pill.dataset.solo)));
    });

    // 3. Stage Toolbar Toggles (Cursors, Region Map, 3D Impasto Relief, Light Azimuth)
    dom.btnToggleCursors.addEventListener('click', () => {
      state.showCursors = !state.showCursors;
      dom.btnToggleCursors.classList.toggle('active', state.showCursors);
      dom.btnToggleCursors.setAttribute('aria-pressed', String(state.showCursors));
      renderMainStage();
    });

    dom.btnToggleRegions.addEventListener('click', () => {
      state.showRegions = !state.showRegions;
      dom.btnToggleRegions.classList.toggle('active', state.showRegions);
      dom.btnToggleRegions.setAttribute('aria-pressed', String(state.showRegions));
      renderMainStage();
    });

    dom.btnToggleImpasto.addEventListener('click', () => {
      state.impastoRelief = !state.impastoRelief;
      dom.btnToggleImpasto.classList.toggle('active', state.impastoRelief);
      dom.btnToggleImpasto.setAttribute('aria-pressed', String(state.impastoRelief));
      state.lastRenderedKey = '';
      renderMainStage();
    });

    dom.inputRakingAngle.addEventListener('input', () => {
      state.rakingAzimuthDeg = Number(dom.inputRakingAngle.value);
      dom.rakingDegVal.textContent = `${state.rakingAzimuthDeg}°`;
      state.lastRenderedKey = '';
      renderMainStage();
    });

    // 4. Split-Curtain Dragging & Pair Switch
    let draggingCurtain = false;
    const updateCurtainFromClientX = (clientX) => {
      const rect = dom.overlay.getBoundingClientRect();
      const rel = (clientX - rect.left) / Math.max(1, rect.width);
      state.curtainPos = Math.min(0.95, Math.max(0.05, rel));
      dom.curtainHandle.style.left = `${(state.curtainPos * 100).toFixed(1)}%`;
      dom.curtainHandle.setAttribute('aria-valuenow', String(Math.round(state.curtainPos * 100)));
      renderMainStage();
    };

    dom.curtainHandle.addEventListener('pointerdown', (e) => {
      draggingCurtain = true;
      dom.curtainHandle.setPointerCapture(e.pointerId);
      e.stopPropagation();
    });

    window.addEventListener('pointermove', (e) => {
      if (draggingCurtain) updateCurtainFromClientX(e.clientX);
    });

    window.addEventListener('pointerup', () => {
      draggingCurtain = false;
    });

    document.querySelectorAll('.curtain-sub-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.curtainPair = btn.dataset.curtainPair;
        document.querySelectorAll('.curtain-sub-btn').forEach((b) => {
          b.classList.toggle('active', b === btn);
        });
        dom.curtainLeftLabel.textContent =
          state.curtainPair === 'ref_vs_v2'
            ? '1889 MoMA Public-Domain Reference'
            : 'Pass 1 Pre-Critique Canvas (v1 · 4,697 Strokes · SSIM 0.6951)';
        renderMainStage();
      });
    });

    // 5. Rework Diff Agent Selector Buttons
    document.querySelectorAll('.rework-agent-btn').forEach((btn) => {
      btn.addEventListener('click', () => selectReworkAgent(Number(btn.dataset.reworkAgent)));
    });

    // 6. Canvas Brushstroke Hover & Click-to-Pin
    dom.overlay.addEventListener('pointermove', (e) => {
      if (draggingCurtain) return;
      const rect = dom.overlay.getBoundingClientRect();
      const mx = ((e.clientX - rect.left) / Math.max(1, rect.width)) * 1000;
      const my = ((e.clientY - rect.top) / Math.max(1, rect.height)) * 792;

      const nearest = findNearestStroke(mx, my);
      state.hoveredStroke = nearest;
      if (!state.lockedStroke && nearest) {
        updateInspectorBar(nearest, false);
      }
      renderStageOverlay(getPhaseDescriptor(Math.round(state.strokeCursor)));
    });

    dom.overlay.addEventListener('pointerleave', () => {
      state.hoveredStroke = null;
      renderStageOverlay(getPhaseDescriptor(Math.round(state.strokeCursor)));
    });

    dom.overlay.addEventListener('click', (e) => {
      if (state.mode === 'curtain') {
        updateCurtainFromClientX(e.clientX);
        return;
      }
      if (state.lockedStroke) {
        state.lockedStroke = null;
      } else if (state.hoveredStroke) {
        state.lockedStroke = state.hoveredStroke;
        updateInspectorBar(state.lockedStroke, true);
      }
      renderStageOverlay(getPhaseDescriptor(Math.round(state.strokeCursor)));
    });

    // 7. Transport Controls & Timeline Scrubber
    dom.btnPlayPause.addEventListener('click', () => {
      if (state.strokeCursor >= TOTAL_STROKES - 10) {
        state.strokeCursor = 350;
      }
      state.isPlaying = !state.isPlaying;
      syncPlayButtonUI();
    });

    dom.btnRestart.addEventListener('click', () => {
      if (state.mode === 'rework') setMode('painting');
      state.isPlaying = true;
      syncPlayButtonUI();
      updateSimulationByStrokeCursor(350, true);
    });

    dom.btnJumpCritique.addEventListener('click', () => {
      if (state.mode === 'rework') setMode('painting');
      state.isPlaying = false;
      syncPlayButtonUI();
      updateSimulationByStrokeCursor(state.data.pass1Count, true);
    });

    dom.btnJumpFinal.addEventListener('click', () => {
      if (state.mode === 'rework') setMode('painting');
      state.isPlaying = false;
      syncPlayButtonUI();
      updateSimulationByStrokeCursor(TOTAL_STROKES, true);
    });

    dom.scrubber.addEventListener('input', () => {
      state.isPlaying = false;
      syncPlayButtonUI();
      updateSimulationByStrokeCursor(Number(dom.scrubber.value), true);
    });

    document.querySelectorAll('.speed-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.speed = Number(btn.dataset.speed);
        document.querySelectorAll('.speed-btn').forEach((b) => {
          b.classList.toggle('active', b === btn);
        });
      });
    });

    // 8. Stream Filter Buttons
    document.querySelectorAll('.stream-filter-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.streamFilter = btn.dataset.filter;
        document.querySelectorAll('.stream-filter-btn').forEach((b) => {
          b.classList.toggle('active', b === btn);
        });
        buildActivityStream();
      });
    });
  }

  // ==========================================================================
  // 10. MAIN 60FPS ANIMATION LOOP
  // ==========================================================================

  function animationLoop(now) {
    const dt = Math.min(0.1, (now - state.lastFrameTime) / 1000);
    state.lastFrameTime = now;

    if (state.isPlaying && state.data) {
      // Base rate: 160 strokes/sec at 1x -> 640 strokes/sec at 4x
      const deltaStrokes = dt * 160 * state.speed;
      const nextCursor = state.strokeCursor + deltaStrokes;
      if (nextCursor >= TOTAL_STROKES) {
        updateSimulationByStrokeCursor(TOTAL_STROKES);
        state.isPlaying = false;
        syncPlayButtonUI();
      } else {
        updateSimulationByStrokeCursor(nextCursor);
      }
    }

    requestAnimationFrame(animationLoop);
  }

  // Expose programmatic API for automated verification & showcase video choreography
  window.__ATELIER__ = {
    state,
    setMode,
    setSoloAgent,
    selectReworkAgent,
    setStrokeCursor: (idx, play = false) => {
      state.isPlaying = play;
      syncPlayButtonUI();
      updateSimulationByStrokeCursor(idx, true);
    },
    setCurtain: (pos, pair = 'ref_vs_v2') => {
      state.curtainPair = pair;
      state.curtainPos = pos;
      dom.curtainHandle.style.left = `${(pos * 100).toFixed(1)}%`;
      document.querySelectorAll('.curtain-sub-btn').forEach((b) => {
        b.classList.toggle('active', b.dataset.curtainPair === pair);
      });
      dom.curtainLeftLabel.textContent =
        pair === 'ref_vs_v2'
          ? '1889 MoMA Public-Domain Reference'
          : 'Pass 1 Pre-Critique Canvas (v1 · 4,697 Strokes · SSIM 0.6951)';
      renderMainStage();
    },
    setRegionsVisible: (vis) => {
      state.showRegions = vis;
      dom.btnToggleRegions.classList.toggle('active', vis);
      dom.btnToggleRegions.setAttribute('aria-pressed', String(vis));
      renderMainStage();
    },
    hoverStrokeAt: (mx, my) => {
      const s = findNearestStroke(mx, my);
      if (s) {
        state.lockedStroke = s;
        updateInspectorBar(s, true);
        renderStageOverlay(getPhaseDescriptor(Math.round(state.strokeCursor)));
      }
    },
  };

  init();
})();
