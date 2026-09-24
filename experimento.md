# Experimento — Fase 0: Impacto de Falhas de Comunicação no Consenso Proporcional (Leader-Follower vs. Leaderless)

## Análise científica, inferência de hipóteses e orquestração experimental

> Documento de trabalho produzido a partir da leitura integral de `Fase 0 — Idealização.md`, `Fase 0 - Corpus - Referências.md`, e da infraestrutura já consolidada para o mestrado (`Skills/Executor_altGRID_consenso/*`, `Skills/Paper_2..4_*`, `Skills/Roteiro_Macro_*`). Não substitui a Fase 0 — a formaliza, identifica o que falta ser decidido antes de codificar, e propõe a orquestração computacional do experimento.
>
> **Atualização de escopo (decisão do pesquisador).** A falha de comunicação continua sendo o eixo científico central do TCC, mas agora é testada em **duas variantes arquiteturais do consenso proporcional**: **Leader-Follower** (um único agente recebe a correção de erro de tensão; convenção já herdada de R0/Giacomini) e **Leaderless** (cada agente aplica sua própria correção local de tensão; convenção adaptada de Kitso et al. (2025), já referenciada em `Skills/Paper_2..._BESS.md §20-21` para BESS, aqui adaptada para curtailment FV). O desenho experimental deixa de ser `1 arquitetura × 5 cenários de falha` e passa a ser **`2 arquiteturas × 5 cenários de falha`**. Também fica registrado explicitamente: **por decisão do pesquisador, a camada de falha de comunicação não é, por ora, incorporada à linha do mestrado** (Papers 2–4) — ela permanece escopo exclusivo deste TCC; a §8 foi revisada para refletir isso.

---

# 1. Enquadramento e o que este documento resolve

A Fase 0 (TCC) já está bem especificada em termos de *intenção científica*: existe pergunta de pesquisa, hipóteses H1–H4, cenários C0–C4, métricas e uma arquitetura de pastas sugerida. O que **ainda não existe** é:

1. uma leitura crítica que separe, dentro da literatura de referência, **o que é transferível diretamente** (equações, condições de convergência, definições de falha) do que é apenas inspiração temática;
2. uma **formalização única e não ambígua** do experimento — variável de estado, regra de atualização, regra de falha, critério de parada — no padrão de rigor já exigido pela skill `Executor_altGRID_consenso` (que rejeita execuções sem essa formalização), **agora para duas arquiteturas de controle distintas** (Leader-Follower e Leaderless), que a skill exige tratar como métodos separados, nunca conflacionados;
3. uma ponte explícita entre a Fase 0 (TCC) e a infraestrutura computacional que **já está sendo construída para o mestrado**, delimitando precisamente **o que atravessa essa ponte agora (a comparação de arquiteturas) e o que fica retido no TCC por decisão do pesquisador (a camada de falha de comunicação)**.

Este documento cobre os três pontos. Ele não inicia a implementação em código — define precisamente o que deve ser implementado e por quê.

---

# 2. Leitura crítica do corpus — o que cada grupo de referências realmente contribui

A tabela de `Fase 0 - Corpus - Referências.md` já classifica as 11 referências em grupos funcionais. Aqui a leitura é aprofundada: **o que é matematicamente reutilizável** para H1–H4.

## 2.0 Âncora metodológica primária (adicionada nesta revisão) — Giacomini Jr, Seraphim Rodrigues, Paredes & Cebrian (2026, CBA)

**Referência:** Giacomini Jr, J.; Seraphim Rodrigues, J. P.; Morales Paredes, H. K.; Cebrian, J. C. *Controle Distribuído de Tensão em Redes de Distribuição com Geradores Fotovoltaicos Baseado em Consenso Proporcional*. Aceito para o **Congresso Brasileiro de Automática (CBA) 2026** — ainda não publicado, sem DOI. Arquivo: `JGJ_Paper_CBA_2026_V4.pdf`.

Esta referência **substitui, como fonte primária de equações**, a leitura indireta que este documento fazia até agora via R0 (tese de doutorado de Giacomini) e via R1–R4. Diferença crucial: este paper compara **exatamente** as duas variáveis de estado que a Fase 0 precisa (potência absoluta vs. fator proporcional adimensional) no **mesmo tipo de alimentador** (IEEE 34 barras modificado, ~90 km, tronco 3F com ramais 1F — mesma base de `Cebrian et al., 2023`, que é a origem dos arquivos `.dss` já presentes em `IEEE34bus/`), com resultados quantitativos diretos.

### Equações verificadas (citação direta, notação original do paper)

**Consenso na potência absoluta:**

$$
p_i^{inj}(k+1) = p_i^{inj}(k) + \epsilon\sum_{j=1}^{\mathcal N} a_{ij}\big(p_j^{inj}(k)-p_i^{inj}(k)\big) - b_i\,G(k)\,\Delta V(k)
$$

**Consenso proporcional:**

$$
\beta_i(k+1) = \beta_i(k) + \epsilon\sum_{j=1}^{\mathcal N} a_{ij}\big(\beta_j(k)-\beta_i(k)\big) - b_i\,G(k)\,\Delta V(k), \qquad p_i^{inj}=\beta_i\cdot p_i^{disp},\;\; \beta_i\in[0,1]
$$

com `ΔV(k) = max(0, V_max−mon(k) − V_ref)`, `V_ref = 1,05 pu`, `b_i` = indicador binário (1 apenas para o líder), `G(k)` = ganho de realimentação, `ε` = parâmetro de convergência derivado da Laplaciana.

**Mapeamento de notação para este documento** (para evitar colisão: este documento já usa `β` como o *ganho* de correção, não como a variável de estado):

| Este documento (`experimento.md`) | Paper-âncora (CBA 2026) |
|---|---|
| `ρ_i` (estado proporcional) | `β_i` |
| `β` (ganho de correção) | `G(k)` |
| `𝟙_{i=líder}` | `b_i` |
| `e_V(k)` | `ΔV(k)` |
| `ε` | `ε` (mesmo símbolo) |

A partir daqui, sempre que este documento citar o paper-âncora, usa a notação do paper-âncora (`β_i`, `G(k)`, `b_i`, `ΔV`) entre aspas ou em bloco de equação isolado, e a notação própria (`ρ_i`, `β`, `e_V`) no restante do texto — nunca misturadas na mesma expressão.

### Confirmação direta da pergunta "por que proporcional, não absoluto"

O paper roda **exatamente** o experimento que responde a essa pergunta, em dois cenários:

- **Cenário 1 (6 GFVs, todas com 120 kVA — capacidade homogênea):** consenso absoluto e proporcional produzem resultados **idênticos** (curtailment de 44,87–44,88% para todas as unidades nas duas estratégias). Confirma que a distinção só importa sob heterogeneidade — o que já era a intuição registrada em §2.1 deste documento, agora com prova numérica.
- **Cenário 2 (6 GFVs, potências distintas: 150, 125, 100, 130, 90, 115 kVA):** consenso absoluto produz curtailment **desigual**, de **30,84% a 53,36%** entre unidades (Tabela 2 do paper); consenso proporcional produz curtailment **quase uniforme**, entre **44,28% e 44,29%** (Tabela 3 do paper) — a dispersão `σ_r` (já definida em §23 da Fase 0 original) cai de algo da ordem de `~8 pontos percentuais` de desvio para `~0,01 ponto percentual`. **Este é o número que deve ancorar a justificativa de `rho_i` como variável de estado em todo o TCC**, substituindo a justificativa apenas normativa que constava antes em §2.1.

A energia total cortada **não muda** entre as duas estratégias (mesma ordem de grandeza) — o ganho do consenso proporcional é inteiramente sobre **como o corte é distribuído**, não sobre **quanto é cortado**. Isso é uma distinção metodológica importante que a Fase 0 deve preservar ao formular H2/H5: falha de comunicação pode piorar a distribuição (`σ_r`) sem necessariamente piorar a energia total cortada — os dois efeitos devem continuar sendo reportados separadamente.

### Elementos que a Fase 0 herda diretamente deste paper (mais precisos que a citação anterior "Paper 2 base value")

- **6 GFVs** nas barras `824, 816, 828, 830, 850, 832`, potências `150, 125, 100, 130, 90, 115 kVA` — esta é a fonte primária exata dos valores já citados em §4.2 deste documento (antes atribuídos de forma mais vaga ao "Paper 2").
- **Topologia de comunicação totalmente conectada** — diferente da topologia "linha com atalho" proposta em §4.3 deste documento. Isso é uma divergência **deliberada e correta**: o paper-âncora não estuda falha de comunicação, então uma topologia densa não é um problema para os objetivos dele; a Fase 0 precisa de uma topologia mais frágil para que C1/C2 sejam informativos (razão já registrada em §4.3). Ambas as escolhas são válidas para seus respectivos objetivos — a divergência deve ser declarada no texto do TCC, não escondida.
- **`V_ref = 1,05 pu`** — confirma o valor já adotado em toda a Fase 0.
- **`ΔV(k) = max(0, V_max−mon(k) − V_ref)`, onde `V_max−mon` é o máximo entre TODOS os barramentos monitorados** (não a tensão local do líder isoladamente) — isso **corrige** a recomendação anterior deste documento em §7.3, que sugeria usar a tensão local do próprio líder. Ver §7.3 revisado e §7.6 (nova) para a consequência disso sob falha de comunicação.

### Ponto crítico ainda não resolvido: seleção do líder é fixa ou dinâmica?

O texto do paper descreve o líder como "o agente que identifica a maior tensão entre os barramentos monitorados... e inicia uma ação corretiva global" — isso é compatível tanto com um líder **fixado uma vez** (quem tinha a maior tensão no início, ou por definição de projeto) quanto com um líder **recalculado a cada ciclo de controle** (quem tem a maior tensão *no momento* de cada novo disparo do controle). O trecho disponível não resolve essa ambiguidade, e **o pesquisador confirmou que precisa checar o código-fonte ou a tese antes de decidir**. Esta é uma decisão estrutural com consequência direta sobre H5 — tratada formalmente em §7.6 (nova).

## 2.1 Bloco "consenso + curtailment + fairness" (R1 Zeraati, R2 Haque, R3 Mai 2019, R4 Mai 2021)

Esses trabalhos assumem comunicação ideal e respondem "por que consenso, e não controle local, para repartir curtailment". Eles fornecem:

- a justificativa normativa de que repartição *proporcional* (não igualitária em kW absoluto) é o critério de justiça adequado quando os agentes são heterogêneos em capacidade — o que **fixa a escolha de `rho_i = P_curt,i / P_available,i` como variável de estado do consenso da Fase 0**, exatamente como já registrado em `Skills/Executor_altGRID_consenso/references/02_consensus_methods.md §2`;
- a estrutura causal `sobretensão → necessidade de controle → consenso → curtailment`, que é o **eixo vertical** da Fase 0 (a falha de comunicação é o eixo horizontal que perturba esse eixo vertical).

Eles **não** contribuem para H1/H3/H4, porque não modelam falha. Servem apenas para justificar por que o baseline C0 é a escolha certa de comparação.

## 2.2 Bloco "PV + consenso + comunicação imperfeita" (R6 Lu 2023, R7 Wang 2023) — núcleo teórico direto

> **Nota sobre integridade do corpus (verificação feita diretamente nos PDFs).** O arquivo `papers/1-s2.0-S037877962030729X-main.pdf`, que o nome sugeria ser R5 (Zhang et al., 2019, IEEE TSMC), **não é esse paper**. Seu conteúdo real é Mai, Haque, Vergara, Nguyen & Pemen (2021), *Adaptive coordination of sequential droop control...*, EPSR 192, 106931 — ou seja, é o **mesmo artigo já catalogado como R4**, salvo em duplicidade sob outro nome de arquivo (o prefixo `S03787796` é a assinatura de ISSN da Electric Power Systems Research no ScienceDirect, não da IEEE TSMC, o que já era um indício). **O PDF de Zhang et al. (2019) não está fisicamente presente em `papers/`.** Isso não invalida R5 como referência (o resumo do corpus, baseado no abstract/DOI, permanece a melhor informação disponível e deve seguir sendo citado dessa forma), mas qualquer citação de equação específica de Zhang et al. deve ser sinalizada como não verificada contra o PDF original até que o arquivo correto seja obtido. Esta lacuna deve ser corrigida antes da submissão do artigo — é uma falha de rastreabilidade bibliográfica, não apenas um detalhe administrativo.

Com essa correção, o bloco que efetivamente fundamenta H1, H2 e H4 com formalismo verificado nos PDFs é:

