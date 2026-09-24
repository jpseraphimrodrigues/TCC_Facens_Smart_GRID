# Implementação — Fase 0: Consenso proporcional sob falha de comunicação (Leader-Follower × Leaderless)

> Registro do que foi implementado a partir de `experimento.md`, das decisões tomadas durante a implementação e das evidências de execução. Fonte de verdade do desenho experimental continua sendo `experimento.md`; este documento registra **como** ele foi materializado em código e **o que** a primeira execução produziu.
>
> Execução de referência deste documento: `Resultados/FASE0_EXP001/manifest.json` (Python 3.13.15, AltDSS 0.2.4, commit registrado no momento da execução: `7219216`).

---

## 1. Escopo implementado

| Item | Situação |
|---|---|
| Arquivo único `Experimento_Consenso_comunication_failure.py` (§4.1) | implementado (~2500 linhas, estilo didático — §4.1.1) |
| Alimentador `ieee34Mod3ORIGINAL_CBA.dss` + 6 `PVSystem` (§4.2, §4.2.1) | implementado |
| Caso sem controle → `S_i` → líder por Critério B (§4.4.1) | implementado |
| Grafo "linha com atalho" rotulado após o caso sem controle (§4.3, checklist item 4) | implementado |
| Arquiteturas Leader-Follower e Leaderless com interface comum de correção (§4.4–4.5) | implementado |
| Cenários C0, C1, C2, C3 (m = líder / m ≠ líder × falha curta / longa) (§4.6, §7.1) | implementado — 7 cenários × 2 arquiteturas = 14 casos + sem controle |
| C4 / Monte Carlo (§7.4, §5.4) | **fora de escopo** (decisão já registrada) |
| Critério de parada elétrico (§4.7) | implementado |
| Métricas `e_c`, `N_iter`, `σ_r` global e por partição, `Vmax`, violações, `λ₂` | implementado |
| Validações de §6 | implementado (todas passam) |
| Saídas de §5.5 (config, manifest, raw, summary, figuras 01–08) | implementado |
| Log de comunicação por mensagem (estilo GOOSE / DNP3) | implementado (pedido adicional) |
| Tabelas e figuras extras inspiradas no código de referência do grupo | implementado (figuras 00, 09–17; CSVs de violação por barra/fase, matrizes hora × barra) |

---

## 2. Como executar

```bash
uv sync          # dependências: altdss, numpy, pandas, matplotlib, networkx, pyyaml
uv run python Experimento_Consenso_comunication_failure.py
```

Tempo de execução observado: ~20 s. Todas as saídas vão para `Resultados/FASE0_EXP001/`.

Para trocar as curvas diárias, editar `Entradas/curvas_24h.csv` (colunas `hora`, `carregamento_pu`, `curva_pv_kw`) — o código sempre lê desse arquivo quando ele existe.

---

## 3. Arquivos criados ou alterados

| Arquivo | O que é |
|---|---|
| `Experimento_Consenso_comunication_failure.py` | o experimento completo (arquivo único) |
| `Entradas/curvas_24h.csv` | curvas de exemplo fornecidas pelo pesquisador (carga em pu; PV em kW) |
| `pyproject.toml`, `uv.lock` | dependências adicionadas via `uv add` |
| `Resultados/FASE0_EXP001/**` | saídas da execução (seção 7) |
| `implementacao.md` | este documento |

O arquivo `.dss` original **não foi modificado** (ver D1 abaixo).

---

## 4. Decisões de implementação

Decisões tomadas durante a implementação, com origem e justificativa. As marcadas como **divergência** diferem de algum trecho literal de `experimento.md` e devem ser declaradas no texto do TCC quando pertinente.

