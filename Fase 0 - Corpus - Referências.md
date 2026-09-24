# Bibliografia-base — Fase 0

## Consenso proporcional, curtailment fotovoltaico e falhas de comunicação

> **Objetivo da tabela:** reunir os trabalhos-base para fundamentação teórica, definição do experimento, identificação do gap e comparação dos resultados da Fase 0.

| ID      | Referência                                                                                                                                                                                                              | Tipo / Veículo                                                                | Tema central                                                                           | Sistema / DERs                                                      | Consenso / Controle                                              | Comunicação analisada                                                                                  |                           Curtailment FV | Relação com a Fase 0                                                                                                                             | O que devemos extrair                                                                                                                    | DOI                              |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **R0**  | **GIACOMINI JUNIOR, J. (2025). *Melhoria do perfil de tensão em redes elétricas de distribuição por meio de controle distribuído com sistemas de geração fotovoltaica*.**                                               | Tese de Doutorado — UNESP, Faculdade de Engenharia de Bauru                   | Controle distribuído para melhoria do perfil de tensão com geração FV                  | **IEEE 34 barras**, 4 GFVs                                          | **Consenso líder-seguidor**, Volt-Var e curtailment ativo        | Diferentes **topologias estáticas** de comunicação; analisa efeito da conectividade sobre convergência |                                  **Sim** | **Base metodológica direta da Fase 0.** O novo experimento parte daqui e introduz falhas efetivas na comunicação                                 | Equações do consenso; ganhos; critério de convergência; topologias; localização/potência dos GFVs; métricas; cenários; trabalhos futuros | —                                |
| **R1**  | **ZERAATI, M.; GOLSHAN, M. E. H.; GUERRERO, J. M. (2019). *A Consensus-Based Cooperative Control of PEV Battery and PV Active Power Curtailment for Voltage Regulation in Distribution Networks*.**                     | IEEE Transactions on Smart Grid, 10(1), 670–680                               | Coordenação distribuída de PEVs e curtailment FV para regulação de tensão              | Rede LV trifásica com PVs e PEVs                                    | Dois algoritmos de consenso; compartilhamento cooperativo        | Comunicação necessária entre agentes, mas falhas não são o foco                                        |                        **Sim — central** | Fundamenta diretamente **consenso + curtailment + tensão + fairness**                                                                            | Definição do compartilhamento proporcional; variável de consenso; cálculo do curtailment; critério de ativação; métricas de justiça      | **10.1109/TSG.2017.2749623**     |
| **R2**  | **HAQUE, A. N. M. M.; XIONG, M.; NGUYEN, P. H. (2019). *Consensus Algorithm for Fair Power Curtailment of PV Systems in LV Networks*.**                                                                                 | IEEE PES GTD Grand International Conference and Exposition Asia, pp. 813–818  | Curtailment justo entre PVs para mitigação de sobretensão                              | Três redes LV                                                       | Algoritmo de consenso entre nós vizinhos + P-V droop             | Comunicação esparsa entre agentes; falhas não são estudadas                                            |                        **Sim — central** | Base direta para **fair/proportional curtailment**                                                                                               | Definição de fairness; algoritmo iterativo; variáveis trocadas; topologia; comparação com P-V local                                      | **10.1109/GTDAsia.2019.8715912** |
| **R3**  | **MAI, T. T.; HAQUE, A. N. M. M.; NGUYEN, P. H. (2019). *Consensus-Based Distributed Control for Overvoltage Mitigation in LV Microgrids*.**                                                                            | IEEE Milan PowerTech                                                          | Controle distribuído para mitigação de sobretensão por PVs                             | Rede francesa LV com sistemas FV                                    | Hierarquia local + consenso; Q-V e P-V droop                     | Infraestrutura esparsa de comunicação, assumida operacional                                            |                                  **Sim** | Liga diretamente **sobretensão → consenso → distribuição do curtailment**                                                                        | Arquitetura hierárquica; interação Q-V/P-V; variável de consenso; cálculo do mínimo curtailment; fairness                                | **10.1109/PTC.2019.8810508**     |
| **R4**  | **MAI, T. T.; HAQUE, A. N. M. M.; VERGARA, P. P.; NGUYEN, P. H.; PEMEN, G. (2021). *Adaptive coordination of sequential droop control for PV inverters to mitigate voltage rise in PV-Rich LV distribution networks*.** | Electric Power Systems Research, 192, 106931                                  | Coordenação adaptativa Q-V/P-V em redes com alta penetração FV                         | Rede LV europeia real; ~150% de penetração FV                       | Droop sequencial coordenado por consenso e decomposição em áreas | Comunicação entre PVs; falha não é variável experimental principal                                     |                                  **Sim** | Referência para coordenação eficiente e impacto do consenso sobre redução de curtailment                                                         | Método de divisão em áreas; algoritmo; fairness; comparação de energia curtailed; resultados quantitativos                               | **10.1016/j.epsr.2020.106931**   |
| **R5**  | **ZHANG, Z.; DOU, C.; ZHANG, B.; YUE, W. (2019). *Voltage Distributed Cooperative Control Considering Communication Security in Photovoltaic Power System*.**                                                           | IEEE Transactions on Systems, Man, and Cybernetics: Systems, 49(8), 1592–1600 | Regulação distribuída de tensão FV considerando imperfeições da comunicação            | Sistema fotovoltaico conectado à rede                               | Controle cooperativo em dois níveis + protocolo de consenso      | **Mudança de topologia, delay, packet loss e grandes atrasos**                                         |     Indiretamente / controle de potência | **Um dos trabalhos mais próximos da Fase 0**                                                                                                     | Modelo de falha; representação matemática de delay e packet loss; topologia variável; métricas de convergência; estratégia preditiva     | **10.1109/TSMC.2019.2915605**    |
| **R6**  | **LU, Y.; FU, M.; GAO, J.; SHI, Q.; LIU, W. (2023). *Voltage limit violation risk evaluation method considering communication failures in distributed voltage regulation system*.**                                     | International Journal of Electrical Power & Energy Systems, 147, 108886       | Risco de violação de tensão causado por falhas de comunicação em controle distribuído  | **IEEE 33 barras modificado**, 8 PVs; PV + BESS; 4 nós de regulação | Algoritmo distribuído por consenso                               | **Falhas de agentes, controladores e infraestrutura de comunicação**                                   |               Não é a variável principal | **Concorrente conceitual mais próximo da Fase 0**: conecta diretamente falha cyber → consenso → tensão elétrica                                  | Tipos de falha; matriz de acessibilidade; severidade; topologia; propagação da falha até tensão; definição de risco; casos críticos      | **10.1016/j.ijepes.2022.108886** |
| **R7**  | **WANG, L.; XIE, L.; YANG, Y.; ZHANG, Y.; WANG, K.; CHENG, S.-J. (2023). *Distributed Online Voltage Control With Fast PV Power Fluctuations and Imperfect Communication*.**                                            | IEEE Transactions on Smart Grid, 14(5), 3681–3695                             | Controle distribuído online de tensão sob variação rápida FV e comunicação imperfeita  | Rede de distribuição rica em PV                                     | **Dynamic consensus** + Volt-Var                                 | **Delay aleatório e packet dropout modelados estocasticamente**                                        | Possível extensão indicada pelos autores | **Referência central para modelagem matemática da comunicação imperfeita**                                                                       | Modelo estocástico dos links; tracking error; modelagem de atraso; packet loss; matrizes row-stochastic; condições de convergência       | **10.1109/TSG.2023.3236724**     |
| **R8**  | **AGHAEE, F.; MAHDIAN DEHKORDI, N.; BAYATI, N.; KARIMI, H. (2022). *A distributed secondary voltage and frequency controller considering packet dropouts and communication delay*.**                                    | International Journal of Electrical Power & Energy Systems, 143, 108466       | Controle secundário distribuído sob packet dropout e delay                             | Microgrid AC ilhada; quatro DGs baseados em inversores              | Controle distribuído baseado em consenso                         | **Packet dropout idêntico e não idêntico + delay**                                                     |                                      Não | **Referência metodológica para modelagem de falhas**, embora a aplicação elétrica seja diferente                                                 | Modelo probabilístico de packet dropout; cadeia de Markov; delay; consensus error; cenários experimentais; estabilidade                  | **10.1016/j.ijepes.2022.108466** |
| **R9**  | **NOJAVANZADEH, D.; LOTFIFARD, S.; LIU, Z.; SABERI, A. A.; STOORVOGEL, A. A. (2022). *Scale-Free Cooperative Control of Inverter-Based Microgrids With General Time-Varying Communication Graphs*.**                    | IEEE Transactions on Power Systems, 37(3), 2197–2207                          | Controle distribuído robusto com grafo variável no tempo                               | CIGRE MV Microgrid                                                  | Controle cooperativo distribuído scale-free                      | **Link failure, packet loss, plug-and-play, ruído e delay**                                            |                                      Não | Referência forte para a futura evolução da Fase 0 em direção a **controle tolerante a falhas**                                                   | Grafos variantes; condições de conectividade; perda de enlace; entrada/saída de agentes; atraso; requisitos mínimos de informação        | **10.1109/TPWRS.2021.3118993**   |
| **R10** | **WANG, X.; ZHU, Z.; DUAN, Y.; WU, X.; MA, J.; MA, X. (2026). *Distributed hierarchical control of islanded active distribution networks with dynamic consensus algorithm and adaptive virtual impedance*.**            | Frontiers in Energy Research, 14, 1781946                                     | Controle hierárquico distribuído com consenso dinâmico e impedância virtual adaptativa | Active Distribution Network ilhada; DGs + ESS                       | Dynamic Consensus Algorithm + adaptive virtual impedance         | **Falha de enlace, delay e plug-and-play**                                                             |                                      Não | Referência recente para testar a hipótese de que **perda de link não implica necessariamente perda do controle se o grafo permanecer conectado** | Cenário de link failure; comportamento da convergência; reconfiguração; efeito elétrico; validação MATLAB/Simulink e OPAL-RT             | **10.3389/fenrg.2026.1781946**   |

