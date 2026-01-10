# scripts/run_pipeline.py
import subprocess
import sys
import os
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
def run_step(label, command, cwd=None):
    print(f"\n▶️  {label}")
    print("💻 Executando:", " ".join(command))
    
    result = subprocess.run(
        command,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False,
        cwd=cwd or ROOT  # Sempre executa da raiz do projeto
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
    
    # Mudar para a raiz do projeto
    os.chdir(ROOT)
    print(f"📍 Diretório atual: {os.getcwd()}")
    
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
            [PYTHON, p("scripts", "ranking", "rank.py")]
        ),
        (
            "Aplicação do limiar editorial (Modo 3)",
            [PYTHON, p("scripts", "editorial", "apply_threshold.py")]
        ),
    ]
    
    for label, command in steps:
        run_step(label, command)
    
    print("\n" + "=" * 50)
    print("🎉 Pipeline finalizado com sucesso!")
    print("=" * 50)
    print("\n📄 Arquivo pronto para upload:")
    print(f"   → {p('data', 'inbox', 'rascunhos.json')}")
    print("\n💡 Próximo passo: upload para o Hostinger")

if __name__ == "__main__":
    main()