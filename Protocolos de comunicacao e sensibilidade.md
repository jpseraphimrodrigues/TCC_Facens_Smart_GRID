## Resumo Técnico: Controle Distribuído por Consenso em Redes Inteligentes (Smart Grids)
O presente documento consolida a análise técnica do controle de curtailment fotovoltaico distribuído no alimentador IEEE 34 barras, integrando normas industriais de comunicação em Smart Grids, modelagem de falhas em malhas de controle de inversores e a formulação teórica e prática das hipóteses de sensibilidade aplicadas ao projeto.
------------------------------
## 1. Protocolos de Comunicação em Smart Grids
Em sistemas elétricos modernos, os inversores solares fotovoltaicos e os sistemas de armazenamento de energia (BESS) operam sob diferentes camadas de abstração, demandando protocolos específicos para cada nível hierárquico da infraestrutura.

| Protocolo | Camada de Transporte | Aplicação Primária | Objeto / Perfil de Dados DER | Mecanismo Típico de Contingência / Falha |
|---|---|---|---|---|
| IEC 61850-7-420 | Camada 2 Ethernet direta (GOOSE multicast) ou TCP/IP (MMS) | Automação e proteção de subestações; controle rápido de Recursos Energéticos Distribuídos (DER) | Nós lógicos: DWMX (controle de potência ativa), MMXU (medições elétricas) | Expiração do tempo de vida útil da mensagem (TimeAllowedToLive - TAL), saltos anômalos em sqNum ou congelamento de stNum |
| IEEE 2030.5 (SEP 2.0) | TCP/TLS sobre redes IP / Web (HTTP/REST com XML/JSON) | Interconexão concessionária-prosumidor (DER), agregação de usinas virtuais e Demand Response | Recursos RESTful: DefaultDERControl, DERControl, CurveData | Timeout TCP, atraso de polling, expiração da concessão de controle temporário (duration) |
| DNP3 (IEEE 1815) | TCP/IP serializado ou conexões seriais (RS-232 / RS-485) | Telemetria SCADA tradicional e envio de comandos ponto a ponto de concessionárias | Blocos analógicos de saída (Analog Output Block) e eventos de classe 1/2/3 | Estouro do temporizador Comm-Loss Timeout, falta de confirmação (App-layer Confirm) |
| Modbus (RTU / TCP) | Serial RS-485 ou TCP/IP | Controle local, parametrização direta de inversores de fabricantes diversos e Grid Zero | Mapas SunSpec (registradores padronizados de tensão, corrente e limitadores de corte) | Falha no enlace de transporte físico ou silêncio do dispositivo escravo (timeout de consulta) |

------------------------------
## 2. Modelagem e Emulação Realista de Falhas no Controle Distribuído
O algoritmo avaliado implementa um consenso de corte proporcional ($\rho_i \in [0, 1]$) entre agentes fotovoltaicos via topologias Leader-Follower e Leaderless.
A transição de modelos genéricos (remocão estática de arestas ou canais puramente estocásticos de Bernoulli) para o paradigma normativo das Smart Grids demanda as seguintes adaptações:

* Validade Temporal com TAL (TimeAllowedToLive - IEC 61850): O agente receptor não deve reter a última amostra indefinidamente. Cada mensagem armazena um número de sequência (sqNum), estado (stNum) e tempo de expiração; transcorrido o limite sem atualização, o enlace é marcado como desconectado.
* Comutação para Modo de Segurança (Failsafe / Local Fallback): Em caso de isolamento ou perda contínua de enlace por período superior ao limite operacional (TAL do IEC 61850 ou Comm-Loss Timeout do DNP3), o inversor abandona a dependência do consenso e migra autonomamente para a curva local Volt-Watt parametrizada (conforme IEEE 1547), limitando a própria geração se a tensão local $V_i$ ultrapassar o patamar seguro de $1{,}05\text{ pu}$.
* Atrasos Estruturais vs. Dinâmica em Redes WAN: Emulação de latências operacionais compatíveis com a tecnologia empregada (latência sub-ciclo em barramentos de subestação com IEC 61850; latências de centenas de milissegundos a múltiplos segundos com perdas em rajadas pelo modelo Gilbert-Elliott no IEEE 2030.5).

------------------------------
## 3. Destrinchando o Conceito de "Sensibilidade"
No contexto do controle distribuído de alimentadores de distribuição como o IEEE 34 barras, o conceito de "sensibilidade" abrange três vertentes teóricas fundamentais:

                  ┌─────────────────────────────────────────┐
                  │          CONCEITO DE SENSIBILIDADE      │
                  └────────────────────┬────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
