/**
 * Sistema de Finanças Pessoais - Scripts Principais
 * Versão Refatorada - ES6+ com Clean Code
 * 
 * Módulos:
 * - Menu e Dropdowns
 * - Sistema de Abas
 * - Sistema de Desligamento
 * - Alertas e Mensagens
 * - Utilitários
 */

"use strict";

// ============================================================================
// CONSTANTES E CONFIGURAÇÕES
// ============================================================================

const CONFIG = {
  TAB_CHANNEL_NAME: 'financas_pessoais_tabs',
  TAB_COUNT_KEY: 'financas_pessoais_tab_count',
  TAB_ID_KEY: 'current_tab_id',
  LAST_UPDATE_KEY: 'last_tab_update',
  SHUTDOWN_TIMEOUT: 15000,
  MENU_EXPAND_DELAY: 300,
  DROPDOWN_CHECK_DELAY: 100,
  ALERT_FADE_DURATION: 500,
};

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

const AppState = {
  initialized: false,
  tabChannel: null,
  currentTabId: null,
  domCache: new Map(),
  activeListeners: new Map(),
};

// ============================================================================
// UTILITÁRIOS
// ============================================================================

/**
 * Query selector seguro com cache
 */
function safeQuerySelector(selector, useCache = true) {
  if (useCache && AppState.domCache.has(selector)) {
    const cached = AppState.domCache.get(selector);
    if (document.contains(cached)) {
      return cached;
    }
    AppState.domCache.delete(selector);
  }
  
  const element = document.querySelector(selector);
  if (element && useCache) {
    AppState.domCache.set(selector, element);
  }
  return element;
}

/**
 * Query selector all com validação
 */
function safeQuerySelectorAll(selector) {
  try {
    return Array.from(document.querySelectorAll(selector));
  } catch (e) {
    console.warn(`Invalid selector: ${selector}`, e);
    return [];
  }
}

/**
 * Gera ID único para aba
 */
