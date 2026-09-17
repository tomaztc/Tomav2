# PRJ-23 Lab 04 - Analise aerodinamica da Tomav2 (AVL)

Resultados gerados automaticamente pelo pipeline em `Lab4/lab4/`. 
Todos os numeros abaixo vem dos arquivos em `Lab4/out/`; editando-os e 
rodando de novo o estagio correspondente, este relatorio se atualiza.


## 1. Arquivos de entrada do AVL

Dois arquivos com a mesma geometria e apenas o `Xref` diferente:

- `avl/fwd.avl` - CG dianteiro, `Xref` = 26.1793 m
- `avl/aft.avl` - CG traseiro, `Xref` = 27.3413 m
- `avl/tomav_wing.dat` - perfil otimizado no Lab 03 (AFILE de todas as secoes da asa)
- `avl/fuse_nondim.dat` - contorno da fuselagem (BFILE)

`CDp` inserido nos dois arquivos = **0.01417** (CD0 limpo calculado pelo `designTool` no ponto de projeto).

Superficies de controle e variavel de projeto:

| indice | nome     | definicao                        |
|--------|----------|----------------------------------|
| d1     | aileron  | 0.65 a 0.97 de b/2, c_a/c = 0.30 |
| d2     | elevator | toda a EH, c_e/c = 0.30          |
| d3     | rudder   | toda a EV, c_r/c = 0.35          |
| g1     | it       | incidencia da EH (menu DE)       |

Hipoteses adicionais (nao definidas pelo `designTool`, em `lab4/config.py`):

- torcao geometrica linear da asa: 0.0 deg na raiz, -3.0 deg na ponta
- empenagens com perfis simetricos NACA 0009 (AVL usa so a linha de camber)
- fuselagem modelada como BODY: **True**; nacelles como superficies anelares: **True**


## 2. Ponto de projeto (Tabela 1)

Condicao: cruzeiro, 50% de combustivel e 100% de carga paga.

| parametro | explicacao                   | valor   | obs.       |
|-----------|------------------------------|---------|------------|
| W0        | peso maximo de decolagem [N] | 2488311 | 253650 kgf |
| W         | peso no ponto de projeto [N] | 2050762 | 209048 kgf |
| h         | altitude [m]                 | 9875.5  | 32400 ft   |
| rho       | densidade [kg/m3]            | 0.41991 |            |
| a         | velocidade do som [m/s]      | 300.045 |            |
| M         | Mach                         | 0.850   |            |
| V         | velocidade [m/s]             | 255.038 | 496 kt     |
| CL        | CL no ponto de projeto       | 0.45506 |            |
| S_ref     | area de referencia [m2]      | 330.00  |            |

Composicao do peso: W = W_vazio (131393 kgf) + W_tripulacao (1053 kgf) + 100% W_carga (32000 kgf) + 50% W_comb (89205 kgf).


## 3. Incidencia da empenagem horizontal

i_t escolhido de forma que a deflexao de profundor necessaria para trimar (Cm = 0) no ponto de projeto seja nula.

| CG        | i_t [deg] | delta_e residual [deg] | alpha [deg] | CL      | Cm        |
|-----------|-----------|------------------------|-------------|---------|-----------|
| dianteiro | -3.4110   | -0.0028                | 3.807       | 0.45506 | -0.000000 |
| traseiro  | -2.1312   | -0.0002                | 3.652       | 0.45506 | -0.000000 |

Plano de Trefftz do AVL: `figs/trefftz_fwd.ps` e `figs/trefftz_aft.ps`.
Equivalente em matplotlib (carga em envergadura): `figs/fig03_spanload.png`.

O CG dianteiro exige i_t mais negativo (-3.41 deg contra -2.13 deg) porque o braco de trimagem e maior e a EH precisa de mais carga para baixo.


## 4. Metodo da secao critica - CLmax de asa limpa

M = 0.20, asa limpa, cl_max do perfil = **1.8841** (polar XFOIL do Lab 03 (airfoil_ajustado), alpha = 19.70 deg).

