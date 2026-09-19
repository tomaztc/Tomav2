"""
Estagio 02 - Geracao dos arquivos de entrada do AVL (questao 1).

Le  : out/01_design_point.json
Grava: avl/fwd.avl, avl/aft.avl, avl/tomav_wing.dat, avl/fuse_nondim.dat
       out/02_avl_model.json  (resumo das secoes e indices de controle)

Os dois arquivos sao identicos a menos do Xref (posicao do CG).
Unidades: SI (m), consistentes com o designTool.

Convencoes de controle (ordem de aparicao -> indice no menu OPER):
    d1 = aileron   (antissimetrico)
    d2 = elevator
    d3 = rudder
Variavel de projeto (menu DE):
    g1 = it  (incidencia da empenagem horizontal)
"""

import os
import shutil

import numpy as np

from . import config, util


# ---------------------------------------------------------------------------
def _interp_section(frac, xr, zr, cr, xt, yt, zt, ct):
    """Interpola LE e corda de um painel trapezoidal em y = frac*yt."""
    x = xr + frac * (xt - xr)
    y = frac * yt
    z = zr + frac * (zt - zr)
    c = cr + frac * (ct - cr)
    return x, y, z, c


def _sec(fid, x, y, z, c, ainc, afile=None, naca=None, controls=(), design=()):
    fid.write('SECTION\n')
    fid.write('#Xle      Yle      Zle      Chord    Ainc\n')
    fid.write('%9.4f %8.4f %8.4f %8.4f %8.4f\n' % (x, y, z, c, ainc))
    if afile:
        fid.write('AFILE\n%s\n' % afile)
    elif naca:
        fid.write('NACA\n%s\n' % naca)
    for name, gain, xhinge, hvec, sgndup in controls:
        fid.write('CONTROL\n%-9s %5.2f %6.3f  %s  %+d\n'
                  % (name, gain, xhinge, hvec, sgndup))
    for name, gain in design:
        fid.write('DESIGN\n%s %.1f\n' % (name, gain))
    fid.write('\n')


# ---------------------------------------------------------------------------
def write_avl(path, dp, xref, title):
    g = dp['geometry']
    ig = dp['inputs_geom']

    S_ref, c_ref, b_ref = dp['S_ref'], dp['c_ref'], dp['b_ref']
    CD0 = dp['CD0']

    # ---- asa: estacoes em fracao de semi-envergadura ----------------------
    ail_end = config.AIL_END_FRAC
    ail_ini = ail_end - ig['b_ail_b_wing']
    xh_ail = 1.0 - ig['c_ail_c_wing']
    stations = sorted({0.0, ail_ini, ail_end, 1.0})

    twist_root = config.WING_ROOT_INCIDENCE_DEG
    twist_tip = twist_root + config.WING_TWIST_TIP_DEG

    with open(path, 'w') as fid:
        fid.write('%s\n\n' % title)
        fid.write('#Mach\n0.0\n\n')
        fid.write('#IYsym  IZsym  Zsym\n 0      0      0.0\n\n')
        fid.write('#Sref     Cref      Bref\n%9.4f %9.4f %9.4f\n\n'
                  % (S_ref, c_ref, b_ref))
        fid.write('#Xref     Yref      Zref\n%9.4f %9.4f %9.4f\n\n'
                  % (xref, 0.0, dp['zcg']))
        fid.write('# CDp (CD0 limpo do designTool no ponto de projeto)\n')
        fid.write('%9.5f\n\n' % CD0)

        # ------------------------------------------------------------------
        # ASA
        # ------------------------------------------------------------------
        fid.write('#' + '-' * 70 + '\nSURFACE\nWing\n')
        fid.write('#Nchordwise  Cspace  Nspanwise  Sspace\n')
        fid.write('%d           1.0     %d         -2.0\n\n'
                  % (config.NCHORD_W, config.NSPAN_W))
        fid.write('COMPONENT\n1\n\nYDUPLICATE\n0.0\n\n')

        for frac in stations:
            x, y, z, c = _interp_section(
                frac, ig['xr_w'], ig['zr_w'], g['cr_w'],
                g['xt_w'], g['yt_w'], g['zt_w'], g['ct_w'])
            ainc = twist_root + frac * (twist_tip - twist_root)
            ctrl = []
            if ail_ini - 1e-9 <= frac <= ail_end + 1e-9:
                ctrl.append(('aileron', -1.0, xh_ail, '0. 0. 0.', -1))
            _sec(fid, x, y, z, c, ainc,
                 afile='tomav_wing.dat', controls=ctrl)

        # ------------------------------------------------------------------
        # EMPENAGEM HORIZONTAL
        # ------------------------------------------------------------------
        xh_elev = 1.0 - dp['c_elev_c_h']
        fid.write('#' + '-' * 70 + '\nSURFACE\nStab\n')
        fid.write('#Nchordwise  Cspace  Nspanwise  Sspace\n')
        fid.write('%d           1.0     %d         -2.0\n\n'
                  % (config.NCHORD_H, config.NSPAN_H))
        fid.write('COMPONENT\n2\n\nYDUPLICATE\n0.0\n\n')
        for frac in (0.0, 1.0):
            x, y, z, c = _interp_section(
                frac, g['xr_h'], ig['zr_h'], g['cr_h'],
                g['xt_h'], g['yt_h'], g['zt_h'], g['ct_h'])
            _sec(fid, x, y, z, c, 0.0, naca=config.HT_NACA,
                 controls=[('elevator', 1.0, xh_elev, '0. 0. 0.', +1)],
                 design=[('it', 1.0)])

        # ------------------------------------------------------------------
        # EMPENAGEM VERTICAL
        # ------------------------------------------------------------------
        xh_rud = 1.0 - dp['c_rud_c_v']
        fid.write('#' + '-' * 70 + '\nSURFACE\nFin\n')
        fid.write('#Nchordwise  Cspace  Nspanwise  Sspace\n')
        fid.write('%d           1.0     %d          1.0\n\n'
                  % (config.NCHORD_V, config.NSPAN_V))
        fid.write('COMPONENT\n3\n\n')
        for frac in (0.0, 1.0):
            x = g['xr_v'] + frac * (g['xt_v'] - g['xr_v'])
            z = ig['zr_v'] + frac * (g['zt_v'] - ig['zr_v'])
            c = g['cr_v'] + frac * (g['ct_v'] - g['cr_v'])
            _sec(fid, x, 0.0, z, c, 0.0, naca=config.VT_NACA,
                 controls=[('rudder', 1.0, xh_rud, '0. 0. 0.', +1)])

        # ------------------------------------------------------------------
        # FUSELAGEM
        # ------------------------------------------------------------------
        if config.INCLUDE_BODY:
            # o contorno nao-dimensional tem eixo em z = 0.11376*D_f
            z_shift = -0.11376 * ig['D_f']
            fid.write('#' + '-' * 70 + '\nBODY\nFuselage\n')
            fid.write('# Nbody  Bspace\n30      1.0\n\n')
            fid.write('SCALE\n# comprimento, diametro, diametro\n')
            fid.write('%9.4f %9.4f %9.4f\n\n' % (ig['L_f'], ig['D_f'], ig['D_f']))
            fid.write('TRANSLATE\n0.0  0.0  %9.4f\n\n' % z_shift)
            fid.write('BFILE\nfuse_nondim.dat\n\n')

        # ------------------------------------------------------------------
        # NACELLES
        # ------------------------------------------------------------------
        if config.INCLUDE_NACELLES and ig['n_engines'] >= 2:
            r = ig['D_n'] / 2
            fid.write('#' + '-' * 70 + '\nSURFACE\nNacelle\n')
            fid.write('#Nchordwise  Cspace  Nspanwise  Sspace\n')
            fid.write('6            1.0     12         0.0\n\n')
            fid.write('COMPONENT\n4\n\nYDUPLICATE\n0.0\n\n')
            fid.write('SCALE\n# comprimento, raio horizontal, raio vertical\n')
            fid.write('%9.4f %9.4f %9.4f\n\n' % (ig['L_n'], r, r))
            fid.write('TRANSLATE\n%9.4f %9.4f %9.4f\n\n'
                      % (ig['x_n'], ig['y_n'], ig['z_n']))
            for ang in np.linspace(90.0, 90.0 + 360.0, 13):
                yy = np.cos(np.radians(ang))
                zz = np.sin(np.radians(ang))
                fid.write('SECTION\n#Xle   Yle    Zle     Chord  Ainc  '
                          'Nspan  Sspace\n')
                fid.write('0.00 %7.4f %7.4f  1.0    0.0   1      0.\n\n'
                          % (yy, zz))

    return {'stations_wing': stations,
            'ail_ini_frac': ail_ini, 'ail_end_frac': ail_end,
            'xref': xref}


