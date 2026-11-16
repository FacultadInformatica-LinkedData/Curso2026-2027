const $ = (id) => document.getElementById(id);
function element(tag, text, className){const e=document.createElement(tag);if(text!==null)e.textContent=text;if(className)e.className=className;return e;}
function appendExternal(parent,label,url){if(!url || !/^https?:\/\//i.test(url))return;const a=element('a',label+' ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';parent.appendChild(a);}
async function fetchData(url){const r=await fetch(url);if(!r.ok)throw new Error('Error al cargar '+url);return r.json();}
function showParks(data){const target=$('results');target.replaceChildren();$('result-count').textContent=data.total;if(!data.total){target.appendChild(element('div','No se han encontrado parques. Prueba con otro nombre o distrito.','empty'));return;}
 for(const park of data.parks){const card=element('article',null,'park-card');card.appendChild(element('div','🌳','park-icon'));const body=element('div');body.appendChild(element('h3',park.name));body.appendChild(element('p','📍 Distrito: '+park.district));appendExternal(body,'Ayuntamiento de Madrid',park.url);appendExternal(body,'Wikidata',park.wikidata);card.appendChild(body);target.appendChild(card);}}
async function search(){const params=new URLSearchParams({name:$('name').value,district:$('district').value});try{showParks(await fetchData('/api/parks?'+params));}catch(err){$('results').textContent='Error: '+err.message;}}
async function initialize(){try{const districts=await fetchData('/api/districts');
for(const d of districts.districts){const opt=element('option',d.name);opt.value=d.name;$('district').appendChild(opt);}

await search();}catch(err){$('results').textContent='No se han podido cargar los datos: '+err.message;}}
$('search-form').addEventListener('submit',(ev)=>{ev.preventDefault();search();});initialize();
