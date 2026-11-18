# -*- coding: utf-8 -*-
"""
Robô do Radar Serra Negra.

Vai à API de Dados Abertos da Câmara Municipal de Serra Negra (sistema da Clan Tecnologia,
https://www.cmserranegra.sp.gov.br/dadosabertos) e baixa:
  - a lista de vereadores em exercício;
  - todas as proposições desde a posse (01/01/2025), de todos os tipos que a API lista
    (indicações, requerimentos, moções, projetos de lei...);
  - as pautas das sessões desde a posse;
e grava tudo em site/dados.js, que as páginas leem.

O TOKEN DE ACESSO NUNCA FICA NO CÓDIGO. O robô lê o token da variável de ambiente
CLAN_TOKEN. No GitHub, ele fica guardado num Secret com esse mesmo nome.
O robô também apaga o token de qualquer mensagem que mostra na tela.

O que a API NÃO tem (e por isso o site não mostra):
  - voto de cada vereador e presença nas sessões (as votações vêm só com o total);
  - bairro de cada proposição (o serviço "bairros" volta vazio): o bairro e a rua
    são lidos do texto da ementa, quando o texto traz "Rua tal - Bairro tal".

Uso:  python coletor/coletar.py
Se a coleta vier incompleta ou estranha, o robô para com erro e NÃO
sobrescreve os dados antigos: o site continua com a última versão boa.
"""
import html, io, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

API = "https://www.cmserranegra.sp.gov.br/jsonweb/web-aplicativo.php"
SITE_CAMARA = "https://www.cmserranegra.sp.gov.br"
POSSE = "2025-01-01"
UA = "RadarCidadao/1.0"  # o servidor da Câmara responde 406 para User-Agent que imita navegador
PAUSA = 1.5              # segundos entre pedidos, para não pesar no servidor
POR_PAGINA = 50          # a API devolve 50 proposições por página
MAX_PAGINAS = 300        # trava contra paginação que nunca acaba
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "site", "dados.js")
FOTOS = os.path.join(RAIZ, "site", "fotos")
TOKEN = os.environ.get("CLAN_TOKEN", "").strip()

BRT = timezone(timedelta(hours=-3))
_ultimo = [0.0]
for _saida in (sys.stdout, sys.stderr):  # no Windows, não quebra ao mostrar acentos
    if hasattr(_saida, "reconfigure"):
        _saida.reconfigure(errors="replace")


# ---------------------------------------------------------------- acesso à API
def sem_token(texto):
    """Apaga o token de qualquer texto antes de mostrar na tela ou nos registros do GitHub."""
    texto = str(texto)
    if TOKEN:
        texto = texto.replace(TOKEN, "***").replace(urllib.parse.quote(TOKEN, safe=""), "***")
    return re.sub(r"(keysoft=)[^&\s\"']+", r"\1***", texto)


