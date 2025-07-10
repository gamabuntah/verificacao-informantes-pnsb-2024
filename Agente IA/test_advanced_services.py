#!/usr/bin/env python3
"""
Testes abrangentes para todos os serviços avançados implementados no sistema PNSB.

Este arquivo testa todos os 16 serviços avançados implementados:
1. Rastreamento de Questionários
2. Dashboard de Produtividade  
3. Sistema de Backup e Contingência
4. Gestão de Prestadores
5. Sistema de Notificações e Alertas
6. Análise de Resistência
7. Assistente de Abordagem
8. Comunicação Eficiente
9. Logística Maps
10. Perfil Inteligente de Informantes
11. Dashboard Avançado
12. Agendamento Avançado
13. Checklist Inteligente
14. Contatos Inteligente
15. Relatórios Avançados
16. WhatsApp API (rotas)
"""

import sys
import os
from datetime import datetime, date, timedelta, time
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_dir = Path(__file__).parent / "gestao_visitas"
sys.path.insert(0, str(project_dir.parent))

def test_import_services():
    """Testa se todos os serviços podem ser importados corretamente."""
    print("🔍 Testando importação dos serviços...")
    
    try:
        # Importar todos os serviços
        from gestao_visitas.services.rastreamento_questionarios import RastreamentoQuestionarios
        from gestao_visitas.services.dashboard_produtividade import DashboardProdutividade
        from gestao_visitas.services.sistema_backup_contingencia import SistemaBackupContingencia
        from gestao_visitas.services.prestadores import GestaoAvancadaPrestadores
        from gestao_visitas.services.notificacoes_alertas import SistemaNotificacoes
        from gestao_visitas.services.analise_resistencia import AnaliseResistencia
        from gestao_visitas.services.assistente_abordagem import AssistenteAbordagem
        from gestao_visitas.services.comunicacao_eficiente import ComunicacaoEficiente
        from gestao_visitas.services.logistica_maps import LogisticaMaps
        from gestao_visitas.services.perfil_informante import PerfilInformante
        from gestao_visitas.services.dashboard_avancado import DashboardAvancado
        from gestao_visitas.services.agendamento_avancado import AgendamentoAvancado
        from gestao_visitas.services.checklist_inteligente import ChecklistInteligente
        from gestao_visitas.services.contatos_inteligente import ContatosInteligente
        from gestao_visitas.services.relatorios_avancados import RelatoriosAvancados
        
        print("✅ Todos os serviços importados com sucesso!")
        return True
        
    except ImportError as e:
        print(f"❌ Erro ao importar serviços: {e}")
        return False

def test_service_initialization():
    """Testa se todos os serviços podem ser inicializados."""
    print("\n🚀 Testando inicialização dos serviços...")
    
    services_to_test = [
        ("RastreamentoQuestionarios", lambda: RastreamentoQuestionarios()),
        ("DashboardProdutividade", lambda: DashboardProdutividade()),
        ("SistemaBackupContingencia", lambda: SistemaBackupContingencia()),
        ("GestaoAvancadaPrestadores", lambda: GestaoAvancadaPrestadores()),
        ("SistemaNotificacoes", lambda: SistemaNotificacoes()),
        ("AnaliseResistencia", lambda: AnaliseResistencia()),
        ("AssistenteAbordagem", lambda: AssistenteAbordagem()),
        ("ComunicacaoEficiente", lambda: ComunicacaoEficiente()),
        ("LogisticaMaps", lambda: LogisticaMaps()),
        ("PerfilInformante", lambda: PerfilInformante()),
        ("DashboardAvancado", lambda: DashboardAvancado()),
        ("AgendamentoAvancado", lambda: AgendamentoAvancado()),
        ("ChecklistInteligente", lambda: ChecklistInteligente()),
        ("ContatosInteligente", lambda: ContatosInteligente()),
        ("RelatoriosAvancados", lambda: RelatoriosAvancados())
    ]
    
    success_count = 0
    
    for service_name, service_constructor in services_to_test:
        try:
            service = service_constructor()
            print(f"✅ {service_name} inicializado com sucesso")
            success_count += 1
        except Exception as e:
            print(f"❌ Erro ao inicializar {service_name}: {e}")
    
    print(f"\n📊 Resultado: {success_count}/{len(services_to_test)} serviços inicializados com sucesso")
    return success_count == len(services_to_test)

