"""
Estagio 08 - Figuras do relatorio.

Le   : out/01..07
Grava: figs/*.png  e  figs/trefftz_*.ps (plano de Trefftz do proprio AVL)

Figuras geradas:
    fig03_trefftz_*.png   carregamento em envergadura no ponto de projeto
    fig04_stall_cl_y.png  metodo da secao critica (cl x y + limite cl_max)
    fig04_stall_ccl.png   carga seccional c*cl/c_ref na condicao de estol
    fig05_polar.png       CD x CL das 4 configuracoes + polar do designTool
    fig05b_CD_alpha.png   ajuste quadratico CD(alpha) da Tabela 7
    fig06_CL_alpha.png    CL x alpha das 4 configuracoes
    fig07_CL_deltae.png   CL x delta_e das 4 configuracoes
"""

import os
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from . import avlrun, config, util

COR = {'a_fwd_clean': 'tab:blue', 'b_aft_clean': 'tab:orange',
       'c_fwd_trim': 'tab:green', 'd_aft_trim': 'tab:red'}
ESTILO = {'a_fwd_clean': '-', 'b_aft_clean': '-',
          'c_fwd_trim': '--', 'd_aft_trim': '--'}


def _fig(nome):
    os.makedirs(config.FIG_DIR, exist_ok=True)
    path = os.path.join(config.FIG_DIR, nome)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    print('  -> figs/%s' % nome)


# ---------------------------------------------------------------------------
def trefftz_ps(dp, tail):
    """Gera o print do plano de Trefftz pelo proprio AVL (PostScript)."""
    os.makedirs(config.FIG_DIR, exist_ok=True)
    rundir = config.RUN_DIR
    for cg in ('fwd', 'aft'):
        cmds = '\n'.join([
            'plop', 'g', '',
            'load %s.avl' % cg,
            'oper', 'm', 'mn %.4f' % dp['tabela1']['M'], '',
            'a c %.6f' % dp['tabela1']['CL'],
            'd2 d2 0.0',
            'de', '1 %.6f' % tail[cg]['it'], '',
            'x', 't', 'h', '', '', 'quit', '']) + '\n'
        subprocess.run([os.path.abspath(config.AVL_EXE)], input=cmds,
                       cwd=rundir, text=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=300)
        src = os.path.join(rundir, 'plot.ps')
        if os.path.isfile(src):
            dst = os.path.join(config.FIG_DIR, 'trefftz_%s.ps' % cg)
            os.replace(src, dst)
            print('  -> figs/trefftz_%s.ps' % cg)


# ---------------------------------------------------------------------------
def fig_spanload(dp, tail):
    """Carregamento em envergadura no ponto de projeto (equivalente Trefftz)."""
    mach, CL = dp['tabela1']['M'], dp['tabela1']['CL']
    b2 = dp['b_ref'] / 2
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for cg, cor in (('fwd', 'tab:blue'), ('aft', 'tab:red')):
        r = avlrun.run_case(cg, mach, CL=CL, it=tail[cg]['it'], elevator=0.0,
                            want=('fs',), tag='s08_span_' + cg)
        w = r['fs']['Wing']
        eta = w['Yle'] / b2
        ax[0].plot(eta, w['c_cl'] / dp['c_ref'], color=cor,
                   label='CG %s ($i_t$ = %+.2f$^\\circ$)'
                         % ('dianteiro' if cg == 'fwd' else 'traseiro',
                            tail[cg]['it']))
        ax[1].plot(eta, w['cl_norm'], color=cor)
    # elipse de referencia
    eta = np.linspace(0, 1, 200)
    ccl_ell = np.sqrt(np.clip(1 - eta ** 2, 0, None))
    r0 = None
    for a in ax[:1]:
        lines = a.get_lines()
        r0 = max(l.get_ydata().max() for l in lines)
    ax[0].plot(eta, r0 * ccl_ell, 'k:', lw=1, label='eliptica (referencia)')
    ax[0].set_xlabel('$y/(b/2)$'); ax[0].set_ylabel('$c\\,c_\\ell / c_{ref}$')
    ax[0].set_title('Carga seccional no ponto de projeto')
    ax[0].grid(alpha=.3); ax[0].legend(fontsize=8)
    ax[1].set_xlabel('$y/(b/2)$'); ax[1].set_ylabel('$c_{\\ell,norm}$')
    ax[1].set_title('Coeficiente de sustentacao seccional')
    ax[1].grid(alpha=.3)
    _fig('fig03_spanload.png')


