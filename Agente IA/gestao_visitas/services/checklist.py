def salvar_checklist_etapa(checklist, etapa, dados):
    campos = get_campos_etapa(etapa)
    for campo in campos:
        if campo in dados:
            setattr(checklist, campo, dados[campo])
    return checklist

def excluir_checklist_etapa(checklist, etapa):
    campos = get_campos_etapa(etapa)
    for campo in campos:
        setattr(checklist, campo, None)
    return checklist

def get_campos_etapa(etapa):
    if etapa == 'Antes da Visita':
        return ['cracha_ibge', 'recibo_entrega', 'questionario_mrs_impresso', 'questionario_map_impresso',
                'carta_oficial', 'questionario_mrs_digital', 'questionario_map_digital', 'manual_pnsb',
                'guia_site_externo', 'card_contato', 'audio_explicativo', 'planejamento_rota', 'agenda_confirmada']
    elif etapa == 'Durante a Visita':
        return ['apresentacao_ibge', 'explicacao_objetivo', 'explicacao_estrutura', 'explicacao_data_referencia',
                'explicacao_prestador', 'explicacao_servicos', 'explicacao_site_externo', 'explicacao_pdf_editavel',
                'validacao_prestadores', 'registro_contatos', 'assinatura_informante', 'observacoes_durante']
    elif etapa == 'Após a Visita':
        return ['devolucao_materiais', 'registro_followup', 'combinacao_entrega', 'combinacao_acompanhamento', 'observacoes_finais']
    return [] 