---

## Classificação funcional para a Fase 0

| Grupo                                      | Referências               | Função na pesquisa                                                                   |
| ------------------------------------------ | ------------------------- | ------------------------------------------------------------------------------------ |
| **Base metodológica direta**               | **R0 — Giacomini (2025)** | Define o sistema elétrico, consenso líder-seguidor e origem direta do experimento    |
| **Consenso + curtailment + fairness**      | **R1, R2, R3, R4**        | Fundamentam por que usar consenso para repartir curtailment e controlar sobretensão  |
| **PV + consenso + comunicação imperfeita** | **R5, R6, R7**            | Trabalhos que mais delimitam o verdadeiro gap da Fase 0                              |
| **Modelagem de falhas de comunicação**     | **R8, R9**                | Fornecem modelos de packet loss, delay, link failure e grafos variantes              |
| **Benchmark recente de resiliência**       | **R10**                   | Mostra experimentalmente comportamento do consenso diante de falha de enlace e delay |

---

## Relação conceitual entre os trabalhos

```text
                          CONSENSO
                             │
              ┌──────────────┴───────────────┐
              │                              │
              ▼                              ▼
     CURTAILMENT / FAIRNESS          COMUNICAÇÃO IMPERFEITA
              │                              │
     R1 Zeraati                         R5 Zhang
     R2 Haque                           R6 Lu
     R3 Mai 2019                        R7 Wang 2023
     R4 Mai 2021                        R8 Aghaee
              │                         R9 Nojavanzadeh
              │                         R10 Wang 2026
              └──────────────┬───────────────┘
                             │
                             ▼
                       R0 GIACOMINI
                             │
              IEEE 34 + FV + consenso
                 líder-seguidor +
                    curtailment
                             │
                             ▼
                         FASE 0
                             │
              FALHA DA COMUNICAÇÃO
                             ↓
                  CONVERGÊNCIA
                             ↓
                    CURTAILMENT
                             ↓
                     FAIRNESS
                             ↓
                       TENSÃO
```

