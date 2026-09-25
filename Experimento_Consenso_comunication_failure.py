"""
Experimento Fase 0 (TCC Facens) — Impacto de falhas de comunicação no consenso
proporcional de curtailment fotovoltaico: Leader-Follower vs. Leaderless.

Fonte de verdade do desenho experimental: `experimento.md` (raiz do repositório).
As referências "§x.y" nos comentários apontam para seções daquele documento.

Resumo do que este arquivo faz:

    1. Monta o alimentador IEEE 34 barras (`ieee34Mod3ORIGINAL_CBA.dss`) com
       6 PVSystems (§4.2, §4.2.1).
    2. Roda o dia (24 snapshots horários) SEM controle, calcula a violação
       acumulada S_i de cada agente e escolhe o líder = argmax S_i (§4.4.1).
    3. Rotula o grafo de comunicação (§4.3): líder -> posição 1, agente com
       menor S_i -> posição 6.
    4. Roda a matriz experimental {Leader-Follower, Leaderless} x
       {C0, C1, C2, C3 (m = líder / m != líder) x (falha curta / longa)} (§4.6.1).
    5. Calcula as métricas (e_c, N_iter, sigma_r, Vmax, violações, lambda_2),
       valida (§6) e salva CSVs, config.yaml, manifest.json e figuras (§5.5).

Convenção de código (§4.1.1): este arquivo é otimizado para LEITURA, não para
desempenho. Nomes longos, funções pequenas, comentários explicando o porquê.

Execução:
    uv run python Experimento_Consenso_comunication_failure.py
"""

# =============================================================================
# IMPORTAÇÕES
# =============================================================================

import argparse
import hashlib
import json
import logging
import platform
import re
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # salva figuras em arquivo, sem abrir janelas
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from altdss import altdss
from dss import SolveModes

# =============================================================================
# CONFIGURAÇÃO DO EXPERIMENTO
# Tudo o que é mantido CONSTANTE entre cenários e arquiteturas fica aqui (§6).
# =============================================================================

PASTA_DO_PROJETO = Path(__file__).resolve().parent
PASTA_DO_ALIMENTADOR = PASTA_DO_PROJETO / "IEEE34bus"
ARQUIVO_DSS_DO_ALIMENTADOR = PASTA_DO_ALIMENTADOR / "ieee34Mod3ORIGINAL_CBA.dss"  # §4.2
ARQUIVO_DE_CURVAS_DIARIAS = PASTA_DO_PROJETO / "Entradas" / "curvas_24h.csv"
PASTA_DE_RESULTADOS = PASTA_DO_PROJETO / "Resultados" / "FASE0_EXP001"  # §5.5
PASTA_DE_LOGS = PASTA_DE_RESULTADOS / "logs"

CONFIGURACAO_COMUNICACAO = {
    "habilitado": False,
    "probabilidades_de_perda": [0.0],
    "atraso_em_iteracoes": 0,
    "semente": None,
}

# --- Rede elétrica -----------------------------------------------------------
# Os 6 GFVs na ordem do código de referência (lista_barras_DGs), §4.2.
# Essa ordem NÃO é a ordem do grafo de comunicação — a ordem do grafo só é
# definida depois de rodar o caso sem controle (§4.4.1, checklist item 4).
BARRAS_DOS_PVS_ORDEM_DE_REFERENCIA = ["824", "816", "828", "830", "850", "832"]
POTENCIA_NOMINAL_KVA_ORDEM_DE_REFERENCIA = [150.0, 125.0, 100.0, 130.0, 90.0, 115.0]
FATOR_DE_ESCALA_DOS_PVS = 1.0  # lambda de §4.2 (fixo em 1: sem varredura de hosting capacity)
TENSAO_NOMINAL_PVS_KV = 24.9

# LoadMult herdado do código de referência (§7.7): +10% de carga na rede.
# O multiplicador horário da curva de carga é aplicado POR CIMA deste valor.
MULTIPLICADOR_BASE_DE_CARGA = 1.1

# --- Limites de tensão e critério de parada (§4.7) ---------------------------
TENSAO_LIMITE_PU = 1.05  # V_lim = V_ref (§2.0, §4.5)
# tol do critério de parada elétrico. O código de referência usava 1e-6, mas com o
# grafo esparso de §4.3 a aproximação de 1,05 pu é assintótica e 1e-6 não era
# atingido em k_max (horas terminando em 1,050001 pu marcadas "nao_convergiu").
# Decisão do pesquisador: 1,050 (3 casas) já é regulação aceitável -> tol = 5e-4,
# isto é, qualquer tensão que arredonda para 1,050 pu (< 1,0505) é aceita.
TOLERANCIA_DE_TENSAO_PU = 5e-4
# Critério separado do critério elétrico: mede uniformidade de rho entre agentes.
TOLERANCIA_DE_CONSENSO = 1e-6
# Limite inferior usado só para CONTAR subtensões (relatório, não controle),
# igual ao VMIN_VIOL do código de referência.
TENSAO_MINIMA_PU = 0.95
NUMERO_MAXIMO_DE_ITERACOES = 500  # k_max
DURACAO_DO_PASSO_HORAS = 1.0  # Delta t (24 snapshots de 1 h)

# --- Controle (§4.5, §7.5, §7.6) -------------------------------------------
# beta: ganho da correção de tensão. Mesmo valor nas DUAS arquiteturas (§7.5,
# opção primária). Valor de partida = ganho_lider_prop do código de referência.
GANHO_DE_CORRECAO_DE_TENSAO = 5.0

# --- Cenário C3 (§4.6, §7.1 — decidido com o pesquisador) ----------------
# A falha é injetada somente na hora de maior sobretensão do caso sem controle,
# a partir da iteração k = 0, com duas durações:
#   curta: o agente volta na iteração k = 20 (DENTRO da mesma hora)
#   longa: o agente fica fora a hora inteira (até k_max)
ITERACAO_DE_RETORNO_FALHA_CURTA = 20

# --- Log de comunicação (estilo GOOSE / DNP3) -------------------------------
# Período de um ciclo de troca de mensagens do consenso, usado SÓ para dar um
# instante simulado (HH:MM:SS.mmm) a cada mensagem no log. Não altera a
# dinâmica: nenhum atraso é modelado (Fase 0 §18). Valor = resolução tau = 0,2 s
# usada por Wang et al. (2023, R7) para o ciclo de comunicação.
PERIODO_DO_CICLO_DE_COMUNICACAO_S = 0.2
ITERACAO_DE_RETORNO_FALHA_LONGA = NUMERO_MAXIMO_DE_ITERACOES

# --- Curvas diárias de exemplo --------------------------------------------
# O arquivo de curvas do paper-âncora (CurvaPV_24pontos_CBA.xls) não está no
# repositório (§7.7). Usamos as curvas de EXEMPLO fornecidas pelo pesquisador
# (planilhas "Carregamento_pu" e "Curva_PV_kW"). Na primeira execução elas são
# gravadas em `Entradas/curvas_24h.csv`; para usar outros valores no futuro,
# basta editar esse CSV (o código sempre lê do CSV quando ele existe).
CURVA_DE_CARGA_EXEMPLO_PU = [
    0.420, 0.420, 0.421, 0.421, 0.420, 0.400, 0.420, 0.400, 0.460, 0.480, 0.500, 0.560,
    0.570, 0.550, 0.500, 0.600, 0.510, 0.610, 0.560, 0.900, 0.970, 0.995, 1.000, 0.850,
]
CURVA_PV_EXEMPLO_KW = [
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 15.0, 45.0, 82.0, 105.0, 118.0, 120.0,
    110.0, 88.0, 60.0, 27.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]

# Nomes das arquiteturas (parâmetro do experimento, §4.1)
ARQUITETURA_LEADER_FOLLOWER = "leader_follower"
ARQUITETURA_LEADERLESS = "leaderless"
ARQUITETURAS_DO_EXPERIMENTO = [ARQUITETURA_LEADER_FOLLOWER, ARQUITETURA_LEADERLESS]


# =============================================================================
# ESTRUTURAS DE DADOS
# =============================================================================


@dataclass
class AgenteFotovoltaico:
    """Um agente do consenso = um PVSystem conectado em uma barra."""

    nome_do_pvsystem: str
    barra: str
    potencia_nominal_kva: float


@dataclass
class DefinicaoDeCenario:
    """
    Definição formal de um cenário de falha (§4.6).

    As posições de agente seguem o grafo de §4.3, mas com índice começando em 0
    (posição 1 do documento = índice 0 aqui = líder).
    """

    nome: str
    descricao: str
    arestas_removidas: list = field(default_factory=list)  # C1/C2: perda de enlace permanente
    indice_do_agente_isolado: int | None = None  # C3: agente m
    iteracao_de_retorno_do_agente: int | None = None  # C3: k_r
    agente_isolado_e_o_lider: bool | None = None  # C3: m = líder? (H5a)
    canal_habilitado: bool = False  # cenario probabilistico: perda/atraso por mensagem sobre topologia nominal
    probabilidade_de_perda_do_canal: float = 0.0  # so tem efeito quando canal_habilitado=True


# =============================================================================
# ENTRADAS — curvas diárias de carga e irradiância
# =============================================================================


def criar_arquivo_de_curvas_de_exemplo():
    """
    Grava `Entradas/curvas_24h.csv` com as curvas de exemplo do pesquisador,
    no mesmo formato das planilhas: hora, carregamento_pu, curva_pv_kw.
    """
    curvas_de_exemplo = pd.DataFrame(
        {
            "hora": list(range(24)),
            "carregamento_pu": CURVA_DE_CARGA_EXEMPLO_PU,
            "curva_pv_kw": CURVA_PV_EXEMPLO_KW,
        }
    )
    ARQUIVO_DE_CURVAS_DIARIAS.parent.mkdir(parents=True, exist_ok=True)
    curvas_de_exemplo.to_csv(ARQUIVO_DE_CURVAS_DIARIAS, index=False)


def converter_curva_pv_em_irradiancia_pu(curva_pv_kw):
    """
    A curva PV é dada em kW de uma unidade de referência (pico de 120 kW no
    exemplo). Dividindo pelo pico obtemos um perfil em pu (0..1), aplicado como
    `Irradiance` em TODOS os PVSystems: cada um gera Pmpp_i * irradiância, ou
    seja, todos têm o mesmo formato de curva, escalado pela própria potência.
    """
    pico_da_curva_kw = max(curva_pv_kw)
    if pico_da_curva_kw <= 0:
        raise ValueError("A curva PV não tem nenhum valor positivo.")
    irradiancia_pu = []
    for potencia_kw in curva_pv_kw:
        irradiancia_pu.append(potencia_kw / pico_da_curva_kw)
    return irradiancia_pu


def carregar_ou_criar_curvas_diarias():
    """
    Lê `Entradas/curvas_24h.csv` (criando-o com as curvas de exemplo se não
    existir) e devolve as duas grandezas que o circuito consome por hora:
        multiplicador_de_carga  = carregamento_pu da curva de carga
        irradiancia_pu          = curva PV normalizada pelo seu pico

    Retorna (DataFrame das curvas, texto indicando a origem das curvas).
    """
    if not ARQUIVO_DE_CURVAS_DIARIAS.exists():
        criar_arquivo_de_curvas_de_exemplo()
    curvas_lidas = pd.read_csv(ARQUIVO_DE_CURVAS_DIARIAS)
    if len(curvas_lidas) != 24:
        raise ValueError(f"As curvas diárias devem ter 24 linhas (uma por hora); têm {len(curvas_lidas)}.")

    curvas = pd.DataFrame(
        {
            "hora": curvas_lidas["hora"].astype(int),
            "multiplicador_de_carga": curvas_lidas["carregamento_pu"].astype(float),
            "curva_pv_kw": curvas_lidas["curva_pv_kw"].astype(float),
            "irradiancia_pu": converter_curva_pv_em_irradiancia_pu(list(curvas_lidas["curva_pv_kw"].astype(float))),
        }
    )
    origem_das_curvas = f"lido de {ARQUIVO_DE_CURVAS_DIARIAS.relative_to(PASTA_DO_PROJETO)} (curvas de exemplo do pesquisador)"
    return curvas, origem_das_curvas


# =============================================================================
# ELÉTRICO — construção do circuito, aplicação de perfis, medição (AltDSS)
# =============================================================================


def ler_dss_corrigindo_caminhos_relativos():
    """
    Lê o texto do .dss do alimentador e troca os caminhos relativos por absolutos.

    Por quê: o .dss faz `Redirect IEEELineCodes.dss`, mas o arquivo no disco se
    chama `IEEELineCodes.DSS`. No Linux (sistema de arquivos sensível a
    maiúsculas) isso falha. Não editamos o .dss original (regra da skill:
    nunca sobrescrever a rede base) — corrigimos só o texto em memória.
    """
    texto_do_dss = ARQUIVO_DSS_DO_ALIMENTADOR.read_text()
    arquivos_da_pasta = {arquivo.name.lower(): arquivo for arquivo in PASTA_DO_ALIMENTADOR.iterdir()}

    def trocar_por_caminho_absoluto(correspondencia):
        comando = correspondencia.group(1)
        nome_do_arquivo = correspondencia.group(2)
        arquivo_real = arquivos_da_pasta.get(nome_do_arquivo.lower())
        if arquivo_real is None:
            return correspondencia.group(0)
        return f'{comando}"{arquivo_real}"'

    padrao_de_arquivo_referenciado = r"(?im)^(\s*(?:Redirect|Buscoords)\s+)(\S+)"
    return re.sub(padrao_de_arquivo_referenciado, trocar_por_caminho_absoluto, texto_do_dss)


def construir_circuito_com_pvs(agentes):
    """
    Monta o circuito do zero: Clear + compile do .dss + criação dos PVSystems.

    Chamado uma vez por caso (cenário x arquitetura) para evitar vazamento de
    estado entre cenários (skill Executor_altGRID_consenso, "Scenario reset").
    """
    altdss(ler_dss_corrigindo_caminhos_relativos())  # o próprio .dss começa com Clear

    for agente in agentes:
        # PVSystem, não Generator (§4.2.1). Pmpp = kVA nominal; fator de potência
        # unitário; sem cut-in/cut-out para que qualquer irradiância gere potência.
        altdss.PVSystem.new(
            agente.nome_do_pvsystem,
            Bus1=agente.barra,
            Phases=3,
            kV=TENSAO_NOMINAL_PVS_KV,
            kVA=agente.potencia_nominal_kva,
            Pmpp=agente.potencia_nominal_kva,
            Irradiance=0.0,
            PF=1.0,
            pctCutIn=0.0,
            pctCutOut=0.0,
        )

    # Modo snapshot: o tempo NÃO é avançado pelo OpenDSS. Quem define "que hora
    # é" é o Python, escrevendo explicitamente carga e irradiância de cada hora
    # (skill, "Use of Mode=Daily": alternativa explícita e equivalente).
    altdss.Solution.Mode = SolveModes.SnapShot


def aplicar_perfil_da_hora(curvas, hora, agentes):
    """Escreve no circuito a carga e a irradiância da hora `hora`."""
    multiplicador_de_carga = float(curvas.loc[hora, "multiplicador_de_carga"])
    irradiancia = float(curvas.loc[hora, "irradiancia_pu"])

    altdss.Solution.LoadMult = MULTIPLICADOR_BASE_DE_CARGA * multiplicador_de_carga
    for agente in agentes:
        altdss.PVSystem[agente.nome_do_pvsystem].Irradiance = irradiancia


def restaurar_pvs_sem_curtailment(agentes):
    """Estado pré-controle da hora: kVA de volta ao valor nominal (sem corte)."""
    for agente in agentes:
        altdss.PVSystem[agente.nome_do_pvsystem].kVA = agente.potencia_nominal_kva


def resolver_fluxo_de_potencia():
    """Roda um SolveSnap e interrompe o experimento se o fluxo não convergir (§6)."""
    altdss.Solution.SolveSnap()
    if not altdss.Solution.Converged:
        raise RuntimeError("SolveSnap não convergiu — resultado elétrico inválido.")


def medir_tensao_maxima_da_barra_pu(nome_da_barra):
    """Maior módulo de tensão (pu) entre as fases da barra."""
    modulos_e_angulos = altdss.Bus[nome_da_barra].puVMagAngle
    modulos_pu = modulos_e_angulos[0::2]  # o vetor alterna [módulo, ângulo, módulo, ângulo, ...]
    return float(np.max(modulos_pu))


def medir_tensoes_locais_dos_agentes(agentes):
    """Vetor V_i (pu): tensão máxima de fase na barra de cada agente."""
    tensoes = np.zeros(len(agentes))
    for indice, agente in enumerate(agentes):
        tensoes[indice] = medir_tensao_maxima_da_barra_pu(agente.barra)
    return tensoes


def medir_potencia_ativa_gerada_por_agente_kw(agentes):
    """Potência ativa entregue por cada PV (kW, positiva quando gera)."""
    potencias = np.zeros(len(agentes))
    for indice, agente in enumerate(agentes):
        potencias_complexas = altdss.PVSystem[agente.nome_do_pvsystem].Powers()
        # Convenção OpenDSS: potência injetada por gerador aparece negativa no terminal.
        potencias[indice] = -float(np.sum(potencias_complexas.real))
    return potencias


def medir_tensao_maxima_da_rede_pu():
    """
    Vmax de toda a rede (relatório, não controle — §7.3).

    A barra `sourcebus` é excluída: ela é a fonte ideal fixada em 1,05 pu no
    .dss, e incluí-la tornaria Vmax >= 1,05 em qualquer situação.
    """
    tensao_maxima = 0.0
    for nome_da_barra in altdss.Bus.Name():
        if nome_da_barra == "sourcebus":
            continue
        tensao_maxima = max(tensao_maxima, medir_tensao_maxima_da_barra_pu(nome_da_barra))
    return tensao_maxima


def medir_estado_de_todas_as_barras(arquitetura, nome_do_cenario, hora):
    """
    Tensão de TODAS as barras da rede no estado resolvido atual (uma linha por barra).

    Para cada barra registra a maior e a menor tensão entre as fases e quantas
    fases violam cada limite. Uma barra conta como "com sobretensão" se
    QUALQUER fase passar de V_lim (mesma regra do código de referência).
    A `sourcebus` fica de fora pelo mesmo motivo de `medir_tensao_maxima_da_rede_pu`.
    """
    registros = []
    for nome_da_barra in altdss.Bus.Name():
        if nome_da_barra == "sourcebus":
            continue
        modulos_pu = np.array(altdss.Bus[nome_da_barra].puVMagAngle[0::2], dtype=float)
        if modulos_pu.size == 0:
            continue
        fases_com_sobretensao = int(np.sum(modulos_pu > TENSAO_LIMITE_PU + TOLERANCIA_DE_TENSAO_PU))
        fases_com_subtensao = int(np.sum(modulos_pu < TENSAO_MINIMA_PU))
        registros.append(
            {
                "arquitetura": arquitetura,
                "cenario": nome_do_cenario,
                "hora": hora,
                "barra": nome_da_barra,
                "tensao_maxima_pu": float(np.max(modulos_pu)),
                "tensao_minima_pu": float(np.min(modulos_pu)),
                "numero_de_fases": int(modulos_pu.size),
                "fases_com_sobretensao": fases_com_sobretensao,
                "fases_com_subtensao": fases_com_subtensao,
                "barra_com_sobretensao": fases_com_sobretensao > 0,
                "barra_com_subtensao": fases_com_subtensao > 0,
            }
        )
    return registros


def aplicar_curtailment_nos_pvs(agentes, fracao_de_curtailment, potencia_disponivel_kw):
    """
    Aplica P_curt,i = rho_i * P_available,i limitando o kVA do inversor (§4.5, §7.7).

    Com fator de potência unitário, limitar kVA a P_available*(1-rho) limita a
    potência ativa gerada a esse valor — mesma técnica do código de referência.
    """
    for indice, agente in enumerate(agentes):
        potencia_permitida_kw = potencia_disponivel_kw[indice] * (1.0 - fracao_de_curtailment[indice])
        altdss.PVSystem[agente.nome_do_pvsystem].kVA = max(potencia_permitida_kw, 0.0)


