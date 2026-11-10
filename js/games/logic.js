/* Game kategori LOGIKA */
"use strict";

/* ================= SUDOKU ================= */
function sdCands(g, i) {
  const r = (i / 9) | 0, c = i % 9, used = new Array(10).fill(false);
  for (let k = 0; k < 9; k++) { used[g[r * 9 + k]] = true; used[g[k * 9 + c]] = true; }
  const br = r - (r % 3), bc = c - (c % 3);
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) used[g[(br + a) * 9 + bc + b]] = true;
  const out = [];
  for (let n = 1; n <= 9; n++) if (!used[n]) out.push(n);
  return out;
}
function sdFill(g) {
  const i = g.indexOf(0);
  if (i < 0) return true;
  for (const n of shuffle(sdCands(g, i))) { g[i] = n; if (sdFill(g)) return true; }
  g[i] = 0; return false;
}
function sdCount(g, limit) {
  let best = -1, bc = null;
  for (let i = 0; i < 81; i++) if (g[i] === 0) {
    const cs = sdCands(g, i);
    if (!cs.length) return 0;
    if (!bc || cs.length < bc.length) { best = i; bc = cs; if (cs.length === 1) break; }
  }
  if (best < 0) return 1;
  let total = 0;
  for (const n of bc) { g[best] = n; total += sdCount(g, limit - total); if (total >= limit) break; }
  g[best] = 0; return total;
}
function sdGenerate(remove) {
  const sol = Array(81).fill(0); sdFill(sol);
  const puz = sol.slice();
  let removed = 0;
  for (const i of shuffle([...Array(81).keys()])) {
    if (removed >= remove) break;
    const v = puz[i]; puz[i] = 0;
    if (sdCount(puz.slice(), 2) !== 1) puz[i] = v; else removed++;
  }
  return { sol, puz };
}

