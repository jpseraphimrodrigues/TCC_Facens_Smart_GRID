# Fundamentação Teórica — Consenso proporcional sob falhas de comunicação (TCC Facens)

> **Projeto:** [TCC_Facens_Smart_GRID](../README.md) · **Documento canônico** · **Última revisão:** 2026-10-09
> **Commit de referência da intervenção documental:** `d70fb55`
> **Fontes consolidadas:** [`README.md`](../README.md) original (§§1–2), [`experimento.md`](../experimento.md) (§§2, 4), [`implementacao.md`](../implementacao.md) (D5, D7, D9, D10), [`revisao.md`](../revisao.md) (§1), [`Fase 0 - Idealização.md`](../Fase%200%20-%20Idealização.md), [`Fase 0 - Corpus - Referências.md`](../Fase%200%20-%20Corpus%20-%20Referências.md), [`Protocolos de comunicacao e sensibilidade.md`](../Protocolos%20de%20comunicacao%20e%20sensibilidade.md), código.

## 1. Conceitos fundamentais

- **Fluxo de potência** em regime permanente (balanço nodal com $Y_{bus} = G + jB$), resolvido pelo OpenDSS/AltDSS em *snapshots*.
- **Sobretensão por fluxo reverso:** $\Delta V \approx (R\,P + X\,Q)/V_{nom}$.
- **Consenso proporcional:** agentes convergem à mesma fração de corte $\rho_i = P_{curt,i}/P_{disp,i}$ — equidade relativa (CBA 2026; Kitso et al., 2025, com $U = P/P_{nom}$).
- **Leader-Follower × Leaderless:** no LF só o líder aplica a correção de tensão; no LL todo agente corrige pela tensão local (adaptação de Kitso et al., 2025, de BESS para *curtailment* FV).
- **Conectividade algébrica** $\lambda_2(L)$ (autovalor de Fiedler): $\lambda_2 > 0 \iff$ grafo conexo.
- **Falha topológica × perda probabilística × atraso** (README original §0.6): enlace indisponível (todas as mensagens falham) × mensagem individual perdida × mensagem entregue depois.

## 2. Modelagem matemática

### 2.1. Grafo de comunicação

$\mathcal{G} = (\mathcal{V}, \mathcal{E})$, $N = 6$; $A = [a_{ij}]$, $D = \mathrm{diag}(d_i)$, $L = D - A$. Topologia nominal "linha com atalho":

$$
\mathcal{E}_0 = \{(1,2), (2,3), (3,4), (4,5), (5,6), (2,5)\}
$$

### 2.2. Regra de atualização (implementada)

Com $\rho_i$ = fração de **corte** (sobretensão aumenta $\rho$; a correção é **somada**):

$$
\rho_i(k+1) = \operatorname{clip}\!\left(\rho_i(k) + \varepsilon\sum_{j} a_{ij}(k)\,[\rho_j(k) - \rho_i(k)] + c_i(k),\; 0,\; 1\right), \qquad
P_{curt,i}(k) = \rho_i(k)\,P_{disp,i}(k)
$$

Forma vetorial (`misturar_por_consenso`): $\rho(k+1) = \operatorname{clip}\big((I - \varepsilon L)\rho(k) + c(k),\,0,\,1\big)$.

> Nota de sinal (D5): o [`experimento.md`](../experimento.md) §4.5 escreve "$-\,c_i(k)$", herdando a convenção do paper-âncora, em que $\beta_i$ é a fração **injetada**. Com $\beta = 1 - \rho$ as duas formas têm dinâmica idêntica. A forma acima é a do código.

### 2.3. Termo de correção (a única diferença entre arquiteturas)

$$
\textbf{LF:}\quad c_i(k) = \mathbb{1}_{i=\ell}\;\beta\,\max\big(0,\, V_{\max\text{-}mon}(k) - V_{lim}\big)
$$
$$
\textbf{LL:}\quad c_i(k) = \beta\,\max\big(0,\, V_i(k) - V_{lim}\big)
$$

$\beta = 5{,}0$ (idêntico nas duas arquiteturas), $V_{lim} = 1{,}05$ pu. No LF, $V_{\max\text{-}mon}$ é o máximo das tensões das barras com PV **na componente conexa do líder** em $A(k)$ (D9).

### 2.4. Passo de consenso

$$
\varepsilon = \frac{2}{\sum_i d_i(A_0)} = \frac{2}{\operatorname{tr}(L_0)} = \frac{2}{12} \approx 0{,}1667
$$

Calculado uma vez no grafo nominal e mantido fixo em todos os cenários (opção (a), D7) — diverge do código do CBA, que recalcula $\varepsilon$ por montagem.

### 2.5. Escolha do líder (Critério B)

