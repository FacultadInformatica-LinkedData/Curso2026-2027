"""Normalización de texto y nombres legibles de calles y distritos de Madrid."""

import re
import unicodedata

# Códigos de distrito del Callejero (bm:districtCode).
DISTRICTS = {
    1: "Centro", 2: "Arganzuela", 3: "Retiro", 4: "Salamanca", 5: "Chamartín", 6: "Tetuán",
    7: "Chamberí", 8: "Fuencarral-El Pardo", 9: "Moncloa-Aravaca", 10: "Latina",
    11: "Carabanchel", 12: "Usera", 13: "Puente de Vallecas", 14: "Moratalaz",
    15: "Ciudad Lineal", 16: "Hortaleza", 17: "Villaverde", 18: "Villa de Vallecas",
    19: "Vicálvaro", 20: "San Blas-Canillejas", 21: "Barajas",
}

_SMALL_WORDS = {"de", "del", "la", "las", "los", "el", "y", "e", "a", "en"}
_ROMAN = re.compile(r"(?=[mdclxvi]{2,}$)m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})")


def fold(text: str) -> str:
    """Mayúsculas sin tildes (conservando la Ñ), como los nombres del Callejero."""
    text = text.upper().replace("Ñ", "\0")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.replace("\0", "Ñ")).strip()


def pretty(name: str) -> str:
    """'ALFONSO XIII' -> 'Alfonso XIII', 'PASEO DE LA CASTELLANA' -> 'Paseo de la Castellana'."""
    words = []
    for i, word in enumerate(name.lower().split()):
        if _ROMAN.fullmatch(word):
            words.append(word.upper())
        elif i and word in _SMALL_WORDS:
            words.append(word)
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def district_names(codes: str | None) -> str:
    """'7,6' (GROUP_CONCAT de bm:districtCode) -> 'Tetuán, Chamberí'."""
    numbers = sorted(int(code) for code in (codes or "").split(",") if code.strip().isdigit())
    return ", ".join(DISTRICTS.get(n, f"Distrito {n}") for n in numbers)
