const $ = id => document.getElementById(id);
let image = null, busy = false, visionReady = false, liveEnabled = false;
let liveTimer = null, frameOperation = null, frameEpoch = 0, lastCameraAt = null;
let registrationData = null, personRead = 0;
const notice = (text, error = false) => { $('notice').textContent = text; $('notice').className = error ? 'error' : ''; };
async function api(path, body, method = 'POST') {
  let response;
  try { response = await fetch('/api/' + path, body === undefined ? {} : {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}); }
  catch (_) { $('serverStatus').textContent = 'Bağlantı yok'; $('ollamaStatus').textContent = 'Durum bilinmiyor'; throw Error('Python sunucusuna ulaşılamıyor. Terminalde sunucuyu yeniden başlat ve sayfayı yenile.'); }
  $('serverStatus').textContent = 'Bağlı';
  let data;
  try { data = await response.json(); } catch (_) { throw Error('Sunucu beklenmeyen yanıt verdi (HTTP ' + response.status + '). Terminali kontrol et.'); }
  if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Alanları ve sunucu terminalini kontrol et.');
  return data;
}
function updateControls() {
  $('ask').disabled = busy || !image || !$('model').value;
  $('captureAsk').disabled = busy || !$('model').value || !$('address').value.trim();
  $('analyze').disabled = busy || !image || !visionReady;
  $('capture').disabled = busy || !$('address').value.trim();
  $('live').disabled = !liveEnabled && (busy || !visionReady || !$('address').value.trim());
  $('live').textContent = liveEnabled ? '■ Otomatik kontrolü durdur' : '▶ Otomatik kontrol';
  ['refresh','file','chooseFile','model','address','question','cpuOnly','personName','personPhoto'].forEach(id => $(id).disabled = busy);
  $('register').disabled = busy || !registrationData || !$('personName').value.trim() || !visionReady;
  document.querySelectorAll('.delete-person').forEach(button => button.disabled = busy);
}
async function task(message, action) {
  if (busy) return;
  busy = true; frameEpoch++; updateControls(); notice(message);
  try { if (frameOperation) await frameOperation.catch(() => {}); await action(); }
  catch(error) { notice(error.message, true); }
  finally { busy = false; updateControls(); }
}
function clearFaces() { $('faceOverlay').replaceChildren(); $('faceList').replaceChildren(); $('faceSummary').textContent = 'Bu kare henüz analiz edilmedi'; $('visionTiming').textContent = '— ms'; }
function showImage(item, clearAnswer = true) {
  image = item;
  $('preview').src = 'data:image/jpeg;base64,' + item.image;
  $('imageStage').hidden = false; $('placeholder').hidden = true;
  $('imageSource').textContent = item.source;
  $('imageTime').textContent = new Date(item.created_at).toLocaleString('tr-TR');
  $('imageSize').textContent = item.width + ' × ' + item.height;
  if (item.source.startsWith('ESP32')) { lastCameraAt = Date.now(); $('cameraStatus').textContent = 'Son kare alındı'; }
  clearFaces();
  if (clearAnswer) { $('answer').textContent = 'Görüntü hazır. Merak ettiğini sorabilirsin.'; $('duration').textContent = ''; }
}
function showVision(result) {
  if (!image || result.image_id !== image.id) return;
  clearFaces();
  $('faceSummary').textContent = result.face_count ? result.face_count + ' yüz algılandı' : 'Yüz algılanmadı';
  $('visionTiming').textContent = result.duration_ms + ' ms';
  $('visionStatus').textContent = result.face_count + ' yüz / son kare';
  $('visionMeta').textContent = 'YuNet + SFace · ' + result.duration_ms + ' ms';
  const ns = 'http://www.w3.org/2000/svg';
  result.faces.forEach((face, index) => {
    const [x,y,w,h] = face.box.map(value => value * 1000);
    const rectangle = document.createElementNS(ns, 'rect');
    for (const [key,value] of Object.entries({x,y,width:w,height:h,fill:'none',stroke:face.person_id ? '#d5f78a' : '#e8ba74','stroke-width':3,'vector-effect':'non-scaling-stroke'})) rectangle.setAttribute(key, value);
    const text = document.createElementNS(ns, 'text');
    text.setAttribute('x', x + 5); text.setAttribute('y', Math.max(24, y - 12)); text.setAttribute('fill', '#edf2e8'); text.setAttribute('font-size', '27'); text.setAttribute('paint-order','stroke'); text.setAttribute('stroke','#111813'); text.setAttribute('stroke-width','4'); text.textContent = (index+1) + ' · ' + face.name;
    $('faceOverlay').append(rectangle, text);
    const chip = document.createElement('span'); chip.className = 'face-chip'; chip.textContent = (index+1) + ' · ' + face.name + ' / ' + face.position;
    $('faceList').append(chip);
  });
}
async function analyzeCurrent() {
  const result = await api('vision/analyze', {image_id:image.id}); showVision(result);
  notice(result.face_count ? result.face_count + ' yüz algılandı. Eşleşmeler kare üzerindedir.' : 'Bu karede yüz algılanmadı.');
}
async function capture(analyze = true) {
  try {
    const item = await api(analyze && visionReady ? 'vision/capture' : 'capture', {address:$('address').value});
    showImage(item);
    if (item.vision) showVision(item.vision);
    if (item.roundtrip_ms !== undefined) $('roundtrip').textContent = item.roundtrip_ms + ' ms';
    try { localStorage.setItem('cameraAddress', $('address').value); } catch (_) {}
    $('cameraStatus').textContent = 'Son kare alındı';
  } catch(error) { $('cameraStatus').textContent = 'Kare alınamadı'; throw error; }
}
function stopLive() { liveEnabled = false; frameEpoch++; clearTimeout(liveTimer); $('feedMode').textContent = 'TEK KARE'; updateControls(); }
async function liveTick() {
  if (!liveEnabled) return;
  if (busy || document.hidden) { liveTimer = setTimeout(liveTick, 1000); return; }
  const epoch = frameEpoch;
  frameOperation = api('vision/capture', {address:$('address').value});
  try {
    const item = await frameOperation;
    if (liveEnabled && epoch === frameEpoch && !busy) {
      showImage(item, false); showVision(item.vision); $('roundtrip').textContent = item.roundtrip_ms + ' ms';
    }
  } catch(error) { if (liveEnabled && epoch === frameEpoch) { stopLive(); $('cameraStatus').textContent = 'Kare alınamadı'; notice('Otomatik kontrol durduruldu: ' + error.message, true); } }
  finally { frameOperation = null; updateControls(); if (liveEnabled) liveTimer = setTimeout(liveTick, 2000); }
}
async function ask() {
  const askedImage = image;
  notice('Görüntü yorumlanıyor. Otomatik kamera kontrolü bu işlem sırasında bekler.');
  const result = await api('ask', {image_id:askedImage.id, model:$('model').value, question:$('question').value, cpu_only:$('cpuOnly').checked});
  $('answer').textContent = result.answer;
  $('duration').textContent = result.duration_seconds + ' sn · kare ' + new Date(askedImage.created_at).toLocaleTimeString('tr-TR');
  notice('Cevap hazır · ' + result.model);
}
function renderPeople(items) {
  $('peopleList').replaceChildren(); $('peopleCount').textContent = items.length + ' KİŞİ'; $('navCount').textContent = items.length;
  if (!items.length) { const empty = document.createElement('p'); empty.className='muted'; empty.textContent='Henüz kimseyle tanışmadım. Soldan ilk kişiyi kaydedebilirsin.'; $('peopleList').append(empty); }
  items.forEach(person => {
    const row = document.createElement('div'); row.className='person-row';
    const avatar=document.createElement('span'); avatar.className='person-avatar'; avatar.textContent=person.name.slice(0,1).toLocaleUpperCase('tr-TR');
    const info=document.createElement('div'); info.className='person-info'; const name=document.createElement('b'); name.textContent=person.name; const date=document.createElement('small'); date.textContent='Kayıt: ' + new Date(person.created_at).toLocaleDateString('tr-TR'); info.append(name,date);
    const remove=document.createElement('button'); remove.className='delete-person'; remove.textContent='Sil'; remove.setAttribute('aria-label',person.name+' kaydını sil');
    remove.onclick=()=>task('Kişi kaydı siliniyor…',async()=>{ await api('people/'+encodeURIComponent(person.id),{},'DELETE'); await refreshPeople(); clearFaces(); notice('Kişi kaydı silindi.'); });
    row.append(avatar,info,remove); $('peopleList').append(row);
  });
}
async function refreshPeople() { renderPeople((await api('people')).people); }
async function refresh() {
  const results=await Promise.allSettled([api('health'),api('vision/status'),refreshPeople()]);
  const health=results[0].status==='fulfilled' ? results[0].value : null;
  const vision=results[1].status==='fulfilled' ? results[1].value : null;
  visionReady=Boolean(vision && vision.ready);
  $('visionStatus').textContent=visionReady?'Hazır':'Hazır değil';
  $('visionMeta').textContent=visionReady?'YuNet + SFace · CPU':vision?.message || 'Sunucu bağlantısını kontrol et';
  $('ollamaStatus').textContent=health?.ollama?'Bağlı · '+health.version:'Bağlantı yok';
  if (health?.ollama) {
    const data=await api('models'); const previous=$('model').value; const models=data.models.filter(model=>model.vision);
    $('model').replaceChildren(new Option(models.length?'Model seç':'Görüntü modeli kurulu değil',''));
    models.forEach(model=>$('model').add(new Option(model.name,model.name)));
    $('model').value=models.some(model=>model.name===previous)?previous:models[0]?.name || '';
    $('modelHint').textContent=models.length?'Yerel model hazır. Görüntüye soru sorabilirsin.':'Terminalde ollama pull qwen3-vl:2b-instruct çalıştır.';
    $('llmMeta').textContent=$('model').value || 'Model kurulmalı';
  }
  const errors=results.filter(result=>result.status==='rejected').map(result=>result.reason.message);
  if (!visionReady && vision?.message) errors.push(vision.message);
  notice(errors.length?errors.join(' '):'Hazır. Fotoğraf çek veya kişi kayıtları bölümünden biriyle tanıştır.',errors.length>0);
}
function readPhoto(file) {
  if (!file) return Promise.reject(Error('Bir fotoğraf seç.'));
  if (file.size>8*1024*1024) return Promise.reject(Error('En fazla 8 MB boyutunda bir fotoğraf seç.'));
  if (!['image/jpeg','image/png','image/webp'].includes(file.type)) return Promise.reject(Error('JPEG, PNG veya WebP fotoğraf seç.'));
  return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(Error('Fotoğraf okunamadı.'));reader.readAsDataURL(file);});
}
$('capture').onclick=()=>task('Kameradan fotoğraf alınıyor…',async()=>{await capture();notice('Yeni kamera karesi alındı.');});
$('analyze').onclick=()=>task('Yüzler algılanıyor…',analyzeCurrent);
$('ask').onclick=()=>task('Hazırlanıyor…',ask);
$('captureAsk').onclick=()=>task('Yeni kare alınıyor…',async()=>{await capture(false);await ask();});
$('refresh').onclick=()=>task('Bağlantılar kontrol ediliyor…',refresh);
$('live').onclick=()=>{if(liveEnabled){stopLive();notice('Otomatik kamera kontrolü durduruldu.');}else if(!busy){liveEnabled=true;frameEpoch++;$('feedMode').textContent='OTOMATİK / 2 SN';updateControls();notice('Otomatik yüz kontrolü başladı.');liveTick();}};
$('chooseFile').onclick=()=>$('file').click();
$('model').onchange=()=>{$('llmMeta').textContent=$('model').value || 'Model seçilmedi';updateControls();};
$('address').oninput=()=>{if(liveEnabled)stopLive();updateControls();};
$('personName').oninput=updateControls;
$('file').onchange=()=>{const file=$('file').files[0];if(!file)return;task('Fotoğraf yükleniyor…',async()=>{const data=await readPhoto(file);showImage(await api('image',{image:data.split(',')[1]}));if(visionReady)await analyzeCurrent();else notice('Fotoğraf yüklendi.');}).finally(()=>{$('file').value='';});};
$('personPhoto').onchange=async()=>{const version=++personRead;registrationData=null;$('personPreview').hidden=true;updateControls();try{const data=await readPhoto($('personPhoto').files[0]);if(version!==personRead)return;registrationData=data.split(',')[1];$('personPreview').src=data;$('personPreview').hidden=false;$('personPhotoText').textContent='Kayıt için seçilen fotoğraf';}catch(error){notice(error.message,true);}updateControls();};
$('personForm').onsubmit=event=>{event.preventDefault();task('Kişi kaydediliyor…',async()=>{if(!registrationData)throw Error('Önce kişi fotoğrafı seç.');const person=await api('people',{name:$('personName').value,image:registrationData});await refreshPeople();$('personForm').reset();personRead++;registrationData=null;$('personPreview').hidden=true;$('personPreview').removeAttribute('src');$('personPhotoText').textContent='＋ Kişi fotoğrafı seç';clearFaces();notice(person.name+' kaydedildi. Operasyon bölümünde yeni fotoğraf çekerek deneyebilirsin.');});};
const pages={mission:['Operasyon','Operasyon merkezi','Kamerayı yönet, yüzleri algıla, gördüklerini sor.'],people:['Kişi kayıtları','Tanıdık yüzler','Fotoğrafla tanıştır, kayıtlarını bu bilgisayarda yönet.'],system:['Sistem','Sistem durumu','Donanımı ve ölçülen işlem sürelerini takip et.']};
document.querySelectorAll('[data-tab]').forEach(button=>button.onclick=()=>{const tab=button.dataset.tab;if(tab!=='mission')stopLive();document.querySelectorAll('.tab-content').forEach(section=>section.hidden=section.id!==tab);document.querySelectorAll('[data-tab]').forEach(item=>item.classList.toggle('active',item===button));const [label,title,description]=pages[tab];$('sectionLabel').textContent=label;$('pageTitle').textContent=title;$('pageDescription').textContent=description;});
document.querySelectorAll('[data-question]').forEach(button=>button.onclick=()=>{$('question').value=button.dataset.question;});
function tickClock(){$('clock').textContent=new Date().toLocaleTimeString('tr-TR',{timeZone:'Europe/Istanbul'});if(lastCameraAt)$('cameraMeta').textContent='Son kare: '+Math.floor((Date.now()-lastCameraAt)/1000)+' sn önce';}
tickClock();setInterval(tickClock,1000);
window.addEventListener('pagehide',stopLive);
try{$('address').value=localStorage.getItem('cameraAddress') || '';}catch(_){}
updateControls();task('Bağlantılar kontrol ediliyor…',refresh);
