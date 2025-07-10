"""
Serviço Avançado de Gestão de Prestadores - PNSB 2024
Sistema completo para cadastro, validação e monitoramento de prestadores de serviços
"""

from datetime import datetime, timedelta
from ..config import MUNICIPIOS
from ..db import db
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
import json
import re
from typing import Dict, List, Optional, Tuple

Base = declarative_base()

class Prestador(Base):
    __tablename__ = 'prestadores'
    
    id = Column(Integer, primary_key=True)
    municipio = Column(String(100), nullable=False)
    nome = Column(String(200), nullable=False)
    cnpj = Column(String(18), nullable=False, unique=True)
    areas_atuacao = Column(JSON, nullable=False)
    contatos = Column(JSON, default=lambda: [])
    contratos = Column(JSON, default=lambda: [])
    endereco = Column(Text)
    responsavel_tecnico = Column(String(200))
    data_cadastro = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='ativo')
    validacao_status = Column(String(20), default='pendente')
    validacao_data = Column(DateTime)
    validacao_observacoes = Column(Text)
    historico_interacoes = Column(JSON, default=lambda: [])
    avaliacao = Column(Float, default=0.0)
    questionario_mrs = Column(JSON, default=lambda: {})
    questionario_map = Column(JSON, default=lambda: {})
    documentos_pendentes = Column(JSON, default=lambda: [])
    
    def to_dict(self):
        return {
            'id': self.id,
            'municipio': self.municipio,
            'nome': self.nome,
            'cnpj': self.cnpj,
            'areas_atuacao': self.areas_atuacao,
            'contatos': self.contatos,
            'contratos': self.contratos,
            'endereco': self.endereco,
            'responsavel_tecnico': self.responsavel_tecnico,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'status': self.status,
            'validacao_status': self.validacao_status,
            'validacao_data': self.validacao_data.isoformat() if self.validacao_data else None,
            'validacao_observacoes': self.validacao_observacoes,
            'historico_interacoes': self.historico_interacoes,
            'avaliacao': self.avaliacao,
            'questionario_mrs': self.questionario_mrs,
            'questionario_map': self.questionario_map,
            'documentos_pendentes': self.documentos_pendentes
        }

