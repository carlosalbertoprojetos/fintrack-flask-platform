"""Funcoes utilitarias compartilhadas pela aplicacao."""

from __future__ import annotations

from typing import Optional


def parse_decimal_input(value) -> Optional[float]:
    """Converte uma entrada monetaria em ponto flutuante.

    Aceita os formatos brasileiros e internacionais mais comuns, mantendo
    compatibilidade com valores que utilizam ponto como separador decimal:

    - "1000,50"      -> 1000.5
    - "1.000,50"     -> 1000.5
    - "10,00"        -> 10.0
    - "150.75"       -> 150.75
    - "1.000.000,00" -> 1000000.0
    - 1234.5 (float) -> 1234.5

    Retorna ``None`` quando o valor estiver vazio. Lanca ``ValueError`` quando
    a entrada nao puder ser convertida em numero.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if text == "":
        return None

    # Remove simbolos de moeda e espacos.
    text = text.replace("R$", "").replace(" ", "").strip()
    if text == "":
        return None

    has_comma = "," in text
    has_dot = "." in text

    if has_comma and has_dot:
        # Formato brasileiro: ponto como separador de milhar e virgula decimal.
        text = text.replace(".", "").replace(",", ".")
    elif has_comma:
        # Apenas virgula: tratamos como separador decimal.
        text = text.replace(",", ".")
    # Apenas ponto (ou nenhum separador): mantem como esta (ponto = decimal).

    return float(text)
