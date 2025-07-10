#!/usr/bin/env python3
"""
Script para debug do erro "'int' object has no attribute 'get'"
"""

import sys
import traceback
import sqlite3
from gestao_visitas.services.route_optimizer import RouteOptimizer
from gestao_visitas.services.route_optimizer import RoutePoint

# Mock do app context para teste
class MockApp:
    def __init__(self):
        self.config = {}

def debug_route_optimization():
    print("🔍 DEBUG: Iniciando teste direto do RouteOptimizer")
    
    try:
        # Criar instância do otimizador
        optimizer = RouteOptimizer()
        print("✅ RouteOptimizer criado com sucesso")
        
        # Simular visitas do banco de dados
        conn = sqlite3.connect('gestao_visitas/gestao_visitas.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, local, municipio FROM visitas LIMIT 2')
        visitas_data = cursor.fetchall()
        conn.close()
        
        print(f"📊 Dados das visitas: {visitas_data}")
        
        # Criar RoutePoints simples
        points = []
        for i, (id_visita, local, municipio) in enumerate(visitas_data):
            point = RoutePoint(
                id=f"visita_{id_visita}",
                name=local or f"Local {id_visita}",
                lat=-26.9 - i * 0.1,  # Coordenadas fictícias
                lng=-48.6 - i * 0.1,
                municipality=municipio,
                priority=1,
                estimated_duration=90
            )
            points.append(point)
            print(f"✅ RoutePoint criado: {point.id} - {point.name}")
        
        print(f"🎯 Testando com {len(points)} pontos")
        
        # Testar método diretamente
        print("🧪 Testando otimização...")
        result = optimizer.optimize_route_with_google_maps(
            points=points, 
            target_date="2025-07-08",
            start_time="08:00",
            end_time="17:00",
            include_business_hours=True
        )
        
        print(f"✅ Resultado: {result.get('sucesso', False)}")
        if not result.get('sucesso'):
            print(f"❌ Erro: {result.get('erro', 'Desconhecido')}")
        
        return result
        
    except Exception as e:
        print(f"❌ ERRO CAPTURADO: {e}")
        print(f"📍 Tipo do erro: {type(e)}")
        print("📋 Traceback completo:")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Configurar Flask app context mock
    from flask import Flask
    app = Flask(__name__)
    app.config['GOOGLE_MAPS_API_KEY'] = ''  # Vazio para teste
    
    with app.app_context():
        result = debug_route_optimization()