class PrestadorService:
    """Serviço avançado para gestão de prestadores de serviços da PNSB"""
    
    def __init__(self):
        self.areas_atuacao = {
            'coleta_domiciliar': 'Coleta Domiciliar',
            'coleta_comercial': 'Coleta Comercial',
            'coleta_seletiva': 'Coleta Seletiva',
            'coleta_volumosos': 'Coleta de Volumosos',
            'transporte_rsu': 'Transporte de RSU',
            'transporte_rss': 'Transporte de RSS',
            'tratamento_organicos': 'Tratamento de Orgânicos',
            'tratamento_reciclaveis': 'Tratamento de Recicláveis',
            'disposicao_final': 'Disposição Final',
            'varricao_manual': 'Varrição Manual',
            'varricao_mecanizada': 'Varrição Mecanizada',
            'capina_poda': 'Capina e Poda',
            'limpeza_bocas_lobo': 'Limpeza de Bocas de Lobo',
            'drenagem_urbana': 'Sistema de Drenagem Urbana',
            'microdrenagem': 'Microdrenagem',
            'macrodrenagem': 'Macrodrenagem',
            'bombas_recalque': 'Estações de Bombeamento',
            'manutencao_galerias': 'Manutenção de Galerias',
            'outros': 'Outros Serviços'
        }
        
        self.tipos_contrato = {
            'concessao': 'Concessão',
            'permissao': 'Permissão',
            'terceirizacao': 'Terceirização',
            'cooperativa': 'Cooperativa',
            'consorcio_intermunicipal': 'Consórcio Intermunicipal',
            'orgao_publico': 'Órgão Público',
            'outros': 'Outros'
        }
        
        self.documentos_obrigatorios = {
            'licenca_ambiental': 'Licença Ambiental',
            'alvara_funcionamento': 'Alvará de Funcionamento',
            'certidao_regularidade_fiscal': 'Certidão de Regularidade Fiscal',
            'contrato_social': 'Contrato Social',
            'anotacao_responsabilidade_tecnica': 'ART/RRT',
            'plano_gerenciamento_residuos': 'PGRS',
            'certificado_iso': 'Certificação ISO',
            'outros': 'Outros Documentos'
        }
        
        self.status_validacao = {
            'pendente': 'Aguardando Validação',
            'em_analise': 'Em Análise',
            'aprovado': 'Aprovado',
            'aprovado_condicional': 'Aprovado com Ressalvas',
            'rejeitado': 'Rejeitado',
            'documentos_pendentes': 'Documentos Pendentes',
            'revisao_necessaria': 'Revisão Necessária'
        }

    def validar_cnpj(self, cnpj: str) -> bool:
        """Valida formato do CNPJ"""
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj) != 14:
            return False
        
        # Algoritmo de validação do CNPJ
        def calcular_digito(cnpj_parcial, pesos):
            soma = sum(int(cnpj_parcial[i]) * pesos[i] for i in range(len(pesos)))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        digito1 = calcular_digito(cnpj[:12], pesos1)
        digito2 = calcular_digito(cnpj[:13], pesos2)
        
        return cnpj[-2:] == f"{digito1}{digito2}"

    def cadastrar_prestador(self, dados: Dict) -> Optional[int]:
        """Cadastra um novo prestador com validações avançadas"""
        try:
            # Validações básicas
            if not dados.get('municipio') or dados['municipio'] not in MUNICIPIOS:
                raise ValueError("Município inválido")
            
            if not dados.get('nome') or len(dados['nome'].strip()) < 3:
                raise ValueError("Nome deve ter pelo menos 3 caracteres")
            
            if not dados.get('cnpj') or not self.validar_cnpj(dados['cnpj']):
                raise ValueError("CNPJ inválido")
            
            if not dados.get('areas_atuacao') or not isinstance(dados['areas_atuacao'], list):
                raise ValueError("Áreas de atuação são obrigatórias")
            
            # Verificar se CNPJ já existe
            if self.obter_prestador_por_cnpj(dados['cnpj']):
                raise ValueError("CNPJ já cadastrado")
            
            # Criar prestador
            prestador = Prestador(
                municipio=dados['municipio'],
                nome=dados['nome'].strip(),
                cnpj=re.sub(r'[^0-9]', '', dados['cnpj']),
                areas_atuacao=dados['areas_atuacao'],
                endereco=dados.get('endereco', ''),
                responsavel_tecnico=dados.get('responsavel_tecnico', ''),
                contatos=dados.get('contatos', []),
                contratos=dados.get('contratos', []),
                documentos_pendentes=self._gerar_documentos_pendentes(dados['areas_atuacao'])
            )
            
            db.session.add(prestador)
            db.session.commit()
            
            # Registrar histórico
            self._registrar_interacao(prestador.id, 'cadastro', 'Prestador cadastrado no sistema')
            
            return prestador.id
            
        except Exception as e:
            db.session.rollback()
            raise e

    def _gerar_documentos_pendentes(self, areas_atuacao: List[str]) -> List[Dict]:
        """Gera lista de documentos obrigatórios baseado nas áreas de atuação"""
        documentos = ['contrato_social', 'certidao_regularidade_fiscal', 'alvara_funcionamento']
        
        # Documentos específicos por área
        if any(area in areas_atuacao for area in ['coleta_domiciliar', 'coleta_comercial', 'coleta_seletiva']):
            documentos.extend(['licenca_ambiental', 'plano_gerenciamento_residuos'])
        
        if any(area in areas_atuacao for area in ['tratamento_organicos', 'tratamento_reciclaveis', 'disposicao_final']):
            documentos.extend(['licenca_ambiental', 'anotacao_responsabilidade_tecnica'])
        
        if any(area in areas_atuacao for area in ['drenagem_urbana', 'microdrenagem', 'macrodrenagem']):
            documentos.append('anotacao_responsabilidade_tecnica')
        
        return [
            {
                'tipo': doc,
                'nome': self.documentos_obrigatorios[doc],
                'status': 'pendente',
                'data_solicitacao': datetime.now().isoformat(),
                'prazo': (datetime.now() + timedelta(days=30)).isoformat()
            }
            for doc in set(documentos)
        ]

    def atualizar_prestador(self, prestador_id: int, dados: Dict) -> bool:
        """Atualiza dados do prestador"""
        try:
            prestador = db.session.query(Prestador).get(prestador_id)
            if not prestador:
                return False
            
            # Campos editáveis
            campos_editaveis = ['nome', 'endereco', 'responsavel_tecnico', 'areas_atuacao']
            alteracoes = []
            
            for campo in campos_editaveis:
                if campo in dados and getattr(prestador, campo) != dados[campo]:
                    valor_anterior = getattr(prestador, campo)
                    setattr(prestador, campo, dados[campo])
                    alteracoes.append(f"{campo}: {valor_anterior} → {dados[campo]}")
            
            if 'contatos' in dados:
                prestador.contatos = dados['contatos']
                alteracoes.append("Contatos atualizados")
            
            if 'contratos' in dados:
                prestador.contratos = dados['contratos']
                alteracoes.append("Contratos atualizados")
            
            if alteracoes:
                db.session.commit()
                self._registrar_interacao(
                    prestador_id, 
                    'atualizacao', 
                    f"Dados atualizados: {'; '.join(alteracoes)}"
                )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            return False

    def validar_prestador(self, prestador_id: int, status: str, observacoes: str = "", documentos_aprovados: List[str] = None) -> bool:
        """Valida ou rejeita um prestador"""
        try:
            prestador = db.session.query(Prestador).get(prestador_id)
            if not prestador:
                return False
            
            if status not in self.status_validacao:
                return False
            
            status_anterior = prestador.validacao_status
            prestador.validacao_status = status
            prestador.validacao_data = datetime.now()
            prestador.validacao_observacoes = observacoes
            
            # Atualizar documentos aprovados
            if documentos_aprovados:
                for doc in prestador.documentos_pendentes:
                    if doc['tipo'] in documentos_aprovados:
                        doc['status'] = 'aprovado'
                        doc['data_aprovacao'] = datetime.now().isoformat()
            
            # Calcular score de qualidade
            if status == 'aprovado':
                prestador.avaliacao = self._calcular_score_qualidade(prestador)
            
            db.session.commit()
            
            self._registrar_interacao(
                prestador_id,
                'validacao',
                f"Status alterado de '{status_anterior}' para '{status}'. Observações: {observacoes}"
            )
            
            return True
            
        except Exception as e:
            db.session.rollback()
            return False

    def _calcular_score_qualidade(self, prestador: Prestador) -> float:
        """Calcula score de qualidade do prestador"""
        score = 0.0
        
        # Documentação completa (40%)
        docs_aprovados = sum(1 for doc in prestador.documentos_pendentes if doc['status'] == 'aprovado')
        docs_total = len(prestador.documentos_pendentes)
        if docs_total > 0:
            score += (docs_aprovados / docs_total) * 0.4
        
        # Responsável técnico (20%)
        if prestador.responsavel_tecnico:
            score += 0.2
        
        # Diversidade de áreas (20%)
        areas_count = len(prestador.areas_atuacao)
        score += min(areas_count * 0.05, 0.2)
        
        # Informações completas (20%)
        campos_obrigatorios = ['nome', 'cnpj', 'endereco', 'contatos']
        campos_preenchidos = sum(1 for campo in campos_obrigatorios if getattr(prestador, campo))
        score += (campos_preenchidos / len(campos_obrigatorios)) * 0.2
        
        return round(min(score, 1.0), 2)

    def obter_prestador(self, prestador_id: int) -> Optional[Dict]:
        """Retorna dados completos do prestador"""
        prestador = db.session.query(Prestador).get(prestador_id)
        if not prestador:
            return None
        
        dados = prestador.to_dict()
        dados['areas_atuacao_nomes'] = [
            self.areas_atuacao.get(area, area) for area in prestador.areas_atuacao
        ]
        dados['status_validacao_nome'] = self.status_validacao.get(
            prestador.validacao_status, prestador.validacao_status
        )
        
        return dados

    def obter_prestador_por_cnpj(self, cnpj: str) -> Optional[Dict]:
        """Busca prestador pelo CNPJ"""
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        prestador = db.session.query(Prestador).filter_by(cnpj=cnpj_limpo).first()
        return prestador.to_dict() if prestador else None

    def listar_prestadores(self, filtros: Dict = None) -> List[Dict]:
        """Lista prestadores com filtros opcionais"""
        query = db.session.query(Prestador)
        
        if filtros:
            if 'municipio' in filtros:
                query = query.filter(Prestador.municipio == filtros['municipio'])
            
            if 'status' in filtros:
                query = query.filter(Prestador.status == filtros['status'])
            
            if 'validacao_status' in filtros:
                query = query.filter(Prestador.validacao_status == filtros['validacao_status'])
            
            if 'area_atuacao' in filtros:
                query = query.filter(Prestador.areas_atuacao.contains([filtros['area_atuacao']]))
        
        prestadores = query.order_by(Prestador.data_cadastro.desc()).all()
        return [p.to_dict() for p in prestadores]

    def obter_prestadores_municipio(self, municipio: str) -> List[Dict]:
        """Retorna prestadores de um município específico"""
        return self.listar_prestadores({'municipio': municipio})

    def obter_prestadores_validados(self) -> List[Dict]:
        """Retorna prestadores aprovados"""
        return self.listar_prestadores({'validacao_status': 'aprovado'})

    def gerar_relatorio_prestadores(self) -> Dict:
        """Gera relatório estatístico dos prestadores"""
        prestadores = db.session.query(Prestador).all()
        
        if not prestadores:
            return {
                'total': 0,
                'por_status': {},
                'por_municipio': {},
                'por_area': {},
                'documentos_pendentes': 0,
                'score_medio': 0.0
            }
        
        # Estatísticas por status
        por_status = {}
        for prestador in prestadores:
            status = prestador.validacao_status
            por_status[status] = por_status.get(status, 0) + 1
        
        # Estatísticas por município
        por_municipio = {}
        for prestador in prestadores:
            mun = prestador.municipio
            por_municipio[mun] = por_municipio.get(mun, 0) + 1
        
        # Estatísticas por área
        por_area = {}
        for prestador in prestadores:
            for area in prestador.areas_atuacao:
                por_area[area] = por_area.get(area, 0) + 1
        
        # Documentos pendentes
        docs_pendentes = sum(
            len([doc for doc in p.documentos_pendentes if doc['status'] == 'pendente'])
            for p in prestadores
        )
        
        # Score médio
        scores = [p.avaliacao for p in prestadores if p.avaliacao > 0]
        score_medio = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'total': len(prestadores),
            'por_status': por_status,
            'por_municipio': por_municipio,
            'por_area': por_area,
            'documentos_pendentes': docs_pendentes,
            'score_medio': round(score_medio, 2),
            'ultima_atualizacao': datetime.now().isoformat()
        }

    def _registrar_interacao(self, prestador_id: int, tipo: str, descricao: str):
        """Registra interação no histórico do prestador"""
        try:
            prestador = db.session.query(Prestador).get(prestador_id)
            if prestador:
                if not prestador.historico_interacoes:
                    prestador.historico_interacoes = []
                
                interacao = {
                    'data': datetime.now().isoformat(),
                    'tipo': tipo,
                    'descricao': descricao,
                    'usuario': 'sistema'  # Pode ser expandido para usuário logado
                }
                
                prestador.historico_interacoes.append(interacao)
                db.session.commit()
                
        except Exception as e:
            print(f"Erro ao registrar interação: {e}")

    def obter_alertas_prestadores(self) -> List[Dict]:
        """Retorna alertas sobre prestadores que precisam de atenção"""
        alertas = []
        prestadores = db.session.query(Prestador).all()
        
        for prestador in prestadores:
            # Documentos vencidos
            for doc in prestador.documentos_pendentes:
                if doc['status'] == 'pendente':
                    prazo = datetime.fromisoformat(doc['prazo'])
                    if prazo < datetime.now():
                        alertas.append({
                            'tipo': 'documento_vencido',
                            'prestador_id': prestador.id,
                            'prestador_nome': prestador.nome,
                            'municipio': prestador.municipio,
                            'mensagem': f"Documento '{doc['nome']}' vencido",
                            'urgencia': 'alta',
                            'data_vencimento': doc['prazo']
                        })
            
            # Prestadores sem validação há muito tempo
            if prestador.validacao_status == 'pendente':
                dias_pendente = (datetime.now() - prestador.data_cadastro).days
                if dias_pendente > 15:
                    alertas.append({
                        'tipo': 'validacao_pendente',
                        'prestador_id': prestador.id,
                        'prestador_nome': prestador.nome,
                        'municipio': prestador.municipio,
                        'mensagem': f"Validação pendente há {dias_pendente} dias",
                        'urgencia': 'media' if dias_pendente < 30 else 'alta',
                        'dias_pendente': dias_pendente
                    })
        
        return sorted(alertas, key=lambda x: x['urgencia'], reverse=True)

    def exportar_prestadores_csv(self) -> str:
        """Exporta dados dos prestadores para CSV"""
        import csv
        import io
        
        prestadores = db.session.query(Prestador).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'ID', 'Município', 'Nome', 'CNPJ', 'Áreas de Atuação',
            'Status Validação', 'Data Cadastro', 'Avaliação',
            'Responsável Técnico', 'Total Documentos', 'Documentos Aprovados'
        ])
        
        # Dados
        for prestador in prestadores:
            docs_aprovados = sum(1 for doc in prestador.documentos_pendentes if doc['status'] == 'aprovado')
            
            writer.writerow([
                prestador.id,
                prestador.municipio,
                prestador.nome,
                prestador.cnpj,
                '; '.join(prestador.areas_atuacao),
                prestador.validacao_status,
                prestador.data_cadastro.strftime('%d/%m/%Y') if prestador.data_cadastro else '',
                prestador.avaliacao,
                prestador.responsavel_tecnico or '',
                len(prestador.documentos_pendentes),
                docs_aprovados
            ])
        
        return output.getvalue()

# Instância global do serviço
prestador_service = PrestadorService()