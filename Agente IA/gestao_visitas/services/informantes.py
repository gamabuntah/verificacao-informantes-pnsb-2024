from datetime import datetime
from ..config import MUNICIPIOS

class InformanteService:
    def __init__(self):
        self.informantes = {}
        self.contatos = {}

    def cadastrar_informante(self, municipio, nome, cargo, area, contato=None):
        """Cadastra um novo informante."""
        if municipio not in MUNICIPIOS:
            return False

        informante_id = f"{municipio}_{len(self.informantes) + 1}"
        self.informantes[informante_id] = {
            'id': informante_id,
            'municipio': municipio,
            'nome': nome,
            'cargo': cargo,
            'area': area,
            'data_cadastro': datetime.now(),
            'status': 'ativo'
        }

        if contato:
            self.adicionar_contato(informante_id, contato)

        return informante_id

    def adicionar_contato(self, informante_id, contato):
        """Adiciona um contato para um informante."""
        if informante_id not in self.informantes:
            return False

        if informante_id not in self.contatos:
            self.contatos[informante_id] = []

        self.contatos[informante_id].append({
            'tipo': contato.get('tipo', 'telefone'),
            'valor': contato.get('valor'),
            'observacoes': contato.get('observacoes'),
            'data_cadastro': datetime.now()
        })
        return True

    def atualizar_informante(self, informante_id, dados):
        """Atualiza os dados de um informante."""
        if informante_id not in self.informantes:
            return False

        self.informantes[informante_id].update({
            'nome': dados.get('nome', self.informantes[informante_id]['nome']),
            'cargo': dados.get('cargo', self.informantes[informante_id]['cargo']),
            'area': dados.get('area', self.informantes[informante_id]['area']),
            'status': dados.get('status', self.informantes[informante_id]['status']),
            'data_atualizacao': datetime.now()
        })
        return True

    def obter_informante(self, informante_id):
        """Retorna os dados de um informante específico."""
        if informante_id not in self.informantes:
            return None

        informante = self.informantes[informante_id].copy()
        informante['contatos'] = self.contatos.get(informante_id, [])
        return informante

    def obter_informantes_por_municipio(self, municipio):
        """Retorna todos os informantes de um município."""
        return [
            self.obter_informante(informante_id)
            for informante_id, dados in self.informantes.items()
            if dados['municipio'] == municipio
        ]

    def obter_informantes_por_area(self, area):
        """Retorna todos os informantes de uma área específica."""
        return [
            self.obter_informante(informante_id)
            for informante_id, dados in self.informantes.items()
            if dados['area'] == area
        ]

    def desativar_informante(self, informante_id, motivo=None):
        """Desativa um informante com motivo opcional."""
        if informante_id not in self.informantes:
            return False

        self.informantes[informante_id].update({
            'status': 'inativo',
            'motivo_desativacao': motivo,
            'data_desativacao': datetime.now()
        })
        return True

    def reativar_informante(self, informante_id):
        """Reativa um informante previamente desativado."""
        if informante_id not in self.informantes:
            return False

        self.informantes[informante_id].update({
            'status': 'ativo',
            'motivo_desativacao': None,
            'data_desativacao': None,
            'data_reativacao': datetime.now()
        })
        return True

    def obter_estatisticas(self):
        """Retorna estatísticas sobre os informantes."""
        total = len(self.informantes)
        ativos = sum(1 for i in self.informantes.values() if i['status'] == 'ativo')
        por_municipio = {}
        por_area = {}

        for informante in self.informantes.values():
            municipio = informante['municipio']
            area = informante['area']

            por_municipio[municipio] = por_municipio.get(municipio, 0) + 1
            por_area[area] = por_area.get(area, 0) + 1

        return {
            'total': total,
            'ativos': ativos,
            'inativos': total - ativos,
            'por_municipio': por_municipio,
            'por_area': por_area
        } 