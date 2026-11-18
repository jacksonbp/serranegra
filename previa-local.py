"""Abre a prévia do Radar Serra Negra no seu computador, no mesmo caminho do site no ar (/serranegra/).

Uso: python previa-local.py   (ou dois cliques em ABRIR-PREVIA.cmd)
Antes, gere os dados e as páginas: python coletor/coletar.py  e  python coletor/paginas.py
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from threading import Timer
import webbrowser


def main():
    raiz = Path(__file__).resolve().parent
    if not (raiz / "site" / "index.html").exists():
        raise SystemExit("Ainda não há páginas. Rode antes: python coletor/coletar.py  e  python coletor/paginas.py")
    with TemporaryDirectory(prefix="radar-serranegra-") as directory:
        preview = Path(directory)
        copytree(raiz / "site", preview / "serranegra")
        handler = partial(SimpleHTTPRequestHandler, directory=preview)

        with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            radar = f"http://127.0.0.1:{server.server_port}/serranegra/"
            print(f"Radar Serra Negra: {radar}", flush=True)
            print("Deixe esta janela aberta durante a prévia. Pressione Ctrl+C para encerrar.", flush=True)
            opener = Timer(0.3, webbrowser.open, (radar,))
            opener.daemon = True
            opener.start()
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
