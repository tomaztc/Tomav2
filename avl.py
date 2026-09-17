import os
import json
import shutil

import numpy as np

from designTool.aerodynamics import aerodynamics
from designTool.auxiliary import atmosphere
from designTool.standard_airplane import standard_airplane
from designTool.analyze import analyze
from designTool.moment_of_inertia import moment_of_inertia

airplane_name = "Tomav"
airplane = standard_airplane(airplane_name)
analyze(airplane)
moment_of_inertia(airplane, fuel_frac=0.5, payload_frac=1.0)

json.dump(airplane, open("tomav.json", "w"), indent=4)

# Pasta de saída (mesma do executável do AVL, onde está fuseB737_nondim.dat)
AVL_DIR = "AVL_package"
AIRFOIL_FILE = "airfoil.dat"
shutil.copy(AIRFOIL_FILE, os.path.join(AVL_DIR, AIRFOIL_FILE))

# Superfícies de controle da empenagem não definidas no designTool (valores do b737simple.avl)
XHINGE_ELEV = 0.60 # Posição da charneira do profundor (x/c)
XHINGE_RUDDER = 0.70 # Posição da charneira do leme (x/c)
AIL_TIP_MARGIN = 0.02 # Margem entre aileron e ponta da asa em fração de b_w/2 (mesma de plots.py)
Z_GAP = 0.01 # Folga vertical mínima [m] entre superfícies e fuselagem/naceles (evita erros no AVL)

#========================================
# DADOS DO AVIÃO

inputs = airplane['inputs']
geo = airplane['geometry']

# Referências
S_w = inputs['S_w']
cm_w = geo['cm_w']
b_w = geo['b_w']

# Condição de cruzeiro com metade do combustível
FUEL_FRAC = 0.5
Mach_cruise = inputs['Mach_cruise']
altitude_cruise = inputs['altitude_cruise']

W_cruise = (airplane['thrust_matching']['W_empty'] + inputs['W_crew'] +
            inputs['W_payload'] + FUEL_FRAC*airplane['thrust_matching']['W_fuel'])

atm_data = atmosphere(altitude_cruise)
v_cruise = Mach_cruise*atm_data['speed_of_sound']
rho = atm_data['density']
CL_cruise = 2.0*W_cruise/rho/S_w/v_cruise**2

_, _, dragDict = aerodynamics(airplane, Mach=Mach_cruise, altitude=altitude_cruise,
                              CL=CL_cruise, n_engines_failed=0, highlift_config='clean',
                              lg_down=0, h_ground=0)

# Arrasto não-induzido (o AVL calcula o induzido)
CDp = dragDict['CD0'] + dragDict['CDwave']

#========================================
# DESLOCAMENTOS VERTICAIS (evitam intersecções no AVL)

# Asa desce até logo abaixo da fuselagem; empenagens sobem até logo acima dela
R_f = inputs['D_f']/2
dz_w = min(0.0, -R_f - Z_GAP - inputs['zr_w'])
dz_h = max(0.0, R_f + Z_GAP - inputs['zr_h'])
dz_v = max(0.0, R_f + Z_GAP - inputs['zr_v'])

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
{xle:.4f}  {yle:.4f}  {zle:.4f}  {chord:.4f}  0.0
AFILE
{AIRFOIL_FILE}
{control_lines}DESIGN
iw 1.0
"""

    return sections

#========================================
# ARQUIVO AVL

def avl_file(xcg, label):

    return f"""{airplane_name} - CG {label} (xcg = {xcg:.4f} m), cruzeiro com {FUEL_FRAC*100:.0f}% do combustivel
# W = {W_cruise:.1f} N, CL = {CL_cruise:.4f}

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
{geo['xr_h']:.4f}  0.0  {inputs['zr_h']:.4f}  {geo['cr_h']:.4f}  0.
CONTROL
elevator  1.0  {XHINGE_ELEV:.3f}    0. 0. 0.  1
DESIGN
it 1.0

SECTION
#Xle    Yle    Zle     Chord   Ainc  Nspanwise  Sspace
{geo['xt_h']:.4f}  {geo['yt_h']:.4f}  {geo['zt_h']:.4f}  {geo['ct_h']:.4f}  0.
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
fuseB737_nondim.dat

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
