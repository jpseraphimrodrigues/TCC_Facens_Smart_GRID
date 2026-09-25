# Auditoria técnica do experimento — TCC FACENS

Data: 2026-09-25  
Escopo: código, modelo IEEE 34 barras, entradas, resultados, documentação e empacotamento.

## Parecer executivo

O repositório contém um experimento executável para comparar `leader_follower` e `leaderless` com seis agentes PV, sete cenários, simulação quase-estática de 24 horas, métricas elétricas, consenso, comunicação e manifesto de execução.

A formulação que os artefatos sustentam é:

> comparação de controle distribuído de tensão e curtailment proporcional sob remoção determinística de enlaces e isolamento temporário de agentes, em snapshots horários, no alimentador IEEE 34 barras.

Não é tecnicamente correto, no estado atual, apresentar o trabalho como avaliação geral de perda aleatória de pacotes, atraso, fila, mensagens obsoletas ou robustez de uma rede real. As mensagens são classificadas como `ENTREGUE`/`PERDIDA`, mas não são armazenadas nem consumidas por uma camada de entrega: a dinâmica usa diretamente a matriz de adjacência no consenso.

> Necessária investigação de correção da fução que simula a falha implementar corretamente essa falha, ou de como a falha é detectada, a fim de validar o método.

Há uma ressalva de rastreabilidade: `Resultados/FASE0_EXP001/manifest.json` registra o commit `7219216` e execução em `2026-09-24`, mas o checkout auditado está em `797f18d` (`Adaptacao_readme`). Os números deste documento são, portanto, resultados versionados do manifesto, não uma prova de execução pelo checkout atual.

## 1. Reconstrução do experimento

O fluxo é: carregar curvas; compilar o alimentador; executar baseline sem controle; obter a violação acumulada `S_i`; escolher o líder; localizar a hora de pico; calcular `epsilon`; simular duas arquiteturas nos cenários C0–C3; exportar CSVs, figuras, logs, configuração e manifesto.

O circuito é recompilado por caso com `Clear + compile`, reduzindo vazamento de estado. O grafo nominal possui seis enlaces:

```python
ENLACES_DO_GRAFO_NOMINAL = [
    (0, 1), (1, 2), (2, 3),
    (3, 4), (4, 5), (1, 4),
]
```

C1 remove `(2,5)` e mantém o grafo conexo; C2 remove `(1,2)` e isola o líder; C3 isola líder ou não-líder na hora de pico, por 20 iterações ou por toda a janela (`k_max=500`). Isso é estudo de caso determinístico, não amostragem estatística.

### Equação efetiva

O estado é a fração de curtailment `rho_i`; aumentar `rho` reduz a injeção PV:

```python
def misturar_por_consenso(rho, A, epsilon):
    L = calcular_laplaciana(A)
    return rho - epsilon * (L @ rho)
```

Logo, a dinâmica é `rho(k+1) = clip[(I - epsilon L)rho(k) + c(k), 0, 1]`. No `leader_follower`, somente o líder recebe a correção; no `leaderless`, cada agente usa a tensão local.

### Semântica real da “perda”

O código implementa a falha assim:

```python
matriz = self.matriz_de_adjacencia_estatica.copy()
if self.agente_esta_isolado(hora, iteracao):
    matriz[agente_isolado, :] = 0.0
    matriz[:, agente_isolado] = 0.0
return matriz
```

E classifica mensagens assim:

```python
enlace_ativo = matriz_de_adjacencia[origem, destino] > 0
situacao = "ENTREGUE" if enlace_ativo else "PERDIDA"
```

Esse registro não alimenta uma fila, buffer ou memória de mensagens. Portanto, `PERDIDA` significa “a aresta não participou desta mistura”; não significa pacote sorteado, atrasado ou descartado por transporte.

## 2. Resultados auditados

Fonte: `Resultados/FASE0_EXP001/tables/resumo_completo.csv`.

| arquitetura | cenário | Vmáx PV (pu) | horas com violação | curtailment diário | σr diário |
|---|---|---:|---:|---:|---:|
| sem controle | — | 1,065079 | 8 | 0,00% | — |
| leader_follower | C0 | 1,050499 | 0 | 41,64% | 0,00758 |
| leader_follower | C1 | 1,050500 | 0 | 41,65% | 0,01922 |
| leader_follower | C2 | 1,060852 | 8 | 16,51% | 0,34939 |
| leader_follower | C3 líder longa | 1,060852 | 1 | 35,52% | — |
| leaderless | C0 | 1,050498 | 0 | 41,65% | — |
| leaderless | C1 | 1,050500 | 0 | 41,65% | — |
| leaderless | C2 | 1,050500 | 0 | 41,73% | — |
| leaderless | C3 líder longa | 1,050498 | 0 | 41,66% | — |

