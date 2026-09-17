"""
Camada fina sobre o executavel do AVL.

Monta a sequencia de comandos do menu OPER, executa e devolve os resultados
ja parseados (forcas totais, derivadas e forcas por faixa).

Todos os logs brutos ficam em avl_runs/ para conferencia manual.
"""

import os
import re
import shutil
import subprocess
import uuid

import numpy as np

from . import config

_NUM = r'[-+]?\d*\.?\d+(?:[EeDd][-+]?\d+)?'


# ---------------------------------------------------------------------------
def _fresh_run_dir():
    """Diretorio de trabalho do AVL.

    O AVL trunca nomes de arquivo em ~80 caracteres, entao rodamos SEMPRE com
    cwd = avl_runs/ e usamos nomes relativos curtos. Os arquivos .avl e .dat
    sao copiados para la a cada execucao (sao pequenos).
    """
    os.makedirs(config.RUN_DIR, exist_ok=True)
    for fname in os.listdir(config.AVL_DIR):
        src = os.path.join(config.AVL_DIR, fname)
        dst = os.path.join(config.RUN_DIR, fname)
        if os.path.isfile(src) and (not os.path.isfile(dst)
                                    or os.path.getmtime(src) > os.path.getmtime(dst)):
            shutil.copy(src, dst)
    return config.RUN_DIR


def _avl(commands, cwd):
    """Executa o AVL alimentando `commands` pelo stdin."""
    exe = os.path.abspath(config.AVL_EXE)
    if not os.path.isfile(exe):
        raise FileNotFoundError('Executavel do AVL nao encontrado: %s' % exe)
    proc = subprocess.run([exe], input=commands, cwd=cwd, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=600)
    return proc.stdout


# ---------------------------------------------------------------------------
def run_case(cg, mach, alpha=None, CL=None, it=0.0,
             elevator=0.0, trim_elevator=False,
             aileron=0.0, rudder=0.0,
             beta=None, pitch_rate=None, roll_rate=None, yaw_rate=None,
             want=('ft',), tag=None):
    """
    Executa um ponto de operacao do AVL.

    cg              : 'fwd' ou 'aft'
    mach            : numero de Mach
    alpha / CL      : escolha UM dos dois (alpha em graus)
    it              : incidencia da EH [graus] (variavel de projeto)
    elevator        : deflexao de profundor imposta [graus]
    trim_elevator   : se True, o profundor e trimado para Cm = 0
    beta            : angulo de derrapagem [graus]
    pitch_rate      : qc/2V   (usado nas diferencas finitas de CDq)
    roll_rate       : pb/2V
    yaw_rate        : rb/2V
    want            : subconjunto de ('ft', 'st', 'sb', 'fs')

    Retorna dict com as chaves pedidas ja parseadas + 'log' (stdout bruto).
    """
    if (alpha is None) == (CL is None):
        raise ValueError('Especifique alpha OU CL (exatamente um).')

    rundir = _fresh_run_dir()
    tag = tag or uuid.uuid4().hex[:8]
    for ext in ('ft', 'st', 'sb', 'fs'):
        f = os.path.join(rundir, tag + '.' + ext)
        if os.path.isfile(f):
            os.remove(f)

    avl_name = {'fwd': 'fwd.avl', 'aft': 'aft.avl'}[cg]

    cmd = []
    cmd.append('load %s' % avl_name)
    cmd.append('oper')
    cmd.append('m')
    cmd.append('mn %.6f' % mach)
    cmd.append('')
    if alpha is not None:
        cmd.append('a a %.6f' % alpha)
    else:
        cmd.append('a c %.6f' % CL)
    cmd.append('d1 d1 %.6f' % aileron)
    if trim_elevator:
        cmd.append('d2 pm 0.0')
    else:
        cmd.append('d2 d2 %.6f' % elevator)
    cmd.append('d3 d3 %.6f' % rudder)
    if beta is not None:
        cmd.append('b b %.6f' % beta)
    if roll_rate is not None:
        cmd.append('r r %.6f' % roll_rate)
    if pitch_rate is not None:
        cmd.append('p p %.6f' % pitch_rate)
    if yaw_rate is not None:
        cmd.append('y y %.6f' % yaw_rate)
    cmd.append('de')
    cmd.append('1 %.6f' % it)
    cmd.append('')
    cmd.append('x')
    for w in want:
        cmd.append(w)
        cmd.append(tag + '.' + w)      # nome relativo curto (limite do AVL)
    cmd.append('')      # sai do OPER
    cmd.append('quit')
    cmd.append('')

    log = _avl('\n'.join(cmd) + '\n', cwd=rundir)

    with open(os.path.join(rundir, tag + '.log'), 'w') as fid:
        fid.write(log)

    out = {'log': log, 'tag': tag, 'files': {}}
    for w in want:
        path = os.path.join(rundir, tag + '.' + w)
        out['files'][w] = path
        if not os.path.isfile(path):
            raise RuntimeError(
                'AVL nao gerou %s. Veja %s.log'
                % (path, os.path.join(rundir, tag)))
        txt = open(path).read()
        if w == 'ft':
            out['ft'] = parse_ft(txt)
        elif w in ('st', 'sb'):
            out[w] = parse_st(txt)
        elif w == 'fs':
            out['fs'] = parse_fs(txt)
    return out


