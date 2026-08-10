from importlib.util import find_spec
if find_spec("matplotlib") is None or find_spec("scipy") is None or find_spec("numpy") is None \
    or find_spec("pandas") is None or find_spec("seaborn") is None or find_spec("pymoo") is None:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib", "scipy", "numpy", "pandas", "seaborn", "pymoo"])

import warnings
import json 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pymoo.core.problem import Problem
from pymoo.operators.sampling.lhs import LHS
from designTool.analyze import analyze
from designTool.standard_airplane import standard_airplane
from designTool.constants import gravity
pd.options.display.float_format = "{:,.3f}".format
np.random.seed(1234)
warnings.simplefilter("error")

def calcular_saidas(airplane: dict, keys_saidas: list[str]) -> dict[str, float]:
    try:
        analyze(airplane)
        saidas = {}
        for key in keys_saidas:
            if key in airplane["thrust_matching"]:
                saidas[key] = airplane["thrust_matching"][key]
            elif key in airplane["balance"]:
                saidas[key] = airplane["balance"][key]
            elif key in airplane["landing_gear"]:
                saidas[key] = airplane["landing_gear"][key]
            else:
                saidas[key] = np.nan
    except RuntimeWarning:
        saidas = {key: np.nan for key in keys_saidas}
    return saidas
    
def sensitivity_table_predefinido(airplane_name: str) -> pd.DataFrame:
    airplane = standard_airplane(airplane_name)
    keys_saidas = ["W0", "W_fuel", "W_empty", "SM_fwd", "SM_aft"]
    perturbacoes = {
        "S_w": 0.02,
        "AR_w": 0.02,
        "sweep_w": 0.02,
        "dihedral_w": np.deg2rad(2), # ABSOLUTA
        "xr_w": 0.02,
        "Cht": 0.02,
        "Mach_cruise": 0.02, # ABSOLUTA
        "range_cruise": 0.02
    }
    sensibilidades = {}
    saidas = calcular_saidas(airplane, keys_saidas)
    
    for key_param, pert in perturbacoes.items():
        param = airplane["inputs"][key_param]
        
        if key_param == "Mach_cruise" or key_param == "dihedral_w":
            param_pert = airplane["inputs"][key_param] + pert
        else:
            param_pert = airplane["inputs"][key_param] * (1+pert)
            
        airplane_pert = standard_airplane(airplane_name)
        airplane_pert["inputs"][key_param] = param_pert
        saidas_pert = calcular_saidas(airplane_pert, keys_saidas)
        
        sensibilidades[key_param] = {}
        for key_saida, saida in saidas.items():
            saida_pert = saidas_pert[key_saida]
            sensibilidades[key_param][key_saida] = \
                ((saida_pert-saida)/saida) / ((param_pert-param)/param)
            
    tabela = pd.DataFrame.from_dict(sensibilidades, orient="index")
    return tabela

def sensitivity_table(airplane_name: str, keys_entradas: list[str], keys_saidas: list[str]) -> pd.DataFrame:
    airplane = standard_airplane(airplane_name)
    sensibilidades = {}
    saidas = calcular_saidas(airplane, keys_saidas)
    
    for key_entrada in keys_entradas:
        param = airplane["inputs"][key_entrada]
        param_pert = airplane["inputs"][key_entrada] * 1.005
        if key_entrada == "delta_xr_w":
            airplane_pert = standard_airplane(airplane_name, delta_xr_w=param_pert)
        else:
            airplane_pert = standard_airplane(airplane_name)
            airplane_pert["inputs"][key_entrada] = param_pert
        saidas_pert = calcular_saidas(airplane_pert, keys_saidas)
        
        sensibilidades[key_entrada] = {}
        for key_saida, saida in saidas.items():
            saida_pert = saidas_pert[key_saida]
            sensibilidades[key_entrada][key_saida] = \
                ((saida_pert-saida)/saida) / ((param_pert-param)/param)
            
    tabela = pd.DataFrame.from_dict(sensibilidades, orient="index")
    return tabela

