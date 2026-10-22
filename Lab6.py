# %% AVL

import os
import json
import shutil

import numpy as np
from scipy.interpolate import CubicSpline

from designTool.aerodynamics import aerodynamics
from designTool.auxiliary import atmosphere
from designTool.constants import gravity, ft2m
from designTool.standard_airplane import standard_airplane
from designTool.analyze import analyze
from designTool.moment_of_inertia import moment_of_inertia

# Hipoteses de montagem [graus]; torcao = incidencia da ponta menos a da raiz.
# AVL 3.40 Linux: CG aft, Mach=0.85, CL=0.4483, Cm=0 via profundor;
# alpha=-0.00001 grau.
WING_ROOT_INCIDENCE_DEG = 5.9311
WING_TWIST_TIP_DEG = -7.0
TAIL_INCIDENCE_DEG = 0.0
# Superfícies de controle da empenagem não definidas no designTool
XHINGE_ELEV = 0.60 # Posição da charneira do profundor (x/c)
XHINGE_RUDDER = 0.70 # Posição da charneira do leme (x/c)
AIL_TIP_MARGIN = 0.02 # Margem entre aileron e ponta da asa em fração de b_w/2 (mesma de plots.py)
Z_GAP = 0.1 # Folga vertical mínima [m] entre superfícies e fuselagem/naceles (evita erros no AVL)

airplane_name = "Tomav"
airplane = standard_airplane(airplane_name)
analyze(airplane)

# Pasta de saída (mesma do executável do AVL, onde está fuseB737_nondim.dat)
AVL_DIR = "AVL_package"
AIRFOIL_FILE = "airfoil.dat"
shutil.copy(AIRFOIL_FILE, os.path.join(AVL_DIR, AIRFOIL_FILE))

#========================================
# DADOS DO AVIÃO

inputs = airplane['inputs']
geo = airplane['geometry']

# Referências
S_w = inputs['S_w']
cm_w = geo['cm_w']
b_w = geo['b_w']

xcg = airplane['balance']['CG_hist']['xcg_efpc']

Mach_cruise = inputs['Mach_cruise']
altitude_cruise = inputs['altitude_cruise']

tm = airplane['thrust_matching']
W0 = float(airplane["thrust_matching"]["W0"])
mf = airplane['fuel_weight']['Mf_hist']
W_cruise_start = tm['W0']
for phase in ('start', 'taxi', 'takeoff', 'climb'):
    W_cruise_start *= mf[phase]
W_cruise_end = W_cruise_start * mf['cruise']

