/* Game kategori KATA */
"use strict";

/* ================= 1. TEBAK KATA (Hangman) ================= */
const HANGMAN_SVG = `
<svg viewBox="0 0 300 290" xmlns="http://www.w3.org/2000/svg" stroke-linecap="round" stroke-linejoin="round" fill="none">
  <defs>
        <linearGradient id="hmHill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3fd68f"/><stop offset="1" stop-color="#1b8f63"/></linearGradient>
  </defs>
  <circle cx="250" cy="44" r="18" fill="#ffe38a" opacity=".9"/>
  <circle cx="44" cy="40" r="2" fill="#fff"/><circle cx="130" cy="18" r="1.6" fill="#fff"/><circle cx="270" cy="110" r="1.8" fill="#fff"/>
  <path d="M0 290 Q 80 250 150 268 T 300 262 V290 Z" fill="url(#hmHill)"/>
  <g stroke="#8a5428" stroke-width="12">
    <path d="M30 274 H140"/><path d="M70 274 V26"/><path d="M64 26 H190"/><path d="M70 72 L114 28" stroke-width="9"/>
  </g>
  <g stroke="#e0a060" stroke-width="7">
    <path d="M30 272 H140"/><path d="M68 272 V26"/><path d="M64 24 H190"/><path d="M69 70 L113 27" stroke-width="5"/>
  </g>
  <path d="M182 26 V58" stroke="#e8d8b0" stroke-width="4"/>
  <g class="swing">
    <g stroke="#ffffff" stroke-width="7">
      <circle class="part" cx="182" cy="82" r="24" fill="rgba(255,255,255,.08)"/>
      <path class="part" d="M182 106 V186"/>
      <path class="part" d="M182 126 L148 162"/>
      <path class="part" d="M182 126 L216 162"/>
      <path class="part" d="M182 186 L154 238"/>
      <path class="part" d="M182 186 L210 238"/>
    </g>
    <g class="face" stroke="#ff5470" stroke-width="3.5">
      <path d="M171 74 l7 7 m0 -7 l-7 7"/>
      <path d="M186 74 l7 7 m0 -7 l-7 7"/>
      <path d="M172 96 q10 -8 20 0"/>
    </g>
  </g>
</svg>`;

