from datetime import datetime
from ..config import ROTEIRO_ABORDAGEM

class RoteiroService:
    def __init__(self):
        self.etapas = ROTEIRO_ABORDAGEM
        self.observacoes = {}

    def iniciar_etapa(self, etapa, observacoes=None):
        """Inicia uma etapa do roteiro com observações opcionais."""
        if etapa not in self.etapas:
            return False

        self.observacoes[etapa] = {
            'inicio': datetime.now(),
            'fim': None,
            'observacoes': observacoes or [],
            'status': 'em_andamento'
        }
        return True

    def finalizar_etapa(self, etapa, observacoes=None):
        """Finaliza uma etapa do roteiro com observações opcionais."""
        if etapa not in self.etapas or etapa not in self.observacoes:
            return False

        if observacoes:
            self.observacoes[etapa]['observacoes'].extend(observacoes)

        self.observacoes[etapa].update({
            'fim': datetime.now(),
            'status': 'concluida'
        })
        return True

    def adicionar_observacao(self, etapa, observacao):
        """Adiciona uma observação a uma etapa específica."""
        if etapa not in self.etapas or etapa not in self.observacoes:
            return False

        self.observacoes[etapa]['observacoes'].append({
            'texto': observacao,
            'data': datetime.now()
        })
        return True

    def obter_progresso(self):
        """Retorna o progresso geral do roteiro."""
        total_etapas = len(self.etapas)
        etapas_concluidas = sum(
            1 for etapa in self.observacoes.values()
            if etapa['status'] == 'concluida'
        )
        return {
            'total_etapas': total_etapas,
            'etapas_concluidas': etapas_concluidas,
            'progresso_percentual': (etapas_concluidas / total_etapas) * 100
        }

    def obter_etapa_atual(self):
        """Retorna a etapa atual do roteiro."""
        for etapa in self.etapas:
            if etapa not in self.observacoes:
                return etapa
            if self.observacoes[etapa]['status'] == 'em_andamento':
                return etapa
        return None

    def obter_duracao_etapa(self, etapa):
        """Calcula a duração de uma etapa específica."""
        if etapa not in self.observacoes:
            return None

        dados = self.observacoes[etapa]
        if not dados['fim']:
            return None

        duracao = dados['fim'] - dados['inicio']
        return {
            'segundos': duracao.total_seconds(),
            'minutos': duracao.total_seconds() / 60,
            'horas': duracao.total_seconds() / 3600
        }

    def obter_resumo(self):
        """Retorna um resumo completo do roteiro."""
        return {
            'etapas': self.etapas,
            'observacoes': self.observacoes,
            'progresso': self.obter_progresso(),
            'etapa_atual': self.obter_etapa_atual(),
            'duracao_total': self._calcular_duracao_total()
        }

    def _calcular_duracao_total(self):
        """Calcula a duração total do roteiro."""
        duracao_total = 0
        for etapa in self.observacoes.values():
            if etapa['fim']:
                duracao = etapa['fim'] - etapa['inicio']
                duracao_total += duracao.total_seconds()

        return {
            'segundos': duracao_total,
            'minutos': duracao_total / 60,
            'horas': duracao_total / 3600
        }

    def reiniciar_etapa(self, etapa):
        """Reinicia uma etapa específica do roteiro."""
        if etapa not in self.etapas:
            return False

        self.observacoes[etapa] = {
            'inicio': datetime.now(),
            'fim': None,
            'observacoes': [],
            'status': 'em_andamento'
        }
        return True

    def pular_etapa(self, etapa, motivo=None):
        """Marca uma etapa como pulada com motivo opcional."""
        if etapa not in self.etapas:
            return False

        self.observacoes[etapa] = {
            'inicio': datetime.now(),
            'fim': datetime.now(),
            'observacoes': [{'texto': f'Etapa pulada: {motivo}', 'data': datetime.now()}] if motivo else [],
            'status': 'pulada'
        }
        return True 