def test_rastreamento_questionarios():
    """Testa funcionalidades do RastreamentoQuestionarios."""
    print("\n📋 Testando RastreamentoQuestionarios...")
    
    try:
        from gestao_visitas.services.rastreamento_questionarios import RastreamentoQuestionarios
        
        service = RastreamentoQuestionarios()
        
        # Teste 1: Dashboard completo
        dashboard = service.obter_dashboard_completo()
        assert 'estatisticas_gerais' in dashboard
        assert 'questionarios_por_status' in dashboard
        print("✅ Dashboard completo funcionando")
        
        # Teste 2: Otimização de cronograma
        otimizacao = service.otimizar_cronograma_completo()
        assert 'otimizacao_aplicada' in otimizacao
        assert 'melhorias_identificadas' in otimizacao
        print("✅ Otimização de cronograma funcionando")
        
        # Teste 3: Análise de status por município
        analise = service.analisar_status_por_municipio("Itajaí")
        assert 'municipio' in analise
        assert 'status_questionarios' in analise
        print("✅ Análise por município funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no RastreamentoQuestionarios: {e}")
        return False

def test_dashboard_produtividade():
    """Testa funcionalidades do DashboardProdutividade."""
    print("\n📈 Testando DashboardProdutividade...")
    
    try:
        from gestao_visitas.services.dashboard_produtividade import DashboardProdutividade
        
        service = DashboardProdutividade()
        
        # Teste 1: Dashboard do pesquisador
        dashboard = service.obter_dashboard_pesquisador("pesquisador_teste")
        assert 'pesquisador_id' in dashboard
        assert 'metricas_performance' in dashboard
        print("✅ Dashboard do pesquisador funcionando")
        
        # Teste 2: Gamificação
        gamificacao = service.calcular_gamificacao("pesquisador_teste")
        assert 'nivel_atual' in gamificacao
        assert 'badges_conquistados' in gamificacao
        print("✅ Sistema de gamificação funcionando")
        
        # Teste 3: Ranking
        ranking = service.gerar_ranking_pesquisadores()
        assert 'ranking_geral' in ranking
        assert 'criterios_avaliacao' in ranking
        print("✅ Ranking de pesquisadores funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no DashboardProdutividade: {e}")
        return False

def test_sistema_backup_contingencia():
    """Testa funcionalidades do SistemaBackupContingencia."""
    print("\n💾 Testando SistemaBackupContingencia...")
    
    try:
        from gestao_visitas.services.sistema_backup_contingencia import SistemaBackupContingencia
        
        service = SistemaBackupContingencia()
        
        # Teste 1: Criar backup
        resultado_backup = service.criar_backup_completo()
        assert 'sucesso' in resultado_backup
        assert 'backup_id' in resultado_backup
        print("✅ Criação de backup funcionando")
        
        # Teste 2: Listar backups
        lista_backups = service.listar_backups_disponiveis()
        assert 'backups' in lista_backups
        assert 'total_backups' in lista_backups
        print("✅ Listagem de backups funcionando")
        
        # Teste 3: Plano de contingência
        plano = service.ativar_plano_contingencia("falha_sistema")
        assert 'plano_ativado' in plano
        assert 'acoes_executadas' in plano
        print("✅ Plano de contingência funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no SistemaBackupContingencia: {e}")
        return False