def sensitivity_table_predefinido_latex(df: pd.DataFrame) -> str:
    row_headers = {
        "S_w": r"$S_w$",
        "AR_w": r"$AR_w$",
        "sweep_w": r"$\Lambda_w$",
        "dihedral_w": r"$\delta_w$",
        "xr_w": r"$x_{r,w}$",
        "Cht": r"$C_{h,t}$",
        "Mach_cruise": r"$M$",
        "range_cruise": r"$R$",
    }

    lines = [
        r"\begin{tabular}{l|ccccc}",
        r"Input & $\dfrac{\Delta W_0/W_0^{*}}{\Delta(\cdot)/(\cdot)^{*}}$ & $\dfrac{\Delta W_f/W_f^{*}}{\Delta(\cdot)/(\cdot)^{*}}$ & $\dfrac{\Delta W_e/W_e^{*}}{\Delta(\cdot)/(\cdot)^{*}}$ & $\dfrac{\Delta SM_{fwd}/SM_{fwd}^{*}}{\Delta(\cdot)/(\cdot)^{*}}$ & $\dfrac{\Delta SM_{aft}/SM_{aft}^{*}}{\Delta(\cdot)/(\cdot)^{*}}$ \\",
        r"\hline",
    ]

    for index, row in df.iterrows():
        values = [rf"${value:.3f}$" if pd.notna(value) else r"$\cdots$" for value in row]
        lines.append(row_headers[index] + " & " + " & ".join(values) + r" \\")

    lines.append(r"\end{tabular}")
    return "\n".join(lines)

def sensitivity_table_latex(df: pd.DataFrame) -> str:
    def esc(s):
        return s.replace("_", r"\_")
    
    lines = [
        r"\begin{tabular}{l|" + "c" * len(df.columns) + "}",
        "Input & " + " & ".join(esc(col) for col in df.columns) +
        r" \\",
        r"\hline",
    ]

    for index, row in df.iterrows():
        values = [rf"${value:.3f}$" if pd.notna(value) else r"$\cdots$" for value in row]
        lines.append(f"{esc(index)} & " + " & ".join(values) + r" \\")

    lines.append(r"\end{tabular}")
    return "\n".join(lines)

def corrdot(*args, **kwargs):
    corr_r = args[0].corr(args[1], 'pearson')
    corr_text = f"{corr_r:2.2f}".replace("0.", ".")
    ax = plt.gca()
    ax.set_axis_off()
    marker_size = abs(corr_r) * 3000
    ax.scatter([.5], [.5], marker_size, [corr_r], alpha=0.6, cmap="coolwarm",
               vmin=-1, vmax=1, transform=ax.transAxes)
    font_size = abs(corr_r) * 16 + 10
    ax.annotate(corr_text, [.5, .5,],  xycoords="axes fraction",
                ha='center', va='center', fontsize=font_size)
    