$$
S_i = \sum_{t=0}^{23} \max\big(0,\, V_i(t) - V_{lim}\big)\,\Delta t, \qquad \ell = \arg\max_i S_i
$$

O líder é fixo durante toda a simulação.

### 2.6. Métricas

$$
\sigma_r(k) = \sqrt{\frac1N\sum_i\big(\rho_i(k) - \bar\rho(k)\big)^2}
$$

(global e por partição); $e_c(k)$ = erro de consenso ([`Fase 0 - Idealização.md`](../Fase%200%20-%20Idealização.md) §20.1); no relatório pós-auditoria, `erro_rho = max(ρ) − min(ρ)`.

### 2.7. Critério de parada

$$
V_{vista}(k) \le V_{lim} + tol \quad (tol = 5\times10^{-4}\ \text{pu}) \qquad \text{ou} \qquad k = k_{max} = 500
$$

No LL, $V_{vista}$ é o máximo das tensões locais. Casos em $k_{max}$ são `nao_convergiu`. O critério é elétrico; a concordância dos estados é registrada separadamente (`consenso_satisfeito`, com `TOLERANCIA_DE_CONSENSO = 1e-6`).

### 2.8. Canal probabilístico (`src/tcc_facens/communication.py`)

`Message` (origem, destino, conteúdo, instante de envio e de entrega) e `CommunicationChannel` (perda Bernoulli com probabilidade $p$ por tentativa, fila com atraso de $d$ iterações, última mensagem válida por par origem–destino; antes da primeira entrega, o consenso usa o estado atual). A topologia permanece a nominal; a camada 3 é `C0_perda_<p>`.

## 3. Equações governantes

Fluxo de potência trifásico desequilibrado (OpenDSS/AltDSS, `SolveSnap`), com carga aplicada por `LoadMult = 1,1 × carregamento(t)` e irradiância por `PVSystem.Irradiance = curva_pv(t)/pico`.

## 4. Definição de símbolos e variáveis

| Símbolo | Significado | Valor |
|---|---|---|
| $\rho_i$ | Fração de corte do agente $i$ | [0, 1] |
| $\beta$ | Ganho de correção | 5,0 |
| $\varepsilon$ | Passo de consenso | 1/6 |
| $V_{lim}$, $tol$ | Limite e tolerância de parada | 1,05 pu; 5×10⁻⁴ pu |
| $k_{max}$ | Iterações máximas por hora | 500 |
| $S_i$ | Violação acumulada sem controle | pu·h |
| $\lambda_2$ | Conectividade algébrica | C0 0,6571; C1 0,2679; C2 0 |
| $p$, $d$ | Perda e atraso do canal | 0,05–0,20; 1 iteração |

## 5. Descrição dos algoritmos

| Bloco | Funções principais (`Experimento_Consenso_comunication_failure.py`) |
|---|---|
| Elétrico | `construir_circuito_com_pvs` (Clear + compile por caso), `aplicar_perfil_da_hora`, `aplicar_curtailment_nos_pvs` (limite de `kVA`, FP = 1, `pctCutIn = pctCutOut = 0`) |
| Comunicação | matriz A, Laplaciana, $\lambda_2$, $\varepsilon$, componentes conexas, `GrafoDeComunicacao`, `definir_cenarios_de_falha` |
| Controle | `misturar_por_consenso`, `corrigir_leader_follower`, `corrigir_leaderless` |
| Métricas | $e_c$, $\sigma_r$ global/por partição, $S_i$, escolha do líder, rotulagem do grafo |
| Simulação | `simular_dia_sem_controle`, `executar_consenso_na_hora` (o tempo não avança no laço), `simular_dia_com_consenso` |

**Teoria × implementação:** a formulação única de "mistura + correção" para LF e LL é uma **adaptação** de Kitso et al. (2025), que usam duas leis separadas (líder integra localmente; seguidores só rastreiam) e um decaimento $U_i(k) = 0{,}5\,U_i(k-1)$ no LL quando a tensão volta à faixa. O decaimento não foi implementado ([`experimento.md`](../experimento.md) §2.5′).

## 6. Hipóteses e simplificações matemáticas

*Snapshots* horários (24 pontos); iterações no mesmo instante; atraso medido em iterações, não em segundos (o período de 0,2 s é apenas rótulo de log); perda i.i.d. simétrica por tentativa; grafo de comunicação desacoplado da rede elétrica.

## 7. Condições de aplicabilidade

Convergência do consenso exige grafo conexo ou conjuntamente conexo no tempo (Nojavanzadeh et al., 2022 — R9). Resultados válidos para o alimentador, curvas, ganhos e cenários usados.

## 8. Limitações teóricas