registerGame({
  id: "tebak-kata",
  name: "Tebak Kata",
  icon: "🪢",
  cat: "kata",
  color: ["#ff5fa2", "#8a3ffc"],
  desc: "Tebak huruf sebelum orangnya tergantung!",
  help: "Tebak kata rahasia huruf demi huruf. Setiap tebakan SALAH akan memunculkan satu potongan tubuh: kepala, badan, dua tangan, dan dua kaki. Kalau tubuhnya lengkap (6 salah), kamu kalah!\n\n💡 Petunjuk membuka satu huruf tapi memakan 1 nyawa.\n🔥 Menang beruntun untuk menambah streak.\nPilih kategori di atas, atau 🎲 Acak.",
  init(root, api) {
    const cat = api.pref("cat", "Acak");
    const MAX = 6;
    const pool = cat === "Acak" ? ALL_WORDS : ALL_WORDS.filter((x) => x.c === cat);
    const recent = Store.get("hm_recent", []);
    let choice = pool.filter((x) => !recent.includes(x.w));
    if (!choice.length) choice = pool;
    const { w: word, c: wordCat } = pick(choice);
    Store.set("hm_recent", [word, ...recent].slice(0, 80));

    const letters = new Set([...word].filter((ch) => /[A-Z]/.test(ch)));
    const guessed = new Set();
    let wrong = 0, over = false, hintsUsed = 0;
    let streak = Store.get("hm_streak", 0);

    const chips = h("div", { class: "scroll-chips" },
      ["Acak", ...CATEGORY_NAMES].map((c) => h("button", {
        class: "chip" + (c === cat ? " active" : ""),
        onclick: () => { api.setPref("cat", c); api.restart(); },
      }, c === "Acak" ? "🎲 Acak" : `${WORD_BANK[c].icon} ${c}`))
    );

    const stage = h("div", { class: "hm-stage", html: HANGMAN_SVG });
    const parts = stage.querySelectorAll(".part");
    const hearts = h("div", { class: "hearts" });
    const wordEl = h("div", { class: "hm-word" });
    const slotEls = [];
    for (const ch of word) {
      let el;
      if (ch === " ") el = h("div", { class: "hm-letter space" });
      else if (!/[A-Z]/.test(ch)) el = h("div", { class: "hm-letter sym" }, ch);
      else el = h("div", { class: "hm-letter" });
      slotEls.push(el); wordEl.append(el);
    }
    const hintBtn = h("button", { class: "btn small", onclick: hint }, "💡 Petunjuk");
    const kb = api.keyboard(guess);

    function renderStats() {
      hearts.textContent = "❤️".repeat(MAX - wrong) + "🖤".repeat(wrong);
      api.stats({ Streak: "🔥 " + streak, Terbaik: api.best("best", 0), Salah: `${wrong}/${MAX}` });
      hintBtn.disabled = over || MAX - wrong <= 1;
    }
    function reveal(ch) {
      [...word].forEach((c, i) => { if (c === ch) { slotEls[i].textContent = c; slotEls[i].classList.add("show"); } });
    }
    function guess(ch) {
      if (over || guessed.has(ch) || !/^[A-Z]$/.test(ch)) return;
      guessed.add(ch);
      if (letters.has(ch)) {
        api.sfx("good"); kb.mark(ch, "hit"); reveal(ch);
        if ([...letters].every((l) => guessed.has(l))) finish(true);
      } else {
        api.sfx("bad"); kb.mark(ch, "miss");
        parts[wrong].classList.add("on");
        wrong++;
        stage.classList.remove("shake"); void stage.offsetWidth; stage.classList.add("shake");
        if (wrong >= MAX) finish(false);
      }
      renderStats();
    }
    function hint() {
      if (over || MAX - wrong <= 1) return;
      const left = [...letters].filter((l) => !guessed.has(l));
      if (!left.length) return;
      const ch = pick(left);
      hintsUsed++;
      parts[wrong].classList.add("on"); wrong++;
      guessed.add(ch); kb.mark(ch, "hit"); reveal(ch); api.sfx("pop");
      if ([...letters].every((l) => guessed.has(l))) finish(true);
      renderStats();
    }
    function finish(won) {
      over = true;
      if (won) {
        streak++; Store.set("hm_streak", streak);
        api.saveBest(streak);
        api.win({
          title: "Benar! 🎉",
          text: `Kata: ${word}\nKategori: ${wordCat}\nSalah: ${wrong} · Petunjuk: ${hintsUsed}\nStreak: 🔥 ${streak}`,
          next: "Kata Berikutnya",
        });
      } else {
        stage.querySelector(".face").classList.add("on");
        stage.querySelector(".swing").classList.add("on");
        [...word].forEach((c, i) => {
          if (/[A-Z]/.test(c) && !guessed.has(c)) { slotEls[i].textContent = c; slotEls[i].classList.add("missed"); }
        });
        const lost = streak; streak = 0; Store.set("hm_streak", 0);
        api.lose({ title: "Tergantung! 😵", text: `Jawabannya: ${word}\nKategori: ${wordCat}` + (lost ? `\nStreak ${lost} terputus.` : ""), next: "Coba Kata Lain" });
      }
      renderStats();
    }

    root.append(
      chips,
      h("div", { class: "hm-wrap" },
        stage,
        h("div", { class: "row" }, h("span", { class: "hm-cat" }, `${WORD_BANK[wordCat].icon} ${wordCat}`), hearts),
        wordEl,
        h("div", { class: "row" }, hintBtn, h("span", { class: "muted", style: { fontSize: "12px" } }, `${word.replace(/[^A-Z]/g, "").length} huruf`)),
        kb.el
      )
    );
    renderStats();
    setTimeout(() => { const a = chips.querySelector(".active"); if (a) a.scrollIntoView({ inline: "center", block: "nearest" }); }, 50);
  },
});

