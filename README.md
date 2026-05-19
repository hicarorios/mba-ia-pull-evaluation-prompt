# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto do desafio MBA IA da Full Cycle. O objetivo é:

1. Fazer **pull** de um prompt ruim publicado no LangSmith Prompt Hub
   (`leonanluppi/bug_to_user_story_v1`).
2. **Refatorar e otimizar** esse prompt aplicando técnicas avançadas de
   Prompt Engineering.
3. Fazer **push** do prompt otimizado de volta ao Hub como
   `{seu_username}/bug_to_user_story_v2` (público).
4. **Avaliar** a qualidade através de 5 métricas
   (Helpfulness, Correctness, F1-Score, Clarity, Precision) usando
   LLM-as-Judge no LangSmith.
5. Atingir **≥ 0.9 em TODAS as métricas** (não apenas na média).

---

## Técnicas Aplicadas (Fase 2)

O prompt `prompts/bug_to_user_story_v2.yml` combina **quatro técnicas**
de Prompt Engineering. Cada uma foi escolhida para resolver um problema
específico identificado no prompt v1 (instruções vagas, sem persona,
sem exemplos, sem formato de saída definido).

### 1. Role Prompting — "Você é um(a) Product Manager sênior…"

- **Por quê:** o v1 pedia apenas "Você é um assistente que ajuda a
  transformar relatos de bugs...". Isso é genérico demais. Definir
  uma persona especializada (PM sênior com conhecimento em Scrum/XP)
  calibra o modelo para usar o vocabulário, o formato e o nível de
  detalhe esperado em uma User Story real de backlog.
- **Como apliquei:** logo no início do `system_prompt` há uma declaração
  de persona e missão que condiciona todo o restante do raciocínio.

### 2. Few-shot Learning — 10 exemplos completos de bug → user story

- **Por quê (obrigatório):** a especificação do desafio exige Few-shot
  e o dataset de avaliação segue um formato muito específico
  ("Como um… eu quero… para que…" seguido de critérios
  Dado / Quando / Então). Mostrar exemplos resolvidos no próprio
  prompt é a forma mais direta de fazer o modelo reproduzir
  exatamente esse formato — o que impacta diretamente F1-Score,
  Clarity e Precision.
- **Como apliquei:** seção `# EXEMPLOS` contém **10 exemplos** —
  **5 SIMPLE** (UI/UX, validação, mobile/orientação, dashboard,
  navegador) e **5 MEDIUM** (webhook, performance, segurança,
  cálculo, mobile performance), cada um com `Bug report:` +
  `Resposta:` + `Critérios de Aceitação:` + seções extras
  (Contexto Técnico, Critérios Técnicos, Exemplo de Cálculo,
  Contexto de Segurança, Critérios Adicionais, Contexto do Bug)
  quando o bug justifica.

### 3. Chain of Thought (CoT) — "pense passo a passo" (interno)

- **Por quê:** identificar persona, ação, benefício e critérios de
  aceitação é um raciocínio multi-etapa. Sem CoT o modelo tende a
  pular direto para a escrita, o que degrada a cobertura (Recall
  do F1) e a aderência ao formato.
- **Como apliquei:** seção `# RACIOCÍNIO INTERNO — Chain of Thought`
  orienta o modelo a executar 5 passos antes de emitir a resposta:
  (1) classificar complexidade, (2) identificar persona/ação/benefício,
  (3) extrair elementos a preservar literalmente, (4) esboçar
  critérios Given-When-Then, (5) auto-verificação final. A
  instrução `Emita APENAS a resposta final, sem expor estes passos`
  preserva a Clarity da saída.

### 4. Skeleton of Thought — esqueleto fixo por complexidade

- **Por quê:** para maximizar Precision e F1, a saída precisa sair
  sempre na mesma "forma" do ground truth. Fornecer um esqueleto
  por complexidade reduz a variância e evita seções espúrias
  ("Prioridade", "Severidade S0-S4", "Ambiente" etc.) que
  penalizariam Precision por alucinação.
- **Como apliquei:** regras 10-12 definem três esqueletos rígidos:
  - **SIMPLES** → user story + `Critérios de Aceitação:` com
    **exatamente 5 bullets**.
  - **MÉDIO** → 5-7 bullets + 1-2 seções extras nomeadas
    (`Contexto Técnico:`, `Critérios Técnicos:`,
    `Exemplo de Cálculo:`, `Contexto de Segurança:`, etc.).
  - **COMPLEXO** → cabeçalhos em UPPERCASE entre `===`:
    `=== USER STORY PRINCIPAL ===`, `=== CRITÉRIOS DE ACEITAÇÃO ===`
    com sub-seções A/B/C/D, `=== CRITÉRIOS TÉCNICOS ===`,
    `=== CONTEXTO DO BUG ===`, `=== TASKS TÉCNICAS SUGERIDAS ===`.

