# scripts/run_pipeline.py

import subprocess
import sys
import time
from pathlib import Path

# --------------------------------------------------
# Paths absolutos
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

def p(*parts):
    return str(ROOT.joinpath(*parts))

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def run_step(label, command):
    print(f"\n▶️  {label}")
    print("💻 Executando:", " ".join(command))

    result = subprocess.run(
        command,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False
    )

    if result.returncode != 0:
        print(f"\n❌ Falha na etapa: {label}")
        sys.exit(result.returncode)

    print(f"✅ Etapa concluída: {label}")
    time.sleep(1)

# --------------------------------------------------
# Pipeline
# --------------------------------------------------

def main():
    print("🚀 Iniciando pipeline Modo 3")
    print(f"📂 Root do projeto: {ROOT}")

    steps = [
        (
            "Unificação de dados",
            [PYTHON, p("scripts", "normalizers", "unify.py")]
        ),
        (
            "Atualização de histórico de preços",
            [PYTHON, p("scripts", "history", "price_history.py")]
        ),
        (
            "Ranking editorial",
            [PYTHON, "-m", "scripts.ranking.rank"]
        ),
        (
            "Aplicação do limiar editorial (Modo 3)",
            [PYTHON, p("scripts", "editorial", "apply_threshold.py")]
        ),
    ]

    for label, command in steps:
        run_step(label, command)

    print("\n🎉 Pipeline finalizado com sucesso!")
    print("📄 Arquivo pronto para upload:")
    print("   → data/inbox/rascunhos.json")

if __name__ == "__main__":
    main()
