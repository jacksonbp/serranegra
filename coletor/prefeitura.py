# -*- coding: utf-8 -*-
"""
Radar da Prefeitura: dinheiro que entra e que sai da Prefeitura de Serra Negra.

Fonte: TCE-SP, Portal da Transparência Municipal (dados que a própria Prefeitura envia ao Tribunal de Contas).
  https://transparencia.tce.sp.gov.br/api/json/despesas/serra-negra/<ano>/<mes>
  https://transparencia.tce.sp.gov.br/api/json/receitas/serra-negra/<ano>/<mes>

Cada mês é resumido e guardado em coletor/cache_tce.json. Meses antigos não são baixados de novo;
os últimos 4 meses disponíveis são baixados todo dia, porque a Prefeitura ainda pode corrigir.
Gera site/prefeitura.js (window.PF). Se o TCE estiver fora do ar, usa o que já está guardado.

Uso: python coletor/prefeitura.py
"""
import json, os, re, sys, time, unicodedata, urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RAIZ, "coletor", "cache_tce.json")
SAIDA = os.path.join(RAIZ, "site", "prefeitura.js")
URL = "https://transparencia.tce.sp.gov.br/api/json/{}/serra-negra/{}/{}"
# Pagamentos da Prefeitura para ela mesma (folha e repasses internos): aparecem à parte, não como fornecedor.
PROPRIA = re.compile(r"PREFEITURA MUNICIPAL (?:DA ESTANCIA HIDROMINERAL )?DE SERRA NEGRA|MUNICIPIO DE SERRA NEGRA")
ANOS = [2025, 2026, 2027, 2028]          # mandato atual
REBAIXAR = 4                             # últimos meses baixados de novo todo dia
PAUSA = 1.5
BRT = timezone(timedelta(hours=-3))


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def baixar(tipo, ano, mes):
    req = urllib.request.Request(URL.format(tipo, ano, mes), headers={"User-Agent": "RadarCidadao/1.0"})
    for tent in range(3):
        try:
            time.sleep(PAUSA)
            return json.loads(urllib.request.urlopen(req, timeout=180).read())
        except Exception as erro:
            if tent == 2:
                raise
            print(f"  tentando de novo {tipo} {mes}/{ano}: {erro}")
            time.sleep(10)


def valor(s):
    return float(str(s).replace(".", "").replace(",", ".") or 0)


# grupos de receita, em linguagem simples (o primeiro que bater vale)
GRUPOS = [
    ("fundeb", "FUNDEB (dinheiro da educação)"),
    ("propriedade predial", "IPTU"),
    ("servicos de qualquer natureza", "ISS (imposto das empresas de serviço)"),
    ("impostos sobre servicos", "ISS (imposto das empresas de serviço)"),
    ("circulacao de mercadorias", "ICMS (parte do Estado)"),
    ("icms", "ICMS (parte do Estado)"),
    ("fundo de participacao dos municipios", "FPM (parte do governo federal)"),
    ("veiculos automotores", "IPVA (parte do Estado)"),
    ("cota-parte do ipva", "IPVA (parte do Estado)"),
    ("cota-parte do ipi", "Outros repasses do Estado"),
    ("petroleo", "Royalties (petróleo e minérios)"),
    ("recursos minerais", "Royalties (petróleo e minérios)"),
    ("multa", "Multas"),
    ("transmissao", "ITBI (venda de imóveis)"),
    ("produto da arrecadacao do imposto de renda", "Imposto de renda retido"),
    ("imposto sobre a renda", "Imposto de renda retido"),
    ("sus", "Saúde (repasses do SUS)"),
    ("saude", "Saúde (repasses do SUS)"),
    ("iluminacao publica", "Taxa de iluminação pública"),
    ("taxa", "Outras taxas"),
    ("remuneracao de depositos", "Rendimento de aplicações"),
    ("aplicacao financeira", "Rendimento de aplicações"),
    ("divida ativa", "Dívida ativa recebida"),
    ("educacao", "Outros repasses da educação"),
    ("convenio", "Convênios"),
    ("transferencia", "Outras transferências"),
]


def grupo(alinea):
    a = sem_acento(alinea)
    for chave, nome in GRUPOS:
        if chave in a:
            return nome
    return "Outras receitas"