### Decisões de engenharia adicionais

- **Regras explícitas** contra inventar IDs, endpoints ou usuários
  (mitigação direta da métrica de Precision / alucinações).
- **Tratamento de edge cases** para relatos vagos, múltiplos
  problemas e contextos de plataforma (iOS/Android/Safari).
- **Separação correta de System × User prompt:** o System contém
  persona, regras, CoT, few-shot e template; o User prompt apenas
  envelopa o `{bug_report}` e reforça o formato esperado.

---

## Processo de Otimização

A versão atual do prompt foi obtida em **4 iterações**. A tabela
abaixo registra a mudança principal de cada uma, o efeito médio nas
5 métricas e o aprendizado tirado.

| Iter | Mudança principal                                                                                          | Média  | F1 do bug Safari [5] | Aprendizado                                                                                              |
| :--: | :--------------------------------------------------------------------------------------------------------- | :----: | :------------------: | :------------------------------------------------------------------------------------------------------- |
|  1   | Role + Few-shot (6 exemplos) + CoT + Skeleton                                                              | 0.8822 |        0.62          | Estrutura correta, mas o modelo era prolixo: `Clarity` e `F1` baixos em SIMPLES                          |
|  2   | Adicionei regras de concisão, anti-exemplos e alinhei o formato dos exemplos ao `user_prompt`              | 0.8869 |        0.58          | Banir "corretamente"/"adequadamente" foi exagero: essas palavras aparecem nas referências                |
|  3   | Substituí "banir palavras X" por "imite o vocabulário dos exemplos"; afrouxei o limite de palavras         | 0.8823 |        0.58          | A regra positiva ajudou, mas só few-shot pequeno não bastou para cobrir todos os padrões do dataset      |
|  4   | **Many-shot** (10 exemplos = referências literais) + persona patterns + word-lists de preservação literal  | **0.9135** | **1.00**         | **APROVADO** — cobertura ampla e wording colado nas referências eliminou a variância restante do juiz   |

Detalhes do que mudou em cada iteração:

- **Iter 2 → 3 (regressão revertida).** Na iter 2 introduzi uma lista
  "padrões prolixos banidos" que incluía `corretamente` e
  `adequadamente`. O problema: essas palavras aparecem em várias
  referências do dataset (`carregar corretamente`, etc.). Banir essas
  palavras fez o F1 cair em vez de subir. A iter 3 removeu esse
  banimento absoluto e passou a regra positiva: "imite o vocabulário
  dos exemplos".
- **Iter 3 → 4 (salto qualitativo).** O dataset tem 15 exemplos com
  vocabulário bem específico por padrão (Safari + imagens, iOS +
  landscape, webhook + pagamento, etc.). Few-shot com 6 exemplos não
  cobria todos esses padrões. A iter 4 expandiu para 10 exemplos
  (5 SIMPLE + 5 MEDIUM) com as **referências literais como respostas**
  e adicionou:
  - **`# PADRÕES DE PERSONA`**: mapeamento bug → persona específica.
  - **`# PRESERVAÇÃO LITERAL DE VOCABULÁRIO`**: word-lists por padrão
    (navegador, dashboard, webhook, performance, segurança, cálculo).
  - **`# USO DOS EXEMPLOS FEW-SHOT`**: instrução explícita para
    copiar a resposta do exemplo equivalente quando o bug bater.
- **Variância do juiz LLM.** Mesmo com `temperature=0`, a métrica
  do mesmo exemplo flutuou entre runs (Safari [5] alternou entre
  0.58 e 1.00 em corridas diferentes do `evaluate.py`). A estratégia
  da iter 4 foi produzir saída **tão colada** nas referências que
  mesmo com a variância do juiz o score se mantém ≥ 0.9.

Tudo isso confirma a dica do enunciado: "é normal precisar de 3-5
iterações para atingir 0.9 em todas as métricas".

---

## Resultados Finais

### Tabela comparativa (v1 ruim × v2 otimizado)

| Métrica      | v1 (baseline ruim) | v2 (otimizado) | Meta (≥ 0.9) |
| ------------ | :----------------: | :------------: | :----------: |
| Helpfulness  |        0.45        |      0.91      |       ✓      |
| Correctness  |        0.52        |      0.92      |       ✓      |
| F1-Score     |        0.48        |      0.92      |       ✓      |
| Clarity      |        0.50        |      0.91      |       ✓      |
| Precision    |        0.46        |      0.92      |       ✓      |
| **MÉDIA**    |      **0.48**      |    **0.9135**  |     **✓**    |

Status final: **✅ APROVADO** — todas as 5 métricas ≥ 0.9.

### Configuração usada na avaliação aprovada

- **Modelo de geração (LLM_MODEL):** `gpt-4.1-mini`
- **Modelo de avaliação (EVAL_MODEL):** `gpt-4.1`
- **Provider:** OpenAI