- **R7 (Wang et al., 2023, IEEE TSG)** — verificado diretamente no PDF — é a referência com o **modelo estocástico mais rigoroso e mais diretamente aplicável a H1**. Eles modelam delay e packet dropout via **nós virtuais**: cada enlace `(i,j)` ganha `ξ−1` nós virtuais Tipo I (cada um representa um passo de atraso discreto `τ`, delay máximo testado = 2 s com resolução `τ=0,2s`, logo `ξ=10`) e 1 nó virtual Tipo II para o mecanismo de *packet dropout* com compensação por checagem (`p_loss = 10%` no experimento deles; um pacote é considerado perdido se o delay excede 2 s). O sistema completo (`n` agentes + `ξμ` nós virtuais, `μ`=nº de enlaces) evolui como uma matriz de transição **linha-estocástica variante no tempo** `M(k)`:
  $$
  Y(k) = Y(k-1)\,M(k-1) + \Delta Q(k), \qquad S(k) = S(k-1)\,M(k-1)
  $$
  e a variável de consenso rastreia uma **média dinâmica** (não um valor estático), com um resultado analítico central que **deve ser citado explicitamente na fundamentação de H1**: o erro de rastreamento se decompõe em um termo de erro inicial que decai exponencialmente e um **termo de erro dinâmico residual que não converge a zero**, proporcional à taxa máxima de variação do processo PV (`Δq_i,max`) e à severidade estrutural da falha (maior delay `ξ`, máximo de perdas consecutivas `b`, maior rota `u` entre dois agentes) — ou seja, a própria teoria já prevê, antes de qualquer simulação, que `e_c^∞` deve crescer com a severidade da falha, dando a H1 uma base analítica e não apenas empírica. Resultado quantitativo direto: sob `10%` de packet dropout e `2s` de delay máximo, o consenso estático de baseline convergiu em `~150` iterações (equivalente a `30s` de ciclo de controle), insuficiente para acompanhar a volatilidade real do PV — saturação de suporte reativo foi observada em um barramento crítico às 2:29 min de simulação, causando sobretensão que o consenso dinâmico proposto evita.
- **R9 (Nojavanzadeh et al., 2022, IEEE TPWRS)** — verificado — fornece a garantia teórica mais forte para **H4/H4′**: o grafo variante no tempo só precisa satisfazer `βI ⪯ L̄(t) ⪯ γI` para *algum* `β,γ>0` desconhecidos do controlador (Laplaciano generalizado limitado, propriedade "scale-free": não exige conhecer `λ₂`, o tamanho da rede, nem cota de delay). O Teorema 1 do paper garante convergência para **qualquer** `β,γ`, **qualquer** tamanho de rede e **qualquer** atraso `τ_ij(t)∈ℝ≥0`, inclusive sob grafos comutados com *dwell-time* mínimo arbitrariamente pequeno. Cenários de teste diretamente análogos aos da Fase 0: enlace com perda intermitente de pacotes (liga/desliga a cada `0,1s`), enlace com ruído multiplicativo `±10%`, falha total de todos os enlaces de um agente + delay de `20ms` nos demais, e desconexão física de um agente (equivalente ao nosso C3). Em todos os casos o observador de tensão se restabelece sem divergência — mas o paper reporta isso qualitativamente (gráficos), sem tabela de erro% vs. taxa de perda, o que é uma lacuna que a Fase 0 pode preencher com seu próprio `e_c(k)` quantificado.
- **R6 (Lu et al., 2023, IJEPES)** — verificado — não modela consenso sob falha estocástica contínua; modela **risco** de violação de tensão como `Risco = ΣΣΣΣ P_i · P_{f,j} · S(i,j)(t,τ)`, onde `P_i` é a probabilidade do cenário de geração FV, `P_{f,j}` é a probabilidade do modo de falha `j` (derivada de taxas de falha reais por tipo de dispositivo — fibra óptica `0,015/km·ano`, sensor/controlador `0,031/ano`, nó agente `0,005/ano`) e `S(i,j)` é a severidade normalizada da violação de tensão. O mecanismo de propagação da falha usa uma **matriz de acessibilidade** `T = f(A + A² + ... + Aⁿ)` (alcançabilidade multi-hop), que é uma forma alternativa e computacionalmente simples de avaliar conectividade — pode ser reportada em paralelo a `λ₂(L)` na Fase 0 sem custo adicional. **Achado central diretamente relevante para H4**: a falha de um **nó agente central/pivô** na topologia produz severidade individual de violação muito maior (`~14%` de desvio de tensão) do que a falha de nós periféricos (`~2–7%`), *mesmo quando a probabilidade de ocorrência do nó central falhar é menor* — ou seja, **risco agregado (prob.×severidade) e severidade pura podem apontar para conclusões opostas** sobre qual falha é "pior". Isso é um refinamento direto de H4: a Fase 0 deve reportar não apenas *se* o grafo particiona, mas *qual* agente é removido para produzir a partição (se é o líder, um nó de alto grau, ou um nó folha), porque a posição topológica do agente falho — não apenas a existência da falha — determina a severidade elétrica.

## 2.3 R8 (Aghaee et al., 2022) — modelagem de falha como extensão futura

Contribui o **modelo probabilístico de packet dropout via cadeia de Markov** (ex.: modelo de Gilbert-Elliott com dois estados, "bom"/"ruim", em vez de perda i.i.d.). Isso é relevante como **extensão futura** do cenário C4: a Fase 0 pode começar com perda i.i.d. Bernoulli (mais simples, mais fácil de justificar estatisticamente com poucas replicações — ver §5.4) e declarar explicitamente que a correlação temporal de rajadas de perda (*burst loss*) fica fora do escopo do TCC — ponto que deve ir na seção de limitações do artigo. Este PDF não foi lido linha a linha (o corpo do texto não estava entre os priorizados na extração), então a citação acima permanece no nível do resumo do corpus, não verificada equação a equação.

## 2.4 R10 (Wang et al., 2026) — benchmark de resiliência mais recente, com limiar numérico citável

Verificado diretamente no PDF (validação dupla: MATLAB/Simulink **e** hardware-in-the-loop real em OPAL-RT Lab 5707, com resultados consistentes entre os dois ambientes). Testam exatamente os modos de falha que a Fase 0 propõe, em uma microrrede ilhada de 4 DGs: (a) grafo intacto; (b) **falha de um único enlace** em `t=2s` (grafo permanece fortemente conexo) — converge, apenas com tempo de acomodação maior; (c) **desconexão física de um agente** em `t=3s` (teste de plug-and-play, análogo ao nosso C3 sem recuperação) — os 3 agentes restantes redistribuem o compartilhamento de potência na proporção correta entre si; (d) **delay em todos os enlaces simultaneamente**, testado em `200ms`, `250ms` e `300ms`. O resultado quantitativo mais citável do corpus inteiro para a discussão da Fase 0 está aqui: o sistema permanece estável (com oscilações visíveis) até `250ms` de atraso e **torna-se instável a partir de `300ms`** — um limiar de delay crítico determinado empiricamente e replicado em hardware real. Isso não testa exatamente o que a Fase 0 testa (a Fase 0 não modela delay, conforme decisão explícita da Seção 18 do documento original), mas fornece a evidência mais forte do corpus de que **existe, de fato, uma fronteira nítida entre degradação tolerável e colapso do controle** — exatamente o tipo de "limiar de tolerância" que H3 e a Seção 26 da Fase 0 original hipotetizam para o caso de perda de mensagens/particionamento, e que a Fase 0 deve buscar de forma análoga (não em `ms` de delay, mas em `%` de enlaces perdidos ou em `λ₂(L)`).

## 2.5 R0 (Giacomini, 2025) — base metodológica para a variante Leader-Follower

Fornece o sistema elétrico (IEEE 34 barras) e a arquitetura de consenso líder-seguidor com correção de tensão, já herdada pela skill `Executor_altGRID_consenso`. A Fase 0 **não reimplementa** essa base — ela a instancia com a variável de estado *proporcional* (`rho_i`, não potência absoluta) e adiciona a camada de falha. R0 é, portanto, a referência-âncora da variante **Leader-Follower** desta Fase 0.

## 2.5′ Kitso et al. (2025) — base para a variante Leaderless, agora verificada diretamente no PDF

Referência: Kitso, M.; Priambodo, B. I.; Alpízar-Castillo, J. J.; Ramírez-Elizondo, L. M.; Bauer, P. (2025). *Coordination of Multiple BESS Units in a Low-Voltage Distribution Network Using Leader–Follower and Leaderless Control*. **Energies**, 18(17), art. 4566. DOI: `10.3390/en18174566`. O PDF foi adicionado a `papers/` e lido diretamente (Seções 2, 4 e 5 do artigo) — o que segue substitui a citação indireta anterior (via `Skills/Paper_2_..._BESS.md`) por formalismo verificado equação a equação.

**Confirmação direta da razão de usar consenso proporcional (não absoluto).** Testam a rede CIGRE LV de 18 barras com 6 unidades PV+BESS de potências nominais heterogêneas (`P_BESS ∈ {5.5, 4, 6, 5.5, 4.5, 6} kW`, Tabela 2 do paper). A variável de consenso é um **fator de utilização adimensional** `U_i`, não a potência em kW. A potência de referência de cada agente só é obtida depois, escalada pela capacidade nominal daquele agente:

$$
P_{ref,i}(k) = P_{nom,i}\times U_i(k) \qquad \text{(Eq. 10, líder-seguidor; Eq. 16, leaderless — mesma forma nas duas)}
$$

Os autores justificam isso textualmente exatamente pela razão que motivou a escolha de `rho_i` na Fase 0: *"the available capacity of each BESS unit does not affect their power contributions [to the consensus variable]"* — cada agente contribui de forma proporcional à sua própria capacidade, não em valor absoluto igual para todos. Isso **confirma e ancora formalmente** a escolha já feita em §2.1/§4.5 deste documento (`rho_i = P_curt,i/P_available,i`, `P_curt,i = rho_i · P_available,i`) — a mesma lógica, aplicada a curtailment de PV em vez de carga/descarga de BESS.

**Formalização exata das duas arquiteturas no paper (relevante para §4.4–4.5):**

- **Leader-Follower (Eq. 7–9 do paper):** o líder **não mistura com vizinhos** — atualiza seu próprio `U_leader` por uma lei puramente local, integrando o erro de tensão do seu próprio barramento: `U_leader(k) = U_leader(k-1) + G_ov·[V_n(k)-1.05]` sob sobretensão (ou termo simétrico com `G_un` sob subtensão; `U_leader=0` dentro da faixa). Os seguidores, por sua vez, **não têm termo de correção próprio** — apenas rastreiam o valor do líder por média ponderada nos vizinhos: `U_i(k) = Σ_j C_ij(k)·U_j(k-1)`, com pesos `C_ij(k) = A_ij(k-1)/Σ_j A_ij(k-1)` (linha-normalizados). É uma estrutura de **duas leis separadas** (líder: integra localmente; seguidor: só rastreia), não uma única equação de mistura-mais-correção.
- **Leaderless (Eq. 12–14 do paper):** todo agente calcula seu próprio fator de utilização local a partir da tensão do seu barramento, `U_i(k) = U_i(k-1) + G_ov·[V_i(k)-1.05]` sob sobretensão local — estruturalmente idêntico ao termo `e_{V,i}` já proposto em §4.5 deste documento. Um detalhe que a Fase 0 **não tinha** e vale adotar: quando a tensão volta para dentro da faixa, o paper não zera `U_i` instantaneamente, usa um **decaimento** `U_i(k) = 0.5·U_i(k-1)` (Eq. 12, terceiro ramo) — evitando que a correção fique "presa" em um valor não-nulo obsoleto assim que a sobretensão local é resolvida. Depois do cálculo local, os valores são compartilhados por consenso puro (Eq. 14, forma idêntica à Eq. 3/5 já citada), sem termo de correção adicional na mistura.

**Decisão de adaptação para a Fase 0 (deve ficar declarada no texto do TCC).** A formulação de `§4.5` deste documento usa uma **única equação de mistura-mais-correção** para as duas arquiteturas (herdada da convenção de R0/Giacomini, já adotada pela skill `Executor_altGRID_consenso`), não a estrutura de duas-leis-separadas de Kitso. As duas formulações são consistentes em espírito (líder/agentes locais corrigem por erro de tensão; a informação se propaga pelo grafo por consenso), mas **não são idênticas linha a linha**. Recomendação: manter a equação única de `§4.5` (mais simples de implementar e já compatível com a base de código herdada do mestrado), citar Kitso como fundamentação conceitual da dicotomia leader-follower/leaderless e da normalização por capacidade — e declarar explicitamente, no texto do TCC, que a Fase 0 não reproduz a mecânica exata de Kitso (duas leis separadas, termo de decaimento), é uma adaptação. Se o tempo permitir, considerar o termo de decaimento (`0.5·U_i(k-1)` quando `V_i` volta à faixa) como refinamento da correção local do Leaderless — evita um viés sistemático em que `ρ_i` fica "travado" acima do necessário depois que a sobretensão local já foi resolvida.

**Correção de uma imprecisão da nota anterior deste documento:** a "regra de balanceamento de SOC" do leaderless de Kitso, mencionada antes como algo a omitir, é na verdade um **filtro de sobreposição baseado em regras** (Eq. 15): quando o SOC de um agente se aproxima dos limites e há potência líquida (`PV−carga`) disponível no sinal certo, o filtro substitui o valor de consenso por um comando derivado diretamente do desequilíbrio local de potência, para manter prontidão de SOC. Não é uma regra de equalização entre agentes — é um *override* local por agente. Continua não aplicável à Fase 0 (sem BESS, sem SOC), e a omissão continua correta, mas a descrição anterior ("balanceamento de SOC") estava imprecisa e é substituída por esta.

## 2.6 Síntese da leitura crítica