registerGame({
  id: "sudoku",
  name: "Sudoku",
  icon: "🔢",
  cat: "logika",
  color: ["#5f2c82", "#49a09d"],
  desc: "Isi angka 1–9 tanpa ada yang kembar.",
  help: "Isi setiap kotak dengan angka 1–9 sehingga setiap BARIS, KOLOM, dan KOTAK 3×3 berisi angka 1–9 tanpa ada yang sama.\n\nKetuk kotak lalu pilih angka. Maksimal 3 kesalahan!",
  init(root, api) {
    const lvl = api.pref("lvl", "mudah");
    const { sol, puz } = sdGenerate({ mudah: 38, sedang: 48, sulit: 56 }[lvl]);
    const cur = puz.slice();
    let sel = -1, mistakes = 0, over = false, sec = 0;
    const board = h("div", { class: "sd" });
    const cells = [];
    for (let i = 0; i < 81; i++) {
      const r = (i / 9) | 0, c = i % 9;
      const el = h("div", { class: "c" + (puz[i] ? " given" : "") + (c % 3 === 2 && c < 8 ? " br" : "") + (r % 3 === 2 && r < 8 ? " bb" : ""), onclick: () => { sel = i; api.sfx("click"); paint(); } });
      cells.push(el); board.append(el);
    }
    function paint() {
      const sr = (sel / 9) | 0, sc = sel % 9;
      cells.forEach((el, i) => {
        const r = (i / 9) | 0, c = i % 9;
        el.textContent = cur[i] || "";
        el.classList.toggle("sel", i === sel);
        const peer = sel >= 0 && (r === sr || c === sc || (((r / 3) | 0) === ((sr / 3) | 0) && ((c / 3) | 0) === ((sc / 3) | 0)));
        el.classList.toggle("hl", peer && i !== sel);
        el.classList.toggle("same", sel >= 0 && cur[sel] && cur[i] === cur[sel] && i !== sel);
        el.classList.toggle("err", !!cur[i] && cur[i] !== sol[i]);
      });
      pad.querySelectorAll("button[data-n]").forEach((b) => {
        const n = +b.dataset.n;
        b.style.opacity = cur.filter((v, i) => v === n && v === sol[i]).length >= 9 ? 0.25 : 1;
      });
    }
    function stats() { api.stats({ Level: lvl[0].toUpperCase() + lvl.slice(1), Waktu: fmtTime(sec), Salah: `${mistakes}/3`, Terbaik: api.best("t_" + lvl) != null ? fmtTime(api.best("t_" + lvl)) : "-" }); }
    function input(n) {
      if (over || sel < 0 || puz[sel]) return;
      if (n === 0) { cur[sel] = 0; paint(); return; }
      if (cur[sel] === n) return;
      cur[sel] = n;
      if (n !== sol[sel]) {
        mistakes++; api.sfx("bad"); cells[sel].classList.add("shake");
        setTimeout(() => cells[sel] && cells[sel].classList.remove("shake"), 400);
        if (mistakes >= 3) { over = true; paint(); stats(); api.lose({ title: "3 Kesalahan", text: "Jangan menyerah, coba lagi!" }); return; }
      } else api.sfx("pop");
      paint(); stats();
      if (cur.every((v, i) => v === sol[i])) {
        over = true;
        const isNew = api.saveBest(sec, { key: "t_" + lvl, lower: true });
        api.win({ title: "Sudoku Selesai!", text: `Waktu ${fmtTime(sec)}${isNew ? " — rekor baru!" : ""}\nKesalahan: ${mistakes}` });
      }
    }
    const pad = h("div", { class: "numpad" },
      [1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => h("button", { "data-n": n, onclick: () => input(n) }, n)),
      h("button", { onclick: () => input(0) }, "⌫")
    );
    api.on(window, "keydown", (e) => {
      if (/^[1-9]$/.test(e.key)) input(+e.key);
      else if (e.key === "Backspace" || e.key === "Delete" || e.key === "0") input(0);
      else if (sel >= 0 && e.key.startsWith("Arrow")) {
        const d = { ArrowUp: -9, ArrowDown: 9, ArrowLeft: -1, ArrowRight: 1 }[e.key];
        sel = (sel + d + 81) % 81; paint(); e.preventDefault();
      }
    });
    api.interval(() => { if (!over) { sec++; stats(); } }, 1000);
    root.append(
      api.seg([["mudah", "Mudah"], ["sedang", "Sedang"], ["sulit", "Sulit"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }),
      board, pad
    );
    paint(); stats();
  },
});

/* ================= PUZZLE GESER ================= */
registerGame({
  id: "puzzle-geser",
  name: "Puzzle Geser",
  icon: "🧱",
  cat: "logika",
  color: ["#00c6ff", "#0072ff"],
  desc: "Geser ubin hingga angka berurutan.",
  help: "Geser ubin ke tempat kosong sampai semua angka tersusun urut dari 1, dengan kotak kosong di pojok kanan bawah.\n\nKetuk ubin yang sebaris/sekolom dengan kotak kosong untuk menggesernya. Bisa juga swipe atau tombol panah.",
  init(root, api) {
    const n = api.pref("n", 3);
    const N = n * n;
    let st = [...Array(N - 1).keys()].map((x) => x + 1).concat(0);
    // acak dengan langkah valid (pasti bisa diselesaikan)
    let e = N - 1, prev = -1;
    for (let k = 0; k < 60 * N; k++) {
      const er = (e / n) | 0, ec = e % n;
      const opts = [];
      if (er > 0) opts.push(e - n); if (er < n - 1) opts.push(e + n);
      if (ec > 0) opts.push(e - 1); if (ec < n - 1) opts.push(e + 1);
      const t = pick(opts.filter((o) => o !== prev));
      st[e] = st[t]; st[t] = 0; prev = e; e = t;
    }
    if (st.every((v, i) => v === (i === N - 1 ? 0 : i + 1))) { [st[0], st[1]] = [st[1], st[0]]; [st[2], st[3]] = [st[3], st[2]]; }
    let moves = 0, sec = 0, over = false;
    const board = h("div", { class: "slide" });
    const tiles = {};
    const pad = 1.2, size = 100 / n;
    for (let v = 1; v < N; v++) {
      const hue = 200 + (v / N) * 140;
      tiles[v] = h("div", {
        class: "tile",
        style: {
          width: `calc(${size}% - ${pad * 2}%)`, height: `calc(${size}% - ${pad * 2}%)`,
          background: `linear-gradient(135deg, hsl(${hue},85%,62%), hsl(${hue + 25},80%,48%))`,
          fontSize: `${Math.round(110 / n)}px`,
        },
        onclick: () => tap(st.indexOf(v)),
      }, v);
      board.append(tiles[v]);
    }
    function paint() {
      st.forEach((v, i) => {
        if (!v) return;
        const t = tiles[v];
        t.style.left = `${(i % n) * size + pad}%`;
        t.style.top = `${((i / n) | 0) * size + pad}%`;
        t.classList.toggle("ok", v === i + 1);
      });
    }
    function stats() { api.stats({ Ukuran: `${n}×${n}`, Langkah: moves, Waktu: fmtTime(sec), Terbaik: api.best("m" + n) ?? "-" }); }
    function tap(i) {
      if (over) return;
      const e = st.indexOf(0);
      const r = (i / n) | 0, c = i % n, er = (e / n) | 0, ec = e % n;
      if (r !== er && c !== ec) return;
      if (i === e) return;
      const step = r === er ? (c < ec ? -1 : 1) : (r < er ? -n : n);
      let p = e;
      while (p !== i) { st[p] = st[p + step]; p += step; moves++; }
      st[i] = 0;
      api.sfx("flip"); paint(); stats();
      if (st.every((v, k) => v === (k === N - 1 ? 0 : k + 1))) {
        over = true;
        const isNew = api.saveBest(moves, { key: "m" + n, lower: true });
        api.win({ title: "Tersusun!", text: `${moves} langkah · ${fmtTime(sec)}${isNew ? "\nRekor baru!" : ""}` });
      }
    }
    api.swipe(board, (d) => {
      const e = st.indexOf(0), er = (e / n) | 0, ec = e % n;
      // swipe arah X = ubin bergerak ke arah X → ubin berada di sisi berlawanan dari kosong
      const t = { up: er < n - 1 ? e + n : -1, down: er > 0 ? e - n : -1, left: ec < n - 1 ? e + 1 : -1, right: ec > 0 ? e - 1 : -1 }[d];
      if (t >= 0) tap(t);
    });
    api.interval(() => { if (!over) { sec++; stats(); } }, 1000);
    root.append(api.seg([[3, "3×3"], [4, "4×4"], [5, "5×5"]], n, (v) => { api.setPref("n", v); api.restart(); }), board);
    paint(); stats();
  },
});

/* ================= LAMPU PADAM (Lights Out) ================= */
registerGame({
  id: "lampu-padam",
  name: "Lampu Padam",
  icon: "💡",
  cat: "logika",
  color: ["#f7b733", "#fc4a1a"],
  desc: "Matikan semua lampu di papan.",
  help: "Mengetuk sebuah lampu akan membalik lampu itu DAN 4 lampu di sebelahnya (atas, bawah, kiri, kanan). Tujuanmu: matikan SEMUA lampu!\n\nSetiap level yang selesai membuka level yang lebih sulit.",
  init(root, api) {
    const level = api.pref("level", 1);
    const n = 5;
    const g = Array(n * n).fill(false);
    const toggle = (i) => {
      const r = (i / n) | 0, c = i % n;
      [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dr, dc]) => {
        const rr = r + dr, cc = c + dc;
        if (rr >= 0 && rr < n && cc >= 0 && cc < n) g[rr * n + cc] = !g[rr * n + cc];
      });
    };
    const presses = shuffle([...Array(n * n).keys()]).slice(0, Math.min(3 + level, 18));
    presses.forEach(toggle);
    if (!g.some(Boolean)) toggle(12);
    let moves = 0, over = false;
    const board = h("div", { class: "board", style: { gridTemplateColumns: `repeat(${n}, 1fr)`, gap: "10px", maxWidth: "360px" } });
    const cells = g.map((_, i) => {
      const el = h("button", { class: "cell", onclick: () => press(i) });
      board.append(el); return el;
    });
    function paint() {
      cells.forEach((el, i) => {
        el.style.background = g[i] ? "radial-gradient(circle at 40% 35%, #fff8c4, #ffd84d 45%, #ff9f1c)" : "rgba(255,255,255,.07)";
        el.style.boxShadow = g[i] ? "0 0 22px rgba(255, 216, 77, .7)" : "inset 0 2px 6px rgba(0,0,0,.4)";
        el.textContent = g[i] ? "" : "";
      });
      api.stats({ Level: level, Langkah: moves, Nyala: g.filter(Boolean).length });
    }
    function press(i) {
      if (over) return;
      toggle(i); moves++; api.sfx("click"); paint();
      if (!g.some(Boolean)) {
        over = true; api.setPref("level", level + 1);
        api.win({ title: `Level ${level} Selesai!`, text: `${moves} langkah`, next: "Level Berikutnya ▶" });
      }
    }
    root.append(board, h("div", { class: "row" }, h("button", { class: "btn small", onclick: () => { api.setPref("level", 1); api.restart(); } }, "⏮ Ulang dari Level 1")));
    paint();
  },
});

