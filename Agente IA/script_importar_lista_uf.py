#!/usr/bin/env python3
"""
Script para importar lista de entidades prioritárias da UF
Uso: python script_importar_lista_uf.py arquivo.csv
"""

import sys
import requests
import pandas as pd
from pathlib import Path

def importar_lista_uf(arquivo_csv, base_url="http://localhost:5000"):
    """
    Importa lista de entidades prioritárias da UF via API
    """
    try:
        # Verificar se arquivo existe
        if not Path(arquivo_csv).exists():
            print(f"❌ Arquivo não encontrado: {arquivo_csv}")
            return False
        
        print(f"📁 Importando arquivo: {arquivo_csv}")
        
        # Preparar o arquivo para upload
        with open(arquivo_csv, 'rb') as f:
            files = {'arquivo': (arquivo_csv, f, 'text/csv')}
            
            # Fazer a requisição
            response = requests.post(
                f"{base_url}/api/questionarios/importar-lista-uf",
                files=files,
                timeout=30
            )
        
        # Processar resposta
        if response.status_code == 200:
            resultado = response.json()
            
            if resultado['success']:
                print("✅ Importação realizada com sucesso!")
                print(f"📊 Resultados:")
                print(f"   • {resultado['entidades_criadas']} entidades criadas")
                print(f"   • {resultado['entidades_atualizadas']} entidades atualizadas")
                
                if resultado.get('erros'):
                    print(f"⚠️  {resultado['total_erros']} erros encontrados:")
                    for erro in resultado['erros'][:5]:  # Mostrar apenas os primeiros 5
                        print(f"   • {erro}")
                
                return True
            else:
                print(f"❌ Erro na importação: {resultado.get('error', 'Erro desconhecido')}")
                return False
        else:
            print(f"❌ Erro HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão: {str(e)}")
        print("💡 Certifique-se de que o servidor Flask está rodando em http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

def validar_csv(arquivo_csv):
    """
    Valida a estrutura do CSV antes da importação
    """
    try:
        print(f"🔍 Validando estrutura do arquivo: {arquivo_csv}")
        
        # Ler CSV
        df = pd.read_csv(arquivo_csv)
        
        # Campos obrigatórios
        campos_obrigatorios = ['codigo_uf', 'municipio', 'nome_entidade', 'tipo_entidade']
        
        # Verificar campos obrigatórios
        campos_faltando = [campo for campo in campos_obrigatorios if campo not in df.columns]
        if campos_faltando:
            print(f"❌ Campos obrigatórios faltando: {', '.join(campos_faltando)}")
            return False
        
        # Verificar municípios válidos
        municipios_validos = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas',
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves',
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        municipios_invalidos = df[~df['municipio'].isin(municipios_validos)]['municipio'].unique()
        if len(municipios_invalidos) > 0:
            print(f"⚠️  Municípios inválidos encontrados: {', '.join(municipios_invalidos)}")
            print(f"✅ Municípios válidos: {', '.join(municipios_validos)}")
        
        # Verificar tipos de entidade válidos
        tipos_validos = ['empresa_terceirizada', 'entidade_catadores', 'empresa_nao_vinculada']
        tipos_invalidos = df[~df['tipo_entidade'].isin(tipos_validos)]['tipo_entidade'].unique()
        if len(tipos_invalidos) > 0:
            print(f"⚠️  Tipos de entidade inválidos: {', '.join(tipos_invalidos)}")
            print(f"✅ Tipos válidos: {', '.join(tipos_validos)}")
        
        # Verificar códigos UF únicos
        codigos_duplicados = df[df['codigo_uf'].duplicated()]['codigo_uf'].unique()
        if len(codigos_duplicados) > 0:
            print(f"⚠️  Códigos UF duplicados: {', '.join(codigos_duplicados)}")
        
        print(f"✅ Arquivo contém {len(df)} linhas")
        print(f"✅ Validação concluída")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao validar CSV: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("📋 IMPORTADOR DE LISTA UF - ENTIDADES PRIORITÁRIAS")
    print("=" * 60)
    
    if len(sys.argv) != 2:
        print("❌ Uso incorreto!")
        print("✅ Uso correto: python script_importar_lista_uf.py arquivo.csv")
        print("\n📝 Exemplo:")
        print("   python script_importar_lista_uf.py exemplo_lista_uf.csv")
        sys.exit(1)
    
    arquivo_csv = sys.argv[1]
    
    # Validar CSV primeiro
    if not validar_csv(arquivo_csv):
        print("❌ Validação falhou. Corrija os erros antes de importar.")
        sys.exit(1)
    
    # Confirmar importação
    resposta = input("\n🤔 Deseja prosseguir com a importação? (s/N): ").lower()
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("❌ Importação cancelada pelo usuário.")
        sys.exit(0)
    
    # Executar importação
    sucesso = importar_lista_uf(arquivo_csv)
    
    if sucesso:
        print("\n🎉 Importação concluída com sucesso!")
        print("💡 Acesse /questionarios-obrigatorios para ver as entidades importadas")
        print("💡 Use 'Processar Todas' para ativar as entidades no sistema")
    else:
        print("\n❌ Importação falhou. Verifique os erros acima.")
        sys.exit(1)

if __name__ == "__main__":
    main()