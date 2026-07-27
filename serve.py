#!/usr/bin/env python3
"""Servidor de desarrollo.

Igual que `python3 -m http.server`, pero añadiendo cabeceras anti-caché.
Sin ellas el navegador se queda con el CSS/JS antiguo tras cada cambio y
hay que ir cambiando de puerto para forzar la recarga.

Uso: python3 serve.py [puerto] [directorio]
"""
import http.server
import socketserver
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
DIRECTORIO = sys.argv[2] if len(sys.argv) > 2 else "."


class SinCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    handler = lambda *args: SinCache(*args, directory=DIRECTORIO)
    with socketserver.TCPServer(("", PUERTO), handler) as httpd:
        print(f"Sirviendo '{DIRECTORIO}' en http://localhost:{PUERTO} (sin caché)")
        httpd.serve_forever()