O manifesto confirma `lambda_2(C0)=0,6571`, `lambda_2(C1)=0,2679`, `lambda_2(C2)=0`, conservação de energia com diferença máxima `2,84e-14 kW` e oito horas-caso em `k_max` marcadas como `nao_convergiu`.

Esses dados sustentam que C2 degrada o `leader_follower` no desenho registrado e que o `leaderless` mantém a tensão no caso registrado. Não sustentam superioridade geral: faltam replicações, topologias, perfis e um modelo probabilístico.

## 3. Achados críticos e correções sugeridas

### A0 - Altíssima: Caso controle efetivo sem problemas de comunicação
Hoje tem caso sem controle, e os demais com controle, mas com problemas de comunicação. PRecisa-se reestruturar para se ter: 
- Caso sem controle (baseline)
- Caso com conrole normal (baseline para provar que o consenso funciona)
- Casos de falhas de comunicação já implementadas. 


### A1 — Alta prioridade: fenômeno de comunicação superdeclarado

Não há sorteio, semente, probabilidade, atraso, timeout ou fila. C1/C2 são remoção permanente de enlaces; C3 é isolamento temporário.

Redação recomendada:

> Neste estágio, “falha de comunicação” é operacionalizada como indisponibilidade determinística de enlaces ou isolamento temporário. O estudo não modela taxa probabilística de perda nem atraso de pacotes.

Para implementar perda probabilística:

```python
def entregar_mensagem(mensagem, rng, p_perda):
    return None if rng.random() < p_perda else mensagem
```

Registrar `seed`, `replicacao`, envio, entrega e motivo da ausência.

### A2 — Alta prioridade: 0,2 s é rótulo de log

`PERIODO_DO_CICLO_DE_COMUNICACAO_S = 0.2` só calcula `t_sim`; não agenda eventos nem retarda o solver. Deve ser chamado de “escala temporal anotada” até existir uma fila real.

Implementação mínima de atraso:

```python
from collections import deque

fila = deque()  # (k_entrega, destino, mensagem)
estado_recebido = [None] * numero_de_agentes

def publicar(k, origem, destino, conteudo, atraso):
    fila.append((k + atraso, destino, conteudo))

def entregar_ate(k):
    while fila and fila[0][0] <= k:
        _, destino, mensagem = fila.popleft()
        estado_recebido[destino] = mensagem
```

O consenso deve consumir `estado_recebido`, nunca o vetor instantâneo global.

### A3 — Alta prioridade: convergência está sendo usada em sentidos diferentes

O critério atual é elétrico:

```python
return tensao_vista_pelo_controle <= TENSAO_LIMITE_PU + TOLERANCIA_DE_TENSAO_PU
```

Isso não prova consenso matemático. Reportar separadamente `erro_rho=max(rho)-min(rho)`, tensão controlada, Vmáx real, iterações, `k_max` e `sigma_r`.

```python
criterios = {
    "eletrico": v_controle <= v_limite + tol_v,
    "consenso": erro_rho <= tol_rho,
    "limite": k >= k_max,
}
```

### A4 — Alta prioridade: resultados não vinculados ao checkout atual

Reexecutar no checkout atual e registrar hashes:

```powershell
uv run python Experimento_Consenso_comunication_failure.py
git rev-parse HEAD
Get-FileHash Entradas/curvas_24h.csv
Get-FileHash IEEE34bus/ieee34Mod3ORIGINAL_CBA.dss
```

O manifesto também deve registrar hash de `uv.lock`, configuração completa e identificador da execução.

### A5 — Média/alta prioridade: ausência de testes

As validações embutidas são úteis, mas não são regressão automatizada. Criar testes para grafo, `lambda_2`, C3, consenso, clipping, conservação de energia e pipeline reduzido:

```python
def test_c2_isola_o_lider():
    c = next(c for c in definir_cenarios_de_falha() if c.nome == "C2")
    g = GrafoDeComunicacao(c, hora_da_falha_temporaria=10)
    A = g.matriz_de_adjacencia_na_iteracao(10, 0)
    assert calcular_conectividade_algebrica(A) == 0.0
```

