"""
Estagio 09 - Monta o relatorio (RESULTADOS.md) a partir de out/*.json.

Nao roda o AVL: so le os resultados intermediarios. Se voce editar qualquer
arquivo em out/, rode apenas este estagio para regerar o texto e as tabelas.
"""

import os

import numpy as np

from . import config, util

def _t(rows, header):
    w = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    out = ['| ' + ' | '.join(str(header[i]).ljust(w[i])
                             for i in range(len(header))) + ' |']
    out.append('|' + '|'.join('-' * (w[i] + 2) for i in range(len(header))) + '|')
    for r in rows:
        out.append('| ' + ' | '.join(str(r[i]).ljust(w[i])
                                     for i in range(len(header))) + ' |')
    return '\n'.join(out)


def _f(x, n=4):
    if x is None:
        return '-'
    if abs(x) >= 1e4:
        return '%.0f' % x
    return '%.*f' % (n, x)


def run():
    util.banner('Estagio 09 - Relatorio (RESULTADOS.md)')
    dp = util.load('01_design_point')
    mdl = util.load('02_avl_model')
    tail = util.load('03_tail_incidence')
    crit = util.load('04_critical_section')
    pol = util.load('05_polars')
    npt = util.load('06_neutral_point')
    t6 = util.load('07_tabela6')
    t7 = util.load('07_tabela7')
    t9 = util.load('07_tabela9')

    t1 = dp['tabela1']
    G = dp.get('gravity', 9.81)
    L = []
    A = L.append

    A('# PRJ-23 Lab 04 - Analise aerodinamica da Tomav2 (AVL)\n')
    A('Resultados gerados automaticamente pelo pipeline em `Lab4/lab4/`. ')
    A('Todos os numeros abaixo vem dos arquivos em `Lab4/out/`; editando-os e ')
    A('rodando de novo o estagio correspondente, este relatorio se atualiza.\n')

    # ---------------------------------------------------------------- Q1 ---
    A('\n## 1. Arquivos de entrada do AVL\n')
    A('Dois arquivos com a mesma geometria e apenas o `Xref` diferente:\n')
    A('- `avl/fwd.avl` - CG dianteiro, `Xref` = %.4f m' % mdl['xref_fwd'])
    A('- `avl/aft.avl` - CG traseiro, `Xref` = %.4f m' % mdl['xref_aft'])
    A('- `avl/tomav_wing.dat` - perfil otimizado no Lab 03 (AFILE de todas as '
      'secoes da asa)')
    A('- `avl/fuse_nondim.dat` - contorno da fuselagem (BFILE)\n')
    A('`CDp` inserido nos dois arquivos = **%.5f** (CD0 limpo calculado pelo '
      '`designTool` no ponto de projeto).\n' % mdl['CDp'])
    A('Superficies de controle e variavel de projeto:\n')
    A(_t([['d1', 'aileron', '%.2f a %.2f de b/2, c_a/c = %.2f'
           % (mdl['aileron_span_frac'][0], mdl['aileron_span_frac'][1],
              dp['inputs_geom']['c_ail_c_wing'])],
          ['d2', 'elevator', 'toda a EH, c_e/c = %.2f' % mdl['c_elev_c_h']],
          ['d3', 'rudder', 'toda a EV, c_r/c = %.2f' % mdl['c_rud_c_v']],
          ['g1', 'it', 'incidencia da EH (menu DE)']],
         ['indice', 'nome', 'definicao']))
    A('\nHipoteses adicionais (nao definidas pelo `designTool`, em '
      '`lab4/config.py`):\n')
    A('- torcao geometrica linear da asa: %.1f deg na raiz, %.1f deg na ponta'
      % (mdl['wing_root_incidence_deg'],
         mdl['wing_root_incidence_deg'] + mdl['wing_twist_tip_deg']))
    A('- empenagens com perfis simetricos NACA %s (AVL usa so a linha de '
      'camber)' % config.HT_NACA)
    A('- fuselagem modelada como BODY: **%s**; nacelles como superficies '
      'anelares: **%s**' % (mdl['include_body'], mdl['include_nacelles']))

    # ---------------------------------------------------------------- Q2 ---
    A('\n\n## 2. Ponto de projeto (Tabela 1)\n')
    A('Condicao: cruzeiro, %d%% de combustivel e %d%% de carga paga.\n'
      % (dp['fuel_frac'] * 100, dp['payload_frac'] * 100))
    A(_t([
        ['W0', 'peso maximo de decolagem [N]', _f(t1['W0'], 1),
         '%.0f kgf' % (t1['W0'] / G)],
        ['W', 'peso no ponto de projeto [N]', _f(t1['W'], 1),
         '%.0f kgf' % (t1['W'] / G)],
        ['h', 'altitude [m]', _f(t1['h'], 1), '%.0f ft' % (t1['h'] / 0.3048)],
        ['rho', 'densidade [kg/m3]', _f(t1['rho'], 5), ''],
        ['a', 'velocidade do som [m/s]', _f(t1['a'], 3), ''],
        ['M', 'Mach', _f(t1['M'], 3), ''],
        ['V', 'velocidade [m/s]', _f(t1['V'], 3),
         '%.0f kt' % (t1['V'] / 0.514444)],
        ['CL', 'CL no ponto de projeto', _f(t1['CL'], 5), ''],
        ['S_ref', 'area de referencia [m2]', _f(t1['S_ref'], 2), ''],
    ], ['parametro', 'explicacao', 'valor', 'obs.']))
    A('\nComposicao do peso: W = W_vazio (%.0f kgf) + W_tripulacao (%.0f kgf) '
      '+ %.0f%% W_carga (%.0f kgf) + %.0f%% W_comb (%.0f kgf).\n'
      % (dp['W_empty'] / G, dp['W_crew'] / G, dp['payload_frac'] * 100,
         dp['W_payload'] / G, dp['fuel_frac'] * 100, dp['W_fuel'] / G))

    # ---------------------------------------------------------------- Q3 ---
    A('\n## 3. Incidencia da empenagem horizontal\n')
    A('i_t escolhido de forma que a deflexao de profundor necessaria para '
      'trimar (Cm = 0) no ponto de projeto seja nula.\n')
    A(_t([[('dianteiro' if cg == 'fwd' else 'traseiro'),
            _f(tail[cg]['it'], 4), _f(tail[cg]['delta_e_residual'], 4),
            _f(tail[cg]['alpha'], 3), _f(tail[cg]['CLtot'], 5),
            _f(tail[cg]['Cmtot'], 6)] for cg in ('fwd', 'aft')],
         ['CG', 'i_t [deg]', 'delta_e residual [deg]', 'alpha [deg]',
          'CL', 'Cm']))
    A('\nPlano de Trefftz do AVL: `figs/trefftz_fwd.ps` e `figs/trefftz_aft.ps`.')
    A('Equivalente em matplotlib (carga em envergadura): `figs/fig03_spanload.png`.')
    A('\nO CG dianteiro exige i_t mais negativo (%.2f deg contra %.2f deg) '
      'porque o braco de trimagem e maior e a EH precisa de mais carga para '
      'baixo.' % (tail['fwd']['it'], tail['aft']['it']))

    # ---------------------------------------------------------------- Q4 ---
    A('\n\n## 4. Metodo da secao critica - CLmax de asa limpa\n')
    A('M = %.2f, asa limpa, cl_max do perfil = **%.4f** (%s).\n'
      % (crit['mach'], crit['clmax_root'], crit['clmax_source']))
    rows = []
    for k in ('fwd_notrim', 'fwd_trim', 'aft_notrim', 'aft_trim'):
        c = crit['casos'][k]
        rows.append([c['nome'], _f(c['it'], 3), _f(c['alpha_max'], 2),
                     _f(c['CLmax'], 4), _f(c['delta_e'], 3),
                     _f(c['eta_crit'], 3)])
    A(_t(rows, ['caso', 'i_t [deg]', 'alpha_max [deg]', 'CLmax',
                'delta_e [deg]', 'y/(b/2) do estol']))
    A('\nFiguras: `figs/fig04_stall_cl_y.png` (cl x y com o limite de '
      'cl_max) e `figs/fig04_stall_ccl.png` (carga seccional).\n')
    A('\n**Discussao das caracteristicas de estol.** '
      'O estol comeca em y/(b/2) = %.2f, ou seja, na regiao externa da asa e '
      'ja dentro do trecho ocupado pelo aileron (de %.2f a %.2f de b/2). '
      % (crit['casos']['aft_trim']['eta_crit'],
         mdl['aileron_span_frac'][0], mdl['aileron_span_frac'][1]))
    A('Isso e o comportamento tipico de asa enflechada (%.1f deg) e muito '
      'afilada (taper = %.2f): a combinacao de enflechamento e afilamento '
      'concentra a sustentacao seccional na ponta. '
      % (np.degrees(dp['inputs_geom']['sweep_w']),
         dp['inputs_geom']['taper_w']))
    A('A torcao de %.1f deg adotada ja alivia parte do problema, mas nao o '
      'suficiente para levar o inicio do estol para a raiz. '
      % abs(mdl['wing_twist_tip_deg']))
    A('Como consequencia, ha risco de perda de eficiencia do aileron e de '
      'tendencia a rolamento assimetrico no estol, alem de momento de arfagem '
      'de cabrar ("pitch-up") por perda de sustentacao atras do CG. ')
    A('Recomendacoes: aumentar o washout, adotar torcao aerodinamica '
      '(perfil de ponta com cl_max maior), deslocar o aileron para dentro ou '
      'incluir dispositivos de controle de estol (stall strips / vortilons). ')
    A('O CLmax limpo obtido (~%.2f) tambem e baixo: o dimensionamento de pista '
      'depende dos dispositivos hipersustentadores (flap %s + %s), que nao '
      'entram neste modelo.'
      % (max(crit['casos'][k]['CLmax'] for k in crit['casos']),
         'double slotted', 'slat'))

    # ---------------------------------------------------------------- Q5 ---
    A('\n\n## 5. Polares\n')
    A('Todas no Mach do ponto de projeto (M = %.2f). Arrasto = %s.\n'
      % (pol['mach'], pol['drag_model']))
    comp = pol['comparacao_designTool']
    rows = []
    for k, caso in pol['casos'].items():
        d = caso['no_ponto_de_projeto']
        rows.append([caso['nome'], _f(d['CD'], 5), _f(d['alpha'], 3),
                     _f(d['delta_e'], 3),
                     '%+.1f%%' % ((d['CD'] / comp['CD_designTool'] - 1) * 100)])
    rows.append(['designTool (CD0 + CDind + CDwave)',
                 _f(comp['CD_designTool'], 5), '-', '-', '0.0%'])
    A(_t(rows, ['configuracao', 'CD no CL de projeto', 'alpha [deg]',
                'delta_e [deg]', 'dif. vs designTool']))
    A('\nCL do ponto de projeto = %.5f. Figura: `figs/fig05_polar.png`.\n'
      % pol['CL_design'])
    cd_b = pol['casos']['b_aft_clean']['no_ponto_de_projeto']['CD']
    dif_b = (cd_b / comp['CD_designTool'] - 1) * 100
    pts_b = pol['casos']['b_aft_clean']['pontos']
    e_dp = min(pts_b, key=lambda p: abs(p['CL'] - pol['CL_design'])).get('e')
    A('\nNo caso b (CG traseiro, sem deflexoes) o AVL fica %+.1f%% em relacao '
      'ao `designTool`. A diferenca esta no arrasto induzido: o `designTool` '
      'usa CDind = K*CL^2 com fator de Oswald vindo de regressao, enquanto o '
      'AVL integra a distribuicao real de circulacao (e = %.3f no ponto de '
      'projeto). Alem disso o AVL nao modela arrasto de onda, que no '
      '`designTool` vale CDwave = %.5f nesse ponto, e o CDp do AVL e um valor '
      'unico fixado no CD0 de cruzeiro (nao varia com CL nem com Reynolds).\n'
      % (dif_b, e_dp if e_dp else float('nan'),
         comp['CDwave_designTool'] or 0.0))
    A('\nAs polares terminam no CLmax de cada caso obtido no item 4 e comecam '
      'em CL = %.1f.' % config.CL_MIN_PLOT)

    # ---------------------------------------------------------------- Q6 ---
    A('\n\n## 6. Curvas de sustentacao (CL x alpha)\n')
    A('Figura: `figs/fig06_CL_alpha.png`. Pontos de projeto marcados com '
      'circulo.\n')
    rows = [[c['nome'], _f(c['no_ponto_de_projeto']['alpha'], 3),
             _f(c['CLmax'], 4)] for c in pol['casos'].values()]
    A(_t(rows, ['configuracao', 'alpha no ponto de projeto [deg]', 'CLmax']))

    # ---------------------------------------------------------------- Q7 ---
    A('\n\n## 7. Deflexao de profundor (CL x delta_e)\n')
    A('Figura: `figs/fig07_CL_deltae.png`.\n')
    rows = []
    for k, caso in pol['casos'].items():
        des = [p['delta_e'] for p in caso['pontos']]
        rows.append([caso['nome'],
                     _f(caso['no_ponto_de_projeto']['delta_e'], 3),
                     _f(min(des), 3), _f(max(des), 3)])
    A(_t(rows, ['configuracao', 'delta_e no ponto de projeto [deg]',
                'delta_e min [deg]', 'delta_e max [deg]']))
    de_max = max(abs(v) for c in pol['casos'].values()
                 for v in [p['delta_e'] for p in c['pontos']])
    A('\n**Discussao.** Com i_t ajustado por CG, a deflexao de profundor no '
      'ponto de projeto e nula (por construcao) e o maior valor exigido em '
      'toda a faixa CL = %.1f ate CLmax e |delta_e| = %.1f deg. '
      % (config.CL_MIN_PLOT, de_max))
    A('Isso esta bem dentro do curso tipico de profundor de aeronaves de '
      'transporte (+-25 deg), ou seja, **as deflexoes estao em niveis '
      'adequados** e ainda sobra autoridade para manobra, rajada e para as '
      'condicoes criticas que nao foram simuladas aqui (flape estendido, '
      'rotacao de decolagem e trimagem com CG nos extremos em baixa '
      'velocidade).')

    # ---------------------------------------------------------------- Q8 ---
    A('\n\n## 8. Ponto neutro e margem estatica\n')
    A(_t([
        ['x_np (AVL)', _f(npt['xnp_avl'], 4), _f(npt['xnp_pct_mac'], 1)],
        ['x_np (designTool)', _f(npt['xnp_designtool'], 4),
         _f(npt['xnp_designtool_pct_mac'], 1)],
        ['x_cg dianteiro', _f(npt['xcg_fwd'], 4), _f(npt['xcg_fwd_pct_mac'], 1)],
        ['x_cg traseiro', _f(npt['xcg_aft'], 4), _f(npt['xcg_aft_pct_mac'], 1)],
    ], ['posicao', '[m do nariz]', '[% MAC]']))
    A('')
    A(_t([
        ['dianteiro', '%.1f%%' % (npt['SM_fwd'] * 100),
         '%.1f%%' % (npt['SM_fwd_designtool'] * 100)],
        ['traseiro', '%.1f%%' % (npt['SM_aft'] * 100),
         '%.1f%%' % (npt['SM_aft_designtool'] * 100)],
    ], ['CG', 'margem estatica (AVL)', 'margem estatica (designTool)']))
    A('\nA aeronave e estaticamente estavel em arfagem nas duas posicoes de CG '
      '(Cma = %.3f 1/rad no CG traseiro). A margem no CG traseiro (%.1f%%) '
      'ainda e alta para um transporte moderno (tipico 5-15%%), o que indica '
      'que ha espaco para reduzir a EH ou recuar o envelope de CG e ganhar '
      'arrasto de trimagem.'
      % (npt['aft_Cma'], npt['SM_aft'] * 100))

    # ------------------------------------------------------------ Secao 3 ---
    A('\n\n## 9. Derivadas de estabilidade e controle (CG traseiro)\n')
    cond = t9['condicao']
    A('Condicao: CG traseiro (x = %.4f m), M = %.2f, CL = %.5f '
      '(alpha = %.3f deg), i_t = %.3f deg, delta_e = 0, **sem restricao de '
      'trimagem**.\n'
      % (cond['xcg'], cond['Mach'], cond['CL'], cond['alpha_deg'],
         cond['it_deg']))
    A('### Tabela 6 - alpha = 0, i_t = 0, todas as deflexoes nulas\n')
    A(_t([['CL0', 'CL para alpha = 0', _f(t6['CL0'], 6)],
          ['CM0', 'CM para alpha = 0', _f(t6['CM0'], 6)]],
         ['parametro', 'explicacao', 'valor']))
    A('\n### Tabela 7 - ajuste quadratico da polar nao trimada\n')
    A('CD = CD0 + CDa*alpha + CDa2*alpha^2, com alpha em rad, ajustado sobre a '
      'polar do item 5.b (CG traseiro, sem deflexoes). RMS do ajuste = %.2e.\n'
      % t7['rms'])
    A(_t([['CD0', 'termo constante', _f(t7['CD0'], 6)],
          ['CDa', 'termo linear [1/rad]', _f(t7['CDa'], 6)],
          ['CDa2', 'termo quadratico [1/rad2]', _f(t7['CDa2'], 6)]],
         ['parametro', 'explicacao', 'valor']))
    A('\nFigura: `figs/fig05b_CD_alpha.png`.')

    A('\n### Tabela 9 - informacoes para analise de estabilidade e controle\n')
    v = t9['valores']
    desc = [
        ('S_ref', 'area de referencia [m2]', ''),
        ('c_ref', 'corda de referencia [m]', ''),
        ('b_ref', 'envergadura de referencia [m]', ''),
        ('m', 'massa da aeronave [kg]', 'ponto de projeto'),
        ('Ixx', 'momento de inercia [kg.m2]', 'designTool'),
        ('Iyy', 'momento de inercia [kg.m2]', 'designTool'),
        ('Izz', 'momento de inercia [kg.m2]', 'designTool'),
        ('Ixz', 'momento de inercia [kg.m2]', 'designTool'),
        ('ip', 'incidencia do motor [deg]', 'config.py'),
        ('xp', 'posicao long. do motor rel. ao CG [m]', 'x positivo p/ tras'),
        ('zp', 'posicao vert. do motor rel. ao CG [m]', 'z positivo p/ baixo'),
        ('Tmax', 'tracao maxima [N]', 'designTool'),
        ('V', 'velocidade de voo [m/s]', 'ponto de projeto'),
        ('h', 'altitude de voo [m]', 'ponto de projeto'),
        ('CL0', 'CL para alpha = 0', 'AVL ft (Tab. 6)'),
        ('CLa', 'dCL/dalpha [1/rad]', 'AVL st'),
        ('CLq', 'dCL/dq [1/rad]', 'AVL st'),
        ('CLit', 'dCL/dit [1/rad]', 'AVL st x 180/pi'),
        ('CLde', 'dCL/ddelta_e [1/rad]', 'AVL st x 180/pi'),
        ('CD0', 'CD para alpha = 0', 'Tab. 7'),
        ('CDa', 'termo linear da polar [1/rad]', 'Tab. 7'),
        ('CDa2', 'termo quadratico da polar [1/rad2]', 'Tab. 7'),
        ('CDq', 'dCD/dq [1/rad]', 'diferenca finita'),
        ('CDit', 'dCD/dit [1/rad]', 'AVL st x 180/pi'),
        ('CDde', 'dCD/ddelta_e [1/rad]', 'AVL st x 180/pi'),
        ('CM0', 'CM para alpha = 0', 'AVL ft (Tab. 6)'),
        ('CMa', 'dCM/dalpha [1/rad]', 'AVL st'),
        ('CMq', 'dCM/dq [1/rad]', 'AVL st'),
        ('CMit', 'dCM/dit [1/rad]', 'AVL st x 180/pi'),
        ('CMde', 'dCM/ddelta_e [1/rad]', 'AVL st x 180/pi'),
        ('CYb', 'dCY/dbeta [1/rad]', 'AVL st, sinal invertido'),
        ('CYp', 'dCY/dp [1/rad]', 'AVL st, sinal invertido'),
        ('CYr', 'dCY/dr [1/rad]', 'AVL st, sinal invertido'),
        ('CYdr', 'dCY/ddelta_r [1/rad]', 'AVL st x 180/pi'),
        ('Clb', 'dCl/dbeta [1/rad]', 'AVL st'),
        ('Clp', 'dCl/dp [1/rad]', 'AVL sb'),
        ('Clr', 'dCl/dr [1/rad]', 'AVL sb'),
        ('Clda', 'dCl/ddelta_a [1/rad]', 'AVL sb, sinal invertido, x 180/pi'),
        ('Cldr', 'dCl/ddelta_r [1/rad]', 'AVL sb, sinal invertido, x 180/pi'),
        ('Cnb', 'dCn/dbeta [1/rad]', 'AVL st'),
        ('Cnp', 'dCn/dp [1/rad]', 'AVL sb'),
        ('Cnr', 'dCn/dr [1/rad]', 'AVL sb'),
        ('Cnda', 'dCn/ddelta_a [1/rad]', 'AVL sb, sinal invertido, x 180/pi'),
        ('Cndr', 'dCn/ddelta_r [1/rad]', 'AVL sb, sinal invertido, x 180/pi'),
    ]
    A(_t([[k, d, _f(v[k], 6), f] for k, d, f in desc],
         ['parametro', 'explicacao', 'valor', 'fonte']))
    pos = t9.get('posicao_do_motor', {})
    if pos:
        A('\n> **Sobre x_p e z_p.** O centro da nacelle esta em x = %.3f m do '
          'nariz e o CG traseiro em x = %.3f m, ou seja, o motor fica %.3f m '
          'A FRENTE do CG. Na convencao do `designTool` (x positivo para tras) '
          'isso da x_p = %.3f m; se o modelo de MVO usar x positivo para '
          'frente, use x_p = %+.3f m. Ja z_p ja esta com o sinal invertido '
          'conforme o enunciado (z positivo para baixo), entao z_p = %+.3f m '
          'indica motor ABAIXO do CG. Confirme a origem com o professor de '
          'MVO antes de alimentar o modelo.\n'
          % (pos['x_engine_abs'], pos['xcg_aft'],
             abs(pos['xp_x_positivo_para_frente']),
             pos['xp_x_positivo_para_tras'],
             pos['xp_x_positivo_para_frente'],
             pos['zp_z_positivo_para_baixo']))

    A('\n**Leitura rapida.** Cma = %.3f 1/rad (estavel em arfagem) e '
      'Clb = %.3f 1/rad (estavel em rolamento / efeito diedro correto). '
      % (v['CMa'], v['Clb']))
    if v['Cnb'] < 0:
        A('Ja Cnb = %.3f 1/rad **no modelo com fuselagem**: negativo, isto e, '
          'o modelo indica instabilidade direcional. '
          'Isso vem do BODY da fuselagem no AVL, cujo momento desestabilizante '
          'e cerca de 1.7x o previsto pela teoria de corpos esbeltos e ~3x a '
          'correlacao de Raymer usada no `designTool`. '
          'Sem a fuselagem no modelo, o AVL da Cnb positivo. '
          'A conclusao pratica e que a EV, dimensionada com Cvt = %.3f '
          '(o minimo admitido pelo grupo), tem pouca margem direcional e '
          'merece ser reavaliada com um metodo especifico (DATCOM/Roskam) '
          'antes de fechar o projeto. Veja `python run.py --sensibilidade`.'
          % (v['Cnb'], 0.075))
    else:
        A('Cnb = %.3f 1/rad (estabilidade direcional positiva).' % v['Cnb'])

    # ------------------------------------------------------------ Extras ---
    if util.exists('90_sensibilidade'):
        sen = util.load('90_sensibilidade')
        A('\n\n## 10. Sensibilidade do modelo AVL (fuselagem e nacelles)\n')
        A('O BODY da fuselagem no AVL e um modelo de corpo esbelto grosseiro e '
          'domina Cma, x_np e Cnb. As nacelles, modeladas como superficies '
          'anelares, tambem desestabilizam. A tabela mostra o efeito de '
          'liga-los e desliga-los (CG traseiro, ponto de projeto):\n')
        A(_t([[str(c['body']), str(c['nacelle']), _f(c['Cma'], 3),
               _f(c['Cnb'], 4), _f(c['CYb'], 4), _f(c['xnp'], 3),
               _f(c['xnp_pct_mac'], 1), '%.1f%%' % (c['SM_aft'] * 100)]
              for c in sen['casos']],
             ['BODY', 'NACELLE', 'Cma', 'Cnb', 'CYb', 'x_np [m]',
              'x_np [% MAC]', 'SM traseiro']))
        ref = sen['referencia_designTool']
        A('\nReferencia do `designTool`: x_np = %.3f m (%.1f%% MAC), '
          'SM traseiro = %.1f%%.\n'
          % (ref['xnp'], ref['xnp_pct_mac'], ref['SM_aft'] * 100))
        A('\nO modelo com fuselagem e sem nacelles e o que mais se aproxima do '
          '`designTool` (%.1f%% contra %.1f%% MAC), o que faz sentido: a '
          'correlacao de Raymer usada no `balance.py` inclui a fuselagem mas '
          'ignora as nacelles. O caso adotado como referencia neste relatorio '
          '(BODY e NACELLE ligados) e o mais completo; sem o BODY o AVL perde '
          'toda a contribuicao desestabilizante da fuselagem e o x_np vai para '
          '%.0f%% MAC, valor claramente irreal para um transporte.\n'
          % (sen['casos'][1]['xnp_pct_mac'], ref['xnp_pct_mac'],
             sen['casos'][3]['xnp_pct_mac']))
        A('Os interruptores estao em `lab4/config.py` '
          '(`INCLUDE_BODY`, `INCLUDE_NACELLES`).')

    A('\n\n## 11. Como reproduzir e como mexer nos resultados\n')
    A('```bash')
    A('cd Lab4')
    A('python run.py --list        # lista os estagios')
    A('python run.py --all         # roda tudo do zero (~5 min)')
    A('python run.py 5 8 9         # roda so os estagios 5, 8 e 9')
    A('python run.py --sensibilidade   # estudo BODY/NACELLE on-off')
    A('```\n')
    A('Cada estagio le apenas arquivos de `out/` e grava outros em `out/`. ')
    A('Para forcar um valor (por exemplo um i_t arredondado), edite o JSON '
      'correspondente e rode so os estagios seguintes.\n')
    A(_t([
        ['01', 'designTool + ponto de projeto', '01_design_point.json'],
        ['02', 'escreve fwd.avl / aft.avl', '02_avl_model.json'],
        ['03', 'incidencia da EH', '03_tail_incidence.json'],
        ['04', 'metodo da secao critica', '04_critical_section.json'],
        ['05', 'polares + ajuste CD(alpha)', '05_polars.json'],
        ['06', 'ponto neutro / margem estatica', '06_neutral_point.json'],
        ['07', 'derivadas (Tab. 6, 7, 9)', '07_tabela9.json'],
        ['08', 'figuras', 'figs/*.png'],
        ['09', 'este relatorio', 'RESULTADOS.md'],
    ], ['estagio', 'o que faz', 'saida principal']))

    txt = '\n'.join(L) + '\n'
    path = os.path.join(config.LAB4_DIR, 'RESULTADOS.md')
    with open(path, 'w') as fid:
        fid.write(txt)
    print('  -> RESULTADOS.md (%d linhas)' % txt.count('\n'))
    return path


if __name__ == '__main__':
    run()