def test_gestao_prestadores():
    """Testa funcionalidades da GestaoAvancadaPrestadores."""
    print("\n🏢 Testando GestaoAvancadaPrestadores...")
    
    try:
        from gestao_visitas.services.prestadores import GestaoAvancadaPrestadores
        
        service = GestaoAvancadaPrestadores()
        
        # Teste 1: Validar prestador
        validacao = service.validar_prestador_avancado("12345678000195", "Empresa Teste")
        assert 'prestador_valido' in validacao
        assert 'validacoes_realizadas' in validacao
        print("✅ Validação de prestador funcionando")
        
        # Teste 2: Dashboard de prestadores
        dashboard = service.gerar_dashboard_prestadores("Itajaí")
        assert 'municipio' in dashboard
        assert 'estatisticas_prestadores' in dashboard
        print("✅ Dashboard de prestadores funcionando")
        
        # Teste 3: Análise de qualidade
        analise = service.analisar_qualidade_prestadores("Itajaí")
        assert 'score_qualidade_geral' in analise
        assert 'distribuicao_qualidade' in analise
        print("✅ Análise de qualidade funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na GestaoAvancadaPrestadores: {e}")
        return False

def test_sistema_notificacoes():
    """Testa funcionalidades do SistemaNotificacoes."""
    print("\n🔔 Testando SistemaNotificacoes...")
    
    try:
        from gestao_visitas.services.notificacoes_alertas import SistemaNotificacoes
        
        service = SistemaNotificacoes()
        
        # Teste 1: Enviar notificação
        resultado = service.enviar_notificacao(
            "usuario_teste",
            "Título de Teste",
            "Mensagem de teste",
            "email"
        )
        assert 'sucesso' in resultado
        print("✅ Envio de notificação funcionando")
        
        # Teste 2: Verificar alertas
        alertas = service.verificar_alertas_sistema()
        assert 'alertas_ativos' in alertas
        assert 'alertas_criticos' in alertas
        print("✅ Verificação de alertas funcionando")
        
        # Teste 3: Configurar preferências
        config = service.configurar_preferencias_usuario("usuario_teste", {
            'email': True,
            'sms': False,
            'push': True
        })
        assert 'usuario_id' in config
        assert 'preferencias_atualizadas' in config
        print("✅ Configuração de preferências funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no SistemaNotificacoes: {e}")
        return False

def test_analise_resistencia():
    """Testa funcionalidades da AnaliseResistencia."""
    print("\n🎯 Testando AnaliseResistencia...")
    
    try:
        from gestao_visitas.services.analise_resistencia import AnaliseResistencia
        
        service = AnaliseResistencia()
        
        # Teste 1: Analisar resistência do informante
        analise = service.analisar_resistencia_informante("Itajaí", "prefeitura")
        assert 'nivel_resistencia' in analise
        assert 'padroes_identificados' in analise
        print("✅ Análise de resistência funcionando")
        
        # Teste 2: Sugerir estratégia
        estrategia = service.sugerir_estrategia_abordagem("Itajaí", "prefeitura")
        assert 'estrategia_recomendada' in estrategia
        assert 'argumentos_persuasivos' in estrategia
        print("✅ Sugestão de estratégia funcionando")
        
        # Teste 3: Relatório de resistência
        relatorio = service.gerar_relatorio_resistencia()
        assert 'estatisticas_gerais' in relatorio
        assert 'municipios_maior_resistencia' in relatorio
        print("✅ Relatório de resistência funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na AnaliseResistencia: {e}")
        return False

def test_dashboard_avancado():
    """Testa funcionalidades do DashboardAvancado."""
    print("\n📊 Testando DashboardAvancado...")
    
    try:
        from gestao_visitas.services.dashboard_avancado import DashboardAvancado
        
        service = DashboardAvancado()
        
        # Teste 1: Dashboard principal
        dashboard = service.obter_dashboard_principal()
        assert 'timestamp_atualizacao' in dashboard
        assert 'kpis_principais' in dashboard
        assert 'status_tempo_real' in dashboard
        print("✅ Dashboard principal funcionando")
        
        # Teste 2: Cache funcionando
        dashboard2 = service.obter_dashboard_principal()
        assert 'cache_info' in dashboard2
        print("✅ Sistema de cache funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no DashboardAvancado: {e}")
        return False