| # | Decisão | Origem | Justificativa |
|---|---|---|---|
| D1 | O `.dss` faz `Redirect IEEELineCodes.dss`, mas o arquivo em disco é `IEEELineCodes.DSS`. O caminho é corrigido **em memória** (texto do `.dss` lido, caminhos trocados por absolutos) | implementação | Linux diferencia maiúsculas; a skill proíbe sobrescrever a rede base |
| D2 | Curvas diárias = curvas de exemplo do pesquisador; irradiância (pu) = `curva_pv_kw / pico` (pico = 120 kW) | pesquisador | `CurvaPV_24pontos_CBA.xls` não está no repositório (§7.7). Normalizar pelo pico faz cada PV gerar `Pmpp_i × irradiância`: mesmo formato, escalado pela própria potência |
| D3 | Carga horária aplicada como `LoadMult = 1,1 × carregamento_pu(t)`; tempo controlado pelo Python em modo SnapShot | §7.7 + skill | Mantém o `LoadMult = 1,1` do código de referência; a skill admite escrever os multiplicadores explicitamente a cada hora |
| D4 | Curtailment via limitação de `kVA` do `PVSystem`, FP = 1, `pctCutIn = pctCutOut = 0` | §4.2.1, §7.7 | Continuidade com o código de referência. Testado: `kVA = 60` → 60 kW; `kVA = 0` → 0 kW, fluxo converge |
| D5 | **Divergência de notação:** `ρ_i` = fração de **curtailment**; a correção `c_i ≥ 0` é **somada**: `ρ(k+1) = clip[ρ + ε Σ a_ij(ρ_j − ρ_i) + c_i, 0, 1]` | §2.1 × §4.5 | O "− c_i" de §4.5 mistura a convenção do paper-âncora (`β_i` = fração **injetada**). Com `β = 1 − ρ` as duas formas têm dinâmica idêntica (a mistura é linear) |
| D6 | **Divergência:** C1 remove a aresta (2,5); C2 remove (1,2) | §4.3 × §4.6 | A tabela de §4.6 cita (2,4)/(2,3), resquício da versão com 5 agentes — (2,4) nem existe em `E_0`. §4.3 é a definição vigente |
| D7 | `ε = 2/tr(L₀) = 0,1667`, calculado uma vez no grafo nominal e fixo em todos os cenários | §4.5, opção (a) | Clareza causal: a falha altera só o grafo, não o passo. Diverge do código de referência (que recalcula `ε`) — declarar no TCC |
| D8 | `β = 5` idêntico nas duas arquiteturas | §7.5, opção primária; §7.6 | Ganho do código de referência; sem normalização por número de atuadores |
| D9 | `V_max-mon` do LF = máximo das barras com PV **na componente conexa do líder** em `A(k)` | §7.3 | O líder só reage ao que consegue observar pela rede de comunicação |
| D10 | Critério de parada: tensão vista pelo controle ≤ `V_lim + tol`, ou `k = k_max = 500`. No Leaderless, a "tensão vista" é o máximo das tensões **locais** (cada agente decide pela sua; o laço síncrono termina quando todos estão satisfeitos) | §4.7 | — |
| D11 | **Tolerância `tol = 5×10⁻⁴ pu`** (tudo que arredonda para 1,050 pu é aceito) | pesquisador | Com `10⁻⁶` (valor do código de referência), a aproximação a 1,05 pu é assintótica no grafo esparso e 53 horas-caso terminavam em 1,050001–1,0001 pu marcadas como `nao_convergiu` (ver seção 9) |
| D12 | Violação **real** registrada separadamente do status do controle (`violacao_real_apos_controle`) | H2, H5 | Sob falha, o líder pode "achar" que resolveu (sua componente está abaixo do limite) enquanto outra partição viola |
| D13 | Líder por Critério B (`argmax S_i`); posição 1 do grafo = líder; posição 6 = agente de menor `S_i` (o "m ≠ líder" de C3); posições 2–5 na ordem do código de referência | §4.4.1, §7.6 | — |
| D14 | C3: falha só na **hora de pico** do caso sem controle, a partir de `k = 0`; duração curta (retorno em `k = 20`) e longa (hora inteira, `k_max`) | §7.1 — decidido com o pesquisador | Permite ver H4′ (recuperação) e o pior caso de H5a |
| D15 | `Vmax` da rede e contagem de violações **excluem `sourcebus`** | implementação | É a fonte ideal fixada em 1,05 pu no `.dss`; incluí-la tornaria `Vmax ≥ 1,05` sempre |
| D16 | Subtensão contada com `V_min = 0,95 pu` (só relatório) | código de referência (`VMIN_VIOL`) | — |
| D17 | Tolerância da checagem "mesma `P_disponível` em todos os casos" = `10⁻⁴ × 150 kVA = 0,015 kW` | implementação | O `SolveSnap` parte do estado da hora anterior (que difere entre cenários); a diferença observada (5 W em 150 kW) é da ordem da tolerância do solver, não vazamento de estado |

