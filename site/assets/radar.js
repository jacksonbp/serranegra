/* Radar Serra Negra: código comum a todas as páginas. Os dados vêm de dados.js (window.RB). */
(function(){
/* ============ CONFIGURAÇÃO ============ */
const BASE = new URL('..', document.currentScript.src).pathname.slice(0, -1);
const CONFIG={
  cidade:'Serra Negra',
  contato:document.body.dataset.contato||'',
  telefone:document.body.dataset.telefone||'',
  site:new URL(BASE + '/', document.querySelector('link[rel=canonical]').href).href
};
/* ===================================== */
const D=window.RB, V=D.v, IT=D.items; // item: [id,codigo,ementa,aaaammdd,grupo,situacao,autores,tipo,tema,rua,bairro,link,autoria]
const nf=n=>Number(n).toLocaleString('pt-BR');
const MES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
const dt=s=>{s=String(s).replace(/-/g,'');return `${+s.slice(6,8)} ${MES[+s.slice(4,6)-1]} ${s.slice(0,4)}`};
const mesAno=s=>`${MES[+s.slice(4,6)-1]} ${s.slice(0,4)}`;
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const norm=s=>String(s).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
const $=id=>document.getElementById(id);
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
const CEL=!matchMedia('(min-width:760px)').matches;
const slug=s=>norm(s).replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
const urlV=v=>`${BASE}/vereador/${slug(v.ap)}/`;
const svg=(p,s=22)=>`<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;
const ICON={
 pin:'<path d="M12 21s7-6.2 7-11a7 7 0 10-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
 ask:'<path d="M21 12a8 8 0 01-11.8 7L4 20l1.2-4.4A8 8 0 1121 12z"/><path d="M9.8 9.5a2.3 2.3 0 114 1.6c-.7.6-1.3 1-1.3 1.9"/><path d="M12.5 16h.01"/>',
 medal:'<circle cx="12" cy="14" r="5"/><path d="M9 9.5L6.5 3h4L12 6.5 13.5 3h4L15 9.5"/>',
 law:'<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4M10 12h6M10 16h6"/>',
 dots:'<circle cx="6" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="18" cy="12" r="1.4"/>',
 road:'<path d="M8 3L4 21M16 3l4 18M12 4v3M12 11v3M12 18v3"/>',
 leaf:'<path d="M5 19c0-9 5-14 15-14 0 10-5 15-14 14z"/><path d="M5 19c3-4 6-7 10-9"/>',
 bulb:'<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0012 3z"/>',
 sign:'<path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
 walk:'<path d="M4 20h16M6 20v-5h4v5M10 15V9h4v11M14 9V4h4v16"/>',
 tree:'<path d="M12 21v-7"/><path d="M12 14a5 5 0 01-4-8 4.5 4.5 0 018 0 5 5 0 01-4 8z"/><path d="M6 21h12"/>',
 cross:'<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>',
 book:'<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2z"/><path d="M4 21V5M9 7h6"/>',
 shield:'<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/>',
 drop:'<path d="M12 3s6 6.5 6 11a6 6 0 01-12 0c0-4.5 6-11 6-11z"/>',
 bus:'<rect x="4" y="4" width="16" height="13" rx="2"/><path d="M4 11h16M8 17v3M16 17v3M8 14h.01M16 14h.01"/>',
 heart:'<path d="M12 20s-7-4.5-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.5-7 10-7 10z"/>',
 star:'<path d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.2 6-5.5-3-5.5 3 1.2-6L3.2 9.4l6.1-.8z"/>',
 cal:'<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3v4M16 3v4"/>',
 flag:'<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
 users:'<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0113 0M16 4.5a3.5 3.5 0 010 7M18 14a6 6 0 013.5 6"/>'
};
const CAT={
 b:['Pedidos de melhoria nos bairros','Tapar buraco, podar árvore, trocar lâmpada, limpar terreno. É um pedido: a Prefeitura decide se faz.','pin','Pedido'],
 c:['Perguntas e cobranças','Pedidos de explicação à Prefeitura e requerimentos a outros órgãos.','ask','Cobrança'],
 h:['Homenagens','Parabéns, votos de pesar, título de cidadão, medalhas, nome de rua e datas comemorativas.','medal','Homenagem'],
 l:['Propostas de lei','Projetos que criam regra, programa ou obrigação na cidade.','law','Proposta de lei'],
 o:['Outros','Moções de apoio ou repúdio, regras internas da Câmara e demais tipos.','dots','Outro']};
const ORDER=['b','c','h','l','o'];
const TH={luz:['Iluminação','bulb'],asf:['Asfalto e buracos','road'],tra:['Trânsito','sign'],agu:['Água e esgoto','drop'],lim:['Limpeza e poda','leaf'],cal:['Calçadas','walk'],
 laz:['Praças e lazer','tree'],sau:['Saúde','cross'],edu:['Escolas','book'],seg:['Segurança','shield'],bus:['Ônibus','bus'],
 pes:['Votos de pesar','heart'],tit:['Títulos e medalhas','star'],nom:['Nomes de rua e prédio','flag'],dat:['Datas comemorativas','cal'],par:['Parabéns e aplausos','medal']};
const TEMA={luz:'iluminação',asf:'conserto de asfalto',tra:'melhoria no trânsito',agu:'água, esgoto e drenagem',lim:'limpeza e poda',cal:'conserto de calçada',laz:'melhoria em praça e área de lazer',sau:'melhoria na saúde',edu:'melhoria em escola',seg:'segurança',bus:'melhoria no ônibus'};

function clean(it){
  let t=String(it[2]||it[1]||'').trim();
  // tira só a fórmula de abertura; o texto oficial completo continua no link "Abrir na Câmara"
  t=t.replace(/^indicando,?\s+na\s+forma\s+regimental,?\s+seja\s+oficiado\s+ao\s+senhor\s+prefeito\s+municipal\s*,?\s*/i,'');
  t=t.replace(/^(solicitando|solicita|requer(?:endo)?|indicando|indica)\s+(?:(?:ao\s+(?:poder\s+)?executivo(?:\s+municipal)?|ao\s+senhor\s+prefeito(?:\s+municipal)?)\s*,?\s*)?(?:a\s+|o\s+)?/i,'');
  return t.charAt(0).toUpperCase()+t.slice(1);
}
IT.forEach(it=>{it.n=norm(it[1]+' '+it[2]+' '+it[9]+' '+it[10]+' '+(it[12]||''));it.tx=clean(it)});
const hue=i=>(i*47+200)%360;
V.forEach((v,i)=>{const w=v.ap.split(/\s+/).filter(x=>!/^(da|de|do|dos|das)$/i.test(x));v.in=(w[0][0]+(w.length>1?w[w.length-1][0]:'')).toUpperCase();v.i=i;v.tot=ORDER.reduce((s,c)=>s+v.cat[c],0)});
const foto=(v,cls='av')=>v.foto?`<img class="${cls}" src="${BASE}/fotos/${esc(v.foto)}.jpg" alt="" loading="lazy">`:`<span class="${cls} ph0" style="background:hsl(${hue(v.i)} 80% 92%);color:hsl(${hue(v.i)} 55% 28%);display:grid;place-items:center;font-weight:700" aria-hidden="true">${v.in}</span>`;
const av=i=>foto(V[i]);
D.rep.forEach(g=>{g.items=g.ids.map(n=>IT[n])});
/* contagem pelo tipo oficial da Câmara (inclui coautoria) */
const TIPOS=(D.tipos||[]).map(t=>t[0]);
V.forEach(v=>{v.tp={};TIPOS.forEach(t=>v.tp[t]=0)});
IT.forEach(it=>{if(TIPOS.includes(it[7]))it[6].forEach(i=>V[i].tp[it[7]]++)});

/* ---------- cartão de proposta ---------- */
function stt(r){if(!r)return'';const k=/^aprovad/i.test(r)?'ok':/rejeit|vetad/i.test(r)?'no':'';return `<span class="stt ${k}">${esc(r)}</span>`}
function autoria(it){
  if(it[6].length)return `<span class="who">${it[6].slice(0,3).map(a=>`<a href="${urlV(V[a])}" style="display:contents;color:inherit;text-decoration:none">${av(a)}<span class="n">${esc(V[a].ap)}</span></a>`).join('')}${it[6].length>3?`<span>+${it[6].length-3}</span>`:''}</span>`;
  return `<span class="who"><span class="n">${it[12]?'Autoria: '+esc(it[12]):'Autoria não informada'}</span></span>`;
}
function itemHTML(it,showAut){
  const c=it[4], t=TH[it[8]], icon=t?t[1]:CAT[c][2];
  return `<li class="it k-${c}"><span class="ic">${svg(ICON[icon])}</span><div>
    <p class="tx">${esc(it.tx)}</p>
    <div class="mt"><span class="lab">${t?esc(t[0]):CAT[c][3]}</span>${stt(it[5])}<span>${dt(it[3])}</span><span>·</span><span>${esc(it[1])}</span></div>
    <div class="ft">${showAut?autoria(it):'<span></span>'}${it[11]?`<a class="ext" href="${esc(it[11])}" target="_blank" rel="noopener">Abrir na Câmara ↗</a>`:''}</div></div></li>`;
}
function pager(host,items,showAut,step){
  let n=0; host.innerHTML='<ul class="items"></ul>';
  const ul=host.firstChild, btn=document.createElement('button');
  btn.className='more'; btn.type='button';
  const add=()=>{ul.insertAdjacentHTML('beforeend',items.slice(n,n+step).map(i=>itemHTML(i,showAut)).join(''));n+=step;
    if(n>=items.length)btn.remove();else btn.textContent=`Mostrar mais ${Math.min(step,items.length-n)} de ${nf(items.length-n)}`};
  btn.addEventListener('click',add); if(items.length>step)host.appendChild(btn); add();
  if(!items.length)host.innerHTML='<p class="mute">Nada por aqui ainda.</p>';
}
function themeCount(items){const m=new Map();items.forEach(it=>{if(it[8])m.set(it[8],(m.get(it[8])||0)+1)});return [...m.entries()].sort((a,b)=>b[1]-a[1])}

/* ---------- painel lateral (criado em toda página) ---------- */
document.body.insertAdjacentHTML('beforeend',`<div class="veil" id="veil"></div>
<aside class="sheet" id="sheet" role="dialog" aria-modal="true" aria-labelledby="sh-t">
  <div class="sh-top" id="sh-top"><span class="ci" id="sh-i"></span><div><h2 id="sh-t"></h2><p id="sh-s"></p></div><button class="x" id="sh-x" type="button" aria-label="Fechar">×</button></div>
  <div id="sh-f"></div><div id="sh-b"></div></aside>`);
const sheet=$('sheet'), veil=$('veil'); let lastFocus=null;
function openSheet(k,icon,title,sub){
  lastFocus=document.activeElement; $('sh-top').className='sh-top k-'+k; $('sh-i').innerHTML=svg(ICON[icon],24);
  $('sh-t').textContent=title; $('sh-s').textContent=sub||''; $('sh-f').innerHTML=''; $('sh-f').style.display='none'; $('sh-b').innerHTML=''; $('sh-b').scrollTop=0;
  sheet.classList.add('on'); veil.classList.add('on'); document.body.style.overflow='hidden'; $('sh-x').focus();
}
function closeSheet(){sheet.classList.remove('on');veil.classList.remove('on');document.body.style.overflow='';if(lastFocus)lastFocus.focus()}
$('sh-x').addEventListener('click',closeSheet); veil.addEventListener('click',closeSheet);
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&sheet.classList.contains('on'))closeSheet()});
function openCat(c,vi){
  const all=IT.filter(it=>it[4]===c&&(vi==null||it[6].includes(vi)));
  openSheet(c,CAT[c][2],CAT[c][0],`${nf(all.length)} ${vi==null?'na Câmara':'de '+V[vi].ap} até agora`);
  const th=themeCount(all); let cur='';
  const draw=()=>pager($('sh-b'),cur?all.filter(it=>it[8]===cur):all,vi==null,20);
  if(th.length>1){
    $('sh-f').style.display='';
    $('sh-f').innerHTML=`<ul class="chips"><li><button class="chip on" type="button" data-t="">Tudo<small>${nf(all.length)}</small></button></li>${th.map(([k,n])=>`<li><button class="chip" type="button" data-t="${k}">${esc(TH[k][0])}<small>${nf(n)}</small></button></li>`).join('')}</ul>`;
    $('sh-f').onclick=e=>{const b=e.target.closest('[data-t]');if(!b)return;cur=b.dataset.t;$('sh-f').querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x===b));$('sh-b').scrollTop=0;draw()};
  }
  draw();
}

/* ---------- pedidos repetidos + cobrar ---------- */
const repHTML=g=>`<button class="rp" type="button" data-g="${D.rep.indexOf(g)}"><span class="rn num">${g.n}<small>VEZES</small></span>
  <span class="rr">${esc(g.r)}</span><span class="rb">${esc(g.b||CONFIG.cidade)}</span>
  <span class="rm"><span class="lab">${esc(TH[g.th][0])}</span><span>${g.a} ${g.a===1?'vereador pediu':'vereadores pediram'}</span><span>·</span><span>de ${mesAno(g.d0)} a ${mesAno(g.d1)}</span></span><span class="go">Ver pedidos e cobrar →</span></button>`;
const SITE=/^https?:/.test(location.protocol)&&!/claude|localhost|127\./.test(location.hostname)?location.origin+BASE+'/':CONFIG.site;
function openRep(g){
  openSheet('b',TH[g.th][1],g.r,`${TH[g.th][0]} · pedido ${g.n} vezes até agora${g.b?' · '+g.b:''}`);
  const cnt=new Map(); g.items.forEach(it=>it[6].forEach(a=>cnt.set(a,(cnt.get(a)||0)+1)));
  const who=[...cnt.entries()].sort((a,b)=>b[1]-a[1]);
  const msg=a=>`Olá, ${V[a].ap}. Moro em ${CONFIG.cidade}. A Câmara já recebeu ${g.n} pedidos de ${TEMA[g.th]||'melhoria'} na ${g.r}${g.b?', '+g.b:''}, desde ${mesAno(g.d0)}. ${cnt.get(a)===1?'Um deles saiu':cnt.get(a)+' deles saíram'} do seu gabinete, e o problema continua. O que a Prefeitura respondeu? O que ainda dá para fazer?\n\nFonte: ${SITE}`;
  $('sh-b').innerHTML=(who.length?`<div class="cob"><h3>Cobre uma resposta</h3>
    <p>A mensagem já vem pronta. Escolha o vereador, ajuste o texto se quiser e envie.</p>
    <label class="field">Para quem<select id="cob-v">${who.map(([a,n])=>`<option value="${a}">${esc(V[a].ap)} (${n} ${n===1?'pedido':'pedidos'} para esta rua)</option>`).join('')}</select></label>
    <label class="field">Mensagem<textarea id="cob-t"></textarea></label>
    <div class="acts" id="cob-a"></div><div class="ct" id="cob-c"></div></div>`:'')
    +`<p class="h3">Os ${g.n} pedidos, do mais recente ao mais antigo</p><div id="replist"></div>`;
  if(who.length){
    const sel=$('cob-v'), ta=$('cob-t');
    const links=()=>{const v=V[+sel.value], t=encodeURIComponent(ta.value);
      $('cob-a').innerHTML=(v.email?`<a class="btn" href="mailto:${esc(v.email)}?subject=${encodeURIComponent(g.r+': o problema continua')}&body=${t}">Enviar por e-mail</a>`:'')
        +`<a class="btn wa" href="https://wa.me/?text=${t}" target="_blank" rel="noopener">Mandar no grupo do bairro</a><button class="btn gh" type="button" id="cob-cp">Copiar mensagem</button>`;
      $('cob-c').innerHTML=(v.email?`E-mail oficial do gabinete: <b>${esc(v.email)}</b>`:'')+(v.email&&CONFIG.telefone?' · ':'')+(CONFIG.telefone?`Telefone da Câmara: <b>${esc(CONFIG.telefone)}</b>`:'');
      $('cob-cp').onclick=async e=>{try{await navigator.clipboard.writeText(ta.value);e.target.textContent='Copiado'}catch(_){ta.focus();ta.select();e.target.textContent='Selecionado: copie com o dedo'}}};
    const fill=()=>{ta.value=msg(+sel.value);links()};
    sel.addEventListener('change',fill); ta.addEventListener('input',links); fill();
  }
  pager($('replist'),g.items,true,20);
}
document.addEventListener('click',e=>{const b=e.target.closest('[data-g]');if(b)openRep(D.rep[+b.dataset.g])});
function listaReps(host,lista,passo){
  let n=0; const btn=document.createElement('button'); btn.className='more'; btn.type='button'; btn.style.gridColumn='1/-1';
  if(!lista.length){host.innerHTML='<p class="mute">Ainda não há pedidos repetidos para a mesma rua.</p>';return}
  const add=()=>{host.insertAdjacentHTML('beforeend',lista.slice(n,n+passo).map(repHTML).join(''));n+=passo;host.appendChild(btn);
    if(n>=lista.length)btn.remove();else btn.textContent=`Mostrar mais ruas (${lista.length-n} na fila)`};
  btn.addEventListener('click',()=>{btn.remove();add()}); add();
}

/* ---------- peças do vereador ---------- */
const bar5=v=>`<div class="bar5" aria-hidden="true">${ORDER.map(c=>v.cat[c]?`<i class="k-${c}" style="flex:${v.cat[c]} 1 0"></i>`:'').join('')}</div>`;
function vcard(v){
  return `<a class="vcard" href="${urlV(v)}" style="--tint:hsl(${hue(v.i)} 85% 94%)">${foto(v,'')}
    <h3>${esc(v.ap)}</h3><span class="pill">${esc(v.part||'sem partido informado')}${v.mesa?' · '+esc(v.mesa):''}</span>
    <div class="kp num"><div><b>${nf(v.tot)}</b><span>propostas</span></div><div><b>${nf(v.cat.b)}</b><span>pedidos no bairro</span></div><div><b>${nf(v.cat.l)}</b><span>propostas de lei</span></div></div>
    ${bar5(v)}<span class="go">Ver tudo sobre ${esc(v.ap.split(' ')[0])} →</span></a>`;
}
const ORD={nome:(a,b)=>a.ap.localeCompare(b.ap,'pt'),vot:(a,b)=>(b.vot||0)-(a.vot||0),l:(a,b)=>b.cat.l-a.cat.l,h:(a,b)=>b.cat.h-a.cat.h,b:(a,b)=>b.cat.b-a.cat.b,c:(a,b)=>b.cat.c-a.cat.c,tot:(a,b)=>b.tot-a.tot};
function pautaHTML(p){
  return `<li class="it k-c"><span class="ic">${svg(ICON.cal)}</span><div>
    <p class="tx">${esc(p.t||'Sessão')}</p>${p.x?`<p class="mute" style="margin:4px 0 0;font-size:14px">${esc(p.x)}</p>`:''}
    <div class="mt"><span>${dt(p.d)}</span></div>
    <div class="ft"><span></span>${p.u?`<a class="ext" href="${esc(p.u)}" target="_blank" rel="noopener">Abrir pauta na Câmara ↗</a>`:''}</div></div></li>`;
}

/* ---------- partes comuns ---------- */
function countUp(el,to){ if(!el)return; if(reduce){el.textContent=nf(to);return} const t0=performance.now(),from=Math.round(to*.82);
  const step=t=>{const p=Math.min(1,(t-t0)/900),e=1-Math.pow(1-p,3);el.textContent=nf(Math.round(from+(to-from)*e));if(p<1)requestAnimationFrame(step)};requestAnimationFrame(step)}
const GER=new Date(D.gerh);
function ago(){const m=Math.max(0,Math.round((Date.now()-GER.getTime())/6e4));
  return m<2?'agora mesmo':m<60?`há ${m} minutos`:m<120?'há 1 hora':m<1440?`há ${Math.floor(m/60)} horas`:m<2880?'ontem':`há ${Math.floor(m/1440)} dias`}
document.querySelectorAll('.phead>.eyebrow').forEach(el=>{el.insertAdjacentText('beforeend',` · atualizado em ${GER.toLocaleDateString('pt-BR',{day:'numeric',month:'long'})}`)});
document.querySelectorAll('[data-atualizado]').forEach(el=>{el.textContent=`Dados conferidos na Câmara em ${GER.toLocaleDateString('pt-BR',{day:'numeric',month:'long'})}, às ${GER.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}.`});

/* ================= PÁGINAS ================= */
const P={};

P.inicio=function(){
  $('livet').textContent=`dados conferidos ${ago()}`; setInterval(()=>{$('livet').textContent=`dados conferidos ${ago()}`},6e4);
  const STATS=[
    ['',D.totalPropostas??IT.length,'propostas desde a posse',''],
    ['k-b',D.catot.b||0,'pedidos nos bairros','b'],
    ['k-h',D.catot.h||0,'homenagens','h'],
    ['k-l',D.catot.l||0,'propostas de lei','l']
  ];
  $('stats').innerHTML=STATS.map(([k,n,label,category],i)=>{
    const filter=category ? `?categoria=${category}` : '';
    return `<a class="stat ${k}" href="${BASE}/propostas/${filter}#lista-propostas"><b class="num" id="st${i}">${nf(n)}</b><span>${label}</span><span class="stat-link">Ver registros &rarr;</span></a>`;
  }).join('');
  STATS.forEach(([k,n],i)=>countUp($('st'+i),n));
  $('faces').innerHTML=V.slice().sort(ORD.nome).map(v=>`<li><a href="${urlV(v)}">${foto(v,'')}<span>${esc(v.ap)}</span></a></li>`).join('');
  $('bairros-chips').innerHTML=D.bairros.slice(0,8).map(b=>`<li><a class="chip" href="${BASE}/bairros/?q=${encodeURIComponent(b)}">${esc(b)}</a></li>`).join('');
  if ($('hq-bairros')) $('hq-bairros').replaceChildren(...D.bairros.map(b => new Option(b,b)));
  $('fbq').addEventListener('submit',e=>{e.preventDefault();location.href=BASE+'/bairros/?q='+encodeURIComponent($('hq').value.trim())});
  const PA=D.pautas||[];
  if(PA.length)$('pautas-inicio').innerHTML='<ul class="items">'+PA.map(pautaHTML).join('')+'</ul>'; else $('sessoes-recentes').hidden=true;
  listaReps($('reps'),D.rep.slice(0,CEL?3:6),CEL?3:6);
};

P.vereadores=function(){
  $('vsub').textContent=`Os ${V.length} vereadores em exercício, com a mesma régua: tudo o que cada um apresentou na Câmara desde a posse. Toque em um nome para ver os detalhes.`;
  [...new Set(V.map(v=>v.part).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pt')).forEach(p=>{const o=document.createElement('option');o.value=p;o.textContent=`${p} (${V.filter(v=>v.part===p).length})`;$('partido').appendChild(o)});
  const render=()=>{
    const q=norm($('q').value.trim()),p=$('partido').value,o=$('ordem').value;
    const L=V.filter(v=>(!p||v.part===p)&&(!q||norm(v.ap+' '+v.nome).includes(q))).sort((a,b)=>ORD[o](a,b)||ORD.nome(a,b));
    $('grid').innerHTML=L.length?L.map(vcard).join(''):'<p class="mute">Nenhum vereador com esse nome. Apague a busca ou escolha “Todos”.</p>';
    $('conta').textContent=L.length===V.length?`Mostrando os ${V.length} vereadores.`:`Mostrando ${L.length} de ${V.length} vereadores.`;
  };
  ['q','partido','ordem'].forEach(id=>$(id).addEventListener('input',render)); render();
  const NOMES=[...V].sort(ORD.nome);
  $('csv').addEventListener('click',()=>{
    const C=[['Vereador',v=>v.ap],['Nome completo',v=>v.nome],['Partido',v=>v.part],['Propostas total',v=>v.tot],['Pedidos de melhoria no bairro',v=>v.cat.b],['Cobranças',v=>v.cat.c],
      ['Homenagens',v=>v.cat.h],['Projetos de lei',v=>v.cat.l],['Outras',v=>v.cat.o],...TIPOS.map(t=>[t+' (contagem da Câmara)',v=>v.tp[t]]),['Votos em 2024 (TSE)',v=>v.vot||''],['Página na Câmara',v=>v.url||'']];
    const q=x=>{x=String(x??'');return /[;"\n]/.test(x)?'"'+x.replace(/"/g,'""')+'"':x};
    const linhas=[C.map(c=>c[0]).join(';'),...NOMES.map(v=>C.map(c=>q(c[1](v))).join(';')),'',
      q(`Fonte: Radar Serra Negra (${CONFIG.site.replace(/^https:\/\//, '').replace(/\/$/, '')}), dados abertos oficiais da Câmara Municipal de Serra Negra. Desde ${new Date(D.posse+'T12:00').toLocaleDateString('pt-BR')}, atualizado em ${GER.toLocaleDateString('pt-BR')}.`)];
    const blob=new Blob(['﻿'+linhas.join('\r\n')],{type:'text/csv;charset=utf-8'});
    const u=URL.createObjectURL(blob),l=document.createElement('a');l.href=u;l.download=`radar-serra-negra-vereadores-${GER.toISOString().slice(0,10)}.csv`;
    document.body.appendChild(l);l.click();l.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);
  });
};

P.vereador=function(id){
  const v=V.find(x=>x.id===id); if(!v)return; const i=v.i;
  document.documentElement.style.setProperty('--tint',`hsl(${hue(i)} 85% 94%)`);
  document.documentElement.style.setProperty('--deep',`hsl(${hue(i)} 55% 26%)`);
  $('kpis').innerHTML=`
    <div class="kpi"><span class="eyebrow">Propostas desde a posse</span><b class="num">${nf(v.tot)}</b><span>como autor ou coautor</span></div>
    <div class="kpi"><span class="eyebrow">Pedidos no bairro</span><b class="num" style="color:var(--b)">${nf(v.cat.b)}</b><span>indicações de melhoria à Prefeitura</span></div>
    <div class="kpi"><span class="eyebrow">Cobranças</span><b class="num" style="color:var(--c)">${nf(v.cat.c)}</b><span>perguntas e pedidos de explicação</span></div>
    <div class="kpi"><span class="eyebrow">Propostas de lei</span><b class="num" style="color:var(--l)">${nf(v.cat.l)}</b><span>projetos que criam ou mudam regras</span></div>`;
  const tps=TIPOS.filter(t=>v.tp[t]);
  if(tps.length)$('kpis').insertAdjacentHTML('afterend',`<div class="tipos"><p class="eyebrow">Na contagem por tipo da Câmara, desde a posse</p>
    <ul>${tps.map(t=>`<li><b class="num">${nf(v.tp[t])}</b><span>${esc(t.toLowerCase())}</span></li>`).join('')}</ul>
    <small>Contando também as propostas feitas junto com outros vereadores.${v.url?` <a href="${esc(v.url)}" target="_blank" rel="noopener">Página oficial ↗</a>`:''}</small></div>`);
  // o que propôs
  $('picks').innerHTML=bar5(v)+ORDER.map(c=>`<button class="pick k-${c} num" type="button" data-c="${c}" ${v.cat[c]?'':'disabled'}><i></i><span>${CAT[c][0]}</span><b>${nf(v.cat[c])}</b><span class="ar" aria-hidden="true">›</span></button>`).join('');
  $('picks').addEventListener('click',e=>{const p=e.target.closest('.pick');if(p&&!p.disabled)openCat(p.dataset.c,i)});
  // lista com abas
  const minhas=IT.filter(it=>it[6].includes(i)); let cat='';
  $('tabs').innerHTML=`<li><button class="chip on" type="button" data-k="">Todas<small>${nf(minhas.length)}</small></button></li>`+ORDER.filter(c=>v.cat[c]).map(c=>`<li><button class="chip" type="button" data-k="${c}">${CAT[c][3]}s<small>${nf(v.cat[c])}</small></button></li>`).join('').replace('Proposta de leis','Propostas de lei');
  const draw=()=>pager($('lista'),cat?minhas.filter(it=>it[4]===cat):minhas,false,CEL?5:10);
  $('tabs').addEventListener('click',e=>{const b=e.target.closest('[data-k]');if(!b)return;cat=b.dataset.k;$('tabs').querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x===b));draw()}); draw();
  // onde pediu
  const b=minhas.filter(it=>it[4]==='b');
  const bai=[...b.reduce((m,it)=>it[10]?m.set(it[10],(m.get(it[10])||0)+1):m,new Map())].sort((a,b)=>b[1]-a[1]).filter(x=>x[1]>=2).slice(0,6);
  const th=themeCount(b).slice(0,6), mx=bai.length?bai[0][1]:1;
  $('onde').innerHTML=(bai.length?`<p class="h3" style="margin-top:0">Bairros com mais pedidos</p><ol class="rank">${bai.map(([n,c])=>`<li><span class="ti">${svg(ICON.pin,16)}</span><span class="nm"><a href="${BASE}/bairros/?q=${encodeURIComponent(n)}">${esc(n)}</a></span><b class="num">${nf(c)}</b><span class="br"><i style="width:${c/mx*100}%"></i></span></li>`).join('')}</ol>`:`<p class="mute">${b.length?'Poucos pedidos com bairro identificado no texto.':'Nenhum pedido de melhoria em bairro desde a posse.'}</p>`)
    +(th.length?`<p class="h3">Assuntos mais pedidos</p><ul class="themes">${th.map(([k,n])=>`<li><span class="ti">${svg(ICON[TH[k][1]],18)}</span><span>${esc(TH[k][0])}</span><b class="num">${nf(n)}</b></li>`).join('')}</ul>`:'');
  // onde foi votado em 2024 (TSE) x onde pede
  if($('loc')&&v.loc&&v.loc.length){
    const lc=v.lc, m=D.locm, tipo=m==null?'':lc>=m+5?'concentrado em poucos locais':lc<=m-5?'espalhado pela cidade':'nem concentrado nem espalhado';
    $('locc').innerHTML=`${v.vot?`${esc(v.ap)} teve <b class="num">${nf(v.vot)}</b> votos em 2024. `:''}<b class="num">${lc}%</b> deles vieram destes 5 locais de votação: um voto ${tipo}${m!=null?` (a média da Câmara é <span class="num">${m}%</span>)`:''}. Em cada local, quantos pedidos de melhoria saíram do gabinete para aquele bairro.`;
    $('loc').innerHTML=v.loc.map((r,n)=>{const p=r[4]==null?`<p class="lpd mute">Sem pedidos com esse nome de bairro</p>`:r[4]?`<p class="lpd ok"><b class="num">${nf(r[4])}</b> ${r[4]===1?'pedido de melhoria':'pedidos de melhoria'} aqui</p>`:`<p class="lpd no"><b class="num">0</b> pedidos de melhoria aqui</p>`;
      return `<article class="lcard"><span class="lnum">${n+1}º</span><b class="lpc num">${String(r[3]).replace('.',',')}%</b><span class="lvt num">${nf(r[2])} votos</span><h3>${esc(r[1]||'—')}</h3><p class="lsc">${esc(r[0])}</p>${p}</article>`}).join('');
  }
  const meusReps=D.rep.filter(g=>g.items.some(it=>it[6].includes(i)));
  $('reps-v').innerHTML=''; listaReps($('reps-v'),meusReps,3);
  $('reps-n').textContent=meusReps.length?`${nf(meusReps.length)} ruas com pedidos repetidos têm pelo menos um pedido de ${v.ap}.`:'';
  // compartilhar
  const link=new URL(urlV(v),SITE).href, txt=`${v.ap} desde a posse: ${nf(v.tot)} propostas na Câmara de Serra Negra. Veja tudo no Radar Serra Negra: ${link}`;
  $('wa').href='https://wa.me/?text='+encodeURIComponent(txt);
  $('cp').onclick=async e=>{try{await navigator.clipboard.writeText(link);e.target.textContent='Link copiado'}catch(_){e.target.textContent=link}};
  // anterior / próximo
  const S=V.slice().sort(ORD.nome), k=S.indexOf(v), ant=S[(k+S.length-1)%S.length], prox=S[(k+1)%S.length];
  $('pn').innerHTML=`<a href="${urlV(ant)}">← ${esc(ant.ap)}</a><a href="${BASE}/vereadores/">Todos os vereadores</a><a href="${urlV(prox)}">${esc(prox.ap)} →</a>`;
};

