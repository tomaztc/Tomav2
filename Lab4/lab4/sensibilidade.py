"""
Estudo de sensibilidade do modelo AVL: fuselagem (BODY) e nacelles ligadas
ou desligadas.

O BODY do AVL e um modelo de corpo esbelto bem grosseiro e muda bastante
Cma, x_np e sobretudo Cnb. Este script quantifica o efeito e devolve os
arquivos .avl ao estado configurado em config.py no final.

Grava: out/90_sensibilidade.json / .csv
"""

import contextlib
import io

from . import avlrun, config, util


def run():
    util.banner('Sensibilidade do modelo AVL - BODY e NACELLE')
    dp = util.load('01_design_point')
    tail = util.load('03_tail_incidence')
    mach, CL = dp['tabela1']['M'], dp['tabela1']['CL']
    xm_w, c_ref = dp['xm_w'], dp['c_ref']

    from . import s02_avl_geometry

    body0, nac0 = config.INCLUDE_BODY, config.INCLUDE_NACELLES
    linhas, rows = [], []
    try:
        for body in (True, False):
            for nac in (True, False):
                config.INCLUDE_BODY, config.INCLUDE_NACELLES = body, nac
                with contextlib.redirect_stdout(io.StringIO()):
                    s02_avl_geometry.run()
                r = avlrun.run_case('aft', mach, CL=CL, it=tail['aft']['it'],
                                    elevator=0.0, want=('st',),
                                    tag='sens_%d%d' % (body, nac))
                st = r['st']
                item = {'body': body, 'nacelle': nac,
                        'CLa': st['CLa'], 'Cma': st['Cma'],
                        'CYb': st['CYb'], 'Clb': st['Clb'], 'Cnb': st['Cnb'],
                        'xnp': st['Xnp'],
                        'xnp_pct_mac': (st['Xnp'] - xm_w) / c_ref * 100,
                        'SM_aft': (st['Xnp'] - dp['xcg_aft']) / c_ref}
                linhas.append(item)
                rows.append([body, nac, item['CLa'], item['Cma'],
                             item['CYb'], item['Clb'], item['Cnb'],
                             item['xnp'], item['xnp_pct_mac'],
                             item['SM_aft'] * 100])
                print('  BODY=%-5s NACELLE=%-5s | Cma=%+7.3f  Cnb=%+7.4f  '
                      'CYb=%+7.4f  x_np=%7.3f m (%5.1f%% MAC)  SM_aft=%5.1f%%'
                      % (body, nac, item['Cma'], item['Cnb'], item['CYb'],
                         item['xnp'], item['xnp_pct_mac'],
                         item['SM_aft'] * 100))
    finally:
        # devolve os .avl ao estado configurado
        config.INCLUDE_BODY, config.INCLUDE_NACELLES = body0, nac0
        with contextlib.redirect_stdout(io.StringIO()):
            s02_avl_geometry.run()

    print('\n  Referencias para comparacao:')
    print('    designTool: x_np = %.3f m (%.1f%% MAC), SM_aft = %.1f%%'
          % (dp['xnp_designtool'],
             (dp['xnp_designtool'] - xm_w) / c_ref * 100,
             dp['SM_aft_designtool'] * 100))
    print('  Arquivos .avl restaurados para BODY=%s, NACELLE=%s'
          % (body0, nac0))

    util.save('90_sensibilidade',
              {'_comment': 'Efeito do BODY e das nacelles no modelo AVL.',
               'configuracao_atual': {'INCLUDE_BODY': body0,
                                      'INCLUDE_NACELLES': nac0},
               'referencia_designTool': {
                   'xnp': dp['xnp_designtool'],
                   'xnp_pct_mac': (dp['xnp_designtool'] - xm_w) / c_ref * 100,
                   'SM_aft': dp['SM_aft_designtool']},
               'casos': linhas})
    util.save_table_csv('90_sensibilidade', rows,
                        ['body', 'nacelle', 'CLa', 'Cma', 'CYb', 'Clb', 'Cnb',
                         'xnp_m', 'xnp_pct_mac', 'SM_aft_pct'])
    return linhas


if __name__ == '__main__':
    run()
