import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

BASE = Path(__file__).resolve().parent
SAIDA = BASE / 'laudo-cloudflare.pdf'
fontes = Path(reportlab.__file__).parent / 'fonts'
pdfmetrics.registerFont(TTFont('Arial', str(fontes / 'Vera.ttf')))
pdfmetrics.registerFont(TTFont('Arial-Bold', str(fontes / 'VeraBd.ttf')))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TituloLaudo', fontName='Arial-Bold', fontSize=15, leading=19, spaceAfter=9))
styles.add(ParagraphStyle(name='SubLaudo', fontName='Arial-Bold', fontSize=11, leading=14, spaceBefore=8, spaceAfter=5))
styles.add(ParagraphStyle(name='TextoLaudo', fontName='Arial', fontSize=9.4, leading=13, spaceAfter=6))
styles.add(ParagraphStyle(name='PequenoLaudo', fontName='Arial', fontSize=8, leading=10.5, spaceAfter=3, wordWrap='CJK'))
styles.add(ParagraphStyle(name='CaixaLaudo', fontName='Arial', fontSize=9, leading=12, leftIndent=8, rightIndent=8, spaceAfter=7, textColor=colors.HexColor('#513d0d'), backColor=colors.HexColor('#fff4d8'), borderPadding=7))
styles.add(ParagraphStyle(name='CodigoLaudo', fontName='Courier', fontSize=8, leading=11, leftIndent=12, spaceAfter=8))
P = lambda s: Paragraph(s, styles['TextoLaudo'])
S = lambda s: Paragraph(s, styles['SubLaudo'])
small = lambda s: Paragraph(s, styles['PequenoLaudo'])

def tabela(rows, widths):
    dados = [[small(str(cell)) for cell in row] for row in rows]
    t = Table(dados, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),0.5,colors.black),
        ('LINEBELOW',(0,0),(-1,0),0.5,colors.black), ('LINEBELOW',(0,-1),(-1,-1),0.5,colors.black),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return t