┌──────────────────┐         ┌──────────────────┐          ┌──────────────────┐
│   Hipótese 1:    │         │   Hipótese 2:    │          │   Hipótese 3:    │
│  Elétrica (∂V/∂P)│         │ Conectividade λ₂ │          │   Paramétrica    │
└──────────────────┘         └──────────────────┘          └──────────────────┘

## Hipótese 1: Matriz de Sensibilidade Elétrica Tensão–Potência ($\partial V / \partial P$)
Esta é a hipótese mais provável e de maior relevância física na engenharia de sistemas de potência.

* Definição Física: A derivada parcial $S_{ij} = \frac{\partial V_i}{\partial P_j}$ quantifica a variação na amplitude da tensão na barra $i$ decorrente de uma perturbação de potência ativa injetada/absorvida na barra $j$. Em redes radiais com alta relação $R/X$, como redes de média tensão, o corte de potência ativa é o recurso dominante para conter a sobretensão.
* Otimização do Ganho de Correção ($\beta$):
No código do experimento, o ganho de corte é fixado empiricamente em GANHO_DE_CORRECAO_DE_TENSAO = 5.0. Se a sensibilidade na barra crítica for $S_{max} = \max(\partial V / \partial P)$, o ganho analiticamente estável deve respeitar:
$$\beta \approx \frac{1}{\frac{\partial V}{\partial P}}$$ Ganhos excessivamente superiores a essa relação levam a oscilações em torno do limite de tensão ($1{,}05\text{ pu}$), gerando instabilidade numérica no fluxo de carga e estresse mecânico/elétrico nos conversores.
* Consenso Ponderado (Minimização do Curtailment Global):
O consenso puramente uniforme força que $\rho_i \approx \rho_j$, penalizando geradores que estão eletricamente distantes do ponto de violação. Ponderar os pesos do consenso pela sensibilidade relativa permite que os inversores localizados nos nós com maior eficácia elétrica absorvam a maior cota do alívio, maximizando a energia injetada na rede como um todo.
* Extração Prática via Algoritmo de Perturbação:
Em simuladores de fluxo de potência (como o OpenDSS/AltDSS), calcula-se essa matriz aplicando um degrau unitário $\Delta P$ (ex.: $1\text{ kW}$) em cada inversor e computando a diferença do vetor de tensões:
$$S_{ij} = \frac{V_i^{\text{base}} - V_i^{\text{perturbado}}}{\Delta P_j}$$ 

## Hipótese 2: Sensibilidade da Conectividade Algébrica do Grafo ($\lambda_2$)
Esta hipótese analisa a robustez estrutural do consenso frente a falhas de comunicação nos nós e enlaces.

* Conectividade Algébrica ($\lambda_2$): Representa o segundo menor autovalor da matriz Laplaciana $L = D - A$ do grafo. Se $\lambda_2 = 0$, a rede encontra-se desconexa ou particionada; se $\lambda_2 > 0$, a convergência assintótica do consenso é garantida.
* Sensibilidade da Aresta à Degradação: Avalia qual enlace do sistema causa o maior impacto negativo na velocidade de sincronização se for rompido:
$$\frac{\partial \lambda_2}{\partial a_{ij}} = \left(v_{2,i} - v_{2,j}\right)^2$$ onde $v_2$ é o autovetor de Fiedler associado a $\lambda_2$. Arestas que conectam nós com grande separação no vetor de Fiedler (como a aresta que isola o nó líder no cenário C2) detêm altíssima sensibilidade e devem ser priorizadas em termos de redundância física.

## Hipótese 3: Análise de Sensibilidade Paramétrica do Algoritmo
Trata-se da avaliação do comportamento do algoritmo frente à variação sistemática de seus hiperparâmetros de simulação.

* Parâmetros de Ajuste:
* Fator de passo do consenso: $\varepsilon = \frac{2}{\sum \lambda_i(L_0)}$;
   * Ganhos de tensão: $\beta$;
   * Taxa de erro e latência do meio: $p_{\text{loss}} \in [0{,}0, 0{,}20]$ e $\Delta k \in [0, 5]$.
* Variáveis de Saída Monitoradas: Mede a dispersão da taxa de corte ($\sigma_r$), o número de iterações para parada ($N_{\text{iter}}$) e a presença de sobretensões residuais na rede ($V_{max} > 1{,}05\text{ pu}$).

Deseja detalhar o código matemático para calcular a matriz de sensibilidade $\partial V / \partial P$ diretamente via perturbativo no OpenDSS, ou estruturar o teste de sensibilidade do autovalor $\lambda_2$ sobre a Laplaciana do circuito?

## Resposta do orientador sobre SENSIBILIDADE
> Sensibilidade do ponto de vista do impacto do recorte da potência ativa

