# Roteiro Macro de Pesquisa — Paper 2 em diante

A partir de agora, a linha de pesquisa deve ser dividida em **três trabalhos adicionais**, e não apenas dois. O motivo é metodológico: juntar comparação de consensos, uso de \(Q\), despacho noturno e análise econômica no mesmo paper voltaria a misturar causas e reduziria a clareza experimental.

A sequência proposta é:

| Trabalho | Pergunta central | Variável científica principal | Produto |
|---|---|---|---|
| **Paper 1 — já existente** | Como diferentes consensos afetam curtailment e seu impacto econômico? | protocolo de consenso | Proporcional × Olfati × CORA + PLD |
| **Paper 2 — próximo** | Como diferentes arquiteturas de coordenação utilizam BESS limitados fisicamente? | estratégia de coordenação dos BESS | SOC, saturação, curtailment residual, HC, robustez |
| **Paper 3 — técnico** | Como combinar recursos energéticos e não energéticos ao longo do dia? | \(Q\) + carga/descarga do BESS | coordenação \(Q/P\), despacho diário, qualidade elétrica, HC |
| **Paper 4 — técnico-econômico** | Qual o valor econômico das diferentes formas de operar o sistema? | estratégia operacional e valor do armazenamento | PLD, curtailment evitado, throughput, sizing, value stacking |

---

# PAPER 2 — Coordenação distribuída de múltiplos BESS

Este é o trabalho que deve ser desenvolvido agora.

## Pergunta científica

> **Como diferentes estratégias de coordenação distribuída alteram a utilização, saturação e robustez de múltiplos BESS empregados na mitigação de sobretensão em uma rede com alta penetração fotovoltaica?**

A mudança em relação ao Paper 1 é fundamental.

No Paper 1, o consenso decidia essencialmente **quanto FV cortar**.

Agora:

\[
\boxed{\text{Consenso}\rightarrow\text{BESS}\rightarrow\text{Curtailment residual}}
\]

O armazenamento passa a ser um recurso físico com memória temporal.

## Hipóteses

### H2.1 — Coordenação

> Diferentes arquiteturas de consenso, mesmo produzindo regulação de tensão semelhante, resultam em diferentes distribuições de utilização dos BESS e, consequentemente, diferentes instantes de saturação e necessidade de curtailment.

Dois métodos podem produzir:

\[
V_{\max}\le1.05
\]

mas fazer isso de formas completamente diferentes.

Exemplo:

\[
SOC=[80,80,35,22]\%
\]

versus:

\[
SOC=[58,61,57,59]\%
\]

A tensão isoladamente esconderia essa diferença.

### H2.2 — Saturação e curtailment

> Estratégias que distribuem melhor o esforço entre os BESS retardam a saturação de unidades individuais e podem reduzir o curtailment residual.

### H2.3 — Robustez

> Estratégias distribuídas diferem na capacidade de manter a regulação de tensão quando um BESS atinge o limite de SOC ou se torna indisponível.

### H2.4 — Hosting Capacity

> A arquitetura de coordenação pode alterar a hosting capacity mesmo quando potência e energia totais instaladas de BESS permanecem idênticas.

Isto significa:

\[
\text{mesmo hardware}
\neq
\text{mesma HC}
\]

dependendo apenas da forma de coordenação.

---

# Método do Paper 2

## Rede

- IEEE 34 barras;
- AltDSS-Python;
- mesmos pontos FV já consolidados nos experimentos anteriores;
- configuração final congelada antes da comparação.

## Tempo

Manter inicialmente:

\[
24\text{ snapshots}\times1h
\]

Sem usar o avanço temporal automático do `Daily` como motor do experimento.

O Python controla:

\[
t=0,1,\ldots,23
\]

Dentro de cada hora:

\[
\text{perfil}
\rightarrow SolveSnap
\rightarrow consenso
\rightarrow SolveSnap
\rightarrow\cdots
\rightarrow convergência
\rightarrow integração\ do\ SOC
\]

A integração energética ocorre **uma única vez por hora**.

## Modelo físico do BESS

O Paper 2 deve incluir pelo menos:

\[
SOC_{\min}\le SOC_i(t)\le SOC_{\max}
\]

\[
0\le P_{ch,i}\le P_{ch,max,i}
\]

