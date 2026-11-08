/* Layer switcher for the microsite. Geometry comes from site/board.js. */
(function () {
  const MOD = new Set(["TAB", "ESC", "LSHFT", "RSHFT", "LCTRL", "LALT", "FN", "RAISE", "SPACE", "BSPC", "RET"]);
  const LOWER = {
    Q: "1", W: "2", E: "3", R: "4", T: "5", Y: "6", U: "7", I: "8", O: "9", P: "0",
    A: "F1", S: "F2", D: "F3", F: "F4", G: "F5", H: "F6", J: "F7", K: "F8", L: "F9",
    SEMI: "F10", SQT: "F11", BSPC: "Del", UP: "PgUp", DOWN: "PgDn", LEFT: "Home", RIGHT: "End"
  };
  const RAISE = { ESC: "Boot", TAB: "Reset" };
  const NOTES = {
    base: "Printed legends. The memory LCD reads BASE. Hold Lower or Raise to see the other layers.",
    lower: "Q through P become 1 through 0. A through the quote key become F1 through F11. Backspace is Delete. Left, Down, Up, and Right become Home, Page Down, Page Up, and End.",
    raise: "Esc asks for the bootloader. Tab asks for reset. Every other key keeps its base meaning. Raise then Esc is the binding. It still needs the J6/J7 hardware path on a real board."
  };
  const NS = "http://www.w3.org/2000/svg";

  function el(name, attrs, parent) {
    const node = document.createElementNS(NS, name);
    Object.entries(attrs || {}).forEach(function (pair) { node.setAttribute(pair[0], pair[1]); });
    if (parent) parent.appendChild(node);
    return node;
  }

  function ring(points) {
    return points.map(function (p, i) { return (i ? "L" : "M") + p[0] + " " + p[1]; }).join("") + "Z";
  }

  function fontSize(text) {
    if (text.length >= 6) return "2.8";
    if (text.length >= 5) return "3.25";
    if (text.length >= 4) return "3.7";
    return "4.4";
  }

  function legendFor(code, label, layer) {
    if (layer === "lower" && LOWER[code]) return { text: LOWER[code], changed: true, dim: false, held: false };
    if (layer === "raise" && RAISE[code]) return { text: RAISE[code], changed: true, dim: false, held: false };
    const held = (layer === "lower" && code === "FN") || (layer === "raise" && code === "RAISE");
    return { text: label, changed: false, dim: layer !== "base" && !held, held: held };
  }

  function build(host) {
    const board = window.BOARD;
    const uid = host.id || "board";
    host.textContent = "";
    const svg = el("svg", {
      viewBox: "-160 -78 322 176",
      role: "img",
      "aria-labelledby": uid + "-title"
    }, host);
    const defs = el("defs", {}, svg);
    const deck = el("linearGradient", { id: uid + "-deck", x1: "0", y1: "0", x2: "0", y2: "1" }, defs);
    el("stop", { offset: "0", "stop-color": "#f4f6f7" }, deck);
    el("stop", { offset: "1", "stop-color": "#c5c9ce" }, deck);
    const palm = el("linearGradient", { id: uid + "-palm", x1: "0", y1: "0", x2: "0", y2: "1" }, defs);
    el("stop", { offset: "0", "stop-color": "#9aa1a8" }, palm);
    el("stop", { offset: "1", "stop-color": "#5e656c" }, palm);
    el("title", { id: uid + "-title" }, svg).textContent = "worxboard ergo, 48-key split Planck";

    const shadow = el("g", {}, svg);
    el("path", {
      d: ring(board.outline),
      fill: "url(#" + uid + "-deck)",
      stroke: "#8d9399",
      "stroke-width": "0.6"
    }, shadow);
    el("path", {
      d: ring(board.palm),
      fill: "url(#" + uid + "-palm)",
      stroke: "#4e555c",
      "stroke-width": "0.45"
    }, shadow);

    board.holes.forEach(function (h) {
      el("circle", { cx: h[0], cy: h[1], r: "1.35", fill: "none", stroke: "#5e666d", "stroke-width": "0.4" }, shadow);
    });
    board.palm_screws.forEach(function (h) {
      el("circle", { cx: h[0], cy: h[1], r: "1.15", fill: "none", stroke: "#2e3439", "stroke-width": "0.4" }, shadow);
    });
    Object.keys(board.ports).forEach(function (name) {
      const p = board.ports[name];
      el("rect", {
        x: p[0] - 5, y: p[1] - 2, width: "10", height: "4", rx: "0.7", fill: "#22262b"
      }, shadow);
    });

    const display = board.display;
    el("rect", {
      x: display.x - display.window_width / 2,
      y: display.y - display.window_depth / 2,
      width: display.window_width,
      height: display.window_depth,
      rx: "1.2",
      fill: "#14312e",
      stroke: "#8fb9ae",
      "stroke-width": "0.35"
    }, shadow);
    const lcd = el("text", {
      class: "lcd-text",
      x: display.x,
      y: display.y + 0.4,
      "text-anchor": "middle",
      "dominant-baseline": "middle",
      fill: "#d7efe8",
      "font-size": "3.1"
    }, shadow);
    lcd.textContent = "BASE";

    board.keys.forEach(function (key) {
      const g = el("g", {
        class: "key" + (MOD.has(key.code) ? " mod" : ""),
        transform: "translate(" + key.x + " " + key.y + ") rotate(" + key.angle + ")"
      }, shadow);
      g.dataset.code = key.code;
      g.dataset.label = key.label;
      el("rect", { class: "cap", x: "-8.55", y: "-8.45", width: "17.1", height: "16.9", rx: "1.7" }, g);
      el("text", {
        class: "legend",
        y: "0.2",
        "text-anchor": "middle",
        "dominant-baseline": "middle"
      }, g);
      el("circle", { class: "led", cx: "0", cy: "6.85", r: "0.55" }, g);
    });
    return svg;
  }

  function paint(svg, layer) {
    svg.querySelectorAll(".key").forEach(function (g) {
      const next = legendFor(g.dataset.code, g.dataset.label, layer);
      g.classList.toggle("changed", next.changed);
      g.classList.toggle("dim", next.dim);
      g.classList.toggle("held", next.held);
      const text = g.querySelector(".legend");
      text.textContent = next.text;
      text.setAttribute("font-size", fontSize(next.text));
    });
    const lcd = svg.querySelector(".lcd-text");
    if (lcd) lcd.textContent = layer.toUpperCase();
  }

  function mount(id) {
    const host = document.getElementById(id);
    if (!host || !window.BOARD) return null;
    return build(host);
  }

  const hero = mount("hero-board");
  const live = mount("layer-board");
  if (hero) paint(hero, "base");

  const params = new URLSearchParams(window.location.search);
  const initial = NOTES[params.get("layer")] ? params.get("layer") : "base";
  if (live) paint(live, initial);

  const note = document.getElementById("layer-note");
  const buttons = document.querySelectorAll(".switcher button");
  if (note) note.textContent = NOTES[initial];
  buttons.forEach(function (button) {
    button.setAttribute("aria-pressed", button.dataset.layer === initial ? "true" : "false");
    button.addEventListener("click", function () {
      const layer = button.dataset.layer;
      buttons.forEach(function (other) { other.setAttribute("aria-pressed", other === button ? "true" : "false"); });
      if (live) paint(live, layer);
      if (note) note.textContent = NOTES[layer];
      const url = new URL(window.location.href);
      if (layer === "base") url.searchParams.delete("layer");
      else url.searchParams.set("layer", layer);
      history.replaceState(null, "", url);
    });
  });
})();