/* ================= 2. ACAK KATA ================= */
registerGame({
  id: "acak-kata",
  name: "Acak Kata",
  icon: "🔀",
  cat: "kata",
  color: ["#ff9a44", "#fc6076"],
  desc: "Susun huruf acak menjadi kata yang benar.",
  help: "Huruf-huruf sebuah kata sudah diacak. Ketuk huruf untuk menyusunnya di kotak. Ketuk kotak yang sudah terisi untuk mengembalikan hurufnya.\n\n10 ronde per permainan. Jawaban benar +10 poin (−3 setiap petunjuk). Kategori kata ditampilkan sebagai bantuan.",
  init(root, api) {
    const ROUNDS = 10;
    const pool = shuffle(plainWords(4, 8));
    let round = 0, score = 0, cur;
    const area = h("div", { class: "panel", style: { display: "flex", flexDirection: "column", gap: "16px", alignItems: "center" } });
    root.append(area);

    function stats() { api.stats({ Ronde: `${Math.min(round + 1, ROUNDS)}/${ROUNDS}`, Skor: score, Terbaik: api.best("best", 0) }); }

    function next() {
      if (round >= ROUNDS) {
        const isNew = api.saveBest(score);
        api.result({ icon: score >= 70 ? "🏆" : "⭐", title: `Skor: ${score}`, text: (isNew ? "Rekor baru! " : "") + `Kamu menyelesaikan ${ROUNDS} ronde.`, good: score >= 50 });
        return;
      }
      const { w, c } = pool[round % pool.length];
      let letters = shuffle([...w]);
      for (let k = 0; k < 10 && letters.join("") === w; k++) letters = shuffle([...w]);
      cur = { w, c, tiles: letters.map((ch) => ({ ch, used: false })), slots: Array(w.length).fill(null), locked: 0, hints: 0 };
      draw(); stats();
    }

    function draw() {
      area.innerHTML = "";
      const slots = h("div", { class: "slots" });
      cur.slots.forEach((ti, i) => {
        slots.append(h("button", {
          class: "slot" + (ti != null ? " f" : ""),
          style: i < cur.locked ? { borderColor: "#2ee59d", color: "#2ee59d" } : null,
          onclick: () => {
            if (ti == null || i < cur.locked) return;
            cur.tiles[ti].used = false; cur.slots[i] = null; api.sfx("flip"); draw();
          },
        }, ti != null ? cur.tiles[ti].ch : ""));
      });
      const tiles = h("div", { class: "tiles" });
      cur.tiles.forEach((t, ti) => {
        tiles.append(h("button", {
          class: "ltile" + (t.used ? " used" : ""),
          onclick: () => place(ti),
        }, t.ch));
      });
      area.append(
        h("span", { class: "hm-cat" }, `${WORD_BANK[cur.c].icon} ${cur.c}`),
        slots, tiles,
        h("div", { class: "row" },
          h("button", { class: "btn small", onclick: () => { clearSlots(); cur.tiles = [...cur.tiles.slice(0)]; reshuffle(); } }, "🔄 Acak"),
          h("button", { class: "btn small", onclick: hint, disabled: cur.locked >= cur.w.length - 1 }, "💡 Petunjuk"),
          h("button", { class: "btn small", onclick: skip }, "⏭️ Lewati")
        )
      );
    }
    function reshuffle() {
      const free = cur.tiles.filter((t) => !t.used);
      const used = cur.tiles.filter((t) => t.used);
      const map = new Map();
      cur.slots.forEach((ti, i) => { if (ti != null) map.set(i, cur.tiles[ti]); });
      cur.tiles = [...used, ...shuffle(free)];
      cur.slots = cur.slots.map((ti, i) => (map.has(i) ? cur.tiles.indexOf(map.get(i)) : null));
      api.sfx("flip"); draw();
    }
    function clearSlots() {
      cur.slots.forEach((ti, i) => { if (ti != null && i >= cur.locked) { cur.tiles[ti].used = false; cur.slots[i] = null; } });
    }
    function place(ti) {
      const t = cur.tiles[ti];
      if (t.used) return;
      const i = cur.slots.indexOf(null);
      if (i < 0) return;
      t.used = true; cur.slots[i] = ti; api.sfx("pop");
      draw();
      if (!cur.slots.includes(null)) check();
    }
    function check() {
      const guess = cur.slots.map((ti) => cur.tiles[ti].ch).join("");
      if (guess === cur.w) {
        api.sfx("good");
        score += Math.max(2, 10 - cur.hints * 3);
        toast("✅ Benar! " + cur.w);
        round++; stats();
        api.timeout(next, 700);
      } else {
        api.sfx("bad");
        area.querySelector(".slots").classList.add("shake");
        api.timeout(() => { clearSlots(); draw(); }, 500);
      }
    }
    function hint() {
      if (cur.locked >= cur.w.length - 1) return;
      // kosongkan semua slot yg tidak terkunci, lalu kunci huruf benar berikutnya
      clearSlots();
      const need = cur.w[cur.locked];
      const ti = cur.tiles.findIndex((t) => !t.used && t.ch === need);
      cur.tiles[ti].used = true; cur.slots[cur.locked] = ti; cur.locked++; cur.hints++;
      api.sfx("pop"); draw();
      if (!cur.slots.includes(null)) check();
    }
    function skip() {
      toast("Jawabannya: " + cur.w, 1800);
      api.sfx("bad");
      round++; stats(); api.timeout(next, 400);
    }
    next();
  },
});

