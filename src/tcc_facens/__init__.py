"""Entry point instalável do experimento FACENS."""

import runpy
from pathlib import Path


def main() -> None:
    """Executa o experimento legado mantendo um único motor de simulação."""
    projeto = Path(__file__).resolve().parents[2]
    runpy.run_path(str(projeto / "Experimento_Consenso_comunication_failure.py"), run_name="__main__")