\[
0\le P_{dis,i}\le P_{dis,max,i}
\]

\[
E_i(t+\Delta t)
=
E_i(t)+\eta_cP_{ch,i}\Delta t-
\frac{P_{dis,i}\Delta t}{\eta_d}
\]

A descarga pode ficar desabilitada na operação normal diurna neste paper, mas a equação deve existir no modelo para permitir evolução posterior.

## Métodos candidatos

| Método | Papel |
|---|---|
| Sem controle | referência elétrica |
| BESS local | benchmark descentralizado |
| Consenso proporcional | continuidade do Paper 1 |
| Olfati-Saber | consenso clássico |
| CORA/iCORA | saturação e redistribuição |
| Leader–Follower | arquitetura coordenada |
| Leaderless | arquitetura distribuída sem líder |

Não é necessário que todos apareçam no artigo final.

A estratégia recomendada é:

1. executar o screening completo;
2. identificar comportamentos realmente distintos;
3. selecionar os métodos que representem famílias metodológicas diferentes.

## Métricas

Medir:

\[
V_{\max}(t),\quad V_{\min}(t)
\]

- número e duração das violações;
- \(P_{BESS,i}(t)\);
- \(SOC_i(t)\);
- \(E_{BESS,i}\);
- tempo até a primeira saturação;
- número de unidades indisponíveis;
- \(E_{curt}\);
- \(Curt\%\);
- Hosting Capacity.

Também deve ser introduzida uma métrica explícita de **desigualdade de utilização**, por exemplo:

\[
\sigma_{SOC}
\]

ou coeficiente de variação do throughput energético dos BESS.

---

# Etapas do Paper 2

| Etapa | Função |
|---|---|
| **P2.0 — Caracterização** | rodar IEEE 34 sem controle e localizar exatamente as violações |
| **P2.1 — Modelo BESS** | implementar SOC, limites, eficiência e saturação |
| **P2.2 — Dimensionamento experimental** | encontrar kW/kWh que não torne o problema trivial |
| **P2.3 — Controle local** | estabelecer benchmark |
| **P2.4 — Consensos existentes** | proporcional, Olfati, CORA |
| **P2.5 — Leader–Follower** | implementar/revisar arquitetura |
| **P2.6 — Leaderless** | implementar arquitetura distribuída sem líder |
| **P2.7 — Saturação** | SOC inicial heterogêneo |
| **P2.8 — Falha** | indisponibilidade de um BESS |
| **P2.9 — Hosting Capacity** | varredura da potência FV |
| **P2.10 — Paper** | selecionar casos que explicam os fenômenos encontrados |

## Resultados esperados do Paper 2

Não se deve formular o estudo como tentativa de provar que um único método é superior.

O objetivo é identificar **trade-offs**.

Exemplos possíveis:

\[
CORA\rightarrow menor\ curtailment
\]

mas:

\[
Leaderless\rightarrow melhor\ equilíbrio\ de\ SOC
\]

e:

\[
Leader-Follower\rightarrow menor\ esforço\ computacional
\]

Esse tipo de resultado é mais cientificamente útil do que tentar estabelecer um único “vencedor”.

---

# PAPER 3 — Coordenação técnica multi-recurso

Somente depois de saber qual arquitetura BESS é mais adequada.

O consenso será congelado.

A nova pergunta deixa de ser:

> Qual consenso?

e passa a ser:

> **Qual é a melhor maneira de utilizar os recursos elétricos disponíveis?**

---

# Hipóteses do Paper 3

### H3.1 — Reativo antes do armazenamento

> O uso de potência reativa dos inversores FV antes da convocação da potência ativa dos BESS reduz o throughput energético necessário do armazenamento mantendo o controle de tensão.

Comparação:

\[
P_{BESS}\rightarrow Curt
\]

contra:

\[
Q_{PV}\rightarrow P_{BESS}\rightarrow Curt
\]

### H3.2 — Despacho temporal

> A descarga programada fora do período solar libera capacidade energética para o ciclo subsequente e melhora simultaneamente o aproveitamento do BESS e determinadas condições elétricas da rede.

Isso transforma:

\[
SOC_{fim}
\]

em variável operacional relevante.

### H3.3 — Interação entre \(Q\) e despacho