# ---------------------------------------------------------------------------
def run():
    util.banner('Estagio 02 - Geometria AVL (fwd.avl / aft.avl)')
    dp = util.load('01_design_point')

    os.makedirs(config.AVL_DIR, exist_ok=True)
    shutil.copy(config.AIRFOIL_DAT, os.path.join(config.AVL_DIR, 'tomav_wing.dat'))
    shutil.copy(config.FUSE_DAT, os.path.join(config.AVL_DIR, 'fuse_nondim.dat'))

    info_fwd = write_avl(os.path.join(config.AVL_DIR, 'fwd.avl'), dp,
                         dp['xcg_fwd'], 'Tomav2 - CG dianteiro')
    info_aft = write_avl(os.path.join(config.AVL_DIR, 'aft.avl'), dp,
                         dp['xcg_aft'], 'Tomav2 - CG traseiro')

    model = {
        '_comment': 'Resumo do modelo AVL escrito no estagio 02.',
        'controls': {'aileron': 1, 'elevator': 2, 'rudder': 3},
        'design_vars': {'it': 1},
        'S_ref': dp['S_ref'], 'c_ref': dp['c_ref'], 'b_ref': dp['b_ref'],
        'CDp': dp['CD0'],
        'xref_fwd': dp['xcg_fwd'], 'xref_aft': dp['xcg_aft'],
        'wing_twist_tip_deg': config.WING_TWIST_TIP_DEG,
        'wing_root_incidence_deg': config.WING_ROOT_INCIDENCE_DEG,
        'aileron_span_frac': [info_fwd['ail_ini_frac'], info_fwd['ail_end_frac']],
        'c_elev_c_h': dp['c_elev_c_h'], 'c_rud_c_v': dp['c_rud_c_v'],
        'include_body': config.INCLUDE_BODY,
        'include_nacelles': config.INCLUDE_NACELLES,
        'files': {'fwd': 'avl/fwd.avl', 'aft': 'avl/aft.avl'},
    }
    util.save('02_avl_model', model)

    print('\n  Xref dianteiro = %.4f m   Xref traseiro = %.4f m'
          % (dp['xcg_fwd'], dp['xcg_aft']))
    print('  CDp inserido nos arquivos = %.5f' % dp['CD0'])
    print('  Secoes da asa em y/(b/2) =', ['%.3f' % s for s in info_fwd['stations_wing']])
    print('  Aileron de %.2f a %.2f de b/2, c_ail/c = %.2f'
          % (info_fwd['ail_ini_frac'], info_fwd['ail_end_frac'],
             dp['inputs_geom']['c_ail_c_wing']))
    return model


if __name__ == '__main__':
    run()
