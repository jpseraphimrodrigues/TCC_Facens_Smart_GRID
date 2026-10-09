# Auditoria — Consenso proporcional sob falhas de comunicação (TCC Facens)

> **Projeto:** [TCC_Facens_Smart_GRID](../README.md) · **Documento canônico** · **Última revisão:** 2026-10-09
> **Commit de referência da intervenção documental:** `d70fb55` (HEAD de `main`, 2026-10-09; árvore limpa no início da intervenção). Documentação em `docs/` ainda não versionada.
>
> Consolida a [`revisao.md`](../revisao.md) (auditoria técnica de 2026-09-25, achados A0–A9 e implementação pós-auditoria) e as decisões D1–D17 de [`implementacao.md`](../implementacao.md), ambos preservados.

## 1. Escopo da auditoria

Repositório `Mestrado/TCC_Facens_Smart_GRID/`: README, `experimento.md`, `implementacao.md`, `revisao.md`, documentos da Fase 0, protocolos, `variaveis de analise`, código principal, módulo de canal, *script* de *sweep*, testes, `.dss`, entradas, três pastas de resultados. Não houve reexecução de simulações nem de testes. `documentacao_altdss.md` (3,3 MB, documentação de terceiros) não foi lida integralmente.

## 2. Estado atual da documentação

| Documento | Papel após a intervenção |
|---|---|
| `README.md` | Índice executivo (reescrito) |
| `docs/guia_didatico.md` | Guia didático do README original (Tópico 0), transcrito sem alterações; complementar, não canônico |
| `docs/*.md` | **Fonte canônica** |
| `experimento.md` | Especificação de desenho, **referenciada pelo código por número de seção** ("Fonte de verdade do desenho experimental"); preservada com aviso; divergências da implementação registradas em D5–D6 e AUD-TCC-005 |
| `implementacao.md` | Registro de implementação (decisões D1–D17, evidências); preservado com aviso |
| `revisao.md` | **Legado** (auditoria de 25/09); consolidada aqui; aviso inserido |
| `Fase 0 - Idealização.md`, `Fase 0 - Corpus - Referências.md` | Documentos de concepção e corpus bibliográfico; preservados sem alteração |
| `Protocolos de comunicacao e sensibilidade.md`, `variaveis de analise` | Notas de apoio (protocolos de Smart Grid; hipóteses de sensibilidade; variáveis de comunicação); preservadas |
| `Skills/Paper_2…`, `Paper_3…`, `Paper_4…`, `Roteiro_Macro…` | Planejamento dos Papers 2–4 **do mestrado** (não deste TCC); indexados na raiz `Mestrado/README.md` |
| `Skills/Executor_altGRID_consenso/`, `Skills/SKILL_…`, `documentacao_altdss.md` | *Skills* de agentes e documentação AltDSS (idênticos aos do Mestrado_OPF) |

## 3. Verificações realizadas

