---
name: SFP - Sistema de Finanças Pessoais
description: Interface local para organizar e acompanhar finanças pessoais.
colors:
  primary: "#02568c"
  primary-hover: "#1a4a7a"
  primary-soft: "rgba(2, 86, 140, 0.16)"
  primary-soft-subtle: "rgba(2, 86, 140, 0.08)"
  neutral-bg: "#f5f5f9"
  neutral-surface: "#ffffff"
  neutral-text: "#566a7f"
  neutral-text-strong: "#2b354f"
  neutral-muted: "#6c757d"
  neutral-border: "#d9dee3"
  dark-bg: "#232333"
  dark-surface: "#2b2c40"
  dark-surface-raised: "#34354a"
  dark-text: "#c3c4dd"
  dark-text-strong: "#e7e7f0"
  dark-muted: "#a9acca"
  dark-border: "#44455e"
  dark-primary: "#0a6ebd"
  dark-accent: "#6cb2ea"
  success: "#71dd37"
  info: "#03c3ec"
  warning: "#ffab00"
  danger: "#ff3e1d"
  success-text: "#287a13"
  info-text: "#087990"
  warning-text: "#8a5b00"
  danger-text: "#b02a37"
  dark-success-text: "#9be27a"
  dark-info-text: "#6ddcf1"
  dark-warning-text: "#ffd166"
  dark-danger-text: "#ff8f82"
typography:
  body:
    fontFamily: 'Public Sans, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.53
  title:
    fontFamily: 'Public Sans, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "1.25rem"
    fontWeight: 600
rounded:
  sm: "0.25rem"
  md: "0.375rem"
  lg: "0.5rem"
  xl: "0.75rem"
  pill: "50rem"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
  button-primary-hover:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
  card:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.neutral-text}"
    rounded: "{rounded.md}"
    padding: "1.5rem"
  input:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.neutral-text}"
    rounded: "{rounded.md}"
---

# Design System: SFP - Sistema de Finanças Pessoais

## Overview

**Creative North Star: "Painel financeiro claro e funcional"**

O sistema visual organiza tarefas financeiras frequentes em uma interface direta, familiar e utilitária. Superfícies neutras e cartões mantêm números, filtros e tabelas fáceis de localizar; o azul financeiro profundo destaca ações e estados ativos sem competir com os dados.

O tema claro é a base visual original. O tema escuro reaproveita a mesma organização e hierarquia com superfícies azuladas, texto claro e acento mais luminoso. A escolha salva no navegador tem precedência; na ausência dela, a interface acompanha a preferência do sistema. O tema inicial é aplicado antes da pintura da página e as cores mudam em 180 ms; com movimento reduzido, a transição cai para 80 ms. A tipografia é sem serifa, de sistema, e os componentes seguem padrões familiares de formulários, navegação e botões.

**Key Characteristics:**
- Azul concentrado em ações, links, ícones e seleção.
- Conteúdo operacional organizado em cartões e tabelas.
- Sombras leves e superfícies tonais para separar áreas.
- Temas claro e escuro com estrutura compartilhada.
- Feedback em português com estado semântico, botão de fechamento e pausa do desaparecimento enquanto o aviso recebe foco ou ponteiro.

## Colors

A paleta usa azul financeiro profundo sobre neutros frios no tema claro, com pares de superfície e texto próprios para o tema escuro; verde, ciano, âmbar e vermelho marcam estados.

### Primary
- **Azul financeiro profundo** (`{colors.primary}`): botões principais, links, ícones e itens selecionados no tema claro.
- **Azul de interação** (`{colors.primary-hover}`): hover e estados interativos do acento no tema claro.
- **Azul de ação noturno** (`{colors.dark-primary}`): botões principais no tema escuro.
- **Azul claro de leitura noturna** (`{colors.dark-accent}`): links e ícones no tema escuro.

