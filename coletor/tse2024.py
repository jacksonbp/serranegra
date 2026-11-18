# -*- coding: utf-8 -*-
"""
Votos de cada candidato a vereador de Serra Negra na eleição de 2024 — resultado oficial do TSE.

Fonte: resultados.tse.jus.br (eleição 619, município 71331 = Serra Negra, cargo 13 = vereador).
Roda uma vez só (o resultado da eleição não muda) e grava coletor/tse2024.json.
O robô diário só lê esse arquivo: nome de urna e total de votos de cada vereador.

Uso: python coletor/tse2024.py
"""
import json, os, urllib.request

URL = "https://resultados.tse.jus.br/oficial/ele2024/619/dados/sp/sp71331-c0013-e000619-u.json"
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tse2024.json")


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "RadarCidadao/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        dados = json.loads(r.read())
    candidatos = []

    def procura(o):
        if isinstance(o, dict):
            if "nm" in o and "vap" in o:
                candidatos.append(o)
            for x in o.values():
                procura(x)
        elif isinstance(o, list):
            for x in o:
                procura(x)
    procura(dados)
    if len(candidatos) < 30:
        raise SystemExit(f"Resposta estranha do TSE: só {len(candidatos)} candidatos")
    out = {"fonte": URL,
           "candidatos": {c["nm"].strip(): {"urna": (c.get("nmu") or "").strip(), "votos": int(c["vap"]), "sit": c.get("st", "")}
                          for c in candidatos}}
    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{len(candidatos)} candidatos a vereador -> {SAIDA}")


if __name__ == "__main__":
    main()
