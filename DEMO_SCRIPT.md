# Ford Intelligence OS — Demo Script
## Ford x Universidade 2026 | Apresentação ao Vivo

**Duração total estimada: 10–12 minutos**
**URL da demo: http://localhost:8501**
**Prepare antes: dashboard aberto, aba "Consulta Inteligente" visível**

---

## ABERTURA (30 segundos)

> *Fale olhando para os avaliadores, não para a tela.*

"Toda semana, a Ford lança uma promoção, uma nova versão, um novo argumento de venda. Enquanto isso, a Volkswagen e a Toyota estão fazendo o mesmo. Hoje, descobrir o que o concorrente está oferecendo exige horas de pesquisa manual. E quando você finalmente tem essa informação, ela já está separada do cliente que você poderia estar abordando com ela.

O Ford Intelligence OS resolve exatamente esse problema: ele coleta inteligência competitiva em tempo real dos sites brasileiros dos fabricantes, conecta isso com a base de clientes Ford, e gera a ação de retenção certa, na hora certa, para o cliente certo. Tudo integrado, tudo automatizado."

---

## DEMO AO VIVO

### TAB 1 — Consulta Inteligente (2 minutos)

*Clique na aba "Consulta Inteligente".*

> "Vamos começar com uma pergunta real que um gerente de produto da Ford faria."

**Digite exatamente no campo de busca:**
```
Qual é a potência e o torque das versões mais potentes da Ranger, Hilux e Amarok disponíveis no Brasil?
```

*Aguarde o resultado. Enquanto carrega, diga:*

> "Estou digitando em português. O sistema converte isso automaticamente em SQL via LLM — sem nenhuma configuração manual da consulta."

*Quando aparecer a tabela de resultados:*

> "Reparem três coisas: primeiro, os resultados têm a fonte — carrosnaweb.com.br, coletado hoje. Segundo, a consulta SQL gerada aparece abaixo, transparente e auditável. Terceiro, isso inclui specs de quatro fabricantes diferentes, todos na mesma base."

**Digite uma segunda pergunta:**
```
Quais modelos concorrentes oferecem mais torque que a Ranger XLT a diesel?
```

> "Essa é a pergunta que o vendedor precisa responder antes de entrar numa negociação. Em dois segundos, o sistema cruza a frota Ford com o mercado inteiro."

---

### TAB 2 — Ficha Tecnica Comparativa (1 minuto 30 segundos)

*Clique na aba "Ficha Tecnica Comparativa".*

> "Aqui o gerente comercial consegue montar uma comparação visual instantânea."

*No seletor de modelos:*
1. Selecione **Ford Ranger Storm 4x4** (ou a versão mais completa disponível)
2. Adicione **Toyota Hilux SRX**
3. Adicione **Volkswagen Amarok V6**

> "Três marcas, lado a lado, todos os campos — potência, torque, capacidade de carga, tração, preço base. Se um campo é vantagem Ford, aparece destacado. Se é desvantagem, aparece sinalizando onde o concorrente lidera."

*Aponte para uma linha onde a Ford lidera:*

> "Aqui o vendedor encontra o argumento. Aqui ele fecha a venda."

---

### TAB 3 — Retencao & Churn (2 minutos)

*Clique na aba "Retencao & Churn".*

> "Módulo 2: retenção de clientes. A base aqui é a frota Ford — clientes reais, veículos reais, histórico de revisões."

*Aponte para o painel de scoring:*

> "Cada cliente tem um score de risco de 0 a 100. O algoritmo usa quatro sinais: tempo desde a última revisão paga, quilometragem acumulada, histórico de reclamações, e proximidade do vencimento da garantia. Quanto maior o score, maior o risco de o cliente migrar para outro fabricante."

*Mostre o filtro de threshold:*

> "Posso filtrar por risco acima de 70 — esses são os clientes em estado crítico. São eles que vamos trabalhar agora."

*Aponte para um cliente com score alto na tabela:*

> "Esse cliente está com score 87. A última revisão foi há 14 meses, a garantia vence em 60 dias, e o veículo tem 58.000 km. Sem intervenção, a probabilidade de ele não voltar à rede Ford é alta."

