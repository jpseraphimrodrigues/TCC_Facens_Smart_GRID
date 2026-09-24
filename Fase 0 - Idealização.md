# Fase 0 — Impacto de Falhas de Comunicação no Consenso Proporcional aplicado ao Controle de Inversores Fotovoltaicos

## 1. Conceito geral

Esta **Fase 0** constitui um experimento preliminar destinado a avaliar como falhas na rede de comunicação afetam um sistema de controle distribuído baseado em **consenso proporcional**, aplicado à coordenação de inversores fotovoltaicos em uma rede de distribuição.

O trabalho será inicialmente desenvolvido como **Trabalho de Conclusão de Curso — TCC**, em formato de artigo científico com limite aproximado de 15 páginas.

Ao mesmo tempo, o experimento será estruturado de forma que possa posteriormente ser expandido no âmbito do mestrado, no qual poderão ser investigadas estratégias mais avançadas de controle distribuído, robustez a falhas, coordenação de recursos energéticos distribuídos, BESS, potência reativa e Hosting Capacity.

A Fase 0 não terá como objetivo propor um novo algoritmo tolerante a falhas.

O objetivo será primeiro **caracterizar quantitativamente a vulnerabilidade do consenso proporcional diante de falhas de comunicação e verificar até que ponto essa degradação afeta o comportamento elétrico da rede**.

---

# 2. Problema de pesquisa

Sistemas de controle distribuído baseados em consenso dependem da troca de informações entre diferentes agentes.

Em implementações teóricas, é comum assumir uma rede de comunicação:

* disponível;
* estável;
* síncrona;
* sem perda de mensagens;
* sem interrupções;
* com topologia conhecida.

Entretanto, sistemas reais podem apresentar:

* perda de enlaces;
* indisponibilidade temporária de agentes;
* perda de pacotes;
* alterações de topologia;
* particionamento da rede de comunicação.

A questão central desta Fase 0 é verificar como essas falhas afetam não apenas o algoritmo de consenso, mas também o sistema elétrico que está sendo controlado.

A cadeia causal investigada será:

```text
Falha de comunicação
        ↓
Alteração do grafo de comunicação
        ↓
Degradação ou perda da convergência do consenso
        ↓
Alteração da distribuição do esforço de controle
        ↓
Alteração do curtailment dos inversores
        ↓
Impacto sobre as tensões da rede elétrica
```

---

# 3. Pergunta de pesquisa

> **Qual é o impacto de falhas de comunicação sobre a convergência e o desempenho elétrico de um controle distribuído baseado em consenso proporcional aplicado à coordenação de inversores fotovoltaicos em uma rede de distribuição?**

Uma questão secundária relevante será:

> **A perda do consenso implica necessariamente perda de desempenho elétrico ou existe uma faixa de degradação da comunicação na qual a rede ainda permanece eletricamente segura?**

Essa segunda pergunta poderá ser particularmente importante para o desenvolvimento posterior da pesquisa de mestrado.

---

# 4. Objetivo geral

Avaliar o impacto de falhas de comunicação no desempenho de um controle distribuído baseado em consenso proporcional aplicado à mitigação de sobretensão por meio da coordenação do curtailment de inversores fotovoltaicos.

---

# 5. Objetivos específicos

1. Implementar uma rede de distribuição de referência baseada no sistema IEEE de 34 barras.

2. Inserir múltiplos sistemas fotovoltaicos distribuídos ao longo do alimentador.

3. Implementar um algoritmo de consenso proporcional para distribuir o esforço de curtailment entre os inversores.

4. Representar explicitamente a rede de comunicação por meio de um grafo independente da topologia elétrica.

5. Simular diferentes condições de falha na rede de comunicação.

6. Avaliar o comportamento do algoritmo de consenso em condições normais e degradadas.

7. Quantificar os efeitos das falhas de comunicação sobre:

   * convergência;
   * erro de consenso;
   * distribuição do curtailment;
   * tensão da rede;
   * violações dos limites operacionais.

8. Identificar condições nas quais a comunicação é degradada, mas o desempenho elétrico continua aceitável.

