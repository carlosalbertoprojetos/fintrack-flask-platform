"use strict";

/* ---------------------------------------------------------------------
   Gerenciamento de tema (claro/escuro)
   - Persistencia em localStorage("theme")
   - Valores: "theme-default" (claro) | "theme-dark" (escuro)
   - Dispara o evento global "themechange" sempre que o tema muda.
   --------------------------------------------------------------------- */

var sessionTheme = null;
var themeTransitionTimer = null;

function isValidTheme(theme) {
  return theme === "theme-dark" || theme === "theme-default";
}

function readStoredTheme() {
  if (typeof window === "undefined") return null;
  try {
    var stored = window.localStorage.getItem("theme");
    return isValidTheme(stored) ? stored : null;
  } catch (e) {
    return null;
  }
}

function getSystemTheme() {
  if (
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "theme-dark";
  }
  return "theme-default";
}

// Tema atual: escolha salva, escolha desta sessao ou preferencia do sistema.
function getThemeFromLocalStorage() {
  return readStoredTheme() || sessionTheme || getSystemTheme();
}

function dispatchThemeChange(theme) {
  try {
    window.dispatchEvent(
      new CustomEvent("themechange", { detail: { theme: theme } })
    );
  } catch (e) {
    /* CustomEvent indisponivel: a interface ainda recebe o novo atributo. */
  }
}

function applyThemeToDocument(theme) {
  if (typeof document === "undefined") return;
  var root = document.documentElement;
  if (!isValidTheme(theme)) theme = getSystemTheme();
  root.setAttribute("data-theme", theme);
  root.classList.toggle("dark-style", theme === "theme-dark");
  root.classList.toggle("light-style", theme !== "theme-dark");
}

// Define o tema, tenta persistir e notifica os componentes compartilhados.
function setTheme(theme, persist) {
  if (typeof window === "undefined") return;
  if (!isValidTheme(theme)) theme = getSystemTheme();

  if (persist !== false) {
    try {
      window.localStorage.setItem("theme", theme);
      sessionTheme = null;
    } catch (e) {
      // Mantem a escolha durante esta sessao se o navegador bloquear storage.
      sessionTheme = theme;
    }
  }

  var root = document.documentElement;
  var changed = root.getAttribute("data-theme") !== theme;
  if (changed) {
    root.classList.add("theme-transition");
    applyThemeToDocument(theme);
    window.clearTimeout(themeTransitionTimer);
    var reduceMotion =
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    themeTransitionTimer = window.setTimeout(function () {
      root.classList.remove("theme-transition");
      themeTransitionTimer = null;
    }, reduceMotion ? 100 : 220);
  }

  dispatchThemeChange(theme);
}

// Alterna entre claro e escuro.
function toggleTheme() {
  var current = getThemeFromLocalStorage();
  var next = current === "theme-dark" ? "theme-default" : "theme-dark";
  setTheme(next);
  return next;
}

// Reaplica o tema corrente (o atributo ja foi setado pelo script anti-FOUC).
function initTheme() {
  applyThemeToDocument(getThemeFromLocalStorage());
}

// Acompanhar mudanca de preferencia do SO quando o usuario nao escolheu manualmente.
if (typeof window !== "undefined" && window.matchMedia) {
  try {
    var systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    var handleSystemThemeChange = function (event) {
      if (!readStoredTheme() && !sessionTheme) {
        sessionTheme = null;
        setTheme(event.matches ? "theme-dark" : "theme-default", false);
      }
    };
    if (systemThemeQuery.addEventListener) {
      systemThemeQuery.addEventListener("change", handleSystemThemeChange);
    } else if (systemThemeQuery.addListener) {
      systemThemeQuery.addListener(handleSystemThemeChange);
    }
  } catch (e) {
    /* Preferencia do sistema indisponivel: mantem o tema ja aplicado. */
  }
}

// Mantem outras abas alinhadas com a escolha persistida.
if (typeof window !== "undefined") {
  window.addEventListener("storage", function (event) {
    if (event.key !== "theme" && event.key !== null) return;
    sessionTheme = null;
    var theme = isValidTheme(event.newValue) ? event.newValue : getSystemTheme();
    setTheme(theme, false);
  });
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initTheme);
}
