# -*- coding: utf-8 -*-
"""
Gera as páginas do site Radar Serra Negra a partir de um modelo único (mesmo topo, menu e rodapé).

Páginas: / (Início), /vereadores/, /vereador/<nome>/ (uma por vereador), /bairros/, /propostas/,
/sessoes/, /prefeitura/ (só se site/prefeitura.js existir), /sobre/ e /404.html.
Se a biblioteca Pillow estiver instalada, também cria a imagem de prévia do site (capa.jpg)
e a de cada vereador (card.jpg), usadas quando alguém compartilha o link no WhatsApp.

Uso: python coletor/paginas.py     (o robô diário roda depois de coletar.py)
"""
import html, json, os, re, shutil, unicodedata

from config_site import BASE, CONTATO, DOMINIO, ENDERECO_SITE, GOATCOUNTER, URL_SITE

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(RAIZ, "site")
CAMINHO_DADOS = os.path.join(SITE, "dados.js")
if not os.path.exists(CAMINHO_DADOS):
    raise SystemExit("Ainda não há dados: rode antes  python coletor/coletar.py  (precisa do token em CLAN_TOKEN).")
D = json.loads(open(CAMINHO_DADOS, encoding="utf-8").read()[len("window.RB="):].rstrip().rstrip(";"))
V = D["v"]
e = lambda s: html.escape(str(s), quote=True)
nf = lambda n: f"{int(n):,}".replace(",", ".")
brl = lambda n: "R$ " + f"{n:,.2f}".translate(str.maketrans(",.", ".,"))
VER = lambda arq: str(int(os.path.getmtime(os.path.join(SITE, "assets", arq))))
CIDADE = "Serra Negra"
TELEFONE_CAMARA = "(19) 3942-9800"  # rodapé do site oficial cmserranegra.sp.gov.br

# Resolução municipal nº 420/2023 e leis estaduais nº 17.617/2023 e 18.384/2025.
SUBSIDIOS = {
    "vereadores": 10,
    "base": 7900,
    "acrescimo": 0.50,
    "limite": 0.30,
    "faixas": [["2025-01-01", 33006.39], ["2025-02-01", 34774.64]],
    "fim": "2027-01-01",  # mês seguinte à última competência estadual verificada
}
PRESIDENCIA_NOMINAL = SUBSIDIOS["base"] * (1 + SUBSIDIOS["acrescimo"])
TETO_ATUAL = round(SUBSIDIOS["faixas"][-1][1] * SUBSIDIOS["limite"], 2)
TOTAL_MENSAL = SUBSIDIOS["vereadores"] * SUBSIDIOS["base"] + min(PRESIDENCIA_NOMINAL, TETO_ATUAL)


def slug(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


SLUGS = [slug(v["ap"]) for v in V]
if len(set(SLUGS)) != len(SLUGS):
    raise SystemExit("Dois vereadores com o mesmo nome curto: ajuste a geração dos endereços.")

LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="8" fill="#e5322d"/>'
        '<path d="M19 17a21 21 0 000 30M45 17a21 21 0 010 30M10 9a33 33 0 000 46M54 9a33 33 0 010 46" '
        'stroke="currentColor" stroke-width="5" fill="none" stroke-linecap="round"/></svg>')
MARCA = "<span><b>RADAR</b><b>SERRA NEGRA</b></span>"
# A página da Prefeitura só existe depois que coletor/prefeitura.py gerou site/prefeitura.js (dados do TCE-SP).
PF = os.path.join(SITE, "prefeitura.js")
TEM_PF = os.path.exists(PF)
MENU = [("inicio", "/", "Início"), ("vereadores", "/vereadores/", "Vereadores"), ("bairros", "/bairros/", "Seu bairro"),
        ("propostas", "/propostas/", "Propostas"), ("sessoes", "/sessoes/", "Sessões")] \
    + ([("prefeitura", "/prefeitura/", "Prefeitura")] if TEM_PF else []) + [("sobre", "/sobre/", "Sobre")]
TEM_TSE = any(v.get("vot") for v in V)
junta = lambda p: ", ".join(p[:-1]) + " e " + p[-1] if len(p) > 1 else p[0]
FONTES = "dados oficiais " + junta(["da Câmara Municipal"] + (["do TSE"] if TEM_TSE else []) + (["do Tribunal de Contas do Estado (TCE-SP)"] if TEM_PF else []))
FONTES_CURTO = junta(["Câmara Municipal de Serra Negra"] + (["TSE"] if TEM_TSE else []) + (["TCE-SP"] if TEM_PF else []))


def menu_mobile(ativa):
    links = [(h, f'<a href="{BASE}{h}"{" aria-current=page" if k == ativa else ""}>{n}</a>') for k, h, n in MENU]
    diretos = ("/vereadores/", "/bairros/")
    main = "".join(link for h, link in links if h in diretos)
    more = "".join(link for h, link in links if h not in diretos)
    return ('<div class="mobile-nav">' + main + '<details><summary>Menu</summary>'
            + '<div class="mobile-nav-links">' + more + '</div></details></div>')


def dados_inicio(dados):
    campos = ("gerh", "posse", "catot", "bairros")
    resumo = {campo: dados[campo] for campo in campos}
    resumo["subsidios"] = SUBSIDIOS
    resumo["totalPropostas"] = len(dados["items"])
    resumo["pautas"] = dados.get("pautas", [])[:3]
    resumo["v"] = [{campo: v[campo] for campo in ("id", "ap", "foto", "cat") if campo in v} for v in dados["v"]]
    indices = {}
    resumo["items"] = []
    resumo["rep"] = []
    for grupo in dados["rep"][:6]:
        ids = []
        for antigo in grupo["ids"]:
            if antigo not in indices:
                indices[antigo] = len(resumo["items"])
                resumo["items"].append(dados["items"][antigo])
            ids.append(indices[antigo])
        resumo["rep"].append({**grupo, "ids": ids})
    return "window.RB=" + json.dumps(resumo, ensure_ascii=False, separators=(",", ":")) + ";\n"