| caso                      | i_t [deg] | alpha_max [deg] | CLmax  | delta_e [deg] | y/(b/2) do estol |
|---------------------------|-----------|-----------------|--------|---------------|------------------|
| CG dianteiro sem trimagem | -3.411    | 12.91           | 1.2513 | 0.000         | 0.841            |
| CG dianteiro com trimagem | -3.411    | 12.94           | 1.1843 | -9.671        | 0.841            |
| CG traseiro sem trimagem  | -2.131    | 12.90           | 1.2673 | 0.000         | 0.841            |
| CG traseiro com trimagem  | -2.131    | 12.92           | 1.2336 | -4.894        | 0.841            |

Figuras: `figs/fig04_stall_cl_y.png` (cl x y com o limite de cl_max) e `figs/fig04_stall_ccl.png` (carga seccional).


**Discussao das caracteristicas de estol.** O estol comeca em y/(b/2) = 0.84, ou seja, na regiao externa da asa e ja dentro do trecho ocupado pelo aileron (de 0.65 a 0.97 de b/2). 
Isso e o comportamento tipico de asa enflechada (35.0 deg) e muito afilada (taper = 0.17): a combinacao de enflechamento e afilamento concentra a sustentacao seccional na ponta. 
A torcao de 3.0 deg adotada ja alivia parte do problema, mas nao o suficiente para levar o inicio do estol para a raiz. 
Como consequencia, ha risco de perda de eficiencia do aileron e de tendencia a rolamento assimetrico no estol, alem de momento de arfagem de cabrar ("pitch-up") por perda de sustentacao atras do CG. 
Recomendacoes: aumentar o washout, adotar torcao aerodinamica (perfil de ponta com cl_max maior), deslocar o aileron para dentro ou incluir dispositivos de controle de estol (stall strips / vortilons). 
O CLmax limpo obtido (~1.27) tambem e baixo: o dimensionamento de pista depende dos dispositivos hipersustentadores (flap double slotted + slat), que nao entram neste modelo.


## 5. Polares

Todas no Mach do ponto de projeto (M = 0.85). Arrasto = CDvis + CDff (Trefftz).

| configuracao                      | CD no CL de projeto | alpha [deg] | delta_e [deg] | dif. vs designTool |
|-----------------------------------|---------------------|-------------|---------------|--------------------|
| CG dianteiro, sem deflexao        | 0.02243             | 3.807       | 0.000         | +7.4%              |
| CG traseiro, sem deflexao         | 0.02185             | 3.652       | 0.000         | +4.6%              |
| CG dianteiro, Cm = 0              | 0.02246             | 3.807       | -0.003        | +7.5%              |
| CG traseiro, Cm = 0               | 0.02188             | 3.652       | -0.000        | +4.8%              |
| designTool (CD0 + CDind + CDwave) | 0.02088             | -           | -             | 0.0%               |

CL do ponto de projeto = 0.45506. Figura: `figs/fig05_polar.png`.


No caso b (CG traseiro, sem deflexoes) o AVL fica +4.6% em relacao ao `designTool`. A diferenca esta no arrasto induzido: o `designTool` usa CDind = K*CL^2 com fator de Oswald vindo de regressao, enquanto o AVL integra a distribuicao real de circulacao (e = 0.793 no ponto de projeto). Alem disso o AVL nao modela arrasto de onda, que no `designTool` vale CDwave = 0.00017 nesse ponto, e o CDp do AVL e um valor unico fixado no CD0 de cruzeiro (nao varia com CL nem com Reynolds).


As polares terminam no CLmax de cada caso obtido no item 4 e comecam em CL = -0.5.


## 6. Curvas de sustentacao (CL x alpha)

Figura: `figs/fig06_CL_alpha.png`. Pontos de projeto marcados com circulo.

| configuracao               | alpha no ponto de projeto [deg] | CLmax  |
|----------------------------|---------------------------------|--------|
| CG dianteiro, sem deflexao | 3.807                           | 1.2513 |
| CG traseiro, sem deflexao  | 3.652                           | 1.2673 |
| CG dianteiro, Cm = 0       | 3.807                           | 1.1843 |
| CG traseiro, Cm = 0        | 3.652                           | 1.2336 |


## 7. Deflexao de profundor (CL x delta_e)

