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
WING_ROOT_INCIDENCE_DEG = 0.0
WING_TWIST_TIP_DEG = -3.0
TAIL_INCIDENCE_DEG = 0.0

airplane_name = "Tomav"
airplane = standard_airplane(airplane_name)
# Mesma aeronave usada no ponto de projeto de Lab3_cordamedia.ipynb.
airplane['inputs']['tcr_w'] = 0.16
analyze(airplane)

# Pasta de saída (mesma do executável do AVL, onde está fuseB737_nondim.dat)
AVL_DIR = "AVL_package"
AIRFOIL_FILE = "airfoil.dat"
shutil.copy(AIRFOIL_FILE, os.path.join(AVL_DIR, AIRFOIL_FILE))

# Superfícies de controle da empenagem não definidas no designTool (valores do b737simple.avl)
XHINGE_ELEV = 0.60 # Posição da charneira do profundor (x/c)
XHINGE_RUDDER = 0.70 # Posição da charneira do leme (x/c)
AIL_TIP_MARGIN = 0.02 # Margem entre aileron e ponta da asa em fração de b_w/2 (mesma de plots.py)
Z_GAP = 0.1 # Folga vertical mínima [m] entre superfícies e fuselagem/naceles (evita erros no AVL)

#========================================
# DADOS DO AVIÃO

inputs = airplane['inputs']
geo = airplane['geometry']

# Referências
S_w = inputs['S_w']
cm_w = geo['cm_w']
b_w = geo['b_w']

# Meio do percurso de cruzeiro, conforme Lab3_cordamedia.ipynb:
# Breguet => W(R/2) = sqrt(W_inicio * W_fim), com carga paga completa.
Mach_cruise = inputs['Mach_cruise']
altitude_cruise = inputs['altitude_cruise']

tm = airplane['thrust_matching']
mf = airplane['fuel_weight']['Mf_hist']
W_cruise_start = tm['W0']
for phase in ('start', 'taxi', 'takeoff', 'climb'):
    W_cruise_start *= mf[phase]
W_cruise_end = W_cruise_start * mf['cruise']
W_cruise = np.sqrt(W_cruise_start * W_cruise_end)
W_fuel_remaining = W_cruise - tm['W_empty'] - inputs['W_crew'] - inputs['W_payload']
fuel_frac = W_fuel_remaining / tm['W_fuel']
moment_of_inertia(airplane, fuel_frac=fuel_frac, payload_frac=1.0)
with open("tomav.json", "w") as f:
    json.dump(airplane, f, indent=4)