/* ================= MINESWEEPER (Sapu Ranjau) ================= */
registerGame({
  id: "ranjau",
  name: "Sapu Ranjau",
  icon: "💣",
  cat: "logika",
  color: ["#536976", "#292e49"],
  desc: "Buka semua kotak tanpa kena ranjau.",
  help: "Buka semua kotak yang aman. Angka menunjukkan jumlah ranjau di 8 kotak sekitarnya.\n\n🚩 Tandai ranjau dengan: tekan lama, klik kanan, atau aktifkan mode Bendera.\nKetuk pertama selalu aman!",
  init(root, api) {
    const lvl = api.pref("lvl", "mudah");
    const { n, m } = { mudah: { n: 8, m: 10 }, sedang: { n: 10, m: 18 }, sulit: { n: 12, m: 30 } }[lvl];
    const mine = Array(n * n).fill(false), open = Array(n * n).fill(false), flag = Array(n * n).fill(false);
    let started = false, over = false, flagMode = false, sec = 0;
    const nb = (i) => {
      const r = (i / n) | 0, c = i % n, out = [];
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
        if (!dr && !dc) continue;
        const rr = r + dr, cc = c + dc;
        if (rr >= 0 && rr < n && cc >= 0 && cc < n) out.push(rr * n + cc);
      }
      return out;
    };
    const count = (i) => nb(i).filter((j) => mine[j]).length;
    const board = h("div", { class: "board", style: { gridTemplateColumns: `repeat(${n}, 1fr)`, gap: "3px" } });
    const cells = mine.map((_, i) => {
      const el = h("button", { class: "cell", style: { fontSize: n > 10 ? "14px" : "17px" } });
      let timer = null, longPressed = false;
      el.addEventListener("pointerdown", () => { longPressed = false; timer = setTimeout(() => { longPressed = true; toggleFlag(i); }, 420); });
      el.addEventListener("pointerup", () => { clearTimeout(timer); });
      el.addEventListener("pointerleave", () => clearTimeout(timer));
      el.addEventListener("click", () => { if (longPressed) return; flagMode ? toggleFlag(i) : reveal(i); });
      el.addEventListener("contextmenu", (e) => { e.preventDefault(); clearTimeout(timer); if (!longPressed) toggleFlag(i); });
      board.append(el); return el;
    });
    const COLORS = ["", "#4fc3ff", "#2ee59d", "#ff5470", "#b388ff", "#ffb74d", "#4dd0e1", "#fff", "#aaa"];
    function paint(showAll) {
      cells.forEach((el, i) => {
        if (open[i] || (showAll && mine[i])) {
          el.style.background = mine[i] ? (open[i] ? "#ff5470" : "rgba(255,84,112,.35)") : "rgba(0,0,0,.25)";
          const k = mine[i] ? 0 : count(i);
          el.textContent = mine[i] ? "💣" : k || "";
          el.style.color = COLORS[k];
        } else {
          el.style.background = "linear-gradient(135deg, rgba(255,255,255,.22), rgba(255,255,255,.1))";
          el.textContent = flag[i] ? "🚩" : "";
        }
      });
      stats();
    }
    function stats() { api.stats({ Ranjau: m - flag.filter(Boolean).length, Waktu: fmtTime(sec), Terbaik: api.best("t_" + lvl) != null ? fmtTime(api.best("t_" + lvl)) : "-" }); }
    function place(safe) {
      const forbidden = new Set([safe, ...nb(safe)]);
      const spots = shuffle([...Array(n * n).keys()].filter((i) => !forbidden.has(i)));
      spots.slice(0, m).forEach((i) => (mine[i] = true));
    }
    function toggleFlag(i) {
      if (over || open[i]) return;
      flag[i] = !flag[i]; api.sfx("pop"); if (navigator.vibrate) navigator.vibrate(20); paint();
    }
    function reveal(i) {
      if (over || flag[i] || open[i]) return;
      if (!started) { place(i); started = true; }
      if (mine[i]) {
        open[i] = true; over = true; paint(true); api.lose({ icon: "💥", title: "BOOM!", text: "Kamu menginjak ranjau." }); return;
      }
      const stack = [i];
      while (stack.length) {
        const j = stack.pop();
        if (open[j] || flag[j]) continue;
        open[j] = true;
        if (count(j) === 0) nb(j).forEach((k) => { if (!open[k]) stack.push(k); });
      }
      api.sfx("click"); paint();
      if (open.filter(Boolean).length === n * n - m) {
        over = true;
        const isNew = api.saveBest(sec, { key: "t_" + lvl, lower: true });
        api.win({ title: "Lapangan Aman!", text: `Waktu ${fmtTime(sec)}${isNew ? " — rekor baru!" : ""}` });
      }
    }
    const modeBtn = h("button", { class: "btn small", onclick: () => { flagMode = !flagMode; modeBtn.textContent = flagMode ? "🚩 Mode Bendera: ON" : "⛏️ Mode Gali"; modeBtn.classList.toggle("primary", flagMode); } }, "⛏️ Mode Gali");
    api.interval(() => { if (started && !over) { sec++; stats(); } }, 1000);
    root.append(api.seg([["mudah", "Mudah"], ["sedang", "Sedang"], ["sulit", "Sulit"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }), board, modeBtn);
    paint();
  },
});