Figura: `figs/fig07_CL_deltae.png`.

| configuracao               | delta_e no ponto de projeto [deg] | delta_e min [deg] | delta_e max [deg] |
|----------------------------|-----------------------------------|-------------------|-------------------|
| CG dianteiro, sem deflexao | 0.000                             | 0.000             | 0.000             |
| CG traseiro, sem deflexao  | 0.000                             | 0.000             | 0.000             |
| CG dianteiro, Cm = 0       | -0.003                            | -6.204            | 7.707             |
| CG traseiro, Cm = 0        | -0.000                            | -2.904            | 3.225             |

**Discussao.** Com i_t ajustado por CG, a deflexao de profundor no ponto de projeto e nula (por construcao) e o maior valor exigido em toda a faixa CL = -0.5 ate CLmax e |delta_e| = 7.7 deg. 
Isso esta bem dentro do curso tipico de profundor de aeronaves de transporte (+-25 deg), ou seja, **as deflexoes estao em niveis adequados** e ainda sobra autoridade para manobra, rajada e para as condicoes criticas que nao foram simuladas aqui (flape estendido, rotacao de decolagem e trimagem com CG nos extremos em baixa velocidade).


## 8. Ponto neutro e margem estatica

| posicao           | [m do nariz] | [% MAC] |
|-------------------|--------------|---------|
| x_np (AVL)        | 28.2189      | 40.9    |
| x_np (designTool) | 28.6379      | 47.3    |
| x_cg dianteiro    | 26.1793      | 9.7     |
| x_cg traseiro     | 27.3413      | 27.5    |

| CG        | margem estatica (AVL) | margem estatica (designTool) |
|-----------|-----------------------|------------------------------|
| dianteiro | 31.2%                 | 37.6%                        |
| traseiro  | 13.4%                 | 19.8%                        |

A aeronave e estaticamente estavel em arfagem nas duas posicoes de CG (Cma = -1.049 1/rad no CG traseiro). A margem no CG traseiro (13.4%) ainda e alta para um transporte moderno (tipico 5-15%), o que indica que ha espaco para reduzir a EH ou recuar o envelope de CG e ganhar arrasto de trimagem.


## 9. Derivadas de estabilidade e controle (CG traseiro)

Condicao: CG traseiro (x = 27.3413 m), M = 0.85, CL = 0.45506 (alpha = 3.652 deg), i_t = -2.131 deg, delta_e = 0, **sem restricao de trimagem**.

### Tabela 6 - alpha = 0, i_t = 0, todas as deflexoes nulas

| parametro | explicacao        | valor     |
|-----------|-------------------|-----------|
| CL0       | CL para alpha = 0 | -0.009950 |
| CM0       | CM para alpha = 0 | -0.073460 |

### Tabela 7 - ajuste quadratico da polar nao trimada

CD = CD0 + CDa*alpha + CDa2*alpha^2, com alpha em rad, ajustado sobre a polar do item 5.b (CG traseiro, sem deflexoes). RMS do ajuste = 3.18e-05.

| parametro | explicacao                | valor     |
|-----------|---------------------------|-----------|
| CD0       | termo constante           | 0.016817  |
| CDa       | termo linear [1/rad]      | -0.060825 |
| CDa2      | termo quadratico [1/rad2] | 2.193175  |

Figura: `figs/fig05b_CD_alpha.png`.

### Tabela 9 - informacoes para analise de estabilidade e controle