# ---------------------------------------------------------------------------
def fig_stall(crit):
    casos = crit['casos']
    ordem = ['fwd_notrim', 'fwd_trim', 'aft_notrim', 'aft_trim']
    cores = ['tab:blue', 'tab:cyan', 'tab:red', 'tab:orange']
    # as quatro distribuicoes praticamente coincidem: larguras/tracos
    # diferentes para que todas fiquem visiveis
    larg = [3.2, 2.4, 1.6, 1.0]
    tracos = ['-', '-', '-', '-']

    plt.figure(figsize=(8, 5))
    for key, cor, lw, ls in zip(ordem, cores, larg, tracos):
        c = casos[key]
        d = c['dist']
        plt.plot(d['eta'], d['cl_norm'], ls, color=cor, lw=lw,
                 label='%s ($\\alpha_{max}$=%.2f$^\\circ$, $C_{Lmax}$=%.3f)'
                       % (c['nome'], c['alpha_max'], c['CLmax']))
        plt.plot(c['eta_crit'], c['cl_norm_crit'], 'o', color=cor, ms=6)
    d = casos[ordem[0]]['dist']
    plt.plot(d['eta'], d['cl_max_local'], 'k--', lw=2,
             label='$c_{\\ell max}$ do perfil (Lab 03)')
    plt.xlabel('$y/(b/2)$'); plt.ylabel('$c_{\\ell,norm}$')
    plt.title('Metodo da secao critica  ($M$ = %.2f, asa limpa)' % crit['mach'])
    plt.grid(alpha=.3); plt.legend(fontsize=8, loc='lower left')
    plt.ylim(0, max(crit['clmax_root'], crit['clmax_tip']) * 1.15)
    _fig('fig04_stall_cl_y.png')

    plt.figure(figsize=(8, 5))
    for key, cor, lw in zip(ordem, cores, larg):
        c = casos[key]; d = c['dist']
        ccl = np.array(d['cl_norm']) * np.array(d['chord'])
        plt.plot(d['eta'], ccl, color=cor, lw=lw, label=c['nome'])
    plt.xlabel('$y/(b/2)$'); plt.ylabel('$c\\,c_\\ell$  [m]')
    plt.title('Carga seccional na condicao de estol')
    plt.grid(alpha=.3); plt.legend(fontsize=8)
    _fig('fig04_stall_ccl.png')


# ---------------------------------------------------------------------------
def _designtool_polar(dp, CL_grid):
    dT = util.import_designtool()
    from designTool.aerodynamics import aerodynamics
    airplane = util.load('01_airplane')
    out = []
    for CL in CL_grid:
        CD, _, _ = aerodynamics(airplane, dp['tabela1']['M'],
                                dp['tabela1']['h'], CL,
                                highlift_config='clean', lg_down=0)
        out.append(CD)
    return np.array(out)


def fig_polar(dp, pol):
    CL_dp = dp['tabela1']['CL']
    plt.figure(figsize=(7.5, 5.5))
    for key, caso in pol['casos'].items():
        CL = [p['CL'] for p in caso['pontos']]
        CD = [p['CD'] for p in caso['pontos']]
        plt.plot(CD, CL, ESTILO[key], color=COR[key], label=caso['nome'])
        d = caso['no_ponto_de_projeto']
        plt.plot(d['CD'], d['CL'], 'o', color=COR[key], ms=6)

    CLg = np.linspace(config.CL_MIN_PLOT,
                      max(c['CLmax'] for c in pol['casos'].values()), 40)
    CDg = _designtool_polar(dp, CLg)
    plt.plot(CDg, CLg, 'k:', lw=2, label='polar do designTool')
    plt.plot(dp['CD0_breakdown']['CD'], CL_dp, 'ks', ms=7,
             label='ponto de projeto (designTool)')

    plt.xlabel('$C_D$'); plt.ylabel('$C_L$')
    plt.title('Polar de arrasto  ($M$ = %.2f, $h$ = %.0f ft)'
              % (dp['tabela1']['M'], dp['tabela1']['h'] / 0.3048))
    plt.grid(alpha=.3); plt.legend(fontsize=8, loc='lower right')
    _fig('fig05_polar.png')


