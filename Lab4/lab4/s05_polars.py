"""
Estagio 05 - Polares e curvas de sustentacao/profundor (questoes 5, 6 e 7).

Gera, no Mach do ponto de projeto, as quatro varreduras pedidas:
    a) CG dianteiro, sem deflexao de superficie de controle (delta_e = 0)
    b) CG traseiro,  sem deflexao de superficie de controle (delta_e = 0)
    c) CG dianteiro, arfagem compensada (Cm = 0 pelo profundor)
    d) CG traseiro,  arfagem compensada (Cm = 0 pelo profundor)

Cada varredura vai de config.CL_MIN_PLOT ate o CLmax do caso correspondente
do metodo da secao critica (estagio 04).

Tambem faz o ajuste quadratico CD = CD0 + CDa*alpha + CDa2*alpha^2 exigido na
Tabela 7 (usando a varredura 'b', CG traseiro sem deflexoes).

Le   : out/01_design_point.json, out/03_tail_incidence.json,
       out/04_critical_section.json
Grava: out/05_polars.json, out/05_polar_<caso>.csv
"""

import numpy as np

from . import avlrun, config, util

CASES = [
    ('a_fwd_clean', 'fwd', False, 'CG dianteiro, sem deflexao',  'fwd_notrim'),
    ('b_aft_clean', 'aft', False, 'CG traseiro, sem deflexao',   'aft_notrim'),
    ('c_fwd_trim',  'fwd', True,  'CG dianteiro, Cm = 0',        'fwd_trim'),
    ('d_aft_trim',  'aft', True,  'CG traseiro, Cm = 0',         'aft_trim'),
]


def _cd(ft):
    """CD usado nos graficos (ver config.USE_TREFFTZ_DRAG)."""
    if config.USE_TREFFTZ_DRAG:
        return ft['CDvis'] + ft['CDff']
    return ft['CDtot']


def sweep(cg, trim, it, mach, CL_list, tag):
    pts = []
    for i, CL in enumerate(CL_list):
        r = avlrun.run_case(cg, mach, CL=CL, it=it, trim_elevator=trim,
                            want=('ft',), tag='%s_%02d' % (tag, i))
        ft = r['ft']
        pts.append({
            'CL': ft['CLtot'],
            'alpha': ft['Alpha'],
            'CD': _cd(ft),
            'CDtot_avl': ft['CDtot'],
            'CDvis': ft['CDvis'],
            'CDff': ft['CDff'],
            'CDind': ft['CDind'],
            'delta_e': ft['elevator'],
            'Cm': ft['Cmtot'],
            'e': ft.get('e'),
        })
    return pts


def _interp(pts, key_x, x, key_y):
    xs = np.array([p[key_x] for p in pts])
    ys = np.array([p[key_y] for p in pts])
    order = np.argsort(xs)
    return float(np.interp(x, xs[order], ys[order]))


def run():
    util.banner('Estagio 05 - Polares, CL x alpha e CL x delta_e')
    dp = util.load('01_design_point')
    tail = util.load('03_tail_incidence')
    crit = util.load('04_critical_section')

    mach = dp['tabela1']['M']
    CL_dp = dp['tabela1']['CL']

    res = {'_comment': 'Varreduras do AVL no Mach do ponto de projeto.',
           'mach': mach, 'CL_design': CL_dp,
           'drag_model': ('CDvis + CDff (Trefftz)' if config.USE_TREFFTZ_DRAG
                          else 'CDtot do AVL (campo proximo)'),
           'casos': {}}

    for key, cg, trim, nome, crit_key in CASES:
        it = tail[cg]['it']
        CLmax = crit['casos'][crit_key]['CLmax']
        CL_list = np.linspace(config.CL_MIN_PLOT, CLmax, config.N_POLAR_POINTS)
        pts = sweep(cg, trim, it, mach, CL_list, 's05_' + key)

        caso = {'nome': nome, 'cg': cg, 'trim': trim, 'it': it,
                'CLmax': CLmax, 'pontos': pts}
        caso['no_ponto_de_projeto'] = {
            'CL': CL_dp,
            'CD': _interp(pts, 'CL', CL_dp, 'CD'),
            'alpha': _interp(pts, 'CL', CL_dp, 'alpha'),
            'delta_e': _interp(pts, 'CL', CL_dp, 'delta_e'),
        }
        res['casos'][key] = caso

        util.save_table_csv(
            '05_polar_' + key,
            [[p['alpha'], p['CL'], p['CD'], p['CDtot_avl'], p['delta_e'],
              p['Cm']] for p in pts],
            ['alpha_deg', 'CL', 'CD', 'CD_avl_nearfield', 'delta_e_deg', 'Cm'])

    # ---- Tabela comparativa no ponto de projeto ---------------------------
    CD_dt = dp['CD0_breakdown']['CD']
    res['comparacao_designTool'] = {
        'CD_designTool': CD_dt,
        'CD0_designTool': dp['CD0'],
        'CDwave_designTool': dp['CD0_breakdown'].get('CDwave'),
        'CDind_designTool': dp['CD0_breakdown'].get('CDind'),
        'por_caso': {k: res['casos'][k]['no_ponto_de_projeto']['CD']
                     for k, *_ in CASES},
    }

    # ---- Ajuste quadratico CD(alpha) - Tabela 7 ---------------------------
    pts_b = res['casos']['b_aft_clean']['pontos']
    al = np.radians([p['alpha'] for p in pts_b])
    cd = np.array([p['CD'] for p in pts_b])
    c2, c1, c0 = np.polyfit(al, cd, 2)
    res['ajuste_CD_alpha'] = {
        '_comment': 'CD = CD0 + CDa*alpha + CDa2*alpha^2, alpha em rad. '
                    'Ajuste sobre o caso b (CG traseiro, sem deflexoes).',
        'CD0': float(c0), 'CDa': float(c1), 'CDa2': float(c2),
        'rms': float(np.sqrt(np.mean((np.polyval([c2, c1, c0], al) - cd) ** 2))),
    }

    util.save('05_polars', res)

    print('\n  CD no CL do ponto de projeto (CL = %.4f):' % CL_dp)
    for key, cg, trim, nome, _ in CASES:
        d = res['casos'][key]['no_ponto_de_projeto']
        print('    %-30s CD = %.5f   alpha = %+6.3f deg   delta_e = %+7.3f deg'
              % (nome, d['CD'], d['alpha'], d['delta_e']))
    print('    %-30s CD = %.5f   (CD0=%.5f + CDind=%.5f + CDwave=%.5f)'
          % ('designTool', CD_dt, dp['CD0'],
             dp['CD0_breakdown'].get('CDind', 0.0),
             dp['CD0_breakdown'].get('CDwave', 0.0)))
    f = res['ajuste_CD_alpha']
    print('\n  Tabela 7 (ajuste quadratico, caso b):')
    print('    CD0   = %.6f' % f['CD0'])
    print('    CDa   = %.6f  1/rad' % f['CDa'])
    print('    CDa2  = %.6f  1/rad^2   (rms = %.2e)' % (f['CDa2'], f['rms']))
    return res


if __name__ == '__main__':
    run()
