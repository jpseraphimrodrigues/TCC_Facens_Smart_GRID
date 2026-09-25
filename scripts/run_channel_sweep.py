"""Executa replicações do modelo probabilístico e agrega métricas.

Uso:
    uv run python scripts/run_channel_sweep.py --replications 3 \
        --loss-probability 0.05 --delay-steps 1 \
        --output-dir Resultados/SWEEP_001
"""

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


def executar_replicacao(projeto: Path, pasta: Path, perda: float, atraso: int, semente: int) -> None:
    comando = [
        sys.executable,
        str(projeto / "Experimento_Consenso_comunication_failure.py"),
        "--enable-channel",
        "--loss-probability",
        str(perda),
        "--delay-steps",
        str(atraso),
        "--seed",
        str(semente),
        "--output-dir",
        str(pasta),
    ]
    subprocess.run(comando, cwd=projeto, check=True)


def agregar_replicacoes(pastas: list[Path], saida: Path) -> pd.DataFrame:
    tabelas = []
    for numero, pasta in enumerate(pastas, start=1):
        tabela = pd.read_csv(pasta / "tables" / "resumo_completo.csv")
        tabela["replicacao"] = numero
        tabelas.append(tabela)
    dados = pd.concat(tabelas, ignore_index=True)
    metricas = [
        "tensao_maxima_barras_pv_dia_pu",
        "horas_com_violacao_barras_pv",
        "curtailment_percentual_dia",
        "sigma_r_diario_por_energia",
    ]
    resumo = (
        dados.groupby(["arquitetura", "cenario"], as_index=False)[metricas]
        .agg(["count", "mean", "std", "min", "max"])
        .reset_index()
    )
    resumo.columns = [
        "_".join(str(parte) for parte in coluna if str(parte) != "").rstrip("_")
        if isinstance(coluna, tuple) else str(coluna)
        for coluna in resumo.columns
    ]
    saida.mkdir(parents=True, exist_ok=True)
    dados.to_csv(saida / "replicacoes_brutas.csv", index=False)
    resumo.to_csv(saida / "resumo_estatistico.csv", index=False)
    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replications", type=int, default=3)
    parser.add_argument("--loss-probability", type=float, default=0.05)
    parser.add_argument("--delay-steps", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.replications < 1:
        parser.error("--replications deve ser pelo menos 1")
    if not 0.0 <= args.loss_probability <= 1.0:
        parser.error("--loss-probability deve estar entre 0 e 1")
    if args.delay_steps < 0:
        parser.error("--delay-steps não pode ser negativo")

    projeto = Path(__file__).resolve().parents[1]
    pastas = []
    for numero in range(args.replications):
        pasta = args.output_dir / f"replicacao_{numero + 1:03d}"
        executar_replicacao(projeto, pasta, args.loss_probability, args.delay_steps, args.seed + numero)
        pastas.append(pasta)
    agregar_replicacoes(pastas, args.output_dir)


if __name__ == "__main__":
    main()