# =============================================================================
# COMUNICAÇÃO — grafo G(t), matriz A(k), Laplaciana, falhas (§4.3, §4.6, §5.3)
# =============================================================================

# Enlaces nominais do grafo "linha com um atalho" (§4.3), em índices 0..5.
# Documento (1-indexado): E_0 = {(1,2),(2,3),(3,4),(4,5),(5,6),(2,5)}
ENLACES_DO_GRAFO_NOMINAL = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (1, 4)]
NUMERO_DE_AGENTES = 6
INDICE_DO_LIDER_NO_GRAFO = 0  # posição 1 do documento: o nó que C2 isola (§4.4.1)
INDICE_DO_AGENTE_DE_CONTRASTE_NO_GRAFO = 5  # posição 6: agente com menor S_i (§7.6)


def montar_matriz_de_adjacencia(lista_de_enlaces, numero_de_agentes):
    """Matriz A simétrica (grafo não direcionado) a partir da lista de enlaces."""
    matriz_de_adjacencia = np.zeros((numero_de_agentes, numero_de_agentes))
    for agente_a, agente_b in lista_de_enlaces:
        matriz_de_adjacencia[agente_a, agente_b] = 1.0
        matriz_de_adjacencia[agente_b, agente_a] = 1.0
    return matriz_de_adjacencia


def calcular_laplaciana(matriz_de_adjacencia):
    """L = D - A (§4.3)."""
    matriz_de_graus = np.diag(matriz_de_adjacencia.sum(axis=1))
    return matriz_de_graus - matriz_de_adjacencia


def calcular_conectividade_algebrica(matriz_de_adjacencia):
    """
    lambda_2(L): segundo menor autovalor da Laplaciana (H4).
    lambda_2 > 0  <=>  grafo conexo.
    """
    autovalores = np.sort(np.linalg.eigvalsh(calcular_laplaciana(matriz_de_adjacencia)))
    lambda_2 = float(autovalores[1])
    if abs(lambda_2) < 1e-10:
        lambda_2 = 0.0  # limpa ruído numérico: grafo desconexo
    return lambda_2


def calcular_epsilon_do_consenso(matriz_de_adjacencia):
    """
    epsilon = 2 / soma dos autovalores não nulos de L = 2 / tr(L) (§4.5).

    Regra verificada no código de referência (`calculo_eps`), incluindo a
    salvaguarda: se epsilon ficar ~1, usa 0,99.
    Calculado UMA vez, no grafo nominal A_0, e mantido fixo em todos os
    cenários (opção (a) de §4.5): assim a falha altera só o grafo, não o passo.
    """
    autovalores = np.linalg.eigvalsh(calcular_laplaciana(matriz_de_adjacencia))
    soma_dos_autovalores_nao_nulos = float(np.sum(autovalores[autovalores > 1e-10]))
    epsilon = 2.0 / soma_dos_autovalores_nao_nulos
    epsilon = min(0.99, epsilon)
    return epsilon


def encontrar_componentes_conexas(matriz_de_adjacencia):
    """
    Lista de componentes conexas (cada uma é uma lista ordenada de índices),
    por busca em largura. Usada para: V_max-mon observável pelo líder (§7.3)
    e sigma_r por partição (H2).
    """
    numero_de_agentes = matriz_de_adjacencia.shape[0]
    agentes_ja_visitados = set()
    componentes = []

    for agente_inicial in range(numero_de_agentes):
        if agente_inicial in agentes_ja_visitados:
            continue
        componente_atual = []
        fila_de_visita = [agente_inicial]
        agentes_ja_visitados.add(agente_inicial)
        while fila_de_visita:
            agente = fila_de_visita.pop(0)
            componente_atual.append(agente)
            for vizinho in range(numero_de_agentes):
                eh_vizinho = matriz_de_adjacencia[agente, vizinho] > 0
                if eh_vizinho and vizinho not in agentes_ja_visitados:
                    agentes_ja_visitados.add(vizinho)
                    fila_de_visita.append(vizinho)
        componentes.append(sorted(componente_atual))

    return componentes


def encontrar_componente_do_agente(matriz_de_adjacencia, indice_do_agente):
    """Índices dos agentes alcançáveis a partir de `indice_do_agente` (inclui ele)."""
    for componente in encontrar_componentes_conexas(matriz_de_adjacencia):
        if indice_do_agente in componente:
            return componente
    raise ValueError("Agente não encontrado em nenhuma componente.")


class GrafoDeComunicacao:
    """
    Estado da rede de comunicação de UM cenário (§5.3).

    Instanciado uma vez por cenário e consultado a cada iteração pelo laço de
    consenso — nunca reconstruído dentro do laço — para evitar vazamento de
    estado entre cenários. É arquitetura-agnóstico: o mesmo objeto serve a
    Leader-Follower e a Leaderless (§4.6).
    """

    def __init__(self, definicao_do_cenario, hora_da_falha_temporaria):
        self.definicao_do_cenario = definicao_do_cenario
        self.hora_da_falha_temporaria = hora_da_falha_temporaria

        enlaces_ativos = []
        for enlace in ENLACES_DO_GRAFO_NOMINAL:
            enlace_foi_removido = enlace in definicao_do_cenario.arestas_removidas
            if not enlace_foi_removido:
                enlaces_ativos.append(enlace)
        # Topologia estática do cenário (C0, C1, C2; e C3 fora da janela de falha)
        self.matriz_de_adjacencia_estatica = montar_matriz_de_adjacencia(enlaces_ativos, NUMERO_DE_AGENTES)

    def agente_esta_isolado(self, hora, iteracao):
        """True se, nesta hora e iteração, o agente m de C3 está fora da rede."""
        cenario = self.definicao_do_cenario
        if cenario.indice_do_agente_isolado is None:
            return False
        esta_na_hora_da_falha = hora == self.hora_da_falha_temporaria
        esta_na_janela_de_iteracoes = iteracao < cenario.iteracao_de_retorno_do_agente
        return esta_na_hora_da_falha and esta_na_janela_de_iteracoes

    def matriz_de_adjacencia_na_iteracao(self, hora, iteracao):
        """
        A(k) do cenário (§4.6). Para C3 dentro da janela de falha, zera a linha
        e a coluna do agente isolado (ele não envia nem recebe mensagens).
        """
        matriz = self.matriz_de_adjacencia_estatica.copy()
        if self.agente_esta_isolado(hora, iteracao):
            agente_isolado = self.definicao_do_cenario.indice_do_agente_isolado
            matriz[agente_isolado, :] = 0.0
            matriz[:, agente_isolado] = 0.0
        return matriz


def definir_cenarios_de_falha():
    """
    Cenários C0–C3 (§4.6, §4.6.1). C4 fora de escopo (§7.4).

    Arestas em índices 0..5 (posição do documento menos 1). Seguimos §4.3:
      C1 remove o atalho (2,5)  -> ainda conexo
      C2 remove (1,2)           -> líder isolado sozinho, lambda_2 = 0
    (A tabela de §4.6 cita arestas (2,4)/(2,3), resquício da versão com 5
    agentes — (2,4) nem existe em E_0; §4.3 é a definição vigente.)
    """
    return [
        DefinicaoDeCenario("C0", "comunicacao ideal"),
        DefinicaoDeCenario("C1", "perda do enlace (2,5), grafo conexo", arestas_removidas=[(1, 4)]),
        DefinicaoDeCenario("C2", "perda do enlace (1,2), lider particionado", arestas_removidas=[(0, 1)]),
        DefinicaoDeCenario(
            "C3_lider_curta",
            "lider isolado na hora de pico, retorna em k=20",
            indice_do_agente_isolado=INDICE_DO_LIDER_NO_GRAFO,
            iteracao_de_retorno_do_agente=ITERACAO_DE_RETORNO_FALHA_CURTA,
            agente_isolado_e_o_lider=True,
        ),
        DefinicaoDeCenario(
            "C3_lider_longa",
            "lider isolado durante toda a hora de pico",
            indice_do_agente_isolado=INDICE_DO_LIDER_NO_GRAFO,
            iteracao_de_retorno_do_agente=ITERACAO_DE_RETORNO_FALHA_LONGA,
            agente_isolado_e_o_lider=True,
        ),
        DefinicaoDeCenario(
            "C3_naolider_curta",
            "agente da posicao 6 isolado na hora de pico, retorna em k=20",
            indice_do_agente_isolado=INDICE_DO_AGENTE_DE_CONTRASTE_NO_GRAFO,
            iteracao_de_retorno_do_agente=ITERACAO_DE_RETORNO_FALHA_CURTA,
            agente_isolado_e_o_lider=False,
        ),
        DefinicaoDeCenario(
            "C3_naolider_longa",
            "agente da posicao 6 isolado durante toda a hora de pico",
            indice_do_agente_isolado=INDICE_DO_AGENTE_DE_CONTRASTE_NO_GRAFO,
            iteracao_de_retorno_do_agente=ITERACAO_DE_RETORNO_FALHA_LONGA,
            agente_isolado_e_o_lider=False,
        ),
    ]


def definir_cenarios_de_perda_probabilistica(probabilidades_de_perda):
    """
    Cenários do canal probabilístico (--enable-channel), topologia SEMPRE nominal.

    Eixo independente do eixo estrutural C1-C3: aqui a topologia nunca muda
    (arestas_removidas=[], nenhum agente isolado); só a probabilidade de perda
    por mensagem varia. Isso evita conflacionar "enlace removido" com "mensagem
    perdida" (achado A1/A9 da auditoria).

    `0.0` é sempre incluído e reaproveita o nome "C0": é o controle "com
    controle, sem perdas de comunicação" do modo probabilístico. Valores
    positivos viram os cenários "com controle, com perda de comunicação"
    (`C0_perda_<p>`).
    """
    valores = sorted({0.0, *probabilidades_de_perda})
    cenarios = []
    for valor in valores:
        nome = "C0" if valor == 0.0 else f"C0_perda_{valor:.2f}"
        descricao = (
            "comunicacao ideal (canal probabilistico ativo, perda 0.00)"
            if valor == 0.0
            else f"topologia nominal, canal probabilistico com perda {valor:.2f} por mensagem"
        )
        cenarios.append(
            DefinicaoDeCenario(nome, descricao, canal_habilitado=True, probabilidade_de_perda_do_canal=valor)
        )
    return cenarios


# =============================================================================
# LOG DA COMUNICAÇÃO — o que a rede de comunicação "fez" em cada iteração
# =============================================================================
#
# Sobre "lag": atraso de comunicação NÃO é modelado nesta fase (Fase 0 §18).
# Toda mensagem enviada por um enlace ativo chega na mesma iteração. O que o
# log mede é a latência ESTRUTURAL, que existe mesmo sem atraso:
#   - saltos até o líder: a correção aplicada no líder leva no mínimo esse
#     número de iterações para influenciar o rho de cada agente (o consenso só
#     troca informação com vizinhos diretos a cada iteração);
#   - idade da informação: há quantas iterações o agente não recebe nenhuma
#     mensagem (cresce enquanto ele está isolado em C3).


def listar_enlaces_ativos(matriz_de_adjacencia):
    """Enlaces nominais que estão ativos em A(k), como pares (i, j) com índice 0."""
    enlaces_ativos = []
    for agente_a, agente_b in ENLACES_DO_GRAFO_NOMINAL:
        if matriz_de_adjacencia[agente_a, agente_b] > 0:
            enlaces_ativos.append((agente_a, agente_b))
    return enlaces_ativos


def calcular_saltos_ate_o_agente(matriz_de_adjacencia, agente_de_origem):
    """
    Distância em saltos (busca em largura) de `agente_de_origem` até cada agente.
    Agentes inalcançáveis ficam com None (informação nunca chega).
    """
    numero_de_agentes = matriz_de_adjacencia.shape[0]
    saltos = [None] * numero_de_agentes
    saltos[agente_de_origem] = 0
    fila_de_visita = [agente_de_origem]
    while fila_de_visita:
        agente = fila_de_visita.pop(0)
        for vizinho in range(numero_de_agentes):
            if matriz_de_adjacencia[agente, vizinho] > 0 and saltos[vizinho] is None:
                saltos[vizinho] = saltos[agente] + 1
                fila_de_visita.append(vizinho)
    return saltos


def formatar_enlace(enlace):
    """(0, 1) -> '(1,2)': mostra na numeração 1..6 do documento (§4.3)."""
    return f"({enlace[0] + 1},{enlace[1] + 1})"


def formatar_particoes(componentes):
    """[[0], [1, 2]] -> '{1} {2,3}'."""
    textos = []
    for componente in componentes:
        textos.append("{" + ",".join(str(indice + 1) for indice in componente) + "}")
    return " ".join(textos)


