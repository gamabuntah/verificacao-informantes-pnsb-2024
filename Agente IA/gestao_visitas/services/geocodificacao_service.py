"""
Serviço de Geocodificação usando Google Maps API
Geocodifica endereços de entidades P1/P2/P3 e mantém backup dos dados originais
"""

import googlemaps
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import current_app

from gestao_visitas.db import db
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, EntidadePrioritariaUF


class GeocodificacaoService:
    """Serviço para geocodificação de entidades usando Google Maps API"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gmaps = None
        self._initialize_gmaps()
    
    def _initialize_gmaps(self):
        """Inicializa cliente Google Maps se API key disponível"""
        try:
            api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
            if api_key and api_key.strip() != '':
                # Inicializar sem timeout para evitar erro de compatibilidade
                self.gmaps = googlemaps.Client(key=api_key.strip())
                self.logger.info("🗺️ Google Maps API inicializada para geocodificação")
            else:
                self.logger.warning("⚠️ Google Maps API key não configurada - geocodificação desabilitada")
                self.gmaps = None
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar Google Maps API: {str(e)}")
            self.gmaps = None
    
    def geocodificar_endereco(self, endereco: str, municipio: str = None) -> Dict:
        """
        Geocodifica um endereço usando Google Maps API
        
        Args:
            endereco: Endereço a ser geocodificado
            municipio: Município para melhorar precisão (opcional)
            
        Returns:
            Dict com resultados da geocodificação
        """
        if not self.gmaps:
            return {
                'status': 'erro',
                'erro': 'Google Maps API não disponível',
                'confianca': None
            }
        
        if not endereco or endereco.strip() == '':
            return {
                'status': 'erro',
                'erro': 'Endereço vazio',
                'confianca': None
            }
        
        try:
            # Preparar endereço para geocodificação
            endereco_completo = endereco.strip()
            if municipio and municipio not in endereco_completo:
                endereco_completo += f", {municipio}, SC, Brasil"
            elif "SC" not in endereco_completo and "Santa Catarina" not in endereco_completo:
                endereco_completo += ", SC, Brasil"
            
            # Chamar Google Maps Geocoding API
            self.logger.info(f"🔍 Geocodificando: {endereco_completo}")
            resultado = self.gmaps.geocode(endereco_completo)
            
            if not resultado:
                return {
                    'status': 'erro',
                    'erro': 'Endereço não encontrado',
                    'confianca': None
                }
            
            # Processar primeiro resultado (mais relevante)
            geo_result = resultado[0]
            geometry = geo_result['geometry']
            
            # Extrair dados geográficos
            dados_geo = {
                'status': 'sucesso',
                'endereco_formatado': geo_result['formatted_address'],
                'latitude': geometry['location']['lat'],
                'longitude': geometry['location']['lng'],
                'place_id': geo_result.get('place_id'),
                'plus_code': geo_result.get('plus_code', {}).get('global_code'),
                'confianca': geometry['location_type'],
                'tipos': geo_result.get('types', []),
                'componentes': geo_result.get('address_components', [])
            }
            
            self.logger.info(f"✅ Geocodificação bem-sucedida: {dados_geo['confianca']}")
            return dados_geo
            
        except googlemaps.exceptions.ApiError as e:
            self.logger.error(f"❌ Erro na API Google Maps: {str(e)}")
            return {
                'status': 'erro',
                'erro': f'Erro na API: {str(e)}',
                'confianca': None
            }
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na geocodificação: {str(e)}")
            return {
                'status': 'erro',
                'erro': f'Erro inesperado: {str(e)}',
                'confianca': None
            }
    
    def geocodificar_entidade_identificada(self, entidade: EntidadeIdentificada, forcar_atualizacao: bool = False) -> bool:
        """
        Geocodifica uma EntidadeIdentificada específica
        
        Args:
            entidade: Entidade a ser geocodificada
            forcar_atualizacao: Se True, geocodifica mesmo se já foi processada
            
        Returns:
            True se geocodificação foi bem-sucedida
        """
        # Verificar se já foi geocodificada
        if not forcar_atualizacao and entidade.geocodificacao_status == 'sucesso':
            self.logger.info(f"⏭️ Entidade {entidade.nome_entidade} já geocodificada - pulando")
            return True
        
        # Backup do endereço original (se não existe)
        if not entidade.endereco_original and entidade.endereco:
            entidade.endereco_original = entidade.endereco
        
        # Geocodificar
        endereco_para_geocodificar = entidade.endereco or ""
        resultado = self.geocodificar_endereco(endereco_para_geocodificar, entidade.municipio)
        
        # Atualizar entidade com resultados
        if resultado['status'] == 'sucesso':
            entidade.endereco_formatado = resultado['endereco_formatado']
            entidade.latitude = resultado['latitude']
            entidade.longitude = resultado['longitude']
            entidade.place_id = resultado['place_id']
            entidade.plus_code = resultado['plus_code']
            entidade.geocodificacao_confianca = resultado['confianca']
            entidade.geocodificacao_status = 'sucesso'
            entidade.geocodificado_em = datetime.utcnow()
            
            self.logger.info(f"✅ {entidade.nome_entidade} geocodificada com sucesso")
            return True
        else:
            entidade.geocodificacao_status = 'erro'
            entidade.geocodificado_em = datetime.utcnow()
            
            self.logger.warning(f"❌ Falha ao geocodificar {entidade.nome_entidade}: {resultado['erro']}")
            return False
    
    def geocodificar_entidade_prioritaria_uf(self, entidade: EntidadePrioritariaUF, forcar_atualizacao: bool = False) -> bool:
        """
        Geocodifica uma EntidadePrioritariaUF específica
        
        Args:
            entidade: Entidade prioritária a ser geocodificada
            forcar_atualizacao: Se True, geocodifica mesmo se já foi processada
            
        Returns:
            True se geocodificação foi bem-sucedida
        """
        # Verificar se já foi geocodificada
        if not forcar_atualizacao and entidade.geocodificacao_status == 'sucesso':
            self.logger.info(f"⏭️ Entidade P1 {entidade.nome_entidade} já geocodificada - pulando")
            return True
        
        # Backup do endereço original (se não existe)
        if not entidade.endereco_original and entidade.endereco_completo:
            entidade.endereco_original = entidade.endereco_completo
        
        # Geocodificar
        endereco_para_geocodificar = entidade.endereco_completo or ""
        resultado = self.geocodificar_endereco(endereco_para_geocodificar, entidade.municipio)
        
        # Atualizar entidade com resultados
        if resultado['status'] == 'sucesso':
            entidade.endereco_formatado = resultado['endereco_formatado']
            entidade.latitude = resultado['latitude']
            entidade.longitude = resultado['longitude']
            entidade.place_id = resultado['place_id']
            entidade.plus_code = resultado['plus_code']
            entidade.geocodificacao_confianca = resultado['confianca']
            entidade.geocodificacao_status = 'sucesso'
            entidade.geocodificado_em = datetime.utcnow()
            
            self.logger.info(f"✅ Entidade P1 {entidade.nome_entidade} geocodificada com sucesso")
            return True
        else:
            entidade.geocodificacao_status = 'erro'
            entidade.geocodificado_em = datetime.utcnow()
            
            self.logger.warning(f"❌ Falha ao geocodificar entidade P1 {entidade.nome_entidade}: {resultado['erro']}")
            return False
    
    def geocodificar_todas_entidades(self, limite: int = None, delay_segundos: float = 0.1) -> Dict:
        """
        Geocodifica todas as entidades P1/P2/P3 existentes
        
        Args:
            limite: Limite de entidades a processar (None = todas)
            delay_segundos: Delay entre chamadas para evitar rate limit
            
        Returns:
            Dict com estatísticas do processamento
        """
        self.logger.info("🚀 Iniciando geocodificação em massa de todas as entidades")
        
        estatisticas = {
            'total_processadas': 0,
            'sucessos': 0,
            'erros': 0,
            'ja_geocodificadas': 0,
            'entidades_identificadas': {'processadas': 0, 'sucessos': 0, 'erros': 0},
            'entidades_prioritarias': {'processadas': 0, 'sucessos': 0, 'erros': 0}
        }
        
        try:
            # Processar EntidadeIdentificada (P1/P2/P3)
            self.logger.info("📍 Processando EntidadeIdentificada...")
            entidades_identificadas = EntidadeIdentificada.query.all()
            
            if limite:
                entidades_identificadas = entidades_identificadas[:limite//2]
            
            for entidade in entidades_identificadas:
                try:
                    if entidade.geocodificacao_status == 'sucesso':
                        estatisticas['ja_geocodificadas'] += 1
                        continue
                    
                    sucesso = self.geocodificar_entidade_identificada(entidade)
                    estatisticas['entidades_identificadas']['processadas'] += 1
                    
                    if sucesso:
                        estatisticas['entidades_identificadas']['sucessos'] += 1
                        estatisticas['sucessos'] += 1
                    else:
                        estatisticas['entidades_identificadas']['erros'] += 1
                        estatisticas['erros'] += 1
                    
                    estatisticas['total_processadas'] += 1
                    
                    # Delay para evitar rate limit
                    if delay_segundos > 0:
                        time.sleep(delay_segundos)
                        
                except Exception as e:
                    self.logger.error(f"❌ Erro ao processar entidade {entidade.id}: {str(e)}")
                    estatisticas['erros'] += 1
            
            # Processar EntidadePrioritariaUF (P1)
            self.logger.info("📍 Processando EntidadePrioritariaUF...")
            entidades_prioritarias = EntidadePrioritariaUF.query.all()
            
            if limite:
                entidades_prioritarias = entidades_prioritarias[:limite//2]
            
            for entidade in entidades_prioritarias:
                try:
                    if entidade.geocodificacao_status == 'sucesso':
                        estatisticas['ja_geocodificadas'] += 1
                        continue
                    
                    sucesso = self.geocodificar_entidade_prioritaria_uf(entidade)
                    estatisticas['entidades_prioritarias']['processadas'] += 1
                    
                    if sucesso:
                        estatisticas['entidades_prioritarias']['sucessos'] += 1
                        estatisticas['sucessos'] += 1
                    else:
                        estatisticas['entidades_prioritarias']['erros'] += 1
                        estatisticas['erros'] += 1
                    
                    estatisticas['total_processadas'] += 1
                    
                    # Delay para evitar rate limit
                    if delay_segundos > 0:
                        time.sleep(delay_segundos)
                        
                except Exception as e:
                    self.logger.error(f"❌ Erro ao processar entidade prioritária {entidade.id}: {str(e)}")
                    estatisticas['erros'] += 1
            
            # Salvar mudanças
            db.session.commit()
            
            self.logger.info(f"✅ Geocodificação concluída: {estatisticas}")
            return estatisticas
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Erro durante geocodificação em massa: {str(e)}")
            raise
    
    def obter_estatisticas_geocodificacao(self) -> Dict:
        """
        Retorna estatísticas sobre o status da geocodificação
        
        Returns:
            Dict com estatísticas detalhadas
        """
        try:
            # Estatísticas EntidadeIdentificada
            total_identificadas = EntidadeIdentificada.query.count()
            identificadas_geocodificadas = EntidadeIdentificada.query.filter_by(geocodificacao_status='sucesso').count()
            identificadas_erro = EntidadeIdentificada.query.filter_by(geocodificacao_status='erro').count()
            identificadas_pendentes = EntidadeIdentificada.query.filter_by(geocodificacao_status='pendente').count()
            
            # Estatísticas EntidadePrioritariaUF
            total_prioritarias = EntidadePrioritariaUF.query.count()
            prioritarias_geocodificadas = EntidadePrioritariaUF.query.filter_by(geocodificacao_status='sucesso').count()
            prioritarias_erro = EntidadePrioritariaUF.query.filter_by(geocodificacao_status='erro').count()
            prioritarias_pendentes = EntidadePrioritariaUF.query.filter_by(geocodificacao_status='pendente').count()
            
            return {
                'entidades_identificadas': {
                    'total': total_identificadas,
                    'geocodificadas': identificadas_geocodificadas,
                    'erro': identificadas_erro,
                    'pendentes': identificadas_pendentes,
                    'percentual_completo': round((identificadas_geocodificadas / total_identificadas * 100), 2) if total_identificadas > 0 else 0
                },
                'entidades_prioritarias': {
                    'total': total_prioritarias,
                    'geocodificadas': prioritarias_geocodificadas,
                    'erro': prioritarias_erro,
                    'pendentes': prioritarias_pendentes,
                    'percentual_completo': round((prioritarias_geocodificadas / total_prioritarias * 100), 2) if total_prioritarias > 0 else 0
                },
                'total_geral': {
                    'total': total_identificadas + total_prioritarias,
                    'geocodificadas': identificadas_geocodificadas + prioritarias_geocodificadas,
                    'erro': identificadas_erro + prioritarias_erro,
                    'pendentes': identificadas_pendentes + prioritarias_pendentes
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter estatísticas: {str(e)}")
            return {}


# Funções de conveniência
def geocodificar_nova_entidade(entidade) -> bool:
    """
    Geocodifica automaticamente uma nova entidade ao ser cadastrada
    
    Args:
        entidade: EntidadeIdentificada ou EntidadePrioritariaUF
        
    Returns:
        True se geocodificação foi bem-sucedida
    """
    service = GeocodificacaoService()
    
    if isinstance(entidade, EntidadeIdentificada):
        return service.geocodificar_entidade_identificada(entidade)
    elif isinstance(entidade, EntidadePrioritariaUF):
        return service.geocodificar_entidade_prioritaria_uf(entidade)
    else:
        return False


def processar_geocodificacao_pendentes(limite: int = 50) -> Dict:
    """
    Processa entidades com geocodificação pendente
    
    Args:
        limite: Número máximo de entidades a processar
        
    Returns:
        Dict com estatísticas do processamento
    """
    service = GeocodificacaoService()
    return service.geocodificar_todas_entidades(limite=limite)