P.bairros=function(){
  $('bl').innerHTML=D.bairros.slice(0,300).map(b=>`<option value="${esc(b)}"></option>`).join('');
  $('chips').innerHTML=D.bairros.slice(0,14).map(b=>`<li><button class="chip" type="button" data-b="${esc(b)}">${esc(b)}</button></li>`).join('');
  let tm;
  function bairro(q){
    const host=$('bres'), k=norm(q.trim()), city=k.length===0;
    $('chips').querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',norm(x.dataset.b)===k));
    try{history.replaceState(null,'',location.pathname+(city?'':'?q='+encodeURIComponent(q.trim()))+location.hash)}catch(_){}
    if(!city&&k.length<3){host.innerHTML='<div class="panel"><p class="mute" style="margin:0">Continue digitando: preciso de pelo menos 3 letras.</p></div>';return}
    const items=city?IT:IT.filter(it=>it.n.includes(k));
    if(!items.length){host.innerHTML=`<div class="panel"><p class="mute" style="margin:0">Nada encontrado para “${esc(q)}”. Confira a grafia ou tente só uma parte do nome.</p></div>`;return}
    const cnt=new Map(); items.forEach(it=>it[6].forEach(a=>cnt.set(a,(cnt.get(a)||0)+1)));
    const top=[...cnt.entries()].sort((a,b)=>b[1]-a[1]), mx=top.length?top[0][1]:1;
    const th=themeCount(items.filter(it=>it[4]==='b'||it[4]==='c')).slice(0,city&&CEL?3:5);
    const reps=city?[]:D.rep.filter(g=>g.items.some(it=>it.n.includes(k))).slice(0,3);
    host.innerHTML=`<div class="panel">
     <div class="ph"><span class="big num">${nf(items.length)}</span><p>${city?'propostas para <b>a cidade inteira</b> até agora':`${items.length===1?'proposta cita':'propostas citam'} <b>${esc(q.trim())}</b> até agora`}</p></div>
     <div class="two">
       ${city||!top.length?'':`<div><h3>Quem mais pediu</h3><ol class="rank">${top.slice(0,5).map(([a,n])=>`<li>${av(a)}<span class="nm"><a href="${urlV(V[a])}">${esc(V[a].ap)}</a>${V[a].part?` <span class="mute" style="font-weight:400">· ${esc(V[a].part)}</span>`:''}</span><b class="num">${nf(n)}</b><span class="br"><i style="width:${n/mx*100}%"></i></span></li>`).join('')}</ol>
         ${top.length>5?`<p class="mute" style="font-size:13.5px;margin:10px 0 0">Mais ${top.length-5} vereadores também citaram.</p>`:''}</div>`}
       ${th.length?`<div><h3>O que mais pedem</h3><ul class="themes">${th.map(([t,n])=>`<li><span class="ti">${svg(ICON[TH[t][1]],18)}</span><span>${esc(TH[t][0])}</span><b class="num">${nf(n)}</b></li>`).join('')}</ul></div>`:''}
       ${city&&!CEL&&D.bairros.length?`<div><h3>Bairros mais citados</h3><ul class="themes">${D.bairros.slice(0,5).map((b,i)=>`<li><span class="ti">${svg(ICON.pin,18)}</span><button class="lnk" type="button" data-b="${esc(b)}">${esc(b)}</button><b class="num">${nf(D.bairrosn[i])}</b></li>`).join('')}</ul></div>`:''}
     </div>
     ${reps.length?`<p class="h3" style="margin-top:24px">Problemas que voltam aqui</p><div class="reps">${reps.map(repHTML).join('')}</div>`:''}
     <p class="h3" style="margin-top:24px">${city?'As propostas mais recentes da cidade':'Os pedidos mais recentes'}</p><div id="blist"></div></div>`;
    const list=$('blist');
    const topics=themeCount(items).filter(([key])=>Object.hasOwn(TH,key));
    const resultCount=document.createElement('span');
    resultCount.className='bairro-topic-count';
    resultCount.setAttribute('role','status');
    const renderList=(key='')=>{
      const matches=key?items.filter(it=>it[8]===key):items;
      resultCount.textContent=nf(matches.length)+(matches.length===1?' proposta':' propostas');
      pager(list,matches,true,city&&CEL?2:4);
    };
    if(topics.length>1){
      const bar=document.createElement('div'); bar.className='bairro-topic-bar';
      const field=document.createElement('div'); field.className='bairro-topic-field';
      const label=document.createElement('label'); label.htmlFor='bairro-topic'; label.textContent='Filtrar por assunto';
      const select=document.createElement('select'); select.id='bairro-topic'; select.className='bairro-topic-select';
      select.append(new Option('Todos os assuntos',''));
      topics.forEach(([key])=>select.append(new Option(TH[key][0],key)));
      select.addEventListener('change',()=>renderList(select.value));
      field.append(label,select); bar.append(field,resultCount); list.before(bar);
    }
    renderList();
  }
  $('bq').addEventListener('input',e=>{clearTimeout(tm);tm=setTimeout(()=>bairro(e.target.value),150)});
  document.addEventListener('click',e=>{const b=e.target.closest('[data-b]');if(b){$('bq').value=b.dataset.b;bairro(b.dataset.b);$('busca').scrollIntoView({block:'start',behavior:reduce?'auto':'smooth'})}});
  const q0=new URLSearchParams(location.search).get('q')||''; $('bq').value=q0; bairro(q0);
  listaReps($('reps'),D.rep,CEL?4:9);
};