/* ================= NONOGRAM ================= */
registerGame({
  id: "nonogram",
  name: "Nonogram",
  icon: "🖼️",
  cat: "logika",
  color: ["#2193b0", "#6dd5ed"],
  desc: "Warnai kotak sesuai petunjuk angka.",
  help: "Angka di kiri tiap baris dan di atas tiap kolom menunjukkan panjang blok kotak yang harus diwarnai, berurutan. Contoh \"3 1\" artinya ada 3 kotak berwarna berurutan, lalu minimal 1 kosong, lalu 1 kotak berwarna.\n\nGunakan mode ❌ untuk menandai kotak yang pasti kosong. Bisa digeser untuk mewarnai banyak kotak.",
  init(root, api) {
    const n = api.pref("n", 5);
    let sol;
    do { sol = Array.from({ length: n * n }, () => Math.random() < 0.58); } while (!sol.some(Boolean));
    const st = Array(n * n).fill(0); // 0 kosong, 1 isi, 2 silang
    let mode = 1, paintVal = null, over = false;
    const clue = (arr) => { const out = []; let k = 0; for (const v of arr) { if (v) k++; else if (k) { out.push(k); k = 0; } } if (k) out.push(k); return out.length ? out : [0]; };
    const row = (a, r) => a.slice(r * n, r * n + n);
    const col = (a, c) => Array.from({ length: n }, (_, r) => a[r * n + c]);
    const rowClues = Array.from({ length: n }, (_, r) => clue(row(sol, r)));
    const colClues = Array.from({ length: n }, (_, c) => clue(col(sol, c)));
    const cellSize = n <= 5 ? 52 : n <= 8 ? 34 : 28;
    const grid = h("div", { class: "nono", style: { gridTemplateColumns: `auto repeat(${n}, ${cellSize}px)`, touchAction: "none" } });
    grid.append(h("div"));
    const colEls = colClues.map((cl) => { const e = h("div", { class: "cl" }, cl.map((x) => h("span", null, x))); grid.append(e); return e; });
    const rowEls = [], cells = [];
    for (let r = 0; r < n; r++) {
      const re = h("div", { class: "rl" }, rowClues[r].map((x) => h("span", null, x)));
      rowEls.push(re); grid.append(re);
      for (let c = 0; c < n; c++) {
        const i = r * n + c;
        const el = h("div", { class: "nc", "data-i": i, style: { borderRight: c % 5 === 4 && c < n - 1 ? "2px solid rgba(255,255,255,.4)" : "", borderBottom: r % 5 === 4 && r < n - 1 ? "2px solid rgba(255,255,255,.4)" : "" } });
        cells.push(el); grid.append(el);
      }
    }
    function paint() {
      cells.forEach((el, i) => { el.classList.toggle("on", st[i] === 1); el.textContent = st[i] === 2 ? "✕" : ""; });
      const filled = st.map((v) => v === 1);
      let ok = true;
      for (let r = 0; r < n; r++) { const good = clue(row(filled, r)).join() === rowClues[r].join(); rowEls[r].classList.toggle("ok", good); ok = ok && good; }
      for (let c = 0; c < n; c++) { const good = clue(col(filled, c)).join() === colClues[c].join(); colEls[c].classList.toggle("ok", good); ok = ok && good; }
      api.stats({ Ukuran: `${n}×${n}`, Mode: mode === 1 ? "⬛ Isi" : "❌ Tanda" });
      if (ok && !over) { over = true; api.win({ title: "Gambar Selesai!", text: "Semua petunjuk terpenuhi." }); }
    }
    function apply(i) {
      if (over || st[i] === paintVal) return;
      st[i] = paintVal; api.sfx("tick"); paint();
    }
    api.on(grid, "pointerdown", (e) => {
      const el = e.target.closest(".nc"); if (!el) return;
      e.preventDefault();
      const i = +el.dataset.i;
      paintVal = st[i] === mode ? 0 : mode;
      apply(i);
    });
    api.on(grid, "pointermove", (e) => {
      if (paintVal == null) return;
      const el = document.elementFromPoint(e.clientX, e.clientY);
      if (el && el.classList.contains("nc")) apply(+el.dataset.i);
    });
    api.on(window, "pointerup", () => (paintVal = null));
    const modeSeg = h("div", { class: "seg" });
    const drawSeg = () => {
      modeSeg.innerHTML = "";
      [[1, "⬛ Isi"], [2, "❌ Tanda"]].forEach(([v, l]) => modeSeg.append(h("button", { class: v === mode ? "on" : "", onclick: () => { mode = v; drawSeg(); paint(); } }, l)));
    };
    drawSeg();
    root.append(api.seg([[5, "5×5"], [8, "8×8"], [10, "10×10"]], n, (v) => { api.setPref("n", v); api.restart(); }), h("div", { style: { overflowX: "auto", maxWidth: "100%" } }, grid), modeSeg);
    paint();
  },
});

/* ================= BINER (Takuzu) ================= */
function takuzuGen(n) {
  const g = Array.from({ length: n }, () => Array(n).fill(-1));
  const half = n / 2;
  function ok(r, c, v) {
    if (c >= 2 && g[r][c - 1] === v && g[r][c - 2] === v) return false;
    if (r >= 2 && g[r - 1][c] === v && g[r - 2][c] === v) return false;
    let rc = 0, cc = 0;
    for (let k = 0; k < c; k++) if (g[r][k] === v) rc++;
    for (let k = 0; k < r; k++) if (g[k][c] === v) cc++;
    if (rc + 1 > half || cc + 1 > half) return false;
    return true;
  }
  function uniqRow(r) { const s = g[r].join(""); for (let k = 0; k < r; k++) if (g[k].join("") === s) return false; return true; }
  function uniqCol(c) { const s = g.map((rw) => rw[c]).join(""); for (let k = 0; k < c; k++) if (g.map((rw) => rw[k]).join("") === s) return false; return true; }
  function fill(i) {
    if (i === n * n) return true;
    const r = (i / n) | 0, c = i % n;
    for (const v of shuffle([0, 1])) {
      if (!ok(r, c, v)) continue;
      g[r][c] = v;
      if (c === n - 1 && !uniqRow(r)) continue;
      if (r === n - 1 && !uniqCol(c)) continue;
      if (fill(i + 1)) return true;
    }
    g[r][c] = -1; return false;
  }
  fill(0);
  return g.flat();
}

registerGame({
  id: "biner",
  name: "Matahari & Bulan",
  icon: "🌗",
  cat: "logika",
  color: ["#ff7e5f", "#3a1c71"],
  desc: "Puzzle biner: seimbangkan ☀️ dan 🌙.",
  help: "Isi semua kotak dengan ☀️ atau 🌙 dengan aturan:\n\n1. Tidak boleh ada 3 simbol sama berurutan (mendatar/menurun).\n2. Setiap baris & kolom berisi ☀️ dan 🌙 sama banyak.\n3. Tidak ada dua baris (atau dua kolom) yang sama persis.\n\nKetuk kotak untuk berganti: kosong → ☀️ → 🌙.",
  init(root, api) {
    const n = api.pref("n", 6);
    const sol = takuzuGen(n);
    const fixed = Array(n * n).fill(false);
    shuffle([...Array(n * n).keys()]).slice(0, Math.round(n * n * (n === 6 ? 0.45 : 0.38))).forEach((i) => (fixed[i] = true));
    const st = sol.map((v, i) => (fixed[i] ? v : -1));
    let over = false;
    const board = h("div", { class: "board", style: { gridTemplateColumns: `repeat(${n}, 1fr)`, gap: "6px", maxWidth: n === 6 ? "360px" : "400px" } });
    const cells = st.map((_, i) => { const el = h("button", { class: "cell", onclick: () => tap(i) }); board.append(el); return el; });
    function errors() {
      const bad = new Set();
      for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
        const v = st[r * n + c]; if (v < 0) continue;
        if (c >= 2 && st[r * n + c - 1] === v && st[r * n + c - 2] === v) [0, 1, 2].forEach((k) => bad.add(r * n + c - k));
        if (r >= 2 && st[(r - 1) * n + c] === v && st[(r - 2) * n + c] === v) [0, 1, 2].forEach((k) => bad.add((r - k) * n + c));
      }
      for (let r = 0; r < n; r++) for (const v of [0, 1]) {
        const idx = [...Array(n).keys()].map((c) => r * n + c);
        if (idx.filter((i) => st[i] === v).length > n / 2) idx.forEach((i) => st[i] === v && bad.add(i));
      }
      for (let c = 0; c < n; c++) for (const v of [0, 1]) {
        const idx = [...Array(n).keys()].map((r) => r * n + c);
        if (idx.filter((i) => st[i] === v).length > n / 2) idx.forEach((i) => st[i] === v && bad.add(i));
      }
      return bad;
    }
    function solved() {
      if (st.includes(-1) || errors().size) return false;
      const rows = new Set(), cols = new Set();
      for (let k = 0; k < n; k++) {
        rows.add(st.slice(k * n, k * n + n).join(""));
        cols.add([...Array(n).keys()].map((r) => st[r * n + k]).join(""));
      }
      return rows.size === n && cols.size === n;
    }
    function paint() {
      const bad = errors();
      cells.forEach((el, i) => {
        const v = st[i];
        el.textContent = v === 0 ? "☀️" : v === 1 ? "🌙" : "";
        el.style.fontSize = n === 6 ? "28px" : "22px";
        el.style.background = v === 0 ? "linear-gradient(135deg,#ffb347,#ff7e5f)" : v === 1 ? "linear-gradient(135deg,#5b6cff,#3a1c71)" : "rgba(255,255,255,.08)";
        el.style.outline = bad.has(i) ? "3px solid #ff5470" : fixed[i] ? "2px solid rgba(255,255,255,.55)" : "none";
        el.style.outlineOffset = "-3px";
      });
      api.stats({ Ukuran: `${n}×${n}`, Terisi: `${st.filter((v) => v >= 0).length}/${n * n}` });
    }
    function tap(i) {
      if (over || fixed[i]) return;
      st[i] = st[i] === -1 ? 0 : st[i] === 0 ? 1 : -1;
      api.sfx("click"); paint();
      if (solved()) { over = true; api.win({ title: "Seimbang Sempurna!", text: "Semua aturan terpenuhi." }); }
    }
    root.append(api.seg([[6, "6×6"], [8, "8×8"]], n, (v) => { api.setPref("n", v); api.restart(); }), board);
    paint();
  },
});

