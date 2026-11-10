/* Dunia Puzzle — core: helpers, router, sound, modal, confetti */
"use strict";

const $ = (s, r = document) => r.querySelector(s);

function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  if (props) {
    for (const [k, v] of Object.entries(props)) {
      if (v == null || v === false) continue;
      if (k === "class") el.className = v;
      else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
      else if (k === "html") el.innerHTML = v;
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
      else el.setAttribute(k, v === true ? "" : v);
    }
  }
  for (const k of kids.flat(Infinity)) {
    if (k == null || k === false) continue;
    el.append(k.nodeType ? k : document.createTextNode(String(k)));
  }
  return el;
}

const rand = (a, b) => Math.floor(Math.random() * (b - a + 1)) + a;
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}
const fmtTime = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

const Store = {
  get(k, d) {
    try { const v = localStorage.getItem("dp_" + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; }
  },
  set(k, v) {
    try { localStorage.setItem("dp_" + k, JSON.stringify(v)); } catch (e) { /* ignore */ }
  },
};

/* ---------- Sound (WebAudio, no files needed) ---------- */
const Sfx = {
  ctx: null,
  on: Store.get("sound", true),
  seqs: {
    click: [[620, 0.04]],
    pop: [[880, 0.05]],
    flip: [[520, 0.05]],
    good: [[660, 0.08], [990, 0.12]],
    bad: [[200, 0.18]],
    win: [[523, 0.1], [659, 0.1], [784, 0.1], [1047, 0.3]],
    lose: [[392, 0.18], [330, 0.18], [262, 0.35]],
    tick: [[1200, 0.02]],
  },
  play(type) {
    if (!this.on) return;
    try {
      this.ctx = this.ctx || new (window.AudioContext || window.webkitAudioContext)();
      const c = this.ctx;
      if (c.state === "suspended") c.resume();
      let t = c.currentTime;
      const harsh = type === "bad" || type === "lose";
      for (const [f, d] of this.seqs[type] || this.seqs.click) {
        const o = c.createOscillator();
        const g = c.createGain();
        o.type = harsh ? "square" : "triangle";
        o.frequency.value = f;
        const vol = harsh ? 0.05 : 0.12;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t + d);
        o.connect(g).connect(c.destination);
        o.start(t);
        o.stop(t + d + 0.03);
        t += d * 0.85;
      }
    } catch (e) { /* audio unavailable */ }
  },
};

/* ---------- Confetti ---------- */
function confetti() {
  let cv = $("#confetti");
  if (!cv) { cv = h("canvas", { id: "confetti" }); document.body.append(cv); }
  const ctx = cv.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  cv.width = innerWidth * dpr; cv.height = innerHeight * dpr;
  ctx.scale(dpr, dpr);
  const colors = ["#ff5fa2", "#7c5cff", "#23d5ff", "#2ee59d", "#ffc94d", "#ffffff"];
  const parts = Array.from({ length: 150 }, () => ({
    x: innerWidth / 2 + (Math.random() - 0.5) * 120,
    y: innerHeight * 0.4,
    vx: (Math.random() - 0.5) * 14,
    vy: -Math.random() * 14 - 4,
    r: Math.random() * 6 + 4,
    c: pick(colors),
    a: Math.random() * Math.PI,
    va: (Math.random() - 0.5) * 0.3,
  }));
  const start = performance.now();
  function frame(now) {
    ctx.clearRect(0, 0, innerWidth, innerHeight);
    for (const p of parts) {
      p.vy += 0.35; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.a += p.va;
      ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.a);
      ctx.fillStyle = p.c; ctx.fillRect(-p.r / 2, -p.r / 4, p.r, p.r / 2);
      ctx.restore();
    }
    if (now - start < 3000) requestAnimationFrame(frame);
    else ctx.clearRect(0, 0, innerWidth, innerHeight);
  }
  requestAnimationFrame(frame);
}