| parametro | explicacao                            | valor       | fonte                             |
|-----------|---------------------------------------|-------------|-----------------------------------|
| S_ref     | area de referencia [m2]               | 330.000000  |                                   |
| c_ref     | corda de referencia [m]               | 6.546547    |                                   |
| b_ref     | envergadura de referencia [m]         | 58.864251   |                                   |
| m         | massa da aeronave [kg]                | 209048      | ponto de projeto                  |
| Ixx       | momento de inercia [kg.m2]            | 12099421    | designTool                        |
| Iyy       | momento de inercia [kg.m2]            | 34044738    | designTool                        |
| Izz       | momento de inercia [kg.m2]            | 44244375    | designTool                        |
| Ixz       | momento de inercia [kg.m2]            | 938023      | designTool                        |
| ip        | incidencia do motor [deg]             | 0.000000    | config.py                         |
| xp        | posicao long. do motor rel. ao CG [m] | -5.241295   | x positivo p/ tras                |
| zp        | posicao vert. do motor rel. ao CG [m] | 3.075000    | z positivo p/ baixo               |
| Tmax      | tracao maxima [N]                     | 374500      | designTool                        |
| V         | velocidade de voo [m/s]               | 255.037937  | ponto de projeto                  |
| h         | altitude de voo [m]                   | 9875.520000 | ponto de projeto                  |
| CL0       | CL para alpha = 0                     | -0.009950   | AVL ft (Tab. 6)                   |
| CLa       | dCL/dalpha [1/rad]                    | 7.821068    | AVL st                            |
| CLq       | dCL/dq [1/rad]                        | 11.307988   | AVL st                            |
| CLit      | dCL/dit [1/rad]                       | 0.950021    | AVL st x 180/pi                   |
| CLde      | dCL/ddelta_e [1/rad]                  | 0.540758    | AVL st x 180/pi                   |
| CD0       | CD para alpha = 0                     | 0.016817    | Tab. 7                            |
| CDa       | termo linear da polar [1/rad]         | -0.060825   | Tab. 7                            |
| CDa2      | termo quadratico da polar [1/rad2]    | 2.193175    | Tab. 7                            |
| CDq       | dCD/dq [1/rad]                        | 0.159740    | diferenca finita                  |
| CDit      | dCD/dit [1/rad]                       | 0.006360    | AVL st x 180/pi                   |
| CDde      | dCD/ddelta_e [1/rad]                  | 0.004011    | AVL st x 180/pi                   |
| CM0       | CM para alpha = 0                     | -0.073460   | AVL ft (Tab. 6)                   |
| CMa       | dCM/dalpha [1/rad]                    | -1.048514   | AVL st                            |
| CMq       | dCM/dq [1/rad]                        | -47.571897  | AVL st                            |
| CMit      | dCM/dit [1/rad]                       | -3.732476   | AVL st x 180/pi                   |
| CMde      | dCM/ddelta_e [1/rad]                  | -2.233905   | AVL st x 180/pi                   |
| CYb       | dCY/dbeta [1/rad]                     | 0.695771    | AVL st, sinal invertido           |
| CYp       | dCY/dp [1/rad]                        | -0.008058   | AVL st, sinal invertido           |
| CYr       | dCY/dr [1/rad]                        | 0.096674    | AVL st, sinal invertido           |
| CYdr      | dCY/ddelta_r [1/rad]                  | -0.255024   | AVL st x 180/pi                   |
| Clb       | dCl/dbeta [1/rad]                     | -0.175192   | AVL st                            |
| Clp       | dCl/dp [1/rad]                        | -0.559880   | AVL sb                            |
| Clr       | dCl/dr [1/rad]                        | 0.120047    | AVL sb                            |
| Clda      | dCl/ddelta_a [1/rad]                  | -0.199447   | AVL sb, sinal invertido, x 180/pi |
| Cldr      | dCl/ddelta_r [1/rad]                  | 0.029851    | AVL sb, sinal invertido, x 180/pi |
| Cnb       | dCn/dbeta [1/rad]                     | -0.097002   | AVL st                            |
| Cnp       | dCn/dp [1/rad]                        | -0.056674   | AVL sb                            |
| Cnr       | dCn/dr [1/rad]                        | -0.175879   | AVL sb                            |
| Cnda      | dCn/ddelta_a [1/rad]                  | -0.013694   | AVL sb, sinal invertido, x 180/pi |
| Cndr      | dCn/ddelta_r [1/rad]                  | -0.114821   | AVL sb, sinal invertido, x 180/pi |

> **Sobre x_p e z_p.** O centro da nacelle esta em x = 22.100 m do nariz e o CG traseiro em x = 27.341 m, ou seja, o motor fica 5.241 m A FRENTE do CG. Na convencao do `designTool` (x positivo para tras) isso da x_p = -5.241 m; se o modelo de MVO usar x positivo para frente, use x_p = +5.241 m. Ja z_p ja esta com o sinal invertido conforme o enunciado (z positivo para baixo), entao z_p = +3.075 m indica motor ABAIXO do CG. Confirme a origem com o professor de MVO antes de alimentar o modelo.