/* ================= 8 RATU ================= */
registerGame({
  id: "ratu",
  name: "Ratu Catur",
  icon: "👑",
  cat: "logika",
  color: ["#c94b4b", "#4b134f"],
  desc: "Letakkan ratu tanpa saling menyerang.",
  help: "Letakkan N ratu di papan catur N×N sehingga tidak ada dua ratu yang saling menyerang — tidak boleh sebaris, sekolom, atau sediagonal.\n\nRatu yang bertabrakan akan berwarna merah.",
  init(root, api) {
    const n = api.pref("n", 8);
    const q = new Set();
    let moves = 0, over = false;
    const board = h("div", { class: "board", style: { gridTemplateColumns: `repeat(${n}, 1fr)`, gap: "0", borderRadius: "12px", overflow: "hidden", maxWidth: "420px", border: "3px solid rgba(255,255,255,.3)" } });
    const cells = [];
    for (let i = 0; i < n * n; i++) {
      const r = (i / n) | 0, c = i % n;
      const el = h("button", { class: "cell", style: { borderRadius: 0, background: (r + c) % 2 ? "#6b4b8f" : "#e9dcff", fontSize: `${Math.round(240 / n)}px` }, onclick: () => tap(i) });
      cells.push(el); board.append(el);
    }
    function conflicts() {
      const arr = [...q], bad = new Set();
      for (let a = 0; a < arr.length; a++) for (let b = a + 1; b < arr.length; b++) {
        const r1 = (arr[a] / n) | 0, c1 = arr[a] % n, r2 = (arr[b] / n) | 0, c2 = arr[b] % n;
        if (r1 === r2 || c1 === c2 || Math.abs(r1 - r2) === Math.abs(c1 - c2)) { bad.add(arr[a]); bad.add(arr[b]); }
      }
      return bad;
    }
    function paint() {
      const bad = conflicts();
      cells.forEach((el, i) => {
        el.textContent = q.has(i) ? "♛" : "";
        el.style.color = bad.has(i) ? "#ff2950" : "#1a1446";
        el.style.textShadow = q.has(i) ? "0 2px 0 rgba(255,255,255,.5)" : "";
      });
      api.stats({ Ratu: `${q.size}/${n}`, Bentrok: bad.size, Langkah: moves });
      return bad;
    }
    function tap(i) {
      if (over) return;
      if (q.has(i)) q.delete(i); else { if (q.size >= n) { toast(`Maksimal ${n} ratu`); return; } q.add(i); }
      moves++; api.sfx("pop");
      const bad = paint();
      if (q.size === n && bad.size === 0) { over = true; api.win({ title: "Kerajaan Damai!", text: `${n} ratu tanpa bentrok dalam ${moves} langkah.` }); }
    }
    root.append(api.seg([[5, "5"], [6, "6"], [8, "8"], [10, "10"]], n, (v) => { api.setPref("n", v); api.restart(); }), board);
    paint();
  },
});

/* ================= MENARA HANOI ================= */
registerGame({
  id: "hanoi",
  name: "Menara Hanoi",
  icon: "🗼",
  cat: "logika",
  color: ["#ee0979", "#ff6a00"],
  desc: "Pindahkan semua cakram ke tiang lain.",
  help: "Pindahkan seluruh tumpukan cakram dari tiang kiri ke tiang KANAN.\n\nAturan: hanya satu cakram yang dipindah sekali jalan, dan cakram besar tidak boleh diletakkan di atas cakram yang lebih kecil.\n\nKetuk tiang asal, lalu tiang tujuan.",
  init(root, api) {
    const n = api.pref("n", 4);
    const pegs = [[...Array(n).keys()].map((k) => n - k), [], []];
    let sel = -1, moves = 0, over = false;
    const min = 2 ** n - 1;
    const wrap = h("div", { class: "hanoi" });
    const pegEls = [0, 1, 2].map((p) => { const el = h("div", { class: "peg", onclick: () => tap(p) }); wrap.append(el); return el; });
    function paint() {
      pegEls.forEach((el, p) => {
        el.innerHTML = ""; el.classList.toggle("sel", p === sel);
        pegs[p].forEach((d, k) => {
          const hue = (d * 360) / (n + 1);
          el.append(h("div", { class: "disk" + (p === sel && k === pegs[p].length - 1 ? " lift" : ""), style: { width: `${28 + (d / n) * 68}%`, background: `linear-gradient(90deg, hsl(${hue},85%,60%), hsl(${hue + 20},85%,48%))` } }));
        });
      });
      api.stats({ Cakram: n, Langkah: moves, Minimal: min, Terbaik: api.best("m" + n) ?? "-" });
    }
    function tap(p) {
      if (over) return;
      if (sel < 0) { if (pegs[p].length) { sel = p; api.sfx("click"); } paint(); return; }
      if (p === sel) { sel = -1; paint(); return; }
      const d = pegs[sel][pegs[sel].length - 1];
      const top = pegs[p][pegs[p].length - 1];
      if (top != null && top < d) { api.sfx("bad"); pegEls[p].classList.add("shake"); setTimeout(() => pegEls[p].classList.remove("shake"), 400); return; }
      pegs[p].push(pegs[sel].pop()); sel = -1; moves++; api.sfx("pop"); paint();
      if (pegs[2].length === n) {
        over = true;
        const isNew = api.saveBest(moves, { key: "m" + n, lower: true });
        api.win({ title: moves === min ? "Sempurna! 🧠" : "Berhasil!", text: `${moves} langkah (minimal ${min})${isNew ? "\nRekor baru!" : ""}` });
      }
    }
    root.append(api.seg([3, 4, 5, 6, 7].map((k) => [k, `${k} cakram`]), n, (v) => { api.setPref("n", v); api.restart(); }), wrap);
    paint();
  },
});

