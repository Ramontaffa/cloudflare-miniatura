import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CAMINHO = '/config/features.json'

def publicar(quantidade):
    dados = {'features': [f'feature_{i % 5}' for i in range(quantidade)]}
    with open(CAMINHO + '.tmp', 'w', encoding='utf-8') as arquivo:
        json.dump(dados, arquivo)
    os.replace(CAMINHO + '.tmp', CAMINHO)
    print(f'Publicada configuracao com {quantidade} entradas', flush=True)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path not in ('/invalida', '/valida'):
            self.send_error(404)
            return
        publicar(12 if self.path == '/invalida' else 5)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

publicar(5)
ThreadingHTTPServer(('0.0.0.0', 8001), Handler).serve_forever()
