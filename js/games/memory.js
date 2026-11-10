/* Game kategori MEMORI */
"use strict";

/* ================= MEMORI KARTU ================= */
registerGame({
  id: "memori-kartu",
  name: "Memori Kartu",
  icon: "🃏",
  cat: "memori",
  color: ["#7f7fd5", "#86a8e7"],
  desc: "Temukan pasangan kartu yang sama.",
  help: "Buka dua kartu sekaligus. Jika gambarnya sama, kartu tetap terbuka. Jika tidak, kartu akan tertutup lagi. Ingat-ingat posisinya dan temukan semua pasangan dengan langkah sesedikit mungkin!",
  init(root, api) {
    const size = api.pref("size", "4x4");
    const [cols, rows] = size.split("x").map(Number);
    const SETS = ["🍎🍌🍇🍉🍓🍒🥝🍍🥥🍑🍋🥭🫐🍐🌽🥕🍆🥑", "🐶🐱🐼🦊🐸🐵🦁🐯🐨🐷🐰🐔🦄🐙🐢🦋🐝🐳", "⚽🏀🏈⚾🎾🏐🏉🎱🏓🏸🥊🎯🎳🛹🏹🎣🥏🪁"];
    const splitEmoji = (s) => (window.Intl && Intl.Segmenter ? [...new Intl.Segmenter().segment(s)].map((x) => x.segment) : Array.from(s));
    const emojis = splitEmoji(pick(SETS));
    const pairs = (cols * rows) / 2;
    const deck = shuffle(shuffle(emojis).slice(0, pairs).flatMap((e) => [e, e]));
    let open = [], done = 0, moves = 0, sec = 0, lock = false, startT = false;
    const grid = h("div", { class: "mem", style: { gridTemplateColumns: `repeat(${cols}, 1fr)`, maxWidth: cols >= 6 ? "440px" : "400px" } });
    const cards = deck.map((e, i) => {
      const el = h("div", { class: "mcard", onclick: () => flip(i) }, h("div", { class: "in" }, h("div", { class: "bk" }, "✦"), h("div", { class: "fr" }, e)));
      grid.append(el); return el;
    });
    function stats() { api.stats({ Pasangan: `${done}/${pairs}`, Langkah: moves, Waktu: fmtTime(sec), Terbaik: api.best("m" + size) ?? "-" }); }
    function flip(i) {
      const c = cards[i];
      if (lock || c.classList.contains("open") || c.classList.contains("done")) return;
      startT = true;
      c.classList.add("open"); api.sfx("flip"); open.push(i);
      if (open.length === 2) {
        moves++; lock = true;
        const [a, b] = open;
        if (deck[a] === deck[b]) {
          setTimeout(() => {
            cards[a].classList.add("done"); cards[b].classList.add("done"); api.sfx("good");
            open = []; lock = false; done++; stats();
            if (done === pairs) {
              const isNew = api.saveBest(moves, { key: "m" + size, lower: true });
              api.win({ title: "Ingatan Super!", text: `${moves} langkah · ${fmtTime(sec)}${isNew ? "\nRekor baru!" : ""}` });
            }
          }, 350);
        } else {
          setTimeout(() => { cards[a].classList.remove("open"); cards[b].classList.remove("open"); open = []; lock = false; }, 800);
        }
        stats();
      }
    }
    api.interval(() => { if (startT && done < pairs) { sec++; stats(); } }, 1000);
    root.append(api.seg([["4x3", "4×3"], ["4x4", "4×4"], ["4x5", "4×5"], ["6x6", "6×6"]], size, (v) => { api.setPref("size", v); api.restart(); }), grid);
    stats();
  },
});