---

## 5. Organização do código

O arquivo é dividido em blocos `# ====` (§4.1):

| Bloco | Conteúdo principal |
|---|---|
| CONFIGURAÇÃO | constantes do experimento (tudo que é mantido idêntico entre casos) |
| ENTRADAS | leitura/criação de `Entradas/curvas_24h.csv`, normalização da curva PV |
| ELÉTRICO | `construir_circuito_com_pvs` (Clear + compile por caso), `aplicar_perfil_da_hora`, medições, `aplicar_curtailment_nos_pvs`, `medir_estado_de_todas_as_barras` |
| COMUNICAÇÃO | matriz A, Laplaciana, `λ₂`, `ε`, componentes conexas, classe `GrafoDeComunicacao` (A(k) por hora e iteração), `definir_cenarios_de_falha` |
| LOG DA COMUNICAÇÃO | classe `RegistradorDeComunicacao` (seção 6) |
| CONTROLE | `misturar_por_consenso` (idêntica nas duas arquiteturas), `corrigir_leader_follower`, `corrigir_leaderless` — **as duas únicas funções que diferem** —, critério de parada |
| MÉTRICAS | `e_c`, `σ_r` global e por partição, `S_i`, escolha do líder, rotulagem do grafo |
| SIMULAÇÃO | `simular_dia_sem_controle`, `executar_consenso_na_hora` (o tempo não avança dentro do laço), `simular_dia_com_consenso` |
| RESUMOS / VALIDAÇÃO | resumo por caso; checklist de §6 |
| RESULTADOS | tabelas extras, matrizes hora × barra, 18 figuras, `config.yaml`, `manifest.json` |

---

## 6. Log de comunicação (estilo GOOSE / DNP3)

Cada caso gera um log por **mensagem**: quem enviou para quem, o conteúdo, o instante e o que aconteceu com ela.

- **Conteúdo** de cada mensagem: `ρ_i(k)` (o estado misturado pelo consenso) e `V_i(k)` (tensão local, que permite ao líder do LF calcular `V_max-mon`, §7.3).
- **stNum / sqNum** com a semântica do GOOSE: `stNum` sobe quando o conteúdo publicado muda (e `sqNum` volta a 0); conteúdo repetido só incrementa `sqNum`. Um `sqNum` crescendo indica agente estabilizado ou saturado, só retransmitindo.
- **Dois timestamps**: relógio real (quando a linha foi escrita) e instante **simulado** `HH:MM:SS.mmm` = hora + `k × 0,2 s`. O período de 0,2 s (resolução τ de Wang et al., 2023 — R7) é **apenas rótulo**: nenhum atraso é modelado (Fase 0 §18).
- **Motivo da perda**: `enlace (i,j) fora (falha permanente)` em C1/C2; `agente X isolado (falha temporária C3)` em C3.
- **"Lag" sem atraso modelado** aparece como latência estrutural: saltos até o líder (mínimo de iterações para a correção do líder alcançar cada agente; `∞` se inalcançável) e idade da informação (iterações sem receber mensagem).
- **Eventos** de mudança da rede (enlace caiu/voltou) são registrados **antes** das mensagens da iteração e também impressos no terminal, junto com um resumo por hora.

**Evidência** — `logs/comunicacao_leader_follower_C3_lider_curta.log`, reconexão do líder na hora de pico:

```text
[t_sim=10:00:03.800 k=019] MSG #0008545 1(816) -> 2(824) stNum=710 sqNum=3 | rho=1.000000 V=1.060550 pu | PERDIDA (agente 1(816) isolado (falha temporária C3))
[t_sim=10:00:03.800 k=019] MSG #0008547 2(824) -> 3(828) stNum=710 sqNum=3 | rho=0.000000 V=1.060852 pu | ENTREGUE
[t_sim=10:00:03.800 k=019] enlaces 5/6 | perdidos: (1,2) | isolados: 1(816) | partições: {1} {2,3,4,5,6} | λ2=0.000 | msgs 10 enviadas, 2 perdidas | saltos até o líder 1:0 2:∞ 3:∞ 4:∞ 5:∞ 6:∞ | ...
[t_sim=10:00:04.000 k=020] EVENTO RECUPERAÇÃO: voltou(voltaram) (1,2) -> enlaces 6/6 | perdidos: - | isolados: - | partições: {1,2,3,4,5,6} | λ2=0.657
[t_sim=10:00:04.000 k=020] MSG #0008557 1(816) -> 2(824) stNum=710 sqNum=4 | rho=1.000000 V=1.060550 pu | ENTREGUE
```

Leitura: durante a falha o líder satura em `ρ = 1` (conteúdo repetido → `sqNum` sobe) e os seguidores, sem correção, publicam `ρ = 0`. Em `k = 20` o enlace volta e a informação do líder passa a chegar.

**Resumo da comunicação por caso** (`summary/comunicacao_por_caso.csv`, todas as horas com consenso):

| Arquitetura | Cenário | Iterações | Iterações sob falha | Msgs tentadas | Perdidas | Perda (%) | Maior idade da info (it.) |
|---|---|---:|---:|---:|---:|---:|---:|
| LF | C0 | 1457 | 0 | 17 484 | 0 | 0,00 | 0 |
| LF | C1 | 1481 | 1481 | 17 772 | 2 962 | 16,67 | 0 |
| LF | C2 | 3647 | 3647 | 43 764 | 7 294 | 16,67 | 500 |
| LF | C3_lider_curta | 1461 | 20 | 17 532 | 40 | 0,23 | 20 |
| LF | C3_lider_longa | 1794 | 500 | 21 528 | 1 000 | 4,65 | 500 |
| LF | C3_naolider_curta | 1457 | 20 | 17 484 | 40 | 0,23 | 20 |
| LF | C3_naolider_longa | 1457 | 163 | 17 484 | 326 | 1,86 | 163 |
| Leaderless | C0 | 530 | 0 | 6 360 | 0 | 0,00 | 0 |
| Leaderless | C1 | 537 | 537 | 6 444 | 1 074 | 16,67 | 0 |
| Leaderless | C2 | 524 | 524 | 6 288 | 1 048 | 16,67 | 117 |
| Leaderless | C3_lider_curta | 530 | 20 | 6 360 | 40 | 0,63 | 20 |
| Leaderless | C3_lider_longa | 528 | 52 | 6 336 | 104 | 1,64 | 52 |
| Leaderless | C3_naolider_curta | 530 | 20 | 6 360 | 40 | 0,63 | 20 |
| Leaderless | C3_naolider_longa | 528 | 52 | 6 336 | 104 | 1,64 | 52 |

Em C1 e C2 a perda é 1/6 dos enlaces por construção (16,67%). No LF-C2 o número de iterações é muito maior porque o controle nunca atinge o critério de parada (7 horas em `k_max`).

---

## 7. Saídas geradas (`Resultados/FASE0_EXP001/`)