P.propostas=function(){
  const tot=ORDER.reduce((s,c)=>s+(D.catot[c]||0),0), lei=D.catot.l||0, hom=D.catot.h||0;
  $('hsub').textContent=`São ${nf(tot)} propostas apresentadas na Câmara desde a posse. `+(lei?`Para cada proposta de lei, ${(hom/lei).toLocaleString('pt-BR',{maximumFractionDigits:1})} homenagens. `:'')+'Toque em um grupo para ler cada uma.';
  $('split').innerHTML=ORDER.map(c=>`<i class="k-${c}" style="flex:${D.catot[c]||0} 1 0"></i>`).join('');
  $('cats').innerHTML=ORDER.map(c=>`<button class="cat k-${c}" type="button" data-c="${c}"><span class="ci">${svg(ICON[CAT[c][2]],26)}</span><span class="cv num">${nf(D.catot[c]||0)}</span><span class="cn">${CAT[c][0]} <span class="now">até agora</span></span><span class="cd">${CAT[c][1]}</span><span class="go">Ver todas →</span></button>`).join('');
  $('cats').addEventListener('click',e=>{const b=e.target.closest('[data-c]');if(b)openCat(b.dataset.c,null)});
  const category=new URLSearchParams(location.search).get('categoria');
  let tm, cat=ORDER.includes(category)?category:'';
  $('ptabs').innerHTML=`<li><button class="chip${cat?'':' on'}" type="button" data-k="">Todas</button></li>`+ORDER.map(c=>`<li><button class="chip${cat===c?' on':''}" type="button" data-k="${c}">${CAT[c][0]}</button></li>`).join('');
  const draw=()=>{const k=norm($('pq').value.trim());const L=IT.filter(it=>(!cat||it[4]===cat)&&(!k||it.n.includes(k)));
    $('pcount').textContent=`${nf(L.length)} ${L.length===1?'proposta':'propostas'}`;pager($('plista'),L,true,CEL?6:12)};
  $('ptabs').addEventListener('click',e=>{const b=e.target.closest('[data-k]');if(!b)return;cat=b.dataset.k;$('ptabs').querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x===b));draw()});
  $('pq').addEventListener('input',()=>{clearTimeout(tm);tm=setTimeout(draw,180)}); draw();
  const T=D.tipos||[], mt=T.length?T[0][1]:1;
  $('ptipos').innerHTML=T.map(([t,n],i)=>`<li><span class="num mute">${i+1}</span><span class="nm">${esc(t)}</span><b class="num">${nf(n)}</b><span class="br"><i style="width:${n/mt*100}%"></i></span></li>`).join('');
  $('psem').textContent=D.semaut?`${nf(D.semaut)} ${D.semaut===1?'proposta não tem':'propostas não têm'} vereador em exercício na autoria (por exemplo, “Câmara Municipal” ou a Prefeitura). Elas aparecem na busca, mas não contam para nenhum vereador.`:'';
};