story = []
story += [Paragraph('Laudo técnico - incidente da Cloudflare', styles['TituloLaudo']),
 P('Disciplina: Fundamentos de Computação Concorrente, Paralela e Distribuída<br/>Integrantes: Ramon Taffarel Guimarães e Pedro Henrique Cavalcanti e Silva<br/>Repositório do experimento: <link href="https://github.com/Ramontaffa/cloudflare-miniatura" color="#205a88">github.com/Ramontaffa/cloudflare-miniatura</link>.'),
 S('A. Mecanismo e conceito'),
 P('<b>Mecanismo em uma frase:</b> uma mudança no acesso a metadados levou à geração e distribuição de uma configuração com entradas duplicadas que ultrapassou o limite do módulo de Bot Management, causando erros em serviços dependentes do proxy [1].'),
 P('O conceito principal é <b>efeito cascata</b>. A configuração compartilhada ultrapassou o limite do módulo do proxy, e a falha afetou produtos que dependiam dele, incluindo Workers KV e Access. O acoplamento desses produtos ao proxy explica a propagação do impacto [1, seções “How Cloudflare processes requests...” e “Other impact...”].'),
 S('Linha do tempo do caso real'),
 P('Horários em UTC, conforme a tabela ao final do relato oficial [1].'),
 tabela([['Horário','Evento e localização no artigo'],
 ['11:05','Alteração de controle de acesso no banco. Tabela final; seção “The query behaviour change”.'],
 ['11:28','A tabela final registra os primeiros erros observados no tráfego HTTP de clientes.'],
 ['13:05','Desvios no caminho de Workers KV e Access reduziram o impacto. Tabela final.'],
 ['13:37','A equipe concentrou esforços em voltar à última configuração válida. Tabela final.'],
 ['14:24-14:30','A geração e propagação foram interrompidas; uma configuração correta foi distribuída e o impacto principal diminuiu. Tabela final.'],
 ['17:06','Todos os serviços estavam recuperados. Tabela final e seção “The outage”.']], [3*cm,14.2*cm]),
 Spacer(1,5),small('Nota: a abertura do artigo menciona falhas significativas desde 11:20 UTC; a tabela final registra 11:28 para os primeiros erros observados no tráfego de clientes. O relato apresenta ambos os horários [1].'),
 PageBreak(), S('B. Miniatura e limitações'),
 P('A miniatura usa três containers na rede Docker “experimento”. O gerador escreve um arquivo em um volume compartilhado, montado no consumidor; o cliente aciona as mudanças e faz requisições HTTP. As setas representam dependências e fluxo de dados, não conexões da arquitetura real.'),
 Preformatted('Rede Docker: experimento\n\n [gerador] ---- volume configuracao ----> [consumidor]\n      ^                                      ^\n      | comandos HTTP                        | requisicoes HTTP\n      +------------- [cliente] --------------+', styles['CodigoLaudo']),
 tabela([['Container','Função no experimento','Correspondência aproximada no incidente'],
 ['gerador','Publica configuração válida ou inválida.','Processo de geração e distribuição do arquivo de features.'],
 ['consumidor','Lê o arquivo e responde às requisições.','Módulo do proxy dependente da configuração.'],
 ['cliente','Aciona mudanças, envia requisições e registra respostas.','Tráfego que depende do serviço afetado.']], [3*cm,6.5*cm,7.7*cm]),
 Spacer(1,8),P('Na miniatura, o gerador publicou uma configuração válida com 5 entradas e uma versão com 12 entradas, incluindo duplicatas, que excedeu o limite do consumidor. As publicações foram registradas em [L1a], linhas 1 e 3. O limite no caso real era de 200 features [1, seção “Memory preallocation”].'),
 S('O que não foi reproduzido'),
 tabela([['Limitação','Efeito sobre as conclusões'],
 ['Um único consumidor e nenhum rollout global.','Não permite estimar alcance geográfico nem quantos clientes seriam afetados.'],
 ['Duplicatas geradas diretamente, sem ClickHouse ou alteração de permissões.','Demonstra o efeito do arquivo inválido, mas não confirma a cadeia completa que o gerou no incidente.'],
 ['O serviço devolve 503 de forma simulada; não implementa o proxy real ou seus produtos dependentes.','Não representa diferenças entre versões do proxy nem todos os tipos de impacto observados.'],
 ['Carga sequencial e pequena, sem distribuição real.','Tempos e percentual de erro dependem do roteiro local e não estimam os do incidente real.']], [7.8*cm,9.4*cm]),
 PageBreak(),S('C. Experimento e evidências'),
 P('Após a prontidão, foram enviadas 20 requisições com configuração válida, 80 com configuração inválida e 30 após sua restauração, com uma pausa programada entre as chamadas [L1, L2]. O primeiro cenário devolve 503 quando o arquivo excede o limite; no segundo, a versão válida permanece em memória.'),
 tabela([['Métrica','Sem mitigação [L1]','Com mitigação [L2]'],
 ['Requisições / erros','130 / 80','130 / 0'],
 ['Erros no total','61,54% (80 / 130)','0% (0 / 130)'],
 ['Da injeção até a primeira falha','0,057252 s (linhas 22–23)','Não observada na janela'],
 ['Da primeira falha até a recuperação','15,428171 s (linhas 23 e 104)','Não aplicável: sem falha observada'],
 ['Da restauração até a recuperação','0,042365 s (linhas 103–104)','Não aplicável: sem falha observada']], [6.0*cm,5.6*cm,5.6*cm]),
 Spacer(1,7),P('A taxa inclui respostas fora de 2xx e falhas de conexão nas três fases. A injeção e a restauração são registradas quando o cliente recebe a confirmação do gerador. A recuperação é marcada pela primeira de três respostas consecutivas bem-sucedidas após a restauração. Os tempos refletem o roteiro e a frequência das sondagens no laboratório.'),
 P('Na execução sem mitigação, as 80 respostas durante a configuração inválida foram 503; as demais foram 200 [L1]. Com mitigação, todas as respostas foram 200, inclusive durante a fase inválida [L2]. O log do consumidor registra a rejeição da configuração [L3].'),
 P('O comportamento qualitativo é compatível com o mecanismo descrito no artigo: uma configuração maior do que o limite afetou o processamento, e uma versão válida ajudou a recuperar o serviço. No caso real, a configuração alternou entre versões válidas e inválidas durante parte do incidente e a recuperação global envolveu outros sistemas; nossa miniatura não reproduz essas oscilações nem a escala do evento [1, “The outage”]. Os percentuais não são comparáveis diretamente.'),
 P('<b>Teste adicional:</b> formulamos a hipótese de que a mitigação continuaria atendendo depois do reinício do consumidor, mesmo com a configuração inválida publicada. Antes do reinício, a resposta foi 200; após ele, foi 503. Quando a configuração válida foi restaurada, a resposta voltou a 200 [L5]. A hipótese não se confirmou: o código guarda a última versão válida apenas na memória, que é perdida quando o processo reinicia. O teste mostra uma limitação da mitigação, sem representar um novo incidente na Cloudflare.'),
 S('Arquivos de evidência'),
 small('[L1] logs/sem-mitigacao/20261123-113212-68649cf6/eventos.jsonl e resumo.json.'),
 small('[L1a] logs/sem-mitigacao/20261123-113212-68649cf6/containers.log.'),
 small('[L2] logs/com-mitigacao/20261123-113305-61675713/eventos.jsonl e resumo.json.'),
 small('[L3] logs/com-mitigacao/20261123-113305-61675713/containers.log.'),
 small('[L5] logs/reinicio-mitigacao/20261123T143128Z-f6a67e76/eventos.jsonl e containers.log.'),
 PageBreak(),S('D. Parecer e mitigação'),
 P('<b>Parecer sobre o Raízes PE:</b> identificamos uma dependência de arquivo compartilhado que pode afetar a disponibilidade do backend. Em <b>backend/src/config/openapi.ts</b>, linhas 7-9, <b>parse(readFileSync(... "openapi.yaml" ...))</b> lê e interpreta a especificação na carga do módulo. Em <b>backend/src/app.ts</b>, linhas 3 e 15, essa especificação é importada na inicialização do mesmo aplicativo que monta as rotas da API [2].'),
 P('<b>Teste local:</b> copiamos o código do backend e carregamos o app Express em três cenários, sem alterar os arquivos originais ou configurar acesso ao banco. Com o OpenAPI original, o app abriu uma porta local e GET /api/saude respondeu HTTP 200. Com o arquivo ausente, o processo encerrou com ENOENT; com YAML sintaticamente inválido, encerrou com YAMLParseError. Nos dois casos, terminou antes de abrir a porta [L4].'),
 P('O resultado confirma o risco de inicialização para essas duas falhas na cópia testada. Ele não comprova o estado do serviço publicado nem o comportamento de todas as configurações inválidas: o trecho interpreta YAML, mas não valida o esquema OpenAPI. A comparação da miniatura não mede o impacto do Raízes.'),
 P('A semelhança com a Cloudflare é o <b>acoplamento a um arquivo comum</b> capaz de ampliar o impacto de um problema local. Há diferenças importantes: no Raízes, o risco identificado envolve leitura ou sintaxe na inicialização, não um limite de features excedido, nem foi demonstrada distribuição global de uma configuração. O teste da miniatura não prova que esse incidente ocorreu no Raízes.'),
 P('<b>Mitigação aplicada:</b> ao receber mais entradas do que o limite, o consumidor rejeita a nova configuração e preserva a última versão válida em memória. A comparação [L1, L2] mostra 80 erros sem mitigação e nenhum com ela para este roteiro. Isso não prova que a solução protege contra todos os defeitos: se o processo iniciar sem ter carregado uma versão válida, ou se o arquivo não puder ser lido, a resposta ainda pode ser 503.'),
 P('<b>Recomendação:</b> validar o YAML e o esquema OpenAPI no processo de entrega e avaliar desacoplar a documentação das rotas essenciais. Para configurações de runtime, validar antes da ativação e monitorar rejeições. São propostas, ainda não implementadas ou testadas como mitigação no Raízes.'),
 small('[L4] logs/raizes-openapi/2026-11-23T02-28-26-994Z-a522e1/: valido.json, ausente.json, yaml-invalido.json e os respectivos arquivos .stdout.log e .stderr.log. Metadados e hashes estão em metadados.json.'),
 S('Referência'),
 P('[1] CLOUDFLARE. <i>Cloudflare outage on November 18, 2025.</i> 18 nov. 2025. Disponível em: <link href="https://blog.cloudflare.com/18-november-2025-outage/" color="#205a88">blog.cloudflare.com/18-november-2025-outage/</link>.'),
 P('[2] RAÍZES PE, cópia local na branch main, commit base fae222b, com alterações locais. Arquivos: backend/src/config/openapi.ts e backend/src/app.ts. Repositório: <link href="https://github.com/brunosm26/Raizes-PE" color="#205a88">github.com/brunosm26/Raizes-PE</link>. A cópia local não comprova o estado em produção.')]

def rodape(canvas, doc):
    canvas.setFont('Arial', 8)
    canvas.setFillColor(colors.black)
    canvas.drawString(2*cm, 1.25*cm, 'Laudo técnico - Cloudflare')
    canvas.drawRightString(19*cm, 1.25*cm, str(doc.page))

doc = SimpleDocTemplate(str(SAIDA), pagesize=(21*cm,29.7*cm), leftMargin=1.9*cm, rightMargin=1.9*cm, topMargin=1.7*cm, bottomMargin=1.8*cm, title='Laudo técnico - Cloudflare')
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(SAIDA)