```text
config.yaml                      parâmetros do experimento (inclui as curvas usadas)
manifest.json                    versões, commit, λ2 e hash da adjacência por cenário, S_i, líder, validações
raw/
  timestep.csv                   caso × hora × agente (P disp/gerada/cortada, rho, r_i, V, status, partição)
  consensus_iterations.csv       caso × hora × k (e_c global e intra-partição, λ2, rho_i(k), V_i(k))
  tensoes_todas_barras.csv       caso × hora × barra (Vmax/Vmin por fase, fases violadas)
  log_comunicacao.csv            caso × hora × k (enlaces, partições, msgs, saltos até o líder, idade da info)
  log_mensagens.csv              uma linha por mensagem (origem, destino, stNum, sqNum, conteúdo, situação, motivo)
summary/
  convergencia_por_cenario.csv   sigma_r_por_cenario.csv       tensao_por_cenario.csv
  violacoes_por_hora.csv         nº de barras/fases com sobre/subtensão e QUAIS barras, por hora
  curtailment_por_pv.csv         energia disponível/gerada/cortada por PV
  comunicacao_por_hora.csv       comunicacao_por_caso.csv
tables/resumo_completo.csv
matrizes/<arquitetura>__<cenario>/   (15 pastas)
  tensao_hora_x_barra.csv  sobretensao_hora_x_barra.csv  sobretensao_valor_hora_x_barra.csv
  subtensao_hora_x_barra.csv  potencias_por_pv.csv  tensoes_barras_pv.csv
logs/comunicacao_<arquitetura>_<cenario>.log   (14 arquivos)
figures/00–17 (PNG)
```

| Figura | Conteúdo |
|---|---|
| 00 | curvas de entrada (carga e irradiância) |
| 01 | IEEE 34 barras com os 6 PVs e o líder |
| 02 | grafo de comunicação em C0, C1, C2, C3 (λ₂ de cada) |
| 03 | `e_c(k)` na hora de pico, por arquitetura |
| 04 | `Vmax` das barras com PV ao longo do dia |
| 05 | curtailment diário (%) por agente |
| 06 | margem de H3: `σ_r` × `Vmax` |
| 07 | H5: `Vmax` por partição em C2, LF × Leaderless |
| 08 | H5a: m = líder × m ≠ líder (Vmax, `σ_r`, iterações) |
| 09 | potência disponível × gerada por PV (LF/Leaderless × C0/C2) |
| 10 | `ρ_i` ao fim de cada hora |
| 11 | tensão individual de cada barra com PV |
| 12 | nº de barras da rede com sobretensão por hora |
| 13 | iterações de consenso por hora |
| 14 | mapa de calor hora × barra (sem controle, LF-C2, Leaderless-C2) |
| 15 | linha do tempo da comunicação por agente (alcança o líder / partição sem líder / isolado) |
| 16 | taxa de perda de mensagens por hora |
| 17 | `ρ_i(k)` na hora de pico: C2 e falha curta do líder |

---

## 8. Evidências de execução

### 8.1 Caso sem controle e escolha do líder

Violação acumulada `S_i = Σ_t max(0, V_i(t) − 1,05)·Δt` (pu·h):

| Barra | 824 | **816** | 828 | 830 | 850 | 832 |
|---|---:|---:|---:|---:|---:|---:|
| `S_i` | 0,06973 | **0,07204** | 0,06908 | 0,04929 | 0,07203 | 0,01730 |

- Líder = **816** (pv2). Agente de contraste (posição 6) = **832**. Ordem do grafo (posições 1–6): 816, 824, 828, 830, 850, 832.
- Hora de pico de sobretensão (falha de C3): **10 h**, `Vmax` das barras com PV = 1,0651 pu.
- Sem controle: 8 horas (7 h–14 h) com violação nas barras com PV.

### 8.2 Grafo de comunicação

| Cenário | λ₂ | Observação |
|---|---:|---|
| C0 | 0,657 | conexo |
| C1 | 0,268 | conexo (sem o atalho) |
| C2 | 0,000 | {1} e {2,…,6} — o líder fica isolado (seu único enlace é (1,2)) |
| C3 (durante a falha) | 0,000 | agente m isolado |

`ε = 2/tr(L₀) = 2/12 = 0,1667`.

### 8.3 Validações de §6 (todas passaram)