| O que a Fase 0 precisa | De onde vem, com que grau de reuso |
|---|---|
| Rede elétrica, infraestrutura AltDSS, alimentador exato | **Giacomini Jr, Seraphim Rodrigues, Paredes & Cebrian (2026, CBA — §2.0)** — âncora primária, verificada equação a equação e por código-fonte; `ieee34Mod3ORIGINAL_CBA.dss` |
| Variável de consenso (`rho_i`≡`β_i`) e regra proporcional, equações exatas do controlador LF | Idem — Eq. (1)/(2) do paper, mapeamento de notação em §2.0; R1–R4 como justificativa normativa complementar |
| Regra de `ε`, critério de parada, `lider_idx`, ganhos numéricos de partida | Código de referência (§2.0/§7.6/§7.7) — substitui as regras teóricas propostas em versões anteriores deste documento |
| Arquitetura Leader-Follower | Giacomini Jr, Seraphim Rodrigues, Paredes & Cebrian (2026, CBA) — reuso direto, equação e código verificados |
| Arquitetura Leaderless | Kitso et al. (2025), Energies 18(17):4566, DOI `10.3390/en18174566` — **PDF verificado em `papers/`**, formalismo confirmado equação a equação (§2.5′); adaptação de domínio (BESS→PV) necessária e declarada |
| Definição de falha de enlace / particionamento | Definição própria da Fase 0, com apoio empírico verificado de R6, R9, R10 |
| Modelo estocástico de packet loss (C4) | R7 (Wang 2023, verificado: nós virtuais + matriz row-stochastic variante no tempo) como referência formal para o *bound* de erro; R8 como nota de limitação (i.i.d. vs. Markov) |
| Condição teórica para H4 (conectividade conjunta / grafo limitado) | R9 (verificado, Teorema 1: Laplaciano generalizado limitado, *scale-free*) — deve ser citada explicitamente na discussão, não só nos resultados |
| Refinamento de H4 (posição topológica do nó falho importa) | R6 (Lu 2023, verificado: severidade individual vs. risco agregado divergem conforme o nó falho é central ou periférico) |
| Evidência de limiar nítido degradação→colapso | R10 (verificado: `250ms` estável/oscilante → `300ms` instável, validado em HIL) — usada para posicionar H3 frente ao estado da arte |
| **Lacuna identificada** | R5 (Zhang et al., 2019) está catalogado no corpus mas o PDF correspondente não existe em `papers/` — ver nota em §2.2 |

---

# 3. Inferência científica das hipóteses

As hipóteses H1–H4 da Fase 0 estão formuladas qualitativamente. Aqui elas são **operacionalizadas**: cada uma recebe uma variável mensurável, uma predição funcional testável e um critério de refutação. Isso é obrigatório antes de gerar qualquer dado, porque sem isso "avaliar o impacto" não é falsificável.

## H1 — Degradação da comunicação aumenta erro e/ou tempo de convergência

**Formalização.** Seja `e_c(k)` o erro de consenso já definido na Fase 0 (§20.1) e `N_iter(ε)` o número de iterações até `e_c(k) < ε` sustentado por `m` iterações consecutivas. Definindo uma variável ordinal de severidade estrutural `s ∈ {C0, C1, C3, C4(p)}` (C2 é excluído aqui porque sob partição não existe mais um único consenso global — ver H4), a predição de H1 é:

$$
s_1 \preceq s_2 \;\Rightarrow\; \mathbb{E}[N_{iter}(s_1)] \le \mathbb{E}[N_{iter}(s_2)]
\quad\text{e}\quad
\mathbb{E}[e_c^{\infty}(s_1)] \le \mathbb{E}[e_c^{\infty}(s_2)]
$$

onde `≼` é uma ordem parcial de severidade (C0 ≺ C1 ≺ C3 ≺ C4(p) para p crescente, por construção dos cenários).

**Critério de refutação.** H1 é refutada se cenários com maior severidade estrutural (mais enlaces perdidos, maior `p_loss`) não produzirem `N_iter` ou `e_c^∞` estatisticamente maiores que C0, dentro do intervalo de confiança das replicações Monte Carlo de C4.

**Observação metodológica importante.** H1, tal como escrita na Fase 0, é a hipótese "óbvia" — a própria Seção 26 do documento original reconhece isso. Ela deve ser tratada como **verificação de sanidade do experimento**, não como resultado principal do TCC. Se H1 falhar (falha não degrada nada), isso invalida a instrumentação, não a física do problema.

**Extensão para as duas arquiteturas.** H1 deve ser verificada **separadamente** para Leader-Follower e Leaderless — ambas devem degradar com a severidade estrutural, mas não necessariamente na mesma magnitude nem pela mesma razão. A pergunta interessante não é mais só "H1 se sustenta?", mas **"H1 se sustenta igualmente nas duas arquiteturas, ou uma delas amplifica/absorve a degradação de forma diferente?"** — essa comparação é resolvida por H5 (§ abaixo), não por H1 isoladamente.

## H2 — Falhas de comunicação distorcem a distribuição do esforço de controle

**Formalização.** Usar a métrica de dispersão já definida em §23:

$$
\sigma_r(k) = \sqrt{\frac{1}{N}\sum_i (r_i(k) - \bar r(k))^2}, \qquad r_i = \frac{P_{curt,i}}{P_{available,i}}
$$

A predição de H2 é que `σ_r` no estado final (ou no instante de parada por saturação de iterações) seja estritamente maior sob C1/C2/C3/C4 do que sob C0, **e que o aumento de `σ_r` não seja monotônico simples em relação a `N_iter`** — ou seja, é possível ter convergência "rápida" para um consenso local incorreto (caso C2, partição) com `σ_r` alto porém `e_c` baixo *dentro de cada partição*. Este é o ponto mais interessante de H2: **erro de consenso local baixo pode coexistir com desigualdade de curtailment alta entre grupos**, porque `e_c` mede apenas dispersão dentro do grafo observável, não do sistema completo.

**Predição adicional testável.** Sob C2 (particionamento), `σ_r` calculado **por partição** deve ser baixo (cada grupo converge entre si), mas `σ_r` calculado **globalmente** deve ser alto. Registrar as duas versões da métrica é obrigatório — omitir isso torna H2 não verificável no cenário mais informativo (C2).

**Extensão para as duas arquiteturas.** Sob Leader-Follower, a previsão acima assume implicitamente que **uma das partições** (a que não contém o líder) fica sem qualquer termo de correção ativo — logo `ρ_i` nessa partição não evolui de forma dirigida por tensão, apenas mistura os valores que já tinha. Sob Leaderless, **ambas** as partições continuam recebendo correção local (§ H5), então a predição precisa ser refeita: `σ_r` por partição deve permanecer baixo em ambos os grupos, e a diferença mais informativa deixa de ser "dentro vs. fora da partição do líder" e passa a ser simplesmente a diferença natural de `ρ̄` entre grupos com necessidades elétricas locais distintas.

## H3 — Degradação do consenso não implica violação elétrica imediata

**Formalização.** H3 propõe a existência de uma região no espaço `(severidade da falha, desempenho elétrico)` onde:

$$
\sigma_r(s) \gg \sigma_r(C0) \quad \text{mas} \quad V_{max}(s) \le V_{lim}
$$

Isso é testável construindo, para cada cenário, o par ordenado `(σ_r, V_max)` e verificando se existe uma faixa de severidade em que `V_max` permanece abaixo do limite apesar de `σ_r` já ter se afastado significativamente do caso ideal. Esta é a hipótese cientificamente mais valiosa da Fase 0 (reconhecido explicitamente em §26 do documento original) porque **não é previsível a priori pela teoria de consenso isolada** — depende da sensibilidade elétrica real do alimentador (`∂V/∂P` local), que só a simulação em OpenDSS revela.

**Por que isso é plausível fisicamente, não apenas hipotético.** A rede de distribuição tem margem: o limite de 1,05 pu não é atingido no primeiro kW de desvio de curtailment mal distribuído. Existe, por construção física, uma folga entre "consenso subótimo" e "violação de tensão". A pergunta de pesquisa não é *se* essa folga existe, mas **quão larga ela é** e se ela é suficiente para absorver as severidades de falha definidas em C1–C4. Isso deve ser reportado como uma **curva de margem**, não como um único ponto de corte.

**Critério de refutação.** H3 é refutada (para o feeder e a configuração de PVs escolhidos) se toda condição de falha testada em que `σ_r` se afasta de forma mensurável do baseline também produzir violação de `V_max`. Nesse caso, a conclusão do TCC muda de "existe folga operacional" para "a folga, se existe, é menor que a menor perturbação testada" — o que ainda é um resultado publicável, apenas com framing diferente.

**Extensão para as duas arquiteturas.** A pergunta mais forte que o desenho `2×5` permite responder não é apenas "existe folga?", mas **"a largura da folga depende da arquitetura?"**. Construir a Figura `06_margem_H3` (§5.5) com pontos coloridos por arquitetura é o teste direto disso: se os pontos Leaderless ficarem sistematicamente mais à direita e ainda abaixo de `V_lim` do que os pontos Leader-Follower na mesma severidade de falha, isso é evidência de que a arquitetura leaderless *amplia* a região de tolerância descrita em H3 — o resultado mais forte que o TCC poderia produzir, porque conecta diretamente a escolha de arquitetura a uma propriedade de segurança elétrica mensurável.

## H4 — Particionamento produz comportamento estruturalmente distinto

**Formalização.** Usar `λ₂(L)`, a conectividade algébrica:

$$
\lambda_2(L) > 0 \;\Leftrightarrow\; \text{grafo conexo}, \qquad \lambda_2(L) = 0 \;\Leftrightarrow\; \text{grafo desconexo}
$$

A predição de H4 tem duas partes que devem ser testadas separadamente, e uma delas agora depende explicitamente da arquitetura:

1. **Parte estrutural, arquitetura-agnóstica (teoria de grafos, não precisa de simulação elétrica para ser verificada):** sob C1 (enlace perdido, grafo ainda conexo), `λ₂(L) > 0` e o consenso proporcional converge para um único valor de equilíbrio partilhado por todos os 6 agentes, **em qualquer uma das duas arquiteturas** (a mistura de `ρ_i` via `εL` é idêntica em Leader-Follower e Leaderless — só o termo de correção difere, ver §4.5). Sob C2 (particionamento), `λ₂(L) = 0` e emergem **dois pontos de equilíbrio distintos**, um por componente conexo — isso também vale para as duas arquiteturas, é consequência pura da Laplaciana, não do controlador.
2. **Parte causal, arquitetura-dependente (só a simulação revela, e é exatamente o que distingue as duas arquiteturas):** o "comportamento distinto" de C2 se traduz eletricamente em quê? Esta pergunta **não tem mais uma resposta única** — ela se bifurca conforme a arquitetura, e essa bifurcação é o conteúdo da hipótese H5 (nova, ver abaixo), que deve ser lida como a continuação direta e arquitetura-explícita de H4.

**Extensão direta de H4, apoiada em R9 (Nojavanzadeh et al.):** para o cenário C3 (falha temporária, com recuperação), a teoria de sistemas chaveados prediz que a **conectividade conjunta ao longo do tempo** (não a conectividade instantânea) é a condição suficiente para convergência assintótica. A Fase 0 pode formular uma sub-hipótese H4′ explícita:

> H4′ — Se a soma cumulativa dos grafos `G(t)` ao longo da janela de simulação permanece conjuntamente conexa, o consenso proporcional recupera convergência para o mesmo ponto de equilíbrio de C0 após o retorno do agente, independentemente da duração da falha temporária (dentro dos limites testados).

Esta sub-hipótese é a que dá à Fase 0 uma contribuição teoricamente ancorada, e não apenas uma constatação empírica isolada. Ela também deve ser lida como arquitetura-agnóstica na sua forma pura (é uma propriedade da matriz `(I-εL(t))`), mas sua **manifestação elétrica** durante a janela de falha (§ H5) depende de qual agente falhou e em qual arquitetura.

## H5 — A arquitetura do consenso determina a robustez à falha estrutural (hipótese nova, específica desta revisão)

Esta é a hipótese que nasce diretamente da decisão de comparar Leader-Follower e Leaderless, e é o resultado cientificamente mais forte que o desenho `2 arquiteturas × 5 cenários` pode produzir — mais forte do que H1–H4 tomadas isoladamente, porque conecta uma escolha de *projeto de controlador* a uma propriedade de *robustez estrutural*, não apenas a uma magnitude de erro.

**Mecanismo causal.** Nas duas arquiteturas (formalizadas em detalhe em §4.4–4.5), a regra de mistura de `ρ_i` via `εL(t)` é idêntica; a única diferença é **onde o termo de correção de tensão é aplicado**:

- **Leader-Follower:** o termo `β·e_V(k)` existe em **um único** índice `i = líder`. Se a falha isola o líder do restante do grafo (C2 com o líder em uma partição; ou C3 com o líder sendo o agente indisponível), **toda a rede perde o único ponto de correção ativa** — os agentes continuam misturando `ρ_i` entre si, mas sem qualquer termo dirigido por tensão, o valor de equilíbrio da mistura fica congelado no que já existia, não há resposta a uma nova sobretensão.
- **Leaderless:** o termo `β·e_{V,i}(k)` existe em **todo** agente `i`, calculado a partir da tensão **local** de cada um (`e_{V,i}(k) = max(0, V_i(k) - V_lim)`, não uma tensão monitorada única). Uma falha que isola qualquer agente (líder conceitual ou não) remove apenas a correção *daquele* agente — os demais, em qualquer partição, continuam corrigindo localmente.

