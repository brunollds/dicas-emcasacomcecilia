import os
import glob

def copiar_arquivos_js():
    # Encontrar todos os arquivos .js na pasta raiz
    arquivos_js = glob.glob("*.js")
    
    # Verificar se foram encontrados arquivos .js
    if not arquivos_js:
        print("Nenhum arquivo .js encontrado na pasta raiz.")
        return
    
    # Abrir o arquivo de saída para escrita
    with open("todosJS.txt", "w", encoding="utf-8") as arquivo_saida:
        # Para cada arquivo .js encontrado
        for nome_arquivo in arquivos_js:
            try:
                # Abrir o arquivo .js para leitura
                with open(nome_arquivo, "r", encoding="utf-8") as arquivo_js:
                    # Ler o conteúdo do arquivo
                    conteudo = arquivo_js.read()
                    
                    # Escrever o nome do arquivo como título
                    arquivo_saida.write(f"========== {nome_arquivo} ==========\n\n")
                    
                    # Escrever o conteúdo do arquivo
                    arquivo_saida.write(conteudo)
                    
                    # Adicionar linhas em branco para separar os arquivos
                    arquivo_saida.write("\n\n\n")
                    
                print(f"Arquivo {nome_arquivo} copiado com sucesso.")
            except Exception as e:
                print(f"Erro ao copiar o arquivo {nome_arquivo}: {e}")
    
    print(f"Todos os arquivos .js foram copiados para 'todosJS.txt'")

# Executar a função principal
if __name__ == "__main__":
    copiar_arquivos_js()