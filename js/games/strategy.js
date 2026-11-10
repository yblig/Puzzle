/* Game kategori STRATEGI (melawan komputer) */
"use strict";

/* ================= TIC TAC TOE ================= */
registerGame({
  id: "tictactoe",
  name: "Tic Tac Toe",
  icon: "❌",
  cat: "strategi",
  color: ["#ff416c", "#ff4b2b"],
  desc: "Kalahkan komputer di X dan O.",
  help: "Kamu bermain sebagai ❌, komputer sebagai ⭕. Giliran bergantian. Yang pertama membuat 3 simbol berderet (mendatar, menurun, atau diagonal) menang!\n\nDi level Sulit, komputer bermain sempurna — bisakah kamu memaksakan seri?",
  init(root, api) {
    const lvl = api.pref("lvl", "sedang");
    const b = Array(9).fill("");
    const L = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
    let over = false, busy = false;
    const score = Store.get("ttt_score", { w: 0, l: 0, d: 0 });
    const winner = (g) => { for (const l of L) if (g[l[0]] && g[l[0]] === g[l[1]] && g[l[1]] === g[l[2]]) return { p: g[l[0]], l }; return g.every(Boolean) ? { p: "D" } : null; };
    function minimax(g, p) {
      const w = winner(g);
      if (w) return { s: w.p === "O" ? 10 : w.p === "X" ? -10 : 0 };
      let best = { s: p === "O" ? -99 : 99, i: -1 };
      for (let i = 0; i < 9; i++) if (!g[i]) {
        g[i] = p; const r = minimax(g, p === "O" ? "X" : "O"); g[i] = "";
        const s = r.s * 0.9;
        if (p === "O" ? s > best.s : s < best.s) best = { s, i };
      }
      return best;
    }
    const grid = h("div", { class: "ttt" });
    const cells = b.map((_, i) => { const el = h("button", { class: "cell", onclick: () => play(i) }); grid.append(el); return el; });
    const msg = h("div", { class: "big-q", style: { fontSize: "18px" } }, "Giliranmu ❌");
    function paint(win) {
      cells.forEach((el, i) => { el.textContent = b[i] === "X" ? "✕" : b[i] === "O" ? "◯" : ""; el.className = "cell " + b[i] + (win && win.includes(i) ? " win" : ""); });
      api.stats({ Menang: score.w, Seri: score.d, Kalah: score.l });
    }
    function end() {
      const w = winner(b); if (!w) return false;
      over = true; paint(w.l);
      if (w.p === "X") { score.w++; Store.set("ttt_score", score); api.win({ title: "Kamu Menang!", text: "Komputer terkalahkan!" }); }
      else if (w.p === "O") { score.l++; Store.set("ttt_score", score); api.lose({ title: "Komputer Menang", text: "Coba strategi lain!" }); }
      else { score.d++; Store.set("ttt_score", score); api.result({ icon: "🤝", title: "Seri!", text: "Pertandingan imbang.", good: lvl === "sulit" }); }
      return true;
    }
    function ai() {
      const empty = b.map((v, i) => (v ? -1 : i)).filter((i) => i >= 0);
      const rnd = lvl === "mudah" ? 0.7 : lvl === "sedang" ? 0.25 : 0;
      const i = Math.random() < rnd ? pick(empty) : minimax(b, "O").i;
      b[i] = "O"; api.sfx("pop"); paint();
      if (!end()) { msg.textContent = "Giliranmu ❌"; busy = false; }
    }
    function play(i) {
      if (over || busy || b[i]) return;
      b[i] = "X"; api.sfx("click"); paint();
      if (end()) return;
      busy = true; msg.textContent = "Komputer berpikir… 🤔";
      api.timeout(ai, 450);
    }
    root.append(api.seg([["mudah", "Mudah"], ["sedang", "Sedang"], ["sulit", "Sulit"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }), msg, grid);
    paint();
  },
});

/* ================= EMPAT SEBARIS (Connect Four) ================= */
registerGame({
  id: "empat-sebaris",
  name: "Empat Sebaris",
  icon: "🔴",
  cat: "strategi",
  color: ["#4776e6", "#8e54e9"],
  desc: "Jatuhkan koin, buat 4 berderet!",
  help: "Ketuk sebuah kolom untuk menjatuhkan koin kuningmu 🟡. Komputer bermain dengan koin merah 🔴. Yang pertama menyusun 4 koin berderet (mendatar, menurun, atau diagonal) menang!",
  init(root, api) {
    const lvl = api.pref("lvl", "sedang");
    const depth = { mudah: 1, sedang: 4, sulit: 6 }[lvl];
    const R = 6, C = 7;
    const b = Array.from({ length: R }, () => Array(C).fill(0));
    let over = false, busy = false, lastDrop = null;
    const drop = (g, c, p) => { for (let r = R - 1; r >= 0; r--) if (!g[r][c]) { g[r][c] = p; return r; } return -1; };
    function lines(g) {
      const out = [];
      for (let r = 0; r < R; r++) for (let c = 0; c < C; c++)
        for (const [dr, dc] of [[0, 1], [1, 0], [1, 1], [1, -1]]) {
          const rr = r + dr * 3, cc = c + dc * 3;
          if (rr < 0 || rr >= R || cc < 0 || cc >= C) continue;
          out.push([0, 1, 2, 3].map((k) => [r + dr * k, c + dc * k]));
        }
      return out;
    }
    const LINES = lines(b);
    const winLine = (g) => LINES.find((l) => { const v = g[l[0][0]][l[0][1]]; return v && l.every(([r, c]) => g[r][c] === v); });
    function evalBoard(g) {
      let s = 0;
      for (let r = 0; r < R; r++) if (g[r][3] === 2) s += 3; else if (g[r][3] === 1) s -= 3;
      for (const l of LINES) {
        let a = 0, h2 = 0;
        for (const [r, c] of l) { if (g[r][c] === 2) a++; else if (g[r][c] === 1) h2++; }
        if (a && h2) continue;
        if (a === 3) s += 5; else if (a === 2) s += 2;
        if (h2 === 3) s -= 6; else if (h2 === 2) s -= 2;
      }
      return s;
    }
    const valid = (g) => [3, 2, 4, 1, 5, 0, 6].filter((c) => !g[0][c]);
    function search(g, d, alpha, beta, max) {
      const w = winLine(g);
      if (w) return g[w[0][0]][w[0][1]] === 2 ? 100000 + d : -100000 - d;
      const vs = valid(g);
      if (!vs.length) return 0;
      if (d === 0) return evalBoard(g);
      if (max) {
        let v = -Infinity;
        for (const c of vs) { const r = drop(g, c, 2); v = Math.max(v, search(g, d - 1, alpha, beta, false)); g[r][c] = 0; alpha = Math.max(alpha, v); if (alpha >= beta) break; }
        return v;
      }
      let v = Infinity;
      for (const c of vs) { const r = drop(g, c, 1); v = Math.min(v, search(g, d - 1, alpha, beta, true)); g[r][c] = 0; beta = Math.min(beta, v); if (alpha >= beta) break; }
      return v;
    }
    function bestMove() {
      let best = -Infinity, bc = valid(b)[0];
      for (const c of valid(b)) {
        const r = drop(b, c, 2);
        const v = search(b, depth - 1, -Infinity, Infinity, false) + (lvl === "mudah" ? Math.random() * 8 : 0);
        b[r][c] = 0;
        if (v > best) { best = v; bc = c; }
      }
      return bc;
    }
    const board = h("div", { class: "c4" });
    const holes = [];
    for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) { const el = h("div", { class: "h", onclick: () => play(c) }); holes.push(el); board.append(el); }
    const msg = h("div", { class: "big-q", style: { fontSize: "18px" } }, "Giliranmu 🟡");
    function paint(win) {
      holes.forEach((el, i) => {
        const r = (i / C) | 0, c = i % C, v = b[r][c];
        const want = "h" + (v ? " p" + v : "") + (win && win.some(([rr, cc]) => rr === r && cc === c) ? " win" : "");
        if (el.className !== want) {
          // hanya animasikan koin yang baru jatuh
          el.className = want;
          if (!(lastDrop && lastDrop[0] === r && lastDrop[1] === c) && v) el.style.animation = "none";
        }
      });
    }
    function check() {
      const w = winLine(b);
      if (w) {
        over = true; paint(w);
        if (b[w[0][0]][w[0][1]] === 1) api.win({ title: "Empat Sebaris!", text: "Kamu mengalahkan komputer!" });
        else api.lose({ title: "Komputer Menang", text: "Komputer berhasil menyusun 4 koin." });
        return true;
      }
      if (!valid(b).length) { over = true; api.result({ icon: "🤝", title: "Seri!", text: "Papan penuh.", good: false }); return true; }
      return false;
    }
    function play(c) {
      if (over || busy) return;
      const r = drop(b, c, 1);
      if (r < 0) return;
      lastDrop = [r, c]; api.sfx("pop"); paint();
      if (check()) return;
      busy = true; msg.textContent = "Komputer berpikir… 🤔";
      api.timeout(() => {
        const cc = bestMove();
        const rr = drop(b, cc, 2); lastDrop = [rr, cc]; api.sfx("click"); paint();
        busy = false; msg.textContent = "Giliranmu 🟡";
        check();
      }, 400);
    }
    root.append(api.seg([["mudah", "Mudah"], ["sedang", "Sedang"], ["sulit", "Sulit"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }), msg, board);
    paint();
  },
});

/* ================= REVERSI ================= */
registerGame({
  id: "reversi",
  name: "Reversi",
  icon: "⚫",
  cat: "strategi",
  color: ["#134e5e", "#71b280"],
  desc: "Balik keping lawan, kuasai papan.",
  help: "Kamu bermain ⚫ hitam, komputer ⚪ putih. Letakkan keping sehingga mengapit keping lawan dalam garis lurus (mendatar, menurun, diagonal) — keping yang terapit akan berbalik menjadi milikmu.\n\nTitik kecil menunjukkan langkah yang sah. Pemilik keping terbanyak saat papan penuh menang!",
  init(root, api) {
    const lvl = api.pref("lvl", "sedang");
    const N = 8;
    const b = Array(N * N).fill(0);
    b[27] = 2; b[28] = 1; b[35] = 1; b[36] = 2;
    const W = [
      100, -20, 10, 5, 5, 10, -20, 100, -20, -50, -2, -2, -2, -2, -50, -20, 10, -2, 1, 1, 1, 1, -2, 10, 5, -2, 1, 0, 0, 1, -2, 5,
      5, -2, 1, 0, 0, 1, -2, 5, 10, -2, 1, 1, 1, 1, -2, 10, -20, -50, -2, -2, -2, -2, -50, -20, 100, -20, 10, 5, 5, 10, -20, 100,
    ];
    let turn = 1, over = false, busy = false;
    const DIRS = [[0, 1], [1, 0], [0, -1], [-1, 0], [1, 1], [1, -1], [-1, 1], [-1, -1]];
    function flips(g, i, p) {
      if (g[i]) return [];
      const r = (i / N) | 0, c = i % N, out = [];
      for (const [dr, dc] of DIRS) {
        const line = []; let rr = r + dr, cc = c + dc;
        while (rr >= 0 && rr < N && cc >= 0 && cc < N && g[rr * N + cc] === 3 - p) { line.push(rr * N + cc); rr += dr; cc += dc; }
        if (line.length && rr >= 0 && rr < N && cc >= 0 && cc < N && g[rr * N + cc] === p) out.push(...line);
      }
      return out;
    }
    const moves = (g, p) => g.map((_, i) => i).filter((i) => flips(g, i, p).length);
    const apply = (g, i, p) => { const f = flips(g, i, p); g[i] = p; f.forEach((k) => (g[k] = p)); return f; };
    const evalG = (g) => g.reduce((s, v, i) => s + (v === 2 ? W[i] : v === 1 ? -W[i] : 0), 0) + (moves(g, 2).length - moves(g, 1).length) * 3;
    function aiMove() {
      const ms = moves(b, 2);
      if (lvl === "mudah") return Math.random() < 0.5 ? pick(ms) : ms.reduce((a, m) => (flips(b, m, 2).length > flips(b, a, 2).length ? m : a), ms[0]);
      let best = -Infinity, bm = ms[0];
      for (const m of ms) {
        const g = b.slice(); apply(g, m, 2);
        let v;
        const opp = moves(g, 1);
        if (lvl === "sedang" || !opp.length) v = evalG(g);
        else {
          v = Infinity;
          for (const o of opp) { const g2 = g.slice(); apply(g2, o, 1); v = Math.min(v, evalG(g2)); }
        }
        if (v > best) { best = v; bm = m; }
      }
      return bm;
    }
    const board = h("div", { class: "rv" });
    const sq = b.map((_, i) => { const el = h("div", { class: "q", onclick: () => play(i) }, h("div", { class: "d" })); board.append(el); return el; });
    const msg = h("div", { class: "big-q", style: { fontSize: "18px" } });
    function paint() {
      const mv = turn === 1 && !over ? new Set(moves(b, 1)) : new Set();
      sq.forEach((el, i) => {
        el.firstChild.className = "d" + (b[i] === 1 ? " b" : b[i] === 2 ? " w" : "");
        el.firstChild.style.visibility = b[i] ? "visible" : "hidden";
        el.classList.toggle("mv", mv.has(i));
      });
      api.stats({ "⚫ Kamu": b.filter((v) => v === 1).length, "⚪ Komputer": b.filter((v) => v === 2).length });
    }
    function finish() {
      over = true; paint();
      const me = b.filter((v) => v === 1).length, ai = b.filter((v) => v === 2).length;
      if (me > ai) api.win({ title: "Kamu Menang!", text: `${me} vs ${ai}` });
      else if (me < ai) api.lose({ title: "Komputer Menang", text: `${me} vs ${ai}` });
      else api.result({ icon: "🤝", title: "Seri!", text: `${me} vs ${ai}`, good: false });
    }
    function nextTurn() {
      const mine = moves(b, 1).length, theirs = moves(b, 2).length;
      if (!mine && !theirs) { finish(); return; }
      if (turn === 2) {
        if (!theirs) { turn = 1; toast("Komputer tidak bisa jalan — giliranmu lagi"); msg.textContent = "Giliranmu ⚫"; paint(); return; }
        busy = true; msg.textContent = "Komputer berpikir… 🤔"; paint();
        api.timeout(() => { apply(b, aiMove(), 2); api.sfx("flip"); busy = false; turn = 1; nextTurn(); }, 550);
      } else {
        if (!mine) { toast("Kamu tidak punya langkah — lewati"); turn = 2; nextTurn(); return; }
        msg.textContent = "Giliranmu ⚫"; paint();
      }
    }
    function play(i) {
      if (over || busy || turn !== 1) return;
      if (!flips(b, i, 1).length) { api.sfx("bad"); return; }
      apply(b, i, 1); api.sfx("flip"); turn = 2; paint(); nextTurn();
    }
    root.append(api.seg([["mudah", "Mudah"], ["sedang", "Sedang"], ["sulit", "Sulit"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }), msg, board);
    nextTurn();
  },
});
