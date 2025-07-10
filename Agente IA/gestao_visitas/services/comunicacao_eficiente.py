"""
Sistema de Comunicação Eficiente - PNSB
Templates, multicanal e automação de comunicação com informantes
"""

from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any
from ..models.agendamento import Visita
from ..models.contatos import Contato
from ..db import db
import json
from collections import defaultdict

class ComunicacaoEficiente:
    """Sistema de comunicação multicanal para informantes PNSB"""
    
    def __init__(self):
        # Templates de mensagem por situação
        self.templates_mensagem = {
            'agendamento_inicial': {
                'telefone': {
                    'script': "Bom dia/Boa tarde, {nome}. Sou {pesquisador} do IBGE. Estou ligando sobre a Pesquisa Nacional de Saneamento Básico em {municipio}. Podemos agendar um horário conveniente para você?",
                    'duracao_estimada': 3,
                    'followup': 'confirmar_por_whatsapp'
                },
                'whatsapp': {
                    'template': "Olá {nome}! Sou {pesquisador} do IBGE 📊\n\nEstou entrando em contato sobre a Pesquisa Nacional de Saneamento Básico em {municipio}.\n\nPodemos agendar um horário conveniente? O processo leva cerca de 30-45 minutos.\n\nObrigado! 🙏",
                    'horario_envio': 'comercial',
                    'aguardar_resposta': 24
                },
                'email': {
                    'assunto': 'IBGE - Pesquisa Nacional de Saneamento Básico - {municipio}',
                    'template': """Prezado(a) {nome},

O Instituto Brasileiro de Geografia e Estatística (IBGE) está conduzindo a Pesquisa Nacional de Saneamento Básico 2024.

Seu município foi selecionado para participar desta importante pesquisa sobre manejo de resíduos sólidos e águas pluviais.

Gostaria de agendar um horário conveniente para a coleta dos dados. O processo é simples e leva aproximadamente 30-45 minutos.

Atenciosamente,
{pesquisador}
Pesquisador IBGE
Telefone: {telefone_pesquisador}""",
                    'prioridade': 'normal'
                }
            },
            'confirmacao_agendamento': {
                'whatsapp': {
                    'template': "✅ Agendamento confirmado!\n\n📅 Data: {data_visita}\n⏰ Horário: {horario}\n📍 Local: {local}\n👤 Pesquisador: {pesquisador}\n\nEm caso de necessidade, entre em contato: {telefone_pesquisador}",
                    'enviar_antes': 1440  # 24h antes
                },
                'email': {
                    'assunto': 'Confirmação - Pesquisa IBGE em {data_visita}',
                    'template': """Prezado(a) {nome},

Confirmamos o agendamento da Pesquisa Nacional de Saneamento Básico:

📅 Data: {data_visita}
⏰ Horário: {horario}  
📍 Local: {local}
👤 Pesquisador: {pesquisador}
📞 Contato: {telefone_pesquisador}

Materiais necessários:
- Dados sobre coleta de resíduos sólidos
- Informações sobre drenagem urbana
- Dados de infraestrutura de saneamento

Atenciosamente,
{pesquisador}"""
                }
            },
            'lembrete_visita': {
                'whatsapp': {
                    'template': "🔔 Lembrete: Pesquisa IBGE hoje!\n\n⏰ {horario} - {local}\n👤 {pesquisador}\n\nAté logo! 👋",
                    'enviar_antes': 120  # 2h antes
                },
                'telefone': {
                    'script': "Bom dia/Boa tarde, {nome}. É {pesquisador} do IBGE. Só para lembrar de nosso agendamento hoje às {horario}. Confirma que está tudo certo?",
                    'enviar_antes': 60  # 1h antes
                }
            },
            'reagendamento': {
                'whatsapp': {
                    'template': "Olá {nome}! Preciso reagendar nossa visita de hoje. Quando seria um bom momento para você? Posso ir em qualquer horário que seja conveniente. 🗓️",
                    'urgente': True
                },
                'telefone': {
                    'script': "Olá {nome}, é {pesquisador} do IBGE. Infelizmente preciso reagendar nossa visita. Qual seria um bom horário alternativo para você?",
                    'prioridade': 'alta'
                }
            },
            'pos_visita_agradecimento': {
                'whatsapp': {
                    'template': "Muito obrigado pela participação na Pesquisa IBGE! 🙏\n\nSua contribuição é fundamental para melhorar o saneamento básico no Brasil.\n\nTenha um ótimo dia! ☀️"
                },
                'email': {
                    'assunto': 'Obrigado pela participação - Pesquisa IBGE',
                    'template': """Prezado(a) {nome},

Muito obrigado por sua participação na Pesquisa Nacional de Saneamento Básico.

Sua contribuição é fundamental para o desenvolvimento de políticas públicas de saneamento que beneficiarão todo o país.

Os resultados da pesquisa serão disponibilizados no site do IBGE em até 6 meses.

Atenciosamente,
Equipe PNSB - IBGE"""
                }
            },
            'escalacao_supervisor': {
                'email': {
                    'assunto': 'URGENTE - Dificuldade com informante {municipio}',
                    'template': """Prezado(a) Supervisor(a),

Estou enfrentando dificuldades para coletar dados em {municipio} com o informante {nome}.

Situação:
- Tentativas realizadas: {tentativas}
- Último contato: {ultimo_contato}
- Principal dificuldade: {dificuldade}

Solicito orientação sobre próximos passos ou possível escalação.

Atenciosamente,
{pesquisador}"""
                }
            }
        }
        
        # Regras para seleção de canal
        self.regras_canal = self._definir_regras_canal()
        
        # Histórico de comunicação
        self.historico_comunicacao = {}
    
    def selecionar_canal_otimo(self, informante_nome: str, municipio: str, 
                             tipo_mensagem: str, contexto: Dict = None) -> Dict:
        """Seleciona o melhor canal de comunicação para uma situação específica"""
        
        # Obter dados do informante
        contato = Contato.query.filter_by(
            nome=informante_nome,
            municipio=municipio
        ).first()
        
        if not contato:
            return {'erro': 'Informante não encontrado'}
        
        # Analisar histórico de comunicação
        historico_sucesso = self._analisar_historico_comunicacao(informante_nome, municipio)
        
        # Aplicar regras de seleção
        canais_disponiveis = self._identificar_canais_disponiveis(contato)
        canais_pontuados = self._pontuar_canais(
            canais_disponiveis, tipo_mensagem, historico_sucesso, contexto
        )
        
        # Selecionar melhor canal
        melhor_canal = max(canais_pontuados, key=lambda x: x['score']) if canais_pontuados else None
        
        if not melhor_canal:
            return {'erro': 'Nenhum canal disponível'}
        
        # Gerar recomendações específicas
        recomendacoes = self._gerar_recomendacoes_canal(
            melhor_canal, tipo_mensagem, historico_sucesso, contexto
        )
        
        return {
            'canal_recomendado': melhor_canal['canal'],
            'score_confianca': melhor_canal['score'],
            'justificativa': melhor_canal['justificativa'],
            'canais_alternativos': [c for c in canais_pontuados if c != melhor_canal][:2],
            'recomendacoes_uso': recomendacoes,
            'horario_ideal': self._sugerir_horario_ideal(melhor_canal['canal'], historico_sucesso),
            'followup_recomendado': self._sugerir_followup(melhor_canal['canal'], tipo_mensagem)
        }
    
    def gerar_mensagem_personalizada(self, informante_nome: str, municipio: str,
                                   tipo_mensagem: str, canal: str, 
                                   dados_personalizacao: Dict = None) -> Dict:
        """Gera mensagem personalizada para um informante específico"""
        
        # Obter template base
        template_info = self.templates_mensagem.get(tipo_mensagem, {}).get(canal, {})
        
        if not template_info:
            return {'erro': f'Template não encontrado para {tipo_mensagem} via {canal}'}
        
        # Obter dados do informante
        contato = Contato.query.filter_by(
            nome=informante_nome,
            municipio=municipio
        ).first()
        
        # Preparar dados para personalização
        dados_base = {
            'nome': informante_nome,
            'municipio': municipio,
            'pesquisador': dados_personalizacao.get('pesquisador', '[Nome do Pesquisador]') if dados_personalizacao else '[Nome do Pesquisador]',
            'telefone_pesquisador': dados_personalizacao.get('telefone_pesquisador', '[Telefone]') if dados_personalizacao else '[Telefone]',
            'data_visita': dados_personalizacao.get('data_visita', '[Data]') if dados_personalizacao else '[Data]',
            'horario': dados_personalizacao.get('horario', '[Horário]') if dados_personalizacao else '[Horário]',
            'local': dados_personalizacao.get('local', f'Prefeitura de {municipio}') if dados_personalizacao else f'Prefeitura de {municipio}'
        }
        
        # Adicionar dados específicos se fornecidos
        if dados_personalizacao:
            dados_base.update(dados_personalizacao)
        
        # Personalizar mensagem baseado no histórico do informante
        mensagem_personalizada = self._personalizar_mensagem_historico(
            template_info, dados_base, informante_nome, municipio
        )
        
        # Gerar instruções de envio
        instrucoes_envio = self._gerar_instrucoes_envio(canal, template_info, contato)
        
        return {
            'canal': canal,
            'tipo_mensagem': tipo_mensagem,
            'mensagem_final': mensagem_personalizada,
            'instrucoes_envio': instrucoes_envio,
            'dados_contato': {
                'telefone': contato.telefone if contato else None,
                'email': contato.email if contato else None,
                'whatsapp': contato.telefone if contato else None  # Assumindo mesmo número
            },
            'timing_recomendado': self._calcular_timing_envio(canal, template_info),
            'followup_necessario': template_info.get('followup', False),
            'prioridade': template_info.get('prioridade', 'normal')
        }
    
    def programar_lembretes_automaticos(self, visita_id: int) -> Dict:
        """Programa lembretes automáticos para uma visita"""
        
        visita = Visita.query.get(visita_id)
        if not visita:
            return {'erro': 'Visita não encontrada'}
        
        # Calcular horários dos lembretes
        data_visita = datetime.combine(visita.data, visita.hora_inicio)
        
        lembretes_programados = []
        
        # Lembrete 24h antes (confirmação)
        lembrete_24h = data_visita - timedelta(hours=24)
        if lembrete_24h > datetime.now():
            lembrete_24h_config = self._configurar_lembrete(
                visita, 'confirmacao_agendamento', lembrete_24h, 'whatsapp'
            )
            lembretes_programados.append(lembrete_24h_config)
        
        # Lembrete 2h antes (último lembrete)
        lembrete_2h = data_visita - timedelta(hours=2)
        if lembrete_2h > datetime.now():
            lembrete_2h_config = self._configurar_lembrete(
                visita, 'lembrete_visita', lembrete_2h, 'whatsapp'
            )
            lembretes_programados.append(lembrete_2h_config)
        
        # Registrar lembretes no sistema
        for lembrete in lembretes_programados:
            self._registrar_lembrete_sistema(lembrete)
        
        return {
            'visita_id': visita_id,
            'total_lembretes_programados': len(lembretes_programados),
            'lembretes': lembretes_programados,
            'status': 'programado'
        }
    
    def registrar_comunicacao(self, informante_nome: str, municipio: str,
                            comunicacao_data: Dict) -> Dict:
        """Registra uma comunicação realizada"""
        
        registro = {
            'timestamp': datetime.now().isoformat(),
            'informante': informante_nome,
            'municipio': municipio,
            'canal_utilizado': comunicacao_data.get('canal'),
            'tipo_mensagem': comunicacao_data.get('tipo_mensagem'),
            'sucesso': comunicacao_data.get('sucesso', False),
            'resposta_recebida': comunicacao_data.get('resposta_recebida', False),
            'tempo_resposta_minutos': comunicacao_data.get('tempo_resposta_minutos'),
            'observacoes': comunicacao_data.get('observacoes', ''),
            'proximo_followup': comunicacao_data.get('proximo_followup'),
            'pesquisador_responsavel': comunicacao_data.get('pesquisador', 'sistema')
        }
        
        # Atualizar histórico do contato
        contato = Contato.query.filter_by(
            nome=informante_nome,
            municipio=municipio
        ).first()
        
        if contato:
            if not contato.historico_comunicacao:
                contato.historico_comunicacao = '[]'
            
            historico = json.loads(contato.historico_comunicacao)
            historico.append(registro)
            contato.historico_comunicacao = json.dumps(historico)
            
            # Atualizar preferências baseado no sucesso
            self._atualizar_preferencias_comunicacao(contato, registro)
            
            db.session.commit()
        
        # Gerar recomendações para próxima comunicação
        recomendacoes_proxima = self._gerar_recomendacoes_proxima_comunicacao(
            informante_nome, municipio, registro
        )
        
        return {
            'registro_salvo': registro,
            'historico_atualizado': True,
            'recomendacoes_proxima_comunicacao': recomendacoes_proxima,
            'canal_preferido_atualizado': self._calcular_canal_preferido_atualizado(
                informante_nome, municipio
            )
        }
    
    def gerar_relatorio_comunicacao(self, periodo_dias: int = 30) -> Dict:
        """Gera relatório de eficiência da comunicação"""
        
        from datetime import date
        data_inicio = date.today() - timedelta(days=periodo_dias)
        
        # Obter comunicações do período
        comunicacoes = self._obter_comunicacoes_periodo(data_inicio)
        
        # Análise por canal
        analise_por_canal = defaultdict(lambda: {
            'tentativas': 0,
            'sucessos': 0,
            'taxa_resposta': 0,
            'tempo_medio_resposta': 0
        })
        
        # Análise por tipo de mensagem
        analise_por_tipo = defaultdict(lambda: {
            'enviadas': 0,
            'bem_sucedidas': 0,
            'taxa_sucesso': 0
        })
        
        # Análise por informante
        informantes_dificeis = []
        informantes_cooperativos = []
        
        # Processar dados
        for comunicacao in comunicacoes:
            canal = comunicacao.get('canal_utilizado', 'indefinido')
            tipo = comunicacao.get('tipo_mensagem', 'indefinido')
            
            analise_por_canal[canal]['tentativas'] += 1
            analise_por_tipo[tipo]['enviadas'] += 1
            
            if comunicacao.get('sucesso'):
                analise_por_canal[canal]['sucessos'] += 1
                analise_por_tipo[tipo]['bem_sucedidas'] += 1
        
        # Calcular estatísticas
        for canal, dados in analise_por_canal.items():
            if dados['tentativas'] > 0:
                dados['taxa_resposta'] = round((dados['sucessos'] / dados['tentativas']) * 100, 1)
        
        for tipo, dados in analise_por_tipo.items():
            if dados['enviadas'] > 0:
                dados['taxa_sucesso'] = round((dados['bem_sucedidas'] / dados['enviadas']) * 100, 1)
        
        # Identificar padrões e recomendações
        recomendacoes_melhoria = self._gerar_recomendacoes_melhoria_comunicacao(
            analise_por_canal, analise_por_tipo
        )
        
        return {
            'periodo_analise': {
                'data_inicio': data_inicio.isoformat(),
                'data_fim': date.today().isoformat(),
                'total_comunicacoes': len(comunicacoes)
            },
            'analise_por_canal': dict(analise_por_canal),
            'analise_por_tipo_mensagem': dict(analise_por_tipo),
            'canal_mais_eficaz': max(analise_por_canal.items(), key=lambda x: x[1]['taxa_resposta'])[0] if analise_por_canal else None,
            'tipo_mensagem_mais_eficaz': max(analise_por_tipo.items(), key=lambda x: x[1]['taxa_sucesso'])[0] if analise_por_tipo else None,
            'recomendacoes_melhoria': recomendacoes_melhoria,
            'estatisticas_gerais': {
                'taxa_sucesso_geral': round(sum(c.get('sucesso', 0) for c in comunicacoes) / len(comunicacoes) * 100, 1) if comunicacoes else 0,
                'canais_utilizados': len(analise_por_canal),
                'tipos_mensagem_utilizados': len(analise_por_tipo)
            }
        }
    
    def configurar_escalacao_inteligente(self, criterios_escalacao: Dict) -> Dict:
        """Configura critérios para escalação automática ao supervisor"""
        
        criterios_padrao = {
            'tentativas_sem_sucesso': 3,
            'dias_sem_resposta': 7,
            'tipos_dificuldade_critica': ['recusa_formal', 'impossivel_contato', 'conflito'],
            'municipios_prioritarios': [],
            'prazo_limite_dias': 30
        }
        
        # Mesclar critérios fornecidos com padrões
        criterios_finais = {**criterios_padrao, **criterios_escalacao}
        
        # Configurar monitoramento automático
        monitoramento_config = {
            'criterios_escalacao': criterios_finais,
            'verificacao_diaria': True,
            'notificacao_supervisor': True,
            'template_escalacao': 'escalacao_supervisor',
            'ativo': True
        }
        
        # Salvar configuração (simplificado)
        self._salvar_configuracao_escalacao(monitoramento_config)
        
        return {
            'configuracao_salva': monitoramento_config,
            'monitoramento_ativo': True,
            'proxima_verificacao': (datetime.now() + timedelta(days=1)).isoformat()
        }
    
    # Métodos auxiliares
    
    def _definir_regras_canal(self) -> Dict:
        """Define regras para seleção automática de canal"""
        return {
            'whatsapp': {
                'horario_ideal': {'inicio': time(8, 0), 'fim': time(18, 0)},
                'eficacia_geral': 85,
                'rapidez_resposta': 'alta',
                'adequado_para': ['lembrete', 'confirmacao', 'reagendamento']
            },
            'telefone': {
                'horario_ideal': {'inicio': time(9, 0), 'fim': time(17, 0)},
                'eficacia_geral': 75,
                'rapidez_resposta': 'imediata',
                'adequado_para': ['agendamento_inicial', 'emergencia', 'escalacao']
            },
            'email': {
                'horario_ideal': {'inicio': time(7, 0), 'fim': time(19, 0)},
                'eficacia_geral': 60,
                'rapidez_resposta': 'baixa',
                'adequado_para': ['formal', 'documentacao', 'followup']
            }
        }
    
    # Implementações simplificadas dos métodos auxiliares
    def _analisar_historico_comunicacao(self, nome, municipio): return {}
    def _identificar_canais_disponiveis(self, contato): return [{'canal': 'whatsapp'}, {'canal': 'telefone'}]
    def _pontuar_canais(self, canais, tipo, historico, contexto): 
        return [{'canal': 'whatsapp', 'score': 85, 'justificativa': 'Melhor taxa de resposta'}]
    def _gerar_recomendacoes_canal(self, canal, tipo, historico, contexto): return {}
    def _sugerir_horario_ideal(self, canal, historico): return "09:00-11:00"
    def _sugerir_followup(self, canal, tipo): return {"tempo": 24, "canal": "telefone"}
    def _personalizar_mensagem_historico(self, template, dados, nome, municipio):
        if 'template' in template:
            return template['template'].format(**dados)
        elif 'script' in template:
            return template['script'].format(**dados)
        return "Mensagem padrão"
    def _gerar_instrucoes_envio(self, canal, template, contato): return {}
    def _calcular_timing_envio(self, canal, template): return datetime.now().isoformat()
    def _configurar_lembrete(self, visita, tipo, horario, canal): return {}
    def _registrar_lembrete_sistema(self, lembrete): pass
    def _atualizar_preferencias_comunicacao(self, contato, registro): pass
    def _gerar_recomendacoes_proxima_comunicacao(self, nome, municipio, registro): return []
    def _calcular_canal_preferido_atualizado(self, nome, municipio): return "whatsapp"
    def _obter_comunicacoes_periodo(self, data_inicio): return []
    def _gerar_recomendacoes_melhoria_comunicacao(self, por_canal, por_tipo): return []
    def _salvar_configuracao_escalacao(self, config): pass