# Sensibilidade sob a Ótica do Impacto do Recorte de Potência Ativa

A validação do direcionamento foca a análise de **sensibilidade estritamente sob o impacto físico e energético do recorte (*curtailment*) da potência ativa (\(\partial V / \partial P\))**. Em redes de distribuição (como o alimentador IEEE 34 barras), a relação entre a variação de tensão e a potência ativa é acentuada devido à característica resistiva (alta relação \(R/X\)) dos condutores de média e baixa tensão.

O objetivo desta abordagem é quantificar a eficácia de cada inversor em mitigar sobretensões e avaliar o "custo" em termos de energia limpa desperdiçada pelo algoritmo de consenso.

---

### 1. Formulação Matemática da Sensibilidade de Impacto

A variação da amplitude da tensão na barra $i$ ($\Delta V_i$) decorrente das ações de corte de potência ativa realizadas por todos os inversores do sistema é linearizada através da **Matriz de Sensibilidade Elétrica**:

$$\Delta V_i \approx \sum_{j=1}^{N} \frac{\partial V_i}{\partial P_j} \cdot \Delta P_j$$

Onde:
*   $\frac{\partial V_i}{\partial P_j}$: Coeficiente de sensibilidade que quantifica o impacto na tensão da barra $i$ causado por uma alteração de potência na barra $j$.
*   $\Delta P_j$: O **impacto do recorte** aplicado pelo inversor $j$, derivado diretamente do fator de corte $\rho_j$ calculado no consenso ($P_{\text{injetada}} = (1 - \rho) \cdot P_{\text{disponível}}$).

---

### 2. Hipóteses de Sensibilidade Baseadas no Impacto do Recorte

A partir dessa definição, estruturam-se três hipóteses fundamentais para avaliar o desempenho do controle distribuído:

#### Hipótese A: Ineficiência do Consenso Uniforme (Eficácia Local)
Inversores conectados nas extremidades do alimentador (zonas eletricamente distantes da subestação) possuem coeficientes $\frac{\partial V_i}{\partial P_i}$ significativamente maiores do que os inversores localizados no início do circuito. 
*   **O Impacto:** Se o algoritmo de consenso for puramente uniforme (forçando $\rho_i \approx \rho_j$), os inversores do início da linha estarão sofrendo um corte de geração inútil, gerando um alto impacto financeiro/energético para um ganho de mitigação de tensão praticamente nulo.

#### Hipótese B: Minimização do Recorte Global via Consenso Ponderado
A sensibilidade pode atuar diretamente como o **fator de ponderação (peso)** na matriz de adjacência do algoritmo de consenso distribuído.
*   **O Impacto:** Ao invés de convergir para uma taxa de corte idêntica, os agentes com maior sensibilidade elétrica ($\frac{\partial V}{\partial P}$) assumem uma cota maior de redução de potência. Isso resulta na otimização do perfil de tensão com o **mínimo impacto energético global**, maximizando a injeção total de energia renovável na rede.

#### Hipótese C: Criticidade do Impacto sob Falhas de Comunicação
O impacto de uma falha de comunicação (estouro de *Timeout* ou perda de pacotes via IEC 61850 / IEEE 2030.5) não é homogêneo na rede.
*   **O Impacto:** Se o canal de comunicação falhar em um nó de **alta sensibilidade**, o impacto sistêmico é crítico, pois a malha distribuída perde o seu atuador mais eficiente. Se a falha ocorrer em um nó de baixa sensibilidade, o consenso permanece resiliente e o impacto no perfil de tensão é marginal.

---

### 3. Métricas de Avaliação para Implementação no Código

Para traduzir a sensibilidade do impacto em resultados quantitativos na simulação, devem ser monitorados os seguintes indicadores:

1.  **Indicador de Impacto Energético Individual ($E_{\text{cut}, i}$):**
    Total de energia ativa ceifada (em kWh) por agente ao longo do horizonte de simulação:
    $$E_{\text{cut}, i} = \sum_{k} \left( P_{\text{disponível}, i}(k) - P_{\text{injetada}, i}(k) \right) \cdot \Delta t$$

2.  **Índice de Severidade de Sobretensão Residual ($S_V$):**
    Mapeia se o corte aplicado foi energeticamente eficiente para eliminar as violações:
    $$S_V = \sum_{k} \sum_{i=1}^{N} \max(0, V_i(k) - 1.05)$$

3.  **Fator de Assimetria e Alocação do Recorte:**
    Análise do desvio padrão e distribuição de $\rho$ entre os nós, demonstrando graficamente como a sensibilidade desloca o impacto do corte para as barras corretas.