def contato_html():
    if not CONTATO:
        return ""
    return (f'<li>Achou um erro? Escreva para<br><a href="mailto:{e(CONTATO)}"><b>{e(CONTATO)}</b></a><br>'
            'Conferimos e corrigimos o mais rápido possível, e a correção fica registrada.</li>')


def pagina(ativa, titulo, descricao, url, corpo, init, imagem="/capa.jpg", titulo_og=None, extra_head=""):
    menu = "".join(f'<li><a href="{BASE}{h}"{" aria-current=page" if k == ativa else ""}>{n}</a></li>' for k, h, n in MENU)
    img = imagem if imagem.startswith("http") else URL_SITE + imagem
    noscript = '<noscript><p class="wrap warn" style="margin-top:20px">Este site precisa do JavaScript ligado no navegador para mostrar os dados.</p></noscript>' if init else ""
    arquivo_dados = 'dados-inicio.js' if ativa == 'inicio' else 'dados.js'
    scripts = f'''<script src="{BASE}/{arquivo_dados}?v={D['gerh']}"></script>
<script src="{BASE}/assets/radar.js?v={VER('radar.js')}"></script>
<script>{init}</script>''' if init else ""
    contador = (f'<!-- Contador de visitas (GoatCounter): sem cookies, não identifica ninguém. -->\n'
                f'<script data-goatcounter="{e(GOATCOUNTER)}" async src="https://gc.zgo.at/count.js"></script>\n') if GOATCOUNTER else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Radar Serra Negra">
<meta property="og:title" content="{e(titulo_og or titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:url" content="{URL_SITE}{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#e5322d">
<link rel="canonical" href="{URL_SITE}{url}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='5' fill='%23e5322d'/%3E%3Cpath d='M8 8a11 11 0 000 16M24 8a11 11 0 010 16' stroke='%230f1720' stroke-width='3' fill='none' stroke-linecap='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{BASE}/assets/radar.css?v={VER('radar.css')}">
<link rel="stylesheet" href="{BASE}/assets/mobile-nav.css?v={VER('mobile-nav.css')}">
{extra_head}</head>
<body data-contato="{e(CONTATO)}" data-telefone="{e(TELEFONE_CAMARA)}">
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<header class="nav"><div class="wrap">
  <a class="brand" href="{BASE}/" aria-label="Radar Serra Negra, página inicial">{LOGO}{MARCA}</a>
  <nav aria-label="Menu principal"><ul class="menu">{menu}</ul>{menu_mobile(ativa)}</nav>
</div></header>
<main id="conteudo">
{noscript}
{corpo}
</main>
<footer class="foot2"><div class="wrap">
  <div><a class="brand" href="{BASE}/">{LOGO}{MARCA}</a>
    <p>O que os vereadores de Serra Negra propõem desde a posse, com os {FONTES}. Mesma régua para todos, sem nota nem opinião.</p></div>
  <div><h4>Páginas</h4><ul>{"".join(f'<li><a href="{BASE}{h}">{n}</a></li>' for k, h, n in MENU)}</ul></div>
  <div><h4>Contato</h4><ul>{contato_html()}<li><a href="{BASE}/sobre/">Como contamos os números</a></li><li>Parte do <a href="{DOMINIO}/">Voz das Cidades</a></li></ul></div>
  <p class="fine"><span data-atualizado></span> Este não é um site oficial. Projeto independente, sem ligação com a Câmara, a Prefeitura, candidatos ou partidos. Todos os dados vêm de fontes públicas, citadas em cada página.</p>
</div></footer>
{scripts}
{contador}</body>
</html>
"""


def escreve(caminho, conteudo):
    p = os.path.join(SITE, caminho)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(conteudo)


SEARCH_ICON = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>'


def tile(k, href, titulo, texto, icone):
    return (f'<a class="tile k-{k}" href="{BASE}{href}"><span class="ci">{icone}</span><b>{titulo}</b>'
            f'<span>{texto}</span><span class="go">Abrir →</span></a>')


I = lambda p: f'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{p}</svg>'
IC_USERS = I('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0113 0M16 4.5a3.5 3.5 0 010 7M18 14a6 6 0 013.5 6"/>')
IC_PIN = I('<path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>')
IC_LAW = I('<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>')
IC_CHECK = I('<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>')
IC_CAL = I('<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/>')

LD = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "Radar Serra Negra", "url": URL_SITE + "/", "inLanguage": "pt-BR", "description": "O que os vereadores de Serra Negra propõem desde a posse, com dados oficiais."}, ensure_ascii=False) + "</script>\n"
SEM_VOTOS = ("Os dados abertos da Câmara de Serra Negra não trazem o voto de cada vereador nem a lista de presença nas sessões. "
             "Por isso o Radar mostra só as proposições.")


# ------------------------------------------------------------------ imagens de compartilhamento (precisam do Pillow)
def fontes():
    from PIL import ImageFont

    def fonte(nomes, s):
        for n in nomes:
            for base in ("C:/Windows/Fonts/", "/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/truetype/liberation/"):
                try:
                    return ImageFont.truetype(base + n, s)
                except Exception:
                    pass
        return ImageFont.load_default()
    return (lambda s: fonte(["ariblk.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"], s),
            lambda s: fonte(["segoeuib.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"], s))


def capa_img(destino):
    """Imagem padrão do site (1200x630), só com o nome e o endereço: nenhum número."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    BLACK, BOLD = fontes()
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), (17, 26, 36)); d = ImageDraw.Draw(im)
    cx, cy = 190, 315
    for r, w in ((150, 16), (100, 14)):
        d.arc([cx - r, cy - r, cx + r, cy + r], 120, 240, fill=(255, 255, 255), width=w)
        d.arc([cx - r, cy - r, cx + r, cy + r], -60, 60, fill=(255, 255, 255), width=w)
    d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(229, 50, 45))
    d.text((390, 215), "RADAR", font=BLACK(96), fill=(255, 255, 255))
    d.text((390, 320), "SERRA NEGRA", font=BLACK(96), fill=(255, 143, 139))
    d.text((392, 450), "O que os vereadores propõem, com dados oficiais da Câmara", font=BOLD(30), fill=(220, 226, 232))
    d.text((W - 60, H - 50), ENDERECO_SITE, font=BOLD(28), fill=(255, 143, 139), anchor="rm")
    im.save(destino, "JPEG", quality=86, optimize=True)
    return True