def fig_cd_alpha(pol):
    pts = pol['casos']['b_aft_clean']['pontos']
    al = np.array([p['alpha'] for p in pts])
    cd = np.array([p['CD'] for p in pts])
    f = pol['ajuste_CD_alpha']
    ar = np.radians(np.linspace(al.min(), al.max(), 200))
    plt.figure(figsize=(7, 4.6))
    plt.plot(al, cd, 'o', ms=4, label='AVL (CG traseiro, sem deflexoes)')
    plt.plot(np.degrees(ar),
             f['CD0'] + f['CDa'] * ar + f['CDa2'] * ar ** 2, '-',
             label='$C_D = %.5f %+.5f\\,\\alpha %+.5f\\,\\alpha^2$'
                   % (f['CD0'], f['CDa'], f['CDa2']))
    plt.xlabel(r'$\alpha$ [graus]'); plt.ylabel('$C_D$')
    plt.title('Ajuste quadratico da polar nao trimada (Tabela 7)')
    plt.grid(alpha=.3); plt.legend(fontsize=8)
    _fig('fig05b_CD_alpha.png')


def fig_cl_alpha(dp, pol):
    CL_dp = dp['tabela1']['CL']
    plt.figure(figsize=(7.5, 5.5))
    for key, caso in pol['casos'].items():
        al = [p['alpha'] for p in caso['pontos']]
        CL = [p['CL'] for p in caso['pontos']]
        plt.plot(al, CL, ESTILO[key], color=COR[key], label=caso['nome'])
        d = caso['no_ponto_de_projeto']
        plt.plot(d['alpha'], CL_dp, 'o', color=COR[key], ms=6)
    plt.axhline(CL_dp, color='k', lw=.6, ls=':')
    plt.xlabel(r'$\alpha$ [graus]'); plt.ylabel('$C_L$')
    plt.title('Curva de sustentacao  ($M$ = %.2f)' % dp['tabela1']['M'])
    plt.grid(alpha=.3); plt.legend(fontsize=8, loc='lower right')
    _fig('fig06_CL_alpha.png')


def fig_cl_deltae(dp, pol):
    CL_dp = dp['tabela1']['CL']
    plt.figure(figsize=(7.5, 5.5))
    for key, caso in pol['casos'].items():
        de = [p['delta_e'] for p in caso['pontos']]
        CL = [p['CL'] for p in caso['pontos']]
        plt.plot(de, CL, ESTILO[key], color=COR[key], label=caso['nome'])
        d = caso['no_ponto_de_projeto']
        plt.plot(d['delta_e'], CL_dp, 'o', color=COR[key], ms=6)
    plt.axhline(CL_dp, color='k', lw=.6, ls=':')
    for lim in (-25, 25):
        plt.axvline(lim, color='0.5', lw=1, ls='-.')
    plt.xlabel(r'$\delta_e$ [graus]'); plt.ylabel('$C_L$')
    plt.title('Deflexao de profundor  ($M$ = %.2f)  - linhas cinza: $\\pm 25^\\circ$'
              % dp['tabela1']['M'])
    plt.grid(alpha=.3); plt.legend(fontsize=8, loc='lower left')
    _fig('fig07_CL_deltae.png')


# ---------------------------------------------------------------------------
def run():
    util.banner('Estagio 08 - Figuras')
    dp = util.load('01_design_point')
    tail = util.load('03_tail_incidence')
    crit = util.load('04_critical_section')
    pol = util.load('05_polars')

    trefftz_ps(dp, tail)
    fig_spanload(dp, tail)
    fig_stall(crit)
    fig_polar(dp, pol)
    fig_cd_alpha(pol)
    fig_cl_alpha(dp, pol)
    fig_cl_deltae(dp, pol)


if __name__ == '__main__':
    run()