| Verificação | Resultado |
|---|---|
| Números de `implementacao.md` §8.4 × `FASE0_EXP001/tables/resumo_completo.csv` | **Conferem** |
| Manifestos: data, commit, versões, canal | Registrados (ver [metodologia §11](metodologia.md#11-reprodutibilidade)) |
| C1–C3 em `CHANNEL_MULTI3` (código `b728e4c`) × baseline (código `7219216`) | **Idênticos** — o caminho determinístico de C1–C3 não mudou entre as versões |
| Perdas efetivas do canal × probabilidade nominal | 4,9% / 9,8% / 19,8% (LF) para 5% / 10% / 20% |
| Curvas `Entradas/curvas_24h.csv` × `CBA/CBA/CurvaPV_24pontos_CBA.xls` | **Idênticas** (24 valores de PV e de carga) |
| Convenção de tempo | Modo *SnapShot* com `LoadMult` e `Irradiance` escritos por hora — sem o deslocamento de LoadShape encontrado no Tech_economical |
| `.dss` × CBA | Igual (diferença só em CRLF); `Redirect` corrigido em memória |
| Entry point `tcc-facens` | Executa o *script* via `runpy` |
| Testes | 8 funções (não executadas nesta intervenção) |
| Arquivos versionados | 455 em `Resultados/`; `.pdf2md/index.sqlite3`, modelos `.docx`/`.zip`; sem `.gitignore` |

Verificações registradas pela implementação (todas passaram): $P_{gerada} \le P_{disp}$; balanço de energia; tensões finitas; $\lambda_2$ esperado; correção só no líder (LF); mesma $P_{disp}$ entre casos; casos em $k_{max}$ marcados.

## 4. Inconsistências encontradas

### 4.1. Achados da `revisao.md` (2026-09-25), com situação atualizada

| ID | Descrição | Correção / tratamento | Situação |
|---|---|---|---|
| AUD-TCC-001 (A1) | Fenômeno de comunicação superdeclarado: sem sorteio, semente, atraso ou fila; "PERDIDA" = aresta fora da mistura. | Canal probabilístico implementado (`communication.py`, `--enable-channel`); README qualifica falha estrutural × probabilística | Corrigido (verificado no código e nos resultados `CHANNEL_*`) |
| AUD-TCC-002 (A4) | Resultados não vinculados ao *checkout* atual: `FASE0_EXP001` gerado em `7219216`; código alterado depois. | Manifesto passou a registrar *hashes*; o baseline **não foi reexecutado**. Evidência indireta: C1–C3 idênticos em `b728e4c` | Parcialmente corrigido |
| AUD-TCC-003 (A2) | 0,2 s é rótulo de log. | Documentado como "escala temporal anotada" | Corrigido (documentação) |
| AUD-TCC-007 (A3) | "Convergência" usada em sentidos diferentes. | Status elétrico, consenso (`consenso_satisfeito`) e $k_{max}$ separados nos resultados novos | Corrigido |
| AUD-TCC-008 (A5) | Ausência de testes. | 8 testes estruturais | Corrigido (não executados aqui) |
| AUD-TCC-009 (A6) | *Entry point* inconsistente. | `tcc_facens.main` executa o experimento | Corrigido |
| AUD-TCC-010 (A7) | Curvas "de exemplo" sem origem declarada. | Ver AUD-TCC-004: origem identificada nesta intervenção | Corrigido (documentação) |
| AUD-TCC-011 (A8) | Regime quase-estático. | — | Limitação aceita |
| AUD-TCC-012 (A9) | Grafo de comunicação é hipótese manual. | README qualifica | Limitação aceita |
| AUD-TCC-013 (A0) | Falta separar "sem controle", "controle sem falha" e "falhas". | Estrutura de três camadas; C0 explícito nos dois modos | Corrigido |

### 4.2. Achados desta intervenção

| ID | Data | Descrição | Evidência | Impacto | Correção | Situação |
|---|---|---|---|---|---|---|
| AUD-TCC-004 | 2026-10-09 | As curvas usadas como "exemplo" são idênticas às da planilha `CurvaPV_24pontos_CBA.xls`, presente em `Mestrado/CBA/CBA/`. `experimento.md` §7.7, `implementacao.md` D2 e o código afirmam que o arquivo não está disponível. | Comparação valor a valor | A proveniência das curvas é a do paper-âncora (CBA 2026), não "exemplo"; muda a redação do TCC | Documentado em `metodologia.md` §5 | Aberto (atualizar texto do TCC e comentário do código) |
| AUD-TCC-005 | 2026-10-09 | `experimento.md` contém trechos superados pela implementação: §4.6 cita enlaces (2,4)/(2,3) para C1/C2; §4.5 usa "$-c_i$" e "$i = 1..5$"; §4.7 cita `tol = 10⁻⁶`; §§5.4/7.4 dizem "C4 fora de escopo, sem Monte Carlo" (o canal probabilístico foi implementado depois); §4.3 rotula 1 = 824 como líder (implementado: 1 = 816); §10 cita o líder como "agente 6/832". | `experimento.md`; D5, D6, D11, D13 | Leitura enganosa da especificação | Aviso inserido no topo; divergências consolidadas nos documentos canônicos | Aberto (decisão do autor: revisar ou manter como histórico) |
| AUD-TCC-006 | 2026-10-09 | `summary/comunicacao_por_caso.csv` de `CHANNEL_MULTI3` reporta 0 mensagens perdidas e 0% de perda nos cenários `C0_perda_*`, porque conta o log **topológico**; as perdas reais (4,9–20,2%) estão só em `raw/timestep.csv` e `raw/channel_messages.csv`. | CSVs | Tabela de resumo enganosa para o modo probabilístico | Registrado em `resultados_discussao.md` | Aberto (proposta: incluir contadores do canal no resumo) |
| AUD-TCC-014 | 2026-10-09 | $\beta$ idêntico nas duas arquiteturas: LL tem até 6 correções simultâneas contra 1 no LF; a sensibilidade com $\beta$ normalizado não foi executada. | `experimento.md` §7.5; `implementacao.md` §11 | Vantagem de convergência do LL confundida | — | Aberto |
| AUD-TCC-015 | 2026-10-09 | O líder (816) vence 850 por 1,2×10⁻⁵ pu·h; o README original mostra ambos como 0,0720 pu·h. | Manifesto; README original | Escolha do líder frágil | Registrado | Limitação aceita |
| AUD-TCC-016 | 2026-10-09 | Higiene do repositório: sem `.gitignore`; ≈ 271 MB de resultados, `documentacao_altdss.md` (3,3 MB), `.pdf2md/index.sqlite3` e modelos `.docx`/`.zip` versionados; `.git` com 62 MB. Manter resultados no Git foi decisão do pesquisador (`implementacao.md` §11). | `git ls-files`; `du` | Tamanho do repositório; risco de versionar caches | Não alterado | Aberto (proposta: `.gitignore` para caches; Git LFS ou arquivamento externo para logs grandes) |
| AUD-TCC-017 | 2026-09-25 | R5 (Zhang et al., 2019) sem PDF: o arquivo `1-s2.0-S037877962030729X-main.pdf` é uma cópia de R4. | `experimento.md` §2.2 | Citação de equações de R5 não verificável | — | Aberto |
| AUD-TCC-018 | 2026-10-09 | No modo canal, o C0 ($p$ = 0, $d$ = 1) difere do C0 do baseline em iterações (LF 1959 × 1457) e marginalmente no corte (41,633% × 41,638%), por causa do atraso. O README afirma que o C0 com canal "valida que o canal não introduz viés quando não há perda" — válido para o resultado elétrico, não para o esforço de convergência. | `resumo_completo.csv` | Interpretação do controle | Registrado | Limitação aceita |
| AUD-TCC-019 | 2026-10-09 | Tolerância de parada de 5×10⁻⁴ pu (D11) difere do código do CBA (10⁻⁶) e reduz ≈ 2 p.p. do corte; o TCC compara seu C0 (41,6%) com o paper-âncora (44,3%). | `implementacao.md` §9 | Comparação com o CBA não direta (também: 24 × 48 pontos, topologia, líder) | — | Limitação aceita |
| AUD-TCC-020 | 2026-10-09 | Barras a montante (800–812r) acima de 1,05 pu com controle (até 1,0508 pu), herança da fonte em 1,05 pu. | `implementacao.md` §11 | "Zero violações nas barras PV" ≠ "zero na rede" | Mantido por decisão | Limitação aceita |

## 5. Correções executadas

### 5.1. Pelo autor após a revisão de 25/09

*Hashes* no manifesto; separação de status elétrico/consenso/$k_{max}$; *entry point*; canal probabilístico com perda, atraso, fila, semente e última mensagem válida; argumentos de linha de comando; contadores reais do canal; testes; *script* de replicações.

### 5.2. Nesta intervenção (somente documentação)

`docs/` criado (cinco documentos canônicos + `guia_didatico.md`); `README.md` reescrito; avisos inseridos no topo de `revisao.md` (legado), `experimento.md` e `implementacao.md` (sem alterar a numeração de seções usada pelo código). Código, resultados, entradas e documentos da Fase 0 não foram alterados.

## 6. Pendências de validação

1. Reexecutar o baseline no commit atual e comparar com `FASE0_EXP001` (inclui C0, não coberto pela evidência indireta).
2. Executar `run_channel_sweep.py` com ≥ 30 replicações por $p$ antes de qualquer afirmação sobre perda de pacotes.
3. Rodar a sensibilidade com $\beta$ normalizado (AUD-TCC-014).
4. Corrigir o resumo de comunicação do modo canal (AUD-TCC-006).
5. Atualizar a proveniência das curvas (AUD-TCC-004).
6. Executar `uv run pytest` e registrar o resultado.

## 7. Limitações científicas

Quase-estático; um dia; uma topologia nominal manual; sem replicações; $\beta$ não normalizado; adaptação de Kitso sem decaimento; sem atraso físico; perda i.i.d.; sem *failsafe*; fonte em 1,05 pu.

## 8. Decisões metodológicas relevantes

Decisões D1–D17 de [`implementacao.md`](../implementacao.md) §4, em especial: D5 (sinal da correção), D6 (enlaces de C1/C2), D7 ($\varepsilon$ fixo do grafo nominal), D8 ($\beta$ idêntico), D9 ($V_{\max\text{-}mon}$ na componente do líder), D11 (tolerância 5×10⁻⁴ pu), D13 (rotulagem do grafo pelo $S_i$), D14 (janela de C3 na hora de pico), D15 (exclusão de `sourcebus`). Escopo: camada de falha de comunicação retida no TCC, fora dos Papers 2–4 ([`experimento.md`](../experimento.md) §8).

## 9. Riscos à reprodutibilidade

| Risco | Severidade | Mitigação |
|---|---|---|
| Baseline gerado por commit anterior | Média | Reexecutar e comparar |
| Modo probabilístico com uma semente | Alta (para conclusões estatísticas) | *Sweep* com replicações |
| Repositório grande sem `.gitignore` | Média | `.gitignore`, LFS ou arquivamento |
| Curvas compartilhadas com o CBA sem vínculo declarado | Baixa | Referenciar a planilha de origem |

## 10. Histórico de auditorias

| Data | Responsável | Escopo | Referência |
|---|---|---|---|
| 2026-09-25 | Auditoria técnica — `revisao.md` | Código, resultados, documentação | Checkout `797f18d` |
| 2026-09-25 | Implementação pós-auditoria (registrada na `revisao.md` §7) | Canal, testes, manifesto | `44055ea` → `c434d72` |
| 2026-10-09 | Intervenção de padronização documental (Claude Code, a pedido do autor) | Consolidação e conferência de CSVs | `d70fb55` |