def card_img(v, destino):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    import colorsys
    BLACK, BOLD = fontes()
    W, H = 1200, 630
    i = V.index(v)
    hue = (i * 47 + 200) % 360
    tint = tuple(int(c * 255) for c in colorsys.hls_to_rgb(hue / 360, .94, .85))
    deep = tuple(int(c * 255) for c in colorsys.hls_to_rgb(hue / 360, .26, .55))
    im = Image.new("RGB", (W, H), tint); d = ImageDraw.Draw(im)
    fp = os.path.join(SITE, "fotos", f"{v['foto']}.jpg") if v.get("foto") else ""
    if fp and os.path.exists(fp):
        ph = Image.open(fp).convert("RGB").resize((300, 300), Image.LANCZOS)
        m = Image.new("L", (900, 900), 0); ImageDraw.Draw(m).ellipse([0, 0, 900, 900], fill=255)
        d.ellipse([62, 112, 378, 428], fill=(255, 255, 255))
        im.paste(ph, (70, 120), m.resize((300, 300), Image.LANCZOS))
    nome = v["ap"]; s = 72
    while d.textlength(nome, font=BLACK(s)) > 720 and s > 40:
        s -= 4
    d.text((430, 150), nome, font=BLACK(s), fill=deep)
    if v.get("part"):
        d.text((432, 150 + s + 18), v["part"], font=BOLD(34), fill=(17, 26, 36))
    tot = sum(v["cat"].values())
    kp = [(nf(tot), "propostas"), (nf(v["cat"]["b"]), "pedidos no bairro"), (nf(v["cat"]["l"]), "projetos de lei")]
    for k, (a, b) in enumerate(kp):
        x = 432 + k * 240
        d.rounded_rectangle([x, 330, x + 220, 450], 24, fill=(255, 255, 255))
        d.text((x + 110, 375), a, font=BLACK(50), fill=(17, 26, 36), anchor="mm")
        d.text((x + 110, 425), b, font=BOLD(22), fill=(93, 105, 118), anchor="mm")
    d.rectangle([0, 520, W, H], fill=(17, 26, 36))
    d.text((70, 575), "RADAR SERRA NEGRA", font=BLACK(36), fill=(255, 255, 255), anchor="lm")
    d.text((W - 70, 575), ENDERECO_SITE, font=BOLD(30), fill=(255, 143, 139), anchor="rm")
    im.save(destino, "JPEG", quality=86, optimize=True)
    return True


CAPA = os.path.join(SITE, "capa.jpg")
if not os.path.exists(CAPA):
    capa_img(CAPA)

