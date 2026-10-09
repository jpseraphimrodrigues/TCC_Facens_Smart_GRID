# Resultados e Discussão — Consenso proporcional sob falhas de comunicação (TCC Facens)

> **Projeto:** [TCC_Facens_Smart_GRID](../README.md) · **Documento canônico** · **Última revisão:** 2026-10-09
> **Commit de referência da intervenção documental:** `d70fb55`
> **Fontes consolidadas:** [`implementacao.md`](../implementacao.md) (§§6, 8, 10–11), [`revisao.md`](../revisao.md) (§§2, 4, 7), [`README.md`](../README.md) original (§6), `Resultados/*/tables/resumo_completo.csv`, `summary/*.csv`, `raw/timestep.csv` (lidos nesta auditoria, não alterados).
>
> Convenção: **FATO** = registrado em artefato identificado; **INFERÊNCIA** = interpretação sustentada; **HIPÓTESE** = não demonstrada.

## 1. Resumo dos experimentos executados

| Execução | Conteúdo | Situação |
|---|---|---|
| `FASE0_EXP001` | Baseline determinístico: sem controle + 14 casos | Números de [`implementacao.md`](../implementacao.md) §8.4 **conferidos** com `tables/resumo_completo.csv` |
| `FASE0_EXP001_CHANNEL_TEST` | Canal: $p$ = 0,05; $d$ = 1; semente 42 | Citado em [`revisao.md`](../revisao.md) §7 |
| `FASE0_EXP001_CHANNEL_MULTI3` | Canal: $p$ ∈ {0,05; 0,10; 0,20}; $d$ = 1; semente 42 | **Sem análise documentada**; resumo abaixo calculado nesta auditoria |
| *Sweep* com replicações | — | **NÃO DISPONÍVEL** (nenhuma pasta `SWEEP_*`) |

## 2. Identificação dos cenários