/* ================= URUTKAN BOLA (Ball Sort) ================= */
registerGame({
  id: "urutkan-bola",
  name: "Urutkan Bola",
  icon: "🧪",
  cat: "logika",
  color: ["#43cea2", "#185a9d"],
  desc: "Kelompokkan bola sesuai warnanya.",
  help: "Pindahkan bola hingga setiap tabung berisi satu warna saja.\n\nKetuk tabung asal lalu tabung tujuan. Bola hanya bisa dipindah ke tabung kosong atau ke atas bola berwarna sama, dan selama tabung belum penuh (maks 4).\n\nTerjebak? Gunakan ↶ Batal atau ➕ Tabung.",
  init(root, api) {
    const k = api.pref("k", 5);
    const CAP = 4;
    const PAL = ["#ff5470", "#ffc94d", "#2ee59d", "#23d5ff", "#b388ff", "#ff8a3d", "#ff5fa2", "#8bc34a", "#ffffff"];
    let tubes;
    do {
      const balls = shuffle([...Array(k).keys()].flatMap((c) => Array(CAP).fill(c)));
      tubes = [...Array(k)].map((_, t) => balls.slice(t * CAP, t * CAP + CAP));
    } while (tubes.some((t) => t.every((b) => b === t[0])));
    tubes.push([], []);
    let sel = -1, moves = 0, over = false, extra = false;
    const hist = [];
    const wrap = h("div", { class: "tubes" });
    const isDone = (t) => t.length === 0 || (t.length === CAP && t.every((b) => b === t[0]));
    function paint() {
      wrap.innerHTML = "";
      tubes.forEach((t, i) => {
        const el = h("div", { class: "tube" + (i === sel ? " sel" : "") + (t.length === CAP && isDone(t) ? " done" : ""), onclick: () => tap(i) });
        t.forEach((b) => el.append(h("div", { class: "ball", style: { background: PAL[b] } })));
        wrap.append(el);
      });
      api.stats({ Warna: k, Langkah: moves });
    }
    function tap(i) {
      if (over) return;
      if (sel < 0) { if (tubes[i].length) { sel = i; api.sfx("click"); paint(); } return; }
      if (sel === i) { sel = -1; paint(); return; }
      const a = tubes[sel], b = tubes[i];
      const color = a[a.length - 1];
      if (b.length >= CAP || (b.length && b[b.length - 1] !== color)) { api.sfx("bad"); sel = i; if (!tubes[i].length) sel = -1; paint(); return; }
      hist.push(tubes.map((t) => t.slice()));
      while (a.length && a[a.length - 1] === color && b.length < CAP) b.push(a.pop());
      sel = -1; moves++; api.sfx("pop"); paint();
      if (tubes.every(isDone)) {
        over = true; api.setPref("k", Math.min(k + 1, 9));
        api.win({ title: "Rapi Sekali!", text: `${moves} langkah`, next: k < 9 ? "Level Berikutnya ▶" : "Main Lagi" });
      }
    }
    root.append(
      api.seg([3, 4, 5, 6, 7, 8, 9].map((x) => [x, `${x}`]), k, (v) => { api.setPref("k", v); api.restart(); }),
      h("div", { class: "note" }, "Jumlah warna"),
      wrap,
      h("div", { class: "row" },
        h("button", { class: "btn small", onclick: () => { if (hist.length && !over) { tubes = hist.pop(); moves++; sel = -1; paint(); } } }, "↶ Batal"),
        h("button", { class: "btn small", onclick: (e) => { if (extra || over) return; extra = true; tubes.push([]); e.currentTarget.disabled = true; paint(); } }, "➕ Tabung")
      )
    );
    paint();
  },
});

/* ================= BANJIR WARNA (Flood-It) ================= */
registerGame({
  id: "banjir-warna",
  name: "Banjir Warna",
  icon: "🌊",
  cat: "logika",
  color: ["#1fa2ff", "#12d8fa"],
  desc: "Banjiri papan dengan satu warna.",
  help: "Mulai dari pojok kiri atas. Pilih warna di bawah untuk mengubah warna area milikmu — area akan meluas menyerap kotak tetangga yang berwarna sama.\n\nJadikan seluruh papan satu warna sebelum langkah habis!",
  init(root, api) {
    const lvl = api.pref("lvl", "sedang");
    const { n, max } = { mudah: { n: 10, max: 20 }, sedang: { n: 12, max: 22 }, sulit: { n: 16, max: 30 } }[lvl];
    const COLS = ["#ff5470", "#ffc94d", "#2ee59d", "#23d5ff", "#b388ff", "#ff8a3d"];
    const g = Array.from({ length: n * n }, () => rand(0, COLS.length - 1));
    let moves = 0, over = false;
    const board = h("div", { class: "flood", style: { gridTemplateColumns: `repeat(${n}, 1fr)`, display: "grid" } });
    const cells = g.map(() => { const el = h("i"); board.append(el); return el; });
    function region() {
      const seen = new Set([0]), st = [0], c = g[0];
      while (st.length) {
        const i = st.pop(), r = (i / n) | 0, cc = i % n;
        for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const rr = r + dr, c2 = cc + dc, j = rr * n + c2;
          if (rr >= 0 && rr < n && c2 >= 0 && c2 < n && !seen.has(j) && g[j] === c) { seen.add(j); st.push(j); }
        }
      }
      return seen;
    }
    function paint() { cells.forEach((el, i) => (el.style.background = COLS[g[i]])); api.stats({ Langkah: `${moves}/${max}`, Dikuasai: `${Math.round((region().size / (n * n)) * 100)}%` }); }
    function choose(c) {
      if (over || c === g[0]) return;
      region().forEach((i) => (g[i] = c));
      moves++; api.sfx("pop"); paint();
      if (g.every((v) => v === g[0])) { over = true; api.win({ title: "Banjir Total!", text: `Selesai dalam ${moves} langkah.` }); }
      else if (moves >= max) { over = true; api.lose({ title: "Langkah Habis", text: `Kamu menguasai ${Math.round((region().size / (n * n)) * 100)}% papan.` }); }
    }
    const pal = h("div", { class: "palette" }, COLS.map((c, i) => h("button", { style: { background: c, width: "48px", height: "48px" }, onclick: () => choose(i) })));
    root.append(api.seg([["mudah", "Mudah"], ["sedang", "Sedang"], ["sulit", "Sulit"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }), board, pal);
    paint();
  },
});

