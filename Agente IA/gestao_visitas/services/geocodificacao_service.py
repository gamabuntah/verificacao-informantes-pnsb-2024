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
    
    def validar_endereco_avancado(self, endereco: str, municipio: str = None) -> Dict:
        """
        Validação avançada de endereço para PNSB 2024
        
        Args:
            endereco: Endereço a ser validado
            municipio: Município para contexto (opcional)
            
        Returns:
            Dict com validação completa e sugestões
        """
        if not self.gmaps:
            return {
                'status': 'erro',
                'erro': 'Google Maps API não disponível',
                'valido': False,
                'confianca': 0,
                'sugestoes': []
            }
        
        if not endereco or endereco.strip() == '':
            return {
                'status': 'erro',
                'erro': 'Endereço vazio',
                'valido': False,
                'confianca': 0,
                'sugestoes': ['Forneça um endereço válido']
            }
        
        try:
            # Geocodificar primeiro
            resultado_geo = self.geocodificar_endereco(endereco, municipio)
            
            if resultado_geo['status'] != 'sucesso':
                return {
                    'status': 'erro',
                    'erro': resultado_geo['erro'],
                    'valido': False,
                    'confianca': 0,
                    'sugestoes': self._gerar_sugestoes_endereco(endereco, municipio)
                }
            
            # Analisar componentes do endereço
            componentes = resultado_geo.get('componentes', [])
            validacao_componentes = self._validar_componentes_endereco(componentes, municipio)
            
            # Calcular score de confiança
            confianca_score = self._calcular_confianca_endereco(
                resultado_geo['confianca'], 
                validacao_componentes,
                resultado_geo.get('tipos', [])
            )
            
            # Gerar sugestões de melhoria
            sugestoes = self._gerar_sugestoes_melhoria(
                endereco, 
                resultado_geo, 
                validacao_componentes
            )
            
            # Verificar se está em Santa Catarina
            validacao_sc = self._validar_santa_catarina(componentes)
            
            return {
                'status': 'sucesso',
                'valido': confianca_score >= 70,
                'confianca': confianca_score,
                'endereco_original': endereco,
                'endereco_formatado': resultado_geo['endereco_formatado'],
                'latitude': resultado_geo['latitude'],
                'longitude': resultado_geo['longitude'],
                'place_id': resultado_geo['place_id'],
                'plus_code': resultado_geo['plus_code'],
                'tipo_localizacao': resultado_geo['confianca'],
                'componentes_validados': validacao_componentes,
                'em_santa_catarina': validacao_sc['valido'],
                'municipio_detectado': validacao_sc['municipio'],
                'sugestoes': sugestoes,
                'alertas': self._gerar_alertas_endereco(validacao_componentes, validacao_sc)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na validação avançada: {str(e)}")
            return {
                'status': 'erro',
                'erro': f'Erro na validação: {str(e)}',
                'valido': False,
                'confianca': 0,
                'sugestoes': ['Erro interno na validação']
            }
    
    def _validar_componentes_endereco(self, componentes: List[Dict], municipio_esperado: str = None) -> Dict:
        """Valida componentes individuais do endereço"""
        validacao = {
            'numero': {'presente': False, 'valor': None},
            'rua': {'presente': False, 'valor': None},
            'bairro': {'presente': False, 'valor': None},
            'cidade': {'presente': False, 'valor': None},
            'estado': {'presente': False, 'valor': None},
            'cep': {'presente': False, 'valor': None},
            'pais': {'presente': False, 'valor': None}
        }
        
        for componente in componentes:
            tipos = componente.get('types', [])
            nome_longo = componente.get('long_name', '')
            nome_curto = componente.get('short_name', '')
            
            if 'street_number' in tipos:
                validacao['numero']['presente'] = True
                validacao['numero']['valor'] = nome_longo
            elif 'route' in tipos:
                validacao['rua']['presente'] = True
                validacao['rua']['valor'] = nome_longo
            elif 'sublocality' in tipos or 'neighborhood' in tipos:
                validacao['bairro']['presente'] = True
                validacao['bairro']['valor'] = nome_longo
            elif 'administrative_area_level_2' in tipos:
                validacao['cidade']['presente'] = True
                validacao['cidade']['valor'] = nome_longo
            elif 'administrative_area_level_1' in tipos:
                validacao['estado']['presente'] = True
                validacao['estado']['valor'] = nome_longo
            elif 'postal_code' in tipos:
                validacao['cep']['presente'] = True
                validacao['cep']['valor'] = nome_longo
            elif 'country' in tipos:
                validacao['pais']['presente'] = True
                validacao['pais']['valor'] = nome_longo
        
        # Validar se município esperado confere
        if municipio_esperado and validacao['cidade']['presente']:
            cidade_detectada = validacao['cidade']['valor']
            validacao['municipio_correto'] = (
                municipio_esperado.lower() in cidade_detectada.lower() or
                cidade_detectada.lower() in municipio_esperado.lower()
            )
        else:
            validacao['municipio_correto'] = True
        
        return validacao
    
    def _calcular_confianca_endereco(self, tipo_localizacao: str, componentes: Dict, tipos: List[str]) -> int:
        """Calcula score de confiança do endereço (0-100)"""
        score = 0
        
        # Score baseado no tipo de localização do Google
        if tipo_localizacao == 'ROOFTOP':
            score += 40
        elif tipo_localizacao == 'RANGE_INTERPOLATED':
            score += 30
        elif tipo_localizacao == 'GEOMETRIC_CENTER':
            score += 20
        else:
            score += 10
        
        # Score baseado nos componentes presentes
        if componentes['numero']['presente']:
            score += 15
        if componentes['rua']['presente']:
            score += 15
        if componentes['bairro']['presente']:
            score += 10
        if componentes['cidade']['presente']:
            score += 10
        if componentes['cep']['presente']:
            score += 10
        
        # Penalizar se município não confere
        if not componentes.get('municipio_correto', True):
            score -= 20
        
        # Bonus para tipos específicos
        if any(t in tipos for t in ['premise', 'establishment', 'point_of_interest']):
            score += 10
        
        return min(100, max(0, score))
    
    def _validar_santa_catarina(self, componentes: List[Dict]) -> Dict:
        """Valida se o endereço está em Santa Catarina"""
        municipios_sc = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        for componente in componentes:
            tipos = componente.get('types', [])
            nome_longo = componente.get('long_name', '')
            nome_curto = componente.get('short_name', '')
            
            # Verificar estado
            if 'administrative_area_level_1' in tipos:
                if 'Santa Catarina' in nome_longo or 'SC' in nome_curto:
                    # Verificar município
                    municipio_detectado = None
                    for comp in componentes:
                        if 'administrative_area_level_2' in comp.get('types', []):
                            municipio_detectado = comp.get('long_name', '')
                            break
                    
                    # Verificar se é um dos municípios PNSB
                    municipio_pnsb = any(
                        mun.lower() in (municipio_detectado or '').lower() 
                        for mun in municipios_sc
                    )
                    
                    return {
                        'valido': True,
                        'municipio': municipio_detectado,
                        'municipio_pnsb': municipio_pnsb,
                        'municipios_pnsb_disponiveis': municipios_sc
                    }
        
        return {
            'valido': False,
            'municipio': None,
            'municipio_pnsb': False,
            'municipios_pnsb_disponiveis': municipios_sc
        }
    
    def _gerar_sugestoes_endereco(self, endereco: str, municipio: str = None) -> List[str]:
        """Gera sugestões para endereços que falharam na geocodificação"""
        sugestoes = []
        
        # Sugestões básicas
        if len(endereco) < 10:
            sugestoes.append("Endereço muito curto - forneça mais detalhes")
        
        if not any(char.isdigit() for char in endereco):
            sugestoes.append("Inclua o número do endereço")
        
        if municipio and municipio not in endereco:
            sugestoes.append(f"Inclua o município: {municipio}")
        
        if "SC" not in endereco and "Santa Catarina" not in endereco:
            sugestoes.append("Inclua o estado: SC ou Santa Catarina")
        
        # Sugestões específicas para PNSB
        sugestoes.extend([
            "Verifique se o nome da rua está correto",
            "Confirme se o número do endereço existe",
            "Considere usar um ponto de referência próximo",
            "Verifique se o endereço é de uma das 11 cidades do PNSB"
        ])
        
        return sugestoes
    
    def _gerar_sugestoes_melhoria(self, endereco: str, resultado_geo: Dict, componentes: Dict) -> List[str]:
        """Gera sugestões de melhoria para endereços válidos"""
        sugestoes = []
        
        # Sugestões baseadas em componentes ausentes
        if not componentes['numero']['presente']:
            sugestoes.append("Considere incluir o número do endereço para maior precisão")
        
        if not componentes['bairro']['presente']:
            sugestoes.append("Incluir o bairro pode melhorar a precisão")
        
        if not componentes['cep']['presente']:
            sugestoes.append("Incluir o CEP aumenta a confiabilidade")
        
        # Sugestões baseadas no tipo de localização
        tipo_loc = resultado_geo.get('confianca', '')
        if tipo_loc == 'APPROXIMATE':
            sugestoes.append("Localização aproximada - verifique se o endereço está completo")
        elif tipo_loc == 'GEOMETRIC_CENTER':
            sugestoes.append("Localização no centro geométrico - confirme o endereço exato")
        
        return sugestoes
    
    def _gerar_alertas_endereco(self, componentes: Dict, validacao_sc: Dict) -> List[Dict]:
        """Gera alertas importantes sobre o endereço"""
        alertas = []
        
        # Alerta se não está em SC
        if not validacao_sc['valido']:
            alertas.append({
                'tipo': 'warning',
                'icone': '⚠️',
                'titulo': 'Endereço fora de Santa Catarina',
                'descricao': 'O endereço não parece estar em Santa Catarina'
            })
        
        # Alerta se não é município PNSB
        if validacao_sc['valido'] and not validacao_sc['municipio_pnsb']:
            alertas.append({
                'tipo': 'info',
                'icone': 'ℹ️',
                'titulo': 'Município não está no PNSB',
                'descricao': f"O município {validacao_sc['municipio']} não está na lista dos 11 municípios do PNSB"
            })
        
        # Alerta se município não confere
        if not componentes.get('municipio_correto', True):
            alertas.append({
                'tipo': 'warning',
                'icone': '⚠️',
                'titulo': 'Município não confere',
                'descricao': 'O município detectado não confere com o esperado'
            })
        
        # Alerta se endereço incompleto
        componentes_essenciais = ['rua', 'cidade', 'estado']
        ausentes = [c for c in componentes_essenciais if not componentes[c]['presente']]
        if ausentes:
            alertas.append({
                'tipo': 'warning',
                'icone': '⚠️',
                'titulo': 'Endereço incompleto',
                'descricao': f"Componentes ausentes: {', '.join(ausentes)}"
            })
        
        return alertas
    
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