function generateTabId() {
  return `tab_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
}

/**
 * Debounce helper
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle helper
 */
function throttle(func, limit) {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Limpa cache DOM
 */
function clearDOMCache() {
  AppState.domCache.clear();
}

// ============================================================================
// SISTEMA DE ABAS
// ============================================================================

/**
 * Inicializa contador de abas com proteção contra race conditions
 */
function initTabCounter() {
  try {
    // Gerar ou recuperar ID da aba
    let tabId = sessionStorage.getItem(CONFIG.TAB_ID_KEY);
    if (!tabId) {
      tabId = generateTabId();
      sessionStorage.setItem(CONFIG.TAB_ID_KEY, tabId);
    }
    AppState.currentTabId = tabId;

    // Configurar BroadcastChannel
    const channel = new BroadcastChannel(CONFIG.TAB_CHANNEL_NAME);
    AppState.tabChannel = channel;
    window.financasTabChannel = channel;

    // Incrementar contador com timestamp para evitar race conditions
    const timestamp = Date.now();
    const currentCount = parseInt(
      localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '0'
    );
    const newCount = currentCount + 1;
    
    localStorage.setItem(CONFIG.TAB_COUNT_KEY, newCount.toString());
    localStorage.setItem(CONFIG.LAST_UPDATE_KEY, timestamp.toString());

    console.log(`Aba ${tabId} inicializada. Total de abas: ${newCount}`);

    // Listener para mensagens de outras abas
    channel.addEventListener('message', handleTabMessage);

    // Solicitar contagem atualizada
    channel.postMessage({ 
      type: 'request_tab_count', 
      tabId 
    });

    // Cleanup ao fechar aba
    const beforeUnloadHandler = () => {
      try {
        channel.postMessage({ 
          type: 'tab_closing', 
          tabId 
        });
      } catch (e) {
        console.warn('Erro ao notificar fechamento de aba:', e);
      }

      const count = parseInt(
        localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '0'
      );
      if (count > 0) {
        localStorage.setItem(
          CONFIG.TAB_COUNT_KEY, 
          (count - 1).toString()
        );
      }

      try {
        channel.close();
      } catch (e) {
        console.warn('Erro ao fechar BroadcastChannel:', e);
      }
    };

    window.addEventListener('beforeunload', beforeUnloadHandler);
    AppState.activeListeners.set('beforeunload', beforeUnloadHandler);

  } catch (error) {
    console.error('Erro na inicialização do contador de abas:', error);
    // Fallback: usar apenas localStorage
    const currentCount = parseInt(
      localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '0'
    );
    localStorage.setItem(
      CONFIG.TAB_COUNT_KEY, 
      (currentCount + 1).toString()
    );
    
    window.addEventListener('beforeunload', () => {
      const count = parseInt(
        localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '0'
      );
      if (count > 0) {
        localStorage.setItem(
          CONFIG.TAB_COUNT_KEY, 
          (count - 1).toString()
        );
      }
    });
  }
}

/**
 * Handler de mensagens do BroadcastChannel
 */
function handleTabMessage(event) {
  const { type, tabId: senderTabId, count } = event.data;

  switch (type) {
    case 'request_tab_count':
      if (AppState.tabChannel) {
        AppState.tabChannel.postMessage({
          type: 'tab_count_response',
          count: parseInt(
            localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '1'
          )
        });
      }
      break;

    case 'tab_count_response':
      if (count && count > 0) {
        localStorage.setItem(CONFIG.TAB_COUNT_KEY, count.toString());
        console.log(
          `Contador de abas atualizado via BroadcastChannel: ${count}`
        );
      }
      break;

    case 'tab_closing':
      if (senderTabId !== AppState.currentTabId) {
        const currentCount = parseInt(
          localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '1'
        );
        if (currentCount > 0) {
          localStorage.setItem(
            CONFIG.TAB_COUNT_KEY, 
            (currentCount - 1).toString()
          );
          console.log(
            `Aba ${senderTabId} fechada. Total restante: ${currentCount - 1}`
          );
        }
      }
      break;
  }
}

/**
 * Detecta número de abas abertas
 */
function detectBrowserTabCount() {
  return new Promise((resolve) => {
    try {
      if (!AppState.tabChannel) {
        const channel = new BroadcastChannel(CONFIG.TAB_CHANNEL_NAME);
        AppState.tabChannel = channel;
      }

      const tabId = sessionStorage.getItem(CONFIG.TAB_ID_KEY) || generateTabId();
      sessionStorage.setItem(CONFIG.TAB_ID_KEY, tabId);

      AppState.tabChannel.postMessage({ 
        type: 'request_tab_count', 
        tabId 
      });

      const timeout = setTimeout(() => {
        const storedCount = parseInt(
          localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '1'
        );
        resolve(storedCount);
      }, 100);

      const messageHandler = (event) => {
        if (event.data.type === 'tab_count_response') {
          clearTimeout(timeout);
          AppState.tabChannel.removeEventListener('message', messageHandler);
          resolve(event.data.count);
        }
      };

      AppState.tabChannel.addEventListener('message', messageHandler);

    } catch (error) {
      console.warn('Erro na detecção de abas:', error);
      const storedCount = parseInt(
        localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '1'
      );
      resolve(storedCount);
    }
  });
}

/**
 * Decrementa contador de abas
 */
function decrementTabCount() {
  const currentCount = parseInt(
    localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '1'
  );
  if (currentCount > 0) {
    localStorage.setItem(
      CONFIG.TAB_COUNT_KEY, 
      (currentCount - 1).toString()
    );
  }
}

/**
 * Limpa storage relacionado a abas
 */
function cleanupTabStorage() {
  localStorage.removeItem(CONFIG.TAB_COUNT_KEY);
  sessionStorage.removeItem(CONFIG.TAB_ID_KEY);
  localStorage.removeItem(CONFIG.LAST_UPDATE_KEY);
}

/**
 * Fecha aba ou navegador baseado no número de abas
 */
async function closeTabOrBrowser() {
  try {
    // Timeout para evitar espera infinita
    const closeTimeout = setTimeout(() => {
      console.warn('Timeout ao detectar abas, forçando fechamento');
      forceClose();
    }, 2000);

    let tabCount;
    try {
      tabCount = await detectBrowserTabCount();
      clearTimeout(closeTimeout);
    } catch (error) {
      console.warn('Erro ao detectar abas, usando fallback:', error);
      clearTimeout(closeTimeout);
      // Fallback: usar localStorage
      tabCount = parseInt(
        localStorage.getItem(CONFIG.TAB_COUNT_KEY) || '1'
      );
    }

    const shouldCloseBrowser = tabCount <= 1;

    if (shouldCloseBrowser) {
      cleanupTabStorage();
      updateShutdownStatus('Fechando navegador completo...');
    } else {
      decrementTabCount();
      updateShutdownStatus('Fechando apenas esta aba...');
      
      // Notificar outras abas
      if (AppState.tabChannel) {
        try {
          AppState.tabChannel.postMessage({
            type: 'tab_closing',
            tabId: AppState.currentTabId
          });
        } catch (e) {
          console.warn('Erro ao notificar fechamento:', e);
        }
      }
    }

    // Aguardar um pouco para atualizar UI
    await new Promise(resolve => setTimeout(resolve, 300));

    // Tentar fechar (não aguardar, executar e continuar)
    forceClose();
    
    // Não aguardar retorno, já que forceClose() tenta múltiplos métodos

  } catch (error) {
    console.error('Erro ao fechar aba/navegador:', error);
    forceClose();
  }
}

/**
 * Força fechamento do navegador/aba
 */
function forceClose() {
  updateShutdownStatus('Fechando navegador...');
  
  // Método 1: Tentar window.close() imediatamente
  try {
    window.close();
    // Se chegou aqui, window.close() não lançou exceção
    // Mas pode não ter funcionado devido a restrições do navegador
  } catch (e) {
    console.warn('window.close() lançou exceção:', e);
  }

  // Método 2: Aguardar um pouco e tentar novamente
  setTimeout(() => {
    try {
      window.close();
    } catch (e) {
      console.warn('Segunda tentativa window.close() falhou:', e);
    }
  }, 100);

  // Método 3: Redirecionar para about:blank (força fechamento em alguns casos)
  setTimeout(() => {
    try {
      window.location.replace('about:blank');
      // Tentar fechar após redirecionar
      setTimeout(() => {
        try {
          window.close();
        } catch (e) {
          console.warn('window.close() após about:blank falhou:', e);
        }
      }, 200);
    } catch (e) {
      console.warn('Redirecionamento para about:blank falhou:', e);
    }
  }, 300);

  // Método 4: Tentar via opener (se a janela foi aberta por outra)
  setTimeout(() => {
    try {
      if (window.opener && !window.opener.closed) {
        window.opener.close();
      }
    } catch (e) {
      console.warn('window.opener.close() falhou:', e);
    }
  }, 500);

  // Método 5: Último recurso - mostrar mensagem após 2 segundos
  setTimeout(() => {
    const statusDiv = document.getElementById('shutdown-status');
    if (statusDiv && !document.hidden) {
      // Se ainda está visível, significa que não fechou
      updateShutdownStatus('Não foi possível fechar automaticamente. Por favor, feche a janela manualmente.');
      // Tentar uma última vez após mostrar mensagem
      setTimeout(() => {
        try {
          window.close();
        } catch (e) {
          console.warn('Tentativa final de window.close() falhou:', e);
        }
      }, 1000);
    }
  }, 2000);
}

/**
 * Fecha navegador de forma inteligente (alias para compatibilidade)
 */
function closeBrowserIntelligently() {
  closeTabOrBrowser();
}

// ============================================================================
// SISTEMA DE MENU E DROPDOWNS
// ============================================================================

/**
 * Alterna estado do dropdown
 */
function toggleDropdown(toggleElement) {
  const menuItem = toggleElement.closest('.menu-item');
  if (!menuItem) return;

  const isOpen = menuItem.classList.contains('open');

  // Fechar outros dropdowns sem itens ativos
  safeQuerySelectorAll('.menu-item.open').forEach((item) => {
    if (item === menuItem) return;

    const submenu = item.querySelector('.menu-sub');
    if (submenu) {
      const activeSubItem = submenu.querySelector('.menu-item.active');
      if (!activeSubItem) {
        item.classList.remove('open');
      }
    } else {
      item.classList.remove('open');
    }
  });

  // Toggle do dropdown atual
  if (isOpen) {
    menuItem.classList.remove('open');
  } else {
    menuItem.classList.add('open');
  }
}

/**
 * Verifica e abre dropdowns com itens ativos
 */
function checkAndOpenActiveDropdowns() {
  safeQuerySelectorAll('.menu-item').forEach((menuItem) => {
    const submenu = menuItem.querySelector('.menu-sub');
    if (submenu) {
      const activeSubItem = submenu.querySelector('.menu-item.active');
      if (activeSubItem) {
        menuItem.classList.add('open');
      }
    }
  });
}

/**
 * Inicializa dropdowns do menu
 */
function initMenuDropdowns() {
  const menuToggles = safeQuerySelectorAll('.menu-toggle');
  
  menuToggles.forEach((toggle) => {
    const clickHandler = function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      const layoutWrapper = safeQuerySelector('.layout-wrapper');
      const isMenuCollapsed = layoutWrapper?.classList.contains(
        'layout-menu-collapsed'
      );

      if (isMenuCollapsed) {
        layoutWrapper.classList.remove('layout-menu-collapsed');
        setTimeout(() => {
          toggleDropdown(this);
        }, CONFIG.MENU_EXPAND_DELAY);
      } else {
        toggleDropdown(this);
      }
    };

    toggle.addEventListener('click', clickHandler);
    AppState.activeListeners.set(`dropdown-${toggle}`, clickHandler);
  });

  // Fechar dropdowns ao clicar fora
  const outsideClickHandler = (e) => {
    if (!e.target.closest('.menu-item')) {
      safeQuerySelectorAll('.menu-item.open').forEach((item) => {
        const submenu = item.querySelector('.menu-sub');
        if (submenu) {
          const activeSubItem = submenu.querySelector('.menu-item.active');
          if (!activeSubItem) {
            item.classList.remove('open');
          }
        } else {
          item.classList.remove('open');
        }
      });
    }
  };

  document.addEventListener('click', outsideClickHandler);
  AppState.activeListeners.set('outside-click', outsideClickHandler);

  // Verificar dropdowns ativos
  checkAndOpenActiveDropdowns();

  // Observer para mudanças no DOM (otimizado)
  const observer = new MutationObserver(
    debounce(() => {
      checkAndOpenActiveDropdowns();
    }, CONFIG.DROPDOWN_CHECK_DELAY)
  );

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  AppState.activeListeners.set('mutation-observer', observer);
}

/**
 * Inicializa menu principal
 */
function initMenu() {
  // Verificar se há elementos de menu na página
  const hasMenuElements = safeQuerySelector('.layout-menu') || 
                         safeQuerySelector('.layout-menu-toggle') ||
                         safeQuerySelector('.layout-wrapper');
  
  if (!hasMenuElements) {
    return; // Página não tem menu (ex: login)
  }

  const menuToggle = safeQuerySelector('.layout-menu-toggle.menu-link');
  const layoutWrapper = safeQuerySelector('.layout-wrapper');

  if (menuToggle && layoutWrapper) {
    const desktopToggleHandler = () => {
      layoutWrapper.classList.toggle('layout-menu-collapsed');
    };
    menuToggle.addEventListener('click', desktopToggleHandler);
    AppState.activeListeners.set('menu-toggle', desktopToggleHandler);
  }

  const mobileMenuToggle = safeQuerySelector(
    '.layout-menu-toggle.navbar-nav'
  );
  if (mobileMenuToggle) {
    const mobileToggleHandler = (e) => {
      e.preventDefault();
      toggleMenu();
    };
    mobileMenuToggle.addEventListener('click', mobileToggleHandler);
    AppState.activeListeners.set('mobile-menu-toggle', mobileToggleHandler);
  }

  const layoutOverlay = safeQuerySelector('.layout-overlay');
  if (layoutOverlay) {
    const overlayHandler = () => {
      closeMenu();
    };
    layoutOverlay.addEventListener('click', overlayHandler);
    AppState.activeListeners.set('overlay-click', overlayHandler);
  }

  // Inicializar dropdowns apenas se houver elementos de menu
  if (safeQuerySelectorAll('.menu-toggle').length > 0) {
    initMenuDropdowns();
  }
}

/**
 * Toggle menu mobile
 */
function toggleMenu() {
  const layoutMenu = safeQuerySelector('.layout-menu');
  const layoutOverlay = safeQuerySelector('.layout-overlay');
  
  if (layoutMenu && layoutOverlay) {
    layoutMenu.classList.toggle('layout-menu-expanded');
    layoutOverlay.classList.toggle('layout-menu-expanded');
  }
}

/**
 * Fecha menu mobile
 */
function closeMenu() {
  const layoutMenu = safeQuerySelector('.layout-menu');
  const layoutOverlay = safeQuerySelector('.layout-overlay');
  
  if (layoutMenu && layoutOverlay) {
    layoutMenu.classList.remove('layout-menu-expanded');
    layoutOverlay.classList.remove('layout-menu-expanded');
  }
}

/**
 * Toggle dropdown do usuário
 */
function toggleUserDropdown() {
  const dropdownMenu = safeQuerySelector('.dropdown-menu');
  if (dropdownMenu) {
    dropdownMenu.classList.toggle('show');
  }
}

// ============================================================================
// SISTEMA DE ALERTAS
// ============================================================================

/**
 * Descarta mensagem flash
 */
function dismissMessage(messageId) {
  const messageElement = document.getElementById(messageId);
  if (!messageElement) return;

  if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
    const bsAlert = new bootstrap.Alert(messageElement);
    bsAlert.close();
  } else {
    messageElement.style.transition = 'opacity 0.5s ease-out';
    messageElement.style.opacity = '0';
    setTimeout(() => {
      if (messageElement.parentNode) {
        messageElement.parentNode.removeChild(messageElement);
      }
    }, CONFIG.ALERT_FADE_DURATION);
  }
}

/**
 * Inicializa auto-dismiss de alertas
 */
function initAutoDismissAlerts() {
  const autoDismissAlerts = safeQuerySelectorAll('.auto-dismiss-alert');

  autoDismissAlerts.forEach((alert) => {
    const dismissTime = alert.getAttribute('data-auto-dismiss');
    if (!dismissTime) return;

    let dismissTimeout;

    const startDismissTimer = () => {
      dismissTimeout = setTimeout(() => {
        if (!alert || !alert.parentNode) return;

        if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
          const bsAlert = new bootstrap.Alert(alert);
          bsAlert.close();
        } else {
          alert.style.transition = 'opacity 0.5s ease-out';
          alert.style.opacity = '0';
          setTimeout(() => {
            if (alert.parentNode) {
              alert.parentNode.removeChild(alert);
            }
          }, CONFIG.ALERT_FADE_DURATION);
        }
      }, parseInt(dismissTime));
    };

    startDismissTimer();

    const mouseEnterHandler = () => {
      if (dismissTimeout) {
        clearTimeout(dismissTimeout);
      }
    };

    const mouseLeaveHandler = () => {
      startDismissTimer();
    };

    alert.addEventListener('mouseenter', mouseEnterHandler);
    alert.addEventListener('mouseleave', mouseLeaveHandler);

    AppState.activeListeners.set(`alert-${alert}`, {
      enter: mouseEnterHandler,
      leave: mouseLeaveHandler
    });
  });
}

// ============================================================================
// SISTEMA DE DESLIGAMENTO
// ============================================================================

/**
 * Cria UI de desligamento
 */
function createShutdownUI() {
  const shutdownMsg = document.createElement('div');
  shutdownMsg.innerHTML = `
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8); z-index: 9999; display: flex;
        align-items: center; justify-content: center;">
      <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
        <h4>Desligando o sistema...</h4>
        <p>Por favor, aguarde...</p>
        <div id="shutdown-status" style="margin-top: 15px; font-size: 14px; color: #02568c;">
          Iniciando processo de desligamento...
        </div>
        <div id="shutdown-timer" style="margin-top: 10px; font-size: 12px; color: #666;">
          Timeout: ${CONFIG.SHUTDOWN_TIMEOUT / 1000} segundos
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(shutdownMsg);
  return shutdownMsg;
}