/* ---------- Modal & toast ---------- */
function closeModal() { const m = $(".modal-bg"); if (m) m.remove(); }
function showModal({ icon = "🎉", title, text = "", body = null, buttons = [] }) {
  closeModal();
  const bg = h("div", { class: "modal-bg" },
    h("div", { class: "modal" },
      h("div", { class: "m-icon" }, icon),
      h("h3", null, title),
      text ? h("p", null, text) : null,
      body,
      h("div", { class: "row" },
        buttons.map((b) => h("button", {
          class: "btn " + (b.primary ? "primary" : ""),
          onclick: () => { Sfx.play("click"); closeModal(); b.action && b.action(); },
        }, b.label))
      )
    )
  );
  document.body.append(bg);
}
let toastTimer;
function toast(msg, ms = 1600) {
  document.querySelectorAll(".toast").forEach((t) => t.remove());
  const t = h("div", { class: "toast" }, msg);
  document.body.append(t);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.remove(), ms);
}

/* ---------- Game registry ---------- */
const GAMES = [];
function registerGame(def) { GAMES.push(def); }
const CATS = [
  ["all", "✨ Semua"],
  ["kata", "🔤 Kata"],
  ["logika", "🧩 Logika"],
  ["angka", "🔢 Angka"],
  ["memori", "🧠 Memori"],
  ["strategi", "♟️ Strategi"],
];

/* ---------- Router ---------- */
let cleanupFns = [];
function runCleanup() {
  for (const f of cleanupFns) { try { f(); } catch (e) { console.error(e); } }
  cleanupFns = [];
}

