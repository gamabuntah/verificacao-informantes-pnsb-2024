import os
import sys
import pandas as pd
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from app import app, db
from gestao_visitas.models.contatos import Contato, TipoEntidade

def remover_acentos(texto):
    if not isinstance(texto, str):
        return texto
    return (texto.lower()
        .replace('á', 'a').replace('ã', 'a').replace('â', 'a')
        .replace('é', 'e').replace('ê', 'e')
        .replace('í', 'i')
        .replace('ó', 'o').replace('õ', 'o').replace('ô', 'o')
        .replace('ú', 'u')
        .replace('ç', 'c'))

def importar_contatos():
    print("Iniciando importação de contatos...")
    
    with app.app_context():
        # Criar o banco de dados se não existir
        db.create_all()
        print("Banco de dados criado/verificado com sucesso!")
        # Limpar contatos antigos para evitar duplicidade
        db.session.query(Contato).delete()
        db.session.commit()
        print("Contatos antigos removidos!")
    
        # Diretório dos arquivos CSV
        csv_dir = root_dir / 'gestao_visitas' / 'pesquisa_contatos_prefeituras'
        print(f"Diretório dos arquivos CSV: {csv_dir}")
        
        # Verificar se o diretório existe
        if not csv_dir.exists():
            print(f"Erro: Diretório {csv_dir} não encontrado!")
            return
        
        # Listar arquivos CSV
        arquivos_csv = list(csv_dir.glob('*.csv'))
        print(f"Arquivos CSV encontrados: {[f.name for f in arquivos_csv]}")
        
        # Nomes exatos das colunas do CSV
        COL_MUNICIPIO = 'Município'
        COL_CAMPO = 'Campo'
        COL_CHATGPT = 'ChatGPT'
        COL_GEMINI = 'Gemini'
        COL_GROK = 'Grok'
        COL_MAIS_PROVAVEL = 'Mais provável'
        
        # Processar cada arquivo CSV
        for arquivo in arquivos_csv:
            print(f"\nProcessando arquivo: {arquivo.name}")
            
            # Determinar o tipo de pesquisa baseado no nome do arquivo
            tipo_pesquisa = 'MRS' if 'MRS' in arquivo.name else 'MAP'
            print(f"Tipo de pesquisa: {tipo_pesquisa}")
            
            try:
                # Ler o arquivo CSV com encoding latin1
                df = pd.read_csv(arquivo, encoding='latin1')
                print(f"Arquivo lido com sucesso. Colunas: {df.columns.tolist()}")
                print(f"Número de linhas: {len(df)}")
                
                municipio_atual = None
                contato_atual = None
                contatos_processados = 0
                
                for idx, row in df.iterrows():
                    print(f"Linha {idx}: {row.to_dict()}")
                    try:
                        municipio = row[COL_MUNICIPIO]
                        campo = row[COL_CAMPO]
                        chatgpt = row[COL_CHATGPT]
                        gemini = row[COL_GEMINI]
                        grok = row[COL_GROK]
                        mais_provavel = row[COL_MAIS_PROVAVEL]
                    except Exception as e:
                        print(f"[ERRO] Linha {idx} - Erro ao acessar campos: {e}")
                        continue
                    
                    # Pular linhas vazias
                    if pd.isna(municipio) or pd.isna(campo):
                        print(f"[INFO] Linha {idx} ignorada (município ou campo vazio)")
                        continue
                    
                    # Se é um novo município, criar novo contato
                    if municipio != municipio_atual:
                        if contato_atual:
                            db.session.add(contato_atual)
                            contatos_processados += 1
                            print(f"[OK] Contato salvo para município: {municipio_atual}")
                        contato_atual = Contato(
                            municipio=municipio,
                            tipo_pesquisa=tipo_pesquisa,
                            tipo_entidade=TipoEntidade.PREFEITURA
                        )
                        municipio_atual = municipio
                        print(f"\n[INFO] Novo município: {municipio}")
                    
                    # Atualizar campos do contato atual
                    campo_norm = remover_acentos(campo)
                    if campo_norm == 'local':
                        contato_atual.local_chatgpt = chatgpt if not pd.isna(chatgpt) else None
                        contato_atual.local_gemini = gemini if not pd.isna(gemini) else None
                        contato_atual.local_grok = grok if not pd.isna(grok) else None
                        contato_atual.local_mais_provavel = mais_provavel if not pd.isna(mais_provavel) else None
                    elif campo_norm == 'responsavel':
                        contato_atual.responsavel_chatgpt = chatgpt if not pd.isna(chatgpt) else None
                        contato_atual.responsavel_gemini = gemini if not pd.isna(gemini) else None
                        contato_atual.responsavel_grok = grok if not pd.isna(grok) else None
                        contato_atual.responsavel_mais_provavel = mais_provavel if not pd.isna(mais_provavel) else None
                    elif campo_norm == 'endereco':
                        contato_atual.endereco_chatgpt = chatgpt if not pd.isna(chatgpt) else None
                        contato_atual.endereco_gemini = gemini if not pd.isna(gemini) else None
                        contato_atual.endereco_grok = grok if not pd.isna(grok) else None
                        contato_atual.endereco_mais_provavel = mais_provavel if not pd.isna(mais_provavel) else None
                    elif campo_norm == 'contato':
                        contato_atual.contato_chatgpt = chatgpt if not pd.isna(chatgpt) else None
                        contato_atual.contato_gemini = gemini if not pd.isna(gemini) else None
                        contato_atual.contato_grok = grok if not pd.isna(grok) else None
                        contato_atual.contato_mais_provavel = mais_provavel if not pd.isna(mais_provavel) else None
                    elif campo_norm == 'horario':
                        contato_atual.horario_chatgpt = chatgpt if not pd.isna(chatgpt) else None
                        contato_atual.horario_gemini = gemini if not pd.isna(gemini) else None
                        contato_atual.horario_grok = grok if not pd.isna(grok) else None
                        contato_atual.horario_mais_provavel = mais_provavel if not pd.isna(mais_provavel) else None
                    
                    print(f"[INFO] Campo '{campo}' atualizado para município {municipio}")
                
                # Salvar o último contato
                if contato_atual:
                    db.session.add(contato_atual)
                    contatos_processados += 1
                    print(f"[OK] Contato salvo para município: {municipio_atual}")
                
                # Commit das alterações
                db.session.commit()
                print(f"\n[OK] Arquivo {arquivo.name} processado com sucesso!")
                print(f"Total de contatos processados: {contatos_processados}")
                
            except Exception as e:
                db.session.rollback()
                print(f"[ERRO] Erro ao processar arquivo {arquivo.name}: {str(e)}")
                continue
        
        print("\nImportação concluída!")

if __name__ == '__main__':
    importar_contatos() 