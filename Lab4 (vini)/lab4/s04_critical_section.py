"""
Estagio 04 - Metodo da secao critica (questao 4).

Determina o CLmax de asa limpa em baixa velocidade (M = config.MACH_LOWSPEED)
para os 4 casos: CG dianteiro/traseiro x com/sem trimagem.

Como o AVL e linear, cl_norm de cada faixa varia linearmente com alpha. Por
isso o alpha de estol e obtido exatamente a partir de duas execucoes
(alpha = 0 e alpha = 10 graus) e depois VERIFICADO com uma execucao no alpha
encontrado - e essa execucao verificada que alimenta as tabelas e os graficos.

Le   : out/01_design_point.json, out/03_tail_incidence.json
Grava: out/04_critical_section.json   (tabela + distribuicoes cl x y)
       out/04_critical_section.csv    (tabela resumida)

Editavel: 'clmax_root'/'clmax_tip' vem de config.py ou da polar do Lab 03;
altere-os em config.py e rode este estagio de novo.
"""

import os
import re

import numpy as np

from . import avlrun, config, util


# ---------------------------------------------------------------------------
def read_clmax_from_polar(path):
    """Maior CL da polar XFOIL do perfil (Lab 03, M = 0.2)."""
    cls = []
    with open(path) as fid:
        for line in fid:
            toks = line.split()
            if len(toks) >= 7:
                try:
                    cls.append((float(toks[0]), float(toks[1])))
                except ValueError:
                    continue
    if not cls:
        raise RuntimeError('Nao consegui ler a polar %s' % path)
    alpha, clmax = max(cls, key=lambda t: t[1])
    return clmax, alpha


def clmax_distribution(y, b2, clmax_root, clmax_tip):
    """cl_max local (linear entre raiz e ponta)."""
    eta = np.clip(np.asarray(y) / b2, 0.0, 1.0)
    return clmax_root + eta * (clmax_tip - clmax_root)


# ---------------------------------------------------------------------------
def _wing_strips(res):
    w = res['fs']['Wing']
    return w['Yle'], w['Chord'], w['cl_norm'], w['cl']


def stall_case(cg, it, trim, mach, b2, clmax_root, clmax_tip, tag):
    """Encontra alpha de estol e devolve o estado verificado nesse alpha."""
    a1, a2 = 0.0, 10.0
    r1 = avlrun.run_case(cg, mach, alpha=a1, it=it, trim_elevator=trim,
                         want=('ft', 'fs'), tag=tag + '_a1')
    r2 = avlrun.run_case(cg, mach, alpha=a2, it=it, trim_elevator=trim,
                         want=('ft', 'fs'), tag=tag + '_a2')

    y, ch, cl1, _ = _wing_strips(r1)
    _, _, cl2, _ = _wing_strips(r2)
    clmax_local = clmax_distribution(y, b2, clmax_root, clmax_tip)

    slope = (cl2 - cl1) / (a2 - a1)
    with np.errstate(divide='ignore', invalid='ignore'):
        a_stall = np.where(slope > 1e-9, (clmax_local - cl1) / slope, np.inf)
    j_crit = int(np.argmin(a_stall))
    alpha_max = float(a_stall[j_crit])

    # verificacao no alpha encontrado
    rv = avlrun.run_case(cg, mach, alpha=alpha_max, it=it, trim_elevator=trim,
                         want=('ft', 'fs'), tag=tag + '_v')
    yv, chv, clv, clv2 = _wing_strips(rv)
    ftv = rv['ft']

    return {
        'alpha_max': alpha_max,
        'CLmax': ftv['CLtot'],
        'delta_e': ftv['elevator'],
        'Cmtot': ftv['Cmtot'],
        'it': it,
        'y_crit': float(y[j_crit]),
        'eta_crit': float(y[j_crit] / b2),
        'clmax_crit': float(clmax_local[j_crit]),
        'cl_norm_crit': float(clv[j_crit]),
        'dist': {
            'y': [float(v) for v in yv],
            'eta': [float(v / b2) for v in yv],
            'chord': [float(v) for v in chv],
            'cl_norm': [float(v) for v in clv],
            'cl': [float(v) for v in clv2],
            'cl_max_local': [float(v) for v in clmax_local],
        },
    }


# ---------------------------------------------------------------------------
def run():
    util.banner('Estagio 04 - Metodo da secao critica (CLmax de asa limpa)')
    dp = util.load('01_design_point')
    tail = util.load('03_tail_incidence')

    b2 = dp['b_ref'] / 2
    mach = config.MACH_LOWSPEED

    if config.CLMAX_AIRFOIL_ROOT is None:
        clmax_root, a_clmax = read_clmax_from_polar(config.AIRFOIL_POLAR)
        src = 'polar XFOIL do Lab 03 (%s), alpha = %.2f deg' % (
            os.path.basename(os.path.dirname(config.AIRFOIL_POLAR)), a_clmax)
    else:
        clmax_root, src = config.CLMAX_AIRFOIL_ROOT, 'config.py'
    clmax_tip = (config.CLMAX_AIRFOIL_TIP if config.CLMAX_AIRFOIL_TIP
                 is not None else clmax_root)

    print('  cl_max do perfil: raiz = %.4f, ponta = %.4f  (fonte: %s)'
          % (clmax_root, clmax_tip, src))
    print('  Mach de baixa velocidade = %.2f\n' % mach)

    casos = [
        ('CG dianteiro sem trimagem', 'fwd', False),
        ('CG dianteiro com trimagem', 'fwd', True),
        ('CG traseiro sem trimagem', 'aft', False),
        ('CG traseiro com trimagem', 'aft', True),
    ]

    res = {'_comment': 'Metodo da secao critica. dist = distribuicoes cl x y '
                       'na condicao de estol.',
           'mach': mach, 'clmax_root': clmax_root, 'clmax_tip': clmax_tip,
           'clmax_source': src, 'casos': {}}

    rows = []
    for nome, cg, trim in casos:
        it = tail[cg]['it']
        key = '%s_%s' % (cg, 'trim' if trim else 'notrim')
        out = stall_case(cg, it, trim, mach, b2, clmax_root, clmax_tip,
                         's04_' + key)
        out['nome'] = nome
        out['cg'] = cg
        out['trim'] = trim
        res['casos'][key] = out
        rows.append([nome, it, out['alpha_max'], out['CLmax'],
                     out['delta_e'], out['eta_crit']])
        print('  %-28s  alpha_max = %6.2f deg   CLmax = %6.4f   '
              'delta_e = %+7.3f deg   estol em y/(b/2) = %.3f'
              % (nome, out['alpha_max'], out['CLmax'], out['delta_e'],
                 out['eta_crit']))

    util.save('04_critical_section', res)
    util.save_table_csv('04_critical_section', rows,
                        ['caso', 'it_deg', 'alpha_max_deg', 'CLmax',
                         'delta_e_deg', 'eta_estol'])
    return res


if __name__ == '__main__':
    run()