/* ================= SOLITAIRE PASAK ================= */
registerGame({
  id: "pasak",
  name: "Solitaire Pasak",
  icon: "📍",
  cat: "logika",
  color: ["#cc2b5e", "#753a88"],
  desc: "Lompati pasak sampai tersisa satu.",
  help: "Pilih sebuah pasak, lalu lompati pasak di sebelahnya (atas/bawah/kiri/kanan) ke lubang kosong di baliknya. Pasak yang dilompati akan hilang.\n\nTarget: sisakan hanya SATU pasak (paling keren di tengah!).",
  init(root, api) {
    const valid = (r, c) => r >= 0 && r < 7 && c >= 0 && c < 7 && !((r < 2 || r > 4) && (c < 2 || c > 4));
    const peg = {};
    for (let r = 0; r < 7; r++) for (let c = 0; c < 7; c++) if (valid(r, c)) peg[r * 7 + c] = !(r === 3 && c === 3);
    let sel = -1, moves = 0, over = false;
    const board = h("div", { class: "pegs" });
    const holes = [];
    for (let i = 0; i < 49; i++) {
      const r = (i / 7) | 0, c = i % 7;
      const el = h("div", { class: "hole" + (valid(r, c) ? "" : " x"), onclick: () => tap(i) });
      holes.push(el); board.append(el);
    }
    const targets = (i) => {
      const r = (i / 7) | 0, c = i % 7, out = [];
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const mr = r + dr, mc = c + dc, tr = r + 2 * dr, tc = c + 2 * dc;
        if (valid(tr, tc) && peg[mr * 7 + mc] && !peg[tr * 7 + tc]) out.push(tr * 7 + tc);
      }
      return out;
    };
    const left = () => Object.values(peg).filter(Boolean).length;
    function paint() {
      const ts = sel >= 0 ? targets(sel) : [];
      holes.forEach((el, i) => {
        el.innerHTML = "";
        el.classList.toggle("sel", i === sel);
        el.classList.toggle("target", ts.includes(i));
        if (peg[i]) el.append(h("div", { class: "pg" }));
      });
      api.stats({ Sisa: left(), Langkah: moves, Terbaik: api.best("best") ?? "-" });
    }
    function tap(i) {
      if (over || peg[i] === undefined) return;
      if (peg[i]) { sel = sel === i ? -1 : i; api.sfx("click"); paint(); return; }
      if (sel >= 0 && targets(sel).includes(i)) {
        const mid = (sel + i) / 2;
        peg[sel] = false; peg[mid] = false; peg[i] = true; sel = i; moves++;
        if (!targets(i).length) sel = -1;
        api.sfx("pop"); paint();
        const any = Object.keys(peg).some((k) => peg[k] && targets(+k).length);
        if (!any) {
          over = true;
          const n = left();
          api.saveBest(n, { lower: true });
          if (n === 1) api.win({ title: peg[24] ? "Sempurna di Tengah! 🌟" : "Tersisa Satu!", text: `${moves} lompatan` });
          else api.result({ icon: n <= 3 ? "⭐" : "🤔", title: `Tersisa ${n} pasak`, text: "Tidak ada lompatan lagi. Target: sisakan 1 pasak.", good: n <= 2 });
        }
      }
    }
    root.append(board);
    paint();
  },
});

/* ================= SOKOBAN (Dorong Peti) ================= */
const SOKO_LEVELS = [
  ["#######", "#@ $ .#", "#######"],
  ["######", "#    #", "# $$ #", "#.@ .#", "######"],
  ["_#####", "_#. .#", "##$ $#", "#  @ #", "#    #", "######"],
  ["#######", "#.   .#", "# $$$ #", "#  @  #", "#  .  #", "#######"],
  ["########", "#  .   #", "# #$#  #", "# . $@ #", "#  $#. #", "#      #", "########"],
  ["__####", "###  #", "#@$  #", "## $.#", "#.$ ##", "#  .#_", "#####_"],
  ["#######", "#..$  #", "#. #$ #", "#  $  #", "# #  @#", "#     #", "#######"],
  ["########", "#   #  #", "# $  $ #", "#.## # #", "#  @ $.#", "# .    #", "########"],
  ["_######", "_#    #", "##$## #", "#. $  #", "# .$# #", "#.@   #", "#######"],
  ["#########", "#.  #   #", "# $   $ #", "## # #.##", "#  $@   #", "# .  #  #", "#########"],
];