/**
 * Atualiza status do shutdown
 */
function updateShutdownStatus(message, timeLeft = null) {
  const statusDiv = document.getElementById('shutdown-status');
  const timerDiv = document.getElementById('shutdown-timer');
  
  if (statusDiv) {
    statusDiv.textContent = message;
  }
  
  if (timerDiv && timeLeft !== null) {
    timerDiv.textContent = `Timeout: ${timeLeft} segundos`;
  }
}

/**
 * Sistema de desligamento
 */
async function shutdownSystem() {
  let globalTimeout;
  let timerInterval;
  
  try {
    // Criar UI primeiro
    createShutdownUI();
    updateShutdownStatus('Enviando comando de desligamento...');

    // Timeout global para forçar fechamento
    globalTimeout = setTimeout(() => {
      console.warn('Timeout global atingido - forçando fechamento');
      updateShutdownStatus('Timeout atingido. Forçando fechamento...');
      if (timerInterval) clearInterval(timerInterval);
      forceClose();
    }, CONFIG.SHUTDOWN_TIMEOUT);

    // Timer de contagem regressiva
    let timeLeft = CONFIG.SHUTDOWN_TIMEOUT / 1000;
    timerInterval = setInterval(() => {
      timeLeft--;
      updateShutdownStatus(null, timeLeft);
      if (timeLeft <= 0) {
        clearInterval(timerInterval);
      }
    }, 1000);

    // Fazer requisição de shutdown com timeout
    try {
      const fetchPromise = fetch('/shutdown', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout na requisição')), 5000)
      );

      const response = await Promise.race([fetchPromise, timeoutPromise]);

      if (response && response.ok) {
        updateShutdownStatus('Servidor respondendo... Encerrando aplicação...');
        
        // Aguardar processamento (reduzido para 2 segundos)
        await new Promise(resolve => setTimeout(resolve, 2000));
        updateShutdownStatus('Verificando número de abas...');

        // Fechar usando sistema inteligente com timeout
        try {
          await Promise.race([
            closeTabOrBrowser(),
            new Promise((_, reject) => 
              setTimeout(() => reject(new Error('Timeout ao fechar')), 3000)
            )
          ]);
        } catch (closeError) {
          console.warn('Erro ao fechar, usando método forçado:', closeError);
          updateShutdownStatus('Fechando navegador...');
          forceClose();
        }
        
        if (globalTimeout) clearTimeout(globalTimeout);
        if (timerInterval) clearInterval(timerInterval);
      } else {
        throw new Error('Resposta não OK do servidor');
      }
    } catch (error) {
      console.error('Erro na comunicação com servidor:', error);
      updateShutdownStatus('Erro na comunicação. Tentando fechar navegador...');
      
      await new Promise(resolve => setTimeout(resolve, 500));
      
      try {
        await Promise.race([
          closeTabOrBrowser(),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout')), 2000)
          )
        ]);
      } catch (closeError) {
        console.warn('Erro ao fechar, usando método forçado:', closeError);
        forceClose();
      }
      
      if (globalTimeout) clearTimeout(globalTimeout);
      if (timerInterval) clearInterval(timerInterval);
    }
  } catch (error) {
    console.error('Erro na função shutdownSystem:', error);
    updateShutdownStatus('Erro crítico. Tentando fechar...');
    if (globalTimeout) clearTimeout(globalTimeout);
    if (timerInterval) clearInterval(timerInterval);
    forceClose();
  }
}