### A6 — Média prioridade: entry point inconsistente

`pyproject.toml` declara `tcc-facens = "tcc_facens:main"`, mas `src/tcc_facens/__init__.py` é placeholder. Hoje a execução real é:

```powershell
uv run python Experimento_Consenso_comunication_failure.py
```

Corrigir o entry point para chamar uma função real ou removê-lo até o pacote encapsular o experimento.

### A7 — Média prioridade: curvas de exemplo

`config.yaml` identifica as curvas como exemplos e o código pode criá-las se ausentes. Isso permite reprodução, mas não validação com dados medidos. Informar origem, unidade, normalização, perfil de carga/PV e representatividade; impedir criação silenciosa em execução de validação.

### A8 — Média prioridade: regime quase-estático

`SolveModes.SnapShot` e o perfil horário representam pontos de operação. Não permitem afirmar estabilidade transitória, dinâmica eletromagnética ou resposta temporal real de inversores.

### A9 — Média prioridade: grafo é hipótese manual

A topologia de comunicação não é derivada automaticamente da rede elétrica. Justificar os seis enlaces e separar claramente “topologia elétrica” de “topologia de comunicação”.

## 4. Conclusões permitidas e proibidas

Permitidas: C0/C1 permanecem controláveis nos resultados versionados; particionar o líder degrada LF; LL mantém o controle em C2; o controle reduz `1,065079 pu` para aproximadamente `1,0505 pu` nos casos bem-sucedidos.

Evitar: “robusto a perda de pacotes”, “atraso de 0,2 s”, “recuperação de mensagens obsoletas”, “leaderless superior em geral” e “modelo de rede IEC 61850 real”.

## 5. Plano recomendado

1. Reexecutar no commit atual e comparar CSVs/figuras com o manifesto antigo.
2. Adicionar hashes das entradas, configuração e lockfile.
3. Corrigir UTF-8, entry point e instruções de execução.
4. Extrair funções puras e criar testes unitários/integração.
5. Separar status elétrico, consenso e `k_max` nos relatórios.
6. Implementar sementes, replicações, perda por mensagem, atraso e buffer.
7. Variar taxa de perda, atraso, duração e hora da falha; reportar média, dispersão e intervalos.

## Veredito

O experimento é uma base funcional, com boa instrumentação de resultados e invariantes elétricos. A correção essencial é de escopo: ele avalia conectividade e isolamento determinísticos em um controlador por snapshots. Com essa qualificação, sustenta método e resultados condicionados ao desenho atual. Para uma conclusão geral sobre robustez de comunicação, são necessárias reexecução rastreável, testes e extensão probabilística/temporal.

## 7. Implementação realizada após a auditoria

As primeiras correções do plano foram implementadas no código:

- o manifesto passou a registrar hashes do código, rede, curvas e lockfile;
- o resultado separa status elétrico, consenso e `k_max`;
- o entry point `tcc-facens` executa o experimento;
- `src/tcc_facens/communication.py` implementa perdas, atrasos, fila, semente e última mensagem válida;
- o consenso possui caminho opcional por estado recebido;
- a execução aceita `--enable-channel`, `--loss-probability`, `--delay-steps`, `--seed` e `--output-dir`;
- os CSVs registram contadores reais do canal por hora;
- foram adicionados seis testes estruturais e dependências de desenvolvimento.

Uma execução ponta a ponta foi validada em `Resultados/FASE0_EXP001_CHANNEL_TEST`, com perda de `0,05`, atraso de uma iteração e semente `42`. Em LF/C0/hora 10, o arquivo `raw/timestep.csv` registrou 2.676 mensagens tentadas, 2.533 entregues, 131 perdidas e 12 pendentes.

O log legado de `comunicacao_*.log` continua registrando a topologia determinística. O novo arquivo `raw/channel_messages.csv` é a fonte por mensagem do modelo probabilístico; os contadores `mensagens_do_canal_*` do `timestep.csv` e a configuração do manifesto complementam essa fonte.

## Evidências consultadas

`Experimento_Consenso_comunication_failure.py`; `Resultados/FASE0_EXP001/manifest.json`; `Resultados/FASE0_EXP001/tables/resumo_completo.csv`; `Resultados/FASE0_EXP001/summary/convergencia_por_cenario.csv`; `Resultados/FASE0_EXP001/summary/comunicacao_por_caso.csv`; `Resultados/FASE0_EXP001/config.yaml`; `pyproject.toml`; `src/tcc_facens/__init__.py`.