/* ================= 3. KATA 5 HURUF (gaya Wordle) ================= */
registerGame({
  id: "kata-5",
  name: "Kata 5 Huruf",
  icon: "🟩",
  cat: "kata",
  color: ["#11998e", "#38ef7d"],
  desc: "Tebak kata 5 huruf dalam 6 percobaan.",
  help: "Tebak kata rahasia 5 huruf dalam 6 kali percobaan.\n\n🟩 Hijau: huruf benar & posisi benar\n🟨 Kuning: huruf ada tapi posisi salah\n⬛ Abu: huruf tidak ada di kata\n\nKetik pakai keyboard di layar lalu tekan ENTER.",
  init(root, api) {
    const answer = pick(FIVE_LETTER);
    const rows = [];
    let cur = "", row = 0, over = false;
    const grid = h("div", { class: "wd-grid" });
    for (let r = 0; r < 6; r++) {
      const re = h("div", { class: "wd-row" });
      const tiles = [];
      for (let c = 0; c < 5; c++) { const t = h("div", { class: "wd-tile" }); tiles.push(t); re.append(t); }
      rows.push({ el: re, tiles }); grid.append(re);
    }
    const kb = api.keyboard(onKey, { enter: true, back: true });
    const streak = Store.get("wd_streak", 0);
    api.stats({ Streak: "🔥 " + streak, Menang: Store.get("wins_kata-5", 0) });

    function paint() {
      rows[row].tiles.forEach((t, i) => {
        t.textContent = cur[i] || "";
        t.classList.toggle("filled", !!cur[i]);
      });
    }
    function onKey(k) {
      if (over) return;
      if (k === "BACK") { cur = cur.slice(0, -1); paint(); return; }
      if (k === "ENTER") { submit(); return; }
      if (cur.length < 5 && /^[A-Z]$/.test(k)) { cur += k; api.sfx("tick"); paint(); }
    }
    function score(guess) {
      const res = Array(5).fill("x");
      const left = {};
      for (let i = 0; i < 5; i++) {
        if (guess[i] === answer[i]) res[i] = "g";
        else left[answer[i]] = (left[answer[i]] || 0) + 1;
      }
      for (let i = 0; i < 5; i++) {
        if (res[i] !== "g" && left[guess[i]]) { res[i] = "y"; left[guess[i]]--; }
      }
      return res;
    }
    function submit() {
      if (cur.length < 5) {
        rows[row].el.classList.remove("shake"); void rows[row].el.offsetWidth; rows[row].el.classList.add("shake");
        toast("Kurang huruf!"); api.sfx("bad"); return;
      }
      const res = score(cur);
      const g = cur;
      rows[row].tiles.forEach((t, i) => {
        setTimeout(() => { t.classList.add("flip", res[i]); kb.mark(g[i], res[i]); api.sfx("flip"); }, i * 180);
      });
      const won = g === answer;
      row++; cur = "";
      if (won || row >= 6) {
        over = true;
        api.timeout(() => {
          if (won) {
            Store.set("wd_streak", streak + 1);
            api.win({ title: ["Jenius!", "Luar biasa!", "Hebat!", "Mantap!", "Bagus!", "Fiuh, nyaris!"][row - 1], text: `Kata: ${answer}\nTebakan ke-${row} · Streak 🔥 ${streak + 1}` });
          } else {
            Store.set("wd_streak", 0);
            api.lose({ title: "Kesempatan habis", text: `Jawabannya: ${answer}` });
          }
        }, 1100);
      }
    }
    root.append(grid, kb.el);
  },
});