**Predição formal.** Seja `m` o agente removido/isolado por uma falha (C2 ou C3), e `G_A`, `G_B` as duas partições resultantes (`m ∈ G_A`). Para Leader-Follower com líder `ℓ`:

$$
\ell \in G_B \;\Rightarrow\; \forall i \in G_B,\; \dot\rho_i \text{ não responde a } e_V \text{ durante a falha} \;\Rightarrow\; \text{risco de violação em } G_B \text{ se houver sobretensão lá}
$$

Para Leaderless, a mesma condição **não produz** perda de correção em nenhuma partição:

$$
\forall i \notin \{m\},\; \dot\rho_i \text{ continua respondendo a } e_{V,i} \text{ localmente, em ambas as partições}
$$

**Critério de refutação.** H5 é refutada se, sob C2/C3 com o líder isolado, a partição sem líder em Leader-Follower **não** apresentar degradação de `V_max` (ou de `σ_r`) mensuravelmente pior do que a mesma partição sob Leaderless. Também é parcialmente refutada — de forma cientificamente interessante — se Leaderless apresentar **outra** patologia compensatória (ex.: oscilação por sobreposição de múltiplas correções locais simultâneas, `N_iter` maior por excesso de graus de liberdade ativos) que a torne não estritamente superior, apenas *diferente*. Este segundo resultado (trade-off, não vitória absoluta de uma arquitetura) é tão publicável quanto o primeiro — é exatamente o padrão de resultado que `Skills/Paper_2..._BESS.md §43` já pede para a comparação de arquiteturas no mestrado ("o objetivo não é provar que existe um único método superior... é identificar trade-offs").

**Sub-hipótese H5a — falha do próprio líder é o pior caso estrutural de Leader-Follower.** Dentro de C3 (falha temporária de agente único), executar o cenário com `m = líder` e, separadamente, com `m ≠ líder` (um agente qualquer não-líder). A predição é que, em Leader-Follower, `m = líder` produz degradação de `V_max`/`σ_r` **estritamente maior** que qualquer `m ≠ líder` — porque a falha do líder é a única que desliga a correção de tensão da rede inteira, enquanto a falha de um não-líder apenas remove um nó da malha de mistura, sem desligar a correção. Em Leaderless, a predição é que a identidade de `m` importa menos (a variação entre `m` diferentes deve ser pequena e dominada pela posição elétrica de `m`, não pelo seu papel na arquitetura de comunicação) — replicando, agora sob um mecanismo causal explícito, o achado de R6 (Lu et al., 2023, §2.2) de que a posição topológica do nó falho determina a severidade.

## 3.1 Resumo do grafo de inferência

```text
H1 (verificação de sanidade, testada em cada arquitetura)
   └─ condição necessária para H2, H3, H4, H5 serem interpretáveis

H2 (distorção do esforço, testada em cada arquitetura)
   └─ pré-requisito mensurável para H3

H3 (núcleo científico "vertical" do TCC: existe folga elétrica?)
   └─ depende de H1 e H2 já estarem caracterizados
   └─ comparar a LARGURA da folga entre arquiteturas é o resultado mais forte

H4 (estrutural, λ2, arquitetura-agnóstica)
   └─ explica *que* C2 produz dois equilíbrios, por teoria de grafos pura
   └─ H4' liga-se diretamente a C3 e à literatura de grafos variantes no tempo (R9)
   └─ NÃO explica sozinha o que acontece eletricamente em cada partição — isso é H5

H5 (núcleo científico "horizontal" do TCC: a arquitetura importa? — NOVA)
   └─ explica *por que* C2/C3 se comportam diferente conforme Leader-Follower ou Leaderless
   └─ H5a isola a falha do líder como pior caso estrutural de Leader-Follower
   └─ é a hipótese que dá ao TCC uma contribuição de projeto de controlador,
      não apenas de caracterização de falha
```

---

# 4. Modelo formal do experimento

Esta seção fixa, sem ambiguidade, o que a skill `Executor_altGRID_consenso` exige antes de qualquer execução: variável de estado, grafo, regra de atualização, regra de falha, critério de parada.

## 4.1 Camadas — decisão final: **um único arquivo `.py`**, organizado internamente por seção

**Decisão do pesquisador nesta revisão:** o experimento será implementado como **um único arquivo Python monolítico**, no mesmo espírito do código de referência (§2.0) — não como módulos/pacotes separados. A separação de responsabilidades abaixo continua valendo, mas como **blocos de funções dentro do mesmo arquivo** (delimitados por comentários `# ====...====`, como já faz o código de referência), não como diretórios/arquivos distintos:

```text
# ELÉTRICO         IEEE 34 barras, 6 PVSystems (§4.2/§4.2.1), powerflow (AltDSS)
# COMUNICAÇÃO      grafo G(t), matriz A(t), Laplaciana L(t), injeção de falhas
# CONTROLE         consenso proporcional sobre rho_i
#                    - corrigir_leader_follower(...)   (correção em 1 agente)
#                    - corrigir_leaderless(...)         (correção local em todos)
# SIMULAÇÃO        executor de snapshots, cenários C0-C3 x {LF, Leaderless}  [C4 fora de escopo, ver §7.4]
# MÉTRICAS         e_c, N_iter, sigma_r, Vmax, violações, lambda_2
# RESULTADOS       csv longo + figuras + manifest
```

A arquitetura (`LF` | `leaderless`) continua sendo um **parâmetro do experimento**, não uma função duplicada — as duas variantes compartilham a mesma mistura de consenso (`εL`), o mesmo grafo, o mesmo executor de snapshots e a mesma camada de medição; divergem apenas na função que calcula o termo de correção de tensão (§4.5). Implementá-las como duas funções que respeitam uma interface comum (`corrigir_leader_follower(rho, V, lider_idx) -> vetor`, `corrigir_leaderless(rho, V) -> vetor`) dentro do mesmo arquivo é o que torna a comparação causalmente limpa — trocar a implementação inteira do controlador entre as duas arquiteturas reintroduziria exatamente o tipo de confundimento que a skill proíbe. Isso é uma restrição de **disciplina interna do arquivo**, não de separação física em módulos.

**Trade-off aceito conscientemente:** um arquivo único é mais rápido de escrever agora e mais próximo do código de referência já validado pelo grupo, mas custa mais para reaproveitar diretamente como "motor comum" no Paper 2 do mestrado (§8) — se e quando o mestrado precisar reaproveitar partes deste código, a refatoração em módulos fica para depois, não é objetivo desta primeira implementação.

### 4.1.1 Convenção de código: otimizar para leitura, não para desempenho (decisão do pesquisador, vale para todo o arquivo)

**Regra explícita, válida para toda a implementação, sem exceção:** o código deve ser otimizado para **leitura e compreensão**, não para desempenho computacional — mesmo que isso custe mais linhas. Isso é uma inversão deliberada em relação à convenção geral de engenharia de software (código enxuto, sem comentários redundantes, nomes curtos quando o contexto já explica); aqui vale o oposto, porque o código **é** um artefato do TCC, não só uma ferramenta descartável — precisa ser lido, entendido e defendido por quem não o escreveu.

Consequências práticas:

- **Funções e variáveis com nomes longos e explícitos**, não abreviações — `potencia_disponivel_por_pv` em vez de `Pdisp`, `fator_proporcional_consenso` em vez de `rho`, `agente_lider_indice` em vez de `lider_idx`. O código de referência (§2.0) já segue parcialmente essa convenção (nomes em português, razoavelmente descritivos) — a Fase 0 deve ir além dele nesse aspecto, não replicar as abreviações que ele ainda usa (`Vmax_dgs`, `P_apl`, `eps`).
- **Quando uma variável representa um símbolo já formalizado neste documento** (`ρ_i`, `ε`, `β`, `S_i`, `V_lim`, `e_c(k)`), o nome da variável no código deve ser descritivo, e um comentário curto ao lado deve declarar a correspondência (`# rho_i (Eq. §4.5) — fracao de curtailment aplicada por agente`), para que o código continue rastreável até a formalização matemática sem exigir que o símbolo compacto apareça literalmente no nome da variável.
- **Funções pequenas e nomeadas pelo que fazem**, não uma função grande fazendo várias coisas — preferir `calcular_violacao_acumulada_por_agente(...)` e `determinar_lider_por_criterio_B(...)` como funções separadas e explícitas, mesmo dentro do arquivo único (§4.1), em vez de uma função `preparar_experimento(...)` monolítica que faz tudo isso implicitamente.
- **Comentários explicando o "porquê", não só o "o quê"**, especialmente nos pontos já identificados como armadilhas neste documento (ex.: por que `SOC`/tempo não avança dentro do laço de consenso, por que o critério de parada é elétrico e não por `e_c`, por que o líder é fixo) — um comentário nesses pontos evita que uma futura edição reintroduza um erro já mapeado.
- **Evitar vetorização "esperta" quando um laço explícito é mais claro** — `numpy` deve ser usado onde já é natural (ex. produto matricial `L @ rho`), mas não para espremer o código em uma linha à custa de legibilidade. Um `for` explícito com nomes claros é preferível a uma compreensão de lista aninhada difícil de ler.
- **Docstring curta em toda função**, descrevendo o que ela recebe, o que retorna, e — quando aplicável — a qual equação/seção deste documento ela corresponde.

Esta convenção **prevalece sobre qualquer orientação geral de estilo de código mais terso** que possa ser aplicada por padrão em outros contextos — está registrada aqui precisamente para não ser esquecida quando a implementação começar.

Esta é literalmente a arquitetura já sugerida em `Fase 0 — Idealização.md §29`, e é **compatível por construção** com a arquitetura de "motor comum" que o `Roteiro_Macro_Papers_2_3_4` pede para o mestrado (rede / curvas / PVs / BESS / controle / protocolo / cenários / métricas → montar → validar → executar snapshots → controlar → registrar → exportar → plotar). A Fase 0 deve ser implementada como o **primeiro protocolo de controle** desse motor comum, não como um script isolado.

## 4.2 Rede elétrica e posicionamento dos PVs — atualizado com o código de referência (§2.0/§7.6)

**Alimentador exato:** `IEEE34bus/ieee34Mod3ORIGINAL_CBA.dss` — não o `ieee34Mod3ORIGINAL.dss` genérico citado em versões anteriores deste documento. É o arquivo específico já usado pelo código de referência, já presente no repositório.

**Recomendação revertida nesta revisão: 6 agentes, não 5.** O código de referência confirma que o paper-âncora e o `Paper 2` do mestrado usam os **6** GFVs abaixo, na ordem exata em que aparecem em `lista_barras_DGs` no código (a ordem importa: índice 0 é o líder, `lider_idx=0`):

| Índice | PV | Barra | Potência (kVA) | Papel elétrico |
|---|---|---|---|---|
| 0 | PV1 | 824 | 150 | líder no código de referência (escolhido por posição na lista, não por critério elétrico — ver §7.6) |
| 1 | PV2 | 816 | 125 | próximo à origem |
| 2 | PV3 | 828 | 100 | intermediário |
| 3 | PV4 | 830 | 130 | intermediário |
| 4 | PV5 | 850 | 90 | nó de passagem de baixa impedância entre 814 e 816 |
| 5 | PV6 | 832 | 115 | eletricamente mais fraco (lateral monofásica a jusante) |

**Por que reverter a recomendação de 5→6 agentes:** a versão anterior deste documento recomendava manter 5 (aderência literal a `Fase 0 — Idealização.md §8`), omitindo `850`. Com o código de referência em mãos, o custo de manter 5 subiu — exigiria reescrever a lista de barras, os índices do código, e potencialmente o `lider_idx`, sem nenhum ganho compensador. **Reuso direto do código já validado pelo grupo (menor risco de erro de implementação, comparabilidade imediata com os resultados já publicados) supera a aderência literal ao número "5" do documento de idealização original.** Esta reversão de recomendação deve ser confirmada pelo pesquisador antes da implementação — se confirmada, o `§8 da Fase 0 original` deve ser tratado como uma estimativa inicial superada por uma decisão de engenharia posterior, não como um requisito rígido.

Se o pesquisador preferir manter 5 agentes apesar do exposto, a única mudança necessária é remover `850` da lista e ajustar `lider_idx` de acordo (o líder não pode ser o agente removido).

Potências FV: mantidas nos valores exatos do código de referência (tabela acima), **escaladas por um fator `λ`** desde o início — mesmo que a Fase 0 não faça varredura de Hosting Capacity, declarar `P_PV,i = λ · P_PV,i^base` com `λ=1` fixo deixa a Fase 0 pronta para virar um cenário `Bloco D` do Paper 2 sem reescrever a definição de PV.

## 4.2.1 Elemento elétrico: `PVSystem` — decisão revertida para continuidade com o código de referência

