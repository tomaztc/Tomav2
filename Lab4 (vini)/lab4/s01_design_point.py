"""
Estagio 01 - Base designTool + ponto de projeto (Tabela 1).

Saidas:
    out/01_airplane.json      dicionario completo do designTool (referencia)
    out/01_design_point.json  Tabela 1 + tudo que os estagios seguintes usam
                              (geometria, CG, CD0, massa, inercias)

Editavel: qualquer campo de out/01_design_point.json pode ser alterado a mao;
os estagios 02+ leem exclusivamente desse arquivo.
"""

import numpy as np

from . import config, util


def run():
    util.banner('Estagio 01 - designTool + ponto de projeto')

    dT = util.import_designtool()
    from designTool.standard_airplane import standard_airplane
    from designTool.analyze import analyze
    from designTool.aerodynamics import aerodynamics
    from designTool.auxiliary import atmosphere
    from designTool.moment_of_inertia import moment_of_inertia
    from designTool.constants import gravity

    airplane = standard_airplane(config.AIRPLANE_NAME)
    analyze(airplane, plot=False, print_log=True)

    inp = airplane['inputs']
    geo = airplane['geometry']
    tm = airplane['thrust_matching']
    bal = airplane['balance']

    # ---------------- Condicao de voo -------------------------------------
    Mach = config.DESIGN_MACH if config.DESIGN_MACH else inp['Mach_cruise']
    h = config.DESIGN_ALTITUDE if config.DESIGN_ALTITUDE else inp['altitude_cruise']
    atm = atmosphere(h)
    rho, a = atm['density'], atm['speed_of_sound']
    V = Mach * a

    # ---------------- Peso no ponto de projeto ----------------------------
    W0 = tm['W0']
    W = (tm['W_empty'] + inp['W_crew']
         + config.PAYLOAD_FRAC * inp['W_payload']
         + config.FUEL_FRAC * tm['W_fuel'])

    S_w = inp['S_w']
    CL = W / (0.5 * rho * V ** 2 * S_w)

    # ---------------- Arrasto parasita no ponto de projeto ----------------
    CD_dt, CLmax_dt, drag = aerodynamics(airplane, Mach, h, CL,
                                         highlift_config='clean', lg_down=0)

    # ---------------- Inercias no ponto de projeto ------------------------
    moment_of_inertia(airplane, fuel_frac=config.FUEL_FRAC,
                      payload_frac=config.PAYLOAD_FRAC)
    moi = airplane['moment_of_inertia']

    # CG no ponto de projeto (mesma formula usada dentro de moment_of_inertia)
    from designTool.balance import tank_properties
    _, _, xcg_fuel, _ = tank_properties(
        geo['cr_w'], geo['ct_w'], inp['tcr_w'], inp['tct_w'], geo['b_w'],
        inp['sweep_w'], inp['xr_w'], inp['x_tank_c_w'], inp['c_tank_c_w'],
        inp['b_tank_b_w_start'], inp['b_tank_b_w_end'], inp['rho_fuel'], gravity)
    xcg_dp = ((tm['W_empty'] * airplane['empty_weight']['xcg_empty']
               + config.FUEL_FRAC * tm['W_fuel'] * xcg_fuel
               + config.PAYLOAD_FRAC * inp['W_payload'] * inp['xcg_payload']
               + inp['W_crew'] * inp['xcg_crew']) / W)

    xm_w, cm_w = geo['xm_w'], geo['cm_w']

    dp = {
        '_comment': 'Tabela 1 + dados de geometria/massa consumidos pelos '
                    'estagios seguintes. Pode ser editado a mao.',

        # ---- Tabela 1 -----------------------------------------------------
        'tabela1': {
            'W0': W0,                       # peso maximo de decolagem [N]
            'W': W,                         # peso no ponto de projeto [N]
            'h': h,                         # altitude [m]
            'rho': rho,                     # densidade [kg/m3]
            'a': a,                         # velocidade do som [m/s]
            'M': Mach,                      # Mach
            'V': V,                         # velocidade [m/s]
            'CL': CL,                       # CL do ponto de projeto
            'S_ref': S_w,                   # area de referencia [m2]
        },

        # ---- condicao / pesos ---------------------------------------------
        'gravity': gravity,
        'fuel_frac': config.FUEL_FRAC,
        'payload_frac': config.PAYLOAD_FRAC,
        'W_empty': tm['W_empty'],
        'W_fuel': tm['W_fuel'],
        'W_payload': inp['W_payload'],
        'W_crew': inp['W_crew'],
        'mass_design_point': W / gravity,
        'T0': tm['T0'],
        'Tmax': inp['engine'].get('Tmax'),

        # ---- referencias AVL ----------------------------------------------
        'S_ref': S_w,
        'c_ref': cm_w,
        'b_ref': geo['b_w'],
        'xm_w': xm_w,
        'CD0': drag['CD0'],
        'CD0_breakdown': {k: v for k, v in drag.items()
                          if k.startswith('CD0') or k in ('K', 'e', 'CDind',
                                                          'CDwave', 'CD',
                                                          'CLmax')},

        # ---- CG ------------------------------------------------------------
        'xcg_fwd': bal['xcg_fwd'],
        'xcg_aft': bal['xcg_aft'],
        'xcg_design_point': xcg_dp,
        'zcg': 0.0,             # designTool referencia inercias em z = 0
        'xnp_designtool': bal['xnp'],
        'SM_fwd_designtool': bal['SM_fwd'],
        'SM_aft_designtool': bal['SM_aft'],
        'xcg_fwd_pct_mac': (bal['xcg_fwd'] - xm_w) / cm_w * 100,
        'xcg_aft_pct_mac': (bal['xcg_aft'] - xm_w) / cm_w * 100,

        # ---- inercias ------------------------------------------------------
        'moment_of_inertia': dict(moi),

        # ---- geometria completa (para escrever o .avl) ---------------------
        'geometry': {k: float(v) for k, v in geo.items()},
        'inputs_geom': {
            'xr_w': inp['xr_w'], 'zr_w': inp['zr_w'],
            'zr_h': inp['zr_h'], 'zr_v': inp['zr_v'],
            'sweep_w': inp['sweep_w'], 'sweep_h': inp['sweep_h'],
            'sweep_v': inp['sweep_v'],
            'dihedral_w': inp['dihedral_w'], 'dihedral_h': inp['dihedral_h'],
            'taper_w': inp['taper_w'],
            'L_f': inp['L_f'], 'D_f': inp['D_f'],
            'x_n': inp['x_n'], 'y_n': inp['y_n'], 'z_n': inp['z_n'],
            'L_n': inp['L_n'], 'D_n': inp['D_n'],
            'n_engines': inp['n_engines'],
            'c_ail_c_wing': inp['c_ail_c_wing'],
            'b_ail_b_wing': inp['b_ail_b_wing'],
            'eta_h': inp['eta_h'],
        },
        # fracao de corda das superficies de controle das empenagens
        'c_elev_c_h': 0.30,
        'c_rud_c_v': 0.35,
    }

    util.save('01_airplane', airplane)
    util.save('01_design_point', dp)

    # ---------------- Resumo na tela --------------------------------------
    t1 = dp['tabela1']
    print('\nTabela 1 - Dados do ponto de projeto')
    print('  W0      [N]      = %12.1f  (%.0f kgf)' % (t1['W0'], t1['W0'] / gravity))
    print('  W       [N]      = %12.1f  (%.0f kgf)' % (t1['W'], t1['W'] / gravity))
    print('  h       [m]      = %12.1f  (%.0f ft)' % (t1['h'], t1['h'] / 0.3048))
    print('  rho     [kg/m3]  = %12.5f' % t1['rho'])
    print('  a       [m/s]    = %12.3f' % t1['a'])
    print('  M                = %12.4f' % t1['M'])
    print('  V       [m/s]    = %12.3f' % t1['V'])
    print('  CL               = %12.5f' % t1['CL'])
    print('  S_ref   [m2]     = %12.3f' % t1['S_ref'])
    print('\n  CD0 (designTool, limpo, ponto de projeto) = %.5f' % dp['CD0'])
    print('  c_ref = %.4f m   b_ref = %.4f m' % (dp['c_ref'], dp['b_ref']))
    print('  xcg_fwd = %.4f m (%.1f%% MAC)   xcg_aft = %.4f m (%.1f%% MAC)'
          % (dp['xcg_fwd'], dp['xcg_fwd_pct_mac'],
             dp['xcg_aft'], dp['xcg_aft_pct_mac']))
    print('  Inercias [kg.m2]: Ixx=%.4g Iyy=%.4g Izz=%.4g Ixz=%.4g'
          % (moi['Ixx'], moi['Iyy'], moi['Izz'], moi['Ixz']))

    return dp


if __name__ == '__main__':
    run()
