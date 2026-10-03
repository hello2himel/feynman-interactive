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

/* Mirror interaction layer: divider, cues, controls, hints, guards.
 * All progressive enhancement over the upstream bundle — every block is
 * null-guarded and runs only for elements that exist. Nothing here is
 * required for the app to work; it only makes it work better. */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  }

  /* Let the app (not the browser) own scroll position on reload. */
  try {
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  } catch (e) {
    /* ignore */
  }

  /* Suspend the bundle's global letter shortcuts while a modal dialog is
   * open (capture phase runs before the bundle's bubble listener). */
  document.addEventListener(
    "keydown",
    function (e) {
      if (document.querySelector("dialog[open]")) e.stopPropagation();
    },
    true
  );

  onReady(function () {
    /* ---------- split pane: clamp stored value, keyboard divider ---------- */
    try {
      var s = window.localStorage.getItem("split");
      var n = s ? parseFloat(s) : NaN;
      if (isFinite(n)) {
        n = Math.min(60, Math.max(30, n));
        document.documentElement.style.setProperty("--split", n + "%");
      }
    } catch (e) {
      /* ignore */
    }

    var divider = $("divider");
    if (divider) {
      var setSplit = function (pct, save) {
        pct = Math.min(75, Math.max(25, pct));
        document.documentElement.style.setProperty("--split", pct + "%");
        divider.setAttribute("aria-valuenow", String(Math.round(pct)));
        if (save !== false) {
          try {
            window.localStorage.setItem("split", pct + "%");
          } catch (e) {
            /* ignore */
          }
        }
      };
      divider.addEventListener("keydown", function (e) {
        var cur = parseFloat(
          getComputedStyle(document.documentElement).getPropertyValue("--split")
        );
        if (!isFinite(cur)) cur = 46;
        if (e.key === "ArrowLeft") {
          setSplit(cur - 5);
          e.preventDefault();
        } else if (e.key === "ArrowRight") {
          setSplit(cur + 5);
          e.preventDefault();
        }
      });
      divider.addEventListener("dblclick", function () {
        setSplit(46);
        try {
          window.localStorage.removeItem("split");
        } catch (e) {
          /* ignore */
        }
      });
    }

    /* ---------- cue position: counter, ends, live region ---------- */
    var column = $("column");
    var prev = $("prev-cue");
    var next = $("next-cue");
    var count = $("cue-count");
    var live = $("pos-live");
    var updateCues = function () {
      if (!column) return;
      var marks = column.querySelectorAll(".cue-mark");
      if (!marks.length) return;
      var active = -1;
      for (var i = 0; i < marks.length; i++) {
        if (marks[i].classList.contains("active")) active = i;
      }
      if (count) {
        count.textContent =
          active >= 0
            ? "Demo " + (active + 1) + " of " + marks.length
            : marks.length + " demo points";
      }
      if (prev) prev.disabled = active <= 0;
      if (next) next.disabled = active >= marks.length - 1;
      if (live && active >= 0 && updateCues.last !== active) {
        updateCues.last = active;
        var note = marks[active].getAttribute("aria-label") || "";
        live.textContent =
          "Demo " + (active + 1) + " of " + marks.length + (note ? ": " + note : "");
      }
    };
    updateCues.last = -2;
    if (column && (prev || next || count || live) && window.MutationObserver) {
      var queued = false;
      var mo = new MutationObserver(function () {
        if (queued) return;
        queued = true;
        setTimeout(function () {
          queued = false;
          try {
            updateCues();
          } catch (e) {
            /* ignore */
          }
        }, 120);
      });
      mo.observe(column, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["class"],
      });
    }

    /* ---------- controls: expose values, label tables ---------- */
    var controls = $("controls");
    if (controls) {
      controls.addEventListener("input", function (e) {
        var t = e.target;
        if (!t || t.type !== "range") return;
        var wrap = t.closest ? t.closest(".ctl") : null;
        var val = wrap ? wrap.querySelector(".ctl-val") : null;
        if (val && val.textContent) {
          try {
            t.setAttribute("aria-valuetext", val.textContent.trim());
          } catch (err) {
            /* ignore */
          }
        }
      });
    }
    var panel = $("panel");
    if (panel && window.MutationObserver) {
      var scopeTables = function () {
        var ths = panel.querySelectorAll("th:not([scope])");
        for (var i = 0; i < ths.length; i++) ths[i].setAttribute("scope", "col");
      };
      scopeTables();
      new MutationObserver(scopeTables).observe(panel, {
        childList: true,
        subtree: true,
      });
    }

    /* Overlay labels duplicate the demo note + data table. */
    var labels = $("labels");
    if (labels) labels.setAttribute("aria-hidden", "true");

    /* ---------- predict: retry path + live outcome ---------- */
    var predict = $("predict");
    if (predict && window.MutationObserver) {
      var armRetry = function () {
        var out = predict.querySelector(".predict-out");
        var opts = predict.querySelectorAll(".predict-opts button");
        if (!out || !out.textContent.trim() || !opts.length) return;
        out.setAttribute("role", "status");
        if (predict.querySelector(".predict-retry")) return;
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "predict-retry";
        btn.textContent = "Try again";
        btn.title = "Re-enable the options and clear saved answers";
        btn.addEventListener("click", function () {
          try {
            var doomed = [];
            for (var i = 0; i < window.localStorage.length; i++) {
              var k = window.localStorage.key(i);
              if (k && k.indexOf("predict:") === 0) doomed.push(k);
            }
            doomed.forEach(function (k) {
              window.localStorage.removeItem(k);
            });
          } catch (e) {
            /* ignore */
          }
          for (var j = 0; j < opts.length; j++) {
            opts[j].disabled = false;
            opts[j].classList.remove("right", "wrong");
          }
          out.textContent = "";
          btn.remove();
        });
        predict.appendChild(btn);
      };
      new MutationObserver(armRetry).observe(predict, {
        childList: true,
        subtree: true,
      });
      armRetry();
    }

    /* ---------- reduced motion: start paused ---------- */
    try {
      if (
        window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ) {
        var play = $("play");
        if (play && play.textContent.trim().toLowerCase() === "pause") play.click();
      }
    } catch (e) {
      /* ignore */
    }

    /* ---------- missing PDF: retry + orphan-demo banner ---------- */
    var missing = $("missing");
    var orphan = $("demo-orphan");
    var retry = $("retry-pdf");
    if (retry) {
      retry.addEventListener("click", function () {
        window.location.reload();
      });
    }
    var syncOrphan = function () {
      if (missing && orphan && !missing.hidden) orphan.hidden = false;
    };
    syncOrphan();
    /* The bundle unhides #missing asynchronously after the PDF fetch fails,
     * usually after DOMContentLoaded — watch for it. */
    if (missing && orphan && window.MutationObserver) {
      new MutationObserver(syncOrphan).observe(missing, {
        attributes: true,
        attributeFilter: ["hidden"],
      });
    }

    /* ---------- one-time first-visit hint ---------- */
    var seen = null;
    try {
      seen = window.localStorage.getItem("feynman-hint-seen");
    } catch (e) {
      seen = "yes";
    }
    if (!seen) {
      var head = document.querySelector(".stage-head");
      if (head) {
        var hint = document.createElement("p");
        hint.id = "first-hint";
        hint.innerHTML =
          "Tip: <em>J</em> / <em>K</em> step demos, <em>H</em> holds one, drag the demo to orbit \u2014 <em>i</em> (top right) explains everything.";
        var got = document.createElement("button");
        got.type = "button";
        got.textContent = "Got it";
        got.addEventListener("click", function () {
          try {
            window.localStorage.setItem("feynman-hint-seen", "yes");
          } catch (e) {
            /* ignore */
          }
          hint.remove();
        });
        hint.appendChild(got);
        head.appendChild(hint);
      }
    }
  });
})();