9. Estabelecer uma base experimental que possa posteriormente ser ampliada no trabalho de mestrado.

---

# 6. Hipóteses

## H1 — Efeito da degradação da comunicação

A degradação da rede de comunicação aumenta o erro e/ou o tempo de convergência do consenso proporcional.

---

## H2 — Efeito sobre a distribuição do esforço de controle

Falhas de comunicação podem provocar distribuição desigual ou inadequada do curtailment entre os inversores participantes.

---

## H3 — Relação entre consenso e desempenho elétrico

A degradação do consenso não implica necessariamente violação imediata dos limites elétricos da rede.

Pode existir uma região operacional na qual:

```text
consenso degradado
       ↓
distribuição de controle menos adequada
       ↓
rede ainda eletricamente segura
```

---

## H4 — Particionamento do grafo

Falhas que preservam a conectividade do grafo de comunicação devem apresentar comportamento distinto das falhas que produzem seu particionamento.

Em particular:

$$
\lambda_2(L) > 0
$$

indica um grafo conectado, enquanto:

$$
\lambda_2(L)=0
$$

indica perda da conectividade global.

A conectividade algébrica poderá, portanto, ser utilizada como uma variável complementar para caracterizar a severidade estrutural da falha.

---

# 7. Sistema elétrico

## 7.1 Alimentador

Será utilizado inicialmente o:

> **IEEE 34-Bus Distribution Test Feeder**

O alimentador será modelado utilizando:

* OpenDSS / AltDSS;
* Python;
* AltDSS-Python.

A utilização do IEEE 34 barras permite reaproveitar a infraestrutura experimental já desenvolvida para estudos anteriores.

---

# 8. Geração fotovoltaica

Serão inicialmente instalados:

> **5 sistemas fotovoltaicos distribuídos**

Os sistemas deverão ser posicionados em diferentes regiões elétricas do alimentador.

A distribuição deverá incluir, preferencialmente:

* inversores próximos à origem do alimentador;
* inversores em regiões intermediárias;
* inversores em regiões eletricamente mais fracas.

Representação conceitual:

```text
Subestação
    │
    ├──────── PV1
    │
    ├──────────── PV2
    │
    ├──────────────── PV3
    │
    ├──────────────────── PV4
    │
    └──────────────────────── PV5
```

As barras exatas, potências nominais e perfis de geração serão definidos durante a implementação.

---

# 9. Variável controlada

Nesta Fase 0 será utilizado apenas o controle de potência ativa por curtailment.

Para cada inversor:

$$
P_i =
P_{\mathrm{PV},i}
-
P_{\mathrm{curt},i}
$$

onde:

* \(P_i\) = potência ativa efetivamente injetada;
* \(P_{\mathrm{PV},i}\) = potência fotovoltaica disponível;
* \(P_{\mathrm{curt},i}\) = potência reduzida pelo controle.

Inicialmente não serão considerados:

* controle de potência reativa;
* Volt-VAR;
* Volt-Watt;
* armazenamento em baterias;
* OPF;
* despacho econômico.

Essa escolha busca isolar a relação causal entre:

```text
comunicação
→ consenso
→ curtailment
→ tensão
```

---

# 10. Consenso proporcional

O controle distribuído será baseado em um algoritmo de consenso proporcional entre os inversores participantes.

O princípio básico será distribuir o esforço global de controle entre os agentes segundo sua capacidade ou disponibilidade.

Para um determinado instante:

$$
P_{\mathrm{curt,total}}
=
\sum_{i=1}^{N}
P_{\mathrm{curt},i}
$$

O esforço relativo de cada inversor pode ser caracterizado por:

$$
r_i =
\frac{P_{\mathrm{curt},i}}
{P_{\mathrm{available},i}}
$$

Em uma situação ideal de compartilhamento proporcional:

$$
r_1 \approx
r_2 \approx
\ldots
\approx
r_N
$$

ou segundo a ponderação definida pelo protocolo utilizado.

O algoritmo empregado será posteriormente formalizado a partir da formulação de consenso já utilizada nos experimentos anteriores.