> "Mas reparem: o sistema não só detecta o risco. Ele age."

---

### TAB 4 — A Ponte (Demo) (3 minutos)

*Clique na aba "A Ponte (Demo)".*

> "Essa é a inovação central do nosso projeto: a ponte entre inteligência competitiva e retenção. Um fluxo de cinco passos."

*Mostre o fluxo na tela enquanto descreve cada passo:*

**Passo 1 — Seleção do cliente em risco**
> "O sistema puxou automaticamente o cliente de maior risco. Score 87, dono de uma Ranger 2021."

**Passo 2 — Análise competitiva direcionada**
> "O sistema pergunta: qual concorrente ameaça especificamente esse perfil de cliente? Para uma Ranger diesel com alto km, o candidato mais provável é a Hilux. O sistema busca na base de specs o diferencial atual da Hilux versus a Ranger."

**Passo 3 — Identificação do argumento Ford**
> "Aqui aparece o JOIN — a ponte de verdade. Os dados do Módulo 1 alimentam o contexto do Módulo 2. O sistema identifica que a Ranger tem vantagem em capacidade de carga e que a Ford está com campanha de revisão com desconto. Esse é o argumento."

**Passo 4 — Geração do template WhatsApp**
> "Um LLM gera uma mensagem personalizada. Não é um template genérico — usa o nome do cliente, o modelo específico, o argumento competitivo correto, e uma chamada para ação com urgência real."

*Leia em voz alta o template gerado (ou aponte para ele):*

> "Olá [Nome], tudo bem? Vimos que sua Ranger está chegando nos 60.000 km — o momento perfeito para a revisão preventiva. Além de manter o desempenho que você já conhece, temos uma condição especial este mês para clientes como você. Posso te passar os detalhes?"

> "Isso não é marketing em massa. É o argumento certo, para o cliente certo, no momento certo."

**Passo 5 — Confirmação LGPD**
> "Antes de qualquer disparo, o sistema verifica o campo lgpd_consent. Se o cliente não deu consentimento explícito, o template não é gerado. Compliance automático, sem depender de checklist manual."

---

## ARQUITETURA TECNICA (1 minuto)

> *Opcional: se houver slide de arquitetura, mude para ele. Se não, descreva verbalmente.*

"Rapidamente sobre como isso funciona por baixo:

O **scraper** usa Playwright com regex dinâmico — ele descobre os modelos atuais direto dos sites dos fabricantes, sem ter nenhum ano ou nome de modelo hardcoded. O ford.com.br bloqueia scraping via WAF, então usamos o carrosnaweb.com.br como fonte verificada para os dados de mercado brasileiro.

O banco é **PostgreSQL** com modelo EAV — uma tabela central de specs com colunas campo e valor, que permite armazenar qualquer atributo de qualquer veículo sem precisar alterar o schema quando um fabricante lança uma feature nova.

A camada de **NL Query** converte perguntas em português para SQL via LLM, com um sanitizador de segurança que bloqueia qualquer comando fora de SELECT e WITH — sem risco de injeção ou alteração acidental dos dados.

Os **templates WhatsApp** passam por um revisor automático que compara os números citados pelo LLM com os campos de entrada — se o LLM alucinar um número de potência errado, o sistema rejeita a mensagem antes de chegar no cliente.

Temos **97 testes automatizados** cobrindo scraper, scoring, SQL sanitizer e geração de template. O projeto está no GitHub e deployado no Streamlit Cloud."

---

## PERGUNTAS PREVISTAS — Q&A PREP

### "Os dados do concorrente são reais ou sintéticos?"

> "Os specs de mercado foram coletados por scraping real dos sites brasileiros dos fabricantes — 94 registros reais, incluindo Ford Ranger em 4 versões, VW com 10 modelos, Toyota com 15 modelos e Mitsubishi. A base de clientes Ford usada na demo é sintética, gerada para preservar privacidade de dados reais. Em produção, seria conectada ao CRM Ford via API ou ETL."

### "Por que vocês não scraped o ford.com.br diretamente?"

