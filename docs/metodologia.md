# Metodologia — Consenso proporcional sob falhas de comunicação (TCC Facens)

> **Projeto:** [TCC_Facens_Smart_GRID](../README.md) · **Documento canônico** · **Última revisão:** 2026-10-09
> **Commit de referência da intervenção documental:** `d70fb55`
> **Fontes consolidadas:** [`README.md`](../README.md) original (§§0.2–0.6, 3, 4.2, 7), [`experimento.md`](../experimento.md) (§§4–6), [`implementacao.md`](../implementacao.md) (§§1–7, 9), [`revisao.md`](../revisao.md) (§7), código, [`pyproject.toml`](../pyproject.toml), manifestos em `Resultados/*/manifest.json`.

## 1. Desenho experimental

Três camadas (README original): (1) **sem controle**; (2) **com controle, sem perda** (C0); (3) **com controle, com falha**. Dois modos:

| Modo | Camada 3 | Pasta de referência |
|---|---|---|
| **Determinístico (baseline)** | Remoção de enlace (C1, C2) ou isolamento temporário de agente (C3) | `Resultados/FASE0_EXP001/` |
| **Probabilístico** (`--enable-channel`) | Perda por mensagem e atraso sobre a topologia nominal (`C0_perda_<p>`); C1–C3 continuam determinísticos, sem canal | `Resultados/FASE0_EXP001_CHANNEL_MULTI3/`, `…_CHANNEL_TEST/` |

Matriz do baseline: 2 arquiteturas × 7 cenários = 14 casos + sem controle.

## 2. Ambiente computacional

| Item | Valor |
|---|---|
| Python | ≥ 3.13 (`pyproject.toml`); execuções registradas com 3.13.15 |
| AltDSS | 0.2.4 (manifestos) |
| Dependências | altdss, matplotlib, networkx, numpy, pandas, pyyaml; dev: pytest, ruff |
| Gerenciador | `uv` (`uv.lock`); entry point `tcc-facens` |

## 3. Sistema elétrico modelado

- [`IEEE34bus/ieee34Mod3ORIGINAL_CBA.dss`](../IEEE34bus/ieee34Mod3ORIGINAL_CBA.dss): mesma rede do CBA (fonte 1,05 pu, reguladores sem controle); difere só em fins de linha CRLF. O `Redirect IEEELineCodes.dss` é corrigido **em memória** para o nome real `IEEELineCodes.DSS` (D1); o `.dss` não é modificado.
- Carga: `LoadMult = 1,1 × carregamento_pu(t)`; modo *SnapShot* com tempo controlado pelo Python (D3).
- `Vmax` da rede e contagem de violações **excluem `sourcebus`** (D15); subtensão contada com 0,95 pu (D16).

## 4. Agentes e dispositivos

Seis `PVSystem` (24,9 kV; FP = 1; *curtailment* por limite de `kVA`; `pctCutIn = pctCutOut = 0`), potências do cenário 2 do CBA. Ordem no grafo definida após o caso sem controle (líder na posição 1, menor $S_i$ na posição 6):

| Posição no grafo | Agente | Barra | Potência (kVA) | $S_i$ (pu·h) | Papel |
|---|---|---|---|---|---|
| 1 | PV2 | 816 | 125 | 0,07204 | **Líder** ($\arg\max S_i$) |
| 2 | PV1 | 824 | 150 | 0,06973 | — |
| 3 | PV3 | 828 | 100 | 0,06908 | — |
| 4 | PV4 | 830 | 130 | 0,04929 | — |
| 5 | PV5 | 850 | 90 | 0,07203 | — |
| 6 | PV6 | 832 | 115 | 0,01730 | Contraste ($\arg\min S_i$) |

> Nota: 816 vence 850 por 1,2×10⁻⁵ pu·h; com outras curvas, o líder pode mudar ([`implementacao.md`](../implementacao.md) §11).

## 5. Configurações e parâmetros

Constantes em `Experimento_Consenso_comunication_failure.py` (l. 58–139, 416–419):