/**
 * Confirma desligamento (chamada pelo modal)
 */
function confirmShutdown() {
  const modalElement = document.getElementById('shutdownModal');
  if (modalElement && typeof bootstrap !== 'undefined') {
    const modal = bootstrap.Modal.getInstance(modalElement);
    if (modal) {
      modal.hide();
    }
  }
  shutdownSystem();
}

// ============================================================================
// SISTEMA DE ABAS (NAV-TABS)
// ============================================================================

/**
 * Alterna entre abas de contas
 */
function switchTab(contaId, contaNome, tabType = 'conta') {
  requestAnimationFrame(() => {
    const tabSelector = tabType === 'reports' ? '#reportsTabs' : '#contaTabs';
    const tabPrefix = tabType === 'reports' ? 'reports-tab' : 'conta-tab';
    const tabItems = safeQuerySelectorAll(`${tabSelector} .nav-link`);
    const activeTab = document.getElementById(`${tabPrefix}-${contaId}`);

    // Animar saída da aba ativa
    tabItems.forEach((tab) => {
      if (tab.classList.contains('active')) {
        tab.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
      }
    });

    // Animar entrada da nova aba
    requestAnimationFrame(() => {
      if (activeTab) {
        activeTab.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        activeTab.classList.add('active');
        activeTab.setAttribute('aria-selected', 'true');
        activeTab.style.animation = 'tabActivate 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        setTimeout(() => {
          activeTab.style.animation = '';
        }, 400);
      }

      // Atualizar nome da conta
      const contaNameElement = document.getElementById('current-conta-name');
      if (contaNameElement) {
        contaNameElement.textContent = contaNome;
      }

      // Redirecionar
      if (tabType === 'reports') {
        const urlParams = new URLSearchParams(window.location.search);
        const reportType = urlParams.get('type') || 'monthly';
        const year = urlParams.get('year') || new Date().getFullYear();
        window.location.href = `/transactions/reports?conta_id=${contaId}&type=${reportType}&year=${year}`;
      } else {
        window.location.href = `/dashboard?conta_id=${contaId}`;
      }
    });
  });
}

