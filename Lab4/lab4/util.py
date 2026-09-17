"""Utilidades comuns aos estagios do Lab 04."""

import json
import os
import sys

import numpy as np

from . import config


# ---------------------------------------------------------------------------
# designTool
# ---------------------------------------------------------------------------
def import_designtool():
    """Deixa o pacote designTool do repositorio Tomav2 importavel."""
    if config.REPO_DIR not in sys.path:
        sys.path.insert(0, config.REPO_DIR)
    import designTool  # noqa: F401
    return designTool


# ---------------------------------------------------------------------------
# IO de resultados intermediarios
# ---------------------------------------------------------------------------
class _NpEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return super().default(o)


def save(name, data):
    """Grava `data` em out/<name>.json (resultado intermediario editavel)."""
    os.makedirs(config.OUT_DIR, exist_ok=True)
    path = os.path.join(config.OUT_DIR, name + '.json')
    with open(path, 'w') as fid:
        json.dump(data, fid, indent=2, cls=_NpEncoder)
    print('  -> out/%s.json' % name)
    return path


def load(name):
    """Le out/<name>.json. Levanta erro claro se o estagio anterior nao rodou."""
    path = os.path.join(config.OUT_DIR, name + '.json')
    if not os.path.isfile(path):
        raise FileNotFoundError(
            'Arquivo %s nao encontrado. Rode o estagio que o gera antes '
            '(veja `python run.py --list`).' % path)
    with open(path) as fid:
        return json.load(fid)


def exists(name):
    return os.path.isfile(os.path.join(config.OUT_DIR, name + '.json'))


def save_table_csv(name, rows, header):
    """Grava uma tabela em out/<name>.csv para inspecao/edicao rapida."""
    os.makedirs(config.OUT_DIR, exist_ok=True)
    path = os.path.join(config.OUT_DIR, name + '.csv')
    with open(path, 'w') as fid:
        fid.write(','.join(header) + '\n')
        for row in rows:
            fid.write(','.join(
                ('%.6g' % v) if isinstance(v, (int, float, np.floating)) else str(v)
                for v in row) + '\n')
    print('  -> out/%s.csv' % name)
    return path


def banner(text):
    print('\n' + '=' * 72)
    print(text)
    print('=' * 72)
