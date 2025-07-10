from Agente_IA import db
from Agente_IA.gestao_visitas.models.agendamento import Visita

def corrigir_tipo_informante():
    visitas = Visita.query.all()
    alteradas = 0
    for visita in visitas:
        if visita.tipo_informante and visita.tipo_informante != visita.tipo_informante.lower():
            visita.tipo_informante = visita.tipo_informante.lower()
            alteradas += 1
    db.session.commit()
    print(f'Corrigidas {alteradas} visitas.')

if __name__ == '__main__':
    corrigir_tipo_informante() 