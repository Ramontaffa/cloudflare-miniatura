import datetime
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

cenario = os.environ['CENARIO']
execucao = os.environ['EXECUCAO']
if not re.fullmatch(r'[a-zA-Z0-9_-]+', cenario) or not re.fullmatch(r'[a-zA-Z0-9_-]+', execucao):
    raise ValueError('CENARIO e EXECUCAO devem conter apenas letras, numeros, hifen ou sublinhado')
pasta = Path('/logs') / cenario / execucao
pasta.mkdir(parents=True, exist_ok=False)
inicio = time.monotonic()
eventos = []

def registrar(tipo, **dados):
    evento = {'tipo': tipo, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'segundos': round(time.monotonic() - inicio, 6), **dados}
    eventos.append(evento)
    with (pasta / 'eventos.jsonl').open('a', encoding='utf-8') as arquivo:
        arquivo.write(json.dumps(evento, ensure_ascii=False) + '\n')
    return evento

def requisicao(url, metodo='GET'):
    try:
        req = urllib.request.Request(url, method=metodo)
        with urllib.request.urlopen(req, timeout=2) as resposta:
            return resposta.status
    except urllib.error.HTTPError as erro:
        return erro.code
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0

def comando(acao):
    status = requisicao('http://gerador:8001/' + acao, 'POST')
    if status != 200:
        registrar('erro_comando', acao=acao, status=status)
        raise RuntimeError(f'Nao foi possivel executar {acao}: {status}')
    return registrar('configuracao_' + acao)

def amostrar(fase, quantidade):
    for _ in range(quantidade):
        status = requisicao('http://consumidor:8000/')
        registrar('requisicao', fase=fase, status=status, sucesso=200 <= status < 300)
        time.sleep(0.1)

for tentativa in range(60):
    if requisicao('http://consumidor:8000/') == 200:
        break
    time.sleep(0.5)
else:
    registrar('erro_inicializacao')
    raise RuntimeError('Consumidor nao ficou pronto em 30 segundos')
registrar('inicio_medicao')
amostrar('normal', 20)
injecao = comando('invalida')
amostrar('invalida', 80)
restauracao = comando('valida')
amostrar('recuperacao', 30)
requisicoes = [e for e in eventos if e['tipo'] == 'requisicao']
erros = [e for e in requisicoes if not e['sucesso']]
primeira_falha = next((e for e in erros if e['segundos'] >= injecao['segundos']), None)
apos = [e for e in requisicoes if e['fase'] == 'recuperacao']
recuperada = next((apos[i] for i in range(len(apos) - 2)
                   if all(e['sucesso'] for e in apos[i:i+3])), None)
resumo = {'cenario': cenario, 'execucao': execucao, 'total_requisicoes': len(requisicoes),
          'requisicoes_com_erro': len(erros), 'percentual_erros': round(100 * len(erros) / len(requisicoes), 2),
          'tempo_ate_falha_s': round(primeira_falha['segundos'] - injecao['segundos'], 6) if primeira_falha else None,
          'tempo_ate_recuperacao_s': round(recuperada['segundos'] - restauracao['segundos'], 6) if primeira_falha and recuperada else None,
          'recuperacao_confirmada': bool(recuperada) if primeira_falha else None,
          'criterio_recuperacao': 'primeira de tres requisicoes consecutivas bem-sucedidas apos restauracao'}
(pasta / 'resumo.json').write_text(json.dumps(resumo, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(resumo, indent=2, ensure_ascii=False), flush=True)
