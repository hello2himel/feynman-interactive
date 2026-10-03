/* Mirror theme control: light / dark / system.
 *
 * Loaded synchronously in <head> (see scripts/theme_patch.py) so the stored
 * choice applies before first paint (no theme flash). The toggle button
 * itself is wired on DOMContentLoaded.
 *
 * Modes: null = follow the OS (default, attribute removed), or explicit
 * "light" / "dark" pinned via the data-theme attribute and localStorage.
 */
(function () {
  var KEY = "feynman-theme";
  var LABELS = { system: "\u25D0 System", light: "\u2600 Light", dark: "\u263E Dark" };

  function stored() {
    try {
      return window.localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  function save(mode) {
    try {
      if (mode === null) window.localStorage.removeItem(KEY);
      else window.localStorage.setItem(KEY, mode);
    } catch (e) {
      /* storage unavailable: still apply for this session */
    }
  }

  function current() {
    var s = stored();
    return s === "light" || s === "dark" ? s : null;
  }

  function paint(mode) {
    var el = document.documentElement;
    if (mode === "light" || mode === "dark") el.setAttribute("data-theme", mode);
    else el.removeAttribute("data-theme");
    var btn = document.getElementById("theme");
    if (btn) {
      var label = mode === null ? LABELS.system : LABELS[mode];
      if (btn.textContent !== label) btn.textContent = label;
      btn.setAttribute("aria-label", "Colour theme: " + label + ". Activate to change.");
    }
  }

  function cycle() {
    var cur = current();
    var next = cur === null ? "light" : cur === "light" ? "dark" : null;
    save(next);
    paint(next);
  }

  window.__feynmanThemeCycle = cycle;

  paint(current());

  document.addEventListener("DOMContentLoaded", function () {
    paint(current());
    var btn = document.getElementById("theme");
    if (btn && !btn.dataset.wired) {
      btn.dataset.wired = "1";
      btn.addEventListener("click", cycle);
    }
  });
})();
