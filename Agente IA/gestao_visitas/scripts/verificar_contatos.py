import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from app import app, db
from gestao_visitas.models.contatos import Contato

def verificar_contatos():
    print("Verificando contatos importados...")
    
    with app.app_context():
        # Contar total de contatos
        total_contatos = Contato.query.count()
        print(f"\nTotal de contatos: {total_contatos}")
        
        # Listar todos os contatos
        print("\nListando todos os contatos:")
        contatos = Contato.query.all()
        for contato in contatos:
            print(f"\nMunicípio: {contato.municipio}")
            print(f"Tipo de Pesquisa: {contato.tipo_pesquisa}")
            print(f"Tipo de Entidade: {contato.tipo_entidade}")
            print(f"Local: ChatGPT={contato.local_chatgpt} | Gemini={contato.local_gemini} | Grok={contato.local_grok} | Mais Provável={contato.local_mais_provavel}")
            print(f"Responsável: ChatGPT={contato.responsavel_chatgpt} | Gemini={contato.responsavel_gemini} | Grok={contato.responsavel_grok} | Mais Provável={contato.responsavel_mais_provavel}")
            print(f"Endereço: ChatGPT={contato.endereco_chatgpt} | Gemini={contato.endereco_gemini} | Grok={contato.endereco_grok} | Mais Provável={contato.endereco_mais_provavel}")
            print(f"Contato: ChatGPT={contato.contato_chatgpt} | Gemini={contato.contato_gemini} | Grok={contato.contato_grok} | Mais Provável={contato.contato_mais_provavel}")
            print(f"Horário: ChatGPT={contato.horario_chatgpt} | Gemini={contato.horario_gemini} | Grok={contato.horario_grok} | Mais Provável={contato.horario_mais_provavel}")
            print("-" * 50)

if __name__ == '__main__':
    verificar_contatos() 