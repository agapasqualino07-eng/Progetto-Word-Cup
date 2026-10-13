"""Guardia anti-rete: qualunque connessione socket durante i test fallisce."""

import socket


def _blocked(*args, **kwargs):
    raise RuntimeError("Chiamata di rete vietata nei test")


socket.socket.connect = _blocked
socket.create_connection = _blocked