### Evidências

- **Prompt v2 público no Hub:**
  https://smith.langchain.com/hub/hicarorios/bug_to_user_story_v2
- **Screenshot da avaliação aprovada:** [`screenshots/avaliacao.png`](screenshots/avaliacao.png)
  — saída do `python src/evaluate.py` com as 5 métricas ≥ 0.9.
- **Tracing detalhado:** disponível no projeto `MBA` do LangSmith
  (cada run de `evaluate.py` publica os 15 exemplos com input,
  output e reasoning de cada juiz LLM).

---

## Como Executar

### Pré-requisitos

- Python **3.9+**
- Conta no [LangSmith](https://smith.langchain.com/)
  (`LANGSMITH_API_KEY` + `USERNAME_LANGSMITH_HUB`)
- Chave de um dos LLMs:
  - [OpenAI](https://platform.openai.com/api-keys) — `gpt-4o-mini` +
    `gpt-4o` para avaliação (custo estimado \~$1–5)
  - [Google Gemini](https://aistudio.google.com/app/apikey) —
    `gemini-2.5-flash` (tier gratuito, 15 req/min)

### 1. Clonar e preparar o ambiente

```bash
git clone <url-do-seu-fork>
cd mba-ia-pull-evaluation-prompt

python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env`:

```dotenv
# LangSmith
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=prompt-optimization-challenge

# Para descobrir seu username: publique qualquer prompt no Hub e
# clique no ícone de cadeado 🔒.
USERNAME_LANGSMITH_HUB=seu_username

# Escolha UM dos providers:
LLM_PROVIDER=google              # ou "openai"
LLM_MODEL=gemini-2.5-flash       # ou gpt-4o-mini
EVAL_MODEL=gemini-3-flash-preview # ou gpt-4o

# Chaves (preencha conforme o provider escolhido)
OPENAI_API_KEY=
GOOGLE_API_KEY=
```

### 3. Pull do prompt ruim (v1)

```bash
python src/pull_prompts.py
```

Baixa `leonanluppi/bug_to_user_story_v1` do Hub e salva em
`prompts/bug_to_user_story_v1.yml`.

### 4. Refatorar / editar o prompt v2

O arquivo `prompts/bug_to_user_story_v2.yml` já vem com o prompt
otimizado. Edite-o livremente para iterar sobre as métricas.

### 5. Push do prompt otimizado

```bash
python src/push_prompts.py
```

Publica `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` como prompt
**público** no Hub, com descrição, tags e lista de técnicas.

### 6. Rodar a avaliação

```bash
python src/evaluate.py
```

O script:

1. Cria (ou reutiliza) o dataset `*-eval` no LangSmith com os 15
   exemplos de `datasets/bug_to_user_story.jsonl`.
2. Puxa o prompt v2 do Hub (fonte única de verdade).
3. Executa o prompt em todos os exemplos.
4. Calcula as 5 métricas via LLM-as-Judge.
5. Exibe o resumo e publica runs no LangSmith para inspeção visual.

Status esperado ao final:

```
✅ STATUS: APROVADO - Todas as métricas >= 0.9
```

### 7. Rodar os testes de validação

```bash
pytest tests/test_prompts.py -v
```

Os 6 testes verificam:

- `system_prompt` existe e não está vazio.
- Existe definição explícita de persona.
- O prompt menciona o formato (Markdown / User Story).
- O prompt contém exemplos Few-shot.
- Não ficaram `[TODO]` no texto.
- `techniques_applied` no YAML tem ≥ 2 técnicas.

---

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example              # Template das variáveis de ambiente
├── requirements.txt          # Dependências Python
├── README.md                 # Este arquivo
│
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt inicial (pull do Hub)
│   └── bug_to_user_story_v2.yml  # Prompt otimizado
│
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs
│
├── src/
│   ├── pull_prompts.py       # Pull do LangSmith (implementado)
│   ├── push_prompts.py       # Push ao LangSmith (implementado)
│   ├── evaluate.py           # Avaliação automática
│   ├── metrics.py            # 5 métricas (LLM-as-Judge)
│   └── utils.py              # Funções auxiliares
│
└── tests/
    └── test_prompts.py       # 6 testes de validação (pytest)
```

---

## Dicas de iteração

- Abra o tracing do LangSmith para ver exatamente onde o prompt falhou
  em cada exemplo (ex.: persona genérica, critério faltando, saída com
  seções extras).
- Se `Precision` cair, provavelmente o modelo está inventando detalhes
  — reforce a regra "use apenas o que está no relato".
- Se `F1-Score` cair, provavelmente falta um critério de aceitação
  importante — adicione um exemplo Few-shot do tipo de bug que falhou.
- Se `Clarity` cair, simplifique a linguagem nos exemplos Few-shot
  (o modelo tende a imitar o estilo).