# ------------------------------------------------------------------ Início
inicio = f"""
<section class="wrap radar-home">
  <div>
    <span class="live"><i></i><span id="livet">Dados da Câmara</span></span>
    <h1 class="logo" aria-label="Radar Serra Negra">{LOGO.replace('currentColor', '#111a24')}{MARCA}</h1>
    <p class="intro">Veja o que os vereadores de Serra Negra propuseram e o que pediram para o seu bairro.</p>
    <form class="search" id="fbq" role="search"><label for="hq" class="eyebrow">O que pediram pelo seu bairro?</label>
      <div class="radar-search-row"><div class="radar-search-field">{SEARCH_ICON}<input id="hq" type="search" list="hq-bairros" placeholder="Digite seu bairro ou sua rua" autocomplete="off"><datalist id="hq-bairros"></datalist></div><button class="btn" type="submit">Buscar</button></div></form>
    <ul class="chips" id="bairros-chips"></ul>
  </div>
  <div>
    <div class="meter radar-salary">
      <p class="t">Estimativa de subsídios de 11 vereadores desde a posse</p>
      <p class="v num" id="tick">{brl(TOTAL_MENSAL)} por mês</p>
      <small>{SUBSIDIOS["vereadores"]} × {brl(SUBSIDIOS["base"])} + presidência de até {brl(TETO_ATUAL)} por mês na referência de 2026</small>
      <a href="{BASE}/sobre/#subsidios">Como calculamos</a>
    </div>
    <div class="stats" id="stats"></div>
    <p class="upd" data-atualizado></p>
  </div>
</section>

<section class="wrap">
  <h2>Explore o Radar</h2>
  <div class="tiles">
    {tile("o", "/vereadores/", f"Os {len(V)} vereadores", "As propostas de cada um desde a posse, com a mesma régua.", IC_USERS)}
    {tile("b", "/bairros/", "Seu bairro", "Tudo o que pediram para a sua rua, e por quem.", IC_PIN)}
    {tile("l", "/propostas/", "Propostas", "Consulte pedidos, homenagens e projetos de lei.", IC_LAW)}
    {tile("c", "/sessoes/", "Sessões", "As pautas das sessões da Câmara, com o link oficial.", IC_CAL)}
  </div>
</section>

<section class="wrap" style="padding-top:26px">
  <ul class="trust">
    <li>{IC_CHECK}<b>Só dados oficiais</b><span>{FONTES_CURTO}</span></li>
    <li>{IC_CHECK}<b>Atualizado todo dia</b><span>Consulta diária à fonte oficial</span></li>
    <li>{IC_CHECK}<b>Mesma régua</b><span>Os {len(V)} vereadores contados do mesmo jeito, sem nota nem opinião</span></li>
    <li>{IC_CHECK}<b>Fonte em cada número</b><span>Cada proposta abre na página da Câmara</span></li>
  </ul>
</section>

<section class="wrap">
  <p class="eyebrow">Um por um</p>
  <h2>Os vereadores</h2>
  <p class="lead">Toque em um rosto para ver tudo o que a pessoa propôs desde a posse.</p>
  <ul class="faces" id="faces"></ul>
</section>

<section class="wrap" id="sessoes-recentes">
  <p class="eyebrow">Na Câmara</p>
  <h2>Últimas sessões</h2>
  <div id="pautas-inicio"></div>
  <p><a href="{BASE}/sessoes/">Ver todas as pautas →</a></p>
</section>

<section class="wrap" id="repetidos">
  <p class="eyebrow">Só aqui</p>
  <h2>O problema que não some</h2>
  <p class="lead">Quando o mesmo pedido volta várias vezes para a mesma rua, é sinal de que o problema continua lá. <a href="{BASE}/bairros/#repetidos">Ver todas as ruas →</a></p>
  <div class="reps" id="reps"></div>
</section>
"""
escreve("dados-inicio.js", dados_inicio(D))
escreve("index.html", pagina("inicio", "Radar Serra Negra",
        "O que os vereadores de Serra Negra propuseram desde a posse: pedidos para os bairros, homenagens e projetos de lei. Só dados oficiais da Câmara, atualizados todo dia.",
        "/", inicio, "Radar.inicio()", titulo_og="Radar Serra Negra: o que os vereadores propõem desde a posse", extra_head=LD))

# ------------------------------------------------------------------ Vereadores
vereadores = f"""
<section class="wrap phead">
  <p class="eyebrow">Um por um</p>
  <h1>Os vereadores de Serra Negra</h1>
  <p class="lead" id="vsub"></p>
  <a class="cmp-cta" href="{BASE}/comparar/"><span class="cmp-ic" aria-hidden="true">⇄</span><span><b>Comparar dois vereadores</b><small>Escolha dois nomes e veja as propostas lado a lado</small></span><span aria-hidden="true">→</span></a>
  <div class="filters">
    <label class="field">Buscar por nome<input id="q" type="search" placeholder="Digite um nome" autocomplete="off"></label>
    <label class="field">Partido<select id="partido"><option value="">Todos</option></select></label>
    <label class="field">Ordenar por<select id="ordem">
      <option value="nome">Nome (A–Z)</option><option value="tot">Mais propostas</option><option value="b">Mais pedidos no bairro</option>
      <option value="c">Mais cobranças</option><option value="l">Mais propostas de lei</option><option value="h">Mais homenagens</option><option value="vot">Mais votos em 2024</option></select></label>
  </div>
  <p class="mute" id="conta" style="font-size:14px;margin:4px 0 0"></p>
  <ul class="legend" aria-label="Legenda das barras coloridas"><li class="k-b"><i></i>Pedidos nos bairros</li><li class="k-c"><i></i>Cobranças</li><li class="k-h"><i></i>Homenagens</li><li class="k-l"><i></i>Propostas de lei</li><li class="k-o"><i></i>Outros</li></ul>
  <div class="vgrid" id="grid"></div>
  <p class="mute" style="font-size:14px;margin-top:16px">{SEM_VOTOS}</p>
</section>
<section class="wrap" id="planilha">
  <div class="dl"><button class="btn gh" id="csv" type="button">Baixar planilha com os {len(V)} vereadores</button>
    <span class="mute">Arquivo CSV, abre no Excel ou no Google Planilhas. Use à vontade, citando a fonte.</span></div>
</section>
"""
escreve("vereadores/index.html", pagina("vereadores", "Vereadores · Radar Serra Negra",
        f"Os {len(V)} vereadores de Serra Negra: as propostas de cada um desde a posse, com dados oficiais da Câmara.",
        "/vereadores/", vereadores, "Radar.vereadores()"))