- **Confundimento de $\beta$:** com $\beta$ idêntico, o LL pode ter até 6 termos de correção ativos contra 1 no LF; a vantagem do LL mistura efeito de arquitetura e número de atuadores ([`experimento.md`](../experimento.md) §§4.5.1, 7.5).
- Partição de comunicação não é partição elétrica: o líder isolado não reduz a própria tensão nem com $\rho = 1$ porque 816, 850 e 824 são eletricamente vizinhas ([`implementacao.md`](../implementacao.md) §10).
- Sem prova de estabilidade da malha consenso + rede.

## 9. Referências

Corpus da Fase 0 ([`Fase 0 - Corpus - Referências.md`](../Fase%200%20-%20Corpus%20-%20Referências.md)), DOIs preservados:

- **R0** — Giacomini Junior, J. (2025). *Melhoria do perfil de tensão em redes elétricas de distribuição por meio de controle distribuído com sistemas de geração fotovoltaica*. Tese de Doutorado, UNESP Bauru. (`papers/giacominijunior_j_dr_bauru.pdf`)
- **R1** — Zeraati, Golshan, Guerrero (2019). A Consensus-Based Cooperative Control of PEV Battery and PV Active Power Curtailment for Voltage Regulation in Distribution Networks. *IEEE TSG* 10(1), 670–680. DOI 10.1109/TSG.2017.2749623
- **R2** — Haque, Xiong, Nguyen (2019). Consensus Algorithm for Fair Power Curtailment of PV Systems in LV Networks. *IEEE PES GTD Asia*, 813–818. DOI 10.1109/GTDAsia.2019.8715912
- **R3** — Mai, Haque, Nguyen (2019). Consensus-Based Distributed Control for Overvoltage Mitigation in LV Microgrids. *IEEE Milan PowerTech*. DOI 10.1109/PTC.2019.8810508
- **R4** — Mai, Haque, Vergara, Nguyen, Pemen (2021). Adaptive coordination of sequential droop control for PV inverters to mitigate voltage rise in PV-Rich LV distribution networks. *EPSR* 192, 106931. DOI 10.1016/j.epsr.2020.106931
- **R5** — Zhang, Dou, Zhang, Yue (2019). Voltage Distributed Cooperative Control Considering Communication Security in Photovoltaic Power System. *IEEE TSMC: Systems* 49(8), 1592–1600. DOI 10.1109/TSMC.2019.2915605 — **PDF ausente** (o arquivo `1-s2.0-S037877962030729X-main.pdf` é uma cópia de R4)
- **R6** — Lu, Fu, Gao, Shi, Liu (2023). Voltage limit violation risk evaluation method considering communication failures in distributed voltage regulation system. *IJEPES* 147, 108886. DOI 10.1016/j.ijepes.2022.108886
- **R7** — Wang, Xie, Yang, Zhang, Wang, Cheng (2023). Distributed Online Voltage Control With Fast PV Power Fluctuations and Imperfect Communication. *IEEE TSG* 14(5), 3681–3695. DOI 10.1109/TSG.2023.3236724
- **R8** — Aghaee, Mahdian Dehkordi, Bayati, Karimi (2022). A distributed secondary voltage and frequency controller considering packet dropouts and communication delay. *IJEPES* 143, 108466. DOI 10.1016/j.ijepes.2022.108466
- **R9** — Nojavanzadeh, Lotfifard, Liu, Saberi, Stoorvogel (2022). Scale-Free Cooperative Control of Inverter-Based Microgrids With General Time-Varying Communication Graphs. *IEEE TPWRS* 37(3), 2197–2207. DOI 10.1109/TPWRS.2021.3118993
- **R10** — Wang, Zhu, Duan, Wu, Ma, Ma (2026). Distributed hierarchical control of islanded active distribution networks with dynamic consensus algorithm and adaptive virtual impedance. *Frontiers in Energy Research* 14, 1781946. DOI 10.3389/fenrg.2026.1781946
- Kitso, M.; Priambodo, B. I.; Alpízar-Castillo, J. J.; Ramírez-Elizondo, L. M.; Bauer, P. (2025). Coordination of Multiple BESS Units in a Low-Voltage Distribution Network Using Leader–Follower and Leaderless Control. *Energies* 18(17), 4566. DOI 10.3390/en18174566
- Giacomini Jr, J.; Seraphim Rodrigues, J. P.; Morales Paredes, H. K.; Cebrian, J. C. (2026). Controle Distribuído de Tensão em Redes de Distribuição com Geradores Fotovoltaicos Baseado em Consenso Proporcional. CBA 2026 (âncora metodológica primária) — ver [CBA](../../CBA/CBA/README.md).

Protocolos de comunicação citados como contexto (IEC 61850-7-420, IEEE 2030.5, DNP3/IEEE 1815, Modbus/SunSpec) em [`Protocolos de comunicacao e sensibilidade.md`](../Protocolos%20de%20comunicacao%20e%20sensibilidade.md); não modelados.