**Decisão final (revertida nesta revisão):** os 6 GFVs são modelados como `PVSystem`, não `Generator`. Regra aplicada pelo pesquisador: *"se os códigos anteriores usavam PVSystem, então deixe-o."* O código de referência (§2.0) usa `altdss.PVSystem.new(...)` com `Irradiance`, `Pmpp`, `EffCurve`, `PTCurve`, `Daily`, `kVA` — a Fase 0 segue essa mesma convenção, por continuidade direta e comparabilidade com os resultados já publicados. A hipótese de usar `Generator` (registrada brevemente nesta revisão por permitir comando direto e simultâneo de `kW`/`kvar`) foi considerada e descartada — não pela hipótese estar errada, mas porque a regra de precedência do pesquisador (seguir o código já existente sempre que ele já resolveu o problema) tem prioridade sobre a conveniência de controle mais direto.

**Consequência:** a nota de §7.7 sobre `kVA` (usado no código de referência) vs. `pctPmpp` (preferido pela skill `Executor_altGRID_consenso`) **volta a valer como estava antes desta revisão** — é uma tensão real entre continuidade de código e aderência ao padrão da skill, e a recomendação permanece: seguir `kVA` por continuidade com o paper-âncora, migrar para `pctPmpp` só se uma necessidade específica exigir (ex. `Q` no Paper 3). Se o despacho `Q` explícito do Paper 3 do mestrado eventualmente exigir controle mais direto que o `PVSystem` ofereça com dificuldade, a opção `Generator` fica registrada aqui como alternativa já avaliada, não como algo a redescobrir.

## 4.3 Grafo de comunicação — topologia nominal C0 — estendida para 6 nós

**Atualizada nesta revisão para 6 agentes** (§4.2). Rotulando os agentes na mesma ordem do código de referência (`1=824` [líder], `2=816`, `3=828`, `4=830`, `5=850`, `6=832`):

$$
G_0 = (V, E_0), \quad V = \{1,2,3,4,5,6\}, \quad E_0 = \{(1,2),(2,3),(3,4),(4,5),(5,6),(2,5)\}
$$

Um grafo em "linha com um atalho" (não completo, não anel puro — e deliberadamente **diferente** da topologia totalmente conectada usada no código de referência, §2.0) continua sendo a escolha correta para a Fase 0, pelas mesmas três razões já registradas (grafo completo tornaria C1 trivial; anel puro exigiria 2 remoções para particionar). A generalização para 6 nós preserva a propriedade mais importante — **isolar com uma única remoção de enlace** os dois cenários C1 (ainda conexo) e C2 (particionado):

- **C1** — remover o atalho `(2,5)`: o grafo permanece conexo via a linha `1–2–3–4–5–6`.
- **C2** — remover `(1,2)`: particiona em `{1}` (o líder, sozinho) e `{2,3,4,5,6}` — o caso mais informativo possível para H5, porque isola o líder **completamente**, não apenas em um subgrupo pequeno.

**Laplaciana nominal:**

$$
L_0 = D_0 - A_0, \qquad \lambda(L_0) = \{0,\; \lambda_2,\; \lambda_3,\; \lambda_4,\; \lambda_5,\;\lambda_6\}, \quad \lambda_2 > 0
$$

O valor numérico de `λ₂(L₀)` deve ser calculado e reportado como parte dos metadados do experimento (não é um valor a "escolher", é uma consequência da topologia acima — deve ser computado com `numpy`/`networkx` e registrado no manifest).

## 4.4 Duas arquiteturas de correção de tensão — especificação obrigatória e não-conflacionável

A skill `Executor_altGRID_consenso` é explícita: "Do not conflate these algorithms... Record the state variable, units, graph, leader definition, epsilon, gains, limits, and stopping rule for every case." As duas arquiteturas compartilham **tudo** exceto o termo de correção — isso deve ser verdade por construção do código, não apenas por descrição em texto.

### 4.4.1 Leader-Follower (LF)

Fonte primária desta arquitetura: Giacomini Jr, Seraphim Rodrigues, Paredes & Cebrian (2026, CBA — §2.0), Eq. (2) do paper, verificada equação a equação. A formulação de `§4.5` abaixo é uma correspondência direta dessa equação (mapeamento de notação em §2.0), não uma reconstrução aproximada — isso é uma diferença importante em relação à situação com Kitso et al. (§2.5′), onde a Fase 0 precisou declarar uma adaptação.

Um agente é designado líder. **Atualizado nesta revisão (decisão tomada em diálogo com o pesquisador, ver §7.6): o líder não é escolhido a priori — é determinado empiricamente a partir da Etapa 2 (caracterização do caso sem controle).**

**Critério de escolha (Critério B — violação acumulada, formalizado nesta revisão):** rodar o caso sem controle (§9, Etapa 3) e calcular, para cada agente `i`, a violação acumulada de tensão em sua própria barra ao longo do dia:

$$
S_i = \sum_{t=0}^{23} \max\big(0,\; V_i(t) - V_{lim}\big)\cdot \Delta t
$$

O líder é `\arg\max_i S_i` — o agente cuja barra acumula a maior área de sobretensão acima de `V_lim` ao longo do dia, não apenas o maior pico instantâneo. Esta escolha (em vez do critério A, pico único, mais sensível a outlier de um único horário; ou do critério C, sensibilidade elétrica `∂V/∂P`, mecanisticamente mais rico mas exigindo uma varredura numérica adicional fora do escopo original da Fase 0) foi deliberada por ser barata — é subproduto direto da Etapa 2, sem trabalho experimental adicional — e mais robusta que o pico único.

Isso **substitui tanto a escolha a priori de versões anteriores deste documento** (que sugeriam fixar o líder no agente eletricamente "mais fraco por suposição", ex. `832`) **quanto a convenção do código de referência** (líder = primeiro agente da lista, `824`, por posição, não por critério elétrico) — nenhuma das duas é usada; o líder da Fase 0 é uma saída do próprio experimento, não uma entrada.

**Apenas o líder** (a barra que vencer o critério `S_i`) recebe o termo de correção de erro de tensão; os demais só recebem informação por consenso vizinho-a-vizinho. Isso é metodologicamente decisivo para C2/C3 (ver H5, §3): quando a falha isola o líder, **toda a rede** perde o único ponto de correção ativa — não só a partição sem líder. Para testar H5a, executar C3 tanto com `m = líder` (o vencedor de `S_i`) quanto com `m ≠ líder` (qualquer outro agente).

**Resolvido nesta revisão (§7.6):** o líder é **fixo** ao longo de toda a simulação (uma vez determinado por `S_i`, não é recalculado) — confirmado diretamente no código de referência, que também usa um líder fixo (embora escolhido por outro critério). H5 e H5a, como formuladas em §3, permanecem válidas sem necessidade de reformulação.

**Consequência para a topologia de 6 nós (§4.3) — resolvida por rotulagem, não por redesenho.** Como a rede de comunicação é desacoplada da rede elétrica por definição (Fase 0 original, §11), a barra que vencer o critério `S_i` é simplesmente **mapeada para a posição `1`** do grafo de §4.3 (o nó que `C2` isola com uma única remoção de aresta) — não há necessidade de redesenhar a topologia, apenas de atribuir os rótulos `1..6` às seis barras físicas **depois** que a Etapa 2 rodar, não antes. Isso também vale para o nó `6` (o outro extremo isolável com uma aresta): se for útil comparar "falha do líder" com "falha do agente eletricamente mais robusto" como caso de contraste (§7.6), o segundo pode ser mapeado para a posição `6`. **Consequência prática para o checklist (§9): a definição final do grafo de comunicação com rótulos atribuídos só pode ocorrer depois da Etapa 3 (caracterização sem controle), não antes — a ordem do checklist precisa refletir essa dependência.**

### 4.4.2 Leaderless

Não há agente designado. **Todo** agente `i` calcula seu próprio termo de correção a partir da **tensão local do seu próprio barramento**, `V_i(k)` — não de uma tensão monitorada única. Esta é a adaptação, para curtailment de PV, da lógica leaderless de Kitso et al. (2025, Eq. 12–14), verificada diretamente no PDF (§2.5′): lá aplicada a `U_i`, fator de utilização de BESS; aqui aplicada a `ρ_i`, fração de curtailment. O filtro de *override* por SOC do método original (Eq. 15 do paper) não se aplica (Fase 0 não tem BESS/SOC) e é omitido por declaração explícita, não por simplificação silenciosa. O termo de decaimento `U_i(k)=0.5\,U_i(k-1)` quando a tensão local retorna à faixa (Eq. 12, terceiro ramo) **não está incluído** na formulação mínima de `c_i(k)` em §4.5, mas é um refinamento citável e recomendado se o tempo permitir (ver discussão completa em §2.5′).

### 4.4.3 Consequência arquitetural para a definição de `V_max−mon`

A decisão em aberto de §7.3 só existe para Leader-Follower — no Leaderless não há ambiguidade, porque `e_{V,i}` é definido localmente por construção para todo `i`. Isso simplifica a Fase 0: essa decisão só precisa ser tomada uma vez, para a arquitetura LF. **Correção nesta revisão:** o paper-âncora (§2.0) resolve essa decisão de forma diferente do que este documento recomendava antes — usa `ΔV(k) = max(0, V_max−mon(k) − V_ref)`, onde `V_max−mon` é o **máximo entre todos os barramentos monitorados**, não a tensão local do líder isoladamente. Sob comunicação ideal (C0) isso é inofensivo; sob falha (C1–C4) isso levanta uma pergunta nova, tratada em §7.3 revisado: o que significa "máximo entre os barramentos monitorados" quando o grafo de comunicação está particionado ou degradado?

## 4.5 Regra de atualização — consenso proporcional, duas variantes

Estado comum às duas arquiteturas: `rho_i(k) ∈ [0,1]`, `i=1..5`. Mistura por consenso **idêntica** nas duas:

$$
\rho_i(k+1) = \operatorname{clip}\Big[\, \rho_i(k) + \varepsilon \sum_{j} a_{ij}(k)\,[\rho_j(k)-\rho_i(k)] \;-\; c_i(k) \,,\; 0,\; 1 \Big], \qquad P_{curt,i}(k) = \rho_i(k)\cdot P_{available,i}(k)
$$

O termo `c_i(k)` é a **única** diferença entre as duas arquiteturas — e deve ser a única linha de código que difere entre os dois módulos de controle:

$$
\textbf{Leader-Follower:}\quad c_i(k) = \mathbb{1}_{i=\text{líder}}\; \beta\, e_V(k), \qquad e_V(k) = \max(0,\; V_{\max-mon}(k) - V_{lim})
$$

onde `V_max-mon(k)` é o máximo entre os barramentos monitorados **efetivamente observáveis pelo líder no instante `k`**, conforme a decisão registrada em §7.3 — sob C0 isso coincide com o máximo global da rede (igual ao paper-âncora, §2.0); sob falha, `V_max-mon` deve ser redefinido explicitamente (§7.3).

$$
\textbf{Leaderless:}\quad c_i(k) = \beta\, e_{V,i}(k), \qquad e_{V,i}(k) = \max(0,\; V_i(k) - V_{lim}) \quad \forall i
$$

**Regra de epsilon — CORRIGIDA nesta revisão para bater com o código de referência (§2.0/§7.6), idêntica nas duas arquiteturas:**

$$
\varepsilon = \frac{2}{\sum_i d_i(A_0)} = \frac{2}{\operatorname{tr}(L_0)}
$$

Esta é a regra **verificada diretamente no código-fonte** (`calculo_eps`): calcula os autovalores da Laplaciana, descarta o autovalor nulo (multiplicidade 1 para grafo conexo), e divide `2` pela soma dos autovalores restantes — que, por propriedade do traço, é exatamente `Σd_i`. **Isto substitui a regra `ε=1/(Δmax+1)` proposta em versões anteriores deste documento**, que era uma escolha teoricamente válida mas não a que o grupo de pesquisa efetivamente usa. Como `Σd_i ≥ λ_max(L)` em geral, esta regra é mais conservadora (passo menor, convergência mais lenta, porém sempre estável) do que o limite clássico `ε<2/λ_max(L)}`. O código inclui uma salvaguarda (`se ε≈1, usar ε=0.99`) que deve ser preservada.

**Consequência para falha de comunicação:** como `ε` depende de `Σd_i(A)`, que muda a cada cenário de falha (C1/C2 removem enlaces; C4 é estocástico), a Fase 0 tem duas opções válidas, que devem ser declaradas explicitamente e nunca misturadas silenciosamente: **(a)** calcular `ε` uma vez a partir de `A_0` (grafo nominal C0) e mantê-lo fixo em todos os cenários — o que preserva a comparabilidade entre cenários, ao custo de não ser exatamente a regra ótima para os grafos degradados; ou **(b)** recalcular `ε(k)` a cada iteração a partir do `A(k)` vigente — mais fiel ao código de referência (que recalcula `eps` sempre que monta um novo `A` em `montar_sistema`), mas introduz uma segunda variável dependente da falha, potencialmente confundindo o efeito "falha degrada o grafo" com o efeito "falha muda a dinâmica de convergência via `ε`". **Recomendação: opção (a)**, por clareza causal (consistente com a regra já registrada no `02_consensus_methods.md`: "não mudar epsilon [...] sem documentar") — mas a divergência do código de referência (que faz (b) por padrão) deve ser declarada no texto do TCC.