# ---------------------------------------------------------------------------
def parse_ft(txt):
    """Le o bloco de forcas totais (comando FT)."""
    res = {}
    pat = re.compile(r'([A-Za-z][\w\'/]*)\s*=\s*(%s)' % _NUM)
    for line in txt.splitlines():
        for name, val in pat.findall(line):
            res.setdefault(name, float(val.replace('D', 'E')))
    return res


def parse_st(txt):
    """Le o bloco de derivadas (comandos ST ou SB)."""
    res = {}
    pat = re.compile(r'([A-Za-z][\w\']*)\s*=\s*(%s)' % _NUM)
    for line in txt.splitlines():
        for name, val in pat.findall(line):
            res.setdefault(name, float(val.replace('D', 'E')))
    # derivadas no formato  "z' force CL |    CLa =   5.7  CLb =  0.0"
    m = re.search(r'Neutral point\s+Xnp\s*=\s*(%s)' % _NUM, txt)
    if m:
        res['Xnp'] = float(m.group(1))
    return res


def parse_fs(txt):
    """
    Le o arquivo de forcas por faixa (comando FS).

    Colunas do AVL 3.40:
      j  Xle  Yle  Zle  Chord  Area  c_cl  ai  cl_norm  cl  cd  cdv
      cm_c/4  cm_LE  C.P.x/c
    """
    surfaces = {}
    lines = txt.splitlines()
    cur, header_cols = None, None
    for i, line in enumerate(lines):
        m = re.match(r'\s*Surface\s*#\s*\d+\s+(.+?)\s*$', line)
        if m:
            cur = m.group(1).strip()
            surfaces.setdefault(cur, [])
            header_cols = None
            continue
        if cur is None:
            continue
        if re.search(r'\bcl_norm\b', line) or re.search(r'\bc\s*cl\b', line):
            header_cols = line.split()
            continue
        if header_cols is None:
            continue
        toks = line.split()
        if len(toks) >= 15:
            try:
                vals = [float(t) for t in toks]
            except ValueError:
                header_cols = None
                continue
            surfaces[cur].append(vals)
    out = {}
    cols = ['j', 'Xle', 'Yle', 'Zle', 'Chord', 'Area', 'c_cl', 'ai',
            'cl_norm', 'cl', 'cd', 'cdv', 'cm_c4', 'cm_LE', 'CP_x_c']
    for name, rows in surfaces.items():
        if not rows:
            continue
        arr = np.array(rows)
        d = {}
        for k, c in enumerate(cols):
            if k < arr.shape[1]:
                d[c] = arr[:, k]
        out[name] = d
    return out


# ---------------------------------------------------------------------------
def clean_runs():
    if os.path.isdir(config.RUN_DIR):
        shutil.rmtree(config.RUN_DIR)