atm_data = atmosphere(altitude_cruise)
v_cruise = Mach_cruise*atm_data['speed_of_sound']
rho = atm_data['density']
q_cruise = 0.5 * rho * v_cruise**2
CL_cruise = W_cruise / (q_cruise * S_w)
Re_mac = rho * v_cruise * cm_w / atm_data['dyn_viscosity']
# Secao de referencia do notebook: cl estimado pela distribuicao eliptica.
eta_mac = geo['ym_w'] / geo['yt_w']
tc_mac = inputs['tcr_w'] + eta_mac * (inputs['tct_w'] - inputs['tcr_w'])
cl_mac_elliptic = (4 * W_cruise / (np.pi * b_w) * np.sqrt(1 - eta_mac**2)
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

def avl_file(xcg, label):

    return f"""{airplane_name} - CG {label} (xcg = {xcg:.4f} m), meio do percurso de cruzeiro
# PONTO DE PROJETO - Lab3_cordamedia.ipynb (calculado com o designTool atual)
# Configuracao limpa; trem recolhido; todos os motores operantes; fora do efeito solo.
# Mach = {Mach_cruise:.4f}; altitude = {altitude_cruise:.2f} m ({altitude_cruise/ft2m:.0f} ft)
# rho = {rho:.8f} kg/m3; a = {atm_data['speed_of_sound']:.4f} m/s
# V = {v_cruise:.4f} m/s; q = {q_cruise:.4f} Pa; mu = {atm_data['dyn_viscosity']:.8e} Pa.s
# W_inicio_cruzeiro = {W_cruise_start:.4f} N; W_fim_cruzeiro = {W_cruise_end:.4f} N
# W_projeto = sqrt(W_inicio_cruzeiro * W_fim_cruzeiro) = {W_cruise:.4f} N
# Massa de projeto = {W_cruise/gravity:.4f} kg; g = {gravity:.4f} m/s2
# Combustivel restante = {W_fuel_remaining:.4f} N ({fuel_frac*100:.4f}% do combustivel da missao)
# CL_projeto = {CL_cruise:.8f}; Re_Cref = {Re_mac:.6e}
# CD0 = {dragDict['CD0']:.8f}; CDwave = {dragDict['CDwave']:.8f}; CDp = {CDp:.8f}
# CD_designTool = {CD_design:.8f}; CLmax_designTool = {CLmax_design:.8f} (estimativas externas ao AVL)
# Secao da MAC: y = {geo['ym_w']:.4f} m; c = {cm_w:.4f} m; t/c = {tc_mac:.6f}
# cl_MAC_eliptico = {cl_mac_elliptic:.8f} (hipotese do Lab3, nao resultado do AVL com washout)
#
# AVIAO - comprimentos em m, areas em m2, pesos em N, angulos em graus
# W0 = {tm['W0']:.4f}; W_empty = {tm['W_empty']:.4f}; W_fuel_missao = {tm['W_fuel']:.4f}
# W_payload = {inputs['W_payload']:.4f}; W_crew = {inputs['W_crew']:.4f}; T0 = {tm['T0']:.4f} N
# Sref = {S_w:.4f}; Cref = {cm_w:.4f}; Bref = {b_w:.4f}
# Asa: AR = {inputs['AR_w']:.4f}; taper = {inputs['taper_w']:.4f}
# Asa: cr = {geo['cr_w']:.4f}; ct = {geo['ct_w']:.4f}; tcr = {inputs['tcr_w']:.4f}; tct = {inputs['tct_w']:.4f}
# Asa: sweep = {np.degrees(inputs['sweep_w']):.4f}; dihedral = {np.degrees(inputs['dihedral_w']):.4f}
# Asa: incidencia_raiz = {WING_ROOT_INCIDENCE_DEG:.4f}; torcao_ponta_menos_raiz = {WING_TWIST_TIP_DEG:.4f}
# Asa: incidencia_ponta = {WING_ROOT_INCIDENCE_DEG + WING_TWIST_TIP_DEG:.4f}; Ainc(eta) = incidencia_raiz + eta * torcao
# EH: S = {geo['S_h']:.4f}; b = {geo['b_h']:.4f}; cr = {geo['cr_h']:.4f}; ct = {geo['ct_h']:.4f}
# EH: incidencia = {TAIL_INCIDENCE_DEG:.4f}; sweep = {np.degrees(inputs['sweep_h']):.4f}; dihedral = {np.degrees(inputs['dihedral_h']):.4f}
# EV: S = {geo['S_v']:.4f}; b = {geo['b_v']:.4f}; cr = {geo['cr_v']:.4f}; ct = {geo['ct_v']:.4f}
# EV: sweep = {np.degrees(inputs['sweep_v']):.4f}
# Fuselagem: L = {inputs['L_f']:.4f}; D = {inputs['D_f']:.4f}
# Naceles: quantidade = {inputs['n_engines']}; L = {inputs['L_n']:.4f}; D = {inputs['D_n']:.4f}
# Nacele direita: x = {inputs['x_n']:.4f}; y = {inputs['y_n']:.4f}; z_AVL = {z_n:.4f}
# Ajustes verticais AVL: dz_w = {dz_w:.4f}; dz_h = {dz_h:.4f}; dz_v = {dz_v:.4f}; folga = {Z_GAP:.4f}
# CGs limites: xcg_fwd = {airplane['balance']['xcg_fwd']:.4f}; xcg_aft = {airplane['balance']['xcg_aft']:.4f}
# Referencia deste arquivo: Xref = {xcg:.4f}; Yref = 0; Zref = 0
# Perfil da asa: {AIRFOIL_FILE}; contorno da fuselagem: {BODY_FILE}
# Controles: d1=slat, d2=flap, d3=aileron, d4=elevator, d5=rudder
# Charneiras x/c: slat = {-inputs['c_slat_c_wing']:.3f}; flap = {1-inputs['c_flap_c_wing']:.3f}
# Charneiras x/c: aileron = {1-inputs['c_ail_c_wing']:.3f}; elevator = {XHINGE_ELEV:.3f}; rudder = {XHINGE_RUDDER:.3f}
# DESIGN: g1=iw, g2=it; incrementos de incidencia sobre os valores de montagem acima.
# Mach e CDp abaixo sao valores de entrada; CL_projeto acima e apenas informativo, nao impoe trimagem.

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

for label in ['aft', 'fwd']:
    xcg = airplane['balance'][f'xcg_{label}']
    with open(os.path.join(AVL_DIR, f"{label}.avl"), "w") as f:
        f.write(avl_file(xcg, label))

print(f"W_cruise [N]: {W_cruise:.1f} | CL: {CL_cruise:.4f} | CDp: {CDp:.5f}")
print(f"dz_w [m]: {dz_w:.4f} | dz_h [m]: {dz_h:.4f} | dz_v [m]: {dz_v:.4f} | z_n [m]: {z_n:.4f}")
print(f"xcg_aft [m]: {airplane['balance']['xcg_aft']:.4f} | xcg_fwd [m]: {airplane['balance']['xcg_fwd']:.4f}")