**Alternativa verificada na literatura (R4, Mai et al. 2021, EPSR):** os **pesos de Metropolis** (`d_ij = 1/max(n_i,n_j)` para vizinhos, `d_ii = 1 − Σ_j d_ij`) produzem, por construção, uma matriz duplamente estocástica sem depender de informação global do grafo (`Σd_i` ou `λ_max`) — cada agente só precisa saber o próprio grau e o dos vizinhos diretos, o que é mais fiel a um cenário de falha (nenhum agente tem visão global do grafo). Continua sendo uma alternativa citável e mais robusta a falhas do que qualquer regra que dependa de `Σd_i` global, mas diverge do código de referência do grupo — usar apenas se a Fase 0 decidir priorizar robustez teórica sobre continuidade direta de código.

### 4.5.1 Decisão crítica de justiça experimental: `β` deve ser o mesmo nas duas arquiteturas?

Usar o **mesmo valor numérico de `β`** nas duas arquiteturas parece a escolha "neutra" óbvia, mas não é necessariamente justa: em Leaderless, até 5 termos `β·e_{V,i}(k)` podem estar ativos simultaneamente (um por agente em sobretensão local), contra no máximo 1 em Leader-Follower — se a sobretensão for espacialmente disseminada (múltiplos PVs acima do limite ao mesmo tempo), Leaderless aplica um "empurrão" agregado maior por iteração **não por ser estruturalmente mais robusto, mas porque tem mais atuadores dirigidos simultaneamente**. Isso é um confundimento real entre "arquitetura melhor" e "mais graus de liberdade de atuação", e deve ser resolvido explicitamente, não descoberto tarde no experimento — ver decisão pendente em §7.5.

## 4.6 Modelo de falha por cenário

| Cenário | Definição formal | O que muda em `A(k)` |
|---|---|---|
| **C0** | `A(k) = A_0` para todo `k` | nada |
| **C1** | `A(k) = A_0` com aresta `(2,4)` removida, para todo `k` | topologia estática, ainda conexa |
| **C2** | `A(k) = A_0` com aresta `(2,3)` removida, para todo `k` | topologia estática, desconexa (`λ₂=0`) |
| **C3** | `A(k) = A_0` para `k<k_f`; agente `m` isolado (linhas/colunas `m` zeradas) para `k_f ≤ k < k_r`; `A(k)=A_0` para `k≥k_r` | topologia variante no tempo, conjuntamente conexa |
| **C4** *(fora de escopo nesta implementação — ver §7.4)* | `a_{ij}(k) = a^{0}_{ij}\cdot\text{Bernoulli}(1-p_{loss})` i.i.d. por par de agentes e por iteração `k` | topologia estocástica, `A(k)` é matriz aleatória |

C4 permanece **formalizado aqui para referência futura**, mas **não entra nesta primeira implementação** — decisão do pesquisador de não fazer Monte Carlo por ora (§7.4 revisado). Como C4 só é cientificamente válido com replicação estatística (§5.4, também revisado), "sem Monte Carlo" e "sem C4" são, na prática, a mesma decisão: rodar C4 uma única vez por `p_loss` não seria válido, então a opção correta é não rodá-lo agora, não rodá-lo sem repetição.

Esta tabela é **arquitetura-agnóstica por construção**: `A(k)` (e, portanto, `λ₂(L(k))`) não depende de qual controlador está rodando por cima — apenas `c_i(k)` (§4.5) depende. Isso é o que permite reutilizar exatamente a mesma classe `CommunicationGraph` (§5.3) para as duas arquiteturas, sem duplicar a lógica de falha.

## 4.6.1 Matriz experimental combinada — arquitetura × cenário

O experimento **desta implementação** é o produto cartesiano de duas variáveis independentes: arquitetura `∈ {LF, Leaderless}` e cenário de falha `∈ {C0,C1,C2,C3}` — determinísticos, sem C4 (§7.4) —, com C3 subdividido em `m=líder` / `m≠líder` (relevante sobretudo para LF, ver H5a).

| | C0 | C1 | C2 | C3 (m=líder) | C3 (m≠líder) |
|---|---|---|---|---|---|
| **Leader-Follower** | baseline LF | LF sob perda de enlace | LF particionado — **caso crítico de H5** | LF, pior caso (H5a) | LF, caso moderado |
| **Leaderless** | baseline Leaderless | Leaderless sob perda de enlace | Leaderless particionado — **contraponto de H5** | Leaderless, falha de qualquer agente | Leaderless, falha de qualquer agente |

O par de células **(Leader-Follower, C2)** vs. **(Leaderless, C2)** é a comparação mais informativa de todo o experimento — é onde H5 é decidida. São **8 células** no total (2 arquiteturas × 4 cenários, com C3 contando como 2), um escopo deliberadamente pequeno o suficiente para caber em um único arquivo sem Monte Carlo.

## 4.7 Critério de parada e status — CORRIGIDO nesta revisão: critério elétrico puro, não por erro de consenso

Versões anteriores deste documento propunham `e_c(k) < ε_tol` sustentado por `m` iterações como critério de parada. **O código de referência (§2.0/§7.6) não usa isso** — usa um critério puramente elétrico, exatamente como a skill já preconiza (`02_consensus_methods.md §8`: *"Electrical stopping should be primary [...] Consensus-state agreement alone is not sufficient if voltage remains outside limits"*):

$$
\text{parar quando } V_{\max-mon}(k) \le V_{ref} + tol, \quad \text{ou } k = k_{max}
$$

com `tol = 10^{-6}` e `k_{max} = 500` como valores de partida verificados no código de referência (a Fase 0 deve testar se esses valores permanecem adequados com a topologia mais esparsa de §4.3 — grafos com menos enlaces tendem a exigir mais iterações para o mesmo `ε`). `e_c(k)` continua sendo **registrado e reportado** a cada iteração — é a métrica central de H1/H2 — mas deixa de ser o gatilho de parada; ele é diagnóstico, não critério de controle.

Se `k = k_max` for atingido sem `V_max-mon(k) ≤ V_ref + tol`, o passo deve ser marcado `status = "nao_convergiu"` e **nunca** tratado como regulação bem-sucedida — replicando a regra já estabelecida em `03_results_validation.md`. Este caso é especialmente relevante sob falha de comunicação (C2/C3 com o líder isolado): o critério elétrico puro é o que permite capturar corretamente o cenário em que a rede fica indefinidamente em sobretensão porque a correção nunca chega àquela partição — com um critério baseado em `e_c(k)`, esse caso poderia ser erroneamente reportado como "convergido" (os `ρ_i` da partição sem líder podem estabilizar entre si rapidamente, mesmo sem nunca corrigir a tensão) — este é, na prática, uma manifestação direta da observação já registrada em H2 (§3): erro de consenso baixo não implica ausência de problema elétrico.

---

# 5. Orquestração computacional do experimento

## 5.1 Por que este NÃO é um problema de `Solve Number=24`

A razão já documentada em `01_altdss_execution_model.md` se aplica integralmente aqui, com uma nuance adicional específica da Fase 0: como não há BESS, não há estado de energia a preservar entre iterações de controle — mas ainda assim **o tempo não pode avançar dentro do laço de consenso**, porque:

- a LoadShape do horário mudaria entre iterações do mesmo instante físico;
- a falha de comunicação (C3, C4) é definida **por iteração de consenso**, não por hora — se o tempo avançasse dentro do laço, a semântica de "quantas iterações sob falha" se perderia.

## 5.2 Fluxo por passo horário `t = 0..23`

```text
# arquitetura in {LEADER_FOLLOWER, LEADERLESS} — parametro fixo do run, nunca trocado no meio do dia

para t em 0..23:
    aplicar carga(t) e irradiância(t)
    resetar comandos de curtailment para o estado pré-controle
    SolveSnap()                                  # estado sem controle
    medir V(t), P_available,i(t)

    se overvoltage:
        aplicar_estado_da_rede_de_comunicacao(cenario, t)   # C0..C4, arquitetura-agnóstico
        k = 0
        enquanto not convergiu and k < k_max:
            se arquitetura == LEADER_FOLLOWER:
                c = corrigir_leader_follower(rho(k), V_lider(k), lider_idx)
            senao:  # LEADERLESS
                c = corrigir_leaderless(rho(k), V(k))          # V(k) = vetor de tensoes locais
            rho(k+1) = clip(rho(k) + eps * L(k) @ rho(k) - c, 0, 1)
            aplicar P_curt,i = rho_i(k+1) * P_available,i
            SolveSnap()
            medir V(t), e_c(k+1)
            k += 1
        registrar status (convergiu / nao_convergiu / saturado)

    registrar metricas finais do passo t   # inclui coluna "arquitetura"
    # nao ha integracao de energia (sem BESS) - nada a "avancar" alem do tempo
```

Isso é uma **especialização** do pseudocódigo já presente em `01_altdss_execution_model.md`, sem o laço de SOC (que não se aplica). O ponto de engenharia crítico é que `corrigir_leader_follower` e `corrigir_leaderless` são as **únicas** duas funções que diferem entre as arquiteturas — tudo o resto do laço (mistura por `εL`, `SolveSnap`, critério de parada) é código compartilhado. Se a implementação real divergir mais do que isso entre as duas arquiteturas, a comparação deixa de isolar a variável "arquitetura" e passa a confundir com diferenças de implementação não declaradas — exatamente o tipo de erro que a skill pede para evitar.

## 5.3 Onde a injeção de falha entra

`aplicar_estado_da_rede_de_comunicacao(cenario, t)` é a função nova que a Fase 0 introduz e que a skill atual **ainda não cobre** (as referências `01`–`05` tratam de consenso sobre grafo fixo; a variação temporal/estocástica do grafo é conteúdo novo). Ela deve:

- para C0/C1/C2: retornar a matriz `A(k)` fixa da topologia do cenário, constante em `k`;
- para C3: checar se `t` está na janela de falha e devolver `A_0` com o agente `m` isolado;
- para C4: sortear uma nova realização de `A(k)` a cada iteração `k` (não a cada `t`!), com uma **semente de RNG registrada no manifest** para reprodutibilidade.

**Recomendação de engenharia:** implementar isso como um objeto `CommunicationGraph` com estado próprio (`.current_adjacency(k)`), instanciado uma vez por cenário e injetado no controlador — nunca reconstruído implicitamente dentro do laço de consenso, para evitar o mesmo tipo de erro de "state leakage entre cenários" que a skill já proíbe explicitamente para a camada elétrica.

## 5.4 Repetições estatísticas (Monte Carlo) — fora de escopo nesta implementação

C4 é estocástico; C0–C3 são determinísticos. Rodar C4 uma única vez por `p_loss` **não seria cientificamente válido** — o corpus (R7, R8) trata perda de pacote como variável aleatória, e reportar `e_c`, `N_iter`, `σ_r`, `V_max` exigiria **distribuições** (replicações com sementes distintas, média ± intervalo de confiança), não pontos únicos.

**Decisão do pesquisador nesta revisão: sem Monte Carlo por ora.** Como consequência direta, **C4 não é implementado nesta primeira versão** (§4.6, §7.4) — não porque a formalização esteja errada, mas porque rodá-lo sem replicação violaria a própria validade que este documento exige. Esta seção fica registrada para quando (se) C4 for retomado: a regra seria `R ≥ 30` replicações por `p_loss ∈ {5%,10%,20%,30%}` e por arquitetura, reportando média ± IC ou mediana + IQR.

## 5.5 Estrutura de saída (compatível com o padrão do mestrado)

```text
Resultados/
  FASE0_EXP001/
    config.yaml                     # topologia, epsilon, beta, buses, potencias, sementes, arquiteturas
    manifest.json                   # lambda_2 por cenario, hash do grafo, versao do codigo
    raw/
      timestep.csv                  # arquitetura, scenario, t, k, agent, rho_i, V, Vmax, status
      consensus_iterations.csv      # arquitetura, scenario, t, k, e_c(k), edges_active(k)
    summary/
      convergencia_por_cenario.csv  # colunas: arquitetura x cenario
      sigma_r_por_cenario.csv       # global E por-particao (obrigatorio p/ H2 em C2), por arquitetura
      tensao_por_cenario.csv        # por arquitetura
    figures/
      01_sistema_eletrico.png
      02_grafo_comunicacao.png      # C0 e cada topologia de falha
      03_convergencia.png           # series por arquitetura, mesmo cenario sobreposto
      04_tensoes.png                # idem
      05_curtailment.png
      06_margem_H3.png              # sigma_r x Vmax, colorido por arquitetura
      07_H5_particionamento.png     # Vmax(t) em cada particao, LF vs Leaderless, mesmo cenario C2
      08_H5a_falha_lider.png        # sigma_r/Vmax: m=lider vs m!=lider, LF vs Leaderless
    tables/
```

`graph_realizations.csv` (usado apenas por C4) foi removido da estrutura — sem Monte Carlo, não há realizações estocásticas de `A(k)` a registrar (§5.4, §7.4).

