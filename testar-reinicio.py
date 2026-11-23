"""Verifica se a última configuração válida sobrevive ao reinício do consumidor."""
import datetime
import json
import os
import subprocess
import time
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent
identificador = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:8]
pasta = BASE / 'logs' / 'reinicio-mitigacao' / identificador
pasta.mkdir(parents=True)
projeto = 'cloudflare-reinicio-' + uuid.uuid4().hex[:10]
ambiente = os.environ.copy()
ambiente['MITIGACAO'] = '1'
eventos = []

def registrar(tipo, **dados):
    evento = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'tipo': tipo, **dados}
    eventos.append(evento)
    with (pasta / 'eventos.jsonl').open('a', encoding='utf-8') as arquivo:
        arquivo.write(json.dumps(evento, ensure_ascii=False) + '\n')
    print(json.dumps(evento, ensure_ascii=False), flush=True)

def compose(*args, exigir=True):
    comando = ['docker', 'compose', '-p', projeto, *args]
    resultado = subprocess.run(comando, cwd=BASE, env=ambiente, capture_output=True, text=True, encoding='utf-8', errors='replace')
    registrar('comando', argumentos=list(args), codigo=resultado.returncode,
              stdout=resultado.stdout, stderr=resultado.stderr)
    if exigir and resultado.returncode:
        raise RuntimeError('Falha em docker compose ' + ' '.join(args))
    return resultado

def chamada(metodo, url, etapa):
    codigo = ("import urllib.request,urllib.error; "
              f"r=urllib.request.Request({url!r},method={metodo!r}); "
              "\ntry:\n with urllib.request.urlopen(r,timeout=2) as x: print('STATUS='+str(x.status)); print('BODY='+x.read().decode())"
              "\nexcept urllib.error.HTTPError as e: print('STATUS='+str(e.code)); print('BODY='+e.read().decode())"
              "\nexcept (urllib.error.URLError,TimeoutError,OSError) as e: print('STATUS=0'); print('BODY='+str(e))")
    resultado = compose('exec', '-T', 'gerador', 'python', '-c', codigo)
    linha = next((x for x in resultado.stdout.splitlines() if x.startswith('STATUS=')), None)
    if not linha:
        raise RuntimeError('Resposta sem status HTTP')
    status = int(linha.partition('=')[2])
    registrar('requisicao', etapa=etapa, metodo=metodo, url=url, status=status, resposta=resultado.stdout)
    return status

def aguardar(etapa, esperado=None, tentativas=30):
    for tentativa in range(1, tentativas + 1):
        status = chamada('GET', 'http://consumidor:8000/', f'{etapa}-{tentativa}')
        if status == esperado or (esperado is None and status != 0):
            return status
        time.sleep(0.5)
    raise RuntimeError(f'{etapa}: status {esperado} não observado')

registrar('hipotese', texto='A mitigação manterá o atendimento disponível após reiniciar o consumidor com a configuração inválida ainda publicada.',
          criterio='Após reinício, observar HTTP 200; uma resposta 503 contradiz a hipótese.')
try:
    compose('up', '-d', 'gerador', 'consumidor')
    aguardar('configuracao-valida', 200)
    if chamada('POST', 'http://localhost:8001/invalida', 'publicar-invalida') != 200:
        raise RuntimeError('Falha ao publicar configuração inválida')
    aguardar('invalida-antes-do-reinicio', 200)
    compose('restart', 'consumidor')
    apos_reinicio = aguardar('invalida-apos-reinicio')
    if chamada('POST', 'http://localhost:8001/valida', 'restaurar-valida') != 200:
        raise RuntimeError('Falha ao restaurar configuração válida')
    aguardar('apos-restauracao', 200)
    if apos_reinicio == 503:
        registrar('conclusao', resultado='hipotese_contradita', explicacao='O código mantém a última versão válida apenas na memória do processo, que é reiniciada.')
    elif apos_reinicio == 200:
        registrar('conclusao', resultado='hipotese_compativel_com_a_observacao')
    else:
        registrar('conclusao', resultado='resposta_inesperada', status=apos_reinicio)
finally:
    resultado = subprocess.run(['docker', 'compose', '-p', projeto, 'logs', '--no-color'], cwd=BASE, env=ambiente, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (pasta / 'containers.log').write_text(resultado.stdout + resultado.stderr, encoding='utf-8')
    compose('down', exigir=False)
    print(f'Logs: {pasta}', flush=True)