# ------------------------------------------------------------------ Página de cada vereador
VOTO24 = """<section class="wrap" id="s-voto24">
  <p class="eyebrow">Eleição de 2024</p><h2>Os locais onde teve mais votos</h2>
  <p class="lead" id="locc"></p>
  <div class="lcards" id="loc"></div>
  <p class="mute small">O local de votação é onde o eleitor vota, que nem sempre é onde mora. Os nomes de bairro da Justiça Eleitoral e da Câmara às vezes não batem; por isso alguns aparecem como “sem pedidos com esse nome”.</p>
</section>"""
for v, s in zip(V, SLUGS):
    tot = sum(v["cat"].values())
    desc = f"{v['ap']}{' (' + v['part'] + ')' if v.get('part') else ''} desde a posse: {nf(tot)} propostas, entre pedidos para os bairros, cobranças, homenagens e projetos de lei. Dados oficiais da Câmara de Serra Negra."
    foto = f'<img class="big-ph" src="{BASE}/fotos/{e(v["foto"])}.jpg" alt="Foto de {e(v["ap"])}">' if v.get("foto") else ""
    tags = (f'<span class="pill">{e(v["part"])}</span>' if v.get("part") else "") \
        + (f'<span class="pill r">{e(v["mesa"])}</span>' if v.get("mesa") else "") \
        + (f'<span class="pill r">{nf(v["vot"])} votos em 2024</span>' if v.get("vot") else "")
    contato = (f'<a class="btn ficha-compare" href="{BASE}/comparar/?a={e(v["id"])}">Comparar vereadores</a>'
               + (f'<a class="btn lt" href="{e(v["url"])}" target="_blank" rel="noopener">Página oficial na Câmara ↗</a>' if v.get("url") else "")
               + (f'<a class="btn lt" href="mailto:{e(v["email"])}">{e(v["email"])}</a>' if v.get("email") else "")
               + '<a class="btn wa" id="wa" href="#" target="_blank" rel="noopener">Compartilhar no WhatsApp</a><button class="btn gh" type="button" id="cp">Copiar link</button>')
    civil = f'<p class="civil">{e(v["nome"])}</p>' if v.get("nome") and v["nome"] != v["ap"] else ""
    corpo = f"""
<section class="wrap phead" style="padding-top:20px">
  <p class="crumbs"><a href="{BASE}/">Início</a> › <a href="{BASE}/vereadores/">Vereadores</a> › {e(v['ap'])}</p>
  <div class="prof">{foto}<div><h1>{e(v['ap'])}</h1>{civil}<div class="tags">{tags}</div><div class="contato">{contato}</div></div></div>
  <nav class="subnav ficha-nav" aria-label="Nesta página"><a href="#s-propostas">Propostas</a><a href="#s-onde">Onde pediu</a>{'<a href="#s-voto24">Onde foi votado</a>' if v.get("loc") else ""}<a href="#s-ruas">Ruas que voltam</a></nav>
  <div class="kpis" id="kpis"></div>
</section>
<section class="wrap" id="s-onde">
  <div class="cols">
    <div class="box"><h3>O que propôs</h3><div id="picks"></div></div>
    <div class="box"><h3>Onde pediu</h3><div id="onde"></div></div>
  </div>
</section>
{VOTO24 if v.get("loc") else ""}
<section class="wrap" id="s-propostas">
  <p class="eyebrow">Proposta por proposta</p><h2>Tudo o que apresentou desde a posse</h2>
  <ul class="tabs chips" id="tabs"></ul><div id="lista"></div>
</section>
<section class="wrap" id="s-ruas">
  <p class="eyebrow">Ruas que voltam</p><h2>Problemas que não somem</h2>
  <p class="lead" id="reps-n"></p><div class="reps" id="reps-v"></div>
  <p class="mute small">{SEM_VOTOS}</p>
  <nav class="pn" id="pn" aria-label="Outros vereadores"></nav>
</section>
"""
    img = f"/vereador/{s}/card.jpg"
    os.makedirs(os.path.join(SITE, "vereador", s), exist_ok=True)
    if not card_img(v, os.path.join(SITE, "vereador", s, "card.jpg")):
        img = "/capa.jpg"
    escreve(f"vereador/{s}/index.html", pagina("vereadores", f"{v['ap']} · Radar Serra Negra", desc, f"/vereador/{s}/", corpo,
            f"Radar.vereador({json.dumps(v['id'])})", imagem=img, titulo_og=f"{v['ap']}: o que propôs desde a posse"))

# ------------------------------------------------------------------ Comparar
comparar = f"""
<section class="wrap phead">
  <p class="eyebrow">Lado a lado</p>
  <h1>Comparar vereadores</h1>
  <p class="lead">Escolha dois vereadores em exercício. Os números são contados do mesmo jeito para todos e vêm dos dados oficiais da Câmara. Nas barras, quem tem o número maior fica com a barra cheia.</p>
  <div class="vs" id="vs"></div>
  <div class="contato"><button class="btn gh" type="button" id="cmp-copy">Copiar link desta comparação</button><span role="status" id="cmp-copy-status"></span></div>
  <div id="cmp"></div>
  <p class="mute" style="font-size:14px;margin-top:18px">Desde a posse, em 1º de janeiro de 2025. {SEM_VOTOS} Como cada número é contado: <a href="{BASE}/sobre/">Sobre</a>.</p>
</section>
"""
escreve("comparar/index.html", pagina("vereadores", "Comparar vereadores · Radar Serra Negra",
        "Compare dois vereadores de Serra Negra lado a lado: as propostas de cada um desde a posse, com dados oficiais da Câmara.",
        "/comparar/", comparar, "Radar.comparar()"))

# páginas de quem não está mais na lista (ou mudou de nome) saem do site
for pasta in os.listdir(os.path.join(SITE, "vereador")):
    if pasta not in SLUGS and os.path.isdir(os.path.join(SITE, "vereador", pasta)):
        shutil.rmtree(os.path.join(SITE, "vereador", pasta))

# ------------------------------------------------------------------ Seu bairro
bairros = f"""
<section class="wrap phead" id="busca">
  <p class="eyebrow">Na sua rua</p>
  <h1>O que pediram pelo seu bairro?</h1>
  <p class="lead">Digite o bairro ou a rua. Sem nada digitado, você vê a cidade inteira.</p>
  <div class="search">{SEARCH_ICON}<input id="bq" type="search" list="bl" placeholder="Digite seu bairro ou sua rua" autocomplete="off" aria-label="Bairro ou rua"><datalist id="bl"></datalist></div>
  <ul class="chips" id="chips"></ul>
  <p class="mute" style="font-size:14px">A Câmara não informa o bairro de cada pedido. O Radar lê o bairro e a rua no próprio texto oficial; quando o texto não traz esses nomes, o pedido aparece só na busca por palavra.</p>
  <div id="bres"></div>
</section>
<section class="wrap" id="repetidos">
  <p class="eyebrow">Só aqui</p>
  <h2>O problema que não some</h2>
  <p class="lead">Quando o mesmo pedido volta várias vezes para a mesma rua, é sinal de que o problema continua lá. O site da Câmara mostra os pedidos um por um; aqui eles são cruzados.</p>
  <p class="warn"><b>Atenção:</b> pedido repetido não prova que a Prefeitura ignorou. Às vezes o serviço foi feito e o problema voltou, ou o pedido é sobre um trecho diferente da mesma rua.</p>
  <div class="reps" id="reps"></div>
</section>
"""
escreve("bairros/index.html", pagina("bairros", "Seu bairro · Radar Serra Negra",
        "Busque seu bairro ou sua rua e veja tudo o que os vereadores de Serra Negra pediram para lá, e por quem.",
        "/bairros/", bairros, "Radar.bairros()"))