class RegistradorDeComunicacao:
    """
    Log com timestamp da camada de comunicação de UM caso (arquitetura x cenário).

    Cada linha leva dois carimbos de tempo:
      - relógio real (quando a linha foi escrita) — vem do `logging`;
      - tempo SIMULADO [t=HH:00 k=NNN] — hora do dia e iteração de consenso.
        k é o índice da troca de mensagens que produz rho(k+1).

    Inspirado nos registros de eventos de protocolos de automação (GOOSE /
    IEC 61850, DNP3): cada MENSAGEM é registrada com quem enviou, para quem,
    o que foi enviado, o instante e o que aconteceu com ela (entregue/perdida).
      - conteúdo: rho_i(k) (o estado que o consenso mistura) e V_i(k) (tensão
        local; é o que permite ao líder calcular V_max-mon, §7.3);
      - stNum / sqNum com a semântica do GOOSE: stNum sobe quando o conteúdo
        publicado MUDA (e o sqNum volta a 0); se o conteúdo se repete, só o
        sqNum sobe. sqNum crescendo = agente já estabilizado, só retransmitindo.

    Destinos:
      - terminal: eventos (falha começou/terminou) e um resumo por hora com controle;
      - arquivo logs/comunicacao_<arquitetura>_<cenario>.log: tudo, inclusive
        uma linha por mensagem e uma por iteração (nível DEBUG);
      - `registros` -> raw/log_comunicacao.csv (estado da rede por iteração);
      - `mensagens` -> raw/log_mensagens.csv (uma linha por mensagem).
    """

    def __init__(self, arquitetura, definicao_do_cenario, agentes):
        self.arquitetura = arquitetura
        self.definicao_do_cenario = definicao_do_cenario
        self.agentes = agentes
        self.registros = []
        self.mensagens = []
        # Contadores por publicador (agente), mantidos durante o caso inteiro.
        self.numero_de_estado_stnum = [0] * len(agentes)
        self.numero_de_sequencia_sqnum = [0] * len(agentes)
        self.ultimo_conteudo_publicado = [None] * len(agentes)
        self.numero_global_de_mensagem = 0

        # Um logger por caso, com arquivo próprio. propagate=False evita que as
        # mensagens sejam repetidas pelo logger raiz do Python.
        self.logger = logging.getLogger(f"comunicacao.{arquitetura}.{definicao_do_cenario.nome}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.logger.handlers.clear()
        formato_com_relogio = logging.Formatter("%(asctime)s.%(msecs)03d | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

        PASTA_DE_LOGS.mkdir(parents=True, exist_ok=True)
        arquivo_de_log = PASTA_DE_LOGS / f"comunicacao_{arquitetura}_{definicao_do_cenario.nome}.log"
        manipulador_de_arquivo = logging.FileHandler(arquivo_de_log, mode="w", encoding="utf-8")
        manipulador_de_arquivo.setLevel(logging.DEBUG)
        manipulador_de_arquivo.setFormatter(formato_com_relogio)
        self.logger.addHandler(manipulador_de_arquivo)

        manipulador_de_terminal = logging.StreamHandler()
        manipulador_de_terminal.setLevel(logging.INFO)
        manipulador_de_terminal.setFormatter(formato_com_relogio)
        self.logger.addHandler(manipulador_de_terminal)

    def _nome_do_agente(self, indice):
        """0 -> '1(816)': posição no grafo + barra física."""
        return f"{indice + 1}({self.agentes[indice].barra})"

    def iniciar_caso(self):
        """Cabeçalho do caso: arquitetura, cenário e falhas permanentes."""
        cenario = self.definicao_do_cenario
        self.logger.info("=" * 78)
        self.logger.info(f"CASO {self.arquitetura} x {cenario.nome}: {cenario.descricao}")
        self.logger.info(
            "Grafo nominal: " + " ".join(formatar_enlace(enlace) for enlace in ENLACES_DO_GRAFO_NOMINAL)
            + " | agentes: " + " ".join(self._nome_do_agente(indice) for indice in range(len(self.agentes)))
        )
        if cenario.arestas_removidas:
            self.logger.info(
                "FALHA PERMANENTE (o dia todo): enlace(s) fora = "
                + " ".join(formatar_enlace(enlace) for enlace in cenario.arestas_removidas)
            )
        if cenario.indice_do_agente_isolado is not None:
            self.logger.info(
                f"FALHA TEMPORÁRIA programada: agente {self._nome_do_agente(cenario.indice_do_agente_isolado)} "
                f"isolado na hora de pico, de k=0 até k={cenario.iteracao_de_retorno_do_agente}"
            )

    def iniciar_hora(self, hora):
        """Zera os contadores da hora (a comunicação só acontece dentro do laço de consenso)."""
        self.hora_atual = hora
        self.enlaces_da_iteracao_anterior = None
        self.idade_da_informacao = [0] * len(self.agentes)
        self.mensagens_enviadas_na_hora = 0
        self.mensagens_perdidas_na_hora = 0
        self.iteracoes_com_falha_na_hora = 0
        self.estado_inicial_da_hora = None
        self.eventos_na_hora = 0

    def calcular_instante_simulado(self, iteracao):
        """
        Instante simulado da iteração k dentro da hora: HH:MM:SS.mmm.
        k-ésimo ciclo de comunicação = hora + k * período do ciclo.
        """
        segundos_desde_o_inicio_da_hora = iteracao * PERIODO_DO_CICLO_DE_COMUNICACAO_S
        minutos = int(segundos_desde_o_inicio_da_hora // 60)
        segundos = segundos_desde_o_inicio_da_hora - 60 * minutos
        return f"{self.hora_atual:02d}:{minutos:02d}:{segundos:06.3f}"

    def _atualizar_stnum_sqnum(self, indice_do_publicador, conteudo):
        """
        Semântica GOOSE: conteúdo novo -> stNum += 1 e sqNum = 0;
        conteúdo repetido -> sqNum += 1. Chamado uma vez por publicação.
        """
        if conteudo != self.ultimo_conteudo_publicado[indice_do_publicador]:
            self.numero_de_estado_stnum[indice_do_publicador] += 1
            self.numero_de_sequencia_sqnum[indice_do_publicador] = 0
            self.ultimo_conteudo_publicado[indice_do_publicador] = conteudo
        else:
            self.numero_de_sequencia_sqnum[indice_do_publicador] += 1

    def _registrar_mensagens_da_iteracao(self, iteracao, instante_simulado, matriz_de_adjacencia,
                                         fracao_de_curtailment, tensoes_locais):
        """
        Uma linha por mensagem direcionada i -> j entre vizinhos NOMINAIS.
        Mensagem sobre enlace ativo: ENTREGUE. Sobre enlace fora: PERDIDA, com motivo.
        """
        for agente_de_origem in range(len(self.agentes)):
            # Conteúdo publicado pelo agente nesta iteração (arredondado para
            # decidir se "mudou" — diferenças abaixo de 1e-6 são tratadas como repetição).
            rho_publicado = round(float(fracao_de_curtailment[agente_de_origem]), 6)
            tensao_publicada = round(float(tensoes_locais[agente_de_origem]), 6)
            self._atualizar_stnum_sqnum(agente_de_origem, (rho_publicado, tensao_publicada))

            for agente_a, agente_b in ENLACES_DO_GRAFO_NOMINAL:
                if agente_de_origem == agente_a:
                    agente_de_destino = agente_b
                elif agente_de_origem == agente_b:
                    agente_de_destino = agente_a
                else:
                    continue  # este enlace não toca o agente de origem

                # Motivo da perda: a falha PERMANENTE do enlace (C1/C2) tem prioridade;
                # em C2 o líder também fica sem vizinhos, mas isso é consequência
                # do enlace (1,2) fora, não de uma falha do agente (C3).
                enlace_esta_ativo = matriz_de_adjacencia[agente_de_origem, agente_de_destino] > 0
                enlace_removido_pelo_cenario = (agente_a, agente_b) in self.definicao_do_cenario.arestas_removidas
                agente_isolado_pelo_cenario = self.definicao_do_cenario.indice_do_agente_isolado
                if enlace_esta_ativo:
                    situacao = "ENTREGUE"
                    motivo = ""
                elif enlace_removido_pelo_cenario:
                    situacao = "PERDIDA"
                    motivo = f"enlace {formatar_enlace((agente_a, agente_b))} fora (falha permanente)"
                elif agente_isolado_pelo_cenario in (agente_de_origem, agente_de_destino):
                    situacao = "PERDIDA"
                    motivo = f"agente {self._nome_do_agente(agente_isolado_pelo_cenario)} isolado (falha temporária C3)"
                else:
                    situacao = "PERDIDA"
                    motivo = f"enlace {formatar_enlace((agente_a, agente_b))} fora"

                self.numero_global_de_mensagem += 1
                texto_do_motivo = f" ({motivo})" if motivo else ""
                self.logger.debug(
                    f"[t_sim={instante_simulado} k={iteracao:03d}] MSG #{self.numero_global_de_mensagem:07d} "
                    f"{self._nome_do_agente(agente_de_origem)} -> {self._nome_do_agente(agente_de_destino)} "
                    f"stNum={self.numero_de_estado_stnum[agente_de_origem]} sqNum={self.numero_de_sequencia_sqnum[agente_de_origem]} "
                    f"| rho={rho_publicado:.6f} V={tensao_publicada:.6f} pu | {situacao}{texto_do_motivo}"
                )
                self.mensagens.append(
                    {
                        "timestamp_real": datetime.now(UTC).isoformat(timespec="milliseconds"),
                        "instante_simulado": instante_simulado,
                        "arquitetura": self.arquitetura,
                        "cenario": self.definicao_do_cenario.nome,
                        "hora": self.hora_atual,
                        "iteracao_k": iteracao,
                        "numero_da_mensagem": self.numero_global_de_mensagem,
                        "origem_posicao": agente_de_origem + 1,
                        "origem_barra": self.agentes[agente_de_origem].barra,
                        "destino_posicao": agente_de_destino + 1,
                        "destino_barra": self.agentes[agente_de_destino].barra,
                        "stNum": self.numero_de_estado_stnum[agente_de_origem],
                        "sqNum": self.numero_de_sequencia_sqnum[agente_de_origem],
                        "conteudo_rho": rho_publicado,
                        "conteudo_tensao_pu": tensao_publicada,
                        "situacao": situacao,
                        "motivo_da_perda": motivo,
                    }
                )

    def registrar_iteracao(self, iteracao, matriz_de_adjacencia, fracao_de_curtailment, tensoes_locais):
        """
        Registra a troca de mensagens da iteração k: cada mensagem (quem -> quem,
        conteúdo, entregue/perdida) e o estado da rede (enlaces, partições,
        saltos até o líder, idade da informação).
        """
        enlaces_ativos = listar_enlaces_ativos(matriz_de_adjacencia)
        enlaces_perdidos = [enlace for enlace in ENLACES_DO_GRAFO_NOMINAL if enlace not in enlaces_ativos]
        componentes = encontrar_componentes_conexas(matriz_de_adjacencia)
        lambda_2 = calcular_conectividade_algebrica(matriz_de_adjacencia)
        saltos_ate_o_lider = calcular_saltos_ate_o_agente(matriz_de_adjacencia, INDICE_DO_LIDER_NO_GRAFO)
        agentes_que_o_lider_observa = encontrar_componente_do_agente(matriz_de_adjacencia, INDICE_DO_LIDER_NO_GRAFO)

        agentes_isolados = []
        for indice in range(len(self.agentes)):
            numero_de_vizinhos = int(matriz_de_adjacencia[indice, :].sum())
            if numero_de_vizinhos == 0:
                agentes_isolados.append(indice)
                self.idade_da_informacao[indice] += 1  # não recebeu nada nesta iteração
            else:
                self.idade_da_informacao[indice] = 0

        # Cada enlace não direcionado carrega 2 mensagens por iteração (i->j e j->i).
        mensagens_enviadas = 2 * len(enlaces_ativos)
        mensagens_perdidas = 2 * len(enlaces_perdidos)
        self.mensagens_enviadas_na_hora += mensagens_enviadas
        self.mensagens_perdidas_na_hora += mensagens_perdidas
        if enlaces_perdidos:
            self.iteracoes_com_falha_na_hora += 1

        instante_simulado = self.calcular_instante_simulado(iteracao)
        carimbo_simulado = f"[t_sim={instante_simulado} k={iteracao:03d}]"
        texto_do_estado = (
            f"enlaces {len(enlaces_ativos)}/{len(ENLACES_DO_GRAFO_NOMINAL)}"
            f" | perdidos: {' '.join(formatar_enlace(e) for e in enlaces_perdidos) or '-'}"
            f" | isolados: {' '.join(self._nome_do_agente(i) for i in agentes_isolados) or '-'}"
            f" | partições: {formatar_particoes(componentes)} | λ2={lambda_2:.3f}"
        )
        if self.estado_inicial_da_hora is None:
            self.estado_inicial_da_hora = texto_do_estado

        # Ordem do log: primeiro o EVENTO (mudança da rede), depois as mensagens da iteração.
        self._registrar_eventos_de_mudanca(carimbo_simulado, enlaces_ativos, texto_do_estado)
        self.enlaces_da_iteracao_anterior = enlaces_ativos
        self._registrar_mensagens_da_iteracao(
            iteracao, instante_simulado, matriz_de_adjacencia, fracao_de_curtailment, tensoes_locais
        )

        texto_dos_saltos = " ".join(
            f"{indice + 1}:{'∞' if saltos is None else saltos}" for indice, saltos in enumerate(saltos_ate_o_lider)
        )
        texto_da_idade = " ".join(f"{indice + 1}:{idade}" for indice, idade in enumerate(self.idade_da_informacao))
        self.logger.debug(
            f"{carimbo_simulado} {texto_do_estado} | msgs {mensagens_enviadas} enviadas, {mensagens_perdidas} perdidas"
            f" | saltos até o líder {texto_dos_saltos} | idade da info {texto_da_idade}"
        )

        registro = {
            "timestamp_real": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "instante_simulado": instante_simulado,
            "arquitetura": self.arquitetura,
            "cenario": self.definicao_do_cenario.nome,
            "hora": self.hora_atual,
            "iteracao_k": iteracao,
            "enlaces_ativos": len(enlaces_ativos),
            "enlaces_perdidos": " ".join(formatar_enlace(e) for e in enlaces_perdidos),
            "agentes_isolados": " ".join(self._nome_do_agente(i) for i in agentes_isolados),
            "particoes": formatar_particoes(componentes),
            "numero_de_particoes": len(componentes),
            "lambda_2": lambda_2,
            "mensagens_enviadas": mensagens_enviadas,
            "mensagens_perdidas": mensagens_perdidas,
            "agentes_observados_pelo_lider": " ".join(str(indice + 1) for indice in agentes_que_o_lider_observa),
        }
        for indice, agente in enumerate(self.agentes):
            registro[f"saltos_ate_lider_{agente.barra}"] = saltos_ate_o_lider[indice]
            registro[f"idade_da_info_{agente.barra}"] = self.idade_da_informacao[indice]
        self.registros.append(registro)

    def _registrar_eventos_de_mudanca(self, carimbo_simulado, enlaces_ativos, texto_do_estado):
        """
        Compara com a iteração anterior e registra (no terminal também) quando a
        comunicação muda: enlace caiu, enlace voltou. Na 1ª iteração da hora,
        compara com o grafo nominal, para deixar explícito se a hora já começa degradada.
        """
        if self.enlaces_da_iteracao_anterior is None:
            enlaces_de_comparacao = list(ENLACES_DO_GRAFO_NOMINAL)
        else:
            enlaces_de_comparacao = self.enlaces_da_iteracao_anterior

        enlaces_que_cairam = [e for e in enlaces_de_comparacao if e not in enlaces_ativos]
        enlaces_que_voltaram = [e for e in enlaces_ativos if e not in enlaces_de_comparacao]

        # Falha permanente (C1/C2) já anunciada no cabeçalho: não repetir a cada hora.
        falha_permanente_ja_anunciada = (
            self.enlaces_da_iteracao_anterior is None
            and set(enlaces_que_cairam) == set(self.definicao_do_cenario.arestas_removidas)
        )
        if enlaces_que_cairam and not falha_permanente_ja_anunciada:
            self.eventos_na_hora += 1
            self.logger.info(
                f"{carimbo_simulado} EVENTO FALHA: caiu(caíram) {' '.join(formatar_enlace(e) for e in enlaces_que_cairam)}"
                f" -> {texto_do_estado}"
            )
        if enlaces_que_voltaram:
            self.eventos_na_hora += 1
            self.logger.info(
                f"{carimbo_simulado} EVENTO RECUPERAÇÃO: voltou(voltaram) {' '.join(formatar_enlace(e) for e in enlaces_que_voltaram)}"
                f" -> {texto_do_estado}"
            )

    def finalizar_hora(self, numero_de_iteracoes, status, tensao_maxima_barras_pv):
        """Resumo da hora no terminal e no arquivo (só se o consenso precisou rodar)."""
        if numero_de_iteracoes == 0:
            self.logger.debug(f"[t={self.hora_atual:02d}:00] sem sobretensão: nenhuma mensagem trocada")
            return
        self.logger.info(
            f"[t={self.hora_atual:02d}:00] fim da hora: k={numero_de_iteracoes} status={status} "
            f"Vmax_pv={tensao_maxima_barras_pv:.4f} | msgs {self.mensagens_enviadas_na_hora} enviadas, "
            f"{self.mensagens_perdidas_na_hora} perdidas | iterações sob falha {self.iteracoes_com_falha_na_hora}"
            f"/{numero_de_iteracoes} | início: {self.estado_inicial_da_hora}"
        )

    def finalizar_caso(self):
        """Fecha o arquivo de log do caso."""
        for manipulador in list(self.logger.handlers):
            manipulador.close()
            self.logger.removeHandler(manipulador)


# =============================================================================
# CONTROLE — consenso proporcional sobre rho_i, duas arquiteturas (§4.4, §4.5)
# =============================================================================
#
# Convenção de sinal (declarada aqui para não confundir com o paper-âncora):
#   rho_i = fração de CURTAILMENT do agente i (§2.1): P_curt,i = rho_i * P_available,i.
#   Sob sobretensão o curtailment precisa AUMENTAR, então o termo de correção
#   c_i(k) >= 0 é SOMADO:
#
#       rho_i(k+1) = clip[ rho_i(k) + eps * sum_j a_ij (rho_j - rho_i) + c_i(k), 0, 1 ]
#
#   Isso é exatamente a Eq. (2) do paper-âncora escrita para beta_i = 1 - rho_i
#   (fração INJETADA), onde a correção aparece com sinal negativo. A mistura por
#   consenso é linear, então as duas formas têm dinâmica idêntica. (O "- c_i" de
#   §4.5 mistura as duas convenções; aqui fica explícito.)


def misturar_por_consenso(fracao_de_curtailment, matriz_de_adjacencia, epsilon):
    """
    Termo de mistura: rho_i + eps * sum_j a_ij (rho_j - rho_i) = (I - eps*L) rho.

    É IDÊNTICO nas duas arquiteturas (§4.5) — só c_i(k) difere.
    """
    laplaciana = calcular_laplaciana(matriz_de_adjacencia)
    return fracao_de_curtailment - epsilon * (laplaciana @ fracao_de_curtailment)


def misturar_por_consenso_com_canal(fracao_de_curtailment, matriz_de_adjacencia, epsilon, canal, iteracao):
    """Mistura usando o último estado recebido por cada enlace direcionado.

    A ausência de uma mensagem nova usa explicitamente a última mensagem válida;
    antes da primeira entrega, usa o estado local atual como inicialização.
    """
    numero_de_agentes = len(fracao_de_curtailment)
    for origem, destino in zip(*np.where(np.triu(matriz_de_adjacencia, k=1) > 0)):
        canal.transmit(origem, destino, {"rho": float(fracao_de_curtailment[origem])}, iteracao)
        canal.transmit(destino, origem, {"rho": float(fracao_de_curtailment[destino])}, iteracao)
    canal.deliver_until(iteracao)

    resultado = fracao_de_curtailment.copy()
    for destino in range(numero_de_agentes):
        for origem in range(numero_de_agentes):
            if matriz_de_adjacencia[destino, origem] <= 0:
                continue
            mensagem = canal.current_state(origem, destino)
            rho_recebido = fracao_de_curtailment[origem] if mensagem is None else mensagem.content["rho"]
            resultado[destino] += epsilon * (rho_recebido - fracao_de_curtailment[destino])
    return resultado


def calcular_tensao_monitorada_pelo_lider(tensoes_locais, matriz_de_adjacencia, indice_do_lider):
    """
    V_max-mon(k) do Leader-Follower (§7.3): máximo das tensões das barras com PV
    que o líder CONSEGUE OBSERVAR, isto é, dentro da sua componente conexa em A(k).
    Sob C0 coincide com o máximo global das barras com PV (código de referência).
    """
    agentes_observaveis = encontrar_componente_do_agente(matriz_de_adjacencia, indice_do_lider)
    return float(np.max(tensoes_locais[agentes_observaveis]))


def corrigir_leader_follower(tensoes_locais, matriz_de_adjacencia, indice_do_lider):
    """
    c_i(k) do Leader-Follower (§4.5):
        c_i = 1{i = líder} * beta * e_V,   e_V = max(0, V_max-mon - V_lim)
    Só o líder recebe correção; os demais só recebem informação por consenso.
    """
    tensao_monitorada = calcular_tensao_monitorada_pelo_lider(tensoes_locais, matriz_de_adjacencia, indice_do_lider)
    erro_de_tensao = max(0.0, tensao_monitorada - TENSAO_LIMITE_PU)  # e_V(k)

    termo_de_correcao = np.zeros(len(tensoes_locais))
    termo_de_correcao[indice_do_lider] = GANHO_DE_CORRECAO_DE_TENSAO * erro_de_tensao
    return termo_de_correcao


def corrigir_leaderless(tensoes_locais):
    """
    c_i(k) do Leaderless (§4.5, adaptado de Kitso et al. 2025):
        c_i = beta * e_V,i,   e_V,i = max(0, V_i - V_lim)   para todo i
    Cada agente usa a SUA tensão local — nunca a tensão monitorada do líder
    (erro de implementação mais provável, alertado em §6).
    """
    termo_de_correcao = np.zeros(len(tensoes_locais))
    for indice_do_agente in range(len(tensoes_locais)):
        erro_de_tensao_local = max(0.0, tensoes_locais[indice_do_agente] - TENSAO_LIMITE_PU)  # e_V,i(k)
        termo_de_correcao[indice_do_agente] = GANHO_DE_CORRECAO_DE_TENSAO * erro_de_tensao_local
    return termo_de_correcao


def calcular_termo_de_correcao(arquitetura, tensoes_locais, matriz_de_adjacencia, indice_do_lider):
    """Despacha para a função de correção da arquitetura — a ÚNICA diferença entre elas (§5.2)."""
    if arquitetura == ARQUITETURA_LEADER_FOLLOWER:
        return corrigir_leader_follower(tensoes_locais, matriz_de_adjacencia, indice_do_lider)
    if arquitetura == ARQUITETURA_LEADERLESS:
        return corrigir_leaderless(tensoes_locais)
    raise ValueError(f"Arquitetura desconhecida: {arquitetura}")


def calcular_tensao_vista_pelo_controle(arquitetura, tensoes_locais, matriz_de_adjacencia, indice_do_lider):
    """
    Tensão que o CONTROLE usa no critério de parada (§4.7).

    Leader-Follower: V_max-mon do líder (restrita ao que ele observa).
    Leaderless: cada agente decide pela própria tensão; o laço síncrono só
    termina quando TODOS estão satisfeitos -> máximo das tensões locais.

    Importante: sob falha, o líder pode "achar" que resolveu (sua componente
    está abaixo do limite) enquanto outra partição continua violando. Por isso
    a violação REAL é registrada separadamente (H2/H5).
    """
    if arquitetura == ARQUITETURA_LEADER_FOLLOWER:
        return calcular_tensao_monitorada_pelo_lider(tensoes_locais, matriz_de_adjacencia, indice_do_lider)
    return float(np.max(tensoes_locais))


def criterio_de_parada_eletrico_satisfeito(tensao_vista_pelo_controle):
    """
    Critério de parada puramente elétrico (§4.7): V_max-mon <= V_ref + tol.

    Por que não usar e_c(k) < tolerância: os rho_i de uma partição sem
    correção podem concordar entre si rapidamente sem nunca corrigir a tensão;
    um critério por consenso reportaria isso como "convergido" (§4.7, H2).
    """
    return tensao_vista_pelo_controle <= TENSAO_LIMITE_PU + TOLERANCIA_DE_TENSAO_PU


# =============================================================================
# MÉTRICAS (§3, Fase 0 §20–23)
# =============================================================================


def calcular_erro_de_consenso(fracao_de_curtailment, indices_dos_agentes=None):
    """
    e_c(k) = sqrt( (1/N) sum_i (rho_i - rho_medio)^2 )  (Fase 0 §20.1).
    Se `indices_dos_agentes` for dado, calcula só dentro desse subconjunto.
    """
    if indices_dos_agentes is None:
        indices_dos_agentes = list(range(len(fracao_de_curtailment)))
    valores = fracao_de_curtailment[indices_dos_agentes]
    return float(np.sqrt(np.mean((valores - np.mean(valores)) ** 2)))


def calcular_maior_erro_de_consenso_dentro_das_componentes(fracao_de_curtailment, componentes):
    """Maior e_c calculado dentro de cada componente conexa (consenso LOCAL, H2)."""
    maior_erro = 0.0
    for componente in componentes:
        maior_erro = max(maior_erro, calcular_erro_de_consenso(fracao_de_curtailment, componente))
    return maior_erro


def calcular_razao_de_curtailment(potencia_cortada, potencia_disponivel):
    """
    r_i = P_curt,i / P_available,i (Fase 0 §23). Agentes sem potência
    disponível (P_available = 0) ficam como NaN — não participam da dispersão.
    """
    razao = np.full(len(potencia_disponivel), np.nan)
    for indice in range(len(potencia_disponivel)):
        if potencia_disponivel[indice] > 1e-9:
            razao[indice] = potencia_cortada[indice] / potencia_disponivel[indice]
    return razao


def calcular_dispersao_sigma_r(razao_de_curtailment, indices_dos_agentes=None):
    """
    sigma_r = sqrt( (1/N) sum_i (r_i - r_medio)^2 )  (Fase 0 §23, H2).
    Ignora agentes com r_i = NaN. Retorna NaN se não sobrar nenhum.
    """
    if indices_dos_agentes is None:
        indices_dos_agentes = list(range(len(razao_de_curtailment)))
    valores = razao_de_curtailment[indices_dos_agentes]
    valores = valores[~np.isnan(valores)]
    if len(valores) == 0:
        return float("nan")
    return float(np.sqrt(np.mean((valores - np.mean(valores)) ** 2)))


def calcular_sigma_r_por_particao(razao_de_curtailment, componentes):
    """sigma_r dentro de cada componente conexa (obrigatório para H2 em C2, §3)."""
    sigma_por_particao = []
    for componente in componentes:
        sigma_por_particao.append(calcular_dispersao_sigma_r(razao_de_curtailment, componente))
    return sigma_por_particao


def calcular_violacao_acumulada_por_agente(tensoes_por_hora_e_agente):
    """
    S_i = sum_t max(0, V_i(t) - V_lim) * Delta t   (Critério B, §4.4.1).
    Entrada: matriz [24 horas x N agentes] de tensões do caso sem controle.
    """
    excesso_de_tensao = np.maximum(0.0, tensoes_por_hora_e_agente - TENSAO_LIMITE_PU)
    return excesso_de_tensao.sum(axis=0) * DURACAO_DO_PASSO_HORAS


def determinar_lider_por_criterio_B(violacao_acumulada, agentes_ordem_de_referencia):
    """Líder = argmax_i S_i (§4.4.1). Fixo durante toda a simulação (§7.6a)."""
    indice_do_lider = int(np.argmax(violacao_acumulada))
    return agentes_ordem_de_referencia[indice_do_lider]


def ordenar_agentes_na_ordem_do_grafo(agentes_ordem_de_referencia, violacao_acumulada):
    """
    Atribui as posições 1..6 do grafo de §4.3 às barras físicas (§4.4.1, checklist item 4):
      posição 1 (índice 0) -> líder (maior S_i): o nó que C2 isola;
      posição 6 (índice 5) -> agente com menor S_i: contraste "m != líder" de C3 (§7.6);
      posições 2..5        -> demais agentes, na ordem do código de referência.
    """
    indice_do_lider = int(np.argmax(violacao_acumulada))
    indice_do_menor_s = int(np.argmin(violacao_acumulada))
    if indice_do_menor_s == indice_do_lider:
        # Só acontece se todos os S_i forem iguais (ex.: nenhuma sobretensão).
        indice_do_menor_s = len(agentes_ordem_de_referencia) - 1 if indice_do_lider == 0 else 0

    agentes_intermediarios = []
    for indice, agente in enumerate(agentes_ordem_de_referencia):
        if indice not in (indice_do_lider, indice_do_menor_s):
            agentes_intermediarios.append(agente)

    return (
        [agentes_ordem_de_referencia[indice_do_lider]]
        + agentes_intermediarios
        + [agentes_ordem_de_referencia[indice_do_menor_s]]
    )


# =============================================================================
# SIMULAÇÃO — snapshots horários sequenciais (§5.1, §5.2)
# =============================================================================


def criar_agentes_na_ordem_de_referencia():
    """Lista de agentes na ordem do código de referência (§4.2)."""
    agentes = []
    for numero, (barra, potencia_kva) in enumerate(
        zip(BARRAS_DOS_PVS_ORDEM_DE_REFERENCIA, POTENCIA_NOMINAL_KVA_ORDEM_DE_REFERENCIA), start=1
    ):
        agentes.append(AgenteFotovoltaico(f"pv{numero}", barra, FATOR_DE_ESCALA_DOS_PVS * potencia_kva))
    return agentes


def simular_dia_sem_controle(curvas, agentes):
    """
    Estratégia A (Fase 0 §19): nenhuma ação coordenada.

    Retorna (DataFrame por hora x agente, matriz [24 x N] de tensões locais,
             DataFrame por hora x barra da rede).
    """
    construir_circuito_com_pvs(agentes)
    registros = []
    registros_de_todas_as_barras = []
    tensoes_por_hora_e_agente = np.zeros((24, len(agentes)))

    for hora in range(24):
        aplicar_perfil_da_hora(curvas, hora, agentes)
        restaurar_pvs_sem_curtailment(agentes)
        resolver_fluxo_de_potencia()

        tensoes_locais = medir_tensoes_locais_dos_agentes(agentes)
        potencia_gerada = medir_potencia_ativa_gerada_por_agente_kw(agentes)
        tensao_maxima_da_rede = medir_tensao_maxima_da_rede_pu()
        tensoes_por_hora_e_agente[hora, :] = tensoes_locais
        registros_de_todas_as_barras.extend(medir_estado_de_todas_as_barras("sem_controle", "sem_controle", hora))

        for indice, agente in enumerate(agentes):
            registros.append(
                {
                    "arquitetura": "sem_controle",
                    "cenario": "sem_controle",
                    "hora": hora,
                    "agente": agente.nome_do_pvsystem,
                    "barra": agente.barra,
                    "potencia_disponivel_kw": potencia_gerada[indice],
                    "potencia_gerada_kw": potencia_gerada[indice],
                    "potencia_cortada_kw": 0.0,
                    "fracao_de_curtailment_rho": 0.0,
                    "tensao_inicial_pu": tensoes_locais[indice],
                    "tensao_final_pu": tensoes_locais[indice],
                    "tensao_maxima_barras_pv_pu": float(np.max(tensoes_locais)),
                    "tensao_maxima_rede_pu": tensao_maxima_da_rede,
                }
            )

    return pd.DataFrame(registros), tensoes_por_hora_e_agente, pd.DataFrame(registros_de_todas_as_barras)


def executar_consenso_na_hora(
    arquitetura, grafo_de_comunicacao, hora, agentes, potencia_disponivel_kw, tensoes_iniciais, epsilon,
    registrador_de_comunicacao, canal=None,
):
    """
    Laço de consenso de UMA hora (§5.2).

    Por que o tempo NÃO avança aqui dentro: todas as iterações k representam
    o mesmo instante físico. Se o tempo avançasse, a curva de carga mudaria
    entre iterações e a semântica "quantas iterações sob falha" (C3) se perderia (§5.1).

    Retorna um dicionário com o estado final e a lista de registros por iteração.
    """
    numero_de_agentes = len(agentes)
    # Estado pré-controle da hora: nenhum curtailment (§5.2 "resetar comandos").
    fracao_de_curtailment = np.zeros(numero_de_agentes)  # rho_i(k), §4.5
    tensoes_locais = tensoes_iniciais.copy()
    registros_das_iteracoes = []
    houve_correcao_fora_do_lider = False

    iteracao = 0
    while True:
        matriz_de_adjacencia = grafo_de_comunicacao.matriz_de_adjacencia_na_iteracao(hora, iteracao)
        tensao_vista_pelo_controle = calcular_tensao_vista_pelo_controle(
            arquitetura, tensoes_locais, matriz_de_adjacencia, INDICE_DO_LIDER_NO_GRAFO
        )
        if criterio_de_parada_eletrico_satisfeito(tensao_vista_pelo_controle):
            break
        if iteracao >= NUMERO_MAXIMO_DE_ITERACOES:
            break

        # Troca de mensagens desta iteração -> log de comunicação com timestamp.
        registrador_de_comunicacao.registrar_iteracao(
            iteracao, matriz_de_adjacencia, fracao_de_curtailment, tensoes_locais
        )

        termo_de_correcao = calcular_termo_de_correcao(
            arquitetura, tensoes_locais, matriz_de_adjacencia, INDICE_DO_LIDER_NO_GRAFO
        )
        # Checagem de §6: em LF, correção não nula em agente que não é líder é bug.
        if arquitetura == ARQUITETURA_LEADER_FOLLOWER:
            for indice in range(numero_de_agentes):
                if indice != INDICE_DO_LIDER_NO_GRAFO and termo_de_correcao[indice] != 0.0:
                    houve_correcao_fora_do_lider = True

        if canal is None:
            fracao_misturada = misturar_por_consenso(fracao_de_curtailment, matriz_de_adjacencia, epsilon)
        else:
            fracao_misturada = misturar_por_consenso_com_canal(
                fracao_de_curtailment, matriz_de_adjacencia, epsilon, canal, iteracao
            )
        fracao_de_curtailment = np.clip(fracao_misturada + termo_de_correcao, 0.0, 1.0)

        aplicar_curtailment_nos_pvs(agentes, fracao_de_curtailment, potencia_disponivel_kw)
        resolver_fluxo_de_potencia()
        tensoes_locais = medir_tensoes_locais_dos_agentes(agentes)
        iteracao += 1

        componentes = encontrar_componentes_conexas(matriz_de_adjacencia)
        registro = {
            "hora": hora,
            "iteracao_k": iteracao,
            "erro_de_consenso_global": calcular_erro_de_consenso(fracao_de_curtailment),
            "erro_de_consenso_max_intra_particao": calcular_maior_erro_de_consenso_dentro_das_componentes(
                fracao_de_curtailment, componentes
            ),
            "enlaces_ativos": int(matriz_de_adjacencia.sum() / 2),
            "lambda_2": calcular_conectividade_algebrica(matriz_de_adjacencia),
            "agente_isolado_c3": grafo_de_comunicacao.agente_esta_isolado(hora, iteracao - 1),
            "tensao_vista_pelo_controle_pu": tensao_vista_pelo_controle,
            "tensao_maxima_barras_pv_pu": float(np.max(tensoes_locais)),
        }
        for indice, agente in enumerate(agentes):
            registro[f"rho_{agente.barra}"] = fracao_de_curtailment[indice]
            registro[f"tensao_{agente.barra}"] = tensoes_locais[indice]
        registros_das_iteracoes.append(registro)

    # Estado final da hora: a matriz de adjacência da última checagem define as partições.
    matriz_final = grafo_de_comunicacao.matriz_de_adjacencia_na_iteracao(hora, iteracao)
    tensao_final_vista_pelo_controle = calcular_tensao_vista_pelo_controle(
        arquitetura, tensoes_locais, matriz_final, INDICE_DO_LIDER_NO_GRAFO
    )
    controle_satisfeito = criterio_de_parada_eletrico_satisfeito(tensao_final_vista_pelo_controle)
    erro_de_consenso_global_final = calcular_erro_de_consenso(fracao_de_curtailment)
    erro_de_consenso_max_intra_particao_final = calcular_maior_erro_de_consenso_dentro_das_componentes(
        fracao_de_curtailment, encontrar_componentes_conexas(matriz_final)
    )
    consenso_satisfeito = erro_de_consenso_global_final <= TOLERANCIA_DE_CONSENSO

    if iteracao == 0:
        status = "sem_sobretensao"  # o controle nem precisou agir
    elif controle_satisfeito:
        status = "convergiu"
    else:
        status = "nao_convergiu"  # atingiu k_max: NUNCA reportar como regulação bem-sucedida (§4.7)

    return {
        "fracao_de_curtailment": fracao_de_curtailment,
        "tensoes_locais": tensoes_locais,
        "numero_de_iteracoes": iteracao,
        "status": status,
        "criterios": {
            "eletrico_satisfeito": bool(controle_satisfeito),
            "consenso_satisfeito": bool(consenso_satisfeito),
            "atingiu_k_max": bool(iteracao >= NUMERO_MAXIMO_DE_ITERACOES),
        },
        "erro_de_consenso_global_final": erro_de_consenso_global_final,
        "erro_de_consenso_max_intra_particao_final": erro_de_consenso_max_intra_particao_final,
        "componentes_finais": encontrar_componentes_conexas(matriz_final),
        "registros_das_iteracoes": registros_das_iteracoes,
        "houve_correcao_fora_do_lider": houve_correcao_fora_do_lider,
        "metricas_do_canal": None if canal is None else canal.metrics(),
    }


def simular_dia_com_consenso(arquitetura, definicao_do_cenario, curvas, agentes, hora_de_pico, epsilon):
    """
    Um caso completo (arquitetura x cenário): 24 snapshots horários (§5.2).

    Retorna um dicionário com DataFrames: "por_hora" (hora x agente),
    "por_iteracao", "todas_as_barras" (hora x barra da rede), "comunicacao"
    (log por iteração) e o dict "checagens".
    """
    construir_circuito_com_pvs(agentes)  # Clear + compile: sem vazamento entre casos
    grafo_de_comunicacao = GrafoDeComunicacao(definicao_do_cenario, hora_de_pico)
    registrador_de_comunicacao = RegistradorDeComunicacao(arquitetura, definicao_do_cenario, agentes)
    registrador_de_comunicacao.iniciar_caso()

    registros_por_hora = []
    registros_por_iteracao = []
    registros_de_todas_as_barras = []
    registros_do_canal = []
    checagens = {"correcao_fora_do_lider": False}

    for hora in range(24):
        aplicar_perfil_da_hora(curvas, hora, agentes)
        restaurar_pvs_sem_curtailment(agentes)
        resolver_fluxo_de_potencia()  # estado sem controle da hora

        tensoes_iniciais = medir_tensoes_locais_dos_agentes(agentes)
        potencia_disponivel_kw = medir_potencia_ativa_gerada_por_agente_kw(agentes)

        registrador_de_comunicacao.iniciar_hora(hora)
        canal = None
        if CONFIGURACAO_COMUNICACAO["habilitado"] and definicao_do_cenario.canal_habilitado:
            from tcc_facens.communication import CommunicationChannel

            semente = CONFIGURACAO_COMUNICACAO["semente"]
            semente_da_hora = None if semente is None else semente + hora
            canal = CommunicationChannel(
                loss_probability=definicao_do_cenario.probabilidade_de_perda_do_canal,
                delay_steps=CONFIGURACAO_COMUNICACAO["atraso_em_iteracoes"],
                seed=semente_da_hora,
            )
        resultado = executar_consenso_na_hora(
            arquitetura, grafo_de_comunicacao, hora, agentes, potencia_disponivel_kw, tensoes_iniciais, epsilon,
            registrador_de_comunicacao, canal,
        )
        if canal is not None:
            for evento in canal.events:
                registros_do_canal.append(
                    {
                        **evento,
                        "arquitetura": arquitetura,
                        "cenario": definicao_do_cenario.nome,
                        "hora": hora,
                    }
                )
        if resultado["houve_correcao_fora_do_lider"]:
            checagens["correcao_fora_do_lider"] = True

        # Medições do estado elétrico FINAL resolvido (não só do comando).
        potencia_gerada_kw = medir_potencia_ativa_gerada_por_agente_kw(agentes)
        potencia_cortada_kw = np.maximum(potencia_disponivel_kw - potencia_gerada_kw, 0.0)
        tensao_maxima_da_rede = medir_tensao_maxima_da_rede_pu()
        tensao_maxima_barras_pv = float(np.max(resultado["tensoes_locais"]))
        razao_de_curtailment = calcular_razao_de_curtailment(potencia_cortada_kw, potencia_disponivel_kw)
        componentes = resultado["componentes_finais"]
        sigma_r_por_particao = calcular_sigma_r_por_particao(razao_de_curtailment, componentes)
        registrador_de_comunicacao.finalizar_hora(resultado["numero_de_iteracoes"], resultado["status"], tensao_maxima_barras_pv)
        registros_de_todas_as_barras.extend(medir_estado_de_todas_as_barras(arquitetura, definicao_do_cenario.nome, hora))

        for indice, agente in enumerate(agentes):
            identificador_da_particao = 0
            for numero_da_particao, componente in enumerate(componentes):
                if indice in componente:
                    identificador_da_particao = numero_da_particao
            registros_por_hora.append(
                {
                    "arquitetura": arquitetura,
                    "cenario": definicao_do_cenario.nome,
                    "hora": hora,
                    "agente": agente.nome_do_pvsystem,
                    "barra": agente.barra,
                    "posicao_no_grafo": indice + 1,
                    "eh_lider": indice == INDICE_DO_LIDER_NO_GRAFO,
                    "particao_final": identificador_da_particao,
                    "potencia_disponivel_kw": potencia_disponivel_kw[indice],
                    "potencia_gerada_kw": potencia_gerada_kw[indice],
                    "potencia_cortada_kw": potencia_cortada_kw[indice],
                    "fracao_de_curtailment_rho": resultado["fracao_de_curtailment"][indice],
                    "razao_de_curtailment_r": razao_de_curtailment[indice],
                    "tensao_inicial_pu": tensoes_iniciais[indice],
                    "tensao_final_pu": resultado["tensoes_locais"][indice],
                    "tensao_maxima_barras_pv_pu": tensao_maxima_barras_pv,
                    "tensao_maxima_rede_pu": tensao_maxima_da_rede,
                    "iteracoes": resultado["numero_de_iteracoes"],
                    "status": resultado["status"],
                    "status_eletrico": resultado["status"],
                    "eletrico_satisfeito": resultado["criterios"]["eletrico_satisfeito"],
                    "consenso_satisfeito": resultado["criterios"]["consenso_satisfeito"],
                    "atingiu_k_max": resultado["criterios"]["atingiu_k_max"],
                    "erro_de_consenso_global_final": resultado["erro_de_consenso_global_final"],
                    "erro_de_consenso_max_intra_particao_final": resultado["erro_de_consenso_max_intra_particao_final"],
                    "mensagens_do_canal_tentadas": None if resultado["metricas_do_canal"] is None else resultado["metricas_do_canal"]["messages_attempted"],
                    "mensagens_do_canal_entregues": None if resultado["metricas_do_canal"] is None else resultado["metricas_do_canal"]["messages_delivered"],
                    "mensagens_do_canal_perdidas": None if resultado["metricas_do_canal"] is None else resultado["metricas_do_canal"]["messages_lost"],
                    "mensagens_do_canal_pendentes": None if resultado["metricas_do_canal"] is None else resultado["metricas_do_canal"]["messages_pending"],
                    # Violação REAL (independe do que o controle "vê"): chave para H5.
                    "violacao_real_apos_controle": tensao_maxima_barras_pv
                    > TENSAO_LIMITE_PU + TOLERANCIA_DE_TENSAO_PU,
                    "sigma_r_global_hora": calcular_dispersao_sigma_r(razao_de_curtailment),
                    "sigma_r_por_particao_hora": json.dumps(
                        [None if np.isnan(valor) else round(valor, 6) for valor in sigma_r_por_particao]
                    ),
                }
            )

        for registro in resultado["registros_das_iteracoes"]:
            registro["arquitetura"] = arquitetura
            registro["cenario"] = definicao_do_cenario.nome
            registros_por_iteracao.append(registro)

    registrador_de_comunicacao.finalizar_caso()
    return {
        "por_hora": pd.DataFrame(registros_por_hora),
        "por_iteracao": pd.DataFrame(registros_por_iteracao),
        "todas_as_barras": pd.DataFrame(registros_de_todas_as_barras),
        "comunicacao": pd.DataFrame(registrador_de_comunicacao.registros),
        "mensagens": pd.DataFrame(registrador_de_comunicacao.mensagens),
        "mensagens_do_canal": pd.DataFrame(registros_do_canal),
        "checagens": checagens,
    }


# =============================================================================
# RESUMOS POR CASO (tabelas de §5.5 summary/)
# =============================================================================


def resumir_um_caso(dados_por_hora, hora_de_pico):
    """
    Métricas diárias e da hora de pico de UM caso (arquitetura x cenário).
    """
    energia_disponivel_por_agente = dados_por_hora.groupby("barra")["potencia_disponivel_kw"].sum() * DURACAO_DO_PASSO_HORAS
    energia_cortada_por_agente = dados_por_hora.groupby("barra")["potencia_cortada_kw"].sum() * DURACAO_DO_PASSO_HORAS
    razao_diaria_por_agente = calcular_razao_de_curtailment(
        energia_cortada_por_agente.to_numpy(), energia_disponivel_por_agente.to_numpy()
    )

    uma_linha_por_hora = dados_por_hora.drop_duplicates("hora")
    dados_da_hora_de_pico = dados_por_hora[dados_por_hora["hora"] == hora_de_pico]
    linha_da_hora_de_pico = dados_da_hora_de_pico.iloc[0]

    horas_com_violacao = int(
        (uma_linha_por_hora["tensao_maxima_barras_pv_pu"] > TENSAO_LIMITE_PU + TOLERANCIA_DE_TENSAO_PU).sum()
    )

    resumo = {
        "arquitetura": linha_da_hora_de_pico["arquitetura"],
        "cenario": linha_da_hora_de_pico["cenario"],
        "tensao_maxima_barras_pv_dia_pu": float(uma_linha_por_hora["tensao_maxima_barras_pv_pu"].max()),
        "tensao_maxima_rede_dia_pu": float(uma_linha_por_hora["tensao_maxima_rede_pu"].max()),
        "horas_com_violacao_barras_pv": horas_com_violacao,
        "energia_disponivel_kwh": float(energia_disponivel_por_agente.sum()),
        "energia_cortada_kwh": float(energia_cortada_por_agente.sum()),
        "curtailment_percentual_dia": 100.0
        * float(energia_cortada_por_agente.sum())
        / max(float(energia_disponivel_por_agente.sum()), 1e-9),
        "sigma_r_diario_por_energia": calcular_dispersao_sigma_r(razao_diaria_por_agente),
        "tensao_maxima_barras_pv_hora_pico_pu": float(linha_da_hora_de_pico["tensao_maxima_barras_pv_pu"]),
    }
    if "status" in dados_por_hora:
        resumo.update(
            {
                "horas_com_controle_ativo": int((uma_linha_por_hora["status"] != "sem_sobretensao").sum()),
                "horas_nao_convergidas": int((uma_linha_por_hora["status"] == "nao_convergiu").sum()),
                "iteracoes_totais_no_dia": int(uma_linha_por_hora["iteracoes"].sum()),
                "horas_com_consenso_satisfeito": int(uma_linha_por_hora["consenso_satisfeito"].sum()),
                "erro_consenso_global_hora_pico": float(linha_da_hora_de_pico["erro_de_consenso_global_final"]),
                "consenso_satisfeito_hora_pico": bool(linha_da_hora_de_pico["consenso_satisfeito"]),
                "iteracoes_hora_pico": int(linha_da_hora_de_pico["iteracoes"]),
                "status_hora_pico": linha_da_hora_de_pico["status"],
                "sigma_r_global_hora_pico": float(linha_da_hora_de_pico["sigma_r_global_hora"]),
                "sigma_r_por_particao_hora_pico": linha_da_hora_de_pico["sigma_r_por_particao_hora"],
            }
        )
    for barra, razao in zip(energia_disponivel_por_agente.index, razao_diaria_por_agente):
        resumo[f"curtailment_percentual_{barra}"] = 100.0 * razao if not np.isnan(razao) else float("nan")
    return resumo


# =============================================================================
# VALIDAÇÃO (§6)
# =============================================================================


def validar_resultados(dados_por_hora_todos, lambda_2_por_cenario, checagens_por_caso):
    """
    Checklist de §6 aplicado aos resultados. Retorna lista de (descrição, passou, detalhe).
    """
    validacoes = []
    tolerancia_de_potencia_kw = 1e-3

    dados_controlados = dados_por_hora_todos[dados_por_hora_todos["arquitetura"] != "sem_controle"]

    excesso_de_geracao = (
        dados_controlados["potencia_gerada_kw"] - dados_controlados["potencia_disponivel_kw"]
    ).max()
    validacoes.append(
        ("P_gerada <= P_disponivel em todo passo", excesso_de_geracao <= tolerancia_de_potencia_kw, f"maior excesso = {excesso_de_geracao:.2e} kW")
    )

    diferenca_energetica = (
        dados_controlados["potencia_disponivel_kw"]
        - dados_controlados["potencia_gerada_kw"]
        - dados_controlados["potencia_cortada_kw"]
    ).abs().max()
    validacoes.append(
        ("E_disponivel = E_gerada + E_cortada", diferenca_energetica <= tolerancia_de_potencia_kw, f"maior diferenca = {diferenca_energetica:.2e} kW")
    )

    tensoes_validas = np.isfinite(dados_por_hora_todos["tensao_maxima_rede_pu"]).all() and (
        dados_por_hora_todos["tensao_maxima_rede_pu"].max() < 2.0
    )
    validacoes.append(("Tensoes pu finitas e < 2 pu (sanidade de base)", bool(tensoes_validas), ""))

    validacoes.append(("lambda_2(C0) > 0", lambda_2_por_cenario["C0"] > 0, f"{lambda_2_por_cenario['C0']:.4f}"))
    validacoes.append(("lambda_2(C1) > 0", lambda_2_por_cenario["C1"] > 0, f"{lambda_2_por_cenario['C1']:.4f}"))
    validacoes.append(("lambda_2(C2) = 0", lambda_2_por_cenario["C2"] == 0.0, f"{lambda_2_por_cenario['C2']:.4f}"))

    houve_vazamento = any(checagem["correcao_fora_do_lider"] for checagem in checagens_por_caso.values())
    validacoes.append(("LF: correcao nao nula apenas no lider", not houve_vazamento, ""))

    # Mesmo perfil físico entre todos os casos: a potência disponível por hora e agente deve coincidir.
    potencia_disponivel_por_caso = dados_controlados.pivot_table(
        index=["hora", "barra"], columns=["arquitetura", "cenario"], values="potencia_disponivel_kw"
    )
    variacao_entre_casos = float((potencia_disponivel_por_caso.max(axis=1) - potencia_disponivel_por_caso.min(axis=1)).max())
    # Por que uma tolerância maior aqui: o SolveSnap é iterativo e parte do estado
    # elétrico anterior (a hora anterior, já com curtailment, que difere entre
    # cenários). A solução converge dentro da tolerância do OpenDSS (~1e-4 pu),
    # o que se reflete em alguns watts na potência medida. Diferença dessa ordem
    # é ruído numérico, não vazamento de estado entre cenários.
    tolerancia_numerica_do_solver_kw = 1e-4 * max(POTENCIA_NOMINAL_KVA_ORDEM_DE_REFERENCIA)
    validacoes.append(
        ("Mesma P_disponivel em todos os casos (sem vazamento de estado)", variacao_entre_casos <= tolerancia_numerica_do_solver_kw, f"maior variacao = {variacao_entre_casos:.2e} kW (tol. {tolerancia_numerica_do_solver_kw:.3f} kW)")
    )

    nao_convergidos = dados_controlados[dados_controlados["status"] == "nao_convergiu"][["arquitetura", "cenario", "hora"]].drop_duplicates()
    validacoes.append(
        ("Casos em k_max marcados como nao_convergiu (informativo)", True, f"{len(nao_convergidos)} horas-caso marcadas")
    )
    return validacoes


# =============================================================================
# RESULTADOS — figuras (§5.5)
# Paleta: slots categóricos da paleta de referência (validada para daltonismo
# na ordem adjacente). Cor segue a ENTIDADE: LF sempre azul, Leaderless sempre
# laranja, "sem controle" sempre cinza.
# =============================================================================

COR_LEADER_FOLLOWER = "#2a78d6"
COR_LEADERLESS = "#eb6834"
COR_SEM_CONTROLE = "#8a8984"
COR_DO_TEXTO_PRINCIPAL = "#0b0b0b"
COR_DO_TEXTO_SECUNDARIO = "#52514e"
COR_DA_GRADE = "#e4e3df"
CORES_POR_ARQUITETURA = {ARQUITETURA_LEADER_FOLLOWER: COR_LEADER_FOLLOWER, ARQUITETURA_LEADERLESS: COR_LEADERLESS}
NOMES_LEGIVEIS_DAS_ARQUITETURAS = {ARQUITETURA_LEADER_FOLLOWER: "Leader-Follower", ARQUITETURA_LEADERLESS: "Leaderless"}
# Cores categóricas em ordem fixa para os cenários (slots 1..7 da paleta de referência)
CORES_POR_CENARIO = {
    "C0": "#2a78d6",
    "C1": "#eb6834",
    "C2": "#1baf7a",
    "C3_lider_curta": "#eda100",
    "C3_lider_longa": "#e87ba4",
    "C3_naolider_curta": "#008300",
    "C3_naolider_longa": "#4a3aa7",
}
# Falhas longas tracejadas: em LF, C2 e C3_lider_longa produzem a MESMA curva na
# hora de pico (ambos isolam o líder a hora toda); o tracejado evita que uma esconda a outra.
ESTILO_DE_LINHA_POR_CENARIO = {
    "C0": "-", "C1": "-", "C2": "-", "C3_lider_curta": "-", "C3_lider_longa": "--",
    "C3_naolider_curta": "-", "C3_naolider_longa": "--",
}
MARCADORES_POR_CENARIO = {
    "C0": "o", "C1": "s", "C2": "D", "C3_lider_curta": "^", "C3_lider_longa": "v",
    "C3_naolider_curta": "<", "C3_naolider_longa": ">",
}


def aplicar_estilo_das_figuras():
    """Estilo comum: linhas finas, grade discreta, texto em tinta neutra."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": COR_DA_GRADE,
            "axes.labelcolor": COR_DO_TEXTO_SECUNDARIO,
            "axes.titlecolor": COR_DO_TEXTO_PRINCIPAL,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.color": COR_DO_TEXTO_SECUNDARIO,
            "ytick.color": COR_DO_TEXTO_SECUNDARIO,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.grid": True,
            "grid.color": COR_DA_GRADE,
            "grid.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "lines.linewidth": 1.5,
            "legend.fontsize": 8,
            "legend.frameon": False,
            "font.size": 9,
        }
    )


def desenhar_linha_do_limite_de_tensao(eixo):
    """Linha horizontal de V_lim = 1,05 pu com rótulo."""
    eixo.axhline(TENSAO_LIMITE_PU, color=COR_DO_TEXTO_SECUNDARIO, linewidth=1.0, linestyle=":")
    eixo.annotate(
        "V_lim = 1,05 pu", xy=(1.0, TENSAO_LIMITE_PU), xycoords=("axes fraction", "data"),
        xytext=(-4, 3), textcoords="offset points", ha="right", fontsize=7, color=COR_DO_TEXTO_SECUNDARIO,
    )


def salvar_figura(figura, pasta_de_figuras, nome_do_arquivo):
    """Salva a figura em PNG (dpi 150) e fecha."""
    figura.savefig(pasta_de_figuras / nome_do_arquivo, dpi=150, bbox_inches="tight")
    plt.close(figura)


def figura_01_sistema_eletrico(pasta_de_figuras, agentes_na_ordem_do_grafo):
    """Diagrama do IEEE 34 barras com os PVs marcados (coordenadas do BusXY.csv)."""
    coordenadas = {}
    for linha in (PASTA_DO_ALIMENTADOR / "IEEE34_BusXY.csv").read_text().splitlines():
        partes = linha.strip().split(",")
        if len(partes) == 3:
            coordenadas[partes[0].lower()] = (float(partes[1]), float(partes[2]))

    construir_circuito_com_pvs(agentes_na_ordem_do_grafo)
    ligacoes = []
    for linha_eletrica in altdss.Line:
        ligacoes.append((linha_eletrica.Bus1.split(".")[0], linha_eletrica.Bus2.split(".")[0]))
    for transformador in altdss.Transformer:
        barras_do_transformador = [barra.split(".")[0] for barra in transformador.Buses]
        ligacoes.append((barras_do_transformador[0], barras_do_transformador[1]))

    figura, eixo = plt.subplots(figsize=(10, 4.2))
    for barra_a, barra_b in ligacoes:
        if barra_a in coordenadas and barra_b in coordenadas:
            eixo.plot(
                [coordenadas[barra_a][0], coordenadas[barra_b][0]],
                [coordenadas[barra_a][1], coordenadas[barra_b][1]],
                color=COR_SEM_CONTROLE, linewidth=1.2, zorder=1,
            )
    for barra, (x, y) in coordenadas.items():
        eixo.scatter(x, y, s=10, color=COR_SEM_CONTROLE, zorder=2)
        eixo.annotate(barra, (x, y), xytext=(2, -8), textcoords="offset points", fontsize=6, color=COR_DO_TEXTO_SECUNDARIO)
    # Deslocamento (em pontos) do rótulo de cada PV, escolhido à mão para não sobrepor.
    deslocamento_do_rotulo_por_barra = {
        "850": (-95, 14), "816": (-45, 30), "824": (8, 14), "828": (-110, -4), "830": (8, 10), "832": (8, 8),
    }
    for indice, agente in enumerate(agentes_na_ordem_do_grafo):
        x, y = coordenadas[agente.barra]
        eh_lider = indice == INDICE_DO_LIDER_NO_GRAFO
        eixo.scatter(
            x, y, s=140 if eh_lider else 90, marker="*" if eh_lider else "s",
            color=COR_LEADERLESS if eh_lider else COR_LEADER_FOLLOWER, edgecolor="white", linewidth=1.5, zorder=3,
        )
        rotulo = f"{agente.nome_do_pvsystem} ({agente.potencia_nominal_kva:.0f} kVA)" + (" — líder" if eh_lider else "")
        eixo.annotate(rotulo, (x, y), xytext=deslocamento_do_rotulo_por_barra.get(agente.barra, (4, 7)),
                      textcoords="offset points", fontsize=7, color=COR_DO_TEXTO_PRINCIPAL)
    eixo.set_title("Figura 01 — IEEE 34 barras com os 6 PVSystems (estrela = líder por S_i)", loc="left")
    eixo.set_xticks([])
    eixo.set_yticks([])
    eixo.grid(False)
    for lado in eixo.spines.values():
        lado.set_visible(False)
    salvar_figura(figura, pasta_de_figuras, "01_sistema_eletrico.png")


def figura_02_grafo_de_comunicacao(pasta_de_figuras, agentes_na_ordem_do_grafo, cenarios, hora_de_pico):
    """Grafo de comunicação em C0, C1, C2 e C3 (m = líder / m != líder) durante a falha."""
    # Desenho simples em "linha dobrada" para que o atalho (2,5) fique visível.
    posicoes_no_desenho = {0: (0, 0), 1: (1, 0), 2: (2, 0.7), 3: (3, 0), 4: (2, -0.7), 5: (3.2, -1.1)}
    cenarios_para_desenhar = [c for c in cenarios if c.nome in ("C0", "C1", "C2", "C3_lider_longa", "C3_naolider_longa")]

    figura, eixos = plt.subplots(1, len(cenarios_para_desenhar), figsize=(3.2 * len(cenarios_para_desenhar), 3.0))
    for eixo, cenario in zip(eixos, cenarios_para_desenhar):
        grafo = GrafoDeComunicacao(cenario, hora_de_pico)
        matriz = grafo.matriz_de_adjacencia_na_iteracao(hora_de_pico, 0)
        for agente_a, agente_b in ENLACES_DO_GRAFO_NOMINAL:
            enlace_ativo = matriz[agente_a, agente_b] > 0
            eixo.plot(
                [posicoes_no_desenho[agente_a][0], posicoes_no_desenho[agente_b][0]],
                [posicoes_no_desenho[agente_a][1], posicoes_no_desenho[agente_b][1]],
                color=COR_DO_TEXTO_SECUNDARIO if enlace_ativo else "#d63a3a",
                linestyle="-" if enlace_ativo else "--", linewidth=1.5 if enlace_ativo else 1.0, zorder=1,
            )
        for indice, agente in enumerate(agentes_na_ordem_do_grafo):
            x, y = posicoes_no_desenho[indice]
            isolado = cenario.indice_do_agente_isolado == indice
            cor = COR_LEADERLESS if indice == INDICE_DO_LIDER_NO_GRAFO else COR_LEADER_FOLLOWER
            eixo.scatter(x, y, s=420, color="white" if isolado else cor, edgecolor=cor, linewidth=2, zorder=2)
            eixo.annotate(str(indice + 1), (x, y), ha="center", va="center", fontsize=9,
                          color=cor if isolado else "white", zorder=3, fontweight="bold")
            eixo.annotate(agente.barra, (x, y), xytext=(0, -17), textcoords="offset points", ha="center", fontsize=7,
                          color=COR_DO_TEXTO_SECUNDARIO)
        lambda_2 = calcular_conectividade_algebrica(matriz)
        eixo.set_title(f"{cenario.nome}\nλ₂ = {lambda_2:.3f}", fontsize=9)
        eixo.set_xlim(-0.5, 3.8)
        eixo.set_ylim(-1.6, 1.2)
        eixo.set_xticks([])
        eixo.set_yticks([])
        eixo.grid(False)
        for lado in eixo.spines.values():
            lado.set_visible(False)
    figura.suptitle("Figura 02 — Grafo de comunicação (nó 1 = líder; tracejado = enlace perdido; nó vazado = agente isolado)",
                    x=0.01, y=1.06, ha="left", fontsize=10)
    salvar_figura(figura, pasta_de_figuras, "02_grafo_comunicacao.png")


def figura_03_convergencia(pasta_de_figuras, dados_por_iteracao, hora_de_pico):
    """e_c(k) na hora de pico, um painel por arquitetura, uma linha por cenário."""
    figura, eixos = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for eixo, arquitetura in zip(eixos, ARQUITETURAS_DO_EXPERIMENTO):
        dados = dados_por_iteracao[(dados_por_iteracao["arquitetura"] == arquitetura) & (dados_por_iteracao["hora"] == hora_de_pico)]
        for nome_do_cenario, cor in CORES_POR_CENARIO.items():
            serie = dados[dados["cenario"] == nome_do_cenario]
            if len(serie) > 0:
                eixo.plot(serie["iteracao_k"], serie["erro_de_consenso_global"], color=cor,
                          linestyle=ESTILO_DE_LINHA_POR_CENARIO[nome_do_cenario], label=nome_do_cenario)
        eixo.set_title(f"{NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura]} — hora {hora_de_pico}", loc="left")
        eixo.set_xlabel("iteração de consenso k")
        eixo.set_xscale("symlog", linthresh=10)
    eixos[0].set_ylabel("erro de consenso e_c(k) sobre rho")
    eixos[1].legend(loc="upper right")
    figura.suptitle("Figura 03 — Convergência do consenso na hora de maior sobretensão", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "03_convergencia.png")


def figura_04_tensoes(pasta_de_figuras, dados_por_hora_todos):
    """Vmax das barras com PV ao longo do dia, por arquitetura, cenários sobrepostos."""
    sem_controle = dados_por_hora_todos[dados_por_hora_todos["arquitetura"] == "sem_controle"].drop_duplicates("hora")
    figura, eixos = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for eixo, arquitetura in zip(eixos, ARQUITETURAS_DO_EXPERIMENTO):
        eixo.plot(sem_controle["hora"], sem_controle["tensao_maxima_barras_pv_pu"], color=COR_SEM_CONTROLE,
                  linestyle="--", label="sem controle")
        dados = dados_por_hora_todos[dados_por_hora_todos["arquitetura"] == arquitetura]
        for nome_do_cenario, cor in CORES_POR_CENARIO.items():
            serie = dados[dados["cenario"] == nome_do_cenario].drop_duplicates("hora")
            eixo.plot(serie["hora"], serie["tensao_maxima_barras_pv_pu"], color=cor,
                      linestyle=ESTILO_DE_LINHA_POR_CENARIO[nome_do_cenario], label=nome_do_cenario)
        desenhar_linha_do_limite_de_tensao(eixo)
        eixo.set_title(NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura], loc="left")
        eixo.set_xlabel("hora do dia")
        eixo.set_xticks(range(0, 24, 3))
    eixos[0].set_ylabel("Vmax nas barras com PV (pu)")
    eixos[1].legend(loc="upper left", ncol=2)
    figura.suptitle("Figura 04 — Tensão máxima nas barras com PV após o controle", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "04_tensoes.png")


def figura_05_curtailment(pasta_de_figuras, tabela_de_resumo, agentes_na_ordem_do_grafo):
    """Curtailment diário (%) por agente, por cenário, um painel por arquitetura."""
    cenarios_mostrados = ["C0", "C1", "C2", "C3_lider_longa", "C3_naolider_longa"]
    barras = [agente.barra for agente in agentes_na_ordem_do_grafo]
    largura_da_barra = 0.8 / len(cenarios_mostrados)

    figura, eixos = plt.subplots(1, 2, figsize=(12, 3.8), sharey=True)
    for eixo, arquitetura in zip(eixos, ARQUITETURAS_DO_EXPERIMENTO):
        for posicao_do_cenario, nome_do_cenario in enumerate(cenarios_mostrados):
            linha = tabela_de_resumo[(tabela_de_resumo["arquitetura"] == arquitetura) & (tabela_de_resumo["cenario"] == nome_do_cenario)].iloc[0]
            valores = [linha[f"curtailment_percentual_{barra}"] for barra in barras]
            deslocamento = (posicao_do_cenario - (len(cenarios_mostrados) - 1) / 2) * largura_da_barra
            eixo.bar(np.arange(len(barras)) + deslocamento, valores, width=largura_da_barra * 0.9,
                     color=CORES_POR_CENARIO[nome_do_cenario], label=nome_do_cenario, edgecolor="white", linewidth=0.5)
        rotulos = [f"{barra}\n(pos {indice + 1}{', líder' if indice == 0 else ''})" for indice, barra in enumerate(barras)]
        eixo.set_xticks(range(len(barras)))
        eixo.set_xticklabels(rotulos)
        eixo.set_title(NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura], loc="left")
        eixo.grid(axis="x", visible=False)
    eixos[0].set_ylabel("energia cortada / disponível no dia (%)")
    eixos[1].legend(loc="upper right")
    figura.suptitle("Figura 05 — Distribuição do curtailment diário entre os agentes (r_i)", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "05_curtailment.png")


def figura_06_margem_H3(pasta_de_figuras, tabela_de_resumo):
    """H3: sigma_r (diário) x Vmax (dia), cor = arquitetura, marcador = cenário."""
    figura, eixo = plt.subplots(figsize=(7.5, 4.8))
    for _, linha in tabela_de_resumo.iterrows():
        if linha["arquitetura"] == "sem_controle":
            eixo.scatter(0, linha["tensao_maxima_barras_pv_dia_pu"], color=COR_SEM_CONTROLE, marker="x", s=70, label="sem controle")
            continue
        eixo.scatter(
            linha["sigma_r_diario_por_energia"], linha["tensao_maxima_barras_pv_dia_pu"],
            color=CORES_POR_ARQUITETURA[linha["arquitetura"]],
            marker=MARCADORES_POR_CENARIO.get(linha["cenario"], "P"),  # "P": cenarios probabilisticos (C0_perda_*)
            s=70, edgecolor="white", linewidth=1.5, zorder=3,
        )
    desenhar_linha_do_limite_de_tensao(eixo)
    # Legenda em duas partes: cor = arquitetura, forma = cenário (identidade nunca só pela cor)
    for arquitetura in ARQUITETURAS_DO_EXPERIMENTO:
        eixo.scatter([], [], color=CORES_POR_ARQUITETURA[arquitetura], marker="o", s=60, label=NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura])
    for nome_do_cenario, marcador in MARCADORES_POR_CENARIO.items():
        eixo.scatter([], [], color=COR_DO_TEXTO_SECUNDARIO, marker=marcador, s=50, label=nome_do_cenario)
    cenarios_probabilisticos = sorted(
        set(tabela_de_resumo["cenario"]) - set(MARCADORES_POR_CENARIO) - {"sem_controle"}
    )
    if cenarios_probabilisticos:
        eixo.scatter([], [], color=COR_DO_TEXTO_SECUNDARIO, marker="P", s=50, label="C0_perda_* (canal probabilístico)")
    eixo.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    eixo.set_xlabel("σ_r diário (dispersão da razão de curtailment entre agentes)")
    eixo.set_ylabel("Vmax do dia nas barras com PV (pu)")
    eixo.set_title("Figura 06 — Margem de H3: desigualdade de curtailment vs. tensão", loc="left")
    salvar_figura(figura, pasta_de_figuras, "06_margem_H3.png")


def figura_07_H5_particionamento(pasta_de_figuras, dados_por_hora_todos):
    """H5: em C2, Vmax(t) em cada partição ({líder} e {demais}), LF vs Leaderless."""
    figura, eixos = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    titulos_das_particoes = {True: "Partição A: {líder} (posição 1)", False: "Partição B: {posições 2–6}"}
    sem_controle = dados_por_hora_todos[dados_por_hora_todos["arquitetura"] == "sem_controle"]
    for eixo, particao_do_lider in zip(eixos, [True, False]):
        for arquitetura in ARQUITETURAS_DO_EXPERIMENTO:
            dados = dados_por_hora_todos[(dados_por_hora_todos["arquitetura"] == arquitetura) & (dados_por_hora_todos["cenario"] == "C2")]
            dados = dados[dados["eh_lider"] == particao_do_lider]
            serie = dados.groupby("hora")["tensao_final_pu"].max()
            eixo.plot(serie.index, serie.values, color=CORES_POR_ARQUITETURA[arquitetura], label=NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura])
        barras_da_particao = dados["barra"].unique()
        serie_sem_controle = sem_controle[sem_controle["barra"].isin(barras_da_particao)].groupby("hora")["tensao_final_pu"].max()
        eixo.plot(serie_sem_controle.index, serie_sem_controle.values, color=COR_SEM_CONTROLE, linestyle="--", label="sem controle")
        desenhar_linha_do_limite_de_tensao(eixo)
        eixo.set_title(titulos_das_particoes[particao_do_lider], loc="left")
        eixo.set_xlabel("hora do dia")
        eixo.set_xticks(range(0, 24, 3))
    eixos[0].set_ylabel("Vmax na partição (pu)")
    eixos[1].legend(loc="upper left")
    figura.suptitle("Figura 07 — H5: cenário C2 (enlace (1,2) perdido), tensão por partição", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "07_H5_particionamento.png")


def figura_08_H5a_falha_do_lider(pasta_de_figuras, tabela_de_resumo):
    """H5a: m = líder vs m != líder (curta/longa), Vmax e sigma_r na hora de pico."""
    cenarios_c3 = ["C3_lider_curta", "C3_lider_longa", "C3_naolider_curta", "C3_naolider_longa"]
    metricas = [
        ("tensao_maxima_barras_pv_hora_pico_pu", "Vmax nas barras com PV (pu)"),
        ("sigma_r_global_hora_pico", "σ_r global na hora de pico"),
        ("iteracoes_hora_pico", "iterações na hora de pico"),
    ]
    figura, eixos = plt.subplots(1, len(metricas), figsize=(14, 3.8))
    largura_da_barra = 0.38
    for eixo, (coluna, rotulo) in zip(eixos, metricas):
        for posicao_arquitetura, arquitetura in enumerate(ARQUITETURAS_DO_EXPERIMENTO):
            valores = []
            for nome_do_cenario in cenarios_c3:
                linha = tabela_de_resumo[(tabela_de_resumo["arquitetura"] == arquitetura) & (tabela_de_resumo["cenario"] == nome_do_cenario)].iloc[0]
                valores.append(linha[coluna])
            deslocamento = (posicao_arquitetura - 0.5) * largura_da_barra
            posicoes_x = np.arange(len(cenarios_c3)) + deslocamento
            if coluna == "tensao_maxima_barras_pv_hora_pico_pu":
                # Tensão em pontos, não barras: o eixo não começa em zero, e barras
                # com base truncada exagerariam visualmente as diferenças.
                eixo.scatter(posicoes_x, valores, s=70, color=CORES_POR_ARQUITETURA[arquitetura],
                             edgecolor="white", linewidth=1.5, zorder=3, label=NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura])
            else:
                eixo.bar(posicoes_x, valores, width=largura_da_barra * 0.92,
                         color=CORES_POR_ARQUITETURA[arquitetura], label=NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura])
        if coluna == "tensao_maxima_barras_pv_hora_pico_pu":
            desenhar_linha_do_limite_de_tensao(eixo)
            todos = tabela_de_resumo[coluna].dropna()
            eixo.set_ylim(min(todos.min(), TENSAO_LIMITE_PU) - 0.005, todos.max() + 0.005)
        eixo.set_xticks(range(len(cenarios_c3)))
        eixo.set_xticklabels([nome.replace("C3_", "").replace("_", "\n") for nome in cenarios_c3])
        eixo.set_title(rotulo, loc="left", fontsize=9)
        eixo.grid(axis="x", visible=False)
    eixos[0].legend(loc="upper right")
    figura.suptitle("Figura 08 — H5a: falha do líder vs. falha de não-líder (C3, hora de pico)", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "08_H5a_falha_lider.png")


# =============================================================================
# RESULTADOS — tabelas extras (inspiradas no código de referência do grupo)
# =============================================================================


def montar_violacoes_por_hora(tabela_de_todas_as_barras):
    """
    Uma linha por (caso, hora): quantas barras/fases violam cada limite e
    QUAIS barras (lista separada por espaço), como no código de referência.
    """
    registros = []
    for (arquitetura, cenario, hora), barras_da_hora in tabela_de_todas_as_barras.groupby(
        ["arquitetura", "cenario", "hora"], sort=False
    ):
        barras_com_sobretensao = barras_da_hora[barras_da_hora["barra_com_sobretensao"]]["barra"].tolist()
        barras_com_subtensao = barras_da_hora[barras_da_hora["barra_com_subtensao"]]["barra"].tolist()
        registros.append(
            {
                "arquitetura": arquitetura,
                "cenario": cenario,
                "hora": hora,
                "numero_de_barras_com_sobretensao": len(barras_com_sobretensao),
                "numero_de_barras_com_subtensao": len(barras_com_subtensao),
                "numero_de_fases_com_sobretensao": int(barras_da_hora["fases_com_sobretensao"].sum()),
                "numero_de_fases_com_subtensao": int(barras_da_hora["fases_com_subtensao"].sum()),
                "tensao_maxima_rede_pu": float(barras_da_hora["tensao_maxima_pu"].max()),
                "tensao_minima_rede_pu": float(barras_da_hora["tensao_minima_pu"].min()),
                "barras_com_sobretensao": " ".join(barras_com_sobretensao),
                "barras_com_subtensao": " ".join(barras_com_subtensao),
            }
        )
    return pd.DataFrame(registros)


def montar_curtailment_por_pv(dados_por_hora_todos):
    """Energia disponível, gerada e cortada (kWh e %) por PV em cada caso."""
    registros = []
    for (arquitetura, cenario, barra), dados in dados_por_hora_todos.groupby(["arquitetura", "cenario", "barra"], sort=False):
        energia_disponivel_kwh = float(dados["potencia_disponivel_kw"].sum()) * DURACAO_DO_PASSO_HORAS
        energia_gerada_kwh = float(dados["potencia_gerada_kw"].sum()) * DURACAO_DO_PASSO_HORAS
        energia_cortada_kwh = float(dados["potencia_cortada_kw"].sum()) * DURACAO_DO_PASSO_HORAS
        registros.append(
            {
                "arquitetura": arquitetura,
                "cenario": cenario,
                "agente": dados["agente"].iloc[0],
                "barra": barra,
                "energia_disponivel_kwh": energia_disponivel_kwh,
                "energia_gerada_kwh": energia_gerada_kwh,
                "energia_cortada_kwh": energia_cortada_kwh,
                "curtailment_percentual": 100.0 * energia_cortada_kwh / energia_disponivel_kwh
                if energia_disponivel_kwh > 0 else 0.0,
            }
        )
    return pd.DataFrame(registros)


def montar_resumo_da_comunicacao(tabela_de_mensagens, tabela_de_comunicacao, agrupar_por_hora):
    """
    Totais de mensagens (enviadas, entregues, perdidas) por caso ou por (caso, hora),
    iterações sob falha e maior idade de informação observada.
    """
    chaves = ["arquitetura", "cenario", "hora"] if agrupar_por_hora else ["arquitetura", "cenario"]
    colunas_de_idade = [coluna for coluna in tabela_de_comunicacao.columns if coluna.startswith("idade_da_info_")]
    registros = []
    for chave, mensagens in tabela_de_mensagens.groupby(chaves, sort=False):
        filtro = np.ones(len(tabela_de_comunicacao), dtype=bool)
        for nome_da_coluna, valor in zip(chaves, chave):
            filtro &= (tabela_de_comunicacao[nome_da_coluna] == valor).to_numpy()
        iteracoes = tabela_de_comunicacao[filtro]
        mensagens_perdidas = int((mensagens["situacao"] == "PERDIDA").sum())
        registro = dict(zip(chaves, chave))
        registro.update(
            {
                "iteracoes_de_comunicacao": len(iteracoes),
                "iteracoes_com_algum_enlace_fora": int((iteracoes["enlaces_ativos"] < len(ENLACES_DO_GRAFO_NOMINAL)).sum()),
                "mensagens_tentadas": len(mensagens),
                "mensagens_entregues": int((mensagens["situacao"] == "ENTREGUE").sum()),
                "mensagens_perdidas": mensagens_perdidas,
                "taxa_de_perda_percentual": 100.0 * mensagens_perdidas / max(len(mensagens), 1),
                "maior_idade_da_informacao_iteracoes": int(iteracoes[colunas_de_idade].to_numpy().max()) if len(iteracoes) else 0,
                "minimo_lambda_2": float(iteracoes["lambda_2"].min()) if len(iteracoes) else float("nan"),
            }
        )
        registros.append(registro)
    return pd.DataFrame(registros)


def salvar_matrizes_hora_por_barra(tabela_de_todas_as_barras, dados_por_hora_todos, pasta_de_matrizes):
    """
    Uma pasta por caso com tabelas "fáceis de ler" (linhas = hora, colunas = barra),
    no formato matriz do código de referência:
      tensao_hora_x_barra.csv           tensão máxima de cada barra
      sobretensao_hora_x_barra.csv      1 = barra violou V_lim na hora, 0 = não
      sobretensao_valor_hora_x_barra.csv tensão onde violou, vazio onde não
      subtensao_hora_x_barra.csv        1 = barra abaixo de V_min
      potencias_por_pv.csv              P disponível, P gerada e rho por PV (formato largo)
      tensoes_barras_pv.csv             tensão das 6 barras com PV por hora
    """
    for (arquitetura, cenario), barras_do_caso in tabela_de_todas_as_barras.groupby(["arquitetura", "cenario"], sort=False):
        pasta_do_caso = pasta_de_matrizes / f"{arquitetura}__{cenario}"
        pasta_do_caso.mkdir(parents=True, exist_ok=True)

        tensao = barras_do_caso.pivot(index="hora", columns="barra", values="tensao_maxima_pu")
        tensao.to_csv(pasta_do_caso / "tensao_hora_x_barra.csv")

        sobretensao = barras_do_caso.pivot(index="hora", columns="barra", values="barra_com_sobretensao").astype(int)
        sobretensao.to_csv(pasta_do_caso / "sobretensao_hora_x_barra.csv")
        tensao.where(sobretensao == 1).to_csv(pasta_do_caso / "sobretensao_valor_hora_x_barra.csv")

        subtensao = barras_do_caso.pivot(index="hora", columns="barra", values="barra_com_subtensao").astype(int)
        subtensao.to_csv(pasta_do_caso / "subtensao_hora_x_barra.csv")

        dados_do_caso = dados_por_hora_todos[
            (dados_por_hora_todos["arquitetura"] == arquitetura) & (dados_por_hora_todos["cenario"] == cenario)
        ]
        tabela_larga = pd.DataFrame({"hora": sorted(dados_do_caso["hora"].unique())}).set_index("hora")
        for barra in dados_do_caso["barra"].unique():
            dados_da_barra = dados_do_caso[dados_do_caso["barra"] == barra].set_index("hora")
            tabela_larga[f"P_disponivel_kw_{barra}"] = dados_da_barra["potencia_disponivel_kw"]
            tabela_larga[f"P_gerada_kw_{barra}"] = dados_da_barra["potencia_gerada_kw"]
            tabela_larga[f"rho_{barra}"] = dados_da_barra["fracao_de_curtailment_rho"]
        tabela_larga.to_csv(pasta_do_caso / "potencias_por_pv.csv")

        dados_do_caso.pivot(index="hora", columns="barra", values="tensao_final_pu").to_csv(
            pasta_do_caso / "tensoes_barras_pv.csv"
        )


# =============================================================================
# RESULTADOS — figuras extras (00, 09–17)
# =============================================================================

# Cor por agente (posição 1..6 no grafo), slots categóricos 1..6 em ordem fixa.
CORES_POR_POSICAO_DO_AGENTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]


def rotulo_do_caso(arquitetura, cenario):
    """Texto curto para título de painel: 'Leader-Follower — C2'."""
    return f"{NOMES_LEGIVEIS_DAS_ARQUITETURAS.get(arquitetura, 'Sem controle')} — {cenario}"


def selecionar_caso(tabela, arquitetura, cenario):
    """Linhas da tabela que pertencem a um caso (arquitetura x cenário)."""
    return tabela[(tabela["arquitetura"] == arquitetura) & (tabela["cenario"] == cenario)]


def figura_00_curvas_de_entrada(pasta_de_figuras, curvas):
    """Curvas diárias usadas: carga (pu) e irradiância (pu). Dois painéis, sem eixo duplo."""
    figura, eixos = plt.subplots(1, 2, figsize=(11, 3.4))
    eixos[0].plot(curvas["hora"], curvas["multiplicador_de_carga"], color=COR_LEADER_FOLLOWER, marker="o", markersize=4)
    eixos[0].set_title(f"Carga (pu) — aplicada × LoadMult base {MULTIPLICADOR_BASE_DE_CARGA}", loc="left")
    eixos[1].plot(curvas["hora"], curvas["irradiancia_pu"], color=COR_LEADERLESS, marker="o", markersize=4)
    eixos[1].set_title("Irradiância (pu) = curva PV / pico", loc="left")
    for eixo in eixos:
        eixo.set_xlabel("hora do dia")
        eixo.set_xticks(range(0, 24, 2))
        eixo.set_ylim(0, 1.05)
    figura.suptitle("Figura 00 — Curvas diárias de entrada", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "00_curvas_de_entrada.png")


def figura_09_potencias_pv(pasta_de_figuras, dados_por_hora_todos, agentes_na_ordem_do_grafo):
    """Potência disponível (cinza tracejado) x gerada (cor) por PV, em 4 casos-chave."""
    casos = [
        (ARQUITETURA_LEADER_FOLLOWER, "C0"), (ARQUITETURA_LEADER_FOLLOWER, "C2"),
        (ARQUITETURA_LEADERLESS, "C0"), (ARQUITETURA_LEADERLESS, "C2"),
    ]
    figura, eixos = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True)
    for eixo, (arquitetura, cenario) in zip(eixos.flat, casos):
        dados = selecionar_caso(dados_por_hora_todos, arquitetura, cenario)
        for indice, agente in enumerate(agentes_na_ordem_do_grafo):
            dados_do_pv = dados[dados["barra"] == agente.barra]
            eixo.plot(dados_do_pv["hora"], dados_do_pv["potencia_disponivel_kw"], color=COR_SEM_CONTROLE,
                      linestyle="--", linewidth=1.0)
            eixo.plot(dados_do_pv["hora"], dados_do_pv["potencia_gerada_kw"], color=CORES_POR_POSICAO_DO_AGENTE[indice],
                      label=f"{indice + 1}: {agente.barra}")
        eixo.set_title(rotulo_do_caso(arquitetura, cenario), loc="left")
        eixo.set_xticks(range(0, 24, 3))
    for eixo in eixos[1]:
        eixo.set_xlabel("hora do dia")
    for eixo in eixos[:, 0]:
        eixo.set_ylabel("potência (kW)")
    eixos[0, 1].plot([], [], color=COR_SEM_CONTROLE, linestyle="--", label="disponível")
    eixos[0, 1].legend(loc="upper right", ncol=2)
    figura.suptitle("Figura 09 — Potência disponível (tracejado) × gerada por PV", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "09_potencias_pv.png")


def figura_10_rho_por_hora(pasta_de_figuras, dados_por_hora_todos, agentes_na_ordem_do_grafo):
    """rho_i final de cada hora, por agente: 2 arquiteturas x 3 cenários."""
    cenarios_mostrados = ["C0", "C2", "C3_lider_longa"]
    figura, eixos = plt.subplots(2, 3, figsize=(14, 6.5), sharex=True, sharey=True)
    for linha, arquitetura in enumerate(ARQUITETURAS_DO_EXPERIMENTO):
        for coluna, cenario in enumerate(cenarios_mostrados):
            eixo = eixos[linha, coluna]
            dados = selecionar_caso(dados_por_hora_todos, arquitetura, cenario)
            for indice, agente in enumerate(agentes_na_ordem_do_grafo):
                dados_do_pv = dados[dados["barra"] == agente.barra]
                eixo.plot(dados_do_pv["hora"], dados_do_pv["fracao_de_curtailment_rho"],
                          color=CORES_POR_POSICAO_DO_AGENTE[indice], label=f"{indice + 1}: {agente.barra}")
            eixo.set_title(rotulo_do_caso(arquitetura, cenario), loc="left", fontsize=9)
            eixo.set_ylim(-0.03, 1.03)
            eixo.set_xticks(range(0, 24, 3))
    for eixo in eixos[1]:
        eixo.set_xlabel("hora do dia")
    for eixo in eixos[:, 0]:
        eixo.set_ylabel("rho_i (fração de curtailment)")
    eixos[0, 2].legend(loc="upper right")
    figura.suptitle("Figura 10 — Fração de curtailment rho_i ao fim de cada hora", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "10_rho_por_hora.png")


def figura_11_tensoes_individuais_pvs(pasta_de_figuras, dados_por_hora_todos, agentes_na_ordem_do_grafo):
    """Tensão de cada barra com PV ao longo do dia em 4 casos (como no código de referência)."""
    casos = [
        ("sem_controle", "sem_controle"), (ARQUITETURA_LEADER_FOLLOWER, "C0"),
        (ARQUITETURA_LEADER_FOLLOWER, "C2"), (ARQUITETURA_LEADERLESS, "C2"),
    ]
    figura, eixos = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True)
    for eixo, (arquitetura, cenario) in zip(eixos.flat, casos):
        dados = selecionar_caso(dados_por_hora_todos, arquitetura, cenario)
        for indice, agente in enumerate(agentes_na_ordem_do_grafo):
            dados_do_pv = dados[dados["barra"] == agente.barra]
            eixo.plot(dados_do_pv["hora"], dados_do_pv["tensao_final_pu"], color=CORES_POR_POSICAO_DO_AGENTE[indice],
                      label=f"{indice + 1}: {agente.barra}")
        desenhar_linha_do_limite_de_tensao(eixo)
        eixo.set_title(rotulo_do_caso(arquitetura, cenario) if arquitetura != "sem_controle" else "Sem controle",
                       loc="left")
        eixo.set_xticks(range(0, 24, 3))
    for eixo in eixos[1]:
        eixo.set_xlabel("hora do dia")
    for eixo in eixos[:, 0]:
        eixo.set_ylabel("tensão na barra do PV (pu)")
    eixos[0, 0].legend(loc="lower left", ncol=2)
    figura.suptitle("Figura 11 — Tensão individual de cada barra com PV", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "11_tensoes_individuais_pvs.png")


def figura_12_violacoes_por_hora(pasta_de_figuras, violacoes_por_hora):
    """Número de barras da rede com sobretensão por hora, por arquitetura e cenário."""
    sem_controle = selecionar_caso(violacoes_por_hora, "sem_controle", "sem_controle")
    figura, eixos = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for eixo, arquitetura in zip(eixos, ARQUITETURAS_DO_EXPERIMENTO):
        eixo.plot(sem_controle["hora"], sem_controle["numero_de_barras_com_sobretensao"], color=COR_SEM_CONTROLE,
                  linestyle="--", label="sem controle")
        for nome_do_cenario, cor in CORES_POR_CENARIO.items():
            dados = selecionar_caso(violacoes_por_hora, arquitetura, nome_do_cenario)
            eixo.plot(dados["hora"], dados["numero_de_barras_com_sobretensao"], color=cor,
                      linestyle=ESTILO_DE_LINHA_POR_CENARIO[nome_do_cenario], label=nome_do_cenario)
        eixo.set_title(NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura], loc="left")
        eixo.set_xlabel("hora do dia")
        eixo.set_xticks(range(0, 24, 3))
    eixos[0].set_ylabel(f"nº de barras com V > {TENSAO_LIMITE_PU} pu")
    # Legenda abaixo dos painéis: dentro deles cobriria a curva "sem controle".
    manipuladores, rotulos = eixos[0].get_legend_handles_labels()
    figura.legend(manipuladores, rotulos, loc="lower center", ncol=8, bbox_to_anchor=(0.5, -0.06))
    figura.suptitle("Figura 12 — Barras da rede com sobretensão por hora", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "12_violacoes_por_hora.png")


def figura_13_iteracoes_por_hora(pasta_de_figuras, dados_por_hora_todos):
    """Iterações de consenso por hora, por arquitetura e cenário."""
    figura, eixos = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    for eixo, arquitetura in zip(eixos, ARQUITETURAS_DO_EXPERIMENTO):
        for nome_do_cenario, cor in CORES_POR_CENARIO.items():
            dados = selecionar_caso(dados_por_hora_todos, arquitetura, nome_do_cenario).drop_duplicates("hora")
            eixo.plot(dados["hora"], dados["iteracoes"], color=cor, marker=MARCADORES_POR_CENARIO[nome_do_cenario],
                      markersize=4, linestyle=ESTILO_DE_LINHA_POR_CENARIO[nome_do_cenario], label=nome_do_cenario)
        eixo.axhline(NUMERO_MAXIMO_DE_ITERACOES, color=COR_DO_TEXTO_SECUNDARIO, linewidth=1.0, linestyle=":")
        eixo.annotate("k_max", xy=(0, NUMERO_MAXIMO_DE_ITERACOES), xytext=(2, 3), textcoords="offset points",
                      fontsize=7, color=COR_DO_TEXTO_SECUNDARIO)
        eixo.set_title(NOMES_LEGIVEIS_DAS_ARQUITETURAS[arquitetura], loc="left")
        eixo.set_xlabel("hora do dia")
        eixo.set_xticks(range(0, 24, 3))
    eixos[0].set_ylabel("iterações de consenso na hora")
    eixos[1].legend(loc="upper right", ncol=2)
    figura.suptitle("Figura 13 — Iterações de consenso por hora", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "13_iteracoes_por_hora.png")


def figura_14_mapa_de_calor_tensao(pasta_de_figuras, tabela_de_todas_as_barras):
    """
    Matriz hora x barra (tensão máxima), como a aba Matriz_V do código de referência.
    Escala sequencial de um só matiz (claro = baixa, escuro = alta), igual nos 3 painéis;
    células acima de V_lim recebem um ponto.
    """
    from matplotlib.colors import LinearSegmentedColormap

    mapa_sequencial = LinearSegmentedColormap.from_list("azul_sequencial", ["#eaf2fc", "#7fb0ea", "#2a78d6", "#0d3a73"])
    casos = [("sem_controle", "sem_controle"), (ARQUITETURA_LEADER_FOLLOWER, "C2"), (ARQUITETURA_LEADERLESS, "C2")]
    ordem_das_barras = list(dict.fromkeys(tabela_de_todas_as_barras["barra"]))
    valor_minimo = tabela_de_todas_as_barras["tensao_maxima_pu"].min()
    valor_maximo = tabela_de_todas_as_barras["tensao_maxima_pu"].max()

    figura, eixos = plt.subplots(1, 3, figsize=(16, 6.5), sharey=True)
    for eixo, (arquitetura, cenario) in zip(eixos, casos):
        dados = selecionar_caso(tabela_de_todas_as_barras, arquitetura, cenario)
        matriz = dados.pivot(index="barra", columns="hora", values="tensao_maxima_pu").reindex(ordem_das_barras)
        imagem = eixo.imshow(matriz.to_numpy(), aspect="auto", cmap=mapa_sequencial, vmin=valor_minimo, vmax=valor_maximo)
        linhas_violadas, colunas_violadas = np.where(matriz.to_numpy() > TENSAO_LIMITE_PU + TOLERANCIA_DE_TENSAO_PU)
        eixo.scatter(colunas_violadas, linhas_violadas, s=6, color="white", edgecolor=COR_DO_TEXTO_PRINCIPAL, linewidth=0.4)
        eixo.set_title("Sem controle" if arquitetura == "sem_controle" else rotulo_do_caso(arquitetura, cenario), loc="left")
        eixo.set_xticks(range(0, 24, 3))
        eixo.set_xlabel("hora do dia")
        eixo.grid(False)
    eixos[0].set_yticks(range(len(ordem_das_barras)))
    eixos[0].set_yticklabels(ordem_das_barras, fontsize=6)
    eixos[0].set_ylabel("barra")
    barra_de_cores = figura.colorbar(imagem, ax=eixos, fraction=0.02, pad=0.01)
    barra_de_cores.set_label("tensão máxima da barra (pu)")
    figura.suptitle(f"Figura 14 — Tensão por barra e hora (ponto = acima de {TENSAO_LIMITE_PU} pu)", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "14_mapa_de_calor_tensao.png")


def figura_15_linha_do_tempo_da_comunicacao(pasta_de_figuras, tabela_de_comunicacao, agentes_na_ordem_do_grafo, hora_de_pico):
    """
    Linha do tempo da comunicação na hora de pico (log de comunicação, LF):
    para cada agente e iteração k, se ele alcança o líder, está numa partição
    sem o líder, ou está isolado. O estado da rede é igual nas duas
    arquiteturas (§4.6); só o número de iterações muda.
    """
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    cores_dos_estados = ["#2a78d6", "#eda100", "#8a8984"]  # alcança o líder / outra partição / isolado
    nomes_dos_estados = ["alcança o líder", "partição sem o líder", "isolado"]
    cenarios = list(CORES_POR_CENARIO.keys())
    figura, eixos = plt.subplots(len(cenarios), 1, figsize=(11, 1.15 * len(cenarios) + 1), sharex=True)
    dados_da_hora = tabela_de_comunicacao[
        (tabela_de_comunicacao["arquitetura"] == ARQUITETURA_LEADER_FOLLOWER) & (tabela_de_comunicacao["hora"] == hora_de_pico)
    ]
    for eixo, cenario in zip(eixos, cenarios):
        dados = dados_da_hora[dados_da_hora["cenario"] == cenario].sort_values("iteracao_k")
        matriz_de_estados = np.zeros((len(agentes_na_ordem_do_grafo), len(dados)))
        for coluna, (_, linha) in enumerate(dados.iterrows()):
            agentes_isolados = [texto.split("(")[0] for texto in str(linha["agentes_isolados"]).split() if texto != "nan"]
            for indice, agente in enumerate(agentes_na_ordem_do_grafo):
                saltos = linha[f"saltos_ate_lider_{agente.barra}"]
                if str(indice + 1) in agentes_isolados:
                    matriz_de_estados[indice, coluna] = 2
                elif pd.isna(saltos):
                    matriz_de_estados[indice, coluna] = 1
                else:
                    matriz_de_estados[indice, coluna] = 0
        eixo.imshow(matriz_de_estados, aspect="auto", cmap=ListedColormap(cores_dos_estados), vmin=0, vmax=2,
                    interpolation="nearest")
        eixo.set_yticks(range(len(agentes_na_ordem_do_grafo)))
        eixo.set_yticklabels([f"{i + 1}:{a.barra}" for i, a in enumerate(agentes_na_ordem_do_grafo)], fontsize=6)
        eixo.set_ylabel(cenario, rotation=0, ha="right", va="center", fontsize=8)
        eixo.grid(False)
    eixos[-1].set_xlabel(f"iteração de consenso k (hora {hora_de_pico}, Leader-Follower; 1 k = {PERIODO_DO_CICLO_DE_COMUNICACAO_S} s no log)")
    figura.legend(handles=[Patch(color=c, label=n) for c, n in zip(cores_dos_estados, nomes_dos_estados)],
                  loc="upper right", ncol=3, bbox_to_anchor=(0.99, 1.0))
    figura.suptitle("Figura 15 — Linha do tempo da comunicação por agente", x=0.01, y=1.0, ha="left", fontsize=11)
    figura.subplots_adjust(top=0.95, hspace=0.25)
    salvar_figura(figura, pasta_de_figuras, "15_linha_do_tempo_comunicacao.png")


def figura_16_mensagens_perdidas(pasta_de_figuras, resumo_de_comunicacao_por_hora):
    """Taxa de perda de mensagens por hora e cenário (Leader-Follower; a topologia é a mesma no Leaderless)."""
    figura, eixo = plt.subplots(figsize=(9, 3.8))
    for nome_do_cenario, cor in CORES_POR_CENARIO.items():
        dados = selecionar_caso(resumo_de_comunicacao_por_hora, ARQUITETURA_LEADER_FOLLOWER, nome_do_cenario)
        eixo.plot(dados["hora"], dados["taxa_de_perda_percentual"], color=cor, marker=MARCADORES_POR_CENARIO[nome_do_cenario],
                  markersize=5, linestyle=ESTILO_DE_LINHA_POR_CENARIO[nome_do_cenario], label=nome_do_cenario)
    eixo.set_xlabel("hora do dia (só horas em que o consenso trocou mensagens)")
    eixo.set_ylabel("mensagens perdidas (%)")
    eixo.set_xticks(range(0, 24, 1))
    eixo.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    eixo.set_title("Figura 16 — Taxa de perda de mensagens por hora (Leader-Follower)", loc="left")
    salvar_figura(figura, pasta_de_figuras, "16_mensagens_perdidas.png")


def figura_17_rho_nas_iteracoes_da_hora_de_pico(pasta_de_figuras, dados_por_iteracao, agentes_na_ordem_do_grafo, hora_de_pico):
    """rho_i(k) na hora de pico: dinâmica do consenso durante e depois da falha."""
    casos = [
        (ARQUITETURA_LEADER_FOLLOWER, "C2"), (ARQUITETURA_LEADERLESS, "C2"),
        (ARQUITETURA_LEADER_FOLLOWER, "C3_lider_curta"), (ARQUITETURA_LEADERLESS, "C3_lider_curta"),
    ]
    figura, eixos = plt.subplots(2, 2, figsize=(12, 7), sharey=True)
    for eixo, (arquitetura, cenario) in zip(eixos.flat, casos):
        dados = selecionar_caso(dados_por_iteracao, arquitetura, cenario)
        dados = dados[dados["hora"] == hora_de_pico]
        for indice, agente in enumerate(agentes_na_ordem_do_grafo):
            eixo.plot(dados["iteracao_k"], dados[f"rho_{agente.barra}"], color=CORES_POR_POSICAO_DO_AGENTE[indice],
                      label=f"{indice + 1}: {agente.barra}")
        if cenario.startswith("C3") and cenario.endswith("curta"):
            eixo.axvline(ITERACAO_DE_RETORNO_FALHA_CURTA, color=COR_DO_TEXTO_SECUNDARIO, linestyle=":", linewidth=1.0)
            eixo.annotate("agente volta", xy=(ITERACAO_DE_RETORNO_FALHA_CURTA, 1.0), xytext=(3, -10),
                          textcoords="offset points", fontsize=7, color=COR_DO_TEXTO_SECUNDARIO)
        eixo.set_title(f"{rotulo_do_caso(arquitetura, cenario)} (hora {hora_de_pico})", loc="left", fontsize=9)
        eixo.set_ylim(-0.03, 1.03)
    for eixo in eixos[1]:
        eixo.set_xlabel("iteração de consenso k")
    for eixo in eixos[:, 0]:
        eixo.set_ylabel("rho_i(k)")
    eixos[0, 1].legend(loc="lower right", ncol=2)
    figura.suptitle("Figura 17 — rho_i(k) na hora de pico: partição (C2) e falha curta do líder (C3)", x=0.01, ha="left", fontsize=11)
    salvar_figura(figura, pasta_de_figuras, "17_rho_iteracoes_hora_pico.png")


# =============================================================================
# RESULTADOS — arquivos de configuração e manifest (§5.5)
# =============================================================================


def obter_versao_do_codigo():
    """Hash do commit git atual (ou 'desconhecido' fora de um repositório)."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=PASTA_DO_PROJETO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconhecido"


def calcular_hash_da_matriz(matriz):
    """Impressão digital curta de uma matriz de adjacência (rastreabilidade)."""
    return hashlib.sha256(np.ascontiguousarray(matriz).tobytes()).hexdigest()[:16]


def calcular_hash_do_arquivo(caminho):
    """Hash completo de um artefato que influencia a execução."""
    sha256 = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            sha256.update(bloco)
    return sha256.hexdigest()


def salvar_config_yaml(pasta, agentes_na_ordem_do_grafo, epsilon, hora_de_pico, origem_das_curvas, curvas, cenarios):
    """config.yaml: tudo o que define o experimento (§5.5, §7.5)."""
    configuracao = {
        "alimentador": str(ARQUIVO_DSS_DO_ALIMENTADOR.relative_to(PASTA_DO_PROJETO)),
        "elemento_eletrico": "PVSystem (curtailment via kVA, PF=1)",
        "multiplicador_base_de_carga": MULTIPLICADOR_BASE_DE_CARGA,
        "fator_de_escala_dos_pvs_lambda": FATOR_DE_ESCALA_DOS_PVS,
        "agentes_na_ordem_do_grafo": [
            {"posicao": indice + 1, "pvsystem": agente.nome_do_pvsystem, "barra": agente.barra, "kva": agente.potencia_nominal_kva}
            for indice, agente in enumerate(agentes_na_ordem_do_grafo)
        ],
        "grafo_nominal_enlaces_1_indexado": [[a + 1, b + 1] for a, b in ENLACES_DO_GRAFO_NOMINAL],
        "arquiteturas": ARQUITETURAS_DO_EXPERIMENTO,
        "cenarios": [
            {
                "nome": cenario.nome,
                "descricao": cenario.descricao,
                "arestas_removidas_1_indexado": [[a + 1, b + 1] for a, b in cenario.arestas_removidas],
                "posicao_do_agente_isolado": None if cenario.indice_do_agente_isolado is None else cenario.indice_do_agente_isolado + 1,
                "iteracao_de_retorno": cenario.iteracao_de_retorno_do_agente,
                "m_e_lider": cenario.agente_isolado_e_o_lider,
                "canal_habilitado": cenario.canal_habilitado,
                "probabilidade_de_perda_do_canal": cenario.probabilidade_de_perda_do_canal,
            }
            for cenario in cenarios
        ],
        "hora_da_falha_c3": int(hora_de_pico),
        "epsilon": float(epsilon),
        "regra_do_epsilon": "2/tr(L0), calculado no grafo nominal e fixo em todos os cenarios (opcao (a), secao 4.5)",
        "ganho_beta": GANHO_DE_CORRECAO_DE_TENSAO,
        "normalizacao_do_beta": "beta identico nas duas arquiteturas (secao 7.5, opcao primaria)",
        "convencao_de_sinal": "rho = fracao de curtailment; correcao somada (equivale a beta_paper = 1 - rho)",
        "tensao_limite_pu": TENSAO_LIMITE_PU,
        "tensao_minima_para_contagem_de_subtensao_pu": TENSAO_MINIMA_PU,
        "periodo_do_ciclo_de_comunicacao_s_apenas_rotulo_do_log": PERIODO_DO_CICLO_DE_COMUNICACAO_S,
        "tolerancia_de_tensao_pu": TOLERANCIA_DE_TENSAO_PU,
        "tolerancia_de_consenso": TOLERANCIA_DE_CONSENSO,
        "numero_maximo_de_iteracoes": NUMERO_MAXIMO_DE_ITERACOES,
        "criterio_de_parada": "eletrico: V vista pelo controle <= V_lim + tol, ou k_max; consenso reportado separadamente",
        "tensao_monitorada_lf": "max das barras com PV na componente conexa do lider em A(k) (secao 7.3)",
        "curvas_diarias": {
            "origem": origem_das_curvas,
            "observacao": "curvas de exemplo; irradiancia = curva_pv_kw / pico da curva",
            "multiplicador_de_carga": [float(valor) for valor in curvas["multiplicador_de_carga"]],
            "irradiancia_pu": [float(valor) for valor in curvas["irradiancia_pu"]],
        },
    }
    with open(pasta / "config.yaml", "w") as arquivo:
        yaml.safe_dump(configuracao, arquivo, allow_unicode=True, sort_keys=False)


def salvar_manifest_json(pasta, lambda_2_por_cenario, hashes_por_cenario, violacao_acumulada, agentes_ordem_de_referencia,
                         lider, hora_de_pico, validacoes):
    """manifest.json: metadados de execução e rastreabilidade (§5.5)."""
    import altdss as pacote_altdss

    manifest = {
        "data_de_execucao": datetime.now(UTC).isoformat(timespec="seconds"),
        "versao_do_codigo_git": obter_versao_do_codigo(),
        "python": platform.python_version(),
        "altdss": getattr(pacote_altdss, "__version__", "desconhecida"),
        "modelo_de_comunicacao": "C1-C3: falha deterministica de topologia (periodo de 0.2 s apenas no log). "
                                 "C0/C0_perda_*: canal probabilistico sobre topologia nominal, quando habilitado.",
        "configuracao_do_canal": CONFIGURACAO_COMUNICACAO.copy(),
        "arquivos_de_entrada": {
            "codigo": calcular_hash_do_arquivo(Path(__file__)),
            "rede": calcular_hash_do_arquivo(ARQUIVO_DSS_DO_ALIMENTADOR),
            "curvas": calcular_hash_do_arquivo(ARQUIVO_DE_CURVAS_DIARIAS),
            "lockfile": calcular_hash_do_arquivo(PASTA_DO_PROJETO / "uv.lock"),
        },
        "lambda_2_por_cenario_estatico": lambda_2_por_cenario,
        "hash_da_adjacencia_por_cenario": hashes_por_cenario,
        "violacao_acumulada_S_i_pu_h": {
            agente.barra: float(valor) for agente, valor in zip(agentes_ordem_de_referencia, violacao_acumulada)
        },
        "lider": {"barra": lider.barra, "pvsystem": lider.nome_do_pvsystem, "criterio": "B: argmax S_i (secao 4.4.1)"},
        "hora_de_pico_para_c3": int(hora_de_pico),
        "validacoes": [{"checagem": d, "passou": bool(p), "detalhe": det} for d, p, det in validacoes],
    }
    with open(pasta / "manifest.json", "w") as arquivo:
        json.dump(manifest, arquivo, indent=2, ensure_ascii=False)


# =============================================================================
# PROGRAMA PRINCIPAL
# =============================================================================


def preparar_pastas_de_resultados():
    """Cria a árvore Resultados/FASE0_EXP001/{raw,summary,figures,tables}."""
    for subpasta in ["raw", "summary", "figures", "tables"]:
        (PASTA_DE_RESULTADOS / subpasta).mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Executa o experimento de consenso FACENS.")
    parser.add_argument("--output-dir", type=Path, help="pasta de resultados desta execução")
    parser.add_argument(
        "--loss-probability",
        type=str,
        default="0.0",
        help="uma ou mais probabilidades de perda por mensagem, separadas por virgula "
             "(ex.: 0.05,0.1,0.2). 0.0 e sempre incluido automaticamente como controle "
             "'com controle, sem perdas' (cenario C0).",
    )
    parser.add_argument("--delay-steps", type=int, default=0, help="atraso inteiro em iterações")
    parser.add_argument("--seed", type=int, default=None, help="semente do canal")
    parser.add_argument("--enable-channel", action="store_true", help="habilita perda/atraso por mensagem")
    argumentos = parser.parse_args()
    global PASTA_DE_RESULTADOS, PASTA_DE_LOGS
    if argumentos.output_dir is not None:
        PASTA_DE_RESULTADOS = argumentos.output_dir.resolve()
        PASTA_DE_LOGS = PASTA_DE_RESULTADOS / "logs"

    try:
        probabilidades_de_perda = [float(valor) for valor in argumentos.loss_probability.split(",") if valor.strip()]
    except ValueError:
        parser.error("--loss-probability deve ser um numero ou uma lista separada por virgula (ex.: 0.05,0.1)")
    if not probabilidades_de_perda:
        parser.error("--loss-probability nao pode ser uma lista vazia")
    if any(not 0.0 <= valor <= 1.0 for valor in probabilidades_de_perda):
        parser.error("--loss-probability deve estar entre 0 e 1")
    if argumentos.delay_steps < 0:
        parser.error("--delay-steps não pode ser negativo")

    CONFIGURACAO_COMUNICACAO.update(
        habilitado=argumentos.enable_channel,
        probabilidades_de_perda=probabilidades_de_perda,
        atraso_em_iteracoes=argumentos.delay_steps,
        semente=argumentos.seed,
    )
    preparar_pastas_de_resultados()
    aplicar_estilo_das_figuras()

    # --- Entradas --------------------------------------------------------------
    curvas, origem_das_curvas = carregar_ou_criar_curvas_diarias()
    print(f"Curvas diárias: {origem_das_curvas}")

    # --- Etapa 2/3: caso sem controle -> S_i -> líder (§4.4.1, checklist 3) ---
    agentes_ordem_de_referencia = criar_agentes_na_ordem_de_referencia()
    dados_sem_controle, tensoes_sem_controle, barras_sem_controle = simular_dia_sem_controle(
        curvas, agentes_ordem_de_referencia
    )
    violacao_acumulada = calcular_violacao_acumulada_por_agente(tensoes_sem_controle)
    lider = determinar_lider_por_criterio_B(violacao_acumulada, agentes_ordem_de_referencia)

    print("\nViolação acumulada S_i (pu·h) no caso sem controle:")
    for agente, valor in zip(agentes_ordem_de_referencia, violacao_acumulada):
        print(f"  {agente.nome_do_pvsystem} (barra {agente.barra}): {valor:.5f}")
    print(f"Líder (argmax S_i): {lider.nome_do_pvsystem}, barra {lider.barra}")

    # Hora de maior sobretensão sem controle: onde a falha de C3 é injetada (§7.1).
    tensao_maxima_por_hora_sem_controle = tensoes_sem_controle.max(axis=1)
    hora_de_pico = int(np.argmax(tensao_maxima_por_hora_sem_controle))
    print(f"Hora de pico de sobretensão (falha de C3): {hora_de_pico} h, "
          f"Vmax = {tensao_maxima_por_hora_sem_controle[hora_de_pico]:.4f} pu")
    if tensao_maxima_por_hora_sem_controle[hora_de_pico] <= TENSAO_LIMITE_PU:
        print("AVISO: nenhuma sobretensão no caso sem controle — o controle nunca atuará.")

    # --- Checklist 4: rótulos do grafo de comunicação -----------------------
    agentes_na_ordem_do_grafo = ordenar_agentes_na_ordem_do_grafo(agentes_ordem_de_referencia, violacao_acumulada)
    print("Agentes na ordem do grafo (posição 1..6): " + ", ".join(a.barra for a in agentes_na_ordem_do_grafo))

    matriz_nominal = montar_matriz_de_adjacencia(ENLACES_DO_GRAFO_NOMINAL, NUMERO_DE_AGENTES)
    epsilon = calcular_epsilon_do_consenso(matriz_nominal)
    print(f"epsilon = 2/tr(L0) = {epsilon:.4f}")

    cenarios = definir_cenarios_de_falha()
    if CONFIGURACAO_COMUNICACAO["habilitado"]:
        # Eixo probabilistico substitui o "C0" estrutural (canal=None) pelo mesmo
        # cenario rodado atraves do canal (perda 0.00) mais um por probabilidade de
        # perda pedida, mantendo C1-C3 como o eixo estrutural determinístico.
        cenarios = [c for c in cenarios if c.nome != "C0"] + definir_cenarios_de_perda_probabilistica(
            CONFIGURACAO_COMUNICACAO["probabilidades_de_perda"]
        )
    lambda_2_por_cenario = {}
    hashes_por_cenario = {}
    for cenario in cenarios:
        grafo = GrafoDeComunicacao(cenario, hora_de_pico)
        matriz_estatica = grafo.matriz_de_adjacencia_estatica
        matriz_durante_falha = grafo.matriz_de_adjacencia_na_iteracao(hora_de_pico, 0)
        lambda_2_por_cenario[cenario.nome] = calcular_conectividade_algebrica(matriz_durante_falha)
        hashes_por_cenario[cenario.nome] = calcular_hash_da_matriz(matriz_durante_falha)
        if cenario.nome in ("C0", "C1", "C2"):
            lambda_2_por_cenario[cenario.nome] = calcular_conectividade_algebrica(matriz_estatica)
    print("lambda_2 por cenário (C3: durante a falha): "
          + ", ".join(f"{nome}={valor:.3f}" for nome, valor in lambda_2_por_cenario.items()))

    # --- Matriz experimental (§4.6.1) ------------------------------------------
    tabelas_por_hora = [dados_sem_controle]
    tabelas_por_iteracao = []
    tabelas_de_todas_as_barras = [barras_sem_controle]
    tabelas_de_comunicacao = []
    tabelas_de_mensagens = []
    tabelas_de_mensagens_do_canal = []
    checagens_por_caso = {}
    for arquitetura in ARQUITETURAS_DO_EXPERIMENTO:
        for cenario in cenarios:
            # O registrador de comunicação imprime o log do caso (eventos e resumo por hora).
            resultado_do_caso = simular_dia_com_consenso(
                arquitetura, cenario, curvas, agentes_na_ordem_do_grafo, hora_de_pico, epsilon
            )
            tabelas_por_hora.append(resultado_do_caso["por_hora"])
            tabelas_por_iteracao.append(resultado_do_caso["por_iteracao"])
            tabelas_de_todas_as_barras.append(resultado_do_caso["todas_as_barras"])
            tabelas_de_comunicacao.append(resultado_do_caso["comunicacao"])
            tabelas_de_mensagens.append(resultado_do_caso["mensagens"])
            tabelas_de_mensagens_do_canal.append(resultado_do_caso["mensagens_do_canal"])
            checagens_por_caso[(arquitetura, cenario.nome)] = resultado_do_caso["checagens"]

    dados_por_hora_todos = pd.concat(tabelas_por_hora, ignore_index=True)
    dados_por_iteracao_todos = pd.concat(tabelas_por_iteracao, ignore_index=True)
    tabela_de_todas_as_barras = pd.concat(tabelas_de_todas_as_barras, ignore_index=True)
    tabela_de_comunicacao = pd.concat(tabelas_de_comunicacao, ignore_index=True)
    tabela_de_mensagens = pd.concat(tabelas_de_mensagens, ignore_index=True)
    tabela_de_mensagens_do_canal = pd.concat(tabelas_de_mensagens_do_canal, ignore_index=True)

    # --- Resumos ---------------------------------------------------------------
    resumos = [resumir_um_caso(dados_sem_controle, hora_de_pico)]
    for arquitetura in ARQUITETURAS_DO_EXPERIMENTO:
        for cenario in cenarios:
            dados_do_caso = dados_por_hora_todos[
                (dados_por_hora_todos["arquitetura"] == arquitetura) & (dados_por_hora_todos["cenario"] == cenario.nome)
            ]
            resumos.append(resumir_um_caso(dados_do_caso, hora_de_pico))
    tabela_de_resumo = pd.DataFrame(resumos)

    violacoes_por_hora = montar_violacoes_por_hora(tabela_de_todas_as_barras)
    total_de_barras_hora_com_violacao = violacoes_por_hora.groupby(["arquitetura", "cenario"], sort=False)[
        ["numero_de_barras_com_sobretensao", "numero_de_barras_com_subtensao"]
    ].sum()
    tabela_de_resumo = tabela_de_resumo.merge(
        total_de_barras_hora_com_violacao.rename(
            columns={
                "numero_de_barras_com_sobretensao": "barras_hora_com_sobretensao_no_dia",
                "numero_de_barras_com_subtensao": "barras_hora_com_subtensao_no_dia",
            }
        ).reset_index(),
        on=["arquitetura", "cenario"],
        how="left",
    )
    curtailment_por_pv = montar_curtailment_por_pv(dados_por_hora_todos)
    resumo_de_comunicacao_por_hora = montar_resumo_da_comunicacao(tabela_de_mensagens, tabela_de_comunicacao, agrupar_por_hora=True)
    resumo_de_comunicacao_por_caso = montar_resumo_da_comunicacao(tabela_de_mensagens, tabela_de_comunicacao, agrupar_por_hora=False)

    # --- Validação (§6) --------------------------------------------------------
    validacoes = validar_resultados(dados_por_hora_todos, lambda_2_por_cenario, checagens_por_caso)
    print("\nValidações (§6):")
    for descricao, passou, detalhe in validacoes:
        print(f"  [{'OK' if passou else 'FALHOU'}] {descricao} {detalhe}")

    # --- Arquivos de saída (§5.5) ----------------------------------------------
    dados_por_hora_todos.to_csv(PASTA_DE_RESULTADOS / "raw" / "timestep.csv", index=False)
    dados_por_iteracao_todos.to_csv(PASTA_DE_RESULTADOS / "raw" / "consensus_iterations.csv", index=False)

    colunas_convergencia = ["arquitetura", "cenario", "horas_com_controle_ativo", "horas_nao_convergidas",
                            "iteracoes_totais_no_dia", "iteracoes_hora_pico", "status_hora_pico"]
    colunas_sigma = ["arquitetura", "cenario", "sigma_r_diario_por_energia", "sigma_r_global_hora_pico",
                     "sigma_r_por_particao_hora_pico"]
    colunas_tensao = ["arquitetura", "cenario", "tensao_maxima_barras_pv_dia_pu", "tensao_maxima_rede_dia_pu",
                      "horas_com_violacao_barras_pv", "tensao_maxima_barras_pv_hora_pico_pu"]
    tabela_controlada = tabela_de_resumo[tabela_de_resumo["arquitetura"] != "sem_controle"]
    tabela_controlada[colunas_convergencia].to_csv(PASTA_DE_RESULTADOS / "summary" / "convergencia_por_cenario.csv", index=False)
    tabela_controlada[colunas_sigma].to_csv(PASTA_DE_RESULTADOS / "summary" / "sigma_r_por_cenario.csv", index=False)
    tabela_de_resumo[colunas_tensao].to_csv(PASTA_DE_RESULTADOS / "summary" / "tensao_por_cenario.csv", index=False)
    tabela_de_resumo.to_csv(PASTA_DE_RESULTADOS / "tables" / "resumo_completo.csv", index=False)

    # Tabelas extras (inspiradas no código de referência)
    tabela_de_todas_as_barras.to_csv(PASTA_DE_RESULTADOS / "raw" / "tensoes_todas_barras.csv", index=False)
    tabela_de_comunicacao.to_csv(PASTA_DE_RESULTADOS / "raw" / "log_comunicacao.csv", index=False)
    tabela_de_mensagens.to_csv(PASTA_DE_RESULTADOS / "raw" / "log_mensagens.csv", index=False)
    tabela_de_mensagens_do_canal.to_csv(PASTA_DE_RESULTADOS / "raw" / "channel_messages.csv", index=False)
    violacoes_por_hora.to_csv(PASTA_DE_RESULTADOS / "summary" / "violacoes_por_hora.csv", index=False)
    curtailment_por_pv.to_csv(PASTA_DE_RESULTADOS / "summary" / "curtailment_por_pv.csv", index=False)
    resumo_de_comunicacao_por_hora.to_csv(PASTA_DE_RESULTADOS / "summary" / "comunicacao_por_hora.csv", index=False)
    resumo_de_comunicacao_por_caso.to_csv(PASTA_DE_RESULTADOS / "summary" / "comunicacao_por_caso.csv", index=False)
    salvar_matrizes_hora_por_barra(tabela_de_todas_as_barras, dados_por_hora_todos, PASTA_DE_RESULTADOS / "matrizes")

    salvar_config_yaml(PASTA_DE_RESULTADOS, agentes_na_ordem_do_grafo, epsilon, hora_de_pico, origem_das_curvas, curvas, cenarios)
    salvar_manifest_json(PASTA_DE_RESULTADOS, lambda_2_por_cenario, hashes_por_cenario, violacao_acumulada,
                         agentes_ordem_de_referencia, lider, hora_de_pico, validacoes)

    # --- Figuras ---------------------------------------------------------------
    pasta_de_figuras = PASTA_DE_RESULTADOS / "figures"
    figura_01_sistema_eletrico(pasta_de_figuras, agentes_na_ordem_do_grafo)
    figura_02_grafo_de_comunicacao(pasta_de_figuras, agentes_na_ordem_do_grafo, cenarios, hora_de_pico)
    figura_03_convergencia(pasta_de_figuras, dados_por_iteracao_todos, hora_de_pico)
    figura_04_tensoes(pasta_de_figuras, dados_por_hora_todos)
    figura_05_curtailment(pasta_de_figuras, tabela_de_resumo, agentes_na_ordem_do_grafo)
    figura_06_margem_H3(pasta_de_figuras, tabela_de_resumo)
    figura_07_H5_particionamento(pasta_de_figuras, dados_por_hora_todos)
    figura_08_H5a_falha_do_lider(pasta_de_figuras, tabela_de_resumo)
    figura_00_curvas_de_entrada(pasta_de_figuras, curvas)
    figura_09_potencias_pv(pasta_de_figuras, dados_por_hora_todos, agentes_na_ordem_do_grafo)
    figura_10_rho_por_hora(pasta_de_figuras, dados_por_hora_todos, agentes_na_ordem_do_grafo)
    figura_11_tensoes_individuais_pvs(pasta_de_figuras, dados_por_hora_todos, agentes_na_ordem_do_grafo)
    figura_12_violacoes_por_hora(pasta_de_figuras, violacoes_por_hora)
    figura_13_iteracoes_por_hora(pasta_de_figuras, dados_por_hora_todos)
    figura_14_mapa_de_calor_tensao(pasta_de_figuras, tabela_de_todas_as_barras)
    figura_15_linha_do_tempo_da_comunicacao(pasta_de_figuras, tabela_de_comunicacao, agentes_na_ordem_do_grafo, hora_de_pico)
    figura_16_mensagens_perdidas(pasta_de_figuras, resumo_de_comunicacao_por_hora)
    figura_17_rho_nas_iteracoes_da_hora_de_pico(pasta_de_figuras, dados_por_iteracao_todos, agentes_na_ordem_do_grafo, hora_de_pico)

    print("\nResumo por caso:")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(tabela_de_resumo[["arquitetura", "cenario", "tensao_maxima_barras_pv_dia_pu", "horas_com_violacao_barras_pv",
                                "curtailment_percentual_dia", "sigma_r_diario_por_energia"]
                               + [c for c in ["iteracoes_hora_pico", "status_hora_pico", "sigma_r_por_particao_hora_pico"] if c in tabela_de_resumo]]
              .to_string(index=False, float_format=lambda valor: f"{valor:.4f}"))

    print("\nNúmero de barras da rede com sobretensão a cada hora (0..23):")
    for (arquitetura, cenario), dados in violacoes_por_hora.groupby(["arquitetura", "cenario"], sort=False):
        print(f"  {arquitetura:16s} {cenario:18s} {dados['numero_de_barras_com_sobretensao'].tolist()}"
              f"  total={int(dados['numero_de_barras_com_sobretensao'].sum())}")

    print("\nComunicação por caso (mensagens entre vizinhos nominais, todas as horas com consenso):")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(resumo_de_comunicacao_por_caso.to_string(index=False, float_format=lambda valor: f"{valor:.2f}"))
    print(f"\nResultados salvos em {PASTA_DE_RESULTADOS.relative_to(PASTA_DO_PROJETO)}")


if __name__ == "__main__":
    main()
