# Problema e Hipóteses — Consenso proporcional sob falhas de comunicação (TCC Facens)

> **Projeto:** [TCC_Facens_Smart_GRID](../README.md) · **Documento canônico** · **Última revisão:** 2026-10-09
> **Commit de referência da intervenção documental:** `d70fb55` (HEAD de `main`, 2026-10-09; árvore limpa no início da intervenção).
> **Fontes consolidadas:** [`Fase 0 - Idealização.md`](../Fase%200%20-%20Idealização.md) (§§2–6, 27–28, 33–34), [`experimento.md`](../experimento.md) (§§1, 3, 8), [`README.md`](../README.md) original (§§0.1, 4), [`revisao.md`](../revisao.md) (§4).

## 1. Contexto científico

O controle distribuído por consenso para *curtailment* proporcional de GFVs (CBA 2026; Giacomini, 2025 — R0) assume comunicação ideal. A literatura de consenso com *curtailment* e *fairness* (R1–R4) também não modela falhas; trabalhos de comunicação imperfeita (R5–R10) tratam de outros objetivos elétricos (Volt-Var, microrredes, frequência). Este TCC estuda o eixo "falha de comunicação → convergência → *curtailment* → *fairness* → tensão" ([`Fase 0 - Corpus - Referências.md`](../Fase%200%20-%20Corpus%20-%20Referências.md)).

Por decisão do pesquisador, a camada de falha de comunicação é escopo **exclusivo** deste TCC e não é, por ora, incorporada aos Papers 2–4 do mestrado ([`experimento.md`](../experimento.md) §8).

## 2. Problema investigado

Impacto de falhas na camada de comunicação no consenso proporcional para *curtailment* FV no IEEE 34 barras, comparando as arquiteturas **Leader-Follower** (LF) e **Leaderless** (LL).

## 3. Lacuna de pesquisa

Ausência de avaliação conjunta de falha de comunicação (enlace, particionamento, isolamento de agente, perda de mensagens) sobre convergência, distribuição justa do corte e tensão em consenso proporcional para *curtailment* FV; e ausência de comparação LF × LL sob essas falhas.

> NÃO VERIFICADO: a lacuna é afirmada com base num corpus de 11 referências (R0–R10); R5 (Zhang et al., 2019) não tem PDF verificado no repositório.

## 4. Questões de pesquisa

- **QP1.** Como a degradação da comunicação altera iterações, erro de consenso e dispersão do *curtailment*?
- **QP2.** Existe uma margem em que o consenso degrada sem violação de tensão?
- **QP3.** O particionamento do grafo produz equilíbrios múltiplos, e a conectividade conjunta no tempo restaura o consenso?
- **QP4.** A arquitetura (LF × LL) determina a robustez à falha estrutural, em especial à falha do líder?

## 5. Objetivo geral

Avaliar, por simulação quase-estática de 24 h no IEEE 34 barras com 6 GFVs, o efeito de falhas de comunicação determinísticas (e, como extensão, probabilísticas) sobre o consenso proporcional, em LF e LL.

## 6. Objetivos específicos

1. Caracterizar o caso sem controle e escolher o líder pela violação acumulada $S_i$ (Critério B).
2. Implementar LF e LL com a mesma mistura de consenso e funções de correção distintas.
3. Simular C0–C3 (C3 com líder/não líder × falha curta/longa) nas duas arquiteturas.
4. Medir $e_c$, $N_{iter}$, $\sigma_r$ global e por partição, $V_{\max}$, violações, $\lambda_2$ e *curtailment*.
5. (Extensão pós-auditoria) Executar canal probabilístico com perda e atraso, com sementes e replicações.

## 7. Hipóteses

Formalizadas em [`experimento.md`](../experimento.md) §3 e no README original §4.1:

| ID | Hipótese | Predição verificável |
|---|---|---|
| H1 | Degradação estrutural aumenta esforço e erro de convergência (verificação de sanidade). | $C0 \prec C1 \prec C3 \Rightarrow \mathbb{E}[N_{iter}]$ e $\mathbb{E}[e_c^\infty]$ não decrescem |
| H2 | Falhas distorcem a distribuição justa do corte. | $\sigma_r(C_{1..3}) > \sigma_r(C0)$; em C2, $\sigma_r$ por partição baixo e global alto |
| H3 | Degradação do consenso não implica violação elétrica imediata (núcleo científico). | Existe região com $\sigma_r \gg \sigma_r(C0)$ e $V_{\max} \le 1{,}05$ pu |
| H4 / H4′ | Particionamento ($\lambda_2 = 0$) produz equilíbrios múltiplos; conectividade conjunta no tempo restaura o consenso após falhas temporárias. | Dois equilíbrios em C2; recuperação em C3 curto |
| H5 | A arquitetura determina a resiliência ao particionamento: em LF, a partição sem líder fica "cega"; em LL, a regulação local persiste. | Violação em LF-C2, ausência em LL-C2 |
| H5a | A falha do próprio líder é o pior caso estrutural do LF, e neutra no LL. | LF: $m$ = líder pior que $m$ ≠ líder; LL: identidade de $m$ irrelevante |
| HA–HC (sensibilidade) | Propostas de trabalho futuro: ineficiência do consenso uniforme, consenso ponderado por $\partial V/\partial P$, criticidade da falha em nó de alta sensibilidade. | Não formalizadas como teste ([`Protocolos de comunicacao e sensibilidade.md`](../Protocolos%20de%20comunicacao%20e%20sensibilidade.md)) |

## 8. Variáveis e métricas associadas

$e_c(k)$ (erro de consenso), $N_{iter}$, $\sigma_r$ global e por partição, $V_{\max}$ das barras com PV e da rede, horas e barras-hora com violação, *curtailment* (kWh, %), $\lambda_2(L)$, $S_i$; no modo probabilístico, mensagens tentadas, entregues, perdidas e pendentes.

## 9. Critérios para testar cada hipótese

Critérios de refutação de [`experimento.md`](../experimento.md) §3:

- **H1** refutada se maior severidade não aumentar $N_{iter}$ ou $e_c^\infty$.
- **H3** refutada se toda falha que afaste $\sigma_r$ do baseline também violar $V_{\max}$.
- **H5** refutada se, com o líder isolado, a partição sem líder em LF não degradar mais que em LL; parcialmente refutada se LL exibir patologia compensatória (trade-off).

> PENDENTE: sem replicações no baseline determinístico, "estatisticamente maiores" (H1) não pode ser avaliado; as conclusões valem para um caso.

## 10. Escopo e delimitações

- **Dentro:** C0–C3 determinísticos × {LF, LL}; extensão probabilística (perda i.i.d. por mensagem, atraso discreto em iterações, semente).
- **Fora (decisões registradas):** atraso físico em segundos, dinâmica de inversores, Monte Carlo no baseline, perda em rajada (Gilbert-Elliott), *failsafe* Volt-Watt, BESS, Q.
- "Perda" em C1/C2 é **estrutural** (enlace removido), não porcentagem de pacotes; o grafo de comunicação é hipótese manual, não a rede física de telecomunicações; o IEEE 34 é alimentador de referência, não instalação medida (README original, itens 6–8).
- Conclusões condicionadas ao alimentador, curvas, ganhos e cenários deste experimento; não constituem prova de superioridade geral do LL.