registerGame({
  id: "sokoban",
  name: "Dorong Peti",
  icon: "📦",
  cat: "logika",
  color: ["#b06ab3", "#4568dc"],
  desc: "Dorong semua peti ke titik tujuan.",
  help: "Gerakkan karakter untuk MENDORONG peti ke titik hijau. Peti hanya bisa didorong (tidak bisa ditarik) dan hanya satu peti sekali dorong.\n\nGunakan tombol panah, swipe, atau keyboard. Salah langkah? Tekan ↶ Batal.",
  init(root, api) {
    let li = Math.min(api.pref("level", 0), SOKO_LEVELS.length - 1);
    const unlocked = Store.get("soko_unlocked", 0);
    const map = SOKO_LEVELS[li];
    const H = map.length, W = Math.max(...map.map((r) => r.length));
    const wall = new Set(), goal = new Set(), boxes = new Set(), voids = new Set();
    let pl = 0;
    map.forEach((row, r) => {
      for (let c = 0; c < W; c++) {
        const ch = row[c] || "_", i = r * W + c;
        if (ch === "#") wall.add(i);
        if (ch === "_") voids.add(i);
        if (ch === "." || ch === "*" || ch === "+") goal.add(i);
        if (ch === "$" || ch === "*") boxes.add(i);
        if (ch === "@" || ch === "+") pl = i;
      }
    });
    let moves = 0, pushes = 0, over = false;
    const hist = [];
    const cellPx = Math.floor(Math.min(380, innerWidth - 40) / W);
    const board = h("div", { class: "soko", style: { gridTemplateColumns: `repeat(${W}, ${cellPx}px)`, fontSize: `${cellPx * 0.6}px` } });
    const cells = [];
    for (let i = 0; i < W * H; i++) {
      const el = h("div", { class: "sk " + (voids.has(i) ? "" : wall.has(i) ? "w" : "f") + (goal.has(i) ? " g" : "") });
      cells.push(el); board.append(el);
    }
    function paint() {
      cells.forEach((el, i) => {
        el.innerHTML = "";
        if (boxes.has(i)) el.append(h("div", { class: "bx" }));
        if (i === pl) el.append(h("div", { class: "pl" }, "🧑‍🔧"));
      });
      const on = [...boxes].filter((b) => goal.has(b)).length;
      api.stats({ Level: `${li + 1}/${SOKO_LEVELS.length}`, Langkah: moves, Dorong: pushes, Peti: `${on}/${boxes.size}` });
    }
    function move(d) {
      if (over) return;
      const delta = { up: -W, down: W, left: -1, right: 1 }[d];
      const t = pl + delta;
      if (wall.has(t) || voids.has(t)) return;
      if (boxes.has(t)) {
        const t2 = t + delta;
        if (wall.has(t2) || boxes.has(t2) || voids.has(t2)) { api.sfx("bad"); return; }
        hist.push({ pl, boxes: new Set(boxes), moves, pushes });
        boxes.delete(t); boxes.add(t2); pushes++; api.sfx("pop");
      } else {
        hist.push({ pl, boxes: new Set(boxes), moves, pushes });
        api.sfx("tick");
      }
      pl = t; moves++; paint();
      if ([...boxes].every((b) => goal.has(b))) {
        over = true;
        const nx = Math.min(li + 1, SOKO_LEVELS.length - 1);
        Store.set("soko_unlocked", Math.max(unlocked, nx));
        api.setPref("level", nx);
        api.win({ title: `Level ${li + 1} Beres!`, text: `${moves} langkah · ${pushes} dorongan`, next: li + 1 < SOKO_LEVELS.length ? "Level Berikutnya ▶" : "Main Lagi" });
      }
    }
    function undo() { const s = hist.pop(); if (!s || over) return; pl = s.pl; boxes.clear(); s.boxes.forEach((b) => boxes.add(b)); moves = s.moves; pushes = s.pushes; paint(); }
    api.swipe(board, move);
    api.on(window, "keydown", (e) => { if (e.key === "z" || e.key === "u") undo(); });
    const lvSel = h("div", { class: "scroll-chips" },
      SOKO_LEVELS.map((_, k) => h("button", {
        class: "chip" + (k === li ? " active" : ""), disabled: k > Math.max(unlocked, li),
        style: k > Math.max(unlocked, li) ? { opacity: 0.35 } : null,
        onclick: () => { api.setPref("level", k); api.restart(); },
      }, k > Math.max(unlocked, li) ? "🔒" : `${k + 1}`))
    );
    root.append(
      lvSel, board,
      h("div", { class: "dpad" },
        h("button", { onclick: undo, style: { fontSize: "18px" } }, "↶"),
        h("button", { onclick: () => move("up") }, "▲"),
        h("button", { onclick: () => api.restart(), style: { fontSize: "18px" } }, "↻"),
        h("button", { onclick: () => move("left") }, "◀"),
        h("button", { onclick: () => move("down") }, "▼"),
        h("button", { onclick: () => move("right") }, "▶")
      )
    );
    paint();
  },
});

/* ================= TEBAK KODE (Mastermind) ================= */
registerGame({
  id: "tebak-kode",
  name: "Tebak Kode",
  icon: "🔐",
  cat: "logika",
  color: ["#360033", "#0b8793"],
  desc: "Pecahkan kode warna rahasia.",
  help: "Komputer menyimpan kode rahasia berisi 4 warna (bisa ada warna yang sama). Tebak kodenya dalam 10 percobaan!\n\nSetelah menebak, kamu mendapat petunjuk:\n⚪ penuh (putih) = warna & posisi benar\n⭕ cincin = warna benar tapi posisi salah",
  init(root, api) {
    const COLS = ["#ff5470", "#ffc94d", "#2ee59d", "#23d5ff", "#b388ff", "#ff8a3d"];
    const secret = Array.from({ length: 4 }, () => rand(0, 5));
    const MAX = 10;
    const guesses = [];
    let cur = [], over = false;
    const rowsEl = h("div", { class: "mm-rows" });
    function feedback(g) {
      let b = 0, w = 0;
      const s1 = {}, g1 = {};
      g.forEach((v, i) => { if (v === secret[i]) b++; else { s1[secret[i]] = (s1[secret[i]] || 0) + 1; g1[v] = (g1[v] || 0) + 1; } });
      for (const k in g1) w += Math.min(g1[k], s1[k] || 0);
      return { b, w };
    }
    function paint() {
      rowsEl.innerHTML = "";
      for (let r = 0; r < MAX; r++) {
        const g = r < guesses.length ? guesses[r].g : r === guesses.length ? cur : [];
        const isCur = r === guesses.length && !over;
        const row = h("div", { class: "mm-row" + (isCur ? " cur" : "") }, h("span", { class: "muted", style: { width: "18px", fontSize: "12px" } }, r + 1));
        for (let k = 0; k < 4; k++) {
          row.append(h("div", { class: "mm-peg", style: g[k] != null ? { background: COLS[g[k]], boxShadow: "inset -3px -4px 0 rgba(0,0,0,.2)" } : null, onclick: isCur ? () => { cur.splice(k, 1); paint(); } : null }));
        }
        const fb = h("div", { class: "mm-fb" });
        if (r < guesses.length) {
          const { b, w } = guesses[r].f;
          for (let k = 0; k < 4; k++) fb.append(h("i", { class: k < b ? "b" : k < b + w ? "w" : "" }));
        } else for (let k = 0; k < 4; k++) fb.append(h("i"));
        row.append(fb);
        rowsEl.append(row);
      }
      api.stats({ Percobaan: `${guesses.length}/${MAX}` });
    }
    function add(c) { if (over || cur.length >= 4) return; cur.push(c); api.sfx("pop"); paint(); }
    function submit() {
      if (over) return;
      if (cur.length < 4) { toast("Isi 4 warna dulu"); return; }
      const f = feedback(cur);
      guesses.push({ g: cur, f }); cur = [];
      api.sfx(f.b === 4 ? "good" : "click");
      if (f.b === 4) { over = true; paint(); api.win({ title: "Kode Terpecahkan!", text: `Dalam ${guesses.length} percobaan.` }); return; }
      if (guesses.length >= MAX) {
        over = true; paint();
        const reveal = h("div", { class: "row", style: { marginBottom: "16px" } }, secret.map((c) => h("div", { class: "mm-peg", style: { background: COLS[c] } })));
        api.sfx("lose");
        api.timeout(() => showModal({ icon: "🔒", title: "Kode Tidak Terpecahkan", text: "Kode rahasianya:", body: reveal, buttons: [{ label: "Menu", action: () => (location.hash = "#/") }, { label: "Coba Lagi", primary: true, action: api.restart }] }), 400);
        return;
      }
      paint();
    }
    root.append(
      rowsEl,
      h("div", { class: "palette" }, COLS.map((c, i) => h("button", { style: { background: c }, onclick: () => add(i) }))),
      h("div", { class: "row" },
        h("button", { class: "btn small", onclick: () => { cur.pop(); paint(); } }, "⌫ Hapus"),
        h("button", { class: "btn primary", onclick: submit }, "✔ Tebak")
      )
    );
    paint();
  },
});