/* ================= SIMON (Ingat Urutan) ================= */
registerGame({
  id: "ingat-urutan",
  name: "Ingat Urutan",
  icon: "🚦",
  cat: "memori",
  color: ["#11998e", "#2a5298"],
  desc: "Ulangi urutan warna yang menyala.",
  help: "Perhatikan urutan tombol yang menyala, lalu ulangi dengan menekan tombol yang sama. Setiap ronde, urutannya bertambah satu. Seberapa panjang yang bisa kamu ingat?",
  init(root, api) {
    const PADS = [["#2ee59d", 330], ["#ff5470", 392], ["#ffc94d", 494], ["#23d5ff", 587]];
    const seq = [];
    let idx = 0, accepting = false, over = false;
    const wrap = h("div", { class: "simon" });
    const btns = PADS.map(([c], i) => { const b = h("button", { style: { background: c, color: c }, onclick: () => press(i) }); wrap.append(b); return b; });
    const msg = h("div", { class: "big-q", style: { fontSize: "20px" } }, "Siap?");
    function tone(i, dur = 0.3) {
      if (!Sfx.on) return;
      try {
        Sfx.ctx = Sfx.ctx || new (window.AudioContext || window.webkitAudioContext)();
        const c = Sfx.ctx, o = c.createOscillator(), g = c.createGain();
        o.type = "sine"; o.frequency.value = PADS[i][1];
        g.gain.setValueAtTime(0.0001, c.currentTime); g.gain.exponentialRampToValueAtTime(0.2, c.currentTime + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + dur);
        o.connect(g).connect(c.destination); o.start(); o.stop(c.currentTime + dur + 0.05);
      } catch (e) { /* noop */ }
    }
    function lit(i, ms) { btns[i].classList.add("lit"); tone(i, ms / 1000); api.timeout(() => btns[i].classList.remove("lit"), ms); }
    function stats() { api.stats({ Ronde: seq.length, Terbaik: api.best("best", 0) }); }
    function nextRound() {
      seq.push(rand(0, 3)); idx = 0; accepting = false; stats();
      msg.textContent = "👀 Perhatikan…";
      const speed = Math.max(250, 600 - seq.length * 25);
      seq.forEach((p, k) => api.timeout(() => lit(p, speed * 0.75), 600 + k * speed));
      api.timeout(() => { accepting = true; msg.textContent = "👆 Giliranmu!"; }, 600 + seq.length * speed);
    }
    function press(i) {
      if (!accepting || over) return;
      lit(i, 220);
      if (i !== seq[idx]) {
        over = true; accepting = false;
        const sc = seq.length - 1;
        const isNew = api.saveBest(sc);
        api.result({ icon: sc >= 10 ? "🏆" : "🧠", title: `Skor: ${sc}`, text: `Kamu mengingat ${sc} urutan.${isNew ? " Rekor baru!" : ""}`, good: sc >= 8 });
        return;
      }
      idx++;
      if (idx === seq.length) { accepting = false; msg.textContent = "✅ Benar!"; api.timeout(nextRound, 800); }
    }
    const startBtn = h("button", { class: "btn primary", onclick: () => { startBtn.remove(); nextRound(); } }, "▶ Mulai");
    root.append(msg, wrap, startBtn);
    stats();
  },
});

/* ================= INGAT ANGKA ================= */
registerGame({
  id: "ingat-angka",
  name: "Ingat Angka",
  icon: "🔟",
  cat: "memori",
  color: ["#c33764", "#1d2671"],
  desc: "Hafalkan deretan angka yang muncul.",
  help: "Sebuah angka akan muncul sebentar. Hafalkan, lalu ketik ulang setelah angkanya hilang. Setiap jawaban benar, angkanya bertambah satu digit. Kamu punya 3 nyawa.",
  init(root, api) {
    let digits = 3, lives = 3, cur = "", over = false;
    const show = h("div", { class: "flash-num" });
    const bar = h("div", { class: "progress" }, h("i", { style: { width: "100%" } }));
    const input = h("input", { class: "input-num", type: "text", inputmode: "numeric", autocomplete: "off", placeholder: "Ketik angka…" });
    const go = h("button", { class: "btn primary", onclick: check }, "Jawab");
    const inputRow = h("div", { class: "row", style: { flexDirection: "column", display: "none" } }, input, go);
    function stats() { api.stats({ Digit: digits, Nyawa: "❤️".repeat(lives) + "🖤".repeat(3 - lives), Terbaik: api.best("best", 0) }); }
    function round() {
      cur = Array.from({ length: digits }, (_, k) => (k === 0 ? rand(1, 9) : rand(0, 9))).join("");
      show.textContent = cur; inputRow.style.display = "none"; input.value = "";
      const ms = 900 + digits * 450;
      bar.firstChild.style.transition = "none"; bar.firstChild.style.width = "100%"; void bar.offsetWidth;
      bar.firstChild.style.transition = `width ${ms}ms linear`; bar.firstChild.style.width = "0%";
      api.timeout(() => { show.textContent = "❓".repeat(Math.min(digits, 8)); inputRow.style.display = "flex"; input.focus(); }, ms);
      stats();
    }
    function check() {
      if (over) return;
      if (input.value.trim() === cur) {
        api.sfx("good"); toast("✅ Benar!"); api.saveBest(digits); digits++; round();
      } else {
        api.sfx("bad"); lives--; stats();
        show.textContent = cur;
        if (lives <= 0) {
          over = true;
          const sc = digits - 1;
          api.result({ icon: sc >= 9 ? "🏆" : "🧠", title: `${sc} digit`, text: `Angka terakhir: ${cur}\nRekor: ${api.best("best", 0)} digit`, good: sc >= 7 });
        } else { toast(`❌ Jawabannya ${cur}`); api.timeout(round, 1400); }
      }
    }
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") check(); });
    const startBtn = h("button", { class: "btn primary", onclick: () => { startBtn.remove(); round(); } }, "▶ Mulai");
    root.append(h("div", { class: "panel", style: { display: "flex", flexDirection: "column", gap: "14px", alignItems: "center" } }, bar, show, inputRow, startBtn));
    stats();
  },
});