| Parâmetro | Valor |
|---|---|
| `TENSAO_LIMITE_PU` | 1,05 |
| `TOLERANCIA_DE_TENSAO_PU` | 5×10⁻⁴ (decisão do pesquisador, D11) |
| `TOLERANCIA_DE_CONSENSO` | 10⁻⁶ |
| `NUMERO_MAXIMO_DE_ITERACOES` ($k_{max}$) | 500 |
| `GANHO_DE_CORRECAO_DE_TENSAO` ($\beta$) | 5,0 |
| $\varepsilon$ | 2/tr(L₀) = 1/6 |
| `MULTIPLICADOR_BASE_DE_CARGA` | 1,1 |
| `DURACAO_DO_PASSO_HORAS` | 1,0 (24 *snapshots*) |
| `ITERACAO_DE_RETORNO_FALHA_CURTA` | 20 |
| `ITERACAO_DE_RETORNO_FALHA_LONGA` | $k_{max}$ |
| `PERIODO_DO_CICLO_DE_COMUNICACAO_S` | 0,2 (apenas rótulo de log) |
| `ENLACES_DO_GRAFO_NOMINAL` | (0,1), (1,2), (2,3), (3,4), (4,5), (1,4) — índices 0-based |

Curvas de entrada: [`Entradas/curvas_24h.csv`](../Entradas/curvas_24h.csv) (`hora`, `carregamento_pu`, `curva_pv_kw`); irradiância = `curva_pv_kw / 120` (D2).

> **Verificado em 2026-10-09:** os 24 valores de `curva_pv_kw` e `carregamento_pu` são **idênticos** às abas `CurvasPV` e `LoadShape48_Cargas` de [`CBA/CBA/CurvaPV_24pontos_CBA.xls`](../../CBA/CBA/CurvaPV_24pontos_CBA.xls). O TCC registra o arquivo como indisponível e as curvas como "de exemplo" (AUD-TCC-004). Diferença de uso: aqui, 24 pontos horários; no CBA, reamostradas para 48.

## 6. Cenários experimentais

| Cenário | Falha | Topologia | $\lambda_2$ | Hipóteses |
|---|---|---|---|---|
| C0 | Nenhuma | Conexa | 0,6571 | Baseline |
| C1 | Perda permanente do atalho (2,5) | Conexa | 0,2679 | H1, H2 |
| C2 | Perda permanente de (1,2): líder isolado | Desconexa | 0 | H4, H5 |
| C3_lider_curta | Líder isolado na hora de pico (10 h), retorno em $k = 20$ | Conjuntamente conexa | 0 durante a falha | H4′, H5a |
| C3_lider_longa | Líder isolado na hora de pico até $k_{max}$ | Desconexa na hora | 0 | H5, H5a |
| C3_naolider_curta | Nó 6 (832) isolado, retorno em $k = 20$ | Conjuntamente conexa | 0 durante a falha | H4′, H5a |
| C3_naolider_longa | Nó 6 isolado até $k_{max}$ | Desconexa na hora | 0 | H5a |
| C0_perda_<p> | Perda probabilística $p$ por mensagem, atraso $d$ (modo canal) | Nominal | 0,6571 | Extensão |

C4 (perda probabilística como cenário do baseline com Monte Carlo) foi formalizado em [`experimento.md`](../experimento.md) §4.6 e mantido fora do baseline; a perda probabilística foi implementada depois como modo separado (pós-auditoria).

## 7. Métodos comparados

Sem controle × Leader-Follower × Leaderless (mesma mistura, correções diferentes).

## 8. Procedimento de execução

```bash
uv sync
uv run python Experimento_Consenso_comunication_failure.py              # baseline determinístico (~20 s)
uv run tcc-facens                                                       # equivalente (entry point)

# Modo probabilístico (pasta separada)
uv run python Experimento_Consenso_comunication_failure.py --enable-channel \
  --loss-probability 0.05,0.1,0.2 --delay-steps 1 --seed 42 \
  --output-dir Resultados/FASE0_EXP001_CHANNEL

# Replicações com sementes consecutivas
uv run python scripts/run_channel_sweep.py --replications 30 \
  --loss-probability 0.05 --delay-steps 1 --seed 42 --output-dir Resultados/SWEEP_005PCT_1STEP

uv run pytest
```