**Leitura rapida.** Cma = -1.049 1/rad (estavel em arfagem) e Clb = -0.175 1/rad (estavel em rolamento / efeito diedro correto). 
Ja Cnb = -0.097 1/rad **no modelo com fuselagem**: negativo, isto e, o modelo indica instabilidade direcional. Isso vem do BODY da fuselagem no AVL, cujo momento desestabilizante e cerca de 1.7x o previsto pela teoria de corpos esbeltos e ~3x a correlacao de Raymer usada no `designTool`. Sem a fuselagem no modelo, o AVL da Cnb positivo. A conclusao pratica e que a EV, dimensionada com Cvt = 0.075 (o minimo admitido pelo grupo), tem pouca margem direcional e merece ser reavaliada com um metodo especifico (DATCOM/Roskam) antes de fechar o projeto. Veja `python run.py --sensibilidade`.


## 10. Sensibilidade do modelo AVL (fuselagem e nacelles)

O BODY da fuselagem no AVL e um modelo de corpo esbelto grosseiro e domina Cma, x_np e Cnb. As nacelles, modeladas como superficies anelares, tambem desestabilizam. A tabela mostra o efeito de liga-los e desliga-los (CG traseiro, ponto de projeto):

| BODY  | NACELLE | Cma    | Cnb     | CYb     | x_np [m] | x_np [% MAC] | SM traseiro |
|-------|---------|--------|---------|---------|----------|--------------|-------------|
| True  | True    | -1.049 | -0.0970 | -0.6958 | 28.219   | 40.9         | 13.4%       |
| True  | False   | -1.421 | -0.0689 | -0.4837 | 28.562   | 46.1         | 18.7%       |
| False | True    | -3.075 | 0.1285  | -0.6404 | 30.298   | 72.7         | 45.2%       |
| False | False   | -3.415 | 0.1576  | -0.4214 | 30.714   | 79.0         | 51.5%       |

Referencia do `designTool`: x_np = 28.638 m (47.3% MAC), SM traseiro = 19.8%.


O modelo com fuselagem e sem nacelles e o que mais se aproxima do `designTool` (46.1% contra 47.3% MAC), o que faz sentido: a correlacao de Raymer usada no `balance.py` inclui a fuselagem mas ignora as nacelles. O caso adotado como referencia neste relatorio (BODY e NACELLE ligados) e o mais completo; sem o BODY o AVL perde toda a contribuicao desestabilizante da fuselagem e o x_np vai para 79% MAC, valor claramente irreal para um transporte.

Os interruptores estao em `lab4/config.py` (`INCLUDE_BODY`, `INCLUDE_NACELLES`).


## 11. Como reproduzir e como mexer nos resultados

```bash
cd Lab4
python run.py --list        # lista os estagios
python run.py --all         # roda tudo do zero (~5 min)
python run.py 5 8 9         # roda so os estagios 5, 8 e 9
python run.py --sensibilidade   # estudo BODY/NACELLE on-off
```

Cada estagio le apenas arquivos de `out/` e grava outros em `out/`. 
Para forcar um valor (por exemplo um i_t arredondado), edite o JSON correspondente e rode so os estagios seguintes.

| estagio | o que faz                      | saida principal          |
|---------|--------------------------------|--------------------------|
| 01      | designTool + ponto de projeto  | 01_design_point.json     |
| 02      | escreve fwd.avl / aft.avl      | 02_avl_model.json        |
| 03      | incidencia da EH               | 03_tail_incidence.json   |
| 04      | metodo da secao critica        | 04_critical_section.json |
| 05      | polares + ajuste CD(alpha)     | 05_polars.json           |
| 06      | ponto neutro / margem estatica | 06_neutral_point.json    |
| 07      | derivadas (Tab. 6, 7, 9)       | 07_tabela9.json          |
| 08      | figuras                        | figs/*.png               |
| 09      | este relatorio                 | RESULTADOS.md            |