> O benefício combinado de \(Q\) e despacho temporal não precisa ser igual à soma dos benefícios isolados.

Esta passa a ser uma hipótese de interação.

---

# Desenho experimental do Paper 3

Usar um **fatorial 2×2**:

| Caso | \(Q\) | Descarga programada |
|---|---:|---:|
| T0 | Não | Não |
| T1 | Sim | Não |
| T2 | Não | Sim |
| T3 | Sim | Sim |

Manter idênticos:

- consenso;
- BESS;
- PV;
- rede;
- curvas;
- SOC;
- limites operacionais.

Isso permite isolar:

\[
Effect_Q
\]

\[
Effect_{dispatch}
\]

e

\[
Interaction_{Q\times dispatch}
\]

---

# Despacho noturno

Não deve ser simplesmente:

> “às 20h descarregue a bateria”.

Devem ser distinguidas pelo menos três políticas:

| Política | Critério |
|---|---|
| Técnica | demanda/tensão |
| Temporal | janela horária definida |
| Técnico-econômica | preço + estado da rede + necessidade de liberar SOC |

Para o **Paper 3 técnico**, a recomendação é iniciar com uma política técnica objetiva.

Exemplos:

\[
V<V_{ref}
\]

ou demanda acima de determinado patamar.

O preço ainda não entra neste paper.

---

# Resolução temporal do Paper 3

Começar por:

\[
24\times1h
\]

para compatibilidade com o Paper 2.

Depois realizar análise de sensibilidade com:

\[
96\times15min
\]

ou:

\[
48\times30min
\]

Se as conclusões forem estáveis, manter 1 h.

Se \(Q\), saturação ou dispatch apresentarem comportamento perdido em 1 h, o Paper 3 deve adotar resolução menor.

---

# Resultados do Paper 3

As métricas principais passam a incluir:

\[
E_{BESS,ch}
\]

\[
E_{BESS,dis}
\]

\[
E_{throughput}
\]

\[
Q_{PV,varh}
\]

\[
E_{curt}
\]

\[
SOC(t)
\]

\[
V_{\max},V_{\min}
\]

além de, quando relevante:

- perdas;
- peak shaving;
- Hosting Capacity.

O resultado científico esperado não é necessariamente que T3 seja superior em todos os critérios.

Um resultado como:

> \(Q\) reduz pouco a sobretensão, mas diminui significativamente o throughput do BESS em determinados pontos da rede

continua sendo relevante.

---

# PAPER 4 — Avaliação técnico-econômica e Value Stacking

Este trabalho será a evolução direta do Paper 1.

No Paper 1, a análise econômica era essencialmente:

\[
E_{curt}(t)\times PLD(t)
\]

Agora, o objetivo será passar de:

\[
\text{custo da energia cortada}
\]

para:

\[
\boxed{\text{valor econômico da flexibilidade}}
\]

---

# Hipóteses do Paper 4

### H4.1 — Valor do despacho

> A energia armazenada durante períodos de excesso FV possui valor diferente dependendo de quando é posteriormente descarregada.

Assim:

\[
1\ kWh_{armazenado}
\]

não é economicamente equivalente em todos os horários.

### H4.2 — Valor indireto de \(Q\)

> A utilização de potência reativa pode produzir benefício econômico indireto ao preservar capacidade energética e reduzir throughput do BESS.

### H4.3 — Curtailment versus degradação

> Minimizar curtailment não necessariamente minimiza custo total quando a redução do corte exige aumento significativo do throughput do BESS.

Pode ocorrer:

\[
E_{curt}\downarrow
\]

mas:

\[
C_{deg}\uparrow
\]

### H4.4 — Sizing

> O controle pode alterar o dimensionamento economicamente justificável do BESS.

A pergunta passa de:

> quanto a bateria custa?

para:

> **quanto armazenamento precisamos para atingir determinada HC ou determinado limite de curtailment?**

---

# Estrutura econômica

Inicialmente:

\[
C_{curt}
=
\sum_t E_{curt}(t)\frac{PLD(t)}{1000}
\]

Depois:

\[
R_{dis}
=
\sum_t E_{dis}(t)\frac{PLD(t)}{1000}
\]

Podem ser adicionados:

\[
C_{loss}
\]

e:

\[
C_{deg}
=
c_{throughput}
\sum_t(E_{ch}+E_{dis})
\]

Uma função econômica conceitual pode assumir:

\[
J=
C_{curt}
+C_{loss}
+C_{deg}
-R_{dis}
\]

Não é necessário transformar imediatamente isso em OPF/MPC.

A avaliação pode inicialmente ser feita **ex post** sobre os resultados técnicos.

---

# Conexão entre os trabalhos

A dependência lógica fica:

\[
\boxed{\text{Paper 1}}
\]

Qual protocolo distribui melhor o curtailment?

↓

\[
\boxed{\text{Paper 2}}
\]

Como esses princípios de coordenação se comportam quando o recurso passa a ser um **BESS limitado por energia e SOC**?

↓

\[
\boxed{\text{Paper 3}}
\]

Como utilizar de maneira coordenada:

\[
Q + BESS_{charge}+BESS_{discharge}+Curtailment
\]

ao longo do dia?

↓

\[
\boxed{\text{Paper 4}}
\]

Qual o valor econômico dessa flexibilidade e quanto armazenamento é justificável?

---

# Papel de cada variável ao longo da linha

| Variável | P1 | P2 | P3 | P4 |
|---|---:|---:|---:|---:|
| Consenso | núcleo | núcleo | fixo | fixo |
| Curtailment | núcleo | residual | residual | econômico |
| BESS | — | núcleo | núcleo | ativo econômico |
| SOC | — | núcleo | núcleo | restrição econômica |
| Saturação | — | núcleo | núcleo | custo/consequência |
| Hosting Capacity | opcional | núcleo | núcleo | valor econômico |
| \(Q\) | — | — | núcleo | valor indireto |
| Descarga | — | mínima/controle | núcleo | núcleo |
| PLD | núcleo | — | — | núcleo |
| Degradação | — | — | throughput técnico | custo |
| Sizing | — | sensibilidade | fixo | econômico |

---

# Infraestrutura única de experimentação

A partir de agora, deve-se evitar produzir um `.py` monolítico diferente para cada paper.

A skill **Executor_altGRID_consenso** deve evoluir para um motor comum em que cada experimento apenas fornece configuração:

```text
rede
curvas
PVs
BESS
controle
protocolo
cenários
métricas
```

e o executor realiza:

```text
montar
→ validar
→ executar snapshots
→ controlar
→ integrar energia
→ registrar
→ exportar
→ plotar
```

Isso é importante porque Paper 3 e Paper 4 deverão reproduzir exatamente cenários do Paper 2.

---

# Caminho operacional a partir de agora

| Ordem | Trabalho |
|---:|---|
| **1** | congelar IEEE 34, cargas, curva FV e barras |
| **2** | eliminar definitivamente dependência temporal do `Daily` automático |
| **3** | implementar executor de 24 snapshots controlados por Python |
| **4** | caracterizar rede sem controle |
| **5** | corrigir modelo físico de BESS |
| **6** | determinar sizing experimental que produza saturação não trivial |
| **7** | reproduzir nosso consenso atual |
| **8** | incorporar proporcional/Olfati/CORA |
| **9** | implementar leader–follower de forma rigorosa |
| **10** | implementar leaderless |
| **11** | rodar experimento nominal |
| **12** | testar SOC inicial heterogêneo |
| **13** | testar indisponibilidade de agente |
| **14** | executar Hosting Capacity |
| **15** | selecionar os métodos que efetivamente entram no Paper 2 |
| **16** | congelar o controlador escolhido para o Paper 3 |
| **17** | introduzir \(Q\) e despacho temporal |
| **18** | transformar os resultados técnicos no Paper 4 econômico |

---

# Objetivo final da linha

O objetivo maior não é provar que “consenso é melhor”.

O objetivo é:

> **Desenvolver e avaliar uma arquitetura distribuída de gestão de flexibilidade para redes de distribuição com alta penetração fotovoltaica, determinando como coordenação, armazenamento, suporte reativo, curtailment e despacho temporal afetam hosting capacity, utilização dos ativos e valor econômico.**

Cada paper deve responder **uma pergunta causal própria**, evitando acumular funcionalidades em um único experimento e preservando a capacidade de atribuir os resultados às variáveis efetivamente modificadas.