---

# Matriz que deverá ser preenchida durante a leitura

Para cada referência, a análise completa deverá posteriormente registrar:

| Campo                           | Informação a levantar                                                 |
| ------------------------------- | --------------------------------------------------------------------- |
| **Objetivo**                    | Qual pergunta o trabalho tenta responder?                             |
| **Gap declarado**               | Que deficiência da literatura os autores identificam?                 |
| **Sistema elétrico**            | IEEE 33, IEEE 34, LV real, CIGRE etc.                                 |
| **Número de DERs**              | Quantos PVs/DGs/BESS participam?                                      |
| **Tipo de DER**                 | PV, BESS, PEV, DG inverter-based etc.                                 |
| **Objetivo elétrico**           | Tensão, frequência, P/Q sharing, curtailment etc.                     |
| **Arquitetura**                 | Local, distribuída, hierárquica, multiagente                          |
| **Tipo de consenso**            | Average, weighted, leader-follower, dynamic etc.                      |
| **Variável de consenso**        | O que efetivamente converge?                                          |
| **Grafo**                       | Direcionado/não direcionado; fixo/variável; topologia                 |
| **Conectividade**               | Requisitos teóricos de conectividade                                  |
| **Laplaciana**                  | Se e como é empregada                                                 |
| **\(\lambda_2\)**               | Se conectividade algébrica é utilizada                                |
| **Falha de link**               | Sim/não e modelo utilizado                                            |
| **Falha de agente**             | Sim/não                                                               |
| **Packet loss**                 | Sim/não; distribuição; probabilidade                                  |
| **Delay**                       | Sim/não; fixo, limitado ou estocástico                                |
| **Particionamento**             | Se o grafo chega a ser desconectado                                   |
| **Momento da falha**            | Antes ou durante a operação                                           |
| **Recuperação**                 | Se a comunicação retorna                                              |
| **Fallback**                    | Qual ação é tomada quando há falha                                    |
| **Critério de convergência**    | Tolerância / erro / número de iterações                               |
| **Métrica de consenso**         | Erro, tracking error etc.                                             |
| **Métrica elétrica**            | \(V_{\max}\), violações, frequência etc.                              |
| **Curtailment**                 | kW, kWh ou percentual                                                 |
| **Fairness**                    | Como é definida e medida                                              |
| **Software**                    | MATLAB, Simulink, OpenDSS, OPAL-RT etc.                               |
| **Tipo de simulação**           | Snapshot, temporal, dinâmica, HIL                                     |
| **Resultados principais**       | Valores quantitativos relevantes                                      |
| **Limitações**                  | O que não foi investigado                                             |
| **Trabalhos futuros**           | Continuidade explicitamente proposta                                  |
| **Diferença para nossa Fase 0** | Elemento que permanece não coberto                                    |
| **Elemento reutilizável**       | Equação, cenário, métrica ou desenho experimental que podemos adaptar |

