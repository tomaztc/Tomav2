"""Diagrama V-g-n em cruzeiro, conforme PRJ-23-CARGAS-Diagrama V-N.pdf.

Referências (páginas do PDF, contando a capa):
  9, 17, 26: limite negativo de -1 até V_C e reta até zero em V_D;
  15: V_E = V_TAS * sqrt(rho / rho_0);
  19, 21, 24, 26: velocidades e parábolas de estol, V_A = V_S1 * sqrt(n_max);
  22: V_D >= 1.25 V_C no critério apresentado no PDF; neste exercício,
      mantém-se o dado específico M_D = M_C + 0.07 = 0.84;
  35, 37: rho local em mu_g e rho_0 na fórmula de rajada em EAS;
  38: U_de decresce linearmente entre V_C e V_D; Delta_n é quadrático;
  39: envelope combinado é a união dos envelopes de manobra e rajada.

As figuras esquemáticas não substituem essas equações: a página 41 mantém
-1 g até V_D, contrariando as páginas 9 e 17. As parábolas de estol são
calculadas desde a origem. Por convenção gráfica, o contorno destacado é
recortado em V_S1 (estol a +1 g) e V_Sneg (estol a -1 g), com as curvas
completas mantidas como linhas tracejadas de construção.
"""

import matplotlib.pyplot as plt
import numpy as np

from designTool.auxiliary import atmosphere
from designTool.constants import gravity, ft2m

EAS2KEAS = 3600 / 1852  # 1 nó = 1852 m / 3600 s
rho_0 = 1.225  # kg/m³

# Dados fornecidos. V_C e V_D são TAS; o gráfico usa velocidade equivalente.
W = 40000 * gravity  # N
S_ref = 93.5  # m²
c_ref = 3.8  # m
altitude = 35000 * ft2m  # m
CLmax = 1.50
CLmin = -0.80
CL_alpha = 6.10  # rad^-1
Mach_C = 0.77
Mach_D = Mach_C + 0.07  # Dado do exercício confirmado; exceção ao critério da p. 22.
U_de = 33.7 * ft2m  # m/s, rajada em V_C na altitude em estudo
U_de_D = U_de / 2  # Hipótese do PDF: metade da rajada de V_C em V_D.
n_max = 2.5
n_min = -1.0

# Atmosfera e velocidades.
atm = atmosphere(altitude)
a = atm['speed_of_sound']
rho = atm['density']
sigma = rho / rho_0
TAS2EAS = np.sqrt(sigma)
W_S = W / S_ref

V_C = Mach_C * a
V_D = Mach_D * a
V_S1 = np.sqrt(2 * W / (rho * S_ref * CLmax))
V_Sneg = np.sqrt(2 * abs(n_min) * W / (rho * S_ref * abs(CLmin)))
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
mu_g = 2 * W_S / (rho * c_ref * CL_alpha * gravity)
K_g = 0.88 * mu_g / (5.3 + mu_g)
k_rajada = rho_0 * CL_alpha * K_g / (2 * W_S)
k_estol_pos = rho_0 * S_ref * CLmax / (2 * W)
k_estol_neg = rho_0 * S_ref * CLmin / (2 * W)
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
n_comb_pos = np.maximum(n_man_pos, n_raj_pos)
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
plt.title('Diagrama V-g-n em cruzeiro')
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig('Lab5_vgn.png', dpi=200)
print('\nGráfico salvo em Lab5_vgn.png')
plt.show()
