"""
Estagio 03 - Incidencia da empenagem horizontal (questao 3).

Para cada posicao de CG procura o i_t que anula a deflexao de profundor
necessaria para trimar (Cm = 0) a aeronave no ponto de projeto.

Como delta_e(i_t) e linear, duas avaliacoes + secante convergem praticamente
de imediato; o laco e mantido com tolerancia de config.IT_TOL_DEG.

Le   : out/01_design_point.json, avl/fwd.avl, avl/aft.avl
Grava: out/03_tail_incidence.json   (it_fwd, it_aft e historico de iteracoes)

Editavel: se quiser impor outro i_t (por exemplo um valor arredondado ou um
i_t unico para os dois CGs), edite 'it' em out/03_tail_incidence.json.
"""

from . import avlrun, config, util


def _delta_e(cg, it, CL, mach, tag):
    r = avlrun.run_case(cg, mach, CL=CL, it=it, trim_elevator=True,
                        want=('ft',), tag=tag)
    ft = r['ft']
    return ft['elevator'], ft


def solve_it(cg, CL, mach):
    hist = []
    it0, it1 = 0.0, -2.0
    d0, ft0 = _delta_e(cg, it0, CL, mach, 's03_%s_0' % cg)
    hist.append({'it': it0, 'delta_e': d0})
    d1, ft1 = _delta_e(cg, it1, CL, mach, 's03_%s_1' % cg)
    hist.append({'it': it1, 'delta_e': d1})

    ft = ft1
    for k in range(config.IT_MAX_ITER):
        if abs(d1) < config.IT_TOL_DEG:
            break
        if abs(d1 - d0) < 1e-12:
            break
        it2 = it1 - d1 * (it1 - it0) / (d1 - d0)
        d2, ft = _delta_e(cg, it2, CL, mach, 's03_%s_%d' % (cg, k + 2))
        hist.append({'it': it2, 'delta_e': d2})
        it0, d0, it1, d1 = it1, d1, it2, d2

    return it1, d1, ft, hist


def run():
    util.banner('Estagio 03 - Incidencia da empenagem horizontal (i_t)')
    dp = util.load('01_design_point')
    util.load('02_avl_model')          # garante que os .avl existem

    CL = dp['tabela1']['CL']
    mach = dp['tabela1']['M']

    res = {'_comment': 'i_t que anula delta_e no ponto de projeto. '
                       'Edite "it" para impor outro valor.',
           'CL_design': CL, 'Mach': mach}

    for cg in ('fwd', 'aft'):
        it, de, ft, hist = solve_it(cg, CL, mach)
        res[cg] = {
            'it': it,
            'delta_e_residual': de,
            'alpha': ft['Alpha'],
            'CLtot': ft['CLtot'],
            'CDtot': ft['CDtot'],
            'CDff': ft.get('CDff'),
            'CDvis': ft.get('CDvis'),
            'Cmtot': ft['Cmtot'],
            'e': ft.get('e'),
            'iteracoes': hist,
        }
        print('  CG %s : i_t = %+8.4f deg   (delta_e residual = %+.4f deg, '
              'alpha = %+.3f deg)' % (cg, it, de, ft['Alpha']))

    util.save('03_tail_incidence', res)
    util.save_table_csv(
        '03_tail_incidence',
        [[cg, res[cg]['it'], res[cg]['delta_e_residual'], res[cg]['alpha'],
          res[cg]['CLtot'], res[cg]['CDtot']] for cg in ('fwd', 'aft')],
        ['CG', 'it_deg', 'delta_e_deg', 'alpha_deg', 'CL', 'CD'])
    return res


if __name__ == '__main__':
    run()
