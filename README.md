# Miniatura do incidente da Cloudflare

Experimento didático sobre a distribuição de uma configuração que ultrapassa o limite do consumidor. O caso real está descrito no [relato oficial de 18/11/2025](https://blog.cloudflare.com/18-november-2025-outage/). A miniatura não representa a infraestrutura completa da Cloudflare.

## Componentes

- **gerador**: publica um arquivo válido com 5 entradas e, quando solicitado, um arquivo com 12 entradas, incluindo duplicatas.
- **consumidor**: responde a requisições usando esse arquivo; o limite escolhido para a miniatura é de 10 entradas. Sem mitigação, responde 503 quando o limite é excedido. Com mitigação, rejeita a configuração inválida e conserva a última válida em memória.
- **cliente**: envia requisições, solicita as mudanças e registra os resultados. Os três containers compartilham a rede `experimento`; gerador e consumidor compartilham o volume `configuracao`.

Esses valores são parâmetros da miniatura, não valores observados no sistema real. O consumidor simula erros HTTP, não o código interno ou todas as formas de impacto do proxy real.

## Requisitos e execução no Windows

Instale e inicie o Docker Desktop com containers Linux e o Docker Compose. Na primeira execução, pode ser necessário baixar a imagem `python:3.12-alpine`. Abra o PowerShell nesta pasta e execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\executar.ps1 -Cenario sem-mitigacao
powershell -ExecutionPolicy Bypass -File .\executar.ps1 -Cenario com-mitigacao
```

Cada execução recebe um identificador próprio e grava arquivos em `logs/<cenario>/<execucao>/`. O script usa o projeto Compose `cloudflare-miniatura` e remove os containers e a rede ao final, preservando o volume nomeado e os logs. O gerador sobrescreve a configuração válida no início de cada execução. Não execute dois testes simultaneamente com esse mesmo nome de projeto.

- `eventos.jsonl`: eventos e resultado individual de cada requisição. Status `0` indica erro de conexão ou timeout.
- `resumo.json`: contagens e métricas calculadas dos eventos.
- `containers.log`: saída dos três containers, incluindo publicação e rejeição da configuração.

Após o serviço ficar pronto, o cliente registra 20 requisições normais, solicita a configuração inválida e registra 80 requisições; depois solicita a restauração e registra mais 30. O intervalo entre requisições é de 0,1 segundo, além do tempo de cada chamada. As solicitações de prontidão não integram as métricas.

## Como ler as métricas

- O instante da mudança é registrado pelo cliente logo após receber a confirmação do gerador; não mede o tempo de propagação de uma rede real.
- Tempo até a falha: diferença entre esse instante e o registro da primeira requisição com erro. Tem resolução limitada pelo intervalo de amostragem e pelo tempo da requisição.
- Tempo até a recuperação: diferença entre a confirmação da restauração e a primeira de três respostas consecutivas bem-sucedidas depois dela. Quando não houve falha, o valor é `null` (não aplicável). Quando houve falha e não há confirmação, `null` indica que a recuperação não foi confirmada na janela; consulte `recuperacao_confirmada`.
- Percentual de erros: requisições com erro dividido pelo total das 130 requisições medidas, incluindo todas as fases. Uma resposta fora da faixa 2xx ou status `0` conta como erro.

Confira os dados em `eventos.jsonl` antes de usar os números no laudo. Repetições podem produzir resultados e tempos diferentes. Compare os cenários com os mesmos parâmetros e inclua o caminho exato dos arquivos citados.

## Limitações iniciais

1. Não há distribuição global ou múltiplos proxies; não se pode extrapolar alcance ou número de clientes afetados.
2. O gerador cria duplicatas diretamente, sem reproduzir as permissões e consultas ClickHouse do incidente; a origem real da duplicação é simplificada.
3. O consumidor retorna 503 de propósito; não reproduz o código do proxy, suas versões ou todos os efeitos sobre produtos dependentes.
4. A carga é sequencial e pequena, de modo que tempos e percentuais não representam os do incidente real.

## Teste adicional: reinício com configuração inválida

Com o Docker Desktop em execução e Python 3 instalado no computador, execute:

```powershell
python .\testar-reinicio.py
```

O teste usa um projeto Compose próprio, carrega uma configuração válida com a mitigação ativada, publica uma inválida, reinicia o consumidor e consulta o serviço antes e depois. Ele restaura a configuração válida e registra hipótese, comandos, respostas e logs em `logs/reinicio-mitigacao/<execucao>/`. O Compose remove os containers e a rede ao final; o volume nomeado específico do teste permanece. As respostas do teste de reinício não fazem parte das 130 requisições dos cenários principais.

## Teste isolado no Raízes PE

O script `testar-raizes.cjs` copia o código do backend para pastas temporárias, usa as dependências já instaladas da cópia local do Raízes e carrega o app Express com três versões da especificação: original, ausente e YAML sintaticamente inválido. O script inicia uma instância local em porta aleatória quando possível e consulta `/api/saude`. Não modifica o projeto original nem configura conexão de banco para o teste.

No Windows, com Node.js e as dependências do backend do Raízes já instaladas, execute na pasta desta miniatura:

```powershell
node .\testar-raizes.cjs
```

Por padrão o script procura `../../WEB/Raizes-PE/backend`. Para outra localização, defina `RAIZES_BACKEND` com o caminho do backend antes de executar. Cada execução cria uma pasta própria em `logs/raizes-openapi/` contendo os resultados, as saídas brutas e os hashes dos arquivos do projeto usado. As cópias temporárias não são removidas automaticamente; seu caminho é exibido ao final. O teste exercita a inicialização do app copiado, não o ambiente publicado, o processo completo de deploy nem os serviços externos.
