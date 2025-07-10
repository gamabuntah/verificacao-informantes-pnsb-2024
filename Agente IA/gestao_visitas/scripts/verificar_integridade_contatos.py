import os
import sys
import pandas as pd
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from app import app, db
from gestao_visitas.models.contatos import Contato

def normalizar_valor(valor):
    """Normaliza um valor para comparação."""
    if pd.isna(valor) or valor == '':
        return None
    return str(valor).strip()

def formatar_valor(valor):
    """Formata um valor para exibição."""
    if valor is None:
        return "VAZIO"
    return str(valor)

def comparar_valores(valor_banco, valor_csv, campo, municipio, tipo_pesquisa):
    """Compara valores do banco e do CSV, retornando True se forem iguais."""
    valor_banco_norm = normalizar_valor(valor_banco)
    valor_csv_norm = normalizar_valor(valor_csv)
    
    if valor_banco_norm != valor_csv_norm:
        print(f"\n{'='*80}")
        print(f"Divergência encontrada para {municipio} ({tipo_pesquisa}) - Campo: {campo}")
        print(f"Valor no banco: {formatar_valor(valor_banco_norm)}")
        print(f"Valor no CSV: {formatar_valor(valor_csv_norm)}")
        print(f"{'='*80}\n")
        return False
    return True

def ler_csvs():
    """Lê todos os arquivos CSV e retorna um dicionário com os dados."""
    csv_dir = root_dir / 'gestao_visitas' / 'pesquisa_contatos_prefeituras'
    arquivos_csv = list(csv_dir.glob('*.csv'))
    dados_csv = {}
    
    for arquivo in arquivos_csv:
        print(f"\nLendo arquivo: {arquivo.name}")
        tipo_pesquisa = 'MRS' if 'MRS' in arquivo.name else 'MAP'
        df = pd.read_csv(arquivo, encoding='latin1')
        
        for _, row in df.iterrows():
            municipio = row['Município']
            campo = row['Campo']
            
            if pd.isna(municipio) or pd.isna(campo):
                continue
            
            chave = f"{municipio}_{tipo_pesquisa}"
            if chave not in dados_csv:
                dados_csv[chave] = {
                    'municipio': municipio,
                    'tipo_pesquisa': tipo_pesquisa,
                    'campos': {}
                }
            
            campo_lower = campo.lower()
            campo_lower_sem_acentos = (campo_lower
                .replace('á', 'a').replace('ã', 'a').replace('â', 'a')
                .replace('é', 'e').replace('ê', 'e')
                .replace('í', 'i')
                .replace('ó', 'o').replace('õ', 'o').replace('ô', 'o')
                .replace('ú', 'u')
                .replace('ç', 'c'))
            dados_csv[chave]['campos'][campo_lower] = {
                'chatgpt': row['ChatGPT'],
                'gemini': row['Gemini'],
                'grok': row['Grok'],
                'mais_provavel': row['Mais provável']
            }
            # Também salva a versão sem acentos para busca flexível
            dados_csv[chave]['campos'][campo_lower_sem_acentos] = dados_csv[chave]['campos'][campo_lower]
    
    return dados_csv

def buscar_campo_flexivel(campos_dict, nome_campo):
    """Busca o campo no dicionário aceitando com e sem acento."""
    nome_campo_sem_acentos = (nome_campo
        .replace('á', 'a').replace('ã', 'a').replace('â', 'a')
        .replace('é', 'e').replace('ê', 'e')
        .replace('í', 'i')
        .replace('ó', 'o').replace('õ', 'o').replace('ô', 'o')
        .replace('ú', 'u')
        .replace('ç', 'c'))
    if nome_campo in campos_dict:
        return campos_dict[nome_campo]
    if nome_campo_sem_acentos in campos_dict:
        return campos_dict[nome_campo_sem_acentos]
    return None

def verificar_integridade():
    """Verifica a integridade dos dados entre o banco e os CSVs."""
    print("Iniciando verificação de integridade...")
    
    with app.app_context():
        # Ler dados do banco
        contatos_banco = Contato.query.all()
        print(f"\nTotal de contatos no banco: {len(contatos_banco)}")
        
        # Ler dados dos CSVs
        dados_csv = ler_csvs()
        print(f"Total de municípios nos CSVs: {len(dados_csv)}")
        
        # Contadores
        total_campos = 0
        divergencias = 0
        
        # Verificar cada contato do banco
        for contato in contatos_banco:
            chave = f"{contato.municipio}_{contato.tipo_pesquisa}"
            if chave not in dados_csv:
                print(f"\n[ERRO] Município {contato.municipio} ({contato.tipo_pesquisa}) não encontrado nos CSVs!")
                continue
            
            dados_municipio = dados_csv[chave]
            
            # Verificar cada campo
            campos = {
                'local': {
                    'chatgpt': contato.local_chatgpt,
                    'gemini': contato.local_gemini,
                    'grok': contato.local_grok,
                    'mais_provavel': contato.local_mais_provavel
                },
                'responsável': {
                    'chatgpt': contato.responsavel_chatgpt,
                    'gemini': contato.responsavel_gemini,
                    'grok': contato.responsavel_grok,
                    'mais_provavel': contato.responsavel_mais_provavel
                },
                'endereço': {
                    'chatgpt': contato.endereco_chatgpt,
                    'gemini': contato.endereco_gemini,
                    'grok': contato.endereco_grok,
                    'mais_provavel': contato.endereco_mais_provavel
                },
                'contato': {
                    'chatgpt': contato.contato_chatgpt,
                    'gemini': contato.contato_gemini,
                    'grok': contato.contato_grok,
                    'mais_provavel': contato.contato_mais_provavel
                },
                'horário': {
                    'chatgpt': contato.horario_chatgpt,
                    'gemini': contato.horario_gemini,
                    'grok': contato.horario_grok,
                    'mais_provavel': contato.horario_mais_provavel
                }
            }
            
            for campo, valores in campos.items():
                dados_csv_campo = buscar_campo_flexivel(dados_municipio['campos'], campo)
                if not dados_csv_campo:
                    print(f"\n[ERRO] Campo '{campo}' não encontrado no CSV para {contato.municipio} ({contato.tipo_pesquisa})!")
                    continue
                
                for fonte in ['chatgpt', 'gemini', 'grok', 'mais_provavel']:
                    total_campos += 1
                    if not comparar_valores(
                        valores[fonte],
                        dados_csv_campo[fonte],
                        f"{campo} ({fonte})",
                        contato.municipio,
                        contato.tipo_pesquisa
                    ):
                        divergencias += 1
        
        # Resumo
        print("\n" + "="*50)
        print("RESUMO DA VERIFICAÇÃO")
        print("="*50)
        print(f"Total de campos verificados: {total_campos}")
        print(f"Total de divergências encontradas: {divergencias}")
        print("="*50 + "\n")

if __name__ == '__main__':
    verificar_integridade() 