/**
 * Alterna aba de relatórios (alias)
 */
function switchTabReports(contaId, contaNome) {
  switchTab(contaId, contaNome, 'reports');
}

/**
 * Inicializa sistema de abas Bootstrap
 */
function initTabs() {
  // Verificar se há tabs na página
  const hasTabs = safeQuerySelector('#contaTabs') || safeQuerySelector('#reportsTabs');
  if (!hasTabs) {
    return; // Página não tem tabs (ex: login)
  }

  // Dashboard tabs
  safeQuerySelectorAll('#contaTabs .nav-link').forEach((tab) => {
    const contaId = tab.getAttribute('data-conta-id');
    if (contaId) {
      tab.classList.add('has-content');
    }
  });

  // Reports tabs
  safeQuerySelectorAll('#reportsTabs .nav-link').forEach((tab) => {
    const contaId = tab.getAttribute('data-conta-id');
    if (contaId) {
      tab.classList.add('has-content');
    }
  });

  // Efeitos de hover otimizados
  const allNavLinks = safeQuerySelectorAll('.nav-link');
  allNavLinks.forEach((tab) => {
    tab.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

    const mouseEnterHandler = throttle(() => {
      if (!tab.classList.contains('active')) {
        tab.style.transform = 'translateY(-2px) translateZ(0)';
        tab.style.boxShadow = '0 4px 12px rgba(2, 86, 140, 0.15)';
      }
    }, 100);

    const mouseLeaveHandler = throttle(() => {
      if (!tab.classList.contains('active')) {
        tab.style.transform = 'translateY(0) translateZ(0)';
        tab.style.boxShadow = '';
      }
    }, 100);

    tab.addEventListener('mouseenter', mouseEnterHandler);
    tab.addEventListener('mouseleave', mouseLeaveHandler);

    tab.addEventListener('mousedown', () => {
      tab.style.transform = 'translateY(-1px) translateZ(0)';
    });

    tab.addEventListener('mouseup', () => {
      if (!tab.classList.contains('active')) {
        tab.style.transform = 'translateY(-2px) translateZ(0)';
      }
    });
  });
}