def correlation_plot(airplane_name: str, n_samples: int) -> None:
    airplane = standard_airplane(airplane_name)
    keys_saidas = ["W0", "W_fuel", "SM_aft"]
    S_w = airplane["inputs"]["S_w"]
    xr_w = airplane["inputs"]["xr_w"]
    bounds = {
        "S_w": (0.9*S_w, 1.1*S_w),
        "AR_w": (6, 14),
        "sweep_w": (np.deg2rad(10), np.deg2rad(40)),
        "dihedral_w": (np.deg2rad(0), np.deg2rad(5)),
        "xr_w": (0.9*xr_w, 1.1*xr_w)
    }
    keys_entradas = bounds.keys()
    n_entradas = len(keys_entradas)
    lb = [bounds[key][0] for key in keys_entradas]
    ub = [bounds[key][1] for key in keys_entradas]
    problem = Problem(n_var=n_entradas, xl=lb, xu=ub)
    sampler = LHS()
    
    X = sampler(problem, n_samples).get("X")
    X = {key_entrada: X[:,j] for j, key_entrada in enumerate(keys_entradas) }
    Y = {key_saida: np.zeros(n_samples) for key_saida in keys_saidas}
    for i in range(n_samples):
        airplane_sample = standard_airplane(airplane_name)
        entradas = {key_entrada: X[key_entrada][i] for key_entrada in keys_entradas}
        for key_entrada in keys_entradas:
            airplane_sample["inputs"][key_entrada] = entradas[key_entrada]
            
        saidas = calcular_saidas(airplane_sample, keys_saidas)
        for key_saida in keys_saidas:
            Y[key_saida][i] = saidas[key_saida]

    labels_fatores = {
        "S_w": ("$S_w$ [m²]", 1),
        "AR_w": ("$AR_w$", 1),
        "sweep_w": ("$\\Lambda_w$ [°]", 180/np.pi),
        "dihedral_w": ("$\\delta_w$ [°]", 180/np.pi),
        "xr_w": ("$x_{r,w}$ [m]", 1),
        "W0": ("$W_0$ [ton]", 1/1000/gravity),
        "W_fuel": ("$W_{fuel}$ [ton]", 1/1000/gravity),
        "SM_aft": ("$SM_{aft}$ [%]", 100)
    }
    dados = {**X, **Y}
    dados = {labels_fatores[key][0]: dados[key]*labels_fatores[key][1] for key in dados}
    df = pd.DataFrame(dados)
    sns.set_theme(style="whitegrid", context="notebook")
    grid = sns.PairGrid(df, diag_sharey=False, height=1.25, aspect=1.2)
    grid.map_lower(
        sns.regplot,
        lowess=True,
        scatter_kws={"s": 8},
        line_kws={"color": "black"},
    )
    grid.map_diag(sns.histplot)
    grid.map_upper(corrdot)
    grid.figure.set_dpi(90)
    
    for ax, xlabel in zip(grid.axes[-1, :], df.columns):
        ax.set_xlabel(xlabel)
        ax.xaxis.set_label_coords(0.5, -0.30)
        ax.tick_params(axis="x", labelbottom=True)

    grid.figure.align_ylabels(grid.axes[:, 0])
    grid.figure.tight_layout()
    grid.figure.suptitle(
        f"Correlation Plot - Tomav ({n_samples} amostras LHS)",
        fontsize=16,
        y=0.99,
    )
    plt.show(block=False)

titulos = ["=== 2.1 Relative Sensitivity - Default Aircraft ===",
           "\n=== 2.2 Relative Sensitivity - Team Aircraft ==="]
for airplane_name, titulo in zip(["fokker100", "Tomav"], titulos):
    print(titulo)
    tabela = sensitivity_table_predefinido(airplane_name)
    print(tabela)
    print("\n=== LATEX ===")
    print(sensitivity_table_predefinido_latex(tabela))

print("\n=== 2.3 Correlation Chart - Team Aircraft ===")
correlation_plot("Tomav", 40)
correlation_plot("Tomav", 400)

print("\n=== 2.4 Getting ready for the Optimization - Team Aircraft ===")
entradas = [
    "delta_xr_w", # variação na posição da asa
    "S_w",
    "sweep_w",
    "AR_w",
    "taper_w",
    "tcr_w",
    "tct_w",
    "c_flap_c_wing",
    "b_flap_b_wing",
    "c_slat_c_wing",
    "b_slat_b_wing",
    "Cht",
    "AR_h",
    "sweep_h",
    "taper_h",
    "tcr_h",
    "tct_h",
    "Cvt",
    "AR_v",
    "sweep_v",
    "taper_v",
    "tcr_v",
    "tct_v",
]
saidas = [
    "W0",
    "W_fuel",
    "deltaS_wlan",
    "SM_fwd",
    "SM_aft",
    "CLv",
    "frac_nlg_fwd",
    "frac_nlg_aft",
    "alpha_tipback",
    "alpha_tailstrike",
    "phi_overturn",
    # "b_tank_b_w", isso é uma entrada
]
tabela = sensitivity_table("Tomav", entradas, saidas)
print(tabela)
print("\n=== LATEX ===")
for metade in (tabela.iloc[:, :6], tabela.iloc[:, 6:]):
    print(sensitivity_table_latex(metade))
    print("\n")

print("Maiores sensibilidades:")
for saida in saidas:
    top3 = abs(tabela[saida]).nlargest(3)
    print(f"{saida}:")
    for i, (entrada, sens) in enumerate(top3.items()):
        print(f"  {i+1}. {entrada} -> {sens:.1%}")
        
print("\n=== Salvando avião ===")
with open("tomav.json", "w") as f:
    json.dump(standard_airplane("Tomav"), f, indent=4)
print("\nDicionário do avião salvo em tomav.json.")
plt.show()