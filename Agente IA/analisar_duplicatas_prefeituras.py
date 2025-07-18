#!/usr/bin/env python3
"""
Análise completa de entidades prefeituras duplicadas
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'gestao_visitas'))

# Import Flask app and create context
from app import app
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada

def analisar_duplicatas():
    """Analisa todas as duplicatas de prefeituras no sistema"""
    
    with app.app_context():
        # Lista dos 11 municípios do PNSB 2024
        municipalities = [
            'Bombinhas', 'Balneário Camboriú', 'Balneário Piçarras', 
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves', 
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        duplicates_analysis = {}
        total_prefeituras = 0
        
        for muni in municipalities:
            # Buscar todas as entidades que contenham "refeitura" no nome
            prefeituras = EntidadeIdentificada.query.filter(
                EntidadeIdentificada.municipio == muni,
                EntidadeIdentificada.nome_entidade.like('%refeitura%')
            ).all()
            
            total_prefeituras += len(prefeituras)
            
            if len(prefeituras) >= 1:  # Incluir todos os municípios
                duplicates_analysis[muni] = []
                for p in prefeituras:
                    duplicates_analysis[muni].append({
                        'id': p.id,
                        'nome': p.nome_entidade,
                        'fonte': p.fonte_identificacao or 'sem_fonte',
                        'mrs_status': p.status_mrs or 'sem_status',
                        'map_status': p.status_map or 'sem_status',
                        'visita_id': p.visita_id or 'sem_visita',
                        'origem_prefeitura': p.origem_prefeitura,
                        'prioridade': p.prioridade,
                        'criado_em': p.criado_em
                    })
        
        print('=' * 60)
        print('ANÁLISE COMPLETA DE ENTIDADES PREFEITURAS')
        print('=' * 60)
        
        municipios_com_duplicatas = 0
        
        for muni, prefeituras in duplicates_analysis.items():
            status_icon = "⚠️" if len(prefeituras) > 1 else "✅"
            print(f'\n{status_icon} {muni}: {len(prefeituras)} entidade(s)')
            
            if len(prefeituras) > 1:
                municipios_com_duplicatas += 1
                
                # Identificar quais manter baseado nos critérios do usuário
                print("   CRITÉRIOS DE ANÁLISE:")
                for i, pref in enumerate(prefeituras, 1):
                    # Identificar características especiais
                    especial = []
                    if 'vigilância' in pref['nome'].lower():
                        especial.append("VIGILÂNCIA SANITÁRIA")
                    if 'captação' in pref['nome'].lower():
                        especial.append("CAPTAÇÃO")
                    if pref['mrs_status'] != 'sem_status' and pref['mrs_status'] != 'nao_iniciado':
                        especial.append(f"MRS:{pref['mrs_status']}")
                    if pref['map_status'] != 'sem_status' and pref['map_status'] != 'nao_iniciado':
                        especial.append(f"MAP:{pref['map_status']}")
                    if pref['visita_id'] != 'sem_visita':
                        especial.append(f"VISITA:{pref['visita_id']}")
                    
                    recomendacao = "🔸 MANTER" if especial else "🔹 CANDIDATO REMOÇÃO"
                    if muni == 'Bombinhas' and ('vigilância' in pref['nome'].lower() or 'captação' in pref['nome'].lower()):
                        recomendacao = "🔺 MANTER (ESPECIFICADO USUÁRIO)"
                    
                    print(f"   {i}. ID:{pref['id']} - {pref['nome']}")
                    print(f"      Fonte: {pref['fonte']} | Status: MRS={pref['mrs_status']}, MAP={pref['map_status']}")
                    print(f"      Especiais: {', '.join(especial) if especial else 'nenhuma'}")
                    print(f"      {recomendacao}")
            else:
                pref = prefeituras[0]
                print(f"   ✅ ID:{pref['id']} - {pref['nome']} (único, OK)")
        
        print('\n' + '=' * 60)
        print('RESUMO GERAL')
        print('=' * 60)
        print(f"Total de municípios analisados: {len(municipalities)}")
        print(f"Municípios com prefeituras: {len(duplicates_analysis)}")
        print(f"Municípios com duplicatas: {municipios_com_duplicatas}")
        print(f"Total de entidades prefeitura: {total_prefeituras}")
        print(f"Entidades esperadas (1 por município): {len(municipalities)}")
        print(f"Entidades excedentes: {total_prefeituras - len(municipalities)}")
        
        # Municípios sem prefeituras
        municipios_sem_prefeitura = set(municipalities) - set(duplicates_analysis.keys())
        if municipios_sem_prefeitura:
            print(f"\n❌ Municípios SEM prefeitura cadastrada:")
            for muni in municipios_sem_prefeitura:
                print(f"   - {muni}")
        
        return duplicates_analysis

if __name__ == '__main__':
    analisar_duplicatas()