/* ================= WARNA KATA (Stroop) ================= */
registerGame({
  id: "warna-kata",
  name: "Warna Kata",
  icon: "🌈",
  cat: "memori",
  color: ["#f857a6", "#ff5858"],
  desc: "Pilih WARNA tulisannya, bukan katanya!",
  help: "Sebuah nama warna akan muncul dengan warna tinta yang berbeda. Pilih WARNA TINTA-nya, bukan tulisan katanya!\n\nContoh: kata \"MERAH\" ditulis dengan tinta biru → jawab BIRU. Kamu punya 30 detik.",
  init(root, api) {
    const C = [["MERAH", "#ff4d6d"], ["BIRU", "#3d8bff"], ["HIJAU", "#2ee59d"], ["KUNING", "#ffd43b"], ["UNGU", "#b06bff"], ["ORANYE", "#ff922b"]];
    let score = 0, wrong = 0, time = 30, over = false, ans = 0;
    const word = h("div", { class: "big-q", style: { fontSize: "52px", fontWeight: 800, letterSpacing: "2px", minHeight: "70px" } });
    const bar = h("div", { class: "progress" }, h("i", { style: { width: "100%" } }));
    const choices = h("div", { class: "choices", style: { gridTemplateColumns: "1fr 1fr 1fr" } });
    function make() {
      const w = rand(0, C.length - 1);
      ans = Math.random() < 0.25 ? w : (w + rand(1, C.length - 1)) % C.length;
      word.textContent = C[w][0]; word.style.color = C[ans][1];
      word.classList.remove("bump"); void word.offsetWidth; word.classList.add("bump");
      choices.innerHTML = "";
      shuffle(C.map((_, i) => i)).forEach((i) => choices.append(h("button", { class: "choice", onclick: () => answer(i) }, C[i][0])));
    }
    function answer(i) {
      if (over) return;
      if (i === ans) { score++; api.sfx("good"); } else { wrong++; time -= 2; api.sfx("bad"); word.classList.add("shake"); }
      stats(); make();
    }
    function stats() { api.stats({ Skor: score, Salah: wrong, Waktu: Math.max(0, Math.ceil(time)), Terbaik: api.best("best", 0) }); }
    api.interval(() => {
      if (over) return;
      time -= 0.1; bar.firstChild.style.width = `${Math.max(0, (time / 30) * 100)}%`;
      if (Math.abs(time - Math.round(time)) < 0.05) stats();
      if (time <= 0) {
        over = true; stats();
        const isNew = api.saveBest(score);
        api.result({ icon: score >= 25 ? "🏆" : "🌈", title: `Skor: ${score}`, text: `Salah: ${wrong}${isNew ? "\nRekor baru!" : ""}`, good: score >= 15 });
      }
    }, 100);
    root.append(h("div", { class: "panel", style: { display: "flex", flexDirection: "column", gap: "16px" } }, bar, word, choices));
    make(); stats();
  },
});

/* ================= CARI BEDA ================= */
registerGame({
  id: "cari-beda",
  name: "Cari Warna Beda",
  icon: "👁️",
  cat: "memori",
  color: ["#00d2ff", "#928dab"],
  desc: "Temukan satu kotak yang warnanya beda.",
  help: "Ada satu kotak dengan warna yang sedikit berbeda. Ketuk kotak itu secepat mungkin! Semakin tinggi level, kotak makin banyak dan bedanya makin tipis. Waktu 60 detik, salah ketuk −3 detik.",
  init(root, api) {
    let level = 1, time = 60, over = false, odd = 0;
    const grid = h("div", { class: "odd" });
    const bar = h("div", { class: "progress" }, h("i", { style: { width: "100%" } }));
    function make() {
      const n = Math.min(2 + Math.floor((level + 1) / 2), 8);
      const hue = rand(0, 359), sat = rand(55, 85), lig = rand(45, 60);
      const delta = Math.max(4, 26 - level * 1.1);
      odd = rand(0, n * n - 1);
      grid.innerHTML = ""; grid.style.gridTemplateColumns = `repeat(${n}, 1fr)`;
      for (let i = 0; i < n * n; i++) {
        grid.append(h("button", { style: { background: `hsl(${hue}, ${sat}%, ${i === odd ? lig + delta : lig}%)` }, onclick: () => tap(i) }));
      }
    }
    function tap(i) {
      if (over) return;
      if (i === odd) { level++; api.sfx("good"); make(); }
      else { time -= 3; api.sfx("bad"); grid.classList.remove("shake"); void grid.offsetWidth; grid.classList.add("shake"); }
      stats();
    }
    function stats() { api.stats({ Level: level, Waktu: Math.max(0, Math.ceil(time)), Terbaik: api.best("best", 0) }); }
    api.interval(() => {
      if (over) return;
      time -= 0.1; bar.firstChild.style.width = `${Math.max(0, (time / 60) * 100)}%`;
      if (Math.abs(time - Math.round(time)) < 0.05) stats();
      if (time <= 0) {
        over = true; stats();
        const isNew = api.saveBest(level);
        api.result({ icon: level >= 25 ? "🦅" : "👁️", title: `Level ${level}`, text: isNew ? "Rekor baru! Matamu tajam!" : `Rekor: ${api.best("best", 0)}`, good: level >= 15 });
      }
    }, 100);
    root.append(bar, grid);
    make(); stats();
  },
});