---

# 11. Separação entre rede elétrica e rede de comunicação

Um princípio metodológico fundamental será representar separadamente:

## Rede elétrica

Define:

* barras;
* linhas;
* cargas;
* sistemas FV;
* fluxos de potência;
* tensões.

## Rede de comunicação

Define:

* agentes;
* enlaces;
* vizinhanças;
* disponibilidade de mensagens;
* topologia do consenso.

Portanto:

```text
REDE ELÉTRICA

Subestação ─────────────── Alimentador

       PV1     PV2     PV3     PV4     PV5
        │       │       │       │       │
      Inv1    Inv2    Inv3    Inv4    Inv5
```

e, paralelamente:

```text
REDE DE COMUNICAÇÃO

Inv1 ── Inv2 ── Inv3 ── Inv4 ── Inv5
```

A topologia da comunicação não precisará reproduzir diretamente a topologia elétrica.

---

# 12. Grafo de comunicação

A rede de comunicação será representada por:

$$
G=(V,E)
$$

onde:

* \(V\) representa os agentes;
* \(E\) representa os enlaces de comunicação.

Serão utilizados conceitos como:

* matriz de adjacência;
* matriz de grau;
* matriz Laplaciana;
* conectividade do grafo;
* conectividade algébrica.

A matriz Laplaciana será:

$$
L=D-A
$$

onde:

* \(D\) = matriz de graus;
* \(A\) = matriz de adjacência.

A segunda menor autovalor da Laplaciana:

$$
\lambda_2(L)
$$

poderá ser utilizada como indicador da conectividade da rede.

---

# 13. Cenário de referência

## C0 — Comunicação ideal

Todos os agentes comunicam-se normalmente.

Não há:

* perda de mensagens;
* perda de enlaces;
* indisponibilidade de agentes.

Esse cenário funcionará como baseline para os demais experimentos.

---

# 14. Cenários de falha

O escopo inicial deverá permanecer pequeno.

## C1 — Perda de enlace sem particionamento

Um enlace da rede de comunicação será removido, mas o grafo continuará conectado.

Exemplo:

```text
ANTES

1 ── 2 ── 3 ── 4 ── 5
     │         │
     └─────────┘
```

Após perda de um enlace:

```text
1 ── 2    3 ── 4 ── 5
     │    │
     └────┘
```

O sistema ainda possui caminho de comunicação entre todos os agentes.

Objetivo:

> verificar se a convergência permanece possível e qual é a degradação do desempenho.

---

# 15. C2 — Particionamento da rede

Uma falha deverá produzir dois grupos desconectados.

Exemplo:

```text
1 ── 2       3 ── 4 ── 5
```

A partir desse instante:

```text
Grupo A     Grupo B

1 ── 2     3 ── 4 ── 5
```

Não existe mais consenso global.

Esse caso deverá permitir avaliar:

* formação de consensos locais;
* alteração da distribuição de curtailment;
* comportamento da tensão;
* eventual violação dos limites elétricos.

---

# 16. C3 — Falha temporária de um agente

Um agente poderá deixar temporariamente de transmitir e/ou receber informações.

Exemplo:

```text
t < tf

1 ── 2 ── 3 ── 4 ── 5
```

Durante a falha:

```text
1 ── 2    [3 OFF]    4 ── 5
```

Após recuperação:

```text
1 ── 2 ── 3 ── 4 ── 5
```

O objetivo será observar o comportamento transitório do consenso e sua recuperação.

---

# 17. C4 — Perda probabilística de mensagens

Caso o desenvolvimento experimental permaneça suficientemente simples, poderá ser incluído um cenário adicional de packet loss.

Cada mensagem poderá possuir uma probabilidade:

$$
p_{\mathrm{loss}}
$$

de não ser recebida.

Por exemplo:

$$
p_{\mathrm{loss}}
=
0,\ 5\%,\ 10\%,\ 20\%,\ 30\%
$$

Esse cenário deverá ser considerado complementar, não obrigatório para a primeira versão do TCC.

---

# 18. Cenário inicialmente excluído — atraso de comunicação

