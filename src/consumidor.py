import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LIMITE = 10
MITIGACAO = os.environ.get('MITIGACAO') == '1'
ultima_valida = None
ultima_rejeitada = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global ultima_valida, ultima_rejeitada
        try:
            with open('/config/features.json', encoding='utf-8') as arquivo:
                features = json.load(arquivo)['features']
            if len(features) > LIMITE:
                if not MITIGACAO or ultima_valida is None:
                    raise ValueError('configuracao acima do limite')
                if features != ultima_rejeitada:
                    print('Configuracao rejeitada; mantendo ultima versao valida', flush=True)
                    ultima_rejeitada = features
            else:
                ultima_valida = features
                ultima_rejeitada = None
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'servico disponivel')
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as erro:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(str(erro).encode())

ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
