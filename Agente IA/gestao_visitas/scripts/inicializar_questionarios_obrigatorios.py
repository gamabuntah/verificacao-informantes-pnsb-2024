"""
Script para inicializar questionários obrigatórios do PNSB 2024
Cria os registros obrigatórios para todos os 11 municípios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from gestao_visitas.db import db
from gestao_visitas.models.questionarios_obrigatorios import QuestionarioObrigatorio, ProgressoQuestionarios
from gestao_visitas.config import MUNICIPIOS
MUNICIPIOS_PNSB = MUNICIPIOS

def inicializar_questionarios_prefeituras():
    """
    Todos os 11 municípios devem ter questionários MRS e MAP obrigatórios para as Prefeituras
    """
    print("🚀 Inicializando questionários obrigatórios para Prefeituras...")
    
    questionarios_criados = 0
    questionarios_atualizados = 0
    
    for municipio in MUNICIPIOS_PNSB:
        print(f"📋 Processando {municipio}...")
        
        # Verificar se já existe
        questionario_existente = QuestionarioObrigatorio.query.filter_by(
            municipio=municipio,
            tipo_entidade='prefeitura'
        ).first()
        
        if questionario_existente:
            # Atualizar para garantir que MRS e MAP sejam obrigatórios
            questionario_existente.mrs_obrigatorio = True
            questionario_existente.map_obrigatorio = True
            questionario_existente.ativo = True
            questionario_existente.observacoes = "Questionários MRS e MAP obrigatórios para todas as prefeituras - PNSB 2024"
            questionarios_atualizados += 1
            print(f"  ✅ Atualizado: {municipio} - Prefeitura")
        else:
            # Criar novo registro
            novo_questionario = QuestionarioObrigatorio(
                municipio=municipio,
                tipo_entidade='prefeitura',
                mrs_obrigatorio=True,
                map_obrigatorio=True,
                ativo=True,
                observacoes="Questionários MRS e MAP obrigatórios para todas as prefeituras - PNSB 2024"
            )
            db.session.add(novo_questionario)
            questionarios_criados += 1
            print(f"  🆕 Criado: {municipio} - Prefeitura")
    
    # Commit das mudanças
    db.session.commit()
    
    print(f"✅ Processamento concluído:")
    print(f"   📊 {questionarios_criados} questionários criados")
    print(f"   🔄 {questionarios_atualizados} questionários atualizados")
    print(f"   🎯 Total: {len(MUNICIPIOS_PNSB)} municípios configurados")
    
    return questionarios_criados, questionarios_atualizados

def calcular_progresso_inicial():
    """
    Calcula o progresso inicial para todos os municípios
    """
    print("📊 Calculando progresso inicial...")
    
    for municipio in MUNICIPIOS_PNSB:
        progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
        print(f"  📈 {municipio}: {progresso.total_mrs_obrigatorios} MRS + {progresso.total_map_obrigatorios} MAP obrigatórios")
    
    print("✅ Progresso inicial calculado!")

def listar_questionarios_obrigatorios():
    """
    Lista todos os questionários obrigatórios configurados
    """
    print("📋 Questionários obrigatórios configurados:")
    print("-" * 80)
    
    questionarios = QuestionarioObrigatorio.query.filter_by(ativo=True).order_by(
        QuestionarioObrigatorio.municipio,
        QuestionarioObrigatorio.tipo_entidade
    ).all()
    
    municipio_atual = ""
    for q in questionarios:
        if q.municipio != municipio_atual:
            print(f"\n🏛️ {q.municipio}:")
            municipio_atual = q.municipio
        
        tipos = []
        if q.mrs_obrigatorio:
            tipos.append("MRS")
        if q.map_obrigatorio:
            tipos.append("MAP")
        
        tipo_entidade_label = {
            'prefeitura': 'Prefeitura',
            'empresa_terceirizada': 'Empresa Terceirizada',
            'entidade_catadores': 'Entidade de Catadores',
            'empresa_nao_vinculada': 'Empresa Não Vinculada'
        }.get(q.tipo_entidade, q.tipo_entidade)
        
        print(f"  📋 {tipo_entidade_label}: {' + '.join(tipos)}")

def main():
    """
    Função principal do script
    """
    print("=" * 80)
    print("🏛️ INICIALIZAÇÃO DE QUESTIONÁRIOS OBRIGATÓRIOS - PNSB 2024")
    print("=" * 80)
    
    try:
        # Inicializar questionários das prefeituras
        inicializar_questionarios_prefeituras()
        
        # Calcular progresso inicial
        calcular_progresso_inicial()
        
        # Listar configuração final
        listar_questionarios_obrigatorios()
        
        print("\n" + "=" * 80)
        print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erro durante a inicialização: {str(e)}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    # Importar app para contexto do Flask
    from app import app
    
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        
        # Executar inicialização
        main()