Atrasos serão inicialmente deixados fora da Fase 0.

A introdução de atraso exige modelagem adicional envolvendo:

* sincronização;
* memória de estados anteriores;
* latência;
* controle assíncrono;
* estabilidade diante de dados defasados.

Esses elementos são mais apropriados para uma expansão posterior da pesquisa.

---

# 19. Estratégias de comparação

O experimento deverá conter pelo menos:

### A — Sem controle

Nenhuma ação coordenada é aplicada aos inversores.

### B — Consenso proporcional com comunicação ideal

Representa o desempenho nominal do método.

### C — Consenso proporcional com comunicação degradada

Representa os diferentes cenários de falha.

Um controle exclusivamente local poderá posteriormente ser incluído como benchmark adicional caso seja necessário responder à questão:

> Por que utilizar controle distribuído baseado em comunicação em vez de controle puramente local?

---

# 20. Métricas de controle

## 20.1 Erro de consenso

Uma possível métrica será:

$$
e_c(k)=
\sqrt{
\frac{1}{N}
\sum_{i=1}^{N}
\left(
x_i(k)-\bar{x}(k)
\right)^2
}
$$

onde:

$$
\bar{x}(k)=
\frac{1}{N}
\sum_i x_i(k)
$$

---

## 20.2 Número de iterações

Será registrado:

$$
N_{\mathrm{iter}}
$$

necessário para atingir um determinado critério de convergência.

---

## 20.3 Critério de convergência

Poderá ser adotado:

$$
e_c(k)<\varepsilon
$$

durante determinado número de iterações consecutivas.

O valor de \(\varepsilon\) será posteriormente definido.

---

## 20.4 Estado final dos agentes

Serão armazenados:

$$
x_1,\ x_2,\ldots,x_N
$$

permitindo comparar diretamente os agentes após cada cenário de falha.

---

# 21. Métricas elétricas

## 21.1 Máxima tensão

$$
V_{\max}
=
\max_{b,t}
V_b(t)
$$

---

## 21.2 Violações de tensão

Será contabilizado:

$$
N_{V>V_{\mathrm{lim}}}
$$

e/ou o tempo total de violação:

$$
T_{V>V_{\mathrm{lim}}}
$$

Inicialmente poderá ser adotado:

$$
V_{\mathrm{lim}}=1.05\;pu
$$

---

# 22. Curtailment

A energia total curtailed poderá ser calculada por:

$$
E_{\mathrm{curt}}
=
\sum_t
\sum_i
P_{\mathrm{curt},i}(t)
\Delta t
$$

Também deverão ser observados:

$$
P_{\mathrm{curt},1},
P_{\mathrm{curt},2},
\ldots,
P_{\mathrm{curt},5}
$$

separadamente.

---

# 23. Métrica de proporcionalidade

Poderá ser utilizada:

$$
r_i=
\frac{P_{\mathrm{curt},i}}
{P_{\mathrm{available},i}}
$$

e posteriormente uma medida de dispersão:

$$
\sigma_r
=
\sqrt{
\frac{1}{N}
\sum_i
(r_i-\bar r)^2
}
$$

Quanto menor:

$$
\sigma_r
$$

mais próximo o sistema estará de um compartilhamento proporcional uniforme.

---

# 24. Estrutura preliminar dos experimentos

Uma matriz experimental inicial poderá assumir a seguinte forma:

| Caso | Comunicação             | Grafo conectado | Falha temporária | Packet loss |
| ---- | ----------------------- | --------------: | ---------------: | ----------: |
| C0   | Normal                  |             Sim |              Não |          0% |
| C1   | Perda de enlace         |             Sim |              Não |          0% |
| C2   | Particionamento         |             Não |              Não |          0% |
| C3   | Agente indisponível     |        variável |              Sim |          0% |
| C4   | Comunicação estocástica |        variável |         variável |       5–30% |

O C4 poderá ser removido da versão final do TCC caso o volume experimental se torne excessivo.

---

# 25. Resultados principais esperados

Os experimentos deverão produzir pelo menos:

## Figura 1 — Sistema elétrico