function route() {
  runCleanup();
  closeModal();
  const m = location.hash.match(/^#\/main\/([\w-]+)/);
  const game = m && GAMES.find((g) => g.id === m[1]);
  window.scrollTo(0, 0);
  if (game) renderGame(game);
  else renderHome();
}
window.addEventListener("hashchange", route);

/* ---------- Home ---------- */
let homeCat = Store.get("homeCat", "all");
let homeQuery = "";

function totalWins() {
  return GAMES.reduce((s, g) => s + Store.get("wins_" + g.id, 0), 0);
}

function renderHome() {
  const app = $("#app");
  app.innerHTML = "";
  document.title = "Dunia Puzzle";

  const soundBtn = h("button", {
    class: "icon-btn", "aria-label": "Suara",
    onclick: () => {
      Sfx.on = !Sfx.on; Store.set("sound", Sfx.on);
      soundBtn.textContent = Sfx.on ? "🔊" : "🔇"; Sfx.play("click");
    },
  }, Sfx.on ? "🔊" : "🔇");

  const played = GAMES.filter((g) => Store.get("wins_" + g.id, 0) > 0).length;
  const grid = h("div", { class: "games" });

  function fill() {
    grid.innerHTML = "";
    const q = homeQuery.trim().toLowerCase();
    const list = GAMES.filter((g) => (homeCat === "all" || g.cat === homeCat) &&
      (!q || g.name.toLowerCase().includes(q) || g.desc.toLowerCase().includes(q)));
    if (!list.length) grid.append(h("div", { class: "empty" }, "😕 Game tidak ditemukan"));
    list.forEach((g, i) => {
      const wins = Store.get("wins_" + g.id, 0);
      grid.append(h("div", {
        class: "gcard",
        style: { background: `linear-gradient(145deg, ${g.color[0]}, ${g.color[1]})`, animationDelay: `${Math.min(i, 12) * 0.03}s` },
        onclick: () => { Sfx.play("click"); location.hash = "#/main/" + g.id; },
      },
        h("span", { class: "num" }, "#" + String(GAMES.indexOf(g) + 1).padStart(2, "0")),
        wins ? h("span", { class: "wins" }, "🏆 " + wins) : null,
        h("span", { class: "gi" }, g.icon),
        h("h3", null, g.name),
        h("p", null, g.desc)
      ));
    });
  }

  const chips = h("div", { class: "chips" },
    CATS.map(([id, label]) => h("button", {
      class: "chip" + (homeCat === id ? " active" : ""),
      onclick: (e) => {
        homeCat = id; Store.set("homeCat", id); Sfx.play("click");
        chips.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
        e.currentTarget.classList.add("active");
        fill();
      },
    }, label))
  );

  const search = h("input", { class: "search", placeholder: "Cari game…", type: "search", value: homeQuery });
  search.addEventListener("input", () => { homeQuery = search.value; fill(); });

  const hero = h("div", { class: "hero", onclick: () => { Sfx.play("click"); location.hash = "#/main/tebak-kata"; } },
    h("span", { class: "tag" }, "⭐ Favorit"),
    h("h2", null, "Tebak Kata"),
    h("p", null, `Tebak kata dari ${WORD_COUNT}+ kata. Salah tebak, potongan tubuh muncul!`),
    h("button", { class: "play" }, "▶ Main sekarang"),
    h("div", { class: "hero-art", html: HANGMAN_MINI_SVG })
  );

  app.append(
    h("div", { class: "home-top" },
      h("div", { class: "brand" },
        h("div", { class: "brand-logo" }, "🧩"),
        h("div", null, h("h1", null, "Dunia Puzzle"), h("p", null, `${GAMES.length} game asah otak`))
      ),
      soundBtn
    ),
    hero,
    h("div", { class: "summary" },
      h("div", null, h("b", null, GAMES.length), h("span", null, "Game")),
      h("div", null, h("b", null, totalWins()), h("span", null, "Total Menang")),
      h("div", null, h("b", null, `${played}`), h("span", null, "Sudah Ditaklukkan"))
    ),
    search,
    chips,
    grid,
    h("div", { class: "footer" }, "Dibuat dengan ❤️ · Bisa dimainkan offline")
  );
  fill();
}

const HANGMAN_MINI_SVG = `<svg viewBox="0 0 120 120" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
<path d="M14 112h60M30 112V12h52v16" opacity=".9"/><circle cx="82" cy="40" r="11"/><path d="M82 51v28M82 60l-14 10M82 60l14 10M82 79l-11 20M82 79l11 20"/></svg>`;

/* ---------- Game screen ---------- */
function renderGame(game) {
  const app = $("#app");
  app.innerHTML = "";
  document.title = game.name + " · Dunia Puzzle";

  const statsEl = h("div", { class: "stats" });
  const body = h("div", { class: "game-body" });

  const showHelp = () => showModal({
    icon: game.icon, title: game.name,
    body: h("p", { class: "help-text" }, game.help),
    buttons: [{ label: "Mengerti!", primary: true }],
  });

  app.append(
    h("div", { class: "game-top" },
      h("button", { class: "icon-btn", "aria-label": "Kembali", onclick: () => { Sfx.play("click"); location.hash = "#/"; } }, "←"),
      h("div", { class: "title" }, h("span", null, game.icon), h("h2", null, game.name)),
      h("button", { class: "icon-btn", "aria-label": "Bantuan", onclick: showHelp }, "❔"),
      h("button", { class: "icon-btn", "aria-label": "Ulangi", onclick: () => { Sfx.play("click"); start(); } }, "↻")
    ),
    statsEl,
    body
  );

  function start() {
    runCleanup();
    closeModal();
    body.innerHTML = "";
    statsEl.innerHTML = "";
    body.style.animation = "none"; void body.offsetWidth; body.style.animation = "";
    const api = makeApi(game, body, statsEl, start);
    try {
      const c = game.init(body, api);
      if (typeof c === "function") cleanupFns.push(c);
    } catch (e) {
      console.error(e);
      body.append(h("p", { class: "note" }, "Terjadi kesalahan: " + e.message));
    }
  }
  start();

  if (!Store.get("seen_" + game.id, false)) {
    Store.set("seen_" + game.id, true);
    setTimeout(showHelp, 250);
  }
}

function makeApi(game, body, statsEl, restart) {
  const api = {
    sfx: (t) => Sfx.play(t),
    toast,
    restart,
    h,
    stats(obj) {
      statsEl.innerHTML = "";
      for (const [k, v] of Object.entries(obj)) {
        statsEl.append(h("div", { class: "stat" }, h("small", null, k), h("b", null, v)));
      }
    },
    pref(key, d) { return Store.get(`pref_${game.id}_${key}`, d); },
    setPref(key, v) { Store.set(`pref_${game.id}_${key}`, v); },
    best(key = "best", d = null) { return Store.get(`best_${game.id}_${key}`, d); },
    saveBest(value, { key = "best", lower = false } = {}) {
      const cur = api.best(key);
      if (cur == null || (lower ? value < cur : value > cur)) { Store.set(`best_${game.id}_${key}`, value); return true; }
      return false;
    },
    interval(fn, ms) { const id = setInterval(fn, ms); cleanupFns.push(() => clearInterval(id)); return id; },
    timeout(fn, ms) { const id = setTimeout(fn, ms); cleanupFns.push(() => clearTimeout(id)); return id; },
    on(target, ev, fn, opts) { target.addEventListener(ev, fn, opts); cleanupFns.push(() => target.removeEventListener(ev, fn, opts)); },
    onCleanup(fn) { cleanupFns.push(fn); },
    seg(options, current, onChange) {
      const wrap = h("div", { class: "seg" });
      options.forEach(([val, label]) => {
        wrap.append(h("button", {
          class: val === current ? "on" : "",
          onclick: () => { Sfx.play("click"); onChange(val); },
        }, label));
      });
      return wrap;
    },
    win({ title = "Kamu Menang!", text = "", icon = "🏆", next = "Main Lagi", extra = [] } = {}) {
      Store.set("wins_" + game.id, Store.get("wins_" + game.id, 0) + 1);
      Sfx.play("win");
      confetti();
      api.timeout(() => showModal({
        icon, title, text,
        buttons: [...extra, { label: "Menu", action: () => (location.hash = "#/") }, { label: next, primary: true, action: restart }],
      }), 450);
    },
    lose({ title = "Yah, Kalah!", text = "", icon = "😵", next = "Coba Lagi" } = {}) {
      Sfx.play("lose");
      api.timeout(() => showModal({
        icon, title, text,
        buttons: [{ label: "Menu", action: () => (location.hash = "#/") }, { label: next, primary: true, action: restart }],
      }), 450);
    },
    result({ icon = "⭐", title, text, good = true }) {
      if (good) { Store.set("wins_" + game.id, Store.get("wins_" + game.id, 0) + 1); Sfx.play("win"); confetti(); }
      else Sfx.play("lose");
      api.timeout(() => showModal({
        icon, title, text,
        buttons: [{ label: "Menu", action: () => (location.hash = "#/") }, { label: "Main Lagi", primary: true, action: restart }],
      }), 400);
    },
    /** attach swipe + arrow keys; cb receives "up" | "down" | "left" | "right" */
    swipe(el, cb) {
      let sx = 0, sy = 0, active = false;
      api.on(el, "pointerdown", (e) => { sx = e.clientX; sy = e.clientY; active = true; });
      api.on(el, "pointerup", (e) => {
        if (!active) return; active = false;
        const dx = e.clientX - sx, dy = e.clientY - sy;
        if (Math.max(Math.abs(dx), Math.abs(dy)) < 24) return;
        if (Math.abs(dx) > Math.abs(dy)) cb(dx > 0 ? "right" : "left"); else cb(dy > 0 ? "down" : "up");
      });
      api.on(window, "keydown", (e) => {
        const map = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right", w: "up", s: "down", a: "left", d: "right" };
        if (map[e.key]) { e.preventDefault(); cb(map[e.key]); }
      });
    },
    /** on-screen A-Z keyboard. onKey(letter) ; returns {el, mark(letter, cls)} */
    keyboard(onKey, { enter = false, back = false } = {}) {
      const rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"];
      const keys = {};
      const el = h("div", { class: "kbd" });
      rows.forEach((r, i) => {
        const row = h("div", { class: "kbd-row" });
        if (i === 2 && enter) row.append(h("button", { class: "key wide", onclick: () => onKey("ENTER") }, "ENTER"));
        for (const ch of r) {
          const k = h("button", { class: "key", onclick: () => onKey(ch) }, ch);
          keys[ch] = k; row.append(k);
        }
        if (i === 2 && back) row.append(h("button", { class: "key wide", onclick: () => onKey("BACK") }, "⌫"));
        el.append(row);
      });
      api.on(window, "keydown", (e) => {
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        if (document.activeElement && document.activeElement.tagName === "INPUT") return;
        if (e.key === "Enter" && enter) { e.preventDefault(); onKey("ENTER"); }
        else if (e.key === "Backspace" && back) { e.preventDefault(); onKey("BACK"); }
        else if (/^[a-zA-Z]$/.test(e.key)) onKey(e.key.toUpperCase());
      });
      return {
        el,
        mark(ch, cls) {
          const k = keys[ch]; if (!k) return;
          const rank = { x: 1, y: 2, g: 3 };
          const cur = ["g", "y", "x"].find((c) => k.classList.contains(c));
          if (rank[cls] && cur && rank[cur] >= rank[cls]) return;
          if (rank[cls]) k.classList.remove("g", "y", "x");
          k.classList.add(cls);
        },
      };
    },
  };
  return api;
}

/* ---------- Boot ---------- */
window.addEventListener("DOMContentLoaded", () => {
  route();
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
});