`06_margem_H3.png` não está na lista original de figuras da Fase 0 (§25) — é uma adição deste documento porque é a **visualização direta de H3**, a hipótese mais valiosa: um scatter/linha com `σ_r` no eixo x e `V_max` no eixo y, um ponto por cenário, com a linha `V_lim = 1.05 pu` marcada e cor/marcador por arquitetura. `07_H5_particionamento.png` e `08_H5a_falha_lider.png` são novas nesta revisão — são as visualizações diretas de H5 e H5a, e devem ser tratadas como as figuras centrais do TCC ao lado de `06_margem_H3.png`, não como material suplementar.

**Nota sobre "visualização de topologia" (esclarecendo escopo, decisão do pesquisador nesta revisão):** `01_sistema_eletrico.png` e `02_grafo_comunicacao.png` são diagramas estáticos simples (matplotlib/networkx — um desenho da rede IEEE 34 com os PVs marcados, e um desenho do grafo de comunicação com 6 nós), gerados como qualquer outra figura do experimento, e **continuam no escopo**, por serem baratos e necessários para explicar C1/C2 no texto do TCC. O que fica **fora de escopo** é o pipeline interativo descrito em `Skills/SKILL_simulacao_visualizacao_topologia.md` (HTML interativo via `pyvis`, com coordenadas reais de barra, drag/zoom/hover, metadados em `.txt`) — essa é uma ferramenta mais elaborada, não necessária para os resultados do TCC. **Se a intenção original incluía também descartar os diagramas estáticos 01/02, avisar** — a leitura aqui assume que só o pipeline interativo está sendo adiado.

---

# 6. Validação antes de aceitar qualquer execução

Adaptando o checklist de `03_results_validation.md` ao caso sem BESS:

- toda `SolveSnap()` convergiu eletricamente;
- `P_curt,i ≥ 0` e `P_gen,i ≤ P_available,i` em todo passo;
- a topologia base `A_0`, as potências FV, o perfil de carga/irradiância e `ε`/`β`/`k_max`/`V_lim` são **idênticos** entre C0–C4 (única variável: o estado da rede de comunicação);
- `λ₂(L)` foi calculado e registrado para cada topologia estática usada (C0, C1, C2) — deve bater com o valor esperado por construção (`>0` para C0/C1, `=0` para C2);
- casos que atingem `k_max` sem convergir estão marcados `nao_convergiu`, nunca reportados como regulação bem-sucedida;
- em C4, a semente de RNG de cada replicação está registrada e é possível reproduzir exatamente a sequência de `A(k)`;
- `σ_r` foi calculado tanto globalmente quanto por partição em todo cenário onde `λ₂(L)=0` for observado (C2, e C3 durante a janela de falha se a falha temporária particionar o grafo).

**Checagens específicas de arquitetura (novas nesta revisão):**

- em Leader-Follower, o termo de correção `c_i(k)` é **não-nulo apenas no índice do líder**, em toda iteração e todo cenário — um vazamento de correção para outro agente é um bug de implementação, não um resultado;
- em Leaderless, o termo de correção usa a **tensão local de cada agente** (`V_i(k)`), nunca uma tensão global compartilhada por engano (reaproveitar acidentalmente `V_mon`/`V_max` da implementação LF é o erro de implementação mais provável, porque o código-fonte é quase idêntico);
- `ε`, `β`, `k_max`, `V_lim`, a topologia `A_0` e todos os cenários de falha (C0–C4) são **idênticos entre as duas arquiteturas**, exceto pela decisão explícita de §7.5 sobre normalização de `β`;
- para C3, todo cenário reporta explicitamente se `m = líder` ou `m ≠ líder` (mesmo em Leaderless, onde a distinção não tem efeito mecanístico na correção, mas ainda é necessária para comparar como H5a).

---

# 7. Decisões em aberto que precisam ser fechadas antes de codificar

Estes pontos não estão resolvidos nem na Fase 0 original nem neste documento — são escolhas de projeto que só o pesquisador pode fechar, porque envolvem trade-off entre simplicidade experimental e fidelidade ao fenômeno.

## 7.1 Duração e posição da janela de falha em C3

A Fase 0 não define `k_f`, `k_r` nem em qual hora `t` do dia a falha temporária ocorre. Como o fenômeno interessante (H3, H4′, H5a) depende de a falha ocorrer **durante** um período de sobretensão ativa (senão não há nada para o consenso corrigir), a falha deve ser injetada deliberadamente no(s) horário(s) de pico de geração FV identificados no caso sem controle (Etapa 2 da Fase 0), não em horário aleatório. Recomenda-se testar pelo menos duas durações de falha (curta: poucas iterações; longa: até o limite antes de `k_max`) para caracterizar a sub-hipótese H4′ como uma curva, não um ponto. Esta decisão é tomada **uma vez** e aplicada identicamente às duas arquiteturas e a ambos os sub-casos de C3 (`m=líder`/`m≠líder`) — mudar a janela entre arquiteturas invalidaria a comparação de H5.

## 7.2 Simetria da perda de pacote em C4

Definir explicitamente se a perda de mensagem em `(i,j)` implica perda simultânea em `(j,i)` (falha de enlace bidirecional) ou se cada direção é um evento Bernoulli independente (falha de canal, mais realista fisicamente, mas produz uma matriz `A(k)` não simétrica a cada iteração, o que quebra a garantia clássica de convergência para consenso de médias e exige justificar convergência por outro caminho — ex.: convergência em média/probabilidade, não determinística). **Recomendação:** começar com a versão simétrica (mais simples, resultado mais limpo para o TCC) e declarar a versão assimétrica como limitação explícita/trabalho futuro do próprio TCC — não como algo a empurrar para o mestrado (ver decisão de escopo em §8: a camada de falha fica retida no TCC por ora).

## 7.3 Definição operacional de `V_max−mon` (tensão monitorada em Leader-Follower) — RESOLVIDO nesta revisão pelo código de referência

Aplica-se **apenas à arquitetura Leader-Follower** — em Leaderless a definição é local por construção (§4.4.2), sem ambiguidade. **Resolvido:** o código de referência (`JGJ_Paper_CBA_2026_V4.pdf`, script Python compartilhado pelo pesquisador — ver §2.0) usa `Vmax_dgs = max(V_i para i nos barramentos com PV)`, isto é, **o máximo entre os barramentos onde há geração fotovoltaica conectada** — nem a tensão local exclusiva do líder, nem o máximo de toda a rede elétrica (`Vmax_rede`, que o código calcula separadamente só para relatório, sem influenciar o controle). Isso substitui a recomendação anterior deste documento (que sugeria usar apenas a tensão local do líder).

**Consequência para falha de comunicação (o código de referência não trata disso, é extensão da Fase 0):** sob C0, "máximo entre os barramentos com PV" é bem definido porque o líder observa todos os 5–6 agentes sem restrição. Sob falha (C1–C4), o líder só pode calcular esse máximo sobre os agentes que **ainda alcança pela rede de comunicação** — a Fase 0 deve, portanto, redefinir `V_max−mon(k)` como o máximo entre as tensões dos agentes **observáveis pelo líder no grafo `A(k)` corrente** (isto é, restrito à componente conexa do líder). Sob C2 (particionamento), isso significa que o líder passa a calcular seu erro de correção usando apenas os agentes da própria partição — o que é fisicamente sensato (o líder não pode reagir a uma tensão que não consegue observar) e é exatamente o mecanismo que torna H4/H5 testáveis sem ambiguidade.

## 7.4 Escopo de C4: RESOLVIDO — fora desta implementação

Conforme §17/§24 da Fase 0, C4 já era opcional. **Decisão final do pesquisador: C4 fica fora de escopo por ora**, junto com o Monte Carlo do qual depende (§5.4). O experimento desta implementação é C0–C3 × {Leader-Follower, Leaderless} (§4.6.1) — determinístico, 8 células, sem replicação estatística. C4 permanece formalizado em §4.6 como trabalho futuro, não é descartado do documento, só da implementação atual.

## 7.5 Normalização do ganho de correção `β` entre arquiteturas (decisão nova, crítica para H5)

Já introduzida em §4.5.1: usar o mesmo `β` nas duas arquiteturas é a opção mais simples, mas potencialmente injusta, porque Leaderless pode ter múltiplos termos de correção ativos simultaneamente (um por agente em sobretensão local) contra no máximo um em Leader-Follower. Três caminhos possíveis, em ordem de preferência recomendada:

1. **Primário — `β` idêntico, declarado como tal.** Reportar os resultados com o mesmo `β` nas duas arquiteturas, mas **discutir explicitamente** no texto do TCC que isso significa que, sob sobretensão espacialmente disseminada, Leaderless tem mais "autoridade de correção" agregada por construção — e que isso é parte do que se está testando (a arquitetura leaderless *é*, por definição, uma arquitetura com mais atuadores dirigidos; não é um artefato a esconder, é uma propriedade do método). Esta é a opção mais simples de implementar e a mais defensável cientificamente **desde que a ressalva seja escrita no artigo**.
2. **Secundário/sensibilidade — `β` normalizado por grau de atuação esperado**, ex. `β_leaderless = β_LF / N̄_ativos`, onde `N̄_ativos` é o número médio de agentes em sobretensão local simultânea observado no caso sem controle (Etapa 2). Rodar como cenário de sensibilidade adicional, não como resultado primário — serve para checar se a conclusão de H5 se sustenta mesmo sob a hipótese mais conservadora contra Leaderless.
3. **Não recomendado:** tentar "otimizar" `β` separadamente para cada arquitetura antes de comparar — isso reintroduz um grau de liberdade não controlado e torna impossível saber se uma arquitetura venceu por ser estruturalmente melhor ou por estar melhor ajustada.

**Esta decisão deve ser tomada e documentada no `config.yaml` do experimento antes de gerar qualquer resultado de H5** — é exatamente o tipo de escolha que, se descoberta tarde, invalida comparações já feitas.

## 7.6 Mecanismo de seleção do líder: RESOLVIDO — fixo, e determinado empiricamente (não a priori, não aleatório)

Duas perguntas distintas ficam resolvidas aqui:

**(a) Fixo ou recalculado dinamicamente?** Respondida pelo código compartilhado (§2.0/§4.4.1): `lider_idx` é definido **uma única vez** e passado como **constante** para as chamadas de `simular_dia` nos três modos de controle, sem qualquer recálculo dentro do laço horário ou do laço de iterações de consenso. **O líder é fixo por toda a simulação.**

**(b) Quem é o líder — escolha a priori, aleatória, ou empírica?** Discutido diretamente com o pesquisador (não está no código de referência, que resolve isso arbitrariamente por posição na lista — `lider_idx=0`, bus `824`). Três opções foram comparadas:

- **a priori** (fixar por suposição, ex. "o agente eletricamente mais fraco") — rejeitada: depende de uma suposição não verificada sobre qual barra é de fato mais crítica.
- **aleatória** (sortear o líder, por rodada ou por replicação) — rejeitada: H5a precisa de um contraste controlado `m=líder` vs. `m≠líder`; randomizar a identidade do líder tornaria essa distinção probabilística e diluiria a hipótese mais forte do TCC, além de acumular mais uma fonte de aleatoriedade sobre a já reservada para C4 (§5.4).
- **empírica, Critério B (decisão final)** — o líder é o agente com maior violação de tensão **acumulada** (`S_i = Σ_t max(0, V_i(t)-V_lim)·Δt`) no caso sem controle (Etapa 2/3). Formalizado em §4.4.1. Barato (subproduto direto da caracterização já planejada), mais robusto que usar apenas o pico instantâneo, e evita tanto a arbitrariedade do código de referência quanto uma suposição não verificada da Fase 0.

**H5 e H5a, como formuladas em §3, permanecem válidas** — a mudança é apenas em *como* o líder é determinado, não na lógica causal da hipótese (líder único = ponto único de falha em LF).

Observação adicional que o código revela: o ganho do líder usado no código de referência é `ganho_lider_pot = ganho_lider_prop = 5` (mesmo valor para as duas variáveis de estado, potência absoluta e proporcional) — útil como ponto de partida numérico para a calibração de `β`/`G(k)` na Fase 0 (§4.5, §7.5), embora precise ser recalibrado porque a topologia de comunicação da Fase 0 (§4.3) é mais esparsa que a topologia completa usada no código de referência.

## 7.7 Outras decisões reveladas pelo código de referência, ainda não fechadas