P.sessoes=function(){
  const PA=D.pautas||[];
  $('pautas-n').textContent=PA.length?`${nf(PA.length)} ${PA.length===1?'pauta publicada':'pautas publicadas'} desde ${dt(D.posse)}.`:'';
  if(!PA.length){$('pautas').innerHTML='<p class="mute">Nenhuma pauta encontrada nos dados abertos desde a posse.</p>';return}
  let n=0; const step=CEL?10:20;
  $('pautas').innerHTML='<ul class="items"></ul>';
  const ul=$('pautas').firstChild, btn=document.createElement('button'); btn.className='more'; btn.type='button';
  const add=()=>{ul.insertAdjacentHTML('beforeend',PA.slice(n,n+step).map(pautaHTML).join(''));n+=step;
    if(n>=PA.length)btn.remove();else btn.textContent=`Mostrar mais ${Math.min(step,PA.length-n)} de ${nf(PA.length-n)}`};
  btn.addEventListener('click',add); if(PA.length>step)$('pautas').appendChild(btn); add();
};

P.comparar=function(){
  const NOMES=[...V].sort(ORD.nome), qs=new URLSearchParams(location.search);
  const pega=(k,d)=>V.find(v=>v.id===qs.get(k))||d;
  let a=pega('a',NOMES[0]), b=pega('b',NOMES.find(v=>v!==a));
  const bairrosDe=v=>new Set(IT.filter(it=>it[4]==='b'&&it[10]&&it[6].includes(v.i)).map(it=>it[10])).size;
  const sozinho=v=>IT.filter(it=>it[6].length===1&&it[6][0]===v.i).length;
  const G=[
    ['Propostas desde a posse',[['Total de propostas',v=>v.tot,'como autor ou coautor'],['Propostas sem coautoria',sozinho,'nenhum outro vereador assina junto'],
      ['Pedidos de melhoria no bairro',v=>v.cat.b,'tapar buraco, podar árvore, trocar lâmpada'],['Cobranças à Prefeitura',v=>v.cat.c,'perguntas e pedidos de explicação'],
      ['Projetos de lei',v=>v.cat.l,'propostas de novas regras para a cidade'],['Homenagens',v=>v.cat.h,'parabéns, títulos, votos de pesar, nomes de rua']]],
    ['Onde pede',[['Bairros citados nos pedidos',bairrosDe,'bairros diferentes lidos no texto dos pedidos de melhoria']]],
    ...(V.some(v=>v.vot)?[['Eleição de 2024',[['Votos recebidos',v=>v.vot||0,'resultado oficial do TSE']]]]:[]),
    ['Na contagem por tipo da Câmara',TIPOS.filter(t=>V.some(v=>v.tp[t])).map(t=>[t,v=>v.tp[t],'',1])]];
  const card=(v,lado)=>`<div class="vs-c" style="--h:${hue(v.i)}">${v.foto?`<img src="${BASE}/fotos/${esc(v.foto)}.jpg" alt="Foto de ${esc(v.ap)}">`:`<span class="vs-ph">${esc(v.in)}</span>`}
    <a class="vs-n" href="${urlV(v)}">${esc(v.ap)}</a><span class="pill">${esc(v.part||'sem partido informado')}${v.mesa?' · '+esc(v.mesa):''}</span>
    <label class="vs-s"><span class="sr">Trocar vereador</span><select data-l="${lado}">${NOMES.map(x=>`<option value="${esc(x.id)}"${x===v?' selected':''}>${esc(x.ap)}</option>`).join('')}</select></label></div>`;
  const desenha=foco=>{
    $('vs').innerHTML=card(a,'a')+'<span class="vs-x" aria-hidden="true">×</span>'+card(b,'b');
    $('cmp').style.cssText=`--ha:${hue(a.i)};--hb:${hue(b.i)}`;
    const hd=`<div class="cg-hd" aria-hidden="true"><span class="a">${esc(a.ap)}</span><span class="b">${esc(b.ap)}</span></div>`;
    const juntos=a===b?0:IT.filter(it=>it[6].includes(a.i)&&it[6].includes(b.i)).length;
    $('cmp').innerHTML=G.map(([tit,L])=>`<div class="cg"><h2>${tit}</h2>${hd}${L.map(([n,f,ex,ocultaZero])=>{
      const x=f(a), y=f(b), max=Math.max(1,x,y), w=n=>Math.max(2,Math.round(n/max*100));
      if(ocultaZero&&!x&&!y)return '';
      return `<div class="cr"><div class="cr-l">${esc(n)}${ex?`<small>${ex}</small>`:''}</div>
        <div class="cr-v a"><b class="num">${nf(x)}</b><small></small><i style="--w:${w(x)}%"></i></div>
        <div class="cr-v b"><b class="num">${nf(y)}</b><small></small><i style="--w:${w(y)}%"></i></div></div>`}).join('')}</div>`).join('')
      +(a===b?'':`<div class="cg cg-j"><h2>Os dois juntos</h2><p>${juntos?`<b class="num">${nf(juntos)}</b> ${juntos===1?'proposta foi apresentada':'propostas foram apresentadas'} pelos dois juntos, como coautores, desde a posse.`:'Os dois não apresentaram nenhuma proposta juntos desde a posse.'}</p></div>`);
    $('vs').querySelectorAll('select').forEach(s=>s.addEventListener('change',()=>{const v=V.find(x=>x.id===s.value);if(s.dataset.l==='a')a=v;else b=v;
      history.replaceState(null,'',`?a=${encodeURIComponent(a.id)}&b=${encodeURIComponent(b.id)}`);desenha(s.dataset.l)}));
    if(foco)$('vs').querySelector(`select[data-l="${foco}"]`).focus();
  };
  const copy=$('cmp-copy');
  if(copy) copy.addEventListener('click',async()=>{
    const url=new URL('comparar/',SITE); url.searchParams.set('a',a.id); url.searchParams.set('b',b.id);
    const status=$('cmp-copy-status');
    try{await navigator.clipboard.writeText(url.href);status.textContent='Link copiado.'}
    catch(_){const link=document.createElement('a');link.href=url.href;link.textContent=url.href;status.replaceChildren(link)}
  });
  desenha();
};