def resumir(desp, rec):
    """Resume um mês. Só guarda totais; pessoas físicas entram só como soma (sem nome)."""
    m = {"pago": 0.0, "emp": 0.0, "cam": 0.0, "rec": 0.0, "pf": 0.0, "npf": 0, "forn": {}, "grp": defaultdict(float)}
    for x in desp:
        ev = sem_acento(x.get("evento", ""))
        v = valor(x.get("vl_despesa", 0))
        camara = "camara" in sem_acento(x.get("orgao", ""))
        if ev == "valor pago":
            if camara:
                m["cam"] += v
                continue
            m["pago"] += v
            ident = x.get("id_fornecedor", "")
            if ident.startswith("CNPJ"):
                doc = re.sub(r"\D", "", ident)[-14:]
                f = m["forn"].setdefault(doc, [x.get("nm_fornecedor", "").strip(), 0.0, 0])
                f[1] += v; f[2] += 1
            else:
                m["pf"] += v; m["npf"] += 1
        elif not camara and ev in ("empenhado", "reforco"):
            m["emp"] += v
        elif not camara and ev == "anulacao":
            m["emp"] -= v
    for x in rec:
        v = valor(x.get("vl_arrecadacao", 0))
        m["rec"] += v
        m["grp"][grupo(x.get("ds_alinea", ""))] += v
    for k in ("pago", "emp", "cam", "rec", "pf"):
        m[k] = round(m[k], 2)
    m["grp"] = {k: round(v, 2) for k, v in m["grp"].items()}
    m["forn"] = {k: [n, round(v, 2), q] for k, (n, v, q) in m["forn"].items()}
    return m


def main():
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    hoje = datetime.now(BRT)
    pendentes = [(a, mm) for a in ANOS for mm in range(1, 13) if (a, mm) <= (hoje.year, hoje.month)]
    disponiveis = sorted(k for k in cache)
    recentes = set(disponiveis[-REBAIXAR:])
    erros = 0
    for a, mm in pendentes:
        k = f"{a}-{mm:02d}"
        if k in cache and k not in recentes:
            continue
        try:
            desp = baixar("despesas", a, mm)
            if not desp:
                print(f"{k}: ainda sem dados no TCE")
                break                      # meses seguintes também não têm
            rec = baixar("receitas", a, mm)
        except Exception as erro:
            print(f"{k}: TCE não respondeu ({erro}); fica o que já estava guardado")
            erros += 1
            break
        m = resumir(desp, rec)
        if m["pago"] <= 0 or m["rec"] <= 0:
            print(f"{k}: dados incompletos (pago {m['pago']}, receita {m['rec']}); não guardei")
            break
        cache[k] = m
        print(f"{k}: recebeu R$ {m['rec']/1e6:.1f} mi, pagou R$ {m['pago']/1e6:.1f} mi, {len(m['forn'])} empresas")
    if not cache:
        sys.exit("Nenhum dado da Prefeitura disponível.")
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    # ---- resumo para o site
    meses = sorted(cache)
    anos = {}
    for k in meses:
        a = k[:4]; m = cache[k]
        y = anos.setdefault(a, {"rec": 0, "pago": 0, "emp": 0, "cam": 0, "pf": 0, "npf": 0, "grp": defaultdict(float), "forn": {}, "n": 0})
        y["n"] += 1
        for c in ("rec", "pago", "emp", "cam", "pf", "npf"):
            y[c] += m[c]
        for g, v in m["grp"].items():
            y["grp"][g] += v
        for doc, (nome, v, q) in m["forn"].items():
            f = y["forn"].setdefault(doc, [nome, 0, 0]); f[1] += v; f[2] += q
    out = {"fonte": "TCE-SP, Portal da Transparência Municipal", "ger": hoje.strftime("%Y-%m-%dT%H:%M"),
           "ult": meses[-1], "meses": [[k, round(cache[k]["rec"]), round(cache[k]["pago"]), round(cache[k]["cam"])] for k in meses],
           "anos": {}}
    for a, y in anos.items():
        propria = {d: f for d, f in y["forn"].items() if PROPRIA.search(sem_acento(f[0]).upper())}
        top = sorted(((d, f) for d, f in y["forn"].items() if d not in propria), key=lambda kv: -kv[1][1])
        out["anos"][a] = {
            "n": y["n"], "rec": round(y["rec"]), "pago": round(y["pago"]), "emp": round(y["emp"]), "cam": round(y["cam"]),
            "pf": round(y["pf"]), "npf": y["npf"], "nforn": len(top), "prop": round(sum(f[1] for f in propria.values())),
            "grp": sorted([[g, round(v)] for g, v in y["grp"].items() if v > 0], key=lambda x: -x[1]),
            "top": [[doc, nome, round(v), q] for doc, (nome, v, q) in top[:25]],
            "top10": round(sum(v for _, (_, v, _) in top[:10])), "forn_tot": round(sum(v for _, (_, v, _) in top)),
        }
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write("window.PF=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"Prefeitura: {len(meses)} meses, último {meses[-1]} -> {SAIDA}" + (" (com falha no TCE)" if erros else ""))


if __name__ == "__main__":
    main()