// ============================================================================
// INICIALIZAÇÃO PRINCIPAL
// ============================================================================

/**
 * Inicializa sistema principal
 */
function initSystem() {
  if (AppState.initialized) {
    console.warn('Sistema já inicializado');
    return;
  }

  initAutoDismissAlerts();
  initTabCounter();
  AppState.initialized = true;
}

/**
 * Inicialização quando DOM está pronto
 */
function initializeApp() {
  const initCallback = () => {
    // Sempre inicializar sistema básico (alertas, contador de abas)
    initSystem();
    
    // Inicializar menu apenas se os elementos existirem
    if (safeQuerySelector('.layout-menu') || safeQuerySelector('.layout-menu-toggle')) {
      initMenu();
    }
    
    // Inicializar tabs apenas se os elementos existirem
    if (safeQuerySelector('#contaTabs') || safeQuerySelector('#reportsTabs')) {
      initTabs();
    }
    
    // Inicializar relatórios se necessário
    handleReportsInit();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCallback);
  } else {
    initCallback();
  }
}

/**
 * Inicializa relatórios se necessário
 */
function handleReportsInit() {
  if (window.location.pathname.includes('/reports')) {
    if (typeof initReportsTabs === 'function') {
      initReportsTabs();
    } else {
      console.warn('Função initReportsTabs não encontrada');
    }
  }
}

// ============================================================================
// EXPOSIÇÃO GLOBAL
// ============================================================================

// Expor funções globalmente para compatibilidade
window.confirmShutdown = confirmShutdown;
window.shutdownSystem = shutdownSystem;
window.initSystem = initSystem;
window.initTabCounter = initTabCounter;
window.closeBrowserIntelligently = closeBrowserIntelligently;
window.toggleMenu = toggleMenu;
window.closeMenu = closeMenu;
window.toggleUserDropdown = toggleUserDropdown;
window.switchTab = switchTab;
window.switchTabReports = switchTabReports;
window.initTabs = initTabs;
window.dismissMessage = dismissMessage;

// ============================================================================
// INICIALIZAÇÃO AUTOMÁTICA
// ============================================================================

initializeApp();