Diagrama simplificado do IEEE 34 barras indicando os sistemas fotovoltaicos.

## Figura 2 — Grafo de comunicação

Representação dos cinco agentes e seus enlaces.

## Figura 3 — Convergência

Exemplo:

```text
erro de consenso
      │\
      │ \
      │  \        C1
      │   \____
      │
      │\____________ C0
      │
      │────── C2
      └───────────────── iterações
```

## Figura 4 — Tensões

Comparação de:

$$
V_{\max}
$$

entre os cenários.

## Figura 5 — Curtailment

Distribuição da potência reduzida entre os cinco inversores.

---

# 26. Resultado cientificamente mais relevante

O resultado mais interessante não será simplesmente demonstrar que:

> quando a comunicação falha, o consenso piora.

Isso é previsível.

O ponto mais relevante será verificar se existe uma região intermediária:

```text
DEGRADAÇÃO DA COMUNICAÇÃO
            ↓
DEGRADAÇÃO DO CONSENSO
            ↓
PERDA DE PROPORCIONALIDADE
            ↓
MAS
            ↓
REDE AINDA ELETRICAMENTE SEGURA
```

Caso essa região seja observada, poderá ser identificada uma espécie de:

> **limiar de tolerância da rede de controle à degradação da comunicação.**

Esse conceito poderá constituir uma linha relevante para expansão posterior no mestrado.

---

# 27. O que a Fase 0 não pretende fazer

A Fase 0 não buscará:

* desenvolver um protocolo completo tolerante a falhas;
* reconstruir automaticamente a rede de comunicação;
* implementar detecção avançada de falhas;
* estudar ataques cibernéticos;
* estudar comunicação 5G/6G;
* modelar protocolos físicos de telecomunicação;
* implementar OPF;
* utilizar BESS;
* controlar simultaneamente \(P\) e \(Q\);
* maximizar Hosting Capacity;
* realizar análise econômica;
* otimizar a topologia de comunicação.

Esses elementos poderão ser investigados posteriormente.

---

# 28. Relação com o mestrado

A Fase 0 será utilizada como estudo preliminar para uma investigação mais ampla.

## Fase 0 — TCC

```text
Falha de comunicação
        ↓
Degradação do consenso
        ↓
Impacto no controle
        ↓
Impacto elétrico
```

Pergunta:

> O que acontece quando a rede de comunicação deixa de ser ideal?

---

## Evolução futura

Uma etapa posterior poderá investigar:

```text
Falha de comunicação
        ↓
Detecção da falha
        ↓
Adaptação da topologia
        ↓
Controle distribuído robusto
        ↓
Manutenção do desempenho
```

O estudo poderá então incorporar:

* grafos variantes no tempo;
* comunicação assíncrona;
* atrasos;
* perda estocástica de pacotes;
* agentes plug-and-play;
* fallback local;
* reconstrução dinâmica do grafo;
* BESS;
* controle conjunto \(P/Q\);
* Hosting Capacity;
* curtailment;
* critérios econômicos;
* critérios de equidade.

---

# 29. Arquitetura computacional sugerida

A implementação deverá manter separados:

```text
electrical/
    feeder
    pv
    powerflow

communication/
    graph
    links
    failures

control/
    consensus
    proportional_dispatch

simulation/
    scenarios
    sequential_runner

metrics/
    consensus
    voltage
    curtailment
    communication

results/
    csv
    plots
    reports
```

Essa separação será importante para permitir a evolução posterior do experimento.

---

# 30. Fluxo computacional

```text
INÍCIO
  │
  ▼
Carregar IEEE 34
  │
  ▼
Inserir 5 sistemas FV
  │
  ▼
Executar power flow
  │
  ▼
Existe sobretensão?
  │
  ├── NÃO ──► próximo instante
  │
  └── SIM
        │
        ▼
Calcular necessidade de controle
        │
        ▼
Aplicar estado da rede de comunicação
        │
        ▼
Executar consenso proporcional
        │
        ▼
Determinar curtailment por inversor
        │
        ▼
Atualizar PVs
        │
        ▼
Executar novo power flow
        │
        ▼
Registrar métricas
        │
        ▼
Próximo instante/cenário
```