/* ================= 4. CARI KATA ================= */
registerGame({
  id: "cari-kata",
  name: "Cari Kata",
  icon: "🔍",
  cat: "kata",
  color: ["#4facfe", "#6a5cff"],
  desc: "Temukan kata tersembunyi di kotak huruf.",
  help: "Temukan semua kata dalam daftar yang tersembunyi di kotak huruf. Kata bisa mendatar, menurun, diagonal, bahkan terbalik (level Sulit).\n\nCara memilih: geser jari dari huruf pertama ke huruf terakhir, ATAU ketuk huruf pertama lalu ketuk huruf terakhir.",
  init(root, api) {
    const lvl = api.pref("lvl", "sedang");
    const conf = { mudah: { n: 8, k: 6, dirs: [[0, 1], [1, 0]] }, sedang: { n: 10, k: 8, dirs: [[0, 1], [1, 0], [1, 1], [-1, 1]] }, sulit: { n: 12, k: 10, dirs: [[0, 1], [1, 0], [1, 1], [-1, 1], [0, -1], [-1, 0], [-1, -1], [1, -1]] } }[lvl];
    const N = conf.n;
    const cats = CATEGORY_NAMES.filter((c) => plainWords(3, N, c).length >= conf.k + 4);
    const cat = pick(cats);
    const cand = shuffle(plainWords(3, N, cat).map((x) => x.w));
    const grid = Array.from({ length: N }, () => Array(N).fill(""));
    const placed = [];
    for (const w of cand) {
      if (placed.length >= conf.k) break;
      for (let t = 0; t < 150; t++) {
        const [dr, dc] = pick(conf.dirs);
        const r0 = rand(0, N - 1), c0 = rand(0, N - 1);
        const r1 = r0 + dr * (w.length - 1), c1 = c0 + dc * (w.length - 1);
        if (r1 < 0 || r1 >= N || c1 < 0 || c1 >= N) continue;
        let ok = true;
        for (let i = 0; i < w.length; i++) { const g = grid[r0 + dr * i][c0 + dc * i]; if (g && g !== w[i]) { ok = false; break; } }
        if (!ok) continue;
        for (let i = 0; i < w.length; i++) grid[r0 + dr * i][c0 + dc * i] = w[i];
        placed.push(w); break;
      }
    }
    const ABC = "AAABCDEEGHIIIJKKLMMNNOPRRSSTTUUWY";
    for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) if (!grid[r][c]) grid[r][c] = pick(ABC);

    const found = new Set();
    const board = h("div", { class: "board", style: { gridTemplateColumns: `repeat(${N}, 1fr)`, gap: "3px" } });
    const cells = [];
    for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) {
      const el = h("div", { class: "cell ws-cell", "data-r": r, "data-c": c }, grid[r][c]);
      cells.push(el); board.append(el);
    }
    const cellAt = (r, c) => cells[r * N + c];
    const wordsEl = h("div", { class: "ws-words" });
    const wordTags = {};
    placed.slice().sort().forEach((w) => { wordTags[w] = h("span", null, w); wordsEl.append(wordTags[w]); });

    let start = null, pending = null, path = [], moved = false;
    const t0 = Date.now();
    function stats() { api.stats({ Kategori: `${WORD_BANK[cat].icon} ${cat}`, Ditemukan: `${found.size}/${placed.length}` }); }
    stats();

    function lineCells(a, b) {
      const dr = b.r - a.r, dc = b.c - a.c;
      if (!(dr === 0 || dc === 0 || Math.abs(dr) === Math.abs(dc))) return [a];
      const len = Math.max(Math.abs(dr), Math.abs(dc));
      const sr = Math.sign(dr), sc = Math.sign(dc);
      return Array.from({ length: len + 1 }, (_, i) => ({ r: a.r + sr * i, c: a.c + sc * i }));
    }
    function paintSel() {
      cells.forEach((el) => el.classList.remove("sel"));
      path.forEach((p) => cellAt(p.r, p.c).classList.add("sel"));
    }
    function cellFromEvent(e) {
      const el = document.elementFromPoint(e.clientX, e.clientY);
      if (!el || !el.dataset || el.dataset.r == null) return null;
      return { r: +el.dataset.r, c: +el.dataset.c };
    }
    function tryWord() {
      const s = path.map((p) => grid[p.r][p.c]).join("");
      const rev = [...s].reverse().join("");
      const w = placed.find((x) => !found.has(x) && (x === s || x === rev));
      if (w) {
        found.add(w); wordTags[w].classList.add("done");
        const hue = (found.size * 47) % 360;
        path.forEach((p) => { const el = cellAt(p.r, p.c); el.style.background = `hsla(${hue}, 85%, 60%, .75)`; el.style.color = "#fff"; });
        api.sfx("good"); stats();
        if (found.size === placed.length) {
          const sec = Math.round((Date.now() - t0) / 1000);
          const isNew = api.saveBest(sec, { key: "t_" + lvl, lower: true });
          api.win({ title: "Semua ketemu!", text: `Waktu: ${fmtTime(sec)}${isNew ? " (rekor baru!)" : ""}` });
        }
        return true;
      }
      return false;
    }
    api.on(board, "pointerdown", (e) => {
      const p = cellFromEvent(e); if (!p) return;
      e.preventDefault();
      if (pending) {
        path = lineCells(pending, p); pending = null;
        if (path.length > 1 && !tryWord()) api.sfx("bad");
        path = []; paintSel(); start = null; return;
      }
      start = p; moved = false; path = [p]; paintSel();
    });
    api.on(board, "pointermove", (e) => {
      if (!start) return;
      const p = cellFromEvent(e); if (!p) return;
      if (p.r !== start.r || p.c !== start.c) moved = true;
      path = lineCells(start, p); paintSel();
    });
    api.on(window, "pointerup", () => {
      if (!start) return;
      if (!moved) { pending = start; start = null; path = [pending]; paintSel(); return; }
      if (path.length > 1 && !tryWord()) api.sfx("bad");
      start = null; path = []; paintSel();
    });

    root.append(
      api.seg([["mudah", "Mudah 8×8"], ["sedang", "Sedang 10×10"], ["sulit", "Sulit 12×12"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }),
      board, wordsEl
    );
  },
});