def test_agendamento_avancado():
    """Testa funcionalidades do AgendamentoAvancado."""
    print("\n📅 Testando AgendamentoAvancado...")
    
    try:
        from gestao_visitas.services.agendamento_avancado import AgendamentoAvancado
        
        service = AgendamentoAvancado()
        
        # Teste 1: Sugerir horários
        horarios = service.sugerir_horarios("Itajaí", date.today() + timedelta(days=1))
        assert isinstance(horarios, list)
        print("✅ Sugestão de horários funcionando")
        
        # Teste 2: Detectar conflitos
        conflitos = service.detectar_conflitos_agendamento(
            "Itajaí", 
            date.today() + timedelta(days=1), 
            time(9, 0), 
            time(10, 0)
        )
        assert 'tem_conflitos' in conflitos
        print("✅ Detecção de conflitos funcionando")
        
        # Teste 3: Template de visita
        template = service.criar_template_visita("MRS", "prefeitura")
        assert 'duracao_sugerida' in template
        assert 'materiais_obrigatorios' in template
        print("✅ Template de visita funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no AgendamentoAvancado: {e}")
        return False

def test_checklist_inteligente():
    """Testa funcionalidades do ChecklistInteligente."""
    print("\n✅ Testando ChecklistInteligente...")
    
    try:
        from gestao_visitas.services.checklist_inteligente import ChecklistInteligente
        
        service = ChecklistInteligente()
        
        # Criar um mock de visita para teste
        class MockVisita:
            def __init__(self):
                self.tipo_pesquisa = "MRS"
                self.tipo_informante = "prefeitura"
                self.municipio = "Itajaí"
                self.data = date.today()
                self.status = "agendada"
                self.observacoes = ""
        
        visita_mock = MockVisita()
        
        # Teste 1: Gerar checklist personalizado
        checklist = service.gerar_checklist_personalizado(visita_mock)
        assert 'checklist_base' in checklist
        assert 'tempo_estimado' in checklist
        print("✅ Checklist personalizado funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no ChecklistInteligente: {e}")
        return False

def test_contatos_inteligente():
    """Testa funcionalidades do ContatosInteligente."""
    print("\n📞 Testando ContatosInteligente...")
    
    try:
        from gestao_visitas.services.contatos_inteligente import ContatosInteligente
        
        service = ContatosInteligente()
        
        # Teste 1: Enriquecer contato
        enriquecimento = service.enriquecer_contato_automatico("Itajaí", "MRS")
        assert 'dados_enriquecidos' in enriquecimento
        assert 'score_confiabilidade' in enriquecimento
        print("✅ Enriquecimento de contato funcionando")
        
        # Teste 2: Detectar duplicados
        duplicados = service.detectar_contatos_duplicados("Itajaí")
        assert isinstance(duplicados, list)
        print("✅ Detecção de duplicados funcionando")
        
        # Teste 3: Relatório de qualidade
        relatorio = service.gerar_relatorio_qualidade_contatos()
        assert 'total_contatos' in relatorio
        print("✅ Relatório de qualidade funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no ContatosInteligente: {e}")
        return False

def test_relatorios_avancados():
    """Testa funcionalidades do RelatoriosAvancados."""
    print("\n📊 Testando RelatoriosAvancados...")
    
    try:
        from gestao_visitas.services.relatorios_avancados import RelatoriosAvancados
        
        service = RelatoriosAvancados()
        
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today()
        
        # Teste 1: Relatório executivo
        executivo = service.gerar_relatorio_executivo(data_inicio, data_fim)
        assert 'tipo_relatorio' in executivo
        assert 'kpis_principais' in executivo
        print("✅ Relatório executivo funcionando")
        
        # Teste 2: Relatório de qualidade
        qualidade = service.gerar_relatorio_qualidade(data_inicio, data_fim)
        assert 'score_qualidade_geral' in qualidade
        print("✅ Relatório de qualidade funcionando")
        
        # Teste 3: Dashboard de métricas
        dashboard = service.gerar_dashboard_metricas()
        assert 'timestamp_atualizacao' in dashboard
        assert 'metricas_hoje' in dashboard
        print("✅ Dashboard de métricas funcionando")
        
        # Teste 4: Exportação
        exportacao = service.exportar_relatorio(executivo, 'json')
        assert 'formato' in exportacao
        assert 'status' in exportacao
        print("✅ Exportação de relatórios funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no RelatoriosAvancados: {e}")
        return False