---

# 31. Estratégia inicial de implementação

## Etapa 1

Reproduzir o sistema IEEE 34 com os sistemas FV.

## Etapa 2

Produzir um caso em que exista sobretensão sem controle.

## Etapa 3

Implementar o consenso proporcional com comunicação perfeita.

## Etapa 4

Validar que o controle:

* converge;
* distribui o esforço corretamente;
* reduz a sobretensão.

## Etapa 5

Criar explicitamente o grafo de comunicação.

## Etapa 6

Implementar remoção de enlaces.

## Etapa 7

Implementar particionamento do grafo.

## Etapa 8

Implementar indisponibilidade temporária de um agente.

## Etapa 9

Executar os cenários e registrar métricas.

## Etapa 10

Comparar os resultados.

---

# 32. Estrutura preliminar do paper do TCC

Considerando um limite aproximado de 15 páginas:

## 1. Introdução

Aproximadamente:

> 1,5–2 páginas

Conteúdo:

* crescimento da geração fotovoltaica distribuída;
* sobretensão;
* necessidade de coordenação entre DERs;
* controle distribuído;
* dependência de comunicação;
* problema de pesquisa;
* contribuição do trabalho.

---

## 2. Fundamentação e trabalhos relacionados

Aproximadamente:

> 2–2,5 páginas

Conteúdo:

* geração distribuída e sobretensão;
* curtailment;
* controle distribuído;
* consenso;
* comunicação entre agentes;
* falhas de comunicação;
* lacuna investigada.

---

## 3. Metodologia

Aproximadamente:

> 3–3,5 páginas

Conteúdo:

* IEEE 34;
* localização dos PVs;
* modelo dos inversores;
* consenso proporcional;
* grafo de comunicação;
* cenários de falha;
* métricas.

---

## 4. Resultados

Aproximadamente:

> 3–4 páginas

Apresentar:

* convergência;
* erro;
* tensões;
* curtailment;
* comparação entre cenários.

---

## 5. Discussão

Aproximadamente:

> 1,5–2 páginas

Interpretar:

* influência da conectividade;
* efeito da falha sobre o consenso;
* efeito da falha sobre a rede elétrica;
* diferença entre falha algorítmica e falha elétrica;
* limitações.

---

## 6. Conclusão

Aproximadamente:

> 0,5–1 página

Responder diretamente à pergunta de pesquisa.

---

## Referências

Literatura sobre:

* consenso;
* controle distribuído;
* DERs;
* sistemas multiagentes;
* comunicação;
* controle de tensão;
* curtailment;
* falhas de comunicação.

---

# 33. Título provisório

Uma primeira opção:

> **Impacto de Falhas de Comunicação em um Controle Distribuído por Consenso Proporcional aplicado a Inversores Fotovoltaicos**

Alternativa:

> **Avaliação da Robustez de um Controle Distribuído por Consenso Proporcional frente a Falhas de Comunicação em Redes de Distribuição com Geração Fotovoltaica**

A primeira formulação é mais conservadora.

A segunda utiliza o termo **robustez**, que deverá ser usado com cautela caso o trabalho apenas caracterize falhas sem propor ou demonstrar formalmente tolerância robusta.

---

# 34. Síntese da Fase 0

A Fase 0 poderá ser resumida por:

$$
\boxed{
\text{IEEE 34}
+
\text{5 inversores FV}
+
\text{curtailment}
+
\text{consenso proporcional}
+
\text{falha de comunicação}
}
$$

A variável experimental principal será a condição da rede de comunicação.

As respostas observadas serão:

$$
\boxed{
\text{convergência}
+
\text{proporcionalidade}
+
\text{curtailment}
+
\text{tensão}
}
$$

A contribuição do TCC será caracterizar como a degradação da comunicação se propaga da camada de controle para a camada física da rede elétrica.

A extensão natural para o mestrado será transformar essa caracterização inicial em um problema de **controle distribuído tolerante a falhas de comunicação**.
