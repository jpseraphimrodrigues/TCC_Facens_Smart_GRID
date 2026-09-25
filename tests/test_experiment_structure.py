"""Testes estruturais das invariantes do experimento determinístico."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from tcc_facens.communication import CommunicationChannel

SWEEP_SPEC = importlib.util.spec_from_file_location(
    "channel_sweep", Path(__file__).parents[1] / "scripts" / "run_channel_sweep.py"
)
SWEEP = importlib.util.module_from_spec(SWEEP_SPEC)
assert SWEEP_SPEC.loader is not None
SWEEP_SPEC.loader.exec_module(SWEEP)

CAMINHO = Path(__file__).parents[1] / "Experimento_Consenso_comunication_failure.py"
SPEC = importlib.util.spec_from_file_location("experimento_facens", CAMINHO)
EXPERIMENTO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(EXPERIMENTO)


def test_c2_isola_o_lider_e_desconecta_o_grafo():
    cenario = next(c for c in EXPERIMENTO.definir_cenarios_de_falha() if c.nome == "C2")
    grafo = EXPERIMENTO.GrafoDeComunicacao(cenario, hora_da_falha_temporaria=10)
    matriz = grafo.matriz_de_adjacencia_na_iteracao(10, 0)

    assert EXPERIMENTO.calcular_conectividade_algebrica(matriz) == 0.0
    assert EXPERIMENTO.encontrar_componente_do_agente(matriz, 0) == [0]


def test_c3_retorna_na_iteracao_programada():
    cenario = next(c for c in EXPERIMENTO.definir_cenarios_de_falha() if c.nome == "C3_lider_curta")
    grafo = EXPERIMENTO.GrafoDeComunicacao(cenario, hora_da_falha_temporaria=10)

    assert grafo.agente_esta_isolado(10, 0)
    assert not grafo.agente_esta_isolado(10, 20)
    assert not grafo.agente_esta_isolado(9, 0)


def test_mistura_por_consenso_preserva_intervalo_com_rho_uniforme():
    matriz = EXPERIMENTO.montar_matriz_de_adjacencia([(0, 1), (1, 2)], 3)
    rho = np.full(3, 0.25)

    resultado = EXPERIMENTO.misturar_por_consenso(rho, matriz, 0.1)

    np.testing.assert_allclose(resultado, rho)
    assert np.all((resultado >= 0.0) & (resultado <= 1.0))


def test_canal_com_atraso_preserva_ultima_mensagem_valida():
    canal = CommunicationChannel(loss_probability=0.0, delay_steps=2, seed=7)
    assert canal.transmit(0, 1, {"rho": 0.2}, step=0)
    assert canal.deliver_until(1) == []
    assert canal.current_state(0, 1) is None

    entregues = canal.deliver_until(2)
    assert len(entregues) == 1
    assert entregues[0].content == {"rho": 0.2}
    assert canal.current_state(0, 1) == entregues[0]


def test_canal_com_perda_deterministica_por_semente():
    canal = CommunicationChannel(loss_probability=1.0, seed=11)
    assert not canal.transmit(0, 1, {"rho": 0.2}, step=0)
    assert canal.deliver_until(0) == []
    assert canal.metrics()["messages_lost"] == 1
    assert canal.events[0]["status"] == "lost"


def test_canal_registra_entrega_e_fila():
    canal = CommunicationChannel(loss_probability=0.0, delay_steps=2, seed=1)
    canal.transmit(0, 1, {"rho": 0.4}, step=3)
    assert canal.events[0]["status"] == "queued"
    canal.deliver_until(5)
    assert canal.events[0]["status"] == "delivered"


def test_mistura_integrada_usa_estado_recebido_do_canal():
    canal = CommunicationChannel(loss_probability=0.0, delay_steps=1, seed=3)
    matriz = EXPERIMENTO.montar_matriz_de_adjacencia([(0, 1)], 2)
    rho = np.array([0.0, 1.0])

    primeiro = EXPERIMENTO.misturar_por_consenso_com_canal(rho, matriz, 0.1, canal, 0)
    segundo = EXPERIMENTO.misturar_por_consenso_com_canal(primeiro, matriz, 0.1, canal, 1)

    np.testing.assert_allclose(primeiro, [0.1, 0.9])
    assert segundo[0] > primeiro[0]
    assert segundo[1] < primeiro[1]


def test_agregador_de_replicacoes_calcula_media(tmp_path):
    linhas = "arquitetura,cenario,tensao_maxima_barras_pv_dia_pu,horas_com_violacao_barras_pv,curtailment_percentual_dia,sigma_r_diario_por_energia\nleaderless,C0,1.05,0,40,0.1\n"
    pastas = []
    for numero in (1, 2):
        pasta = tmp_path / f"replicacao_{numero:03d}" / "tables"
        pasta.mkdir(parents=True)
        (pasta / "resumo_completo.csv").write_text(linhas.replace("1.05", f"{1.04 + numero / 100:.2f}"), encoding="utf-8")
        pastas.append(pasta.parent)

    resumo = SWEEP.agregar_replicacoes(pastas, tmp_path / "saida")

    linha = resumo.iloc[0]
    assert linha["tensao_maxima_barras_pv_dia_pu_mean"] == pytest.approx(1.055)
    assert linha["tensao_maxima_barras_pv_dia_pu_count"] == 2