# ------------------------------------------------------------------ Propostas
propostas = f"""
<section class="wrap phead">
  <p class="eyebrow">Tudo o que entrou na Câmara</p>
  <h1>As propostas apresentadas na Câmara</h1>
  <p class="lead" id="hsub"></p>
  <div class="split" id="split" aria-hidden="true"></div>
  <div class="cats" id="cats"></div>
</section>
<section class="wrap" id="lista-propostas">
  <p class="eyebrow">Proposta por proposta</p>
  <h2>Procure qualquer proposta</h2>
  <div class="search" style="max-width:640px">{SEARCH_ICON}<input id="pq" type="search" placeholder="Ex.: creche, iluminação, nome de uma rua" autocomplete="off" aria-label="Procurar proposta"></div>
  <ul class="chips" id="ptabs"></ul>
  <p class="mute" id="pcount" style="font-size:14px;margin:6px 0 10px"></p>
  <div id="plista"></div>
</section>
<section class="wrap" id="por-tipo">
  <p class="eyebrow">Na contagem da Câmara</p>
  <h2>Por tipo de proposição</h2>
  <div class="box"><ol class="rank" id="ptipos"></ol><p class="mute" id="psem" style="font-size:14px;margin:14px 0 0"></p></div>
</section>
"""
escreve("propostas/index.html", pagina("propostas", "Propostas · Radar Serra Negra",
        "Todas as propostas apresentadas na Câmara de Serra Negra desde a posse: pedidos, cobranças, homenagens e projetos de lei.",
        "/propostas/", propostas, "Radar.propostas()"))

# ------------------------------------------------------------------ Sessões
sessoes = f"""
<section class="wrap phead">
  <p class="eyebrow">Na Câmara</p>
  <h1>Pautas das sessões</h1>
  <p class="lead">A pauta é a lista do que a Câmara vai analisar em cada sessão. Abra a pauta oficial para ver os detalhes.</p>
  <p class="mute" id="pautas-n" style="font-size:14px"></p>
  <div id="pautas"></div>
  <p class="mute" style="font-size:14px;margin-top:18px">{SEM_VOTOS}</p>
</section>
"""
escreve("sessoes/index.html", pagina("sessoes", "Sessões · Radar Serra Negra",
        "As pautas das sessões da Câmara de Serra Negra desde a posse, com o link para o documento oficial.",
        "/sessoes/", sessoes, "Radar.sessoes()"))

# ------------------------------------------------------------------ Prefeitura (TCE-SP)
prefeitura = """
<section class="wrap phead">
  <p class="eyebrow">Radar da Prefeitura</p>
  <h1>O dinheiro da Prefeitura</h1>
  <p class="lead" id="pf-lead">Quanto a Prefeitura de Serra Negra recebe, quanto paga e para quem. Os números são os que a própria Prefeitura envia ao Tribunal de Contas do Estado (TCE-SP).</p>
  <ul class="chips" id="pf-anos" aria-label="Escolha o ano"></ul>
  <div class="kpis" id="pf-kpis"></div>
</section>
<section class="wrap">
  <p class="eyebrow">Mês a mês</p>
  <h2>Quanto entrou e quanto foi pago</h2>
  <p class="mute" id="pf-mes-sub" style="margin:0 0 6px"></p>
  <div class="box"><ul class="pf-leg"><li><i class="e"></i>Entrou (receita)</li><li><i class="s"></i>Pago pela Prefeitura</li></ul><div class="pf-meses" id="pf-meses"></div></div>
</section>
<section class="wrap">
  <div class="cols">
    <div class="box"><h3>De onde vem o dinheiro</h3><p class="mute" style="margin:-4px 0 14px;font-size:14px">Impostos da cidade e repasses do Estado e do governo federal.</p><ol class="rank" id="pf-grp"></ol></div>
    <div class="box"><h3>Quanto custa a Câmara</h3><div id="pf-cam"></div></div>
  </div>
</section>
<section class="wrap">
  <p class="eyebrow">Fornecedores</p>
  <h2>Para quem a Prefeitura mais pagou</h2>
  <p class="mute" id="pf-forn-sub" style="margin:0 0 12px"></p>
  <div class="box"><ol class="pf-forn" id="pf-forn"></ol><button class="btn gh" type="button" id="pf-mais" hidden>Ver mais empresas</button>
  <p class="mute" id="pf-pf" style="font-size:14px;margin:16px 0 0"></p></div>
</section>
<section class="wrap">
  <p class="eyebrow">Como ler</p>
  <h2>De onde vêm esses números</h2>
  <div class="method">
    <details open><summary>Fonte</summary><p>Portal da Transparência Municipal do Tribunal de Contas do Estado de São Paulo (TCE-SP), com os dados que a Prefeitura envia todo mês. O Radar consulta esses dados diariamente. Os números de um mês costumam aparecer no TCE uns 30 a 60 dias depois. Veja a fonte em <a href="https://transparencia.tce.sp.gov.br/" target="_blank" rel="noopener">transparencia.tce.sp.gov.br</a> (município: Serra Negra).</p></details>
    <details open><summary>“Pago” e “entrou”</summary><p><b>Pago</b> é o dinheiro que de fato saiu do caixa da Prefeitura naquele mês. Pode incluir contas de meses ou anos anteriores. Inclui também o Serviço de Previdência dos Funcionários Municipais, que o TCE lista junto com a Prefeitura. <b>Entrou</b> é o que a Prefeitura arrecadou: impostos, taxas e repasses do Estado e do governo federal. Os dois não se comparam como um “lucro” ou “prejuízo”: a Prefeitura também guarda dinheiro para pagar depois, e parte das receitas tem destino obrigatório, como saúde e educação.</p></details>
    <details open><summary>Fornecedores</summary><p>A lista soma os pagamentos feitos a cada CNPJ no ano. Aparecer na lista não indica nenhum problema: mostra só para onde o dinheiro foi. Pagamentos a pessoas físicas aparecem só como total, sem nomes, para proteger a privacidade de servidores, aposentados e prestadores.</p></details>
    <details open><summary>Câmara</summary><p>O custo da Câmara é o que a própria Câmara pagou no período, com o dinheiro que recebe da Prefeitura: salários, funcionários, contas e serviços.</p></details>
  </div>
</section>
"""
if TEM_PF:
    escreve("prefeitura/index.html", pagina("prefeitura", "Prefeitura · Radar Serra Negra",
            "Quanto a Prefeitura de Serra Negra recebe, quanto paga e para quem, com os dados oficiais do TCE-SP.",
            "/prefeitura/", prefeitura, "Radar.prefeitura()",
            extra_head=f'<script src="{BASE}/prefeitura.js?v={int(os.path.getmtime(PF))}"></script>\n'))

