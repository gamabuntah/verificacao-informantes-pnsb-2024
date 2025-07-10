#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3
from datetime import datetime, timedelta
import json

# Adicionar o caminho para importar os módulos
sys.path.append('/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA')

def analisar_visitas_follow_up():
    """Analisa visitas em status 'em follow-up' e sugere próximas ações"""
    
    db_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/gestao_visitas.db"
    
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado: {db_path}")
        return
    
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Buscar visitas em follow-up
    query = '''
    SELECT 
        id, 
        municipio, 
        local, 
        data, 
        data_criacao, 
        observacoes, 
        data_atualizacao, 
        status,
        tipo_pesquisa,
        hora_inicio,
        hora_fim
    FROM visitas 
    WHERE status = 'em follow-up'
    ORDER BY data;
    '''
    
    cursor.execute(query)
    visitas = cursor.fetchall()
    
    print(f"📋 ANÁLISE DE VISITAS EM FOLLOW-UP")
    print(f"=" * 60)
    print(f"Total de visitas encontradas: {len(visitas)}")
    print(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"=" * 60)
    
    if not visitas:
        print("❌ Nenhuma visita encontrada com status 'em follow-up'")
        conn.close()
        return
    
    hoje = datetime.now().date()
    recomendacoes = []
    
    for i, visita in enumerate(visitas, 1):
        id_visita = visita[0]
        municipio = visita[1]
        local = visita[2]
        data_visita = visita[3]
        data_criacao = visita[4]
        observacoes = visita[5] or ""
        data_atualizacao = visita[6]
        status = visita[7]
        tipo_pesquisa = visita[8]
        hora_inicio = visita[9]
        hora_fim = visita[10]
        
        print(f"\n🔍 VISITA {i}: ID {id_visita}")
        print(f"   Município: {municipio}")
        print(f"   Local: {local}")
        print(f"   Data prevista: {data_visita}")
        print(f"   Data criação: {data_criacao}")
        print(f"   Tipo pesquisa: {tipo_pesquisa}")
        print(f"   Horário: {hora_inicio} - {hora_fim}")
        print(f"   Observações: {observacoes}")
        
        # Analisar situação
        situacao = "indefinida"
        proxima_acao = "verificar manualmente"
        prioridade = "média"
        
        # Converter data_visita para objeto date se necessário
        if data_visita:
            try:
                if isinstance(data_visita, str):
                    if '.' in data_visita:
                        data_visita_obj = datetime.strptime(data_visita.split('.')[0], "%Y-%m-%d %H:%M:%S").date()
                    else:
                        data_visita_obj = datetime.strptime(data_visita, "%Y-%m-%d").date()
                else:
                    data_visita_obj = data_visita
            except:
                data_visita_obj = None
        else:
            data_visita_obj = None
        
        # Análise baseada na data e observações
        if data_visita_obj:
            dias_desde_visita = (hoje - data_visita_obj).days
            
            if dias_desde_visita > 14:
                situacao = "muito_atrasada"
                proxima_acao = "verificação whatsapp urgente"
                prioridade = "alta"
            elif dias_desde_visita > 7:
                situacao = "atrasada"
                proxima_acao = "verificação whatsapp"
                prioridade = "alta"
            elif dias_desde_visita > 3:
                situacao = "precisa_contato"
                proxima_acao = "verificação whatsapp"
                prioridade = "média"
            elif dias_desde_visita > 0:
                situacao = "aguardando_resposta"
                proxima_acao = "aguardar mais 1-2 dias"
                prioridade = "baixa"
            else:
                situacao = "futura"
                proxima_acao = "manter follow-up"
                prioridade = "baixa"
        
        # Análise baseada nas observações
        obs_lower = observacoes.lower()
        
        if any(palavra in obs_lower for palavra in ['confirmad', 'agendad', 'marcad']):
            situacao = "confirmada"
            proxima_acao = "agendada"
            prioridade = "baixa"
        elif any(palavra in obs_lower for palavra in ['não respond', 'sem resposta', 'não atend']):
            situacao = "sem_resposta"
            proxima_acao = "verificação whatsapp"
            prioridade = "alta"
        elif any(palavra in obs_lower for palavra in ['cancelad', 'desmarcad', 'remarcad']):
            situacao = "cancelada"
            proxima_acao = "reagendar"
            prioridade = "média"
        elif any(palavra in obs_lower for palavra in ['whatsapp', 'mensagem', 'msg']):
            situacao = "contato_whatsapp"
            proxima_acao = "verificação whatsapp"
            prioridade = "média"
        elif any(palavra in obs_lower for palavra in ['telefone', 'ligar', 'ligação']):
            situacao = "contato_telefone"
            proxima_acao = "verificação whatsapp"
            prioridade = "média"
        elif any(palavra in obs_lower for palavra in ['problema', 'erro', 'incorret']):
            situacao = "problema_dados"
            proxima_acao = "novo local"
            prioridade = "alta"
        elif any(palavra in obs_lower for palavra in ['ficou de responder', 'vai responder', 'irá responder']):
            # Análise específica para compromissos assumidos
            if data_visita_obj and dias_desde_visita > 7:
                situacao = "compromisso_nao_cumprido"
                proxima_acao = "verificação whatsapp"
                prioridade = "alta"
            else:
                situacao = "compromisso_assumido"
                proxima_acao = "verificação whatsapp"
                prioridade = "média"
        elif any(palavra in obs_lower for palavra in ['verificar', 'checar', 'consultar']):
            situacao = "pendencia_verificacao"
            proxima_acao = "verificação whatsapp"
            prioridade = "média"
        
        # Definir próximo status baseado na análise
        if proxima_acao == "agendada":
            proximo_status = "agendada"
        elif proxima_acao == "verificação whatsapp":
            proximo_status = "verificação whatsapp"
        elif proxima_acao == "novo local":
            proximo_status = "preparação"
        elif proxima_acao == "reagendar":
            proximo_status = "preparação"
        else:
            proximo_status = "em follow-up"
        
        print(f"   ⚠️  Situação: {situacao}")
        print(f"   🎯 Próxima ação: {proxima_acao}")
        print(f"   📊 Prioridade: {prioridade}")
        print(f"   🔄 Próximo status: {proximo_status}")
        
        # Gerar recomendação específica
        if data_visita_obj:
            dias_texto = f"({dias_desde_visita} dias atrás)"
        else:
            dias_texto = ""
        
        if situacao == "compromisso_nao_cumprido":
            recomendacao = f"URGENTE: {local} assumiu compromisso há {dias_desde_visita} dias e não cumpriu. Enviar WhatsApp cobrando resposta."
        elif situacao == "compromisso_assumido":
            recomendacao = f"Enviar WhatsApp para {local} lembrando do compromisso assumido de responder o questionário."
        elif situacao == "pendencia_verificacao":
            recomendacao = f"Entrar em contato com {local} para verificar pendência mencionada nas observações."
        elif situacao == "atrasada":
            recomendacao = f"Visita está atrasada {dias_texto}. Enviar WhatsApp para verificar status da resposta."
        elif situacao == "muito_atrasada":
            recomendacao = f"CRÍTICO: Visita muito atrasada {dias_texto}. Contato urgente necessário."
        else:
            recomendacao = f"Monitorar situação e entrar em contato conforme necessário."
        
        print(f"   💡 Recomendação: {recomendacao}")
        
        # Adicionar às recomendações
        recomendacoes.append({
            'id': id_visita,
            'municipio': municipio,
            'local': local,
            'data_visita': data_visita,
            'situacao': situacao,
            'proxima_acao': proxima_acao,
            'prioridade': prioridade,
            'proximo_status': proximo_status,
            'observacoes': observacoes
        })
    
    # Resumo por prioridade
    print(f"\n📊 RESUMO POR PRIORIDADE")
    print(f"=" * 40)
    
    alta_prioridade = [r for r in recomendacoes if r['prioridade'] == 'alta']
    media_prioridade = [r for r in recomendacoes if r['prioridade'] == 'média']
    baixa_prioridade = [r for r in recomendacoes if r['prioridade'] == 'baixa']
    
    print(f"🔴 Alta prioridade: {len(alta_prioridade)} visitas")
    for v in alta_prioridade:
        print(f"   - ID {v['id']}: {v['municipio']} - {v['proxima_acao']}")
    
    print(f"\n🟡 Média prioridade: {len(media_prioridade)} visitas")
    for v in media_prioridade:
        print(f"   - ID {v['id']}: {v['municipio']} - {v['proxima_acao']}")
    
    print(f"\n🟢 Baixa prioridade: {len(baixa_prioridade)} visitas")
    for v in baixa_prioridade:
        print(f"   - ID {v['id']}: {v['municipio']} - {v['proxima_acao']}")
    
    # Resumo por ação
    print(f"\n🎯 RESUMO POR AÇÃO NECESSÁRIA")
    print(f"=" * 40)
    
    acoes = {}
    for r in recomendacoes:
        acao = r['proxima_acao']
        if acao not in acoes:
            acoes[acao] = []
        acoes[acao].append(r)
    
    for acao, visitas_acao in acoes.items():
        print(f"\n📋 {acao.upper()}: {len(visitas_acao)} visitas")
        for v in visitas_acao:
            print(f"   - ID {v['id']}: {v['municipio']} ({v['prioridade']} prioridade)")
    
    # Salvar relatório em JSON
    relatorio = {
        'data_analise': datetime.now().isoformat(),
        'total_visitas': len(visitas),
        'recomendacoes': recomendacoes,
        'resumo_prioridade': {
            'alta': len(alta_prioridade),
            'media': len(media_prioridade),
            'baixa': len(baixa_prioridade)
        },
        'resumo_acoes': {acao: len(visitas_acao) for acao, visitas_acao in acoes.items()}
    }
    
    # Salvar no arquivo
    relatorio_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/relatorio_follow_up.json"
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório salvo em: {relatorio_path}")
    
    conn.close()
    
    return recomendacoes

if __name__ == "__main__":
    analisar_visitas_follow_up()