```text
[OK] P_gerada <= P_disponivel em todo passo            maior excesso = 2.84e-14 kW
[OK] E_disponivel = E_gerada + E_cortada               maior diferenca = 2.84e-14 kW
[OK] Tensoes pu finitas e < 2 pu (sanidade de base)
[OK] lambda_2(C0) > 0                                  0.6571
[OK] lambda_2(C1) > 0                                  0.2679
[OK] lambda_2(C2) = 0                                  0.0000
[OK] LF: correcao nao nula apenas no lider
[OK] Mesma P_disponivel em todos os casos              maior variacao = 5.32e-03 kW (tol. 0.015 kW)
[OK] Casos em k_max marcados como nao_convergiu        8 horas-caso marcadas
```

As 8 horas-caso `nao_convergiu` são falhas reais do controle: 7 no LF-C2 (a hora 14 atinge 1,0504 pu e passa) e 1 no LF-C3_lider_longa (hora 10). Nenhum caso C0/C1 fica em `k_max`.

### 8.4 Resumo por caso

| Arquitetura | Cenário | Vmax PV no dia (pu) | Horas c/ violação PV | Curtailment (%) | σ_r diário | Iter. na hora de pico | Status na hora de pico | σ_r por partição (pico) |
|---|---|---:|---:|---:|---:|---:|---|---|
| sem controle | — | 1,0651 | 8 | 0,00 | — | — | — | — |
| LF | C0 | 1,0505 | 0 | 41,64 | 0,0076 | 163 | convergiu | [0,0083] |
| LF | C1 | 1,0505 | 0 | 41,65 | 0,0192 | 167 | convergiu | [0,0227] |
| LF | **C2** | **1,0609** | **8** | 16,51 | **0,3494** | 500 | **nao_convergiu** | [0,0; 0,0] |
| LF | C3_lider_curta | 1,0505 | 0 | 41,63 | 0,0076 | 167 | convergiu | [0,0084] |
| LF | **C3_lider_longa** | **1,0609** | **1** | 35,52 | 0,0628 | 500 | **nao_convergiu** | [0,3727] |
| LF | C3_naolider_curta | 1,0505 | 0 | 41,64 | 0,0076 | 163 | convergiu | [0,0083] |
| LF | C3_naolider_longa | 1,0505 | 0 | 41,69 | 0,0425 | 163 | convergiu | [0,0076; 0,0] |
| Leaderless | C0 | 1,0505 | 0 | 41,65 | 0,0066 | 54 | convergiu | [0,0077] |
| Leaderless | C1 | 1,0505 | 0 | 41,66 | 0,0165 | 55 | convergiu | [0,0237] |
| Leaderless | **C2** | 1,0505 | 0 | 41,73 | **0,1175** | 52 | convergiu | [0,0; 0,0021] |
| Leaderless | C3_lider_curta | 1,0505 | 0 | 41,65 | 0,0067 | 54 | convergiu | [0,0081] |
| Leaderless | C3_lider_longa | 1,0505 | 0 | 41,66 | 0,0232 | 52 | convergiu | [0,0; 0,0021] |
| Leaderless | C3_naolider_curta | 1,0505 | 0 | 41,65 | 0,0069 | 54 | convergiu | [0,0092] |
| Leaderless | C3_naolider_longa | 1,0505 | 0 | 41,69 | 0,0354 | 52 | convergiu | [0,0066; 0,0] |

Energia disponível no dia: 4 573,6 kWh (idêntica em todos os casos).

### 8.5 Curtailment diário por PV (%) — casos-chave (`summary/curtailment_por_pv.csv`)

| Arquitetura | Cenário | 816 (líder) | 824 | 828 | 830 | 850 | 832 |
|---|---|---:|---:|---:|---:|---:|---:|
| LF | C0 | 43,2 | 41,8 | 41,4 | 41,1 | 41,2 | 40,9 |
| LF | C2 | **93,8** | 0,0 | 0,0 | 0,0 | 0,0 | 0,0 |
| LF | C3_lider_longa | 49,4 | 33,0 | 32,6 | 32,4 | 32,5 | 32,2 |
| Leaderless | C0 | 43,0 | 41,8 | 41,2 | 41,1 | 41,6 | 41,0 |
| Leaderless | C2 | **67,7** | 36,1 | 35,9 | 36,1 | 36,5 | 36,3 |
| Leaderless | C3_lider_longa | 46,8 | 40,9 | 40,4 | 40,4 | 40,8 | 40,3 |