/* ================= Quiz runner (dipakai Emoji, Kuis, Bendera, Pola Angka) ================= */
function runQuiz(root, api, { rounds = 10, seconds = 0, make, promptClass = "big-q", passScore = 6 }) {
  let i = 0, correct = 0, points = 0, timerId = null, left = 0, locked = false;
  const prog = h("div", { class: "progress" }, h("i", { style: { width: "0%" } }));
  const timeBar = h("div", { class: "progress", style: { height: "6px", opacity: seconds ? 1 : 0 } }, h("i", { style: { width: "100%" } }));
  const promptEl = h("div", { class: promptClass });
  const choices = h("div", { class: "choices" });
  const panel = h("div", { class: "panel", style: { display: "flex", flexDirection: "column", gap: "14px" } }, prog, timeBar, promptEl, choices);
  root.append(panel);
  const used = new Set();

  function stats() { api.stats({ Soal: `${Math.min(i + 1, rounds)}/${rounds}`, Benar: correct, Poin: points, Terbaik: api.best("best", 0) }); }
  function next() {
    if (i >= rounds) {
      clearInterval(timerId);
      const isNew = api.saveBest(points);
      api.result({
        icon: correct >= rounds * 0.8 ? "🏆" : correct >= passScore ? "⭐" : "📚",
        title: `${correct} dari ${rounds} benar`,
        text: `Poin: ${points}${isNew ? " — Rekor baru!" : ""}`,
        good: correct >= passScore,
      });
      return;
    }
    locked = false;
    let q, guard = 0;
    do { q = make(); guard++; } while (used.has(q.key) && guard < 50);
    used.add(q.key);
    prog.firstChild.style.width = `${(i / rounds) * 100}%`;
    promptEl.innerHTML = "";
    promptEl.append(q.prompt);
    choices.innerHTML = "";
    shuffle(q.options).forEach((opt) => {
      choices.append(h("button", { class: "choice", onclick: (e) => answer(e.currentTarget, opt, q.answer) }, String(opt)));
    });
    stats();
    if (seconds) {
      left = seconds * 10; clearInterval(timerId);
      timeBar.firstChild.style.width = "100%";
      timerId = setInterval(() => {
        left--; timeBar.firstChild.style.width = `${(left / (seconds * 10)) * 100}%`;
        if (left <= 0) { clearInterval(timerId); answer(null, null, q.answer); }
      }, 100);
    }
  }
  function answer(btn, opt, ans) {
    if (locked) return; locked = true; clearInterval(timerId);
    const ok = String(opt) === String(ans);
    choices.querySelectorAll(".choice").forEach((b) => { if (b.textContent === String(ans)) b.classList.add("right"); });
    if (ok) { correct++; points += 10 + (seconds ? Math.ceil(left / 10) : 0); api.sfx("good"); }
    else { if (btn) btn.classList.add("wrong"); api.sfx("bad"); if (!btn) toast("⏰ Waktu habis!"); }
    i++; stats();
    api.timeout(next, ok ? 700 : 1300);
  }
  api.onCleanup(() => clearInterval(timerId));
  next();
}

