"""
Estagio 06 - Ponto neutro e margens estaticas (questao 8).

O ponto neutro nao depende do Xref usado; mesmo assim rodamos os dois CGs
para mostrar que o AVL devolve o mesmo x_np, e comparamos com o designTool.

Le   : out/01_design_point.json, out/03_tail_incidence.json
Grava: out/06_neutral_point.json
"""

from . import avlrun, util


def run():
    util.banner('Estagio 06 - Ponto neutro e margem estatica')
    dp = util.load('01_design_point')
    tail = util.load('03_tail_incidence')

    CL = dp['tabela1']['CL']
    mach = dp['tabela1']['M']
    xm_w, cm_w = dp['xm_w'], dp['c_ref']

    res = {'_comment': 'x_np do AVL e margens estaticas. SM = (x_np - x_cg)/c_ref.',
           'c_ref': cm_w, 'xm_w': xm_w, 'Mach': mach, 'CL': CL}

    xnps = {}
    for cg in ('fwd', 'aft'):
        r = avlrun.run_case(cg, mach, CL=CL, it=tail[cg]['it'],
                            elevator=0.0, want=('st',), tag='s06_' + cg)
        xnps[cg] = r['st']['Xnp']
        res['%s_Cma' % cg] = r['st']['Cma']
        res['%s_CLa' % cg] = r['st']['CLa']

    xnp = xnps['aft']
    res['xnp_avl'] = xnp
    res['xnp_avl_fwd_run'] = xnps['fwd']
    res['xnp_pct_mac'] = (xnp - xm_w) / cm_w * 100
    res['xnp_designtool'] = dp['xnp_designtool']
    res['xnp_designtool_pct_mac'] = (dp['xnp_designtool'] - xm_w) / cm_w * 100

    for cg, xcg in (('fwd', dp['xcg_fwd']), ('aft', dp['xcg_aft'])):
        res['SM_%s' % cg] = (xnp - xcg) / cm_w
        res['xcg_%s' % cg] = xcg
        res['xcg_%s_pct_mac' % cg] = (xcg - xm_w) / cm_w * 100
    res['SM_fwd_designtool'] = dp['SM_fwd_designtool']
    res['SM_aft_designtool'] = dp['SM_aft_designtool']

    print('  x_np (AVL)        = %.4f m  (%.1f%% MAC)'
          % (xnp, res['xnp_pct_mac']))
    print('  x_np (designTool) = %.4f m  (%.1f%% MAC)'
          % (dp['xnp_designtool'], res['xnp_designtool_pct_mac']))
    print('  x_cg dianteiro    = %.4f m  (%.1f%% MAC)  ->  SM = %.1f%%  '
          '(designTool: %.1f%%)'
          % (dp['xcg_fwd'], res['xcg_fwd_pct_mac'], res['SM_fwd'] * 100,
             dp['SM_fwd_designtool'] * 100))
    print('  x_cg traseiro     = %.4f m  (%.1f%% MAC)  ->  SM = %.1f%%  '
          '(designTool: %.1f%%)'
          % (dp['xcg_aft'], res['xcg_aft_pct_mac'], res['SM_aft'] * 100,
             dp['SM_aft_designtool'] * 100))

    util.save('06_neutral_point', res)
    return res


if __name__ == '__main__':
    run()