### 8.6 Violações na rede inteira (`summary/violacoes_por_hora.csv`)

Nº de barras da rede com sobretensão a cada hora (0–23), `sourcebus` excluída:

```text
sem_controle     [1,1,1,1,1,2,3,16,29,29,29,16,15,15,11,0,...]  total=170
LF  C0           [1,1,1,1,1,2,3, 6, 6, 6, 6, 3, 3, 4, 6,0,...]  total=50
LF  C2           [1,1,1,1,1,2,3,16,16,29,29,15,11,11, 8,0,...]  total=145
LF  C3_lider_longa [1,1,1,1,1,2,3,6,6,6,29,3,3,4,6,0,...]        total=73
Leaderless C0/C2/C3  ≈ igual ao LF-C0                           total=50–51
```

Barras-hora com subtensão (< 0,95 pu): **85 em todos os casos**, inclusive sem controle (horário de ponta da carga, sem geração FV; o controle não atua sobre subtensão).

---

## 9. Histórico de ajustes (evidência do processo)

| Rodada | Mudança | Efeito observado |
|---|---|---|
| 1 | `tol = 10⁻⁶` (valor do código de referência) | 53 horas-caso `nao_convergiu`, a maioria terminando em 1,050001–1,0001 pu; LF-C0 com "5 horas de violação" que eram artefato da tolerância; 459 iterações na hora de pico (LF-C0). Curtailment LF-C0 = 43,9% (≈ 44,3% do paper-âncora) |
| 1 | checagem de `P_disponível` com tolerância 10⁻³ kW falhou (variação de 5,37×10⁻³ kW) | diagnosticado como tolerância do solver (parte do estado da hora anterior); tolerância da checagem ajustada para 0,015 kW (D17) |
| 2 | `tol = 10⁻⁴` | ainda restavam horas terminando em 1,05011 pu (hora 7, baixa sensibilidade `∂V/∂ρ` com pouca geração) |
| 3 | `tol = 5×10⁻⁴` (decisão do pesquisador: "1,050 já é aceitável") | 8 horas-caso `nao_convergiu`, todas falhas reais; LF-C0 com 163 iterações na hora de pico; curtailment LF-C0 = 41,6% (a tolerância mais folgada reduz ~2 p.p. de curtailment) |
| — | figuras revisadas após inspeção visual | rótulos sobrepostos (fig. 01), título sobre painéis (fig. 02, 15), curvas coincidentes escondidas (tracejado nas falhas longas, fig. 03/04), barras com eixo truncado trocadas por pontos (fig. 08), legenda cobrindo curva (fig. 12) |
| — | motivo de perda de mensagem em C2 | inicialmente rotulado "agente isolado (C3)"; corrigido para "enlace (1,2) fora (falha permanente)" |

---

## 10. Leitura dos resultados frente às hipóteses

Resultados de uma única execução determinística, com curvas de exemplo. Separação FATO / INFERÊNCIA conforme a skill `Executor_altGRID_consenso`.

**Sanidade (C0).** FATO: as duas arquiteturas regulam as barras com PV (Vmax 1,0505 pu) com curtailment ≈ 41,6% e `σ_r` ≈ 0,007 — repartição praticamente proporcional, coerente com o paper-âncora (44,3%).

**H1 — degradação aumenta erro/tempo.** FATO: C1 aumenta levemente as iterações (LF 1457 → 1481; Leaderless 530 → 537) e `σ_r` diário (LF 0,0076 → 0,0192; Leaderless 0,0066 → 0,0165). INFERÊNCIA: H1 se sustenta, com efeito pequeno — perder o atalho reduz λ₂ de 0,657 para 0,268 mas não muda o resultado elétrico.

