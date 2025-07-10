import os
import csv

arquivos = [
    ('MAP', 'gestao_visitas/pesquisa_contatos_prefeituras/Comparacao_MAP.csv'),
    ('MRS', 'gestao_visitas/pesquisa_contatos_prefeituras/Comparacao_MRS.csv')
]

total_linhas = 0
municipios = set()
campos = set()

for tipo, caminho in arquivos:
    print(f'=== Arquivo {tipo} ===')
    try:
        with open(caminho, encoding='latin1') as f:
            reader = csv.DictReader(f)
            linhas_arquivo = 0
            for row in reader:
                municipio = row.get('Município', '').strip()
                campo = row.get('Campo', '').strip()
                
                if municipio and municipio != 'Município':
                    municipios.add(municipio)
                    linhas_arquivo += 1
                    total_linhas += 1
                    
                if campo:
                    campos.add(campo)
                    
                # Mostrar primeira linha com dados reais
                if linhas_arquivo == 1 and municipio:
                    print(f'Primeira linha: Município={municipio}, Campo={campo}')
                    print(f'ChatGPT: {row.get("ChatGPT", "")}')
                    print(f'Gemini: {row.get("Gemini", "")}')
                    print(f'Grok: {row.get("Grok", "")}')
                    print(f'Mais provável: {row.get("Mais provável", "")}')
                    
            print(f'Linhas válidas: {linhas_arquivo}')
    except Exception as e:
        print(f'Erro ao ler {caminho}: {e}')

print(f'\n=== RESUMO GERAL ===')
print(f'Total de linhas: {total_linhas}')
print(f'Municípios únicos: {len(municipios)}')
print(f'Municípios: {sorted(municipios)}')
print(f'Campos: {sorted(campos)}')

# Verificar quantos contatos únicos deveríamos ter
contatos_esperados = len(municipios) * 2  # MAP + MRS para cada município
print(f'Contatos esperados (município x tipo): {contatos_esperados}')