> "Ford.com.br tem WAF ativo que retorna 403 para qualquer scraper automatizado — isso protege a infraestrutura deles, mas significa que os dados Ford no nosso Módulo 1 seriam os dados que a própria Ford já conhece. O valor competitivo está nos dados dos concorrentes. Para os dados Ford, a fonte natural em produção seria o próprio sistema interno da Ford, não scraping externo."

### "Como o sistema escala para toda a frota Ford Brasil?"

> "O scoring é rule-based — roda em O(n) linear, sem necessidade de modelo de ML que precise retreinamento. Para 500 mil veículos na frota, o processamento completo leva minutos no PostgreSQL. O scraper é incremental — só re-coleta specs que mudaram. A geração de template usa LLM, que é o único gargalo de custo variável, mas só é invocado para clientes acima do threshold de risco definido."

### "Qual o custo operacional do LLM?"

> "Usamos o modelo gpt-5.4-nano, que tem o menor custo por token da família GPT-5. Para a camada de NL Query, o custo por consulta é na ordem de frações de centavo. Para geração de templates em escala, o custo é ativado só para clientes de alto risco — se você define threshold 70, você está ativando LLM para 20-30% da frota, não 100%."

### "Vocês pensaram em LGPD?"

> "Sim, e foi uma decisão de arquitetura, não um afterthought. Todo SELECT na tabela de retenção tem filtro obrigatório de lgpd_consent = TRUE aplicado no próprio SQL sanitizer — a query não executa sem esse filtro. Se um cliente revoga o consentimento, ele sai automaticamente do scope de todas as consultas e templates na próxima execução."

### "O que diferencia isso de um BI tradicional como Power BI?"

> "Três coisas: primeiro, os dados chegam dos sites dos concorrentes automaticamente — BI tradicional precisaria de alguém alimentando planilhas manualmente. Segundo, a interface é linguagem natural em português — qualquer gerente regional usa, sem precisar aprender SQL ou Power Query. Terceiro, o sistema não só mostra dados, ele age — o output final é uma mensagem de retenção pronta para ser enviada, não um gráfico para alguém interpretar e decidir o que fazer."

### "Qual seria o próximo passo para produção?"

> "Três sprints: primeiro, conectar o Módulo 2 ao CRM Ford real via API — provavelmente Salesforce ou sistema interno. Segundo, adicionar feedback loop — quando um cliente responde ao WhatsApp, o score é atualizado. Terceiro, expandir para outros segmentos além de pickups — o modelo EAV no banco já suporta qualquer tipo de veículo sem mudança de schema."

---

## FECHAMENTO (30 segundos)

> *Fale para os avaliadores novamente, não para a tela.*

"O que mostramos hoje não é um protótipo de faculdade. É uma plataforma com dados reais de mercado brasileiro, 97 testes automatizados, compliance LGPD embutido, e um produto que um gerente da Ford poderia abrir agora e usar sem treinamento.

O gap entre inteligência competitiva e ação de retenção custa clientes todos os dias. O Ford Intelligence OS fecha esse gap.

Obrigado."

---

## CHECKLIST PRE-DEMO

Antes de entrar na sala, confirme:

- [ ] `streamlit run app/main.py` rodando em localhost:8501
- [ ] Banco PostgreSQL acessível (testar: `python scripts/run_churn_scorer.py --threshold 70`)
- [ ] `.env` com `OPENAI_API_KEY` e `DATABASE_URL` configurados
- [ ] Dados carregados: pelo menos 94 specs e clientes sintéticos no banco
- [ ] NL Query testada uma vez para garantir que o LLM está respondendo
- [ ] Aba "A Ponte" com pelo menos 1 cliente de score acima de 70 para demonstrar
- [ ] Conexão de internet estável (LLM call em tempo real)
- [ ] Tela em modo de apresentação — esconder barra de endereço, abas do navegador

---

## TIMING SUGERIDO

| Segmento | Duração |
|---|---|
| Abertura | 30s |
| Tab 1 — Consulta Inteligente | 2min |
| Tab 2 — Ficha Tecnica Comparativa | 1min 30s |
| Tab 3 — Retencao & Churn | 2min |
| Tab 4 — A Ponte | 3min |
| Arquitetura Tecnica | 1min |
| Fechamento | 30s |
| **Total sem Q&A** | **~10min 30s** |
| Q&A | 3-5min |
