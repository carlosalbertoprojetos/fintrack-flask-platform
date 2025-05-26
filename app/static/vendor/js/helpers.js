"use strict";

// Função para obter o tema atual
function getThemeFromLocalStorage() {
  if (typeof window !== "undefined") {
    if (localStorage.getItem("theme")) {
      return localStorage.getItem("theme");
    }
    return "theme-default";
  }
  return "theme-default";
}

// Função para definir o tema
function setTheme(theme) {
  if (typeof window !== "undefined") {
    localStorage.setItem("theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
  }
}

// Função para alternar o tema
function toggleTheme() {
  const currentTheme = getThemeFromLocalStorage();
  const newTheme = currentTheme === "theme-default" ? "theme-dark" : "theme-default";
  setTheme(newTheme);
}

// Função para inicializar o tema
function initTheme() {
  const theme = getThemeFromLocalStorage();
  setTheme(theme);
}

// Inicializar o tema quando o documento estiver pronto
if (typeof document !== "undefined") {
  document.addEventListener("DOMContentLoaded", initTheme);
} 