Parâmetros do canal: `--loss-probability` ∈ [0, 1] (lista separada por vírgula; 0 sempre incluído como C0), `--delay-steps` ≥ 0, `--seed` (opcional; sem ele, a execução não é repetível), `--output-dir`. O *sweep* grava `replicacao_###/`, `replicacoes_brutas.csv` e `resumo_estatistico.csv` na pasta informada.

Guia didático completo (instalação do `uv` e do Git, mensagens, semente, abordagem estatística): [`guia_didatico.md`](guia_didatico.md), transcrito do README original.

> NÃO VERIFICADO: comandos não reexecutados nesta intervenção.

### Saídas (por pasta de execução)

`config.yaml`, `manifest.json` (versões, commit, data, $\lambda_2$ e *hash* da adjacência por cenário, $S_i$, líder, hora de pico, validações; no modo canal, configuração do canal e *hashes* de entradas); `raw/` (`timestep.csv`, `consensus_iterations.csv`, `tensoes_todas_barras.csv`, `log_comunicacao.csv`, `log_mensagens.csv`, `channel_messages.csv` no modo canal); `summary/` (convergência, $\sigma_r$, tensão, violações por hora, *curtailment* por PV, comunicação por hora e por caso); `tables/resumo_completo.csv`; `matrizes/<arquitetura>__<cenário>/`; `logs/comunicacao_<arquitetura>_<cenário>.log` (estilo GOOSE/DNP3, `stNum`/`sqNum`); `figures/00–17`.

## 9. Indicadores e métricas

Ver [problema_hipoteses.md §8](problema_hipoteses.md#8-variáveis-e-métricas-associadas). No modo canal, os contadores reais de perda estão em `raw/timestep.csv` (`mensagens_do_canal_*`) e `raw/channel_messages.csv`.

## 10. Procedimentos de validação

Validações embutidas (todas passaram no baseline — [`implementacao.md`](../implementacao.md) §8.3): $P_{gerada} \le P_{disp}$; balanço de energia (2,84×10⁻¹⁴ kW); tensões finitas e < 2 pu; $\lambda_2$ esperado por construção; correção não nula só no líder (LF); mesma $P_{disp}$ em todos os casos (tol. 0,015 kW); casos em $k_{max}$ marcados `nao_convergiu`.

Testes ([`tests/test_experiment_structure.py`](../tests/test_experiment_structure.py), 8 funções): C2 isola o líder; C3 retorna na iteração programada; mistura preserva intervalo; canal preserva última mensagem válida; perda determinística por semente; registro de entrega e fila; mistura usa estado recebido; agregador de replicações.

## 11. Reprodutibilidade

| Execução | Data (manifesto) | Commit no manifesto | Commit que versionou os resultados |
|---|---|---|---|
| `FASE0_EXP001` | 2026-09-24T01:13 | `7219216` | `95ddcb3` |
| `FASE0_EXP001_CHANNEL_TEST` ($p$ = 0,05; $d$ = 1; semente 42) | 2026-09-25T14:29Z | `44055ea` | `77ea8eb` |
| `FASE0_EXP001_CHANNEL_MULTI3` ($p$ ∈ {0,05; 0,10; 0,20}; $d$ = 1; semente 42) | 2026-09-25T15:25Z | `b728e4c` | `c434d72` |

Resultados **versionados no Git** (455 arquivos, ≈ 271 MB nas três pastas). Não há `.gitignore` no repositório. O baseline `FASE0_EXP001` não foi reexecutado após as alterações de código da auditoria (AUD-TCC-002).

## 12. Limitações metodológicas

Um dia (curvas do CBA, 24 pontos); um alimentador; uma topologia nominal manual; sem replicações no baseline; $\beta$ não normalizado entre arquiteturas; tolerância de 5×10⁻⁴ pu (reduz ≈ 2 p.p. de corte em relação a 10⁻⁶); barras a montante acima de 1,05 pu com controle (fonte em 1,05 pu); subtensão em horário de ponta fora do escopo.