def baixar(url, tentativas=4):
    for t in range(tentativas):
        espera = PAUSA - (time.time() - _ultimo[0])
        if espera > 0:
            time.sleep(espera)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json, */*"})
            with urllib.request.urlopen(req, timeout=120) as r:
                dado = r.read()
            _ultimo[0] = time.time()
            return dado
        except Exception as e:  # noqa
            _ultimo[0] = time.time()
            print(f"  ! falhou ({sem_token(e)}); tentando de novo em {5 * (t + 1)}s", file=sys.stderr)
            time.sleep(5 * (t + 1))
    raise SystemExit(f"Não consegui baixar: {sem_token(url)}")


def decodificar(dado):
    try:
        return dado.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dado.decode("cp1252", "replace")


def chamar(servico, **params):
    """Chama um serviço da API e devolve o JSON já lido (ou None se a resposta vier vazia)."""
    url = API + "?" + urllib.parse.urlencode({"keysoft": TOKEN, "call": servico, **params})
    texto = decodificar(baixar(url)).strip()
    if not texto:
        return None
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        raise SystemExit(f"A resposta do serviço '{servico}' não veio em JSON: {sem_token(texto[:200])}")


def registros(resposta):
    """A API devolve uma lista de registros, às vezes dentro de um objeto. Acha essa lista."""
    if isinstance(resposta, list):
        return [x for x in resposta if isinstance(x, dict)]
    if isinstance(resposta, dict):
        listas = [v for v in resposta.values() if isinstance(v, list) and any(isinstance(x, dict) for x in v)]
        if listas:
            return [x for x in max(listas, key=len) if isinstance(x, dict)]
        dentro = [r for r in (registros(v) for v in resposta.values() if isinstance(v, dict)) if r]
        if dentro:
            return max(dentro, key=len)
        valores = list(resposta.values())
        if valores and all(isinstance(v, dict) for v in valores):
            return valores
    return []


def erro_da_api(resposta):
    """Se a API devolveu uma mensagem de erro (token errado, por exemplo), devolve o texto dela."""
    if isinstance(resposta, dict):
        for k, v in resposta.items():
            if re.search(r"erro|error|mensagem|message|msg", k, re.I) and isinstance(v, str) and v.strip():
                return sem_token(v.strip())
    return ""


# ---------------------------------------------------------------- texto
def limpa(s):
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.lower()).strip()


def palavras(s):
    """Só letras e números, separados por um espaço: 'Ver. João-Paulo' -> 'ver joao paulo'."""
    return re.sub(r"[^a-z0-9]+", " ", norm(s)).strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")


def bonito(s):
    s = re.sub(r"\s+", " ", s).strip()
    if s != s.upper():
        return s  # já vem com maiúsculas e minúsculas: mantém como a Câmara escreveu
    s = s.title()
    return re.sub(r"\b(Da|De|Do|Dos|Das|E)\b", lambda m: m.group(1).lower(), s)


def pega(d, *nomes):
    """Lê o primeiro campo preenchido entre os nomes dados, sem ligar para maiúsculas, acentos ou hífens."""
    chaves = {re.sub(r"[^a-z0-9]+", "_", norm(k)).strip("_"): k for k in d}
    for n in nomes:
        k = chaves.get(n)
        if k is None:
            continue
        v = d[k]
        if isinstance(v, dict):
            v = pega(v, "sigla", "nome", "descricao", "titulo")
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str) and limpa(v):
            return limpa(v)
    return ""


def data_iso(s):
    """'22/09/2026', '22/09/2026 19:30', '2026-09-22' ou '2026-09-22 19:30:00' -> '2026-09-22'."""
    s = str(s or "").strip()
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def link_oficial(u):
    """Endereço da página oficial, sempre completo e nunca com o token."""
    u = str(u or "").strip()
    if not u:
        return ""
    u = urllib.parse.urljoin(SITE_CAMARA + "/", u)
    partes = urllib.parse.urlsplit(u)
    if partes.scheme not in ("http", "https"):
        return ""
    consulta = [(k, v) for k, v in urllib.parse.parse_qsl(partes.query, keep_blank_values=True) if k.lower() != "keysoft"]
    return urllib.parse.urlunsplit(partes._replace(query=urllib.parse.urlencode(consulta)))


def da_camara(u):
    host = urllib.parse.urlsplit(u).hostname or ""
    return host == "cmserranegra.sp.gov.br" or host.endswith(".cmserranegra.sp.gov.br")


def mostra_campos(nome, lista):
    if lista:
        print(f"   campos de '{nome}':", ", ".join(sorted(map(str, lista[0].keys()))))


# ---------------------------------------------------------------- fotos
def reduzir_foto(dado, lado=240):
    """Pega um quadrado no centro e salva um JPEG pequeno. Sem a biblioteca Pillow, guarda a foto original."""
    try:
        from PIL import Image
    except ImportError:
        return dado
    im = Image.open(io.BytesIO(dado))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fundo = Image.new("RGB", im.size, (255, 255, 255))
        fundo.paste(im, mask=im.getchannel("A"))
        im = fundo
    else:
        im = im.convert("RGB")
    w, h = im.size
    q = min(w, h)
    esq = (w - q) // 2
    im = im.crop((esq, 0, esq + q, q)).resize((lado, lado), Image.LANCZOS)
    saida = io.BytesIO()
    im.save(saida, "JPEG", quality=82, optimize=True)
    return saida.getvalue()


# ---------------------------------------------------------------- vereadores
def coletar_vereadores():
    print("1/4 Vereadores em exercício…")
    resposta = chamar("vereadores")
    lista = registros(resposta)
    if not lista:
        motivo = erro_da_api(resposta) or "resposta vazia"
        raise SystemExit(f"A API não devolveu vereadores ({motivo}). Confira se o token em CLAN_TOKEN está certo.")
    mostra_campos("vereadores", lista)
    V = []
    for n, r in enumerate(lista):
        nome = pega(r, "nome_completo", "nomecompleto", "nome_civil", "nomecivil", "nome")
        ap = pega(r, "nome_parlamentar", "nomeparlamentar", "apelido", "parlamentar", "nome_urna", "nome") or nome
        if not ap:
            continue
        v = {"nome": bonito(nome or ap), "ap": bonito(ap),
             "part": pega(r, "partido", "sigla_partido", "siglapartido", "partido_sigla"),
             "mesa": pega(r, "cargo", "cargo_mesa", "funcao", "mesa"),
             "url": link_oficial(pega(r, "link", "url", "perfil", "pagina"))}
        email = pega(r, "email", "e_mail", "email_oficial")
        if re.fullmatch(r"[\w.+-]+@cmserranegra\.sp\.gov\.br", email or "", re.I):
            v["email"] = email.lower()  # só e-mail oficial do gabinete, nunca pessoal
        v["id"] = pega(r, "id", "codigo", "cod", "id_vereador", "idvereador") or slug(ap)
        v["_foto"] = link_oficial(pega(r, "foto", "imagem", "url_foto", "foto_url", "img", "fotografia"))
        V.append(v)
    ids = [str(v["id"]) for v in V]
    if len(set(ids)) != len(ids):  # a API não trouxe um código único: usa o nome
        for v in V:
            v["id"] = slug(v["ap"])
    os.makedirs(FOTOS, exist_ok=True)
    for v in V:
        v["id"] = str(v["id"])
        destino = Path(FOTOS) / f"{slug(v['id'])}.jpg"
        u = v.pop("_foto")
        if u and da_camara(u):
            try:
                foto = reduzir_foto(baixar(u, tentativas=2))
            except (Exception, SystemExit) as e:  # noqa
                print(f"  foto de {v['ap']} falhou: {sem_token(e)}", file=sys.stderr)
            else:
                temporario = destino.with_suffix(".tmp")
                temporario.write_bytes(foto)
                temporario.replace(destino)
        if destino.is_file() and destino.stat().st_size > 0:
            v["foto"] = slug(v["id"])
    V.sort(key=lambda v: norm(v["ap"]))
    print(f"   {len(V)} vereadores")
    return V


def chaves_vereador(v):
    """Formas do nome que podem aparecer no campo 'autoria'. Nomes muito curtos ficam de fora."""
    ks = {palavras(v["ap"]), palavras(v["nome"])}
    return {k for k in ks if len(k) >= 4}


def casar_autores(autoria, V, chaves):
    """Quais vereadores aparecem no texto da autoria. Testa os nomes mais longos primeiro,
    para 'João Pedro' não ser contado também como 'João'."""
    t = f" {palavras(autoria)} "
    achados = []
    for k, i in chaves:
        if f" {k} " in t:
            if i not in achados:
                achados.append(i)
            t = t.replace(f" {k} ", " | ")
    return achados


# ---------------------------------------------------------------- proposições
def coletar_tipos():
    print("2/4 Tipos de proposição…")
    resposta = chamar("proposicoes_tipos")
    lista = registros(resposta)
    mostra_campos("proposicoes_tipos", lista)
    tipos = []
    for r in lista:
        c = pega(r, "contract", "contrato", "slug", "legenda", "tipo")
        nome = pega(r, "nome", "descricao", "titulo", "tipo") or c.replace("-", " ")
        if c and c not in [t[0] for t in tipos]:
            tipos.append((c, nome))
    if not tipos:
        motivo = erro_da_api(resposta) or "resposta vazia"
        raise SystemExit(f"A API não devolveu os tipos de proposição ({motivo}).")
    print("   " + ", ".join(nome for _, nome in tipos))
    return tipos


def coletar_proposicoes(tipos):
    print("3/4 Proposições desde a posse (isso demora alguns minutos)…")
    docs, vistos, semdata = [], set(), 0
    mostrou = False
    for contract, nome_tipo in tipos:
        pagina, anterior, descendente, n_tipo = 1, None, None, 0
        while True:
            if pagina > MAX_PAGINAS:
                raise SystemExit(f"'{nome_tipo}' passou de {MAX_PAGINAS} páginas: a paginação da API mudou?")
            lista = registros(chamar("proposicoes", tipo=contract, pagina=pagina))
            if not lista:
                break
            if not mostrou:
                mostra_campos("proposicoes", lista)
                mostrou = True
            assinatura = json.dumps(lista, sort_keys=True, ensure_ascii=False)
            if assinatura == anterior:
                break  # a API repetiu a página anterior: acabou
            anterior = assinatura
            datas = []
            for r in lista:
                d = data_iso(pega(r, "data", "data_apresentacao", "data_protocolo", "data_cadastro", "datahora", "dt"))
                if not d:
                    semdata += 1
                    continue
                datas.append(d)
                if d < POSSE:
                    continue
                titulo = pega(r, "titulo", "numero", "identificacao", "nome")
                link = link_oficial(pega(r, "link", "url", "arquivo"))
                chave = link or f"{contract}|{titulo}|{d}"
                if chave in vistos:
                    continue
                vistos.add(chave)
                docs.append({"tipo": nome_tipo, "cod": titulo or nome_tipo, "data": d.replace("-", ""),
                             "txt": pega(r, "ementa", "descricao", "assunto", "resumo", "texto"),
                             "autoria": pega(r, "autoria", "autor", "autores"),
                             "res": pega(r, "situacao", "status", "resultado"), "link": link})
                n_tipo += 1
            if descendente is None and len(datas) >= 2:
                descendente = datas == sorted(datas, reverse=True)
            if len(lista) < POR_PAGINA:
                break
            # lista da mais nova para a mais antiga e a página inteira é de antes da posse: não precisa ir adiante
            if descendente and datas and max(datas) < POSSE:
                break
            pagina += 1
        print(f"   {nome_tipo}: {n_tipo} desde a posse ({pagina} {'página' if pagina == 1 else 'páginas'})")
    return docs, semdata


# ---------------------------------------------------------------- classificação
HOMEN = (r"congratula|aplauso|parabeniz|parabens|cumpriment|felicita|enaltec|agradec|louvor|homenag|pesar|falecimento|condolenc|"
         r"titulo de cidad|cidadao honorario|cidada honoraria|cidadao emerito|cidada emerita|"
         r"medalha|diploma|honra ao merito|denomina|da nome|da denominacao|institui o dia|institui a semana|institui o mes|"
         r"dia municipal|semana municipal|calendario oficial|data comemorativa|reconhecimento")


def classificar(doc):
    """Mesma regra para todos. Devolve o grupo: b pedido no bairro, c pergunta/cobrança, h homenagem, l lei, o outros."""
    t, tipo = norm(doc["txt"] + " " + doc["cod"]), norm(doc["tipo"])
    homen = re.search(HOMEN, t)
    if re.match(r"indicac", tipo):
        return "b"
    if re.match(r"pedidos? de informac", tipo):
        return "c"
    if re.match(r"requerimento", tipo):
        return "h" if homen else "c"
    if re.match(r"moc", tipo):
        if re.search(r"\bapelo\b", t):
            return "c"
        return "h" if homen else "o"
    if re.match(r"projetos? de resoluc", tipo):
        return "h" if homen else "o"
    if re.match(r"projeto|propostas? de emenda|emendas? a lei organica", tipo):
        return "h" if homen else "l"
    return "o"


TEMAS = [  # assunto do pedido, pelas palavras do texto oficial (ordem importa)
    ("luz", r"iluminac|lampada|luminaria|poste|\bled\b"),
    ("asf", r"tapa[- ]buraco|buraco|asfalt|recape|pavimenta|cascalh|patrolamento|nivelamento"),
    ("tra", r"sinalizac|lombada|transito|semaforo|faixa de pedestre|redutor de velocidade|rotatoria|estacionamento|placa|radar"),
    ("agu", r"esgoto|vazamento|drenagem|alagamento|enchente|\bagua\b|bueiro|boca de lobo|galeria|erosao"),
    ("lim", r"rocag|limpeza|capina|poda|\bmato\b|entulho|arvore|descarte|lixo|coleta"),
    ("cal", r"calcada|passeio publico|sarjet|meio[- ]fio|guia"),
    ("laz", r"praca|playground|academia ao ar livre|parque|quadra|campo de futebol|area de lazer"),
    ("sau", r"\bubs\b|saude|medic|hospital|\bupa\b|dengue|vacina|santa casa|caps\b"),
    ("edu", r"escola|emef|emeb|creche|aluno|educac"),
    ("seg", r"seguranca|guarda civil|guarda municipal|ronda|camera|policia|monitoramento"),
    ("bus", r"onibus|transporte publico|transporte coletivo|ponto de parada|abrigo"),
]
TEMAS_H = [
    ("pes", r"pesar|falecimento|condolenc"),
    ("tit", r"titulo|medalha|diploma|honra ao merito|cidadao|cidada"),
    ("nom", r"denomina|da nome"),
    ("dat", r"institui o dia|institui a semana|institui o mes|dia municipal|semana municipal|calendario|data comemorativa"),
    ("par", r"."),
]


def tema(doc, g, rua=""):
    """O assunto vem do texto do pedido, sem o nome da rua: 'Praça Tal' sozinho não vira pedido de praça."""
    t = norm(doc["txt"])
    if rua:
        t = t.replace(norm(rua), " ")
    for k, rx in (TEMAS_H if g == "h" else TEMAS):
        if re.search(rx, t):
            return k
    return ""


LOGR = r"(?:Rua|Avenida|Av\.|Alameda|Travessa|Estrada Municipal|Estrada|Rodovia|Pra[cç]a|Viela|Largo|Via|Vicinal)"
MAIUSC = "A-ZÁÉÍÓÚÂÊÔÃÕÇ"


def endereco(txt):
    """Tenta achar 'Rua X - Bairro Y' (ou 'no Bairro Y') na ementa. Devolve (rua, bairro); o que não achar vem None."""
    rua = bairro = None
    m = re.search(r"(" + LOGR + r"\s+[^,;\-–(]+?)(?:,?\s*(?:n[º°o.]?\s*)?\d+[^\-–]*?)?\s*[-–]\s*([" + MAIUSC + r"][^.;,()]{2,60})", txt)
    if m:
        rua = re.sub(r"\s+", " ", m.group(1)).strip().rstrip(".")
        rua = re.sub(r"^Av\.\s*", "Avenida ", rua)
        rua = re.sub(r"\s*\)+\s*$", "", rua).strip(" .,")
        if rua.count("(") > rua.count(")"):
            rua = rua.split("(")[0].strip()
        bairro = re.sub(r"\s+", " ", m.group(2)).strip().rstrip(".")
        bairro = re.split(r"\s+(?:e|em|no|na|para|com|entre)\s+", bairro)[0]
    if (not bairro or len(bairro) < 3 or re.match(r"(?i)(rua|avenida|altura|esquina|pr[oó]ximo)", bairro)
            or norm(bairro).startswith("serra negra")):
        bairro = None
        # "no Bairro das Posses": guarda o nome inteiro, para "Bairro da Serra" não virar só "Serra"
        mb = re.search(r"\b[Bb]airro\s+((?:d[aeo]s?\s+)?[" + MAIUSC + r"][^.;,()\-–]{2,50})", txt)
        if mb:
            resto = re.split(r"\s+(?:e|em|no|na|para|com|entre|nesta|neste|desta|deste)\s+", mb.group(1).strip())[0].strip()
            if len(resto) >= 3 and not norm(resto).startswith("serra negra"):
                bairro = "Bairro " + resto
    if not rua:
        mr = re.search(r"(" + LOGR + r"\s+[" + MAIUSC + r"][^,;\-–()]{2,60})", txt)
        if mr:
            rua = re.sub(r"\s+", " ", mr.group(1)).strip(" .,")
            rua = re.sub(r"^Av\.\s*", "Avenida ", rua)
            rua = re.split(r"\s+(?:e|em|no|na|para|com|entre|nesta|neste|desta|deste|altura|pr[oó]ximo)\s+", rua)[0]
    return rua, bairro


# ---------------------------------------------------------------- pautas das sessões
def coletar_pautas():
    print("4/4 Pautas das sessões…")
    P, pagina, anterior, descendente, vistos = [], 1, None, None, set()
    mostrou = False
    while pagina <= MAX_PAGINAS:
        lista = registros(chamar("pautas", pagina=pagina))
        if not lista:
            break
        if not mostrou:
            mostra_campos("pautas", lista)
            mostrou = True
        assinatura = json.dumps(lista, sort_keys=True, ensure_ascii=False)
        if assinatura == anterior:
            break
        anterior = assinatura
        datas = []
        for r in lista:
            d = data_iso(pega(r, "data", "data_sessao", "datasessao", "data_pauta", "datahora", "dt"))
            if not d:
                continue
            datas.append(d)
            if d < POSSE:
                continue
            titulo = pega(r, "titulo", "sessao", "nome", "descricao")
            texto = pega(r, "descricao", "ementa", "resumo", "texto")
            link = link_oficial(pega(r, "link", "url", "arquivo"))
            chave = link or f"{d}|{titulo}"
            if chave in vistos:
                continue
            vistos.add(chave)
            P.append({"d": d.replace("-", ""), "t": titulo, "x": texto if texto != titulo else "", "u": link})
        if descendente is None and len(datas) >= 2:
            descendente = datas == sorted(datas, reverse=True)
        if len(lista) < POR_PAGINA or (descendente and datas and max(datas) < POSSE):
            break
        pagina += 1
    P.sort(key=lambda p: p["d"], reverse=True)
    print(f"   {len(P)} pautas desde a posse")
    return P


# ---------------------------------------------------------------- montagem
def montar():
    if not TOKEN:
        raise SystemExit(
            "Falta o token da API da Câmara.\n"
            "O robô lê o token da variável de ambiente CLAN_TOKEN (nunca do código).\n"
            "No Windows (PowerShell), para testar no seu computador:\n"
            '    $env:CLAN_TOKEN = [Net.NetworkCredential]::new("", (Read-Host "Cole o token" -AsSecureString)).Password\n'
            "    python coletor\\coletar.py\n"
            "No GitHub, o token fica no Secret CLAN_TOKEN do repositório.")
    V = coletar_vereadores()
    tipos = coletar_tipos()
    docs, semdata = coletar_proposicoes(tipos)
    pautas = coletar_pautas()
    return cruzar(V, docs, pautas, semdata)


def chave_bairro(b):
    """'Bairro das Posses' e 'Posses' são o mesmo bairro."""
    return re.sub(r"^bairro\s+(?:d[aeo]s?\s+)?", "", norm(b)).strip()


def nome_urna(urna, civil):
    """'LETICIA ESTEFFANY' -> 'Letícia Esteffany': o TSE grava em maiúsculas e às vezes sem acento;
    a grafia de cada palavra vem do nome completo, quando a palavra aparece lá."""
    grafia = {palavras(p): p for p in civil.split()}
    out = []
    for n, p in enumerate(urna.split()):
        k = palavras(p)
        if k in grafia:
            g = grafia[k]
            out.append(g[0].upper() + g[1:] if n == 0 else g)
        elif n and k in ("da", "de", "do", "das", "dos", "e"):
            out.append(k)
        else:
            out.append(p.capitalize())
    return " ".join(out)


def juntar_tse(V):
    """Nome de urna e votos de 2024 (resultado oficial do TSE, gravado por coletor/tse2024.py)."""
    caminho = os.path.join(RAIZ, "coletor", "tse2024.json")
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as arquivo:
        tse = {palavras(nome): c for nome, c in json.load(arquivo)["candidatos"].items()}
    for v in V:
        c = tse.get(palavras(v["nome"]))
        if not c:
            print(f"   (sem resultado do TSE para {v['nome']})")
            continue
        v["vot"] = c["votos"]
        if c.get("urna"):
            v["ap"] = nome_urna(c["urna"], v["nome"])


def chave_local(b):
    """Nome de bairro sem 'Bairro', 'Jardim', 'Vila', 'das'...: 'Bairro das Posses' e 'POSSES' viram 'posses'."""
    b = norm(b)
    for _ in range(3):
        b = re.sub(r"^(bairro|jardim|jd|vila|vl|parque|pq|residencial|res|recanto|loteamento|chacaras?|estancia|condominio|conjunto|nucleo|cidade|do|da|dos|das|de)\s+", "", b)
    return b.strip()


ACENTO = {"agua": "Água", "aguas": "Águas", "sao": "São", "joao": "João", "jose": "José", "antonio": "Antônio", "sebastiao": "Sebastião",
          "conceicao": "Conceição", "goncalves": "Gonçalves", "lourenco": "Lourenço", "mauricio": "Maurício", "sergio": "Sérgio",
          "lucia": "Lúcia", "camara": "Câmara", "ii": "II", "profa": "Profª", "profa.": "Profª.", "tres": "Três", "barrocao": "Barrocão",
          "luis": "Luís", "ipes": "Ipês", "vinicius": "Vinícius", "inacio": "Inácio", "julio": "Júlio", "nazare": "Nazaré"}
LIGA = {"de", "da", "do", "das", "dos", "e"}


def locais_de_voto(V, IT):
    """Onde cada vereador teve mais votos em 2024 (TSE, por local de votação) e quantos pedidos de
    melhoria fez para o bairro de cada local. Lê coletor/tse_locais.json (gerado por tse_locais.py).
    Devolve a média da Câmara (quanto dos votos veio dos 5 locais principais) ou None sem o arquivo."""
    caminho = os.path.join(RAIZ, "coletor", "tse_locais.json")
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as arquivo:
        tse = json.load(arquivo)
    todos_b = {chave_local(it[10]) for it in IT if it[4] == "b" and it[10]}
    grafia_b = {chave_local(it[10]): it[10] for it in IT if it[10]}

    def arruma(t):  # o TSE grava em maiúsculas e sem acento
        out = []
        for n, p in enumerate(t.replace("-", " - ").split()):
            k = norm(p)
            if n == 0 and k in ("ee.", "ee", "em.", "em", "emef", "emeb"):
                out.append(p.upper())
            elif k in ACENTO:
                out.append(ACENTO[k])
            elif n and k in LIGA:
                out.append(p.lower())
            else:
                out.append(p)
        return " ".join(out).replace(" - ", "-")

    por_nome = {palavras(n): c for n, c in tse["votos"].items()}
    concs = []
    for i, v in enumerate(V):
        c = por_nome.get(palavras(v["nome"]))
        if not c:
            v["loc"] = None
            continue
        total = sum(c.values())
        meus = Counter(chave_local(it[10]) for it in IT if it[4] == "b" and it[10] and i in it[6])
        top = list(c.items())[:5]
        v["loc"] = []
        for k, n in top:
            local = tse["locais"].get(k, {})
            kb = chave_local(local.get("bairro", ""))
            v["loc"].append([arruma(local.get("nome", "?")), grafia_b.get(kb) or arruma(local.get("bairro", "")), n,
                             round(n / total * 100, 1), meus.get(kb) or (0 if kb in todos_b else None)])
        v["lc"] = round(sum(n for _, n in top) / total * 100)
        concs.append(v["lc"])
    return round(sum(concs) / len(concs)) if concs else None


def cruzar(V, docs, pautas, semdata):
    print("Cruzando os dados…")
    juntar_tse(V)
    V.sort(key=lambda v: norm(v["ap"]))  # antes de numerar os autores: a ordem dos índices vale para todo o arquivo
    chaves = sorted(((k, i) for i, v in enumerate(V) for k in chaves_vereador(v)), key=lambda x: -len(x[0]))
    # itens: [id, código, ementa, aaaammdd, grupo, situação, autores, tipo, tema, rua, bairro, link, autoria como veio da API]
    IT, sem_vereador = [], Counter()
    for n, d in enumerate(sorted(docs, key=lambda d: (d["data"], d["cod"]), reverse=True)):
        g = classificar(d)
        rua, bairro = endereco(d["txt"]) if g in "bc" else (None, None)
        aut = casar_autores(d["autoria"], V, chaves)
        if not aut:
            sem_vereador[d["autoria"] or "(autoria em branco)"] += 1
        IT.append([n, d["cod"], d["txt"], d["data"], g, d["res"], aut, d["tipo"], tema(d, g, rua or ""), rua or "", bairro or "", d["link"], d["autoria"]])
    # o mesmo bairro escrito de jeitos diferentes fica com o nome mais usado nos textos oficiais
    grafias = defaultdict(Counter)
    for it in IT:
        if it[10]:
            grafias[chave_bairro(it[10])][it[10]] += 1
    for it in IT:
        if it[10]:
            it[10] = grafias[chave_bairro(it[10])].most_common(1)[0][0]
    if sem_vereador:
        print(f"   {sum(sem_vereador.values())} proposições sem vereador em exercício na autoria. As mais comuns:")
        for a, n in sem_vereador.most_common(12):
            print(f"     {n:5}  {a[:90]}")

    catot = Counter(it[4] for it in IT)
    for i, v in enumerate(V):
        v["cat"] = {c: sum(1 for it in IT if it[4] == c and i in it[6]) for c in "bchlo"}
    locm = locais_de_voto(V, IT)

    # bairros mais citados
    cont_b, nome_b = Counter(), {}
    for it in IT:
        if it[10]:
            k = norm(it[10])
            cont_b[k] += 1
            nome_b.setdefault(k, it[10])
    bairros = [(nome_b[k], n) for k, n in cont_b.most_common() if n >= 2]

    # problemas que não somem: mesmo assunto, mesma rua, várias vezes
    grp = defaultdict(list)
    for n, it in enumerate(IT):
        if it[4] == "b" and it[9] and it[8]:
            grp[(norm(it[9]), norm(it[10]), it[8])].append(n)
    rep = []
    for (r, b, th), ids in grp.items():
        if len(ids) < 3:
            continue
        its = [IT[n] for n in ids]
        rep.append({"r": its[0][9], "b": its[0][10], "th": th, "n": len(ids), "ids": ids,
                    "a": len({a for it in its for a in it[6]}),
                    "d0": min(it[3] for it in its), "d1": max(it[3] for it in its)})
    rep.sort(key=lambda g: (-g["n"], -g["a"]))

    agora = datetime.now(BRT)
    dados = {
        "gerh": agora.isoformat(timespec="seconds"), "ger": agora.strftime("%Y-%m-%d"), "posse": POSSE,
        "catot": catot, "tipos": Counter(it[7] for it in IT).most_common(),
        "semaut": sum(1 for it in IT if not it[6]), "semdata": semdata,
        "bairros": [b for b, _ in bairros], "bairrosn": [n for _, n in bairros],
        "rep": rep, "pautas": pautas, "locm": locm,
        "v": [{k: v.get(k) for k in ("id", "ap", "nome", "part", "mesa", "foto", "email", "url", "cat", "vot", "loc", "lc")} for v in V],
        "items": IT,
    }
    conferir(dados)
    return dados


def conferir(D):
    """Trava de segurança: se algo vier estranho, não publica."""
    erros = []
    if not 5 <= len(D["v"]) <= 25:
        erros.append(f"número de vereadores estranho: {len(D['v'])}")
    if len(D["items"]) < 30:
        erros.append(f"poucas proposições desde a posse: {len(D['items'])}")
    if D["semdata"] > max(20, len(D["items"]) // 10):
        erros.append(f"{D['semdata']} proposições sem data reconhecida: o formato da API mudou?")
    if D["items"] and all(not it[6] for it in D["items"]):
        erros.append("nenhuma proposição foi ligada a um vereador: confira o campo de autoria")
    if sum(1 for v in D["v"] if sum(v["cat"].values()) == 0) > len(D["v"]) // 2:
        erros.append("mais da metade dos vereadores sem nenhuma proposição")
    ids = [v["id"] for v in D["v"]]
    if len(set(ids)) != len(ids):
        erros.append("vereadores com IDs duplicados")
    if TOKEN and TOKEN in json.dumps(D, ensure_ascii=False):
        erros.append("o token apareceu nos dados: nada será gravado")
    if os.path.exists(SAIDA):
        velho = ler_dados()
        for chave, anterior, atual in (
            ("proposições", len(velho["items"]), len(D["items"])),
            ("pautas", len(velho.get("pautas", [])), len(D["pautas"])),
        ):
            if atual * 10 < anterior * 9:
                erros.append(f"{chave} caíram de {anterior} para {atual}")
    if erros:
        raise SystemExit("COLETA RECUSADA, site mantido como estava:\n - " + "\n - ".join(erros))


def ler_dados():
    texto = Path(SAIDA).read_text(encoding="utf-8").strip()
    if not texto.startswith("window.RB=") or not texto.endswith(";"):
        raise ValueError(f"Formato inesperado: {SAIDA}")
    return json.loads(texto[len("window.RB="):-1])


def recruzar():
    """Refaz só o cruzamento (grupos, assuntos, ruas, bairros) a partir do site/dados.js já baixado.
    Não acessa a API e não precisa do token. Mantém a data e a hora da última coleta."""
    velho = ler_dados()
    V = [dict(v) for v in velho["v"]]
    docs = [{"tipo": it[7], "cod": it[1], "data": it[3], "txt": it[2], "autoria": it[12], "res": it[5], "link": it[11]}
            for it in velho["items"]]
    D = cruzar(V, docs, velho["pautas"], velho.get("semdata", 0))
    D["gerh"], D["ger"] = velho["gerh"], velho["ger"]
    return D


if __name__ == "__main__":
    D = recruzar() if "--recruzar" in sys.argv[1:] else montar()
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    tmp = SAIDA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("window.RB=" + json.dumps(D, ensure_ascii=False, separators=(",", ":")) + ";\n")
    os.replace(tmp, SAIDA)
    print(f"Pronto: {len(D['items'])} proposições, {len(D['v'])} vereadores, {len(D['pautas'])} pautas, {len(D['rep'])} problemas repetidos.")
