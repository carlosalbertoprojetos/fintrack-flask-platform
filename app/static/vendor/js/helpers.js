"use strict";

/* ---------------------------------------------------------------------
   Gerenciamento de tema (claro/escuro)
   - Persistencia em localStorage("theme")
   - Valores: "theme-default" (claro) | "theme-dark" (escuro)
   - Dispara o evento global "themechange" sempre que o tema muda.
   --------------------------------------------------------------------- */

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

// Tema atual: salvo pelo usuario ou preferencia do sistema.
function getThemeFromLocalStorage() {
  if (typeof window === "undefined") return "theme-default";
  var stored = localStorage.getItem("theme");
  if (stored === "theme-dark" || stored === "theme-default") {
    return stored;
  }
  return getSystemTheme();
}

function applyThemeToDocument(theme) {
  if (typeof document === "undefined") return;
  var root = document.documentElement;
  root.setAttribute("data-theme", theme);
  root.classList.toggle("dark-style", theme === "theme-dark");
  root.classList.toggle("light-style", theme !== "theme-dark");
}

// Define o tema (persistindo) e notifica a aplicacao.
function setTheme(theme, persist) {
  if (typeof window === "undefined") return;
  if (persist !== false) {
    localStorage.setItem("theme", theme);
  }
  applyThemeToDocument(theme);
  try {
    window.dispatchEvent(
      new CustomEvent("themechange", { detail: { theme: theme } })
    );
  } catch (e) {
    /* CustomEvent indisponivel: ignora */
  }
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
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", function (event) {
        if (!localStorage.getItem("theme")) {
          setTheme(event.matches ? "theme-dark" : "theme-default", false);
        }
      });
  } catch (e) {
    /* navegadores antigos: ignora */
  }
}

if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initTheme);
}