---

# Núcleo bibliográfico mínimo do TCC

Para um paper de aproximadamente 15 páginas, estes trabalhos não terão todos o mesmo peso.

O núcleo técnico deverá ser construído principalmente sobre:

**Giacomini (2025) → Zeraati (2019) → Haque (2019) → Mai (2019/2021) → Zhang (2019) → Lu (2023) → Wang (2023).**

Aghaee, Nojavanzadeh e Wang (2026) funcionam principalmente como referências para a modelagem e discussão da **robustez da camada de comunicação**.

A sequência lógica da revisão poderá ser:

```text
Sobretensão provocada por elevada penetração FV
                         ↓
            necessidade de curtailment
                         ↓
        problema da distribuição injusta
                         ↓
       consenso para repartir o esforço
                         ↓
       dependência de uma rede de comunicação
                         ↓
  hipótese usual de comunicação ideal deixa de valer
                         ↓
        delay / packet loss / link failure
                         ↓
      impacto sobre convergência do consenso
                         ↓
   impacto sobre curtailment e perfil de tensão
                         ↓
                      FASE 0
```

---

# Referências bibliográficas preliminares

**GIACOMINI JUNIOR, J.** Melhoria do perfil de tensão em redes elétricas de distribuição por meio de controle distribuído com sistemas de geração fotovoltaica. 2025. 111 f. Tese (Doutorado) — Universidade Estadual Paulista (UNESP), Faculdade de Engenharia, Bauru, 2025.

