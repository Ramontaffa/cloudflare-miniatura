# Registro de uso de IA

## Como foi usada

A IA foi usada para ajudar a entender a tarefa e o incidente, preparar uma primeira versão da miniatura e orientar os testes e a escrita do laudo. Ela também produziu a versão inicial do código e do roteiro de execução. A equipe revisou o código. Os resultados apresentados no laudo vieram das execuções registradas na pasta `logs/`.

## Pedidos e decisões

Os pedidos abaixo estão resumidos, sem reproduzir a conversa palavra por palavra.

1. **Entendimento da atividade e escolha do caso.** A IA explicou os requisitos e sugeriu estudar a Cloudflare. A escolha foi mantida porque o limite de configuração podia ser demonstrado em pequena escala.
2. **Miniatura e testes.** A IA preparou o código inicial de três serviços e um roteiro para medir respostas com e sem mitigação. O roteiro foi executado e os logs foram preservados para conferência.
3. **Redação do laudo.** Foi pedido um texto com base no artigo e nas medições. O rascunho foi mantido para revisão, com as limitações da miniatura e as pendências identificadas.
4. **Risco no Raízes.** Foi pedido um teste local da hipótese ligada ao arquivo OpenAPI. O teste foi feito em cópias do backend, e o parecer foi atualizado com os resultados. A hipótese não foi apresentada como falha observada em produção.
5. **Revisão do experimento.** Foi pedido que os cenários fossem repetidos e que a mitigação fosse verificada após um reinício. Foi preparado um teste adicional, cuja hipótese e respostas foram registradas em `logs/reinicio-mitigacao/`; o laudo recebeu a limitação observada.

## Erros identificados ao executar

1. **Cópia do código para o teste:** a primeira versão do script usou `fs.cpSync` e o processo terminou antes de preparar a cópia, sem mensagem de erro disponível. A causa específica não foi estabelecida. A cópia foi substituída por uma rotina que percorre os diretórios e copia os arquivos; a execução posterior conseguiu preparar os cenários. As primeiras pastas de log contêm apenas metadados e não devem ser tratadas como resultados.
2. **Tempo de espera insuficiente:** uma versão do script limitava a espera em 15 segundos. Numa execução, o cenário válido atingiu esse limite sem abrir a porta e o teste o encerrou; não houve erro de aplicação no log. A causa exata da demora não foi estabelecida. A espera máxima passou a 60 segundos; na execução seguinte, o controle válido respondeu HTTP 200. O resultado inicial está em `logs/raizes-openapi/2026-11-23T02-27-35-841Z-21b5fa/valido.json` e a execução posterior em `logs/raizes-openapi/2026-11-23T02-28-26-994Z-a522e1/`.
