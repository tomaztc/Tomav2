"""
Estagio 07 - Derivadas de estabilidade e controle (secao 3, Tabelas 6, 7 e 9).

Configuracao: CG traseiro, ponto de projeto, SEM restricao de trimagem
(profundor fixo em 0, i_t = valor do estagio 03).

Execucoes do AVL:
    R1  alpha = 0, i_t = 0, todas as deflexoes nulas        -> Tabela 6
    R2  CL = CL_projeto, i_t = i_t_aft, delta_e = 0         -> ft + st + sb
    R3/R4 alpha fixo de R2 com qc/2V = +-0.01               -> CDq (dif. finita)

Conversoes aplicadas (conforme o enunciado):
    * derivadas de controle e de i_t vem em 1/grau  -> x 180/pi
    * z_p, C_Ybeta, C_Yp, C_Yr  -> inverter sinal
    * C_ldeltaa, C_ldeltar, C_ndeltaa, C_ndeltar -> inverter sinal (e x 180/pi)
    * latero-direcionais de p, r, delta_a, delta_r vem do comando SB

Le   : out/01_design_point.json, out/03_tail_incidence.json, out/05_polars.json
Grava: out/07_tabela6.json, out/07_tabela7.json, out/07_tabela9.json
       out/07_tabela9.csv, out/07_derivadas_brutas.json
"""

import numpy as np

from . import avlrun, config, util

R2D = 180.0 / np.pi


def _cd(ft):
    return ft['CDvis'] + ft['CDff']


