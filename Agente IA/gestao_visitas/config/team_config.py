# Configuração da Equipe PNSB 2024 - Santa Catarina
"""
Configurações da equipe de pesquisadores para o projeto PNSB 2024.
Estas configurações são usadas em todo o sistema para cálculos de capacidade,
estimativas e métricas de produtividade.
"""

from datetime import datetime, time

# =============================================================================
# CONFIGURAÇÃO DA EQUIPE
# =============================================================================

# Número total de pesquisadores ativos no projeto
NUM_PESQUISADORES = 1

# Pesquisador principal responsável
PESQUISADOR_PRINCIPAL = "Pesquisador PNSB 1"

# =============================================================================
# HORÁRIOS DE TRABALHO
# =============================================================================

# Horário de início do trabalho de campo
HORARIO_INICIO = time(8, 0)  # 08:00

# Horário de fim do trabalho de campo  
HORARIO_FIM = time(18, 0)   # 18:00

# Total de horas de trabalho por dia
HORAS_TRABALHO_DIA = 10

# =============================================================================
# CAPACIDADE DE VISITAS
# =============================================================================

# Duração média por visita (em minutos)
MINUTOS_POR_VISITA = 60

# Tempo para deslocamento entre visitas (em minutos)
MINUTOS_DESLOCAMENTO = 15

# Tempo total por visita incluindo deslocamento
MINUTOS_TOTAIS_POR_VISITA = MINUTOS_POR_VISITA + MINUTOS_DESLOCAMENTO

# Capacidade máxima de visitas por dia por pesquisador
VISITAS_MAX_POR_DIA = int((HORAS_TRABALHO_DIA * 60) // MINUTOS_TOTAIS_POR_VISITA)  # ~8 visitas/dia

# Capacidade total da equipe por dia
CAPACIDADE_TOTAL_DIA = NUM_PESQUISADORES * VISITAS_MAX_POR_DIA

# =============================================================================
# PRAZOS DO PROJETO
# =============================================================================

# Data limite para conclusão das visitas P1+P2
DEADLINE_VISITAS = datetime(2025, 9, 19)

# Data limite para finalização dos questionários
DEADLINE_QUESTIONARIOS = datetime(2025, 10, 17)

# Data de entrega final do projeto
DEADLINE_FINALIZACAO = datetime(2025, 12, 15)

# =============================================================================
# MÉTRICAS DE EFICIÊNCIA
# =============================================================================

# Percentual de capacidade considerado como sobrecarga
LIMITE_SOBRECARGA = 0.80  # 80%

# Meta de eficiência da equipe
META_EFICIENCIA = 0.85  # 85%

# Número mínimo de visitas por semana para manter cronograma
VISITAS_MIN_SEMANA = 25  # ~5 visitas/dia útil

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def get_dias_restantes_visitas():
    """Calcula quantos dias restam para o deadline das visitas."""
    hoje = datetime.now()
    return (DEADLINE_VISITAS - hoje).days

def get_dias_restantes_questionarios():
    """Calcula quantos dias restam para o deadline dos questionários."""
    hoje = datetime.now()
    return (DEADLINE_QUESTIONARIOS - hoje).days

def calcular_capacidade_restante():
    """Calcula a capacidade total restante até o deadline das visitas."""
    dias_restantes = get_dias_restantes_visitas()
    # Considerando 5 dias úteis por semana
    dias_uteis = int(dias_restantes * (5/7))
    return dias_uteis * CAPACIDADE_TOTAL_DIA

def get_team_summary():
    """Retorna um resumo das configurações da equipe."""
    return {
        'num_pesquisadores': NUM_PESQUISADORES,
        'pesquisador_principal': PESQUISADOR_PRINCIPAL,
        'horario_inicio': HORARIO_INICIO.strftime('%H:%M'),
        'horario_fim': HORARIO_FIM.strftime('%H:%M'),
        'horas_trabalho_dia': HORAS_TRABALHO_DIA,
        'minutos_por_visita': MINUTOS_POR_VISITA,
        'visitas_max_dia': VISITAS_MAX_POR_DIA,
        'capacidade_total_dia': CAPACIDADE_TOTAL_DIA,
        'deadline_visitas': DEADLINE_VISITAS.strftime('%d/%m/%Y'),
        'deadline_questionarios': DEADLINE_QUESTIONARIOS.strftime('%d/%m/%Y'),
        'dias_restantes_visitas': get_dias_restantes_visitas(),
        'dias_restantes_questionarios': get_dias_restantes_questionarios(),
        'capacidade_restante': calcular_capacidade_restante()
    }

if __name__ == "__main__":
    # Exemplo de uso
    import json
    print(json.dumps(get_team_summary(), indent=2, ensure_ascii=False))