Ver [metodologia §6](metodologia.md#6-cenários-experimentais). Hora de pico de sobretensão (falha de C3): 10 h ($V_{\max}$ PV = 1,0651 pu).

## 3. Resultados quantitativos

### 3.1. Caso sem controle

**FATO:** 8 horas (7 h–14 h) com violação nas barras com PV; $V_{\max}$ = 1,0651 pu; energia disponível 4573,6 kWh; 170 barras-hora com sobretensão na rede (`sourcebus` excluída); 85 barras-hora com subtensão (< 0,95 pu) em todos os casos.

### 3.2. Baseline determinístico (`FASE0_EXP001`)

**FATO (conferido):**

| Arquitetura | Cenário | $V_{\max}$ PV dia (pu) | Horas c/ violação PV | Corte (%) | $\sigma_r$ diário | Iter. na hora de pico | Status no pico |
|---|---|---:|---:|---:|---:|---:|---|
| LF | C0 | 1,0505 | 0 | 41,64 | 0,0076 | 163 | convergiu |
| LF | C1 | 1,0505 | 0 | 41,65 | 0,0192 | 167 | convergiu |
| LF | **C2** | **1,0609** | **8** | 16,51 | **0,3494** | 500 | **nao_convergiu** |
| LF | C3_lider_curta | 1,0505 | 0 | 41,63 | 0,0076 | 167 | convergiu |
| LF | **C3_lider_longa** | **1,0609** | **1** | 35,52 | 0,0628 | 500 | **nao_convergiu** |
| LF | C3_naolider_curta | 1,0505 | 0 | 41,64 | 0,0076 | 163 | convergiu |
| LF | C3_naolider_longa | 1,0505 | 0 | 41,69 | 0,0425 | 163 | convergiu |
| LL | C0 | 1,0505 | 0 | 41,65 | 0,0066 | 54 | convergiu |
| LL | C1 | 1,0505 | 0 | 41,66 | 0,0165 | 55 | convergiu |
| LL | **C2** | 1,0505 | 0 | 41,73 | **0,1175** | 52 | convergiu |
| LL | C3_lider_curta | 1,0505 | 0 | 41,65 | 0,0067 | 54 | convergiu |
| LL | C3_lider_longa | 1,0505 | 0 | 41,66 | 0,0232 | 52 | convergiu |
| LL | C3_naolider_curta | 1,0505 | 0 | 41,65 | 0,0069 | 54 | convergiu |
| LL | C3_naolider_longa | 1,0505 | 0 | 41,69 | 0,0354 | 52 | convergiu |

- $\sigma_r$ por partição na hora de pico em C2: ≈ 0 nas duas arquiteturas (LF [0,0; 0,0]; LL [0,0; 0,0021]).
- 8 horas-caso `nao_convergiu`: 7 no LF-C2 e 1 no LF-C3_lider_longa (hora 10).
- $V_{\max}$ da rede com controle: 1,0508 pu (barras 800, 802, 806, 808, 812, 812r acima de 1,05 pu em 1–6 barras por hora).

*Curtailment* diário por PV (%), casos-chave:

| Arquitetura | Cenário | 816 (líder) | 824 | 828 | 830 | 850 | 832 |
|---|---|---:|---:|---:|---:|---:|---:|
| LF | C0 | 43,2 | 41,8 | 41,4 | 41,1 | 41,2 | 40,9 |
| LF | C2 | 93,8 | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| LF | C3_lider_longa | 49,4 | 33,0 | 32,6 | 32,4 | 32,5 | 32,2 |
| LL | C0 | 43,0 | 41,8 | 41,2 | 41,1 | 41,6 | 41,0 |
| LL | C2 | 67,7 | 36,1 | 35,9 | 36,1 | 36,5 | 36,3 |
| LL | C3_lider_longa | 46,8 | 40,9 | 40,4 | 40,4 | 40,8 | 40,3 |

Barras-hora com sobretensão na rede: sem controle 170; LF-C0 50; LF-C2 145; LF-C3_lider_longa 73; LL (todos) 50–51.

Comunicação (topológica; `summary/comunicacao_por_caso.csv`): perda estrutural de 16,67% das mensagens em C1 e C2 (1 de 6 enlaces); maior idade da informação 500 iterações no LF-C2.

### 3.3. Modo probabilístico (`FASE0_EXP001_CHANNEL_MULTI3`)

> NÃO VALIDADO: uma única semente (42), sem replicações; resumo calculado nesta auditoria.

**FATO (`tables/resumo_completo.csv`; `raw/timestep.csv`):**

| Arq. | Cenário | Msgs tentadas | Perdidas (canal) | Perda efetiva | Iter. no dia | Iter. no pico | Corte (%) | $\sigma_r$ | Horas c/ violação |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LF | C0 (canal, $p$ = 0) | 23 508 | 0 | 0,0% | 1959 | 220 | 41,633 | 0,0074 | 0 |
| LF | C0_perda_0.05 | 23 832 | 1164 | 4,9% | 1986 | 223 | 41,633 | 0,0074 | 0 |
| LF | C0_perda_0.10 | 24 156 | 2362 | 9,8% | 2013 | 226 | 41,627 | 0,0074 | 0 |
| LF | C0_perda_0.20 | 24 996 | 4955 | 19,8% | 2083 | 235 | 41,625 | 0,0074 | 0 |
| LL | C0 (canal, $p$ = 0) | 8 604 | 0 | 0,0% | 717 | 73 | 41,653 | 0,0061 | 0 |
| LL | C0_perda_0.05 | 8 712 | 429 | 4,9% | 726 | 74 | 41,645 | 0,0061 | 0 |
| LL | C0_perda_0.10 | 8 820 | 891 | 10,1% | 735 | 75 | 41,630 | 0,0062 | 0 |
| LL | C0_perda_0.20 | 9 156 | 1854 | 20,2% | 763 | 79 | 41,643 | 0,0061 | 0 |

- O C0 via canal ($p$ = 0, $d$ = 1) já exige mais iterações que o C0 do baseline (LF 1959 × 1457; LL 717 × 530): o **atraso de uma iteração**, sozinho, aumenta o esforço.
- C1–C3 nesta pasta são idênticos aos do baseline (determinísticos, sem canal).

**FATO (`FASE0_EXP001_CHANNEL_TEST`, LF/C0/hora 10, segundo [`revisao.md`](../revisao.md) §7):** 2676 mensagens tentadas, 2533 entregues, 131 perdidas, 12 pendentes.

## 4. Tabelas e figuras

`Resultados/FASE0_EXP001/figures/`: 00 curvas de entrada; 01 IEEE 34 com PVs e líder; 02 grafo em C0–C3 com $\lambda_2$; 03 $e_c(k)$ no pico; 04 $V_{\max}$ das barras PV; 05 *curtailment* por agente; **06 margem de H3** ($\sigma_r$ × $V_{\max}$); **07 H5 particionamento**; **08 H5a falha do líder**; 09–17 complementares (potências, $\rho_i$, tensões, violações, iterações, mapas de calor, linha do tempo da comunicação, perda por hora, $\rho_i(k)$ no pico).

## 5. Comparação entre métodos

| Critério | Leader-Follower | Leaderless |
|---|---|---|
| C0: regulação e corte | 1,0505 pu; 41,64% | 1,0505 pu; 41,65% |
| C0: iterações no pico | 163 | 54 |
| C2 (líder isolado) | Falha: 8 h com violação; corte só no líder (93,8%) | Regula; perde proporcionalidade (816: 67,7%; demais ≈ 36%) |
| Falha longa do líder | Violação na hora de pico | Sem efeito em $V_{\max}$ |
| Perda probabilística até 20% ($d$ = 1) | Sem violação; +6,3% de iterações no dia | Sem violação; +6,4% de iterações no dia |

## 6. Interpretação dos resultados

- **INFERÊNCIA:** H1 se sustenta com efeito pequeno (C1 reduz $\lambda_2$ de 0,657 para 0,268, aumenta levemente iterações e $\sigma_r$, sem efeito elétrico).
- **INFERÊNCIA:** em C2, consenso local (por partição) coexiste com desigualdade global alta.
- **INFERÊNCIA:** existe folga elétrica: LL-C2 tem $\sigma_r$ ≈ 18× o C0 sem violação nas barras PV; o LL amplia essa região (fig. 06).
- **INFERÊNCIA:** em LF, a partição sem líder perde toda correção; em LL a correção local persiste. Partição de comunicação não é partição elétrica (o líder isolado não reduz a própria tensão porque 816, 850 e 824 são vizinhas).
- **INFERÊNCIA com ressalva:** o LL converge em ≈ 1/3 das iterações do LF, mas com $\beta$ idêntico ele tem até 6 termos de correção ativos (confundimento arquitetura × número de atuadores).
- **INFERÊNCIA (modo canal):** perdas i.i.d. de até 20% com atraso de 1 iteração, sobre topologia nominal, não afetam a regulação neste caso; o custo aparece em iterações. **HIPÓTESE:** a robustez decorre da política de "última mensagem válida" e da redundância do grafo; não testado contra perda em rajada ou atraso maior.

## 7. Avaliação das hipóteses

| Hipótese | Avaliação | Evidência |
|---|---|---|
| H1 | **Sustentada (efeito pequeno)** | C0 → C1: iterações 1457 → 1481 (LF), $\sigma_r$ 0,0076 → 0,0192 |
| H2 | **Sustentada** | $\sigma_r$ global LF-C2 0,349; LL-C2 0,118; por partição ≈ 0 |
| H3 | **Sustentada no caso** | LL-C2 e LF-C3_naolider_longa sem violação com $\sigma_r$ elevado |
| H4 / H4′ | **Sustentadas** | $\lambda_2$ = 0 em C2/C3; falha curta ≈ C0 (41,63% × 41,64%) |
| H5 | **Sustentada no caso** | LF-C2 8 h de violação; LL-C2 nenhuma |
| H5a | **Sustentada no caso** | LF líder longa: 1,0609 pu; não líder longa: 1,0505 pu; LL invariante |

Todas as avaliações valem para **uma execução determinística**, curvas do CBA, $\beta$ idêntico e tolerância de 5×10⁻⁴ pu.

## 8. Limitações dos resultados

- Sem replicações (baseline determinístico; modo canal com uma semente).
- Baseline não reexecutado no código atual (AUD-TCC-002).
- `summary/comunicacao_por_caso.csv` reporta 0% de perda nos cenários `C0_perda_*` (conta o log topológico, não o canal) — usar `raw/timestep.csv` (AUD-TCC-006).
- "Zero violações nas barras com PV" ≠ "zero violações na rede" (barras a montante até 1,0508 pu).
- Confundimento de $\beta$; adaptação não fiel de Kitso; líder decidido por margem de 1,2×10⁻⁵ pu·h.

## 9. Conclusões parciais

Conclusões permitidas ([`revisao.md`](../revisao.md) §4): C0/C1 permanecem controláveis; particionar o líder degrada o LF; o LL mantém o controle em C2; o controle reduz 1,0651 pu para ≈ 1,0505 pu nos casos bem-sucedidos. Evitar: "robusto a perda de pacotes" (sem replicações), "atraso de 0,2 s", "LL superior em geral", "modelo IEC 61850 real".

## 10. Trabalhos futuros

Replicações (`run_channel_sweep.py`, ≥ 30 por $p$); varrer perda, atraso, duração e hora da falha; $\beta$ normalizado (sensibilidade); decaimento de Kitso; perda em rajada (Gilbert-Elliott); TAL e *failsafe* Volt-Watt (IEC 61850/IEEE 1547); consenso ponderado por $\partial V/\partial P$ (hipóteses A–C de sensibilidade); outras topologias e alimentadores.
