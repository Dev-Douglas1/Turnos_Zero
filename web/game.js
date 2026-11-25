const RAW = 'https://raw.githubusercontent.com/Dev-Douglas1/Turnos_Zero/main/';
const missions = [
  ['loja_24h','Loja 24 horas','LOCAL 01',2],
  ['edificio_9','Edifício Residencial 9','LOCAL 02',3],
  ['cinema_vazio','Última Sessão','LOCAL 03',3],
  ['laboratorio','Protocolo de Contenção','LOCAL 04',3]
];
const diffs = {
  facil:['ESTAGIÁRIO',5,2,50],
  medio:['EFETIVO',4,1,75],
  dificil:['TERCEIRIZADO',3,1,100]
};
let data = null, ready = false, idx = 0, diff = 'facil', s = {};
const $ = id => document.getElementById(id);
function screen(id) {
  document.querySelectorAll('.screen').forEach(el => el.classList.remove('active'));
  $(id).classList.add('active');
}
async function boot() {
  const startButton = $('start');
  startButton.disabled = true;
  startButton.textContent = 'CARREGANDO ARQUIVOS...';
  try {
    const response = await fetch(RAW + 'dados/objetos_cenas.json', {cache:'no-store'});
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const json = await response.json();
    if (!json.scenes || missions.some(m => !json.scenes[m[0]])) throw new Error('Dados de cenas incompletos');
    data = json;
    ready = true;
    startButton.disabled = false;
    startButton.textContent = 'INICIAR EXPEDIENTE →';
  } catch (error) {
    console.error('Falha ao carregar TURNOS ZERO:', error);
    $('intro').innerHTML = '<p>ARQUIVO INDISPONÍVEL</p><h2>Não foi possível carregar o jogo.</h2><p>Verifique sua conexão e recarregue a página. Se o problema continuar, os arquivos de dados precisam ser corrigidos.</p><button onclick="location.reload()">TENTAR NOVAMENTE</button>';
  }
}
$('start').onclick = () => { if (ready) screen('tutorial'); };\n$('tutorialNext').onclick = () => screen('contract');
document.querySelectorAll('[data-d]').forEach(button => {
  button.onclick = () => { if (!ready) return; diff = button.dataset.d; start(); };
});
function start() {
  if (!ready) return;
  const mission = missions[idx];
  s = {
    st:diffs[diff][1], pressure:0, seen:[], changed:{}, proof:[], logs:[],
    radio:3, camera:3, battery:100, shelter:false, fail:0, cash:diffs[diff][3]
  };
  $('tag').textContent = 'CONTRATO ' + (idx + 1);
  $('mission').textContent = mission[1];\n  $('objectiveText').textContent = 'Toque nos objetos, leia as pistas e reúna pelo menos ' + mission[3] + ' evidências antes de encerrar.';\n  $('objectiveProgress').textContent = '0 / ' + mission[3] + ' evidências';
  $('sceneCode').textContent = mission[2];
  $('reportTitle').textContent = 'Aguardando inspeção';
  $('reportText').textContent = 'Clique nos objetos do ambiente para examinar. ' + mission[1] + ' — ocorrência anômala registrada.';
  $('action').innerHTML = '';
  $('log').innerHTML = '';
  document.querySelectorAll('.tab').forEach(tab => tab.classList.add('hidden'));
  $('report').classList.remove('hidden');
  draw(); hud(); screen('game'); log('Contrato iniciado: ' + mission[1]);
}
function svgAsset(path) { return RAW + path.replace(/\.png$/i, '.svg'); }
function draw() {
  const id = missions[idx][0], scene = data.scenes[id];
  const background = {
    loja_24h:'loja_24_horas', edificio_9:'edificio_residencial',
    cinema_vazio:'cinema_ultima_sessao', laboratorio:'laboratorio_experimental'
  }[id];
  const el = $('scene');
  el.innerHTML = '';
  el.style.backgroundImage = 'linear-gradient(#0002,#0003),url("' + RAW + 'assets/ambientes/' + background + '.svg")';
  scene.objects.filter(object => object.visible).sort((a,b) => a.z-b.z).forEach(object => {
    const img = document.createElement('img');
    img.className = 'object';
    const changedAsset = s.changed[object.id] && object.asset_states && object.asset_states['1'];
    img.src = svgAsset('assets/objetos/' + (changedAsset || object.asset));
    img.onerror = () => { img.onerror = null; img.src = RAW + 'assets/objetos/' + (changedAsset || object.asset); };
    img.alt = object.label || '';
    img.style.cssText = 'left:'+(object.x*100)+'%;top:'+(object.y*100)+'%;width:'+(object.w*100)+'%;height:'+(object.h*100)+'%;z-index:'+object.z;
    el.append(img);
  });
  scene.hotspots.forEach(hotspot => {
    const button = document.createElement('button');
    const [x,y,right,bottom] = hotspot.bounds;
    button.className = 'hotspot' + (s.seen.includes(hotspot.id) ? ' seen' : '');
    button.title = 'Toque para investigar: ' + hotspot.label;
    button.setAttribute('aria-label','Examinar ' + hotspot.label);
    button.style.cssText = 'left:'+(x*100)+'%;top:'+(y*100)+'%;width:'+((right-x)*100)+'%;height:'+((bottom-y)*100)+'%';
    button.onclick = () => inspect(hotspot);
    el.append(button);
  });
  $('count').textContent = s.proof.length + ' EVIDÊNCIAS';\n  $('objectiveProgress').textContent = Math.min(s.proof.length, missions[idx][3]) + ' / ' + missions[idx][3] + ' evidências';
}
function inspect(hotspot) {
  const done = !!s.changed[hotspot.object];
  $('reportTitle').textContent = hotspot.label;
  $('reportText').textContent = hotspot.finding;
  $('action').innerHTML = '';
  if (!s.seen.includes(hotspot.id)) {
    s.seen.push(hotspot.id);
    s.proof.push({n:hotspot.label,t:hotspot.finding});
    s.pressure = Math.min(100,s.pressure+8);
    log('Evidência registrada: ' + hotspot.label);
  }
  const action = document.createElement('button');
  action.className = 'actionbtn';
  action.textContent = done && !hotspot.interaction.repeatable ? '✓ INTERAÇÃO REGISTRADA' : hotspot.interaction.label;
  action.disabled = done && !hotspot.interaction.repeatable;
  action.onclick = () => manipulate(hotspot);
  $('action').append(action);
  draw(); hud();
}
function manipulate(hotspot) {
  const first = !s.changed[hotspot.object];
  s.changed[hotspot.object] = true;
  const response = hotspot.interaction.responses[first ? 1 : 0] || hotspot.finding;
  $('reportText').textContent = response;
  if (first) {
    s.proof.push({n:hotspot.label+' — manipulação',t:response});
    log('Objeto manipulado: ' + hotspot.label);
  }
  s.pressure = Math.min(100,s.pressure+12);
  if (s.pressure >= 100) {
    s.st--; s.pressure = 35;
    $('reportText').textContent += ' A presença percebeu você. Estabilidade reduzida.';
    log('ALERTA: presença detectada.');
  }
  draw(); hud();
  if (s.st <= 0) end(false,'A presença alcançou você antes do encerramento do contrato.');
}
function log(message) {
  s.logs.unshift(message);
  $('log').innerHTML = s.logs.slice(0,6).map(item => '› ' + item).join('<br>');
}
function hud() {
  $('stability').textContent = '♥ '.repeat(Math.max(0,s.st)) + '♡ '.repeat(Math.max(0,diffs[diff][1]-s.st));
  $('pressure').textContent = s.pressure + '%';
  $('cash').textContent = 'R$ ' + s.cash.toLocaleString('pt-BR');
  $('count').textContent = s.proof.length + ' EVIDÊNCIAS';
  $('proofs').innerHTML = s.proof.length ? s.proof.map(p => '<p><b>'+p.n+'</b><br>'+p.t+'</p>').join('') : 'Nenhuma evidência registrada.';
}
document.querySelectorAll('[data-tab]').forEach(button => {
  button.onclick = () => {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.add('hidden'));
    $(button.dataset.tab).classList.remove('hidden');
  };
});
function msg(message) { $('toolout').textContent = message; log(message); }
function useTool(key, message) {
  if (!s[key] || s[key] <= 0) return msg('Sem usos restantes.');
  s[key]--;
  msg(message + ' Restam ' + s[key] + '.');
}
$('radio').onclick = () => useTool('radio','CENTRAL: Não confie em reflexos. Registre evidências e evite interagir duas vezes com o mesmo fenômeno.');
$('camera').onclick = () => {
  if (s.camera <= 0) return msg('Câmera sem registros.');
  s.camera--;
  s.proof.push({n:'Fotografia de campo',t:'Uma silhueta aparece no limite do enquadramento.'});
  msg('FOTO REGISTRADA. Silhueta detectada. Restam ' + s.camera + ' fotos.'); hud();
};
$('cctv').onclick = () => msg('CFTV // CANAIS 01–06: canal 05 mostra o ambiente vazio. Canal 06 registra você de costas — embora não exista câmera nessa posição.');
$('flash').onclick = () => {
  if (s.battery <= 0) return msg('Bateria da lanterna esgotada.');
  s.battery = Math.max(0,s.battery-15);
  msg('LANTERNA: bateria ' + s.battery + '%.');
};
$('shelter').onclick = () => {
  if (s.shelter) return msg('Abrigo já utilizado neste contrato.');
  s.shelter = true; s.pressure = Math.max(0,s.pressure-35);
  msg('ABRIGO UTILIZADO. Pressão anômala reduzida.'); hud();
};
$('finish').onclick = () => {
  if (s.proof.length < missions[idx][3]) {
    s.fail++; s.st--; s.pressure = Math.min(100,s.pressure+15);
    log('Ocorrência encerrada sem evidências suficientes.'); hud();
    if (s.st <= 0 || s.fail >= diffs[diff][2]) end(false,'O protocolo foi encerrado sem evidências suficientes. Falha crítica registrada.');
    else { $('reportTitle').textContent='Relatório incompleto'; $('reportText').textContent='Evidências insuficientes. A estabilidade foi reduzida. Continue investigando.'; }
    return;
  }
  end(true,'Ocorrência concluída. As evidências foram anexadas ao relatório e o pagamento foi autorizado.');
};
function end(success,message) {
  screen('end');
  $('endtitle').textContent = success ? 'EXPEDIENTE CONCLUÍDO' : 'CONTRATO ENCERRADO';
  $('endtext').textContent = message;
  $('stats').textContent = 'PROVAS '+s.proof.length+'   /   ESTABILIDADE '+s.st+'   /   CRÉDITO R$ '+(success?s.cash:0);
  $('again').textContent = success ? (idx<3?'ACEITAR PRÓXIMO CONTRATO →':'REINICIAR CAMPANHA →') : 'TENTAR NOVAMENTE →';
  $('again').onclick = () => { if (success && idx<3) idx++; else if (success) idx=0; start(); };
}
boot();