def run():
    util.banner('Estagio 07 - Derivadas de estabilidade e controle (CG traseiro)')
    dp = util.load('01_design_point')
    tail = util.load('03_tail_incidence')
    pol = util.load('05_polars')

    t1 = dp['tabela1']
    mach, CL_dp = t1['M'], t1['CL']
    it_aft = tail['aft']['it']

    # ---------------- R1: Tabela 6 ----------------------------------------
    r1 = avlrun.run_case('aft', mach, alpha=0.0, it=0.0, elevator=0.0,
                         want=('ft',), tag='s07_r1')
    tab6 = {
        '_comment': 'alpha=0, i_t=0, beta=0, pb/2V=rb/2V=0, da=dr=0.',
        'CL0': r1['ft']['CLtot'],
        'CM0': r1['ft']['Cmtot'],
        'CD_alpha0': _cd(r1['ft']),
    }

    # ---------------- R2: ponto de projeto --------------------------------
    r2 = avlrun.run_case('aft', mach, CL=CL_dp, it=it_aft, elevator=0.0,
                         want=('ft', 'st', 'sb'), tag='s07_r2')
    ft, st, sb = r2['ft'], r2['st'], r2['sb']
    alpha_dp = ft['Alpha']

    # ---------------- R3/R4: CDq por diferenca finita ---------------------
    dq = 0.01
    rp = avlrun.run_case('aft', mach, alpha=alpha_dp, it=it_aft, elevator=0.0,
                         pitch_rate=+dq, want=('ft',), tag='s07_qp')
    rm = avlrun.run_case('aft', mach, alpha=alpha_dp, it=it_aft, elevator=0.0,
                         pitch_rate=-dq, want=('ft',), tag='s07_qm')
    CDq = (_cd(rp['ft']) - _cd(rm['ft'])) / (2 * dq)

    # ---------------- Tabela 7 (vem do estagio 05) ------------------------
    fit = pol['ajuste_CD_alpha']
    tab7 = {'_comment': 'CD = CD0 + CDa*alpha + CDa2*alpha^2 (alpha em rad), '
                        'ajuste da questao 5.b (CG traseiro, sem deflexoes).',
            'CD0': fit['CD0'], 'CDa': fit['CDa'], 'CDa2': fit['CDa2'],
            'rms': fit['rms']}

    # ---------------- Tabela 9 --------------------------------------------
    ig = dp['inputs_geom']
    moi = dp['moment_of_inertia']
    xcg = dp['xcg_aft']

    t9 = {}
    t9['S_ref'] = dp['S_ref']
    t9['c_ref'] = dp['c_ref']
    t9['b_ref'] = dp['b_ref']
    t9['m'] = dp['mass_design_point']
    t9['Ixx'] = moi['Ixx']
    t9['Iyy'] = moi['Iyy']
    t9['Izz'] = moi['Izz']
    t9['Ixz'] = moi['Ixz']
    t9['ip'] = config.IP_DEG
    # posicao do motor em relacao ao CG; z_p com sinal invertido (MVO: z p/ baixo)
    t9['xp'] = ig['x_n'] + ig['L_n'] / 2 - xcg
    t9['zp'] = -(ig['z_n'] - dp['zcg'])
    t9['Tmax'] = dp['Tmax']
    t9['V'] = t1['V']
    t9['h'] = t1['h']

    t9['CL0'] = tab6['CL0']
    t9['CLa'] = st['CLa']
    t9['CLq'] = st['CLq']
    t9['CLit'] = st['CLg01'] * R2D
    t9['CLde'] = st['CLd02'] * R2D

    t9['CD0'] = tab7['CD0']
    t9['CDa'] = tab7['CDa']
    t9['CDa2'] = tab7['CDa2']
    t9['CDq'] = CDq
    t9['CDit'] = st['CDffg01'] * R2D
    t9['CDde'] = st['CDffd02'] * R2D

    t9['CM0'] = tab6['CM0']
    t9['CMa'] = st['Cma']
    t9['CMq'] = st['Cmq']
    t9['CMit'] = st['Cmg01'] * R2D
    t9['CMde'] = st['Cmd02'] * R2D

    t9['CYb'] = -st['CYb']                 # inverter sinal
    t9['CYp'] = -st['CYp']                 # inverter sinal
    t9['CYr'] = -st['CYr']                 # inverter sinal
    t9['CYdr'] = st['CYd03'] * R2D

    t9['Clb'] = st['Clb']
    t9['Clp'] = sb['Clp']
    t9['Clr'] = sb['Clr']
    t9['Clda'] = -sb['Cld01'] * R2D        # inverter sinal
    t9['Cldr'] = -sb['Cld03'] * R2D        # inverter sinal

    t9['Cnb'] = st['Cnb']
    t9['Cnp'] = sb['Cnp']
    t9['Cnr'] = sb['Cnr']
    t9['Cnda'] = -sb['Cnd01'] * R2D        # inverter sinal
    t9['Cndr'] = -sb['Cnd03'] * R2D        # inverter sinal

    tab9 = {'_comment': 'Tabela 9 ja com as conversoes de sinal e de unidade '
                        'pedidas no enunciado.',
            'condicao': {'cg': 'traseiro', 'xcg': xcg, 'Mach': mach,
                         'CL': CL_dp, 'alpha_deg': alpha_dp, 'it_deg': it_aft,
                         'delta_e_deg': 0.0, 'trimagem': False},
            'valores': t9}

    brutas = {'_comment': 'Saidas cruas do AVL, antes de qualquer conversao.',
              'R1_ft_alpha0_it0': r1['ft'],
              'R2_ft': ft, 'R2_st': st, 'R2_sb': sb,
              'R3_ft_q_mais': rp['ft'], 'R4_ft_q_menos': rm['ft'],
              'CDq_diferenca_finita': CDq, 'dq': dq}

    util.save('07_tabela6', tab6)
    util.save('07_tabela7', tab7)
    util.save('07_tabela9', tab9)
    util.save('07_derivadas_brutas', brutas)

    ordem = ['S_ref', 'c_ref', 'b_ref', 'm', 'Ixx', 'Iyy', 'Izz', 'Ixz',
             'ip', 'xp', 'zp', 'Tmax', 'V', 'h',
             'CL0', 'CLa', 'CLq', 'CLit', 'CLde',
             'CD0', 'CDa', 'CDa2', 'CDq', 'CDit', 'CDde',
             'CM0', 'CMa', 'CMq', 'CMit', 'CMde',
             'CYb', 'CYp', 'CYr', 'CYdr',
             'Clb', 'Clp', 'Clr', 'Clda', 'Cldr',
             'Cnb', 'Cnp', 'Cnr', 'Cnda', 'Cndr']
    util.save_table_csv('07_tabela9', [[k, t9[k]] for k in ordem],
                        ['parametro', 'valor'])

    print('\n  Tabela 6:  CL0 = %+.6f     CM0 = %+.6f'
          % (tab6['CL0'], tab6['CM0']))
    print('  Tabela 7:  CD0 = %+.6f  CDa = %+.6f  CDa2 = %+.6f'
          % (tab7['CD0'], tab7['CDa'], tab7['CDa2']))
    print('  Ponto de projeto: alpha = %+.3f deg, i_t = %+.3f deg, delta_e = 0'
          % (alpha_dp, it_aft))
    print('\n  Tabela 9:')
    for k in ordem:
        print('    %-6s = %+14.6g' % (k, t9[k]))
    return tab9


if __name__ == '__main__':
    run()
