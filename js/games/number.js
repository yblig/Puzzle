/* Game kategori ANGKA */
"use strict";

/* ================= 2048 ================= */
registerGame({
  id: "2048",
  name: "2048",
  icon: "🎯",
  cat: "angka",
  color: ["#f12711", "#f5af19"],
  desc: "Gabungkan angka sampai 2048!",
  help: "Swipe (atau tombol panah) untuk menggeser semua ubin. Dua ubin dengan angka sama akan bergabung menjadi satu.\n\nCapai ubin 2048 untuk menang — lalu lanjutkan sejauh mungkin!",
  init(root, api) {
    const COLORS = { 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179", 16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72", 256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e" };
    let g = Array(16).fill(0), score = 0, won = false, over = false;
    const board = h("div", { class: "g2048" });
    const cells = g.map(() => { const el = h("div", { class: "t" }); board.append(el); return el; });
    function addTile() {
      const empty = g.map((v, i) => (v ? -1 : i)).filter((i) => i >= 0);
      if (!empty.length) return -1;
      const i = pick(empty); g[i] = Math.random() < 0.9 ? 2 : 4; return i;
    }
    function paint(newI = -1, merged = []) {
      cells.forEach((el, i) => {
        const v = g[i];
        el.textContent = v || "";
        el.style.background = v ? COLORS[v] || "#3c3a32" : "rgba(255,255,255,.06)";
        el.style.color = v <= 4 ? "#776e65" : "#fff";
        el.style.fontSize = v >= 1024 ? "clamp(16px,5vw,26px)" : v >= 128 ? "clamp(18px,6vw,30px)" : "";
        el.style.boxShadow = v >= 128 ? `0 0 20px ${COLORS[v] || "#fff"}88` : "";
        el.classList.remove("new", "merged"); void el.offsetWidth;
        if (i === newI) el.classList.add("new");
        if (merged.includes(i)) el.classList.add("merged");
      });
      api.stats({ Skor: score, Terbaik: Math.max(score, api.best("best", 0)), Ubin: Math.max(...g) });
    }
    function line(idx) { return idx.map((i) => g[i]); }
    function move(dir) {
      if (over) return;
      const lines = [];
      for (let k = 0; k < 4; k++) {
        const L = [0, 1, 2, 3];
        if (dir === "left") lines.push(L.map((j) => k * 4 + j));
        if (dir === "right") lines.push(L.map((j) => k * 4 + 3 - j));
        if (dir === "up") lines.push(L.map((j) => j * 4 + k));
        if (dir === "down") lines.push(L.map((j) => (3 - j) * 4 + k));
      }
      let changed = false; const merged = [];
      for (const idx of lines) {
        const vals = line(idx).filter(Boolean), out = [];
        for (let i = 0; i < vals.length; i++) {
          if (vals[i] === vals[i + 1]) { out.push(vals[i] * 2); score += vals[i] * 2; merged.push(idx[out.length - 1]); i++; }
          else out.push(vals[i]);
        }
        while (out.length < 4) out.push(0);
        idx.forEach((i, k) => { if (g[i] !== out[k]) changed = true; g[i] = out[k]; });
      }
      if (!changed) return;
      api.sfx(merged.length ? "pop" : "tick");
      const ni = addTile();
      api.saveBest(score);
      paint(ni, merged);
      if (!won && g.includes(2048)) {
        won = true;
        Store.set("wins_2048", Store.get("wins_2048", 0) + 1);
        api.sfx("win"); confetti();
        api.timeout(() => showModal({ icon: "🏆", title: "2048!", text: `Skor ${score}. Mau lanjut?`, buttons: [{ label: "Ulang", action: api.restart }, { label: "Lanjut ▶", primary: true }] }), 300);
      }
      if (!canMove()) { over = true; api.lose({ icon: "🧱", title: "Tidak Ada Langkah", text: `Skor akhir: ${score}\nUbin tertinggi: ${Math.max(...g)}` }); }
    }
    function canMove() {
      if (g.includes(0)) return true;
      for (let i = 0; i < 16; i++) {
        if (i % 4 < 3 && g[i] === g[i + 1]) return true;
        if (i < 12 && g[i] === g[i + 4]) return true;
      }
      return false;
    }
    api.swipe(board, move);
    addTile(); addTile();
    root.append(board, h("p", { class: "note" }, "Swipe di papan atau gunakan tombol panah ⬅️⬆️⬇️➡️"));
    paint();
  },
});

/* ================= TEBAK ANGKA ================= */
registerGame({
  id: "tebak-angka",
  name: "Tebak Angka",
  icon: "🎲",
  cat: "angka",
  color: ["#00b09b", "#96c93d"],
  desc: "Tebak angka rahasia 1–100.",
  help: "Komputer memilih angka rahasia. Kamu punya beberapa kesempatan untuk menebaknya. Setiap tebakan akan diberi petunjuk: terlalu BESAR atau terlalu KECIL, plus seberapa dekat (🔥 panas / ❄️ dingin).",
  init(root, api) {
    const lvl = api.pref("lvl", 100);
    const max = lvl, tries = { 50: 6, 100: 7, 1000: 10 }[lvl];
    const secret = rand(1, max);
    let left = tries, lo = 1, hi = max, over = false;
    const display = h("div", { class: "flash-num" }, "?");
    const hint = h("div", { class: "big-q", style: { fontSize: "18px" } }, `Antara ${lo} – ${hi}`);
    const input = h("input", { class: "input-num", type: "number", inputmode: "numeric", placeholder: "…", min: 1, max });
    const log = h("div", { class: "log" });
    function stats() { api.stats({ Sisa: `${left}/${tries}`, Rentang: `${lo}–${hi}` }); }
    function go() {
      if (over) return;
      const v = parseInt(input.value, 10);
      if (!Number.isFinite(v) || v < 1 || v > max) { toast(`Masukkan angka 1–${max}`); return; }
      input.value = ""; left--;
      const diff = Math.abs(v - secret) / max;
      const heat = diff === 0 ? "🎯" : diff < 0.03 ? "🔥🔥" : diff < 0.08 ? "🔥" : diff < 0.2 ? "🌤️" : "❄️";
      if (v === secret) {
        over = true; display.textContent = secret; api.sfx("good");
        api.win({ title: "Tepat Sekali!", text: `Angkanya ${secret}. Ditebak dalam ${tries - left} kali.` }); stats(); return;
      }
      if (v < secret) lo = Math.max(lo, v + 1); else hi = Math.min(hi, v - 1);
      api.sfx("bad");
      log.prepend(h("div", null, h("b", null, v), h("span", null, `${v < secret ? "⬆️ Terlalu kecil" : "⬇️ Terlalu besar"} ${heat}`)));
      hint.textContent = `Antara ${lo} – ${hi}`;
      display.classList.remove("shake"); void display.offsetWidth; display.classList.add("shake");
      stats();
      if (left <= 0) { over = true; display.textContent = secret; api.lose({ title: "Kesempatan Habis", text: `Angka rahasianya: ${secret}` }); }
      else input.focus();
    }
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
    root.append(
      api.seg([[50, "1–50"], [100, "1–100"], [1000, "1–1000"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }),
      h("div", { class: "panel", style: { display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" } },
        display, hint, input, h("button", { class: "btn primary", onclick: go }, "Tebak!"), log)
    );
    stats();
  },
});

/* ================= MATEMATIKA KILAT ================= */
registerGame({
  id: "mat-kilat",
  name: "Matematika Kilat",
  icon: "⚡",
  cat: "angka",
  color: ["#fc466b", "#3f5efb"],
  desc: "Jawab soal hitungan secepat kilat.",
  help: "Kamu punya 60 detik! Jawab soal hitungan sebanyak mungkin. Jawaban benar +1 poin dan +2 detik. Salah −3 detik. Soal makin sulit seiring skor naik.",
  init(root, api) {
    let score = 0, time = 60, over = false, combo = 0;
    const q = h("div", { class: "big-q", style: { fontSize: "42px" } });
    const choices = h("div", { class: "choices" });
    const bar = h("div", { class: "progress" }, h("i", { style: { width: "100%" } }));
    function make() {
      const lv = Math.floor(score / 5);
      const ops = lv < 1 ? ["+", "-"] : lv < 3 ? ["+", "-", "×"] : ["+", "-", "×", "÷"];
      const op = pick(ops);
      const m = 10 + lv * 8;
      let a, b, ans;
      if (op === "+") { a = rand(1, m); b = rand(1, m); ans = a + b; }
      if (op === "-") { a = rand(1, m); b = rand(1, a); ans = a - b; }
      if (op === "×") { a = rand(2, 5 + lv * 2); b = rand(2, 9 + lv); ans = a * b; }
      if (op === "÷") { b = rand(2, 9 + lv); ans = rand(2, 9 + lv); a = b * ans; }
      const opts = new Set([ans]);
      while (opts.size < 4) { const d = ans + rand(-Math.max(3, Math.ceil(ans * 0.2)), Math.max(3, Math.ceil(ans * 0.2))); if (d >= 0) opts.add(d); }
      q.textContent = `${a} ${op} ${b} = ?`;
      choices.innerHTML = "";
      shuffle([...opts]).forEach((o) => choices.append(h("button", { class: "choice", style: { fontSize: "24px" }, onclick: (e) => answer(e.currentTarget, o === ans) }, o)));
    }
    function answer(btn, ok) {
      if (over) return;
      if (ok) { score++; combo++; time = Math.min(time + 2, 99); api.sfx("good"); btn.classList.add("right"); }
      else { combo = 0; time -= 3; api.sfx("bad"); btn.classList.add("wrong"); }
      stats();
      setTimeout(() => !over && make(), ok ? 150 : 350);
    }
    function stats() { api.stats({ Skor: score, Waktu: Math.max(0, Math.ceil(time)), Combo: "x" + combo, Terbaik: api.best("best", 0) }); bar.firstChild.style.width = `${Math.max(0, Math.min(100, (time / 60) * 100))}%`; }
    api.interval(() => {
      if (over) return;
      time -= 0.1;
      if (Math.abs(time - Math.round(time)) < 0.05) stats();
      bar.firstChild.style.width = `${Math.max(0, Math.min(100, (time / 60) * 100))}%`;
      if (time <= 0) {
        over = true; stats();
        const isNew = api.saveBest(score);
        api.result({ icon: score >= 20 ? "🏆" : "⚡", title: `Skor: ${score}`, text: isNew ? "Rekor baru!" : `Rekor: ${api.best("best", 0)}`, good: score >= 15 });
      }
    }, 100);
    root.append(h("div", { class: "panel", style: { display: "flex", flexDirection: "column", gap: "16px" } }, bar, q, choices));
    make(); stats();
  },
});

/* ================= POLA ANGKA ================= */
function makeSequence() {
  const type = rand(0, 7);
  let seq = [], next;
  const a = rand(1, 12), d = rand(2, 9);
  switch (type) {
    case 0: seq = [0, 1, 2, 3, 4].map((k) => a + d * k); next = a + d * 5; break; // aritmetika
    case 1: { const r = rand(2, 3); const s = rand(1, 4); seq = [0, 1, 2, 3, 4].map((k) => s * r ** k); next = s * r ** 5; break; } // geometri
    case 2: { const s = rand(1, 6); seq = [0, 1, 2, 3, 4].map((k) => (s + k) ** 2); next = (s + 5) ** 2; break; } // kuadrat
    case 3: { let x = rand(1, 5), y = rand(1, 5); seq = [x, y]; for (let k = 0; k < 3; k++) seq.push(seq[seq.length - 1] + seq[seq.length - 2]); next = seq[4] + seq[3]; break; } // fibonacci
    case 4: { const d2 = rand(1, 4); seq = [a]; let inc = d; for (let k = 0; k < 4; k++) { seq.push(seq[seq.length - 1] + inc); inc += d2; } next = seq[4] + inc; break; } // selisih naik
    case 5: { const p = rand(2, 6), q = rand(1, 5); seq = [a]; for (let k = 0; k < 4; k++) seq.push(k % 2 ? seq[seq.length - 1] - q : seq[seq.length - 1] + p); next = seq[4] + p; break; } // naik-turun
    case 6: { const s = 60 + rand(0, 40); seq = [0, 1, 2, 3, 4].map((k) => s - d * k); next = s - d * 5; break; } // menurun
    default: { const s = rand(1, 3); seq = [0, 1, 2, 3, 4].map((k) => s * (k + 1) * (k + 2) / 2); next = s * 6 * 7 / 2; } // segitiga
  }
  return { seq, next };
}
registerGame({
  id: "pola-angka",
  name: "Pola Angka",
  icon: "📈",
  cat: "angka",
  color: ["#7f00ff", "#e100ff"],
  desc: "Temukan angka berikutnya dalam deret.",
  help: "Perhatikan deret angka, temukan polanya (penjumlahan, perkalian, kuadrat, Fibonacci, dan lain-lain), lalu pilih angka yang tepat untuk melanjutkan deret. 10 soal, 20 detik per soal.",
  init(root, api) {
    runQuiz(root, api, {
      seconds: 20,
      make() {
        const { seq, next } = makeSequence();
        const opts = new Set([next]);
        while (opts.size < 4) opts.add(next + pick([-1, 1]) * rand(1, Math.max(4, Math.round(Math.abs(next) * 0.15))));
        return { key: seq.join(","), prompt: h("div", { style: { fontSize: "26px", letterSpacing: "1px" } }, seq.join(", ") + ", ?"), answer: next, options: [...opts] };
      },
    });
  },
});

/* ================= KOTAK AJAIB ================= */
registerGame({
  id: "kotak-ajaib",
  name: "Kotak Ajaib",
  icon: "✨",
  cat: "angka",
  color: ["#ff512f", "#dd2476"],
  desc: "Semua baris, kolom & diagonal = sama.",
  help: "Isi kotak 3×3 dengan angka 1–9 (masing-masing sekali) sehingga jumlah setiap BARIS, KOLOM, dan kedua DIAGONAL sama dengan 15.\n\nKetuk kotak kosong lalu pilih angka. Angka di sisi papan menunjukkan jumlah saat ini.",
  init(root, api) {
    const base = [2, 7, 6, 9, 5, 1, 4, 3, 8];
    const rot = (g) => [g[6], g[3], g[0], g[7], g[4], g[1], g[8], g[5], g[2]];
    const flip = (g) => [g[2], g[1], g[0], g[5], g[4], g[3], g[8], g[7], g[6]];
    let sq = base; for (let k = rand(0, 3); k > 0; k--) sq = rot(sq); if (Math.random() < 0.5) sq = flip(sq);
    const lvl = api.pref("lvl", 2);
    const fixed = new Set(shuffle([0, 1, 2, 3, 5, 6, 7, 8]).slice(0, lvl));
    const st = sq.map((v, i) => (fixed.has(i) ? v : 0));
    let sel = st.findIndex((v) => !v), over = false;
    const LINES = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
    const grid = h("div", { style: { display: "grid", gridTemplateColumns: "repeat(3, 76px) 40px", gap: "8px", alignItems: "center", justifyItems: "center" } });
    const cells = [], sums = [];
    const sumEl = () => { const e = h("div", { style: { fontWeight: 800, fontSize: "14px" } }); sums.push(e); return e; };
    const anti = h("div", { style: { fontWeight: 800, fontSize: "14px" } });
    grid.append(h("div"), h("div"), h("div"), anti);
    for (let r = 0; r < 3; r++) {
      for (let c = 0; c < 3; c++) {
        const i = r * 3 + c;
        const el = h("button", { class: "cell", style: { width: "76px", fontSize: "34px", borderRadius: "16px" }, onclick: () => { if (!fixed.has(i)) { sel = i; api.sfx("click"); paint(); } } });
        cells.push(el); grid.append(el);
      }
      grid.append(sumEl());
    }
    for (let c = 0; c < 3; c++) grid.append(sumEl());
    grid.append(sumEl()); // diagonal utama
    const pad = h("div", { class: "numpad" }, [1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => h("button", { "data-n": n, onclick: () => put(n) }, n)), h("button", { onclick: () => put(0) }, "⌫"));
    function paint() {
      cells.forEach((el, i) => {
        el.textContent = st[i] || "";
        el.style.background = fixed.has(i) ? "rgba(255,255,255,.22)" : i === sel ? "linear-gradient(135deg,#ff5fa2,#7c5cff)" : "rgba(255,255,255,.08)";
        el.style.color = fixed.has(i) ? "#fff" : "#9feaff";
      });
      const lineSums = LINES.map((L) => L.reduce((s, i) => s + st[i], 0));
      const order = [0, 1, 2, 3, 4, 5, 6];
      order.forEach((k, idx) => { const s = lineSums[k]; sums[idx].textContent = s; sums[idx].style.color = s === 15 ? "#2ee59d" : s > 15 ? "#ff5470" : "#a9a3d6"; });
      anti.textContent = "↗" + lineSums[7]; anti.style.color = lineSums[7] === 15 ? "#2ee59d" : "#a9a3d6";
      sums[6].textContent = "↘" + lineSums[6];
      pad.querySelectorAll("button[data-n]").forEach((b) => (b.style.opacity = st.includes(+b.dataset.n) ? 0.3 : 1));
      api.stats({ Terisi: `${st.filter(Boolean).length}/9`, Target: 15 });
      return lineSums;
    }
    function put(n) {
      if (over || sel < 0 || fixed.has(sel)) return;
      if (n && st.includes(n)) { const j = st.indexOf(n); if (fixed.has(j)) { toast("Angka itu sudah dipakai"); return; } st[j] = 0; }
      st[sel] = n; api.sfx("pop");
      if (n) { const nx = st.findIndex((v, i) => !v && !fixed.has(i)); if (nx >= 0) sel = nx; }
      const s = paint();
      if (st.every(Boolean) && s.every((x) => x === 15)) { over = true; api.setPref("lvl", Math.max(0, lvl - 1)); api.win({ title: "Ajaib!", text: "Semua garis berjumlah 15." + (lvl > 0 ? "\nLevel berikutnya: petunjuk lebih sedikit." : "") }); }
    }
    api.on(window, "keydown", (e) => { if (/^[1-9]$/.test(e.key)) put(+e.key); if (e.key === "Backspace") put(0); });
    root.append(
      api.seg([[3, "Mudah"], [2, "Sedang"], [1, "Sulit"], [0, "Master"]], lvl, (v) => { api.setPref("lvl", v); api.restart(); }),
      h("div", { class: "panel", style: { display: "flex", justifyContent: "center" } }, grid), pad
    );
    paint();
  },
});