# ------------------------------------------------------------------ Sobre
TSE_SOBRE = ('<li><span class="ti">2</span><span>Tribunal Superior Eleitoral (TSE), resultado oficial da eleição de 2024: nome de urna e votos de cada vereador</span><b></b></li>'
             if TEM_TSE else "")
TCE_SOBRE = TSE_SOBRE + ('<li><span class="ti">3</span><span>Tribunal de Contas do Estado (TCE-SP), Portal da Transparência Municipal: receitas, pagamentos e fornecedores da Prefeitura e gastos da Câmara</span><b></b></li>'
             if TEM_PF else "")
LOC_SOBRE = ('    <details open><summary>Onde foi votado e onde pede</summary><p>Os votos de 2024 são os dados oficiais do TSE, somados por local de votação. '
             'O bairro de cada local é o que a Justiça Eleitoral informa. Mostramos os 5 locais onde cada vereador teve mais votos e quantos pedidos de melhoria '
             f'saíram do gabinete para aquele bairro. “Voto concentrado” quer dizer que boa parte dos votos veio desses 5 locais; na média da Câmara, {D["locm"]}%. '
             'Atenção: o eleitor vota perto de onde morava quando tirou o título, que nem sempre é onde mora hoje. Por isso o cruzamento mostra uma tendência, não uma regra.</p></details>'
             if D.get("locm") is not None else "")
contato_sobre = (f'Escreva para <a href="mailto:{e(CONTATO)}"><b>{e(CONTATO)}</b></a> com o link da proposta ou da página. A correção é feita rápido.'
                 if CONTATO else "Em breve um endereço de contato para correções aparecerá aqui.")