P.prefeitura=function(){
  const F=window.PF; if(!F)return;
  const MES=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
  const MESX=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];
  const mi=v=>{const a=Math.abs(v);return a>=1e9?(v/1e9).toLocaleString('pt-BR',{maximumFractionDigits:2})+' bi':a>=1e6?(v/1e6).toLocaleString('pt-BR',{maximumFractionDigits:1})+' mi':a>=1e3?Math.round(v/1e3).toLocaleString('pt-BR')+' mil':nf(v)};
  const R=v=>'R$ '+mi(v);
  const cnpj=d=>d.length===14?`${d.slice(0,2)}.${d.slice(2,5)}.${d.slice(5,8)}/${d.slice(8,12)}-${d.slice(12)}`:d;
  const anos=Object.keys(F.anos).sort(); let ano=anos[anos.length-1];
  const ate=a=>{const L=F.meses.filter(m=>m[0].startsWith(a));const u=+L[L.length-1][0].slice(5);return u===12?`em ${a}`:`de janeiro a ${MESX[u-1]} de ${a}`};
  $('pf-anos').innerHTML=anos.map(a=>`<li><button class="chip" type="button" data-a="${a}">${a}</button></li>`).join('');
  $('pf-anos').addEventListener('click',e=>{const b=e.target.closest('[data-a]');if(b){ano=b.dataset.a;draw()}});
  const draw=()=>{
    const Y=F.anos[ano], per=ate(ano);
    $('pf-anos').querySelectorAll('.chip').forEach(c=>c.classList.toggle('on',c.dataset.a===ano));
    $('pf-kpis').innerHTML=`
      <div class="kpi"><span class="eyebrow">Entrou</span><b class="num" style="color:var(--l)">${R(Y.rec)}</b><span>impostos, taxas e repasses, ${per}</span></div>
      <div class="kpi"><span class="eyebrow">Pago pela Prefeitura</span><b class="num" style="color:var(--b)">${R(Y.pago)}</b><span>dinheiro que saiu do caixa, ${per}</span></div>
      <div class="kpi"><span class="eyebrow">Empresas que receberam</span><b class="num">${nf(Y.nforn)}</b><span>as 10 maiores ficaram com ${Math.round(Y.top10/Y.forn_tot*100)}% do que foi pago a empresas</span></div>
      <div class="kpi"><span class="eyebrow">Custo da Câmara</span><b class="num" style="color:var(--c)">${R(Y.cam)}</b><span>pago pela Câmara, ${per}</span></div>`;
    // mês a mês
    const L=F.meses.filter(m=>m[0].startsWith(ano)), mx=Math.max(...L.map(m=>Math.max(m[1],m[2])),1);
    $('pf-mes-sub').textContent=`Em milhões de reais, ${per}. Os meses seguintes aparecem quando a Prefeitura enviar os dados ao TCE.`;
    $('pf-meses').innerHTML=Array.from({length:12},(_,i)=>{const m=L.find(x=>+x[0].slice(5)===i+1);
      return `<div class="pm${m?'':' vz'}" title="${m?`${MESX[i]}: entrou ${R(m[1])}, pago ${R(m[2])}`:'sem dados ainda'}"><div class="pm-b">${m?`<i class="e" style="height:${m[1]/mx*100}%"><span>${Math.round(m[1]/1e6)}</span></i><i class="s" style="height:${m[2]/mx*100}%"><span>${Math.round(m[2]/1e6)}</span></i>`:''}</div><small>${MES[i]}</small></div>`}).join('');
    // receitas
    const tg=Y.grp.reduce((s,g)=>s+g[1],0)||1;
    $('pf-grp').innerHTML=Y.grp.slice(0,10).map((g,i)=>`<li><span class="num mute">${i+1}</span><span class="nm">${esc(g[0])}</span><b class="num">${R(g[1])}</b><span class="br"><i style="width:${g[1]/Y.grp[0][1]*100}%;background:var(--l)"></i></span></li>`).join('')
      +(Y.grp.length>10?`<li><span></span><span class="nm mute">Outras ${Y.grp.length-10} fontes</span><b class="num mute">${R(Y.grp.slice(10).reduce((s,g)=>s+g[1],0))}</b></li>`:'');
    // câmara
    $('pf-cam').innerHTML=`<p class="pf-big num">${R(Y.cam)}</p><p style="margin:0 0 10px">foi o que a Câmara pagou ${per}: cerca de <b>${R(Y.cam/Y.n)}</b> por mês.</p>
      <p class="mute" style="margin:0;font-size:14px">É o equivalente a ${(Y.cam/Y.pago*100).toLocaleString('pt-BR',{maximumFractionDigits:1})}% do que a Prefeitura pagou no mesmo período. Inclui salários dos vereadores e funcionários, contas e serviços. <a href="${BASE}/vereadores/">Veja o que cada vereador propôs</a>.</p>`;
    // fornecedores
    $('pf-forn-sub').textContent=`As empresas que mais receberam ${per}. Ao todo, ${nf(Y.nforn)} empresas receberam pagamentos.`;
    let n=10; const mxf=Y.top[0]?Y.top[0][2]:1;
    const lista=()=>{$('pf-forn').innerHTML=Y.top.slice(0,n).map((f,i)=>`<li><span class="num mute">${i+1}</span><div><b>${esc(f[1])}</b><small>CNPJ ${cnpj(f[0])} · ${nf(f[3])} ${f[3]===1?'pagamento':'pagamentos'}</small><span class="br"><i style="width:${f[2]/mxf*100}%"></i></span></div><b class="num">${R(f[2])}</b></li>`).join('');
      $('pf-mais').hidden=n>=Y.top.length};
    $('pf-mais').onclick=()=>{n=Y.top.length;lista()}; lista();
    $('pf-pf').innerHTML=`Fora desta lista: <b>${R(Y.prop)}</b> pagos em nome da própria Prefeitura, em geral salários e repasses internos, e <b>${R(Y.pf)}</b> em ${nf(Y.npf)} pagamentos a pessoas físicas. Os nomes das pessoas não são mostrados, para proteger a privacidade.`;
  };
  draw();
};

P.sobre=function(){};

window.Radar=P;
})();