**H2 — distorção do esforço.** FATO: em C2, `σ_r` por partição é ≈ 0 em ambas as arquiteturas, enquanto `σ_r` global é alto (LF 0,349; Leaderless 0,118). INFERÊNCIA: confirma a predição de §3 — consenso local baixo coexistindo com desigualdade global alta.

**H3 — degradação do consenso sem violação elétrica.** FATO: Leaderless-C2 tem `σ_r` = 0,118 (≈ 18× o C0) e nenhuma hora de violação nas barras com PV; LF-C3_naolider_longa tem `σ_r` = 0,043 sem violação. INFERÊNCIA: existe folga; a arquitetura Leaderless a amplia (fig. 06).

**H4 / H4′ — particionamento e recuperação.** FATO: λ₂ = 0 em C2 e durante C3; com falha curta (retorno em k = 20) os resultados diários são praticamente idênticos ao C0 (LF 41,63% × 41,64%; Vmax 1,0505 pu) e a fig. 17 mostra os seguidores reconvergindo após a volta do líder. INFERÊNCIA: consistente com H4′ (conectividade conjunta → recuperação).

**H5 — a arquitetura determina a robustez.** FATO: no LF-C2 o líder isolado corta 93,8% e os demais 0%; 8 horas com violação nas barras com PV (Vmax 1,0609 pu) e 145 barras-hora com sobretensão na rede (contra 50 no C0). No Leaderless-C2 não há violação nas barras com PV; o custo aparece na repartição (816 corta 67,7%, os demais ~36%). INFERÊNCIA: H5 confirmada — em LF a partição sem líder perde toda correção; em Leaderless a correção local persiste, com perda de proporcionalidade. Observação adicional: o líder isolado não consegue baixar a própria tensão nem com `ρ = 1`, porque 816, 850 e 824 são eletricamente vizinhas — partição de comunicação não é partição elétrica.

**H5a — falha do líder é o pior caso em LF.** FATO: LF-C3_lider_longa: Vmax 1,0609 pu e 29 barras com sobretensão na hora 10; LF-C3_naolider_longa: Vmax 1,0505 pu. Em Leaderless a identidade de m não altera Vmax (1,0505 pu nos quatro subcasos). INFERÊNCIA: H5a confirmada.

**Velocidade de convergência.** FATO: Leaderless converge em ~1/3 das iterações do LF (54 × 163 na hora de pico). INFERÊNCIA a declarar com ressalva: com `β` idêntico, Leaderless tem até 6 termos de correção ativos contra 1 no LF — a vantagem mistura efeito de arquitetura e de número de atuadores (§4.5.1, §7.5).

---

## 11. Limitações e pontos conhecidos

- **Barras próximas à subestação acima de 1,05 pu com o controle ativo** (800, 802, 806, 808, 812, 812r; 1–6 barras por hora, até 1,0508 pu). O controle monitora só as barras com PV (convenção do código de referência, §7.3) e a fonte está fixada em 1,05 pu. Aparece em todos os casos, inclusive sem controle. **Caso já conhecido; mantido como está.** No texto do TCC: "zero violações nas barras com PV" ≠ "zero violações na rede".
- **Subtensão no horário de ponta** (85 barras-hora < 0,95 pu em todos os casos) — fora do escopo do controle de sobretensão.
- **Curvas de exemplo.** O líder (816) vence 850 por 1,2×10⁻⁵ pu·h em `S_i` — com outras curvas o líder, a hora de pico e o rótulo do grafo podem mudar.
- **Confundimento de `β`** entre arquiteturas (§7.5) — a opção de sensibilidade (`β` normalizado) não foi rodada.
- **Adaptações não reproduzidas de Kitso et al.** (duas leis separadas, termo de decaimento `0,5·U_i`) — ver §2.5′.
- **Sem atraso de comunicação, sem C4, sem Monte Carlo** — decisões de escopo já registradas.
- **Tamanho das saídas**: ~66 MB, principalmente `raw/log_mensagens.csv` (~24 MB) e `logs/` (~33 MB). Mantidos no git por decisão do pesquisador.