for W, nome_caso in zip((W_cruise_start, W_cruise_end), ("Início do Cruzeiro", "Fim do Cruzeiro")):
    print(f"========== AVL {nome_caso} ==========")
    W_fuel_remaining = W - tm['W_empty'] - inputs['W_crew'] - inputs['W_payload']
    fuel_frac = W_fuel_remaining / tm['W_fuel']
    moment_of_inertia(airplane, fuel_frac=fuel_frac, payload_frac=1.0)
    with open("tomav.json", "w") as f:
        json.dump(airplane, f, indent=4)

    atm_data = atmosphere(altitude_cruise)
    v_cruise = Mach_cruise*atm_data['speed_of_sound']
    rho = atm_data['density']
    q_cruise = 0.5 * rho * v_cruise**2
    CL_cruise = W / (q_cruise * S_w)
    Re_mac = rho * v_cruise * cm_w / atm_data['dyn_viscosity']
    # Secao de referencia do notebook: cl estimado pela distribuicao eliptica.
    eta_mac = geo['ym_w'] / geo['yt_w']
    tc_mac = inputs['tcr_w'] + eta_mac * (inputs['tct_w'] - inputs['tcr_w'])
    cl_mac_elliptic = (4 * W / (np.pi * b_w) * np.sqrt(1 - eta_mac**2)
                    / (q_cruise * cm_w))

    CD_design, CLmax_design, dragDict = aerodynamics(airplane, Mach=Mach_cruise, altitude=altitude_cruise,
                                CL=CL_cruise, n_engines_failed=0, highlift_config='clean',
                                lg_down=0, h_ground=0)

    # Arrasto não-induzido (o AVL calcula o induzido)
    CDp = dragDict['CD0'] + dragDict['CDwave']

    #========================================
    # DESLOCAMENTOS VERTICAIS (evitam intersecções no AVL)

    # Contorno da fuselagem (BFILE adimensional: x/L_f, z/D_f; superior do nariz até x=0, depois inferior)
    # O AVL interpola o contorno com spline cúbica na coordenada de arco, que ultrapassa os
    # pontos do arquivo perto dos cantos; os limites são calculados sobre essa spline
    BODY_FILE = "fuseB737_nondim.dat"
    body = np.loadtxt(os.path.join(AVL_DIR, BODY_FILE), skiprows=1)
    s_body = np.concatenate(([0.0], np.cumsum(np.hypot(*np.diff(body, axis=0).T))))
    s_fine = np.linspace(0.0, s_body[-1], 20001)
    x_body = CubicSpline(s_body, body[:, 0])(s_fine)*inputs['L_f']
    z_body = CubicSpline(s_body, body[:, 1])(s_fine)*inputs['D_f']
    upper_body = s_fine <= s_body[np.argmin(body[:, 0])]

    def body_z(x_start, x_end, surface):
        '''
        Retorna o z extremo [m] da fuselagem entre x_start e x_end:
        máximo do contorno superior ou mínimo do inferior.
        '''
        in_range = (x_body >= x_start) & (x_body <= x_end)
        if surface == 'upper':
            return z_body[in_range & upper_body].max()
        return z_body[in_range & ~upper_body].min()

    # Asa desce até logo abaixo da fuselagem; empenagens sobem até logo acima dela
    dz_w = min(0.0, body_z(inputs['xr_w'], inputs['xr_w'] + geo['cr_w'], 'lower') - Z_GAP - inputs['zr_w'])
    dz_h = max(0.0, body_z(geo['xr_h'], geo['xr_h'] + geo['cr_h'], 'upper') + Z_GAP - inputs['zr_h'])
    dz_v = max(0.0, body_z(geo['xr_v'], geo['xr_v'] + geo['cr_v'], 'upper') + Z_GAP - inputs['zr_v'])

    # Naceles descem até logo abaixo da asa (menor z da asa na faixa de envergadura da nacele)
    R_n = inputs['D_n']/2
    y_nac = np.array([inputs['y_n'] - R_n, inputs['y_n'] + R_n])
    z_wing_nac = inputs['zr_w'] + dz_w + y_nac/geo['yt_w']*(geo['zt_w'] - inputs['zr_w'])
    z_n = min(inputs['z_n'], z_wing_nac.min() - Z_GAP - R_n)

    #========================================
    # SEÇÕES DA ASA

    def wing_sections():
        '''
        Cria as seções da asa entre a raiz e a ponta, incluindo quebras
        onde começam/terminam flap, slat e aileron.
        Um controle só atua entre duas seções consecutivas que o contenham.
        '''

        yt_w = geo['yt_w']

        # Extensão de cada controle em fração da semi-envergadura: (início, fim, xhinge, ganho, sinal duplicata)
        y_fus = inputs['D_f']/b_w
        controls = {
            'slat': (y_fus, inputs['b_slat_b_wing'], -inputs['c_slat_c_wing'], -1.0, +1),
            'flap': (y_fus, inputs['b_flap_b_wing'], 1 - inputs['c_flap_c_wing'], 1.0, +1),
            'aileron': (1 - AIL_TIP_MARGIN - inputs['b_ail_b_wing'], 1 - AIL_TIP_MARGIN,
                        1 - inputs['c_ail_c_wing'], -1.0, -1),
        }

        eta_list = {0.0, 1.0}
        for eta_start, eta_end, *_ in controls.values():
            eta_list.update([eta_start, eta_end])

        sections = ""
        for eta in sorted(eta_list):

            # Interpolação linear entre raiz e ponta (bordo de ataque)
            xle = inputs['xr_w'] + eta*(geo['xt_w'] - inputs['xr_w'])
            yle = eta*yt_w
            zle = inputs['zr_w'] + eta*(geo['zt_w'] - inputs['zr_w'])
            chord = geo['cr_w'] + eta*(geo['ct_w'] - geo['cr_w'])
            ainc = WING_ROOT_INCIDENCE_DEG + eta * WING_TWIST_TIP_DEG

            control_lines = ""
            for name, (eta_start, eta_end, xhinge, gain, sgn_dup) in controls.items():
                if eta_start - 1e-9 <= eta <= eta_end + 1e-9:
                    control_lines += f"""CONTROL
{name:<8} {gain:4.1f}  {xhinge:.3f}  0. 0. 0.  {sgn_dup:+d}
"""

            sections += f"""
# eta = {eta:.3f}
SECTION
#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace
{xle:.4f}  {yle:.4f}  {zle:.4f}  {chord:.4f}  {ainc:.4f}
AFILE
{AIRFOIL_FILE}
{control_lines}DESIGN
iw 1.0
"""

        return sections

    #========================================
    # ARQUIVO AVL

    def avl_file():
        return f"""{nome_caso.replace("í","i")}
#Mach
 {Mach_cruise:.3f}

#IYsym   IZsym   Zsym
 0       0       0.0

#Sref    Cref    Bref
{S_w:.4f}   {cm_w:.4f}   {b_w:.4f}

#Xref    Yref    Zref
{xcg:.4f}   0.0     0.0

# CDp
{CDp:.5f}


#--------------------------------------------------
SURFACE
Wing
#Nchordwise  Cspace  Nspanwise  Sspace
12           1.0     40         -1.1

COMPONENT
1

YDUPLICATE
0.0

ANGLE
0.0

SCALE
1.0   1.0   1.0

TRANSLATE
0.0  0.0  {dz_w:.4f}
{wing_sections()}
#--------------------------------------------------
SURFACE
Stab
#Nchordwise  Cspace  Nspanwise  Sspace
6            1.0     15         -1.1

COMPONENT
1

YDUPLICATE
0.0

SCALE
1.0  1.0  1.0

TRANSLATE
0.0  0.0  {dz_h:.4f}

SECTION
#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace
{geo['xr_h']:.4f}  0.0  {inputs['zr_h']:.4f}  {geo['cr_h']:.4f}  {TAIL_INCIDENCE_DEG:.4f}
CONTROL
elevator  1.0  {XHINGE_ELEV:.3f}    0. 0. 0.  1
DESIGN
it 1.0

SECTION
#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace
{geo['xt_h']:.4f}  {geo['yt_h']:.4f}  {geo['zt_h']:.4f}  {geo['ct_h']:.4f}  {TAIL_INCIDENCE_DEG:.4f}
CONTROL
elevator  1.0  {XHINGE_ELEV:.3f}    0. 0. 0.  1
DESIGN
it 1.0

#--------------------------------------------------
SURFACE
Fin
#Nchordwise  Cspace   Nspanwise  Sspace
7            1.0      11          1.0

COMPONENT
1

SCALE
1.0   1.0  1.0

TRANSLATE
0.0  0.0  {dz_v:.4f}

SECTION
#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace
{geo['xr_v']:.4f}  0.0  {inputs['zr_v']:.4f}  {geo['cr_v']:.4f}  0.
CONTROL
rudder  1.0  {XHINGE_RUDDER:.3f}   0. 0. 0.  1

SECTION
#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace
{geo['xt_v']:.4f}  0.0  {geo['zt_v']:.4f}  {geo['ct_v']:.4f}  0.
CONTROL
rudder  1.0  {XHINGE_RUDDER:.3f}   0. 0. 0.  1

#--------------------------------------------------
BODY
Fuselage
# Nbody Bspace
30 1.0

SCALE
# Length Diameter Diameter
{inputs['L_f']:.4f} {inputs['D_f']:.4f} {inputs['D_f']:.4f}

BFILE
{BODY_FILE}

#--------------------------------------------------
SURFACE
Nacelle
#Nchordwise  Cspace   Nspanwise  Sspace
6            1.0      12          0.0

COMPONENT
1

YDUPLICATE
0.0

SCALE
# Length, Hor. radius, and Vert. radius
{inputs['L_n']:.4f}   {inputs['D_n']/2:.4f}  {inputs['D_n']/2:.4f}

TRANSLATE
{inputs['x_n']:.4f}  {inputs['y_n']:.4f}  {z_n:.4f}

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  0.0    1.0       1.0   0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  0.5    0.866     1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  0.866  0.5       1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  1.0    0.0       1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  0.866 -0.5       1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  0.5   -0.866     1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  0.0   -1.0       1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00 -0.5   -0.866     1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00 -0.866 -0.5       1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00 -1.0    0.0       1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00 -0.866  0.5       1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00 -0.5    0.866     1.0    0.    1          0.

SECTION
#Xle   Yle    Zle      Chord   Ainc  Nspanwise  Sspace
 0.00  0.0    1.0       1.0    0.    1          0.
"""

    with open(f"{nome_caso.replace("í","i").split()[0]}.avl", "w") as f:
        f.write(avl_file())

    print(f"W [N]: {W:.1f} | CL: {CL_cruise:.4f} | CDp: {CDp:.5f}")
    print(f"dz_w [m]: {dz_w:.4f} | dz_h [m]: {dz_h:.4f} | dz_v [m]: {dz_v:.4f} | z_n [m]: {z_n:.4f}")
    print(f"xcg_aft [m]: {airplane['balance']['xcg_aft']:.4f} | xcg_fwd [m]: {airplane['balance']['xcg_fwd']:.4f}")

    # %% Diagrama

    import matplotlib.pyplot as plt
    import numpy as np

    from designTool.auxiliary import atmosphere
    from designTool.constants import gravity, ft2m

    EAS2KEAS = 3600 / 1852  # 1 nó = 1852 m / 3600 s
    rho_0 = 1.225  # kg/m³

    # Indique os valores de:
    # V_C e V_D são TAS; o gráfico usa velocidade equivalente.
    print(f"\n========== DIAGRAMA {nome_caso} ==========")
    print(f"MTOW = {W0:.1f} N = {W0/gravity:.1f} kgf")
    print(f"W = {W:.1f} N = {W/gravity:.1f} kgf")
    print(f"S_w = {S_w:.1f} m²")
    print(f"cm_w = {cm_w:.1f} m")
    print(f"altitude_cruise = {altitude_cruise:.1f} m")
    print(f"CLmax_design = {CLmax_design:.2f}")
    CLmin = -0.80
    print(f"CLmin = {CLmin:.2f}")
    CL_alpha = 6.3  # rad^-1 # TODO: mudar
    Mach_cruise = airplane["inputs"]["Mach_cruise"]
    print(f"Mach_cruise = {Mach_cruise:.3f}")
    Mach_D = Mach_cruise + 0.07  # Dado do exercício confirmado; exceção ao critério da p. 22.
    print(f"Mach_D = {Mach_D:.3f}")
    U_de = 33.7 * ft2m  # m/s, rajada em V_C na altitude em estudo
    print(f"U_de = {U_de:.1f} m/s = {U_de/ft2m:.1f} ft/s")
    U_de_D = U_de / 2  # Hipótese do PDF: metade da rajada de V_C em V_D.
    n_max = 2.5
    print(f"n_max = {n_max:.1f}")
    n_min = -1.0
    print(f"n_min = {n_min:.1f}")

    # Atmosfera e velocidades.
    atm = atmosphere(altitude_cruise)
    a = atm['speed_of_sound']
    rho = atm['density']
    sigma = rho / rho_0
    TAS2EAS = np.sqrt(sigma)
    W_S = W / S_w

    V_C = Mach_cruise * a
    V_D = Mach_D * a
    V_S1 = np.sqrt(2 * W / (rho * S_w * CLmax_design))
    V_Sneg = np.sqrt(2 * abs(n_min) * W / (rho * S_w * abs(CLmin)))
    V_A = V_S1 * np.sqrt(n_max)

    V_C_EAS = V_C * TAS2EAS
    V_D_EAS = V_D * TAS2EAS
    V_S1_EAS = V_S1 * TAS2EAS
    V_Sneg_EAS = V_Sneg * TAS2EAS
    V_A_EAS = V_A * TAS2EAS

    V_C_KEAS = V_C_EAS * EAS2KEAS
    V_D_KEAS = V_D_EAS * EAS2KEAS
    V_S1_KEAS = V_S1_EAS * EAS2KEAS
    V_Sneg_KEAS = V_Sneg_EAS * EAS2KEAS
    V_A_KEAS = V_A_EAS * EAS2KEAS

    # Alívio de rajada: rho local em mu_g e rho_0 na equação em EAS do PDF.
    mu_g = 2 * W_S / (rho * cm_w * CL_alpha * gravity)
    K_g = 0.88 * mu_g / (5.3 + mu_g)
    k_rajada = rho_0 * CL_alpha * K_g / (2 * W_S)
    k_estol_pos = rho_0 * S_w * CLmax_design / (2 * W)
    k_estol_neg = rho_0 * S_w * CLmin / (2 * W)
    m_neg = -n_min / (V_D_EAS - V_C_EAS)
    b_neg = n_min - m_neg * V_C_EAS
    m_U = (U_de_D - U_de) / (V_D_EAS - V_C_EAS)
    b_U = U_de - m_U * V_C_EAS

    # Malha em m/s EAS, incluindo exatamente as velocidades de referência.
    V_E = np.unique(np.r_[
        np.linspace(0, V_D_EAS, 2001),
        V_S1_EAS, V_Sneg_EAS, V_A_EAS, V_C_EAS, V_D_EAS,
    ])
    V_KEAS = V_E * EAS2KEAS

    n_estol_pos = k_estol_pos * V_E**2
    n_estol_neg = k_estol_neg * V_E**2
    n_lim_neg = np.interp(V_E, [0, V_C_EAS, V_D_EAS], [n_min, n_min, 0])
    n_man_pos = np.minimum(n_estol_pos, n_max)
    n_man_neg = np.maximum(n_estol_neg, n_lim_neg)

    # Reduzir U linearmente entre V_C e V_D torna Delta_n quadrático nesse trecho.
    U = np.interp(V_E, [0, V_C_EAS, V_D_EAS], [U_de, U_de, U_de_D])
    delta_n = k_rajada * V_E * U
    n_raj_pos = 1 + delta_n
    n_raj_neg = 1 - delta_n
    n_comb_pos = n_man_pos
    n_comb_neg = np.minimum(n_man_neg, n_raj_neg)

    # Convenção gráfica: recortar os dois ramos nas velocidades de estol
    # a +1 g e -1 g, mantendo as curvas calculadas completas nas tracejadas.
    regiao_pos = V_E >= V_S1_EAS
    regiao_neg = V_E >= V_Sneg_EAS
    i_S1 = np.flatnonzero(V_E == V_S1_EAS)[0]
    i_Sneg = np.flatnonzero(V_E == V_Sneg_EAS)[0]
    i_C = np.flatnonzero(V_E == V_C_EAS)[0]
    i_D = np.flatnonzero(V_E == V_D_EAS)[0]

    # Fórmulas simbólicas com resultados na mesma linha, sem repetir as entradas.
    print('\nGRANDEZAS CALCULADAS')
    print(f'ISA: a = {a:.3f} m/s; rho = {rho:.6f} kg/m³')
    print(f'sigma = rho / rho_0 = {sigma:.6f}; TAS2EAS = sqrt(sigma) = {TAS2EAS:.6f}')
    print(f'W_S = W / S_ref = {W_S:.3f} N/m²')

    print('\nVELOCIDADES')
    print(f'Mach_D = Mach_C + 0.07 = {Mach_D:.4f}; V_D / V_C = {V_D / V_C:.6f}')
    print('Adota-se M_D = 0.84 como dado específico do exercício; '
        'o critério V_D >= 1.25 V_C da p. 22 não é aplicado neste caso.')
    print('Conversão: V_E = V_TAS * TAS2EAS; V_KEAS = V_E * EAS2KEAS')
    for nome, formula, velocidade in [
        ('V_S1', 'sqrt(2 * W / (rho * S_ref * CLmax))', V_S1),
        ('V_Sneg', 'sqrt(2 * abs(n_min) * W / (rho * S_ref * abs(CLmin)))', V_Sneg),
        ('V_A', 'V_S1 * sqrt(n_max)', V_A),
        ('V_C', 'Mach_C * a', V_C),
        ('V_D', 'Mach_D * a', V_D),
    ]:
        print(f'{nome} = {formula} = {velocidade:.3f} m/s TAS = '
            f'{velocidade * TAS2EAS:.3f} m/s EAS = {velocidade * TAS2EAS * EAS2KEAS:.3f} KEAS')

    print('\nRAJADA (V_E EM m/s EAS)')
    print(f'mu_g = 2 * W_S / (rho * c_ref * CL_alpha * gravity) = {mu_g:.6f}')
    print(f'K_g = 0.88 * mu_g / (5.3 + mu_g) = {K_g:.6f}')
    print(f'U_de_D = U_de / 2 = {U_de_D:.6f} m/s = {U_de_D / ft2m:.3f} ft/s (hipótese do PDF)')
    print(f'k_rajada = rho_0 * CL_alpha * K_g / (2 * W_S) = {k_rajada:.9f}')
    print('U(V_E) = U_de até V_C_EAS; depois U(V_E) = m_U * V_E + b_U até V_D_EAS')
    print(f'm_U = (U_de_D - U_de) / (V_D_EAS - V_C_EAS) = {m_U:.9f}')
    print(f'b_U = U_de - m_U * V_C_EAS = {b_U:.6f} m/s')
    print(f'delta_n = k_rajada * V_E * U(V_E): em V_C = {delta_n[i_C]:.6f}; em V_D = {delta_n[i_D]:.6f}')
    print(f'n_raj_pos = 1 + delta_n: em V_C = {n_raj_pos[i_C]:.6f}; em V_D = {n_raj_pos[i_D]:.6f}')
    print(f'n_raj_neg = 1 - delta_n: em V_C = {n_raj_neg[i_C]:.6f}; em V_D = {n_raj_neg[i_D]:.6f}')

    print('\nMANOBRA (V_E EM m/s EAS)')
    print(f'k_estol_pos = rho_0 * S_ref * CLmax / (2 * W) = {k_estol_pos:.9f}')
    print(f'k_estol_neg = rho_0 * S_ref * CLmin / (2 * W) = {k_estol_neg:.9f}')
    print(f'n_estol_pos = k_estol_pos * V_E²: em V_S1 = {n_estol_pos[i_S1]:.6f}')
    print(f'n_estol_neg = k_estol_neg * V_E²: em V_Sneg = {n_estol_neg[i_Sneg]:.6f}')
    print(f'n_lim_neg = n_min = {n_min:.3f} até V_C_EAS; depois n_lim_neg = m_neg * V_E + b_neg até V_D_EAS')
    print(f'm_neg = -n_min / (V_D_EAS - V_C_EAS) = {m_neg:.9f} s/m')
    print(f'b_neg = n_min - m_neg * V_C_EAS = {b_neg:.6f}')
    print(f'n_man_pos = min(n_estol_pos, n_max): máximo = {np.max(n_man_pos):.6f}')
    print(f'n_man_neg = max(n_estol_neg, n_lim_neg): em V_C = {n_man_neg[i_C]:.6f}; em V_D = {n_man_neg[i_D]:.6f}')

    print('\nENVELOPE COMBINADO E FECHAMENTOS')
    print(f'n_comb_pos = max(n_man_pos, n_raj_pos): máximo = {np.max(n_comb_pos[regiao_pos]):.6f}')
    print(f'n_comb_neg = min(n_man_neg, n_raj_neg): mínimo = {np.min(n_comb_neg[regiao_neg]):.6f}')
    print(f'Vertical V_E = V_S1_EAS: de n = 0 até n_comb_pos(V_S1_EAS) = {n_comb_pos[i_S1]:.6f}')
    print(f'Vertical V_E = V_Sneg_EAS: de n_comb_neg(V_Sneg_EAS) = {n_comb_neg[i_Sneg]:.6f} até n = 0')
    print(f'Vertical V_E = V_D_EAS: de n_comb_neg(V_D_EAS) = {n_comb_neg[i_D]:.6f} '
        f'até n_comb_pos(V_D_EAS) = {n_comb_pos[i_D]:.6f}')
    print('Recortes gráficos nas velocidades de estol a +1 g e -1 g; '
        'entre eles, fechamento em n = 0. Tracejadas completas de zero a V_D_EAS.')

    # Um único gráfico, sem resultados numéricos nas anotações.
    plt.figure(figsize=(12, 7))
    plt.fill_between(V_KEAS, 0, n_comb_pos, where=regiao_pos, color='steelblue', alpha=0.12)
    plt.fill_between(V_KEAS, n_comb_neg, 0, where=regiao_neg, color='steelblue', alpha=0.12)
    plt.plot(V_KEAS[regiao_pos], n_comb_pos[regiao_pos], color='black', linewidth=2.8, label='Envelope combinado')
    plt.plot(V_KEAS[regiao_neg], n_comb_neg[regiao_neg], color='black', linewidth=2.8)
    # As linhas tracejadas de construção continuam de zero até V_D.
    plt.plot(V_KEAS, n_man_pos, '--', color='tab:blue', linewidth=1.5, label='Manobra')
    plt.plot(V_KEAS, n_man_neg, '--', color='tab:blue', linewidth=1.5)
    plt.plot(V_KEAS, n_raj_pos, '--', color='tab:red', linewidth=1.5, label='Rajada')
    plt.plot(V_KEAS, n_raj_neg, '--', color='tab:red', linewidth=1.5)

    # Fechamentos nos dois recortes de estol e na velocidade de mergulho.
    plt.plot([V_S1_KEAS, V_S1_KEAS], [0, n_comb_pos[i_S1]], color='black', linewidth=2)
    plt.plot([V_Sneg_KEAS, V_Sneg_KEAS], [n_comb_neg[i_Sneg], 0], color='black', linewidth=2)
    plt.plot([V_S1_KEAS, V_Sneg_KEAS], [0, 0], color='black', linewidth=2)
    plt.plot([V_D_KEAS, V_D_KEAS], [n_comb_neg[i_D], n_comb_pos[i_D]], color='black', linewidth=2)

    y_anotacoes = np.max(n_comb_pos[regiao_pos]) + 0.35
    for nome, velocidade in [(r'$V_{S1}$', V_S1_KEAS), (r'$V_{Sneg}$', V_Sneg_KEAS),
                            (r'$V_A$', V_A_KEAS), (r'$V_C$', V_C_KEAS), (r'$V_D$', V_D_KEAS)]:
        plt.axvline(velocidade, color='0.55', linestyle=':', linewidth=0.8)
        plt.text(velocidade, y_anotacoes, nome, ha='center', va='center', fontsize=11)

    plt.axhline(0, color='0.4', linewidth=0.7, zorder=0)
    plt.minorticks_on()
    plt.grid(which='major', color='0.75', linewidth=0.7)
    plt.grid(which='minor', color='0.87', linestyle=':', linewidth=0.5)
    plt.xlim(0, V_D_KEAS * 1.05)
    plt.ylim(min(-1.2, np.min(n_comb_neg[regiao_neg]) - 0.25), y_anotacoes + 0.25)
    plt.xlabel('Velocidade equivalente [KEAS]')
    plt.ylabel('Fator de carga n')
    plt.title(f'Diagrama V-g-n - {nome_caso}')
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(f'Lab6_{nome_caso.split()[0]}.png', dpi=200)
    print(f'Diagrama salvo emLab6_{nome_caso.split()[0]}.png')
    plt.show()
