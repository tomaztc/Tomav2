"""
Parametros ajustaveis do Lab 04.

TUDO que nao vem diretamente do designTool esta aqui, para que o grupo possa
alterar hipoteses sem mexer no codigo dos estagios.
"""

import os

# ----------------------------------------------------------------------------
# Caminhos
# ----------------------------------------------------------------------------
LAB4_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(LAB4_DIR)                      # .../Tomav2
OUT_DIR = os.path.join(LAB4_DIR, 'out')                   # resultados intermediarios
AVL_DIR = os.path.join(LAB4_DIR, 'avl')                   # arquivos de entrada do AVL
FIG_DIR = os.path.join(LAB4_DIR, 'figs')
RUN_DIR = os.path.join(LAB4_DIR, 'avl_runs')              # logs brutos do AVL

# Executavel do AVL (macOS arm64 compilado localmente).
AVL_EXE = os.path.join(REPO_DIR, '..', 'Lab4', 'AVL_package', 'avl340')

# Perfil otimizado no Lab 03 (usado como AFILE das secoes da asa)
AIRFOIL_DAT = os.path.join(REPO_DIR, 'Lab3', 'airfoil_ajustado', 'airfoil.dat')
# Polar XFOIL do mesmo perfil (M=0.2, Re=30.1e6) usada para o cl_max de secao
AIRFOIL_POLAR = os.path.join(REPO_DIR, 'Lab3', 'airfoil_ajustado', 'polar.txt')
# Contorno nao-dimensional da fuselagem (fornecido com o AVL_package)
FUSE_DAT = os.path.join(REPO_DIR, 'AVL_package', 'fuseB737_nondim.dat')

# ----------------------------------------------------------------------------
# Aeronave
# ----------------------------------------------------------------------------
AIRPLANE_NAME = 'Tomav'          # chave em designTool.standard_airplane

# ----------------------------------------------------------------------------
# Ponto de projeto (questao 2)
# ----------------------------------------------------------------------------
FUEL_FRAC = 0.50                 # 50% da capacidade de combustivel
PAYLOAD_FRAC = 1.00              # 100% de carga paga
# Mach/altitude: por padrao usa Mach_cruise e altitude_cruise do designTool.
# Preencha abaixo para sobrescrever.
DESIGN_MACH = None               # ex.: 0.85
DESIGN_ALTITUDE = None           # ex.: 9875.5 [m]

# ----------------------------------------------------------------------------
# Hipoteses de geometria nao definidas pelo designTool
# ----------------------------------------------------------------------------
# Torcao geometrica (washout) linear da asa: incidencia na ponta [graus].
# O designTool NAO define torcao; -3 deg e um valor tipico de transporte e
# tem efeito forte no estol de ponta. Coloque 0.0 para asa sem torcao.
WING_TWIST_TIP_DEG = -3.0
WING_ROOT_INCIDENCE_DEG = 0.0    # incidencia da raiz da asa em relacao a fuselagem

# Aileron: fracao de semi-envergadura ocupada vem do designTool (b_ail_b_wing);
# aqui definimos apenas onde ele termina (fracao de b/2).
AIL_END_FRAC = 0.97

# Perfis das empenagens (AVL usa apenas a linha de camber -> simetricos)
HT_NACA = '0009'
VT_NACA = '0009'

# Componentes opcionais no modelo AVL
INCLUDE_BODY = True              # fuselagem (BODY + BFILE)
INCLUDE_NACELLES = True          # nacelles como superficies anelares

# Discretizacao
NCHORD_W, NSPAN_W = 10, 40
NCHORD_H, NSPAN_H = 8, 16
NCHORD_V, NSPAN_V = 8, 12

# ----------------------------------------------------------------------------
# Metodo da secao critica (questao 4)
# ----------------------------------------------------------------------------
MACH_LOWSPEED = 0.20
# cl_max do perfil. Se None, e lido do topo da polar XFOIL do Lab 03.
CLMAX_AIRFOIL_ROOT = None
CLMAX_AIRFOIL_TIP = None         # se None, usa o mesmo da raiz (cl_max constante)
ALPHA_SWEEP_LOWSPEED = (0.0, 26.0, 0.25)   # inicio, fim, passo [graus]

# ----------------------------------------------------------------------------
# Polares (questao 5)
# ----------------------------------------------------------------------------
CL_MIN_PLOT = -0.5
N_POLAR_POINTS = 25
# Arrasto induzido: True usa o plano de Trefftz (CDff, campo distante) e
# False usa a integracao de campo proximo (CDind) do AVL. O campo proximo
# do AVL chega a dar CDind < 0 em CL baixo, entao Trefftz e o padrao.
USE_TREFFTZ_DRAG = True

# ----------------------------------------------------------------------------
# Trimagem da empenagem (questao 3)
# ----------------------------------------------------------------------------
IT_TOL_DEG = 0.01                # tolerancia em |delta_e| para aceitar o i_t
IT_MAX_ITER = 12

# ----------------------------------------------------------------------------
# Propulsao (tabela 9) - dados nao presentes no designTool
# ----------------------------------------------------------------------------
IP_DEG = 0.0                     # incidencia do motor [graus]