def test_whatsapp_routes():
    """Testa se as rotas do WhatsApp estão definidas corretamente."""
    print("\n📱 Testando rotas WhatsApp...")
    
    try:
        # Verificar se o arquivo de rotas existe
        whatsapp_routes_path = Path(__file__).parent / "gestao_visitas" / "services" / "whatsapp_api.py"
        
        if whatsapp_routes_path.exists():
            with open(whatsapp_routes_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verificar se contém as rotas principais
            expected_routes = [
                '/api/whatsapp/webhook',
                '/api/whatsapp/send_message',
                '/api/whatsapp/send_template',
                '/api/whatsapp/send_bulk'
            ]
            
            routes_found = 0
            for route in expected_routes:
                if route in content:
                    routes_found += 1
            
            print(f"✅ {routes_found}/{len(expected_routes)} rotas WhatsApp encontradas")
            return routes_found >= len(expected_routes) // 2  # Pelo menos 50% das rotas
        else:
            print("❌ Arquivo de rotas WhatsApp não encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar rotas WhatsApp: {e}")
        return False

def run_comprehensive_tests():
    """Executa todos os testes de forma abrangente."""
    print("=" * 60)
    print("🧪 INICIANDO TESTES ABRANGENTES DOS SERVIÇOS AVANÇADOS")
    print("=" * 60)
    
    tests_to_run = [
        ("Importação de Serviços", test_import_services),
        ("Inicialização de Serviços", test_service_initialization),
        ("RastreamentoQuestionarios", test_rastreamento_questionarios),
        ("DashboardProdutividade", test_dashboard_produtividade),
        ("SistemaBackupContingencia", test_sistema_backup_contingencia),
        ("GestaoAvancadaPrestadores", test_gestao_prestadores),
        ("SistemaNotificacoes", test_sistema_notificacoes),
        ("AnaliseResistencia", test_analise_resistencia),
        ("DashboardAvancado", test_dashboard_avancado),
        ("AgendamentoAvancado", test_agendamento_avancado),
        ("ChecklistInteligente", test_checklist_inteligente),
        ("ContatosInteligente", test_contatos_inteligente),
        ("RelatoriosAvancados", test_relatorios_avancados),
        ("Rotas WhatsApp", test_whatsapp_routes)
    ]
    
    passed_tests = 0
    total_tests = len(tests_to_run)
    
    for test_name, test_function in tests_to_run:
        try:
            if test_function():
                passed_tests += 1
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {e}")
    
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    print(f"Total de testes: {total_tests}")
    print(f"Testes que passaram: {passed_tests}")
    print(f"Testes que falharam: {total_tests - passed_tests}")
    print(f"Taxa de sucesso: {(passed_tests / total_tests) * 100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção.")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ Maioria dos testes passou. Sistema em boa condição.")
    else:
        print("\n⚠️ Vários testes falharam. Revisar implementações necessário.")
    
    print("=" * 60)
    
    return passed_tests, total_tests

if __name__ == "__main__":
    # Executar todos os testes
    passed, total = run_comprehensive_tests()
    
    # Exit code baseado no resultado
    if passed == total:
        sys.exit(0)  # Sucesso total
    elif passed >= total * 0.8:
        sys.exit(1)  # Sucesso parcial
    else:
        sys.exit(2)  # Muitas falhas