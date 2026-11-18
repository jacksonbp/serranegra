# Radar Serra Negra

Site que mostra o que cada vereador de Serra Negra-SP propôs desde a posse (01/01/2025):
pedidos para os bairros, cobranças, homenagens e projetos de lei. Só dados oficiais da Câmara,
atualizados todo dia por um robô. Faz parte do **Voz das Cidades** e fica em
`https://vozdascidades.com.br/serranegra/`.

## O que tem aqui

| Pasta / arquivo | O que é |
|---|---|
| `coletor/config_site.py` | Endereço do site (`/serranegra`), e-mail de contato e contador de visitas. |
| `coletor/coletar.py` | O robô que vai à API da Câmara e grava `site/dados.js`. |
| `coletor/tse2024.py` | Roda uma vez só: grava em `coletor/tse2024.json` o nome de urna e os votos de 2024 de cada candidato (resultado oficial do TSE). |
| `coletor/tse_locais.py` | Roda uma vez só, com os arquivos `votacao_secao_2024_SP.zip` e `eleitorado_local_votacao_2024.zip` do TSE (cdn.tse.jus.br): grava em `coletor/tse_locais.json` os votos de cada candidato por local de votação de Serra Negra. |
| `coletor/prefeitura.py` | Baixa do TCE-SP o dinheiro que entra e sai da Prefeitura e grava `site/prefeitura.js` (não precisa de token). |
| `coletor/paginas.py` | Gera as páginas do site a partir de `site/dados.js` e `site/prefeitura.js`. |
| `site/assets/` | Visual (`radar.css`, igual ao do Radar Bragança) e o código das páginas (`radar.js`). |
| `.github/workflows/atualizar.yml` | Faz o GitHub rodar o robô todo dia às 4h17 e republicar o site. |
| `previa-local.py`, `ABRIR-PREVIA.cmd` | Abrem a prévia no seu computador, no caminho `/serranegra/`. |

## De onde vêm os dados

API de Dados Abertos da Câmara Municipal de Serra Negra (sistema da Clan Tecnologia,
`https://www.cmserranegra.sp.gov.br/dadosabertos`). O robô usa os serviços `vereadores`,
`proposicoes_tipos`, `proposicoes` (todos os tipos, 50 por página) e `pautas`.

A página da Prefeitura usa o Portal da Transparência Municipal do TCE-SP
(`https://transparencia.tce.sp.gov.br/api/json/despesas/serra-negra/<ano>/<mes>` e `.../receitas/...`),
com os dados que a própria Prefeitura envia ao Tribunal de Contas. Cada mês fica guardado em
`coletor/cache_tce.json`; os 4 meses mais recentes são baixados de novo todo dia.

**O que a API não tem, e por isso o site não mostra:**

- voto de cada vereador e presença nas sessões (as votações vêm só com o total);
- bairro de cada proposição (o serviço `bairros` volta vazio). O bairro e a rua são lidos do texto
  da ementa, quando ele traz "Rua tal - Bairro tal" ou "Bairro tal";
- parte das proposições tem autoria "Câmara Municipal" ou da Prefeitura. Elas aparecem na busca
  com a autoria original, mas não contam para nenhum vereador.

## O token da API (importante)

O token **nunca** vai no código, em arquivo, em commit ou em conversa.

- O robô lê o token da variável de ambiente `CLAN_TOKEN`.
- No GitHub, ele fica num **Secret** chamado `CLAN_TOKEN`.
- O robô apaga o token de toda mensagem que mostra na tela e de todo link que grava,
  e se recusa a gravar os dados se o token aparecer neles.

## Testar no seu computador

Abra o PowerShell na pasta `serranegra` e rode, um por vez:

```powershell
$env:CLAN_TOKEN = [Net.NetworkCredential]::new("", (Read-Host "Cole o token" -AsSecureString)).Password
python coletor\coletar.py
python coletor\prefeitura.py
python coletor\paginas.py
python previa-local.py
```

- A primeira linha pede o token e mostra só asteriscos na tela; ele também não fica no
  histórico de comandos. O token vale só para aquela janela do PowerShell: ao fechar a janela,
  ele some.
- A coleta leva alguns minutos, porque o robô espera 1,5 segundo entre cada pedido.
- Na primeira vez, o robô mostra os **nomes dos campos** que a API devolve
  (por exemplo, `campos de 'vereadores': ...`) e as autorias que não casaram com nenhum vereador.
  Isso serve para conferir se ele entendeu o formato da API.
- Sem a biblioteca Pillow, o site funciona, mas sem as imagens de compartilhamento
  (`capa.jpg` e `card.jpg`). No GitHub ela é instalada sozinha.

Se a coleta vier estranha (poucos vereadores, poucas proposições, queda grande em relação
à última coleta), o robô para com erro e não troca os dados antigos.

Depois de mudar só as regras de grupos, assuntos, ruas ou bairros em `coletar.py`, dá para
refazer o cruzamento com os dados já baixados, sem acessar a API e sem token:

```powershell
python coletor\coletar.py --recruzar
python coletor\paginas.py
```

## O que falta para publicar

1. **Testar a coleta com o token de verdade** (passo acima) e conferir 2 ou 3 vereadores
   na mão contra o site da Câmara: número de indicações, nomes, partidos.
   Se os nomes dos campos forem diferentes dos esperados, ajustar `coletor/coletar.py`.
2. **Definir o e-mail de contato** em `coletor/config_site.py` (`CONTATO`). Enquanto estiver
   vazio, o site não mostra a linha de contato.
3. **Revisar os textos da página Sobre** (quem faz, financiamento, correções).
4. **Criar o repositório público** `jacksonbp/serranegra` no GitHub e enviar estes arquivos.
5. **Criar o Secret** `CLAN_TOKEN`: Settings → Secrets and variables → Actions →
   New repository secret.
6. **Ligar o GitHub Pages**: Settings → Pages → Source: GitHub Actions.
7. **Rodar o robô pela primeira vez**: Actions → Atualizar dados e publicar → Run workflow.
   Isso também testa se a API responde a partir dos servidores do GitHub, o que ainda não
   foi conferido. Se a API recusar, o robô para com erro e nada é publicado.
8. **Opcional:** criar um contador GoatCounter e colocar o endereço em `GOATCOUNTER`.
9. **Depois que estiver no ar:** no portal Voz das Cidades, trocar o cartão e o pino de
   Serra Negra de "Em breve" para "No ar", com link para `/serranegra/`.