/* ================= 5. TEBAK EMOJI ================= */
registerGame({
  id: "tebak-emoji",
  name: "Tebak Emoji",
  icon: "🤔",
  cat: "kata",
  color: ["#f7971e", "#ffd200"],
  desc: "Emoji ini maksudnya apa ya?",
  help: "Lihat rangkaian emoji dan tebak kata atau frasa yang dimaksud dari 4 pilihan. Ada 10 soal, jawab cepat untuk bonus poin!",
  init(root, api) {
    runQuiz(root, api, {
      seconds: 15,
      make() {
        const [e, a] = pick(EMOJI_PUZZLES);
        const wrong = shuffle(EMOJI_PUZZLES.filter((x) => x[1] !== a)).slice(0, 3).map((x) => x[1]);
        return { key: a, prompt: h("div", { style: { fontSize: "64px", letterSpacing: "6px" } }, e), answer: a, options: [a, ...wrong] };
      },
    });
  },
});

/* ================= 6. KUIS PINTAR ================= */
registerGame({
  id: "kuis",
  name: "Kuis Pintar",
  icon: "🎓",
  cat: "kata",
  color: ["#8e2de2", "#4a00e0"],
  desc: "Uji pengetahuan umummu!",
  help: `Jawab 10 pertanyaan pengetahuan umum (dari ${TRIVIA.length} soal). Setiap soal punya waktu 15 detik — semakin cepat, semakin banyak bonus poin.`,
  init(root, api) {
    runQuiz(root, api, {
      seconds: 15,
      promptClass: "big-q",
      make() {
        const [q, a, ...w] = pick(TRIVIA);
        return { key: q, prompt: h("div", { style: { fontSize: "20px", lineHeight: 1.35 } }, q), answer: a, options: [a, ...w] };
      },
    });
  },
});

/* ================= 7. TEBAK BENDERA ================= */
registerGame({
  id: "bendera",
  name: "Tebak Bendera",
  icon: "🚩",
  cat: "kata",
  color: ["#e52d27", "#b31217"],
  desc: "Kenali bendera negara-negara dunia.",
  help: `Tebak nama negara dari benderanya. ${FLAGS.length} bendera, 10 soal per permainan, 12 detik per soal.`,
  init(root, api) {
    runQuiz(root, api, {
      seconds: 12,
      make() {
        const [f, a] = pick(FLAGS);
        const wrong = shuffle(FLAGS.filter((x) => x[1] !== a)).slice(0, 3).map((x) => x[1]);
        return { key: a, prompt: h("div", { style: { fontSize: "96px", lineHeight: 1 } }, f), answer: a, options: [a, ...wrong] };
      },
    });
  },
});