- **Curtailment via saturação de `kVA`, não `pctPmpp`.** O código de referência aplica o comando de curtailment fazendo `pv.kVA = valor_aplicado` (com fator de potência unitário), não pela propriedade `pctPmpp` que a skill `Executor_altGRID_consenso` recomenda como "modelo de despacho físico preferido" (`04_bess_pv_control.md`, que trata o uso de `kVA` como "implementação histórica", legado). **Confirmado nesta revisão (§4.2.1):** a Fase 0 segue `PVSystem`/`kVA` por continuidade direta com o código de referência — decisão final, não mais pendente. Migrar para `pctPmpp` só se uma necessidade específica (ex. despacho `Q` explícito do Paper 3) exigir.
- **Dependência de dados ainda não presente no repositório.** As curvas de carga (`LS_Tipo1`, `LS_Tipo2`) e de irradiância PV vêm de um arquivo Excel (`CurvaPV_24pontos_CBA.xls`) que existe apenas na máquina local do Prof. Giacomini, não em `papers/`, `IEEE34bus/` nem em nenhum outro lugar deste repositório. **Esta é uma dependência bloqueante para reproduzir os resultados exatos do paper-âncora** e deve ser resolvida (solicitar o arquivo, ou gerar curvas equivalentes) antes da Etapa 2 do checklist (§9) — caracterizar o caso sem controle.
- **`altdss.Solution.LoadMult = 1.1`** — o código de referência aumenta a carga total da rede em 10% "para evitar cortes tão acentuados". Esse é um parâmetro de calibração do cenário elétrico (torna o problema de sobretensão nem trivial nem catastrófico), análogo ao "sizing experimental que produza uma região não trivial" já discutido para o Paper 2 (`Skills/Paper_2..._BESS.md §23-24`). A Fase 0 deve herdar esse valor como ponto de partida e validar se ele ainda produz uma região não trivial com a topologia de comunicação mais esparsa proposta em §4.3.
- **Critério de parada é puramente elétrico, não por erro de consenso — corrigido em §4.7 (ver abaixo).**

---

# 8. Relação com o mestrado — o que este experimento entrega adiante (escopo revisado)

**Decisão explícita do pesquisador, registrada nesta revisão:** por ora, a camada de falha de comunicação **não** é incorporada à linha do mestrado (Papers 2–4). Ela permanece escopo exclusivo deste TCC. Isso significa que a recomendação anterior deste documento — criar `references/06_communication_failures.md` na skill `Executor_altGRID_consenso` para que o Paper 2 (Bloco C) reutilize a semântica de falha — **fica suspensa**, não cancelada: o formalismo da Seção 4.6 continua correto e reaproveitável, mas não deve ser promovido à skill compartilhada até o pesquisador decidir explicitamente estendê-lo ao mestrado. O que efetivamente atravessa a ponte para o mestrado, nesta revisão, é mais restrito:

| Artefato produzido na Fase 0 | Reuso direto no mestrado |
|---|---|
| 6 PVs em barras `824,816,828,830,850,832` (§4.2, atualizado), potências e perfis congelados | Insumo direto de `Paper 2 — P2.0 Caracterização` (mesma rede, mesmos PVs) |
| Caso sem controle (sobretensão caracterizada) | Mesmo artefato exigido em `Paper_2 §16 (C0)` |
| Lógica de snapshots sequenciais (sem BESS), dentro do arquivo único | Referência conceitual para o executor determinístico pedido em `Roteiro_Macro §"Infraestrutura única"` — **reuso por leitura/adaptação, não por importação direta de módulo**, já que a Fase 0 é um arquivo monolítico (§4.1, decisão desta revisão) |
| **Implementações Leader-Follower e Leaderless do consenso proporcional**, com interface comum de correção (§4.4) | Precedente conceitual relevante para `Paper 2 — C5 (Leader-Follower Kitso)` e `C6 (Leaderless Kitso)`, que hoje ainda não estão implementados para BESS. Útil como referência de design (o padrão de duas funções com interface comum), não como código diretamente importável — a adaptação `U_i↔rho_i` continua sendo trabalho novo do Paper 2, e a eventual refatoração em módulos reutilizáveis fica para quando o mestrado precisar dela |
| `λ₂(L)` como métrica de severidade estrutural | Pode ser promovida a métrica padrão de robustez em Papers 2–4, hoje ausente das métricas listadas — **isso não depende de levar a camada de falha para o mestrado**, é só a métrica de grafo em si |
| Classe `CommunicationGraph` (§5.3) e o formalismo dos 5 cenários de falha (§4.6) | **Retido no TCC por decisão do pesquisador.** Fica documentado aqui para reuso futuro, mas não deve ser promovido à skill compartilhada nesta fase |

Esta divisão é, na verdade, mais limpa do que a versão anterior deste documento: o mestrado ganha algo genuinamente pronto para uso imediato (a comparação de arquiteturas, que o Paper 2 já planejava fazer para BESS), sem herdar uma dependência (falha de comunicação) que o pesquisador ainda não decidiu incorporar à linha maior.

---

# 9. Checklist operacional — próxima ação prática

> **Referência de API disponível:** `documentacao_altdss.md` (raiz do repositório) contém a documentação de referência completa do AltDSS-Python 0.2.3 (todas as classes: `PVSystem`, `Generator`, `Solution`, `Bus`, `LoadShape`, `XYcurve` etc.). Checado nesta revisão: `pctPmpp`, `kVA`, `Pmpp`, `Irradiance`, `WattPriority`, `kvarMax` (PVSystem — o elemento usado na Fase 0, §4.2.1) e `SolveSnap`/`Number`/`StepSize`/`FinishTimeStep` (Solution), `puVMagAngle`/`kVBase` (Bus) — todos existem exatamente como usados no código de referência (§2.0). `Generator.kW`/`kvar`/`Model`/`Status` também foram verificados e ficam registrados como alternativa avaliada (§4.2.1), não adotada. Consultar antes de implementar qualquer chamada nova à API.

> **Escopo travado nesta revisão:** um único arquivo `.py` (§4.1); arquiteturas Leader-Follower e Leaderless; cenários C0–C3 (**C4 fora de escopo**, §7.4); **sem Monte Carlo** (§5.4); **sem** o pipeline interativo de visualização de topologia (§5.5) — só os diagramas estáticos 01/02.

1. Fechar as decisões remanescentes da Seção 7 (janela de C3 — §7.1, simetria de C4 — §7.2, **normalização de `β` entre arquiteturas — §7.5**) — decisão do pesquisador, não do código. (Definição do líder e escopo de C4 já resolvidos, itens 3 e acima.)
2. Implementar a camada elétrica reaproveitando diretamente o padrão AltDSS já documentado (compilar `ieee34Mod3ORIGINAL_CBA.dss` — arquivo específico do código de referência, §4.2 —, criar 6 objetos `PVSystem` (§4.2.1) nas barras da Seção 4.2, sem BESS), tudo no arquivo único.
3. Rodar o caso sem controle e, para cada agente `i`, calcular `S_i` (§4.4.1, Critério B) a partir das violações acumuladas de tensão — isso **determina o líder** (`argmax_i S_i`) e onde injetar falha em C3. Este passo é agora um **bloqueador**: os itens 4, 6 e 7 dependem do resultado dele.
4. Com o líder já determinado, **atribuir os rótulos `1..6` da topologia de comunicação (§4.3)** — líder → posição `1` (o nó que `C2` isola); se houver rodada de contraste com o agente mais robusto (§7.6), esse vai para a posição `6`.
5. Implementar **apenas** a arquitetura Leader-Follower com `G0` fixo (C0) e validar H1 trivialmente (C0 deve convergir e reduzir sobretensão) antes de tocar em qualquer falha ou na segunda arquitetura.
6. Implementar a arquitetura Leaderless sobre a mesma base (trocando apenas a função de correção, §4.4–4.5) e validar que, sob C0, ambas convergem para regular a sobretensão — esta é a verificação de sanidade "H1 nas duas arquiteturas" antes de qualquer falha.
7. Implementar a função/classe de grafo de comunicação com os 4 modos ativos da Seção 4.6 (C0–C3, agora com os rótulos do item 4 já fixados); validar `λ₂(L)` calculado bate com o esperado por construção para C0/C1/C2 — compartilhada pelas duas arquiteturas dentro do mesmo arquivo, não deve ser duplicada.
8. Rodar C0–C3 **nas duas arquiteturas** (8 células, §4.6.1), priorizando C2 (o par que decide H5) e C3 com `m=líder`/`m≠líder` (H5a) antes de qualquer refinamento cosmético de figuras. Produzir os gráficos 01–05, 07 e 08 (estáticos, matplotlib) e a tabela de convergência.
9. Produzir a Figura `06_margem_H3` (colorida por arquitetura) e usá-la para responder diretamente à pergunta de pesquisa secundária (§3, H3) — e as Figuras `07`/`08` para responder H5/H5a. Este par de resultados decide se o TCC tem uma conclusão "forte" (existe região de tolerância, e a arquitetura a modula) ou "negativa mas honesta" (não há folga observável, ou a arquitetura não faz diferença mensurável).
10. Redigir a seção de discussão separando explicitamente falha algorítmica (consenso não converge) de falha elétrica (rede viola limites) — a distinção que a própria Fase 0 pede em §32.5 — **e, adicionalmente, separando efeito de severidade da falha (H1–H4) de efeito de arquitetura (H5/H5a)**, para não misturar as duas perguntas de pesquisa na conclusão.

---

# 10. Limitações reconhecidas deste documento

- O formalismo citado para R7 (Wang et al., 2023), R9 (Nojavanzadeh et al., 2022), R6 (Lu et al., 2023) e R10 (Wang et al., 2026) foi **verificado diretamente contra os PDFs originais** (§2.2–2.4) — pode ser citado no artigo com confiança de notação. Já R5 (Zhang et al., 2019) e R8 (Aghaee et al., 2022) permanecem citados apenas no nível do corpus/abstract, porque o PDF de R5 **não está presente** em `papers/` (o arquivo com nome sugestivo é, na verdade, uma cópia duplicada de R4 — ver nota em §2.2) e R8 não foi priorizado na extração. **Ação pendente antes da submissão:** localizar e adicionar o PDF correto de Zhang et al. (2019, DOI 10.1109/TSMC.2019.2915605) a `papers/`, e verificar R8 se sua citação for além do nível qualitativo.
- A escolha de barras (§4.2) e de topologia de comunicação (§4.3) são propostas fundamentadas, não definições irrevogáveis — qualquer uma pode ser ajustada desde que a mudança seja declarada e aplicada identicamente a todos os cenários (C0–C4), preservando a causalidade experimental exigida pela skill.
- Este documento não substitui a necessidade de calibrar `k_max`, `ε_tol`, `β` e `m` (iterações de confirmação de convergência) empiricamente contra o caso C0 antes de interpretar qualquer resultado de falha — isso só pode ser feito depois que o código existir. O achado de R4 (`N_iter` entre 468 e 2253 dependendo do tamanho da rede controlada) é um lembrete de que `k_max` deve ser generoso e testado, não assumido.
- **Kitso et al. (2025)** — item resolvido nesta revisão: PDF adicionado a `papers/` e formalismo verificado equação a equação (§2.5′). O que permanece como decisão em aberto, não como lacuna bibliográfica, é a **fidelidade da adaptação**: a Fase 0 usa uma equação única de mistura-mais-correção (§4.5), enquanto Kitso usa duas leis separadas (líder local + seguidor de rastreamento puro) e inclui um termo de decaimento no leaderless que a Fase 0 ainda não incorpora. Essa divergência está documentada em §2.5′ e deve ser declarada no texto do TCC como adaptação deliberada, não citada como reprodução fiel do método original.
- A decisão de normalização de `β` entre arquiteturas (§7.5) é uma escolha metodológica deste documento, não uma verdade estabelecida pela literatura. Kitso et al. também não enfrentam esse problema diretamente — no paper, `G_ov`/`G_un` (equivalente ao nosso `β`) aparecem uma vez por agente em ambas as arquiteturas (Eq. 7 para o líder único; Eq. 13 para cada agente no leaderless), então o mesmo confundimento de "mais atuadores simultâneos ativos" que motivou §7.5 também existe, em princípio, no desenho experimental deles — mas não é discutido no artigo. Isso reforça que a ressalva de §7.5 é uma contribuição metodológica própria deste TCC, não algo importado da literatura, e deve ser apresentada como decisão do autor.
- **Giacomini Jr, Seraphim Rodrigues, Paredes & Cebrian (2026, CBA)** — item resolvido nesta revisão como âncora primária (§2.0), com equações e código-fonte verificados diretamente (não apenas o abstract). Isso resolveu definitivamente a ambiguidade fixo/dinâmico do líder (§7.6: fixo, confirmado) e corrigiu três pontos que este documento tinha aproximado incorretamente em versões anteriores: a regra de `ε` (§4.5), o critério de parada (§4.7) e a definição de `V_max−mon` (§7.3). **Três itens permanecem pendentes de decisão do pesquisador, não resolvidos nesta revisão:**
  1. confirmar a reversão de 5→6 agentes (§4.2) — recomendada, não obrigatória;
  2. renumerar a topologia de comunicação de §4.3 para que o nó isolado por C2 coincida com o líder escolhido pela Fase 0 (agente `6`/`832`), já que o código de referência usa um líder diferente (agente `1`/`824`) — ajuste mecânico, mas ainda não aplicado ao grafo de §4.3;
  3. obter o arquivo de curvas de carga/irradiância (`CurvaPV_24pontos_CBA.xls`, §7.7) — sem ele, os resultados exatos do paper-âncora não são reproduzíveis, embora a Fase 0 possa prosseguir com curvas equivalentes próprias se necessário.
- Este documento ainda não recebeu o código-fonte da arquitetura **Leaderless** nem confirmação de que ela foi implementada e testada pelo mesmo grupo na mesma base de código do paper CBA 2026 — o código compartilhado cobre apenas `sem_controle`, `consenso_potencia` e `consenso_proporcional` (todas variantes Leader-Follower). A formalização do Leaderless neste documento (§4.4.2) continua apoiada exclusivamente em Kitso et al. (2025), não em código do grupo.
