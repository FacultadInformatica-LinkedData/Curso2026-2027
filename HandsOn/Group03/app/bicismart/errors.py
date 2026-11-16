"""Errores de una petición que la API responde con un código HTTP (manejadores en server.py).

Son excepciones propias para que un fallo de programación no llegue al usuario como «no existe»
o «no es válido»: un KeyError es un LookupError y daría un 404, y un ValueError inesperado,
un 400. Así, esos fallos dan un 500.
"""


class NotFound(LookupError):
    """Lo que se pide no existe (404): una estación, una calle o un lugar."""


class BadRequest(ValueError):
    """La petición no es válida (400): una referencia o un radio mal escritos."""