sobre = f"""
<section class="wrap phead">
  <p class="eyebrow">Transparência</p>
  <h1>Sobre o Radar Serra Negra</h1>
  <p class="lead">Um site independente que reúne, num só lugar, as propostas dos vereadores de Serra Negra desde a posse, em 1º de janeiro de 2025. Só com dados oficiais, a mesma régua para todos e nenhuma nota ou opinião.</p>
  <div class="cols" style="margin-top:10px">
    <div class="box"><h3>De onde vêm os dados</h3><ul class="themes" style="gap:10px">
      <li><span class="ti">1</span><span>Dados Abertos da Câmara Municipal de Serra Negra (<a href="https://www.cmserranegra.sp.gov.br/dadosabertos" target="_blank" rel="noopener">cmserranegra.sp.gov.br/dadosabertos</a>): vereadores em exercício, proposições e pautas das sessões</span><b></b></li>{TCE_SOBRE}</ul>
      <p class="mute" style="margin:12px 0 0;font-size:14px">Consultamos as fontes oficiais todos os dias. Quando a coleta retorna dados incompletos ou inconsistentes, o site continua mostrando a última versão validada.</p></div>
    <div class="box"><h3>Achou um erro?</h3><p style="margin:0 0 10px">{contato_sobre}</p></div>
  </div>
</section>
<section class="wrap">
  <p class="eyebrow">Metodologia</p>
  <h2>Como contamos</h2>
  <div class="method">
    <details open><summary>Os grupos de propostas</summary><p>A mesma regra vale para todos.<br>• <b>Pedido de melhoria no bairro</b> (na Câmara se chama “indicação”): o vereador pede à Prefeitura uma melhoria na rua ou no bairro.<br>• <b>Cobrança</b>: pedido de informação, requerimento ou moção de apelo, quando o vereador pergunta ou cobra algo da Prefeitura ou de outro órgão.<br>• <b>Homenagem</b>: parabéns, voto de pesar, título, medalha, nome de rua ou data comemorativa.<br>• <b>Projeto de lei</b>: cria ou muda uma regra da cidade.<br>• <b>Outros</b>: moções de apoio ou repúdio, regras internas da Câmara e demais tipos.</p></details>
    <details open><summary>Quem é o autor</summary><p>O autor de cada proposta é o que a Câmara informa no campo “autoria”. O Radar procura ali o nome de cada vereador em exercício. Quando a autoria é “Câmara Municipal”, a Prefeitura ou alguém que não está em exercício hoje, a proposta aparece na busca com a autoria original, mas não é contada para nenhum vereador.</p></details>
    <details open><summary>Bairros e ruas</summary><p>Os dados abertos da Câmara não informam o bairro de cada pedido. O bairro e a rua são lidos do texto oficial de cada pedido (o trecho “Rua tal – Bairro tal”). Quando o texto não segue esse formato, o pedido não entra no cruzamento por rua, mas continua aparecendo na busca por palavra.</p></details>
    <details id="subsidios" open><summary>Estimativa de subsídios dos vereadores</summary>
      <p>O contador soma os subsídios brutos mensais estimados de {SUBSIDIOS["vereadores"]} vereadores e de quem ocupa a presidência, desde 1º de janeiro de 2025. O mês em andamento é proporcional ao tempo decorrido.</p>
      <p>A <a href="https://ecrie.com.br/sistema/conteudos/arquivo/a_107_0_1_27122023144318.pdf#page=21">Resolução nº 420/2023</a> fixa {brl(SUBSIDIOS["base"])} por vereador. Para a presidência, o acréscimo de 50% resultaria em {brl(PRESIDENCIA_NOMINAL)} antes do teto. O cálculo aplica o limite de 30% do subsídio estadual em cada período, conforme as leis <a href="https://www.al.sp.gov.br/repositorio/legislacao/lei/2023/lei-17617-16.01.2023.html">nº 17.617/2023</a> e <a href="https://www.al.sp.gov.br/repositorio/legislacao/lei/2025/lei-18384-23.12.2025.html">nº 18.384/2025</a>. Pela referência de 2026, são até {brl(TETO_ATUAL)} para a presidência e {brl(TOTAL_MENSAL)} mensais no conjunto.</p>
      <p>A estimativa usa os valores de referência da resolução e tem cobertura até dezembro de 2026. A folha pode refletir reajustes ou descontos. A conta exclui 13º e outros pagamentos.</p>
    </details>
{LOC_SOBRE}
    <details open><summary>O que o site não mostra</summary><p>{SEM_VOTOS} As votações aparecem nos dados abertos só com o resultado total, e o Radar não deduz o voto de ninguém a partir dele.</p></details>
  </div>
</section>
<section class="wrap" id="correcoes">
  <p class="eyebrow">Transparência do próprio site</p>
  <h2>Quem somos, correções e aviso legal</h2>
  <div class="method">
    <details open><summary>Quem faz</summary><p>O Radar Serra Negra faz parte do <a href="{DOMINIO}/">Voz das Cidades</a>, projeto independente, sem ligação com Câmaras, Prefeituras ou partidos.</p></details>
    <details open><summary>Correções</summary><p>Quando alguém aponta um erro, conferimos na fonte oficial. Se o erro for nosso, corrigimos e anotamos aqui a data e o que mudou.</p><ul><li>Nenhuma correção registrada até agora.</li></ul></details>
    <details open><summary>Aviso legal</summary><p>Este não é um site oficial. É um projeto independente, sem ligação com a Câmara, a Prefeitura, candidatos ou partidos, e não faz propaganda a favor ou contra ninguém. Todas as informações vêm de dados que os próprios órgãos públicos publicam, como manda a Lei de Acesso à Informação (Lei 12.527/2011). O site mostra fatos e contagens, não dá notas nem acusa ninguém. Se um dado oficial estiver errado na origem, o erro aparece aqui também até que o órgão o corrija.</p></details>
    <details open><summary>Privacidade</summary><p>O site não usa cookies e não identifica quem o visita.{" As visitas são contadas de forma anônima, sem guardar quem é a pessoa." if GOATCOUNTER else ""} As fontes de letra são carregadas do Google Fonts.</p></details>
  </div>
</section>
"""
escreve("sobre/index.html", pagina("sobre", "Sobre · Radar Serra Negra",
        "Como o Radar Serra Negra conta os números: fonte oficial, regras e o que o site não mostra.",
        "/sobre/", sobre, "Radar.sobre()"))

# ------------------------------------------------------------------ 404, robots, sitemap
escreve("404.html", pagina("", "Página não encontrada · Radar Serra Negra", "Página não encontrada.", "/404.html", f"""
<section class="wrap e404">
  <p class="bign">404</p>
  <h1 style="font-family:var(--display);font-weight:900;font-size:clamp(26px,6vw,40px);margin:0 0 10px">Esta página não existe</h1>
  <p class="lead" style="margin:0 auto 20px">O endereço pode ter mudado. Comece por uma destas páginas:</p>
  <p style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap"><a class="btn" href="{BASE}/">Página inicial</a><a class="btn gh" href="{BASE}/vereadores/">Vereadores</a><a class="btn gh" href="{BASE}/bairros/">Seu bairro</a></p>
</section>""", ""))
urls = ["/", "/vereadores/", "/comparar/", "/bairros/", "/propostas/", "/sessoes/"] + (["/prefeitura/"] if TEM_PF else []) + ["/sobre/"] + [f"/vereador/{s}/" for s in SLUGS]
escreve("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{URL_SITE}{u}</loc><lastmod>{D['ger']}</lastmod></url>\n" for u in urls) + "</urlset>\n")
escreve("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {URL_SITE}/sitemap.xml\n")

print(f"Páginas geradas: início, vereadores, {len(V)} vereadores, bairros, propostas, sessões, {'prefeitura, ' if TEM_PF else ''}sobre.")
