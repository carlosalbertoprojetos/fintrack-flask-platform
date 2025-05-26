"use strict";

// Função para inicializar o tema
document.addEventListener("DOMContentLoaded", function () {
  // Inicializar o tema
  initTheme();

  // Inicializar o menu
  initMenu();

  // Inicializar o sistema
  initSystem();
});

// Função para inicializar o menu
function initMenu() {
  const menuToggle = document.querySelector(".layout-menu-toggle");
  const layoutWrapper = document.querySelector(".layout-wrapper");

  if (menuToggle && layoutWrapper) {
    menuToggle.addEventListener("click", function () {
      layoutWrapper.classList.toggle("layout-menu-collapsed");
    });
  }
}

// Função para inicializar o sistema
function initSystem() {
  // Adicionar evento de clique para o botão de desligar
  const shutdownButton = document.querySelector('[onclick="shutdownSystem()"]');
  if (shutdownButton) {
    shutdownButton.addEventListener("click", function (e) {
      e.preventDefault();
      if (confirm("Tem certeza que deseja desligar o sistema?")) {
        // Aqui você pode adicionar a lógica para desligar o sistema
        window.location.href = "/shutdown";
      }
    });
  }
}

// Função para mostrar/esconder o menu em dispositivos móveis
function toggleMenu() {
  const layoutMenu = document.querySelector(".layout-menu");
  const layoutOverlay = document.querySelector(".layout-overlay");

  if (layoutMenu && layoutOverlay) {
    layoutMenu.classList.toggle("layout-menu-expanded");
    layoutOverlay.classList.toggle("layout-menu-expanded");
  }
}

// Função para fechar o menu em dispositivos móveis
function closeMenu() {
  const layoutMenu = document.querySelector(".layout-menu");
  const layoutOverlay = document.querySelector(".layout-overlay");

  if (layoutMenu && layoutOverlay) {
    layoutMenu.classList.remove("layout-menu-expanded");
    layoutOverlay.classList.remove("layout-menu-expanded");
  }
}

// Função para mostrar/esconder o dropdown do usuário
function toggleUserDropdown() {
  const dropdownMenu = document.querySelector(".dropdown-menu");
  if (dropdownMenu) {
    dropdownMenu.classList.toggle("show");
  }
}

// Função para fechar o dropdown do usuário quando clicar fora
document.addEventListener("click", function (e) {
  const dropdownMenu = document.querySelector(".dropdown-menu");
  const dropdownToggle = document.querySelector(".dropdown-toggle");

  if (dropdownMenu && dropdownToggle) {
    if (!dropdownToggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
      dropdownMenu.classList.remove("show");
    }
  }
});
