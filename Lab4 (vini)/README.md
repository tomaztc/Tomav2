# Lab 04 - PRJ-23 - Analise aerodinamica no AVL (Tomav2)

Pipeline em estagios. Cada estagio le resultados intermediarios de `out/`,
roda o que precisa e grava novos resultados em `out/`. Nada fica preso na
memoria de um script so: da para **inspecionar e editar qualquer resultado
intermediario** e rodar apenas os estagios seguintes.

## Uso

```bash
cd Lab4
python run.py --list              # lista os estagios e o que ja foi rodado
python run.py --all               # tudo do zero (~4 min)
python run.py 3                   # so o estagio 3
python run.py 5-9                 # estagios 5 a 9
python run.py --sensibilidade     # estudo BODY / NACELLE on-off
python run.py --limpar            # apaga avl_runs/ (logs brutos do AVL)
```

O relatorio final e `RESULTADOS.md`, montado pelo estagio 9 a partir dos JSONs.

## Estagios

| # | modulo | o que faz | saida principal |
|---|--------|-----------|-----------------|
| 1 | `s01_design_point` | roda o `designTool`, monta a Tabela 1, CD0, CG, inercias | `out/01_design_point.json` |
| 2 | `s02_avl_geometry` | escreve `avl/fwd.avl` e `avl/aft.avl` | `out/02_avl_model.json` |
| 3 | `s03_tail_incidence` | i_t que anula delta_e no ponto de projeto | `out/03_tail_incidence.json` |
| 4 | `s04_critical_section` | metodo da secao critica -> CLmax dos 4 casos | `out/04_critical_section.json` |
| 5 | `s05_polars` | polares, CL x alpha, CL x delta_e, ajuste CD(alpha) | `out/05_polars.json` |
| 6 | `s06_neutral_point` | x_np e margens estaticas | `out/06_neutral_point.json` |
| 7 | `s07_derivatives` | Tabelas 6, 7 e 9 (derivadas) | `out/07_tabela9.json` |
| 8 | `s08_figures` | figuras | `figs/*.png`, `figs/trefftz_*.ps` |
| 9 | `s09_report` | monta o relatorio | `RESULTADOS.md` |

## Onde mexer

**`lab4/config.py`** concentra tudo que nao vem do `designTool`:

- `WING_TWIST_TIP_DEG` - torcao (washout) da asa. O `designTool` nao define
  torcao; o valor adotado (-3 deg) muda bastante o estol e o CLmax.
- `CLMAX_AIRFOIL_ROOT` / `_TIP` - cl_max do perfil no metodo da secao critica.
  Com `None`, e lido do topo da polar XFOIL do Lab 03.
- `INCLUDE_BODY` / `INCLUDE_NACELLES` - liga/desliga fuselagem e nacelles no
  modelo AVL. Efeito grande em `Cma`, `x_np` e `Cnb`
  (veja `python run.py --sensibilidade`).
- `USE_TREFFTZ_DRAG` - usa `CDvis + CDff` (plano de Trefftz) em vez do
  `CDtot` de campo proximo do AVL, que chega a dar `CDind < 0` em CL baixo.
- `MACH_LOWSPEED`, `CL_MIN_PLOT`, `N_POLAR_POINTS`, `HT_NACA`, `VT_NACA`,
  discretizacao das superficies, `IP_DEG`.

**Forcar um resultado intermediario.** Exemplo: arredondar o i_t para -2.0 deg
no CG traseiro.

```bash
python run.py 1 2 3            # gera out/03_tail_incidence.json
# edite "it" dentro de out/03_tail_incidence.json
python run.py 4-9              # tudo daqui pra frente usa o valor editado
```

O mesmo vale para o CL do ponto de projeto (`out/01_design_point.json` ->
`tabela1.CL`), para o CD0 inserido no `.avl` (`tabela1`/`CD0`), etc.

## Estrutura

```
Lab4/
  run.py               driver
  lab4/                codigo dos estagios
    config.py          <- parametros ajustaveis
    avlrun.py          camada sobre o executavel do AVL
    s01..s09           estagios
    sensibilidade.py   estudo BODY/NACELLE
  avl/                 arquivos de entrada do AVL (gerados pelo estagio 2)
  avl_runs/            logs e saidas brutas do AVL (conferencia manual)
  out/                 resultados intermediarios (JSON + CSV, editaveis)
  figs/                figuras
  RESULTADOS.md        relatorio gerado
```

## Dependencias

- `numpy`, `matplotlib` (ambiente `prj/.venv`)
- executavel do AVL 3.40 em `../../Lab4/AVL_package/avl340`
  (caminho em `lab4/config.py`, `AVL_EXE`)
- pacote `designTool` do proprio repositorio
- perfil e polar do Lab 03 em `../Lab3/airfoil_ajustado/`

## Observacoes sobre o modelo

- Unidades SI em todo o `.avl` (o `b737mod.avl` de referencia esta em pes).
- O `CDp` do cabecalho e o CD0 limpo do `designTool` no ponto de projeto,
  constante em toda a polar.
- Controles na ordem `d1 = aileron`, `d2 = elevator`, `d3 = rudder`;
  variavel de projeto `g1 = it` (menu `DE`).
- O AVL trunca nomes de arquivo em ~80 caracteres: por isso todas as execucoes
  acontecem com `cwd = avl_runs/` e nomes relativos curtos.
- O AVL e linear, entao o alpha de estol do metodo da secao critica e obtido
  exatamente de duas execucoes e depois **verificado** com uma terceira.
