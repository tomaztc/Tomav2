#!/usr/bin/env python
"""
Driver do Lab 04 (PRJ-23).

    python run.py --list            lista os estagios
    python run.py --all             roda todos os estagios na ordem
    python run.py 3 4 5             roda apenas os estagios indicados
    python run.py 5-9               roda um intervalo
    python run.py --sensibilidade   estudo BODY/NACELLE on-off
    python run.py --limpar          apaga avl_runs/ (logs brutos do AVL)

Cada estagio le apenas arquivos JSON de out/ e grava outros em out/. Por isso
da para editar um resultado intermediario a mao e rodar so os estagios
seguintes, sem refazer o que ja estava bom.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lab4 import config, util  # noqa: E402

ESTAGIOS = [
    (1, 's01_design_point', 'designTool + ponto de projeto (Tabela 1)'),
    (2, 's02_avl_geometry', 'escreve avl/fwd.avl e avl/aft.avl'),
    (3, 's03_tail_incidence', 'incidencia da EH que anula delta_e'),
    (4, 's04_critical_section', 'metodo da secao critica (CLmax)'),
    (5, 's05_polars', 'polares, CL x alpha, CL x delta_e, ajuste CD(alpha)'),
    (6, 's06_neutral_point', 'ponto neutro e margens estaticas'),
    (7, 's07_derivatives', 'derivadas de estabilidade (Tabelas 6, 7 e 9)'),
    (8, 's08_figures', 'figuras em figs/'),
    (9, 's09_report', 'monta RESULTADOS.md'),
]


def _feito(n):
    if n == 8:
        return (os.path.isdir(config.FIG_DIR)
                and any(f.endswith('.png') for f in os.listdir(config.FIG_DIR)))
    if n == 9:
        return os.path.isfile(os.path.join(config.LAB4_DIR, 'RESULTADOS.md'))
    if not os.path.isdir(config.OUT_DIR):
        return False
    return any(f.startswith('%02d_' % n) for f in os.listdir(config.OUT_DIR))


def listar():
    print('\nEstagios do Lab 04:\n')
    for n, mod, desc in ESTAGIOS:
        print('  %d  [%s]  %-22s %s'
              % (n, 'ok' if _feito(n) else '  ', mod, desc))
    print('\n  Resultados intermediarios em out/ (JSON e CSV editaveis).')
    print('  Parametros ajustaveis em lab4/config.py\n')


def rodar(numeros):
    import importlib
    for n in numeros:
        entry = next((e for e in ESTAGIOS if e[0] == n), None)
        if entry is None:
            raise SystemExit('Estagio %s nao existe (use --list).' % n)
        mod = importlib.import_module('lab4.' + entry[1])
        mod.run()


def parse(args):
    nums = []
    for a in args:
        if '-' in a and not a.startswith('-'):
            i, j = a.split('-')
            nums.extend(range(int(i), int(j) + 1))
        else:
            nums.append(int(a))
    return nums


def main():
    args = sys.argv[1:]
    if not args or '--list' in args or '-l' in args:
        listar()
        return
    if '--limpar' in args:
        from lab4 import avlrun
        avlrun.clean_runs()
        print('avl_runs/ removido.')
        return
    if '--sensibilidade' in args:
        from lab4 import sensibilidade
        sensibilidade.run()
        return
    if '--all' in args or '-a' in args:
        rodar([e[0] for e in ESTAGIOS])
        return
    rodar(parse(args))


if __name__ == '__main__':
    main()