### Neutral
- **Fundo névoa** (`{colors.neutral-bg}`) e **branco de superfície** (`{colors.neutral-surface}`): fundo de página e cartões no tema claro.
- **Texto ardósia** (`{colors.neutral-text}`), **texto forte** (`{colors.neutral-text-strong}`) e **texto auxiliar** (`{colors.neutral-muted}`): texto geral, ênfase e informação secundária.
- Os textos semânticos (`{colors.success-text}`, `{colors.info-text}`, `{colors.warning-text}` e `{colors.danger-text}`) são usados sobre superfícies claras; suas variantes noturnas (`{colors.dark-success-text}`, `{colors.dark-info-text}`, `{colors.dark-warning-text}` e `{colors.dark-danger-text}` preservam contraste no tema escuro.
- **Borda névoa** (`{colors.neutral-border}`): divisores e contornos discretos.
- **Fundo meia-noite** (`{colors.dark-bg}`), **superfície noite** (`{colors.dark-surface}`) e **superfície elevada noite** (`{colors.dark-surface-raised}`): página e camadas no tema escuro.
- **Texto lavanda frio** (`{colors.dark-text}`), **texto claro forte** (`{colors.dark-text-strong}`), **texto auxiliar noturno** (`{colors.dark-muted}`) e **borda noite** (`{colors.dark-border}`): conteúdo e separação no tema escuro.

### Named Rules
**The Financial Accent Rule.** Preserve o azul como sinal de ação e seleção; use as cores de estado para significados de sucesso, informação, alerta e erro.

## Typography

**Display Font:** Sem família distinta; usa a mesma pilha sem serifa do corpo
**Body Font:** Public Sans (com fallbacks de sistema)

**Character:** Sem serifa, familiar e compacta, adequada à leitura frequente de valores, tabelas e formulários. O projeto também pode usar os fallbacks locais quando Public Sans não estiver disponível.

### Hierarchy
- **Title** (600, 1.25rem): marca e títulos de componentes destacados.
- **Body** (400, 0.9375rem, line-height 1.53): texto geral da aplicação.
- **Labels and data**: seguem a tipografia de corpo e as variações de escala fornecidas pelos componentes Bootstrap e pelas telas.

### Named Rules
**The Familiar Sans Rule.** Mantenha a família sem serifa e os fallbacks de sistema; não introduza uma família decorativa como voz paralela.

## Layout

A aplicação usa uma navegação lateral fixa de 260px em telas largas, que pode recolher para 80px. A barra superior ocupa 4.375rem; o conteúdo preenche o espaço restante com cartões, tabelas e grupos de formulários. O container usa gutters de 1.5rem em telas largas, 1rem em telas menores e 0.75rem no container em telas até 767.98px. Em larguras abaixo de 1200px, a navegação lateral sai da tela e abre sobre uma camada de fundo; o conteúdo passa a ocupar toda a largura. Em telas pequenas, cartões e navegação por abas permitem rolagem horizontal quando necessário. O viewport não restringe o zoom do navegador.

## Elevation & Depth

A profundidade combina superfícies em tons diferentes, bordas leves e sombras difusas. Cartões recebem elevação baixa, enquanto menus suspensos e dropdowns usam uma sombra mais evidente para indicar sobreposição. O tema escuro preserva essa hierarquia com sombras mais escuras.

### Shadow Vocabulary
- **Cartão** (`0 0 0.875rem 0 rgba(33, 37, 41, 0.05)`): separa painéis brancos do fundo claro.
- **Dropdown** (`0 0.25rem 1rem rgba(161, 172, 184, 0.45)`): destaca menus sobre o conteúdo.
- **Sutil** (`0 0.0625rem 0.125rem rgba(161, 172, 184, 0.075)`): elevação mínima para superfícies pequenas.

### Named Rules
**The Subtle Layers Rule.** Use sombras para separar superfícies e sobreposições; preserve os níveis mais fortes para menus e controles que flutuam.

## Shapes

Controles e cartões usam cantos discretamente arredondados, principalmente 0.375rem; menus aninhados podem usar 0.5rem e links da navegação lateral usam formato de pílula. Bordas são finas e de baixo contraste. Não há uma linguagem de recortes ou formas decorativas recorrentes.

## Components

### Buttons
- **Shape:** cantos familiares de 0.375rem.
- **Primary:** fundo azul e texto branco; no hover, o fundo fica branco e o texto azul.
- **Hover / Focus:** transição curta; mantenha o foco visível e o contorno azul do formulário ao teclado.
- **Secondary:** use as variantes Bootstrap já presentes quando a ação não for a principal.
- **Theme toggle:** botão compartilhado com área mínima de 2.75rem, foco visível e nome acessível que comunica o modo ativo e o modo que será ativado.

### Cards / Containers
- **Corner Style:** cantos discretos (0.375rem, herdados do Bootstrap).
- **Background:** branco no tema claro; superfície escura no tema escuro.
- **Shadow Strategy:** elevação difusa baixa; consulte Elevation & Depth.
- **Border:** sem borda externa na maioria dos cartões; divisores aparecem em cabeçalhos e rodapés.
- **Internal Padding:** escala comum de 1rem a 1.5rem, com ajustes pontuais em cartões de dados densos.

### Inputs / Fields
- **Style:** superfície branca ou secundária no escuro, borda neutra e cantos de 0.375rem.
- **Focus:** borda azul e brilho sutil azul.
- **Error / Disabled:** use os estados semânticos já disponíveis do Bootstrap; preserve legibilidade nos dois temas.

### Navigation
- **Style:** navegação lateral fixa em desktop, recolhível e em gaveta em telas menores; links usam azul e fundo azul suave em hover e seleção.
- **Tabs:** abas têm fundo claro para seleção, indicador inferior azul e rolagem horizontal em telas estreitas.
- **Top bar:** superfície clara ou escura correspondente ao tema, com links e menus de conta.

### Tables and Financial Data
Tabelas mantêm os dados no primeiro plano, com cabeçalhos, linhas alternadas ou hover quando aplicável e cores de estado reservadas para significado financeiro. Em telas estreitas, priorize rolagem horizontal em vez de comprimir valores e rótulos até ficarem ilegíveis.

### Alerts and Feedback
Avisos usam os estados Bootstrap (`success`, `info`, `warning` e `danger`) com cores adaptadas ao tema. Mensagens dinâmicas são inseridas como texto, aceitam conteúdo longo com quebra de linha, usam rótulos em português e oferecem fechamento por botão. O auto-fechamento padrão é de oito segundos, limitado a dois minutos, e pausa durante foco ou passagem do ponteiro; uma duração zero mantém o aviso até o usuário dispensá-lo.

## Do's and Don'ts

### Do:
- **Do:** use o azul financeiro profundo para ações, links e seleção no tema claro.
- **Do:** mantenha contraste de texto e superfícies apropriado ao tema ativo.
- **Do:** use camadas sutis para separar cartões e sombras mais fortes para sobreposições.
- **Do:** preserve os padrões familiares do Bootstrap em formulários, botões e navegação.
- **Do:** comunique estados financeiros com texto semântico legível no tema ativo, sem depender apenas da cor.
- **Do:** preserve zoom, foco de teclado e preferência por movimento reduzido.

### Don't:
- **Don't:** introduza cores de marca adicionais sem uma função clara na interface.
- **Don't:** substitua os temas existentes por uma única paleta fixa.
- **Don't:** use sombras pesadas em todos os cartões ou aplique decoração que prejudique a leitura de números e tabelas.
- **Don't:** interpolar texto de mensagens em HTML; renderize conteúdo dinâmico como texto.
