/* Jump palette: Ctrl/Cmd+K or "/" lists all 14 chapters + 78 sections +
 * recent points. Commits by setting the real selects and instant-jumping
 * (never dispatches change, so no bundle smooth flight starts).
 * Mirror-owned; loaded with defer after theme.js. */
(function () {
  "use strict";

  function $(id) {
    return document.getElementById(id);
  }

  var built = false;
  var pal = null;
  var palInput = null;
  var palList = null;
  var lastFocus = null;

  function secs() {
    var out = [];
    try {
      (window.__NAV || []).forEach(function (ch) {
        (ch[3] || []).forEach(function (s) {
          out.push({ ch: ch[0], chTitle: ch[1], id: s[0], title: s[1] });
        });
      });
    } catch (e) {
      /* ignore */
    }
    return out;
  }

  function points() {
    try {
      var arr = JSON.parse(window.localStorage.getItem("feynman-points") || "[]");
      return Array.isArray(arr) ? arr.slice(0, 6) : [];
    } catch (e) {
      return [];
    }
  }

  function goSection(chN, secId) {
    try {
      var gk = $("chapter"),
        sk = $("section");
      if (gk) {
        var has = false;
        for (var i = 0; i < gk.options.length; i++) {
          if (gk.options[i].value === String(chN)) {
            has = true;
            break;
          }
        }
        if (has) gk.value = String(chN);
      }
      if (window.__NAV && window.__goPage) {
        outer: for (var q = 0; q < window.__NAV.length; q++) {
          if (window.__NAV[q][0] !== chN) continue;
          var ss = window.__NAV[q][3] || [];
          for (var j = 0; j < ss.length; j++) {
            if (ss[j][0] === secId) {
              window.__goPage(ss[j][2], ss[j][3] || 0);
              break outer;
            }
          }
        }
      } else if (sk) {
        sk.value = secId;
      }
      if (sk) {
        try {
          sk.value = secId;
        } catch (e) {
          /* ignore */
        }
      }
    } catch (e) {
      /* ignore */
    }
  }

  function rowHTML() {
    return "";
  }

  function render(filter) {
    palList.innerHTML = "";
    var q = (filter || "").trim().toLowerCase();
    var addRow = function (label, sub, fn, current) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "pal-row" + (current ? " on" : "");
      b.setAttribute("role", "option");
      b.setAttribute("aria-selected", current ? "true" : "false");
      b.tabIndex = -1;
      var t = document.createElement("span");
      t.className = "pal-t";
      t.textContent = label;
      b.appendChild(t);
      if (sub) {
        var s = document.createElement("span");
        s.className = "pal-s";
        s.textContent = sub;
        b.appendChild(s);
      }
      b.addEventListener("click", function () {
        fn();
        close();
      });
      palList.appendChild(b);
      return b;
    };
    var pts = points();
    if (!q && pts.length) {
      var h = document.createElement("div");
      h.className = "pal-kicker";
      h.textContent = "Pick up where you left off";
      palList.appendChild(h);
      pts.forEach(function (p) {
        addRow(
          p.t || p.h,
          p.h,
          function () {
            var m = /^#(\d+)-/.exec(p.h || "");
            if (m && window.__NAV && window.__goPage) {
              var chN = +m[1];
              for (var i = 0; i < window.__NAV.length; i++) {
                if (window.__NAV[i][0] !== chN) continue;
                var ss = window.__NAV[i][3] || [];
                for (var j = 0; j < ss.length; j++) {
                  if ((""+p.h).slice(1) === ss[j][0]) {
                    var gk = $("chapter");
                    if (gk) {
                      try {
                        gk.value = String(chN);
                      } catch (e) {}
                    }
                    window.__goPage(ss[j][2], ss[j][3] || 0);
                    return;
                  }
                }
              }
            }
            try {
              window.location.hash = p.h;
            } catch (e) {}
          },
          false
        );
      });
    }
    var cur = "";
    try {
      cur = window.location.hash || "";
    } catch (e) {}
    secs().forEach(function (s) {
      var hay = s.ch + " " + s.chTitle + " " + s.id + " " + s.title;
      if (q && hay.toLowerCase().indexOf(q) < 0) return;
      addRow(
        "§" + s.id + " " + s.title,
        "Ch " + s.ch + " · " + s.chTitle,
        (function (chN, secId) {
          return function () {
            goSection(chN, secId);
          };
        })(s.ch, s.id),
        cur === "#" + s.id
      );
    });
    var first = palList.querySelector(".pal-row");
    if (first) first.tabIndex = 0;
  }

  function open() {
    build();
    if (!pal) return;
    lastFocus = null;
    try {
      lastFocus = document.activeElement;
    } catch (e) {}
    pal.hidden = false;
    render("");
    palInput.value = "";
    try {
      palInput.focus();
    } catch (e) {}
  }

  function close() {
    if (!pal || pal.hidden) return;
    pal.hidden = true;
    try {
      if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
    } catch (e) {}
  }

  function build() {
    if (built) return;
    built = true;
    pal = document.createElement("div");
    pal.id = "jump-pal";
    pal.hidden = true;
    pal.setAttribute("role", "dialog");
    pal.setAttribute("aria-modal", "false");
    pal.setAttribute("aria-label", "Jump to chapter or section");
    var box = document.createElement("div");
    box.className = "pal-box";
    palInput = document.createElement("input");
    palInput.id = "jump-q";
    palInput.type = "search";
    palInput.setAttribute("placeholder", "Type chapter or section…  (14 chapters · 78 sections)");
    palInput.setAttribute("aria-label", "Search chapters and sections");
    palInput.setAttribute("autocomplete", "off");
    palList = document.createElement("div");
    palList.id = "jump-list";
    palList.setAttribute("role", "listbox");
    palList.setAttribute("aria-label", "Chapters and sections");
    var foot = document.createElement("p");
    foot.className = "pal-foot";
    foot.textContent = "↑↓ to move · Enter to go · Esc to close";
    box.appendChild(palInput);
    box.appendChild(palList);
    box.appendChild(foot);
    pal.appendChild(box);
    var scrim = document.createElement("div");
    scrim.className = "pal-scrim";
    scrim.setAttribute("aria-hidden", "true");
    pal.appendChild(scrim);
    document.body.appendChild(pal);
    palInput.addEventListener("input", function () {
      render(palInput.value);
    });
    palInput.addEventListener("keydown", function (e) {
      var rows = palList.querySelectorAll(".pal-row");
      if (!rows.length) return;
      var idx = -1;
      for (var i = 0; i < rows.length; i++) {
        if (rows[i] === document.activeElement) {
          idx = i;
          break;
        }
      }
      if (e.key === "ArrowDown") {
        (rows[idx + 1] || rows[0]).focus();
        e.preventDefault();
      } else if (e.key === "ArrowUp") {
        if (idx <= 0) palInput.focus();
        else rows[idx - 1].focus();
        e.preventDefault();
      } else if (e.key === "Enter") {
        if (idx >= 0) rows[idx].click();
        else {
          var f = palList.querySelector(".pal-row");
          if (f) f.click();
        }
        e.preventDefault();
      } else if (e.key === "Escape") {
        close();
        e.preventDefault();
      }
    });
    palList.addEventListener("keydown", function (e) {
      var rows = palList.querySelectorAll(".pal-row");
      var idx = -1;
      for (var i = 0; i < rows.length; i++) {
        if (rows[i] === document.activeElement) {
          idx = i;
          break;
        }
      }
      if (e.key === "ArrowDown") {
        (rows[idx + 1] || rows[0]).focus();
        e.preventDefault();
      } else if (e.key === "ArrowUp") {
        if (idx <= 0) palInput.focus();
        else rows[idx - 1].focus();
        e.preventDefault();
      } else if (e.key === "Escape") {
        close();
        e.preventDefault();
      }
    });
    scrim.addEventListener("click", close);
  }

  window.__openPalette = open;
  window.__closePalette = close;

  document.addEventListener("keydown", function (e) {
    try {
      var t = e.target;
      var typing =
        t &&
        (t.tagName === "INPUT" ||
          t.tagName === "TEXTAREA" ||
          t.tagName === "SELECT" ||
          t.isContentEditable);
      if (typing) return;
      if ((e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey) || ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K"))) {
        e.preventDefault();
        if (pal && !pal.hidden) close();
        else open();
      } else if (e.key === "Escape" && pal && !pal.hidden) {
        close();
      }
    } catch (err) {
      /* ignore */
    }
  });
})();
