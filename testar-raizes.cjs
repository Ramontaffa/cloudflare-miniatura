// Teste local e isolado da inicialização do app Express do Raízes.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');

const raiz = process.env.RAIZES_BACKEND || path.resolve(__dirname, '..', '..', 'WEB', 'Raizes-PE', 'backend');
const modulos = path.join(raiz, 'node_modules');
const loader = path.join(modulos, 'tsx', 'dist', 'cjs', 'index.cjs');
const id = new Date().toISOString().replace(/[:.]/g, '-') + '-' + crypto.randomBytes(3).toString('hex');
const logs = path.join(__dirname, 'logs', 'raizes-openapi', id);
const temporario = fs.mkdtempSync(path.join(os.tmpdir(), 'raizes-falha-'));
fs.mkdirSync(logs, { recursive: true });
const origem = path.join(raiz, 'src');
const spec = path.join(raiz, 'openapi.yaml');
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
function copiarDiretorio(origem, destino) {
  fs.mkdirSync(destino, { recursive: true });
  for (const entrada of fs.readdirSync(origem, { withFileTypes: true })) {
    const de = path.join(origem, entrada.name), para = path.join(destino, entrada.name);
    if (entrada.isDirectory()) copiarDiretorio(de, para);
    else if (entrada.isFile()) fs.copyFileSync(de, para);
  }
}

async function rodar(cenario) {
  const pasta = path.join(temporario, cenario);
  fs.mkdirSync(pasta, { recursive: true });
  copiarDiretorio(origem, path.join(pasta, 'src'));
  if (cenario === 'valido') fs.copyFileSync(spec, path.join(pasta, 'openapi.yaml'));
  if (cenario === 'yaml-invalido') fs.writeFileSync(path.join(pasta, 'openapi.yaml'), 'openapi: [\n');
  const worker = path.join(pasta, 'teste.cjs');
  fs.writeFileSync(worker, `const { app } = require('./src/app.ts');\nconst s = app.listen(0, '127.0.0.1', () => console.log('TEST_PORT=' + s.address().port));\n`);
  const ambiente = { ...process.env, NODE_PATH: modulos, NODE_ENV: 'test' };
  for (const nome of ['DATABASE_URL', 'DIRECT_URL', 'SESSION_SECRET', 'LOCAL_API_URL', 'API_URL', 'IA_RECOMENDACAO_URL']) delete ambiente[nome];
  const proc = spawn(process.execPath, ['-r', loader, worker], { cwd: pasta, env: ambiente, windowsHide: true });
  let stdout = '', stderr = '', codigo = null, sinal = null, porta = null, resposta = null, timeout = false;
  proc.stdout.on('data', d => { stdout += d; });
  proc.stderr.on('data', d => { stderr += d; });
  const encerramento = new Promise(resolve => proc.on('close', (code, signal) => { codigo = code; sinal = signal; resolve(); }));
  const limite = Date.now() + 60000;
  while (Date.now() < limite && codigo === null && sinal === null) {
    const match = stdout.match(/TEST_PORT=(\d+)/);
    if (match) { porta = Number(match[1]); break; }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  if (porta !== null) {
    try {
      const r = await fetch(`http://127.0.0.1:${porta}/api/saude`, { signal: AbortSignal.timeout(5000) });
      resposta = { status: r.status, corpo: await r.text() };
    } catch (e) { resposta = { erro: String(e) }; }
    proc.kill();
  } else if (codigo === null && sinal === null) {
    timeout = true;
    proc.kill();
  }
  await encerramento;
  fs.writeFileSync(path.join(logs, `${cenario}.stdout.log`), stdout);
  fs.writeFileSync(path.join(logs, `${cenario}.stderr.log`), stderr);
  const resultado = { cenario, porta_aberta: porta !== null, resposta_saude: resposta, codigo_saida: codigo,
    sinal_saida: sinal, timeout, observacao: porta !== null ? 'Processo encerrado pelo teste após a requisição.' : 'Processo terminou antes de abrir a porta ou expirou.' };
  fs.writeFileSync(path.join(logs, `${cenario}.json`), JSON.stringify(resultado, null, 2) + '\n');
  console.log(JSON.stringify(resultado));
}

(async () => {
  if (!fs.existsSync(loader) || !fs.existsSync(spec)) throw new Error('Backend, dependências ou OpenAPI não encontrados: ' + raiz);
  fs.writeFileSync(path.join(logs, 'metadados.json'), JSON.stringify({ data_utc: new Date().toISOString(),
    backend_local: raiz, node: process.version, teste: 'app Express copiado; porta efêmera; sem acesso intencional a banco',
    sha256_openapi: sha(spec), sha256_app: sha(path.join(origem, 'app.ts')),
    sha256_leitor: sha(path.join(origem, 'config', 'openapi.ts')) }, null, 2) + '\n');
  for (const cenario of ['valido', 'ausente', 'yaml-invalido']) await rodar(cenario);
  console.log('LOGS=' + logs);
  console.log('COPIA_TEMPORARIA=' + temporario);
})().catch(erro => { console.error(erro); process.exitCode = 1; });
