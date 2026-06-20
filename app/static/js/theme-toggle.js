"use strict";

/* ---------------------------------------------------------------------
   Liga o botao de alternancia de tema e mantem os graficos legiveis.
   Depende de helpers.js (getThemeFromLocalStorage / toggleTheme) e do
   evento "themechange".
   --------------------------------------------------------------------- */
(function () {
  function currentTheme() {
    if (typeof getThemeFromLocalStorage === "function") {
      return getThemeFromLocalStorage();
    }
    return document.documentElement.getAttribute("data-theme") || "theme-default";
  }

  function token(name, fallback) {
    try {
      var value = getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();
      return value || fallback;
    } catch (e) {
      return fallback;
    }
  }

  /* Atualiza o icone/titulo do botao conforme o tema. */
  function updateToggleUI(theme) {
    var isDark = theme === "theme-dark";
    var icons = document.querySelectorAll("[data-theme-toggle-icon]");
    icons.forEach(function (icon) {
      icon.classList.remove("fa-moon", "fa-sun", "bx-moon", "bx-sun");
      icon.classList.add(isDark ? "fa-sun" : "fa-moon");
    });
    var buttons = document.querySelectorAll("[data-theme-toggle]");
    buttons.forEach(function (btn) {
      btn.setAttribute(
        "title",
        isDark ? "Mudar para tema claro" : "Mudar para tema escuro"
      );
      btn.setAttribute("aria-label", btn.getAttribute("title"));
      var label = btn.querySelector("[data-theme-toggle-label]");
      if (label) {
        label.textContent = isDark ? "Tema Claro" : "Tema Escuro";
      }
    });
  }

  /* Define os padroes do Chart.js a partir dos tokens (texto/grade). */
  function applyChartDefaults() {
    if (typeof window.Chart === "undefined" || !window.Chart.defaults) return;
    var textColor = token("--app-chart-text", "#697a8d");
    var gridColor = token("--app-chart-grid", "rgba(0,0,0,0.08)");
    window.Chart.defaults.color = textColor;
    if (window.Chart.defaults.borderColor !== undefined) {
      window.Chart.defaults.borderColor = gridColor;
    }
    var scale = window.Chart.defaults.scale || (window.Chart.defaults.scales || {});
    if (window.Chart.defaults.scale) {
      if (window.Chart.defaults.scale.grid)
        window.Chart.defaults.scale.grid.color = gridColor;
      if (window.Chart.defaults.scale.ticks)
        window.Chart.defaults.scale.ticks.color = textColor;
    }
    if (window.Chart.defaults.plugins && window.Chart.defaults.plugins.legend) {
      window.Chart.defaults.plugins.legend.labels =
        window.Chart.defaults.plugins.legend.labels || {};
      window.Chart.defaults.plugins.legend.labels.color = textColor;
    }
  }

  /* Re-renderiza os graficos da pagina (cada pagina registra sua funcao). */
  function rerenderCharts() {
    applyChartDefaults();
    if (typeof window.renderPageCharts === "function") {
      try {
        window.renderPageCharts();
      } catch (e) {
        /* ignora falha de re-render */
      }
    }
  }

  // Padroes de chart corretos ja na carga inicial (antes da pagina criar charts).
  applyChartDefaults();

  document.addEventListener("DOMContentLoaded", function () {
    updateToggleUI(currentTheme());

    document.querySelectorAll("[data-theme-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        if (typeof toggleTheme === "function") {
          toggleTheme();
        }
      });
    });
  });

  window.addEventListener("themechange", function (e) {
    var theme = (e.detail && e.detail.theme) || currentTheme();
    updateToggleUI(theme);
    rerenderCharts();
  });
})();