**ZERAATI, M.; GOLSHAN, M. E. H.; GUERRERO, J. M.** A Consensus-Based Cooperative Control of PEV Battery and PV Active Power Curtailment for Voltage Regulation in Distribution Networks. *IEEE Transactions on Smart Grid*, v. 10, n. 1, p. 670–680, 2019. DOI: 10.1109/TSG.2017.2749623.

**HAQUE, A. N. M. M.; XIONG, M.; NGUYEN, P. H.** Consensus Algorithm for Fair Power Curtailment of PV Systems in LV Networks. In: *2019 IEEE PES GTD Grand International Conference and Exposition Asia*. p. 813–818, 2019. DOI: 10.1109/GTDAsia.2019.8715912.

**MAI, T. T.; HAQUE, A. N. M. M.; NGUYEN, P. H.** Consensus-Based Distributed Control for Overvoltage Mitigation in LV Microgrids. In: *2019 IEEE Milan PowerTech*. IEEE, 2019. DOI: 10.1109/PTC.2019.8810508.

**MAI, T. T.; HAQUE, A. N. M. M.; VERGARA, P. P.; NGUYEN, P. H.; PEMEN, G.** Adaptive coordination of sequential droop control for PV inverters to mitigate voltage rise in PV-Rich LV distribution networks. *Electric Power Systems Research*, v. 192, 106931, 2021. DOI: 10.1016/j.epsr.2020.106931.

**ZHANG, Z.; DOU, C.; ZHANG, B.; YUE, W.** Voltage Distributed Cooperative Control Considering Communication Security in Photovoltaic Power System. *IEEE Transactions on Systems, Man, and Cybernetics: Systems*, v. 49, n. 8, p. 1592–1600, 2019. DOI: 10.1109/TSMC.2019.2915605.

**LU, Y.; FU, M.; GAO, J.; SHI, Q.; LIU, W.** Voltage limit violation risk evaluation method considering communication failures in distributed voltage regulation system. *International Journal of Electrical Power & Energy Systems*, v. 147, 108886, 2023. DOI: 10.1016/j.ijepes.2022.108886.

**WANG, L.; XIE, L.; YANG, Y.; ZHANG, Y.; WANG, K.; CHENG, S.-J.** Distributed Online Voltage Control With Fast PV Power Fluctuations and Imperfect Communication. *IEEE Transactions on Smart Grid*, v. 14, n. 5, p. 3681–3695, 2023. DOI: 10.1109/TSG.2023.3236724.

**AGHAEE, F.; MAHDIAN DEHKORDI, N.; BAYATI, N.; KARIMI, H.** A distributed secondary voltage and frequency controller considering packet dropouts and communication delay. *International Journal of Electrical Power & Energy Systems*, v. 143, 108466, 2022. DOI: 10.1016/j.ijepes.2022.108466.

**NOJAVANZADEH, D.; LOTFIFARD, S.; LIU, Z.; SABERI, A. A.; STOORVOGEL, A. A.** Scale-Free Cooperative Control of Inverter-Based Microgrids With General Time-Varying Communication Graphs. *IEEE Transactions on Power Systems*, v. 37, n. 3, p. 2197–2207, 2022. DOI: 10.1109/TPWRS.2021.3118993.

**WANG, X.; ZHU, Z.; DUAN, Y.; WU, X.; MA, J.; MA, X.** Distributed hierarchical control of islanded active distribution networks with dynamic consensus algorithm and adaptive virtual impedance. *Frontiers in Energy Research*, v. 14, 1781946, 2026. DOI: 10.3389/fenrg.2026.1781946.
