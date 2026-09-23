# Trimagem longitudinal do Tomav

Ajuste de `avl.py` para torção de -7 graus e alpha aproximadamente zero no CG aft,
com Mach 0.85 e CL 0.4483. A convenção existente foi preservada: **torção =
incidência da ponta menos incidência da raiz** (washout linear).

- Incidência da raiz: **5.9311 graus**.
- Torção ponta menos raiz: **-7.0000 graus**.
- Incidência da ponta: **-1.0689 graus**.
- Incidência da empenagem horizontal: 0 graus.

`aft.avl` e `fwd.avl` foram regenerados com a mesma asa. A otimização e a
verificação de alpha foram feitas em `aft.avl`; não se impôs alpha zero ao CG fwd.

## Condições e restrições

A geometria, a malha, o perfil, as referências e o CDp foram mantidos.
Condições do cabeçalho de `aft.avl`: altitude 9875.52 m (32400 ft), velocidade
255.0379 m/s, densidade 0.41990606 kg/m³, massa 205928.1206 kg e g=9.81 m/s².
Xcg=27.3457 m, Ycg=Zcg=0, Sref=330 m², Cref=6.5465 m, Bref=58.8643 m e CDp=0.01421.

O CL calculado pelo designTool é 0.44826931; a restrição usada no AVL é
**0.4483**, conforme solicitado. Mach é definido explicitamente no menu OPER/M.
Alpha é resolvido para CL=0.4483 e o profundor (D4) é resolvido para Cm=0.
Beta, velocidades angulares, slat, flap, aileron e rudder ficam em zero.
Os incrementos DESIGN iw e it também ficam em zero: o ajuste está incorporado
na geometria gerada, sem incremento oculto de incidência durante a verificação.

## Resultados do AVL

| Caso | Incidência raiz (graus) | Torção (graus) | Alpha (graus) | CL | Cm | Profundor (graus) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original | 5.2170 | -5.0 | 0.12525 | 0.44830 | -0.00000 | -1.54260 |
| Apenas torção alterada | 5.2170 | -7.0 | 0.62722 | 0.44830 | -0.00000 | -0.70505 |
| Ajuste final | 5.9311 | -7.0 | -0.00001 | 0.44830 | -0.00000 | -0.41940 |

Valores conforme a precisão da saída do AVL, incluindo Cm. O critério de
aceitação para o caso final é |alpha| < 0.001 grau, |CL-0.4483| < 0.00001 e
|Cm| < 0.00001 na saída. `aft_trim.ft` contém as forças e `aft_trim.run` contém
o caso salvo pelo AVL. Não se trata de uma análise de modos dinâmicos.

## Reprodução em Linux

Foi utilizado o executável oficial Linux 64-bit distribuído como AVL 3.40b
(o banner informa Version 3.40):

https://web.mit.edu/drela/Public/web/avl/avl3.40_execs/LINUX64/avl

SHA-256: `758a9c634d7bfc266f74f0bc964d66e906563742031ef57d4f3108ebdb9e8cde`.

O executável requer libX11; os gráficos são desativados no arquivo de comandos.
O binário não é versionado neste repositório.

Na raiz do repositório, com NumPy, SciPy e Matplotlib disponíveis:

```sh
python avl.py
cd AVL_package
# Remova as saídas anteriores para evitar perguntas de sobrescrita do AVL.
rm -f validation/aft_trim.ft validation/aft_trim.run
/caminho/para/avl < validation/aft_trim.in > validation/aft_trim.log
```

O resultado é uma trimagem dentro do modelo AVL. Sua correção de compressibilidade
é Prandtl–Glauert e não resolve choques transônicos; para a asa com enflechamento
35.05 graus, Mach perpendicular é aproximadamente 0.696. Essa limitação deve ser
considerada ao interpretar o resultado em Mach 0.85, conforme o manual oficial:
https://web.mit.edu/drela/Public/web/avl/avl_doc.txt
