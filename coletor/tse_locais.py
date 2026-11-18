"""Votos de 2024 por local de votação (roda uma vez só; a eleição não muda).

Fonte: dados abertos do TSE (dadosabertos.tse.jus.br)
  - votacao_secao_2024_SP.zip           votos de cada seção eleitoral
  - eleitorado_local_votacao_2024.zip   endereço e bairro de cada local de votação

Uso:
  python coletor/tse_locais.py caminho/votacao_secao_2024_SP.zip caminho/eleitorado_local_votacao_2024.zip

Gera coletor/tse_locais.json só com Serra Negra (município 71331 no TSE), cargo vereador, 1º turno.
"""
import csv
import io
import json
import os
import sys
import zipfile
from collections import Counter, defaultdict

MUN = "71331"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def linhas(caminho_zip):
    with zipfile.ZipFile(caminho_zip) as z:
        nome = next(n for n in z.namelist() if n.endswith(".csv"))
        with z.open(nome) as h:
            yield from csv.DictReader(io.TextIOWrapper(h, encoding="latin-1"), delimiter=";")


def main(secao_zip, local_zip):
    locais = {}
    for r in linhas(local_zip):
        if r["SG_UF"] == "SP" and r["CD_MUNICIPIO"] == MUN and r["NR_TURNO"] == "1":
            k = f'{r["NR_ZONA"]}|{r["NR_LOCAL_VOTACAO"]}'
            locais.setdefault(k, {"nome": r["NM_LOCAL_VOTACAO"].title(), "bairro": r["NM_BAIRRO"].title()})
    votos = defaultdict(Counter)
    for r in linhas(secao_zip):
        if r["CD_MUNICIPIO"] == MUN and r["CD_CARGO"] == "13" and r["NR_TURNO"] == "1":
            votos[r["NM_VOTAVEL"]][f'{r["NR_ZONA"]}|{r["NR_LOCAL_VOTACAO"]}'] += int(r["QT_VOTOS"])
    if len(locais) < 5 or len(votos) < 50:  # Serra Negra é menor que Bragança
        raise SystemExit(f"Dados estranhos: {len(locais)} locais, {len(votos)} votáveis")
    out = {"fonte": "TSE, dados abertos: votacao_secao_2024_SP e eleitorado_local_votacao_2024",
           "locais": locais,
           "votos": {nome: dict(c.most_common()) for nome, c in votos.items()}}
    destino = os.path.join(RAIZ, "coletor", "tse_locais.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(locais)} locais de votação, {len(votos)} votáveis -> {destino}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
