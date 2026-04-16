// ── API ───────────────────────────────────────────────────────────────────────
const API       = '/api/detect';
const VIDEO_API = '/api/detect/video';

// ── Tab Switching ─────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// IMAGE DETECTION
// ─────────────────────────────────────────────────────────────────────────────
const fileInput      = document.getElementById('file-input');
const dropZone       = document.getElementById('drop-zone');
const previewArea    = document.getElementById('preview-area');
const previewImg     = document.getElementById('preview-img');
const fileNameTag    = document.getElementById('file-name-tag');
const metaName       = document.getElementById('meta-name');
const metaSize       = document.getElementById('meta-size');
const metaType       = document.getElementById('meta-type');
const loader         = document.getElementById('loader');
const errorBox       = document.getElementById('error-box');
const resultPanel    = document.getElementById('result-panel');
const verdictIcon    = document.getElementById('verdict-icon');
const verdictLabel   = document.getElementById('verdict-label');
const verdictConf    = document.getElementById('verdict-conf');
const realBar        = document.getElementById('real-bar');
const fakeBar        = document.getElementById('fake-bar');
const realPct        = document.getElementById('real-pct');
const fakePct        = document.getElementById('fake-pct');
const demoNote       = document.getElementById('demo-note');
const btnAnalyze     = document.getElementById('btn-analyze');
const btnReset       = document.getElementById('btn-reset');
const historySection = document.getElementById('history-section');
const historyList    = document.getElementById('history-list');

let currentFile = null;
const history   = [];

// Drag & drop — image
dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault(); dropZone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) loadImageFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => { if (fileInput.files[0]) loadImageFile(fileInput.files[0]); });

function loadImageFile(file) {
  currentFile = file;
  hideImageResults();
  const reader = new FileReader();
  reader.onload = ev => {
    previewImg.src          = ev.target.result;
    fileNameTag.textContent = file.name;
    metaName.textContent    = file.name.length > 28 ? file.name.slice(0, 25) + '…' : file.name;
    metaSize.textContent    = formatBytes(file.size);
    metaType.textContent    = file.type || 'unknown';
    previewArea.classList.add('visible');
    btnAnalyze.disabled = false;
  };
  reader.readAsDataURL(file);
}

btnAnalyze.addEventListener('click', async () => {
  if (!currentFile) return;
  btnAnalyze.disabled = true;
  hideImageResults();
  errorBox.classList.remove('visible');
  loader.classList.add('visible');

  try {
    const fd = new FormData();
    fd.append('image', currentFile);
    const resp = await fetch(API, { method: 'POST', body: fd });
    const data = await resp.json();
    loader.classList.remove('visible');
    if (!resp.ok || data.error) throw new Error(data.error || 'Server error');
    showImageResult(data);
    addToHistory(previewImg.src, data, 'image');
  } catch (e) {
    loader.classList.remove('visible');
    errorBox.textContent = '⚠ ' + e.message;
    errorBox.classList.add('visible');
    btnAnalyze.disabled = false;
  }
});

function showImageResult(data) {
  const isFake = data.label === 'FAKE';
  verdictIcon.textContent  = isFake ? '🔴' : '🟢';
  verdictIcon.className    = `verdict-icon ${isFake ? 'fake' : 'real'}`;
  verdictLabel.textContent = data.label;
  verdictLabel.className   = `verdict-label ${isFake ? 'fake' : 'real'}`;
  verdictConf.textContent  = `${data.confidence}% confidence`;
  demoNote.style.display   = data.demo_mode ? 'flex' : 'none';
  resultPanel.classList.add('visible');
  requestAnimationFrame(() => {
    realBar.style.width = data.real_prob + '%';
    fakeBar.style.width = data.fake_prob + '%';
    realPct.textContent = data.real_prob + '%';
    fakePct.textContent = data.fake_prob + '%';
  });
  btnAnalyze.disabled = false;
}

function hideImageResults() {
  loader.classList.remove('visible');
  resultPanel.classList.remove('visible');
  realBar.style.width = '0';
  fakeBar.style.width = '0';
}

btnReset.addEventListener('click', () => {
  currentFile = null;
  fileInput.value = '';
  previewArea.classList.remove('visible');
  hideImageResults();
  errorBox.classList.remove('visible');
  btnAnalyze.disabled = true;
});

// ─────────────────────────────────────────────────────────────────────────────
// VIDEO DETECTION
// ─────────────────────────────────────────────────────────────────────────────
const videoInput       = document.getElementById('video-input');
const videoDropZone    = document.getElementById('video-drop-zone');
const videoPreviewArea = document.getElementById('video-preview-area');
const videoPreview     = document.getElementById('video-preview');
const vmetaName        = document.getElementById('vmeta-name');
const vmetaSize        = document.getElementById('vmeta-size');
const vmetaType        = document.getElementById('vmeta-type');
const videoLoader      = document.getElementById('video-loader');
const videoLoaderText  = document.getElementById('video-loader-text');
const videoErrorBox    = document.getElementById('video-error-box');
const videoResultPanel = document.getElementById('video-result-panel');
const vverdictIcon     = document.getElementById('vverdict-icon');
const vverdictLabel    = document.getElementById('vverdict-label');
const vverdictConf     = document.getElementById('vverdict-conf');
const vrealBar         = document.getElementById('vreal-bar');
const vfakeBar         = document.getElementById('vfake-bar');
const vrealPct         = document.getElementById('vreal-pct');
const vfakePct         = document.getElementById('vfake-pct');
const vdemoNote        = document.getElementById('vdemo-note');
const statFrames       = document.getElementById('stat-frames');
const statDuration     = document.getElementById('stat-duration');
const btnVideoAnalyze  = document.getElementById('btn-video-analyze');
const btnVideoReset    = document.getElementById('btn-video-reset');

let currentVideo = null;

// Drag & drop — video
videoDropZone.addEventListener('dragover',  e => { e.preventDefault(); videoDropZone.classList.add('drag-over'); });
videoDropZone.addEventListener('dragleave', ()  => videoDropZone.classList.remove('drag-over'));
videoDropZone.addEventListener('drop', e => {
  e.preventDefault(); videoDropZone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) loadVideoFile(e.dataTransfer.files[0]);
});
videoInput.addEventListener('change', () => { if (videoInput.files[0]) loadVideoFile(videoInput.files[0]); });

function loadVideoFile(file) {
  currentVideo = file;
  hideVideoResults();
  videoPreview.src     = URL.createObjectURL(file);
  vmetaName.textContent = file.name.length > 28 ? file.name.slice(0, 25) + '…' : file.name;
  vmetaSize.textContent = formatBytes(file.size);
  vmetaType.textContent = file.type || 'unknown';
  videoPreviewArea.classList.add('visible');
  btnVideoAnalyze.disabled = false;
}

btnVideoAnalyze.addEventListener('click', async () => {
  if (!currentVideo) return;
  btnVideoAnalyze.disabled = true;
  hideVideoResults();
  videoErrorBox.classList.remove('visible');
  videoLoader.classList.add('visible');
  videoLoaderText.textContent = 'EXTRACTING & ANALYSING FRAMES…';

  try {
    const fd = new FormData();
    fd.append('video', currentVideo);
    const resp = await fetch(VIDEO_API, { method: 'POST', body: fd });
    const data = await resp.json();
    videoLoader.classList.remove('visible');
    if (!resp.ok || data.error) throw new Error(data.error || 'Server error');
    showVideoResult(data);
    addToHistory(null, data, 'video');
  } catch (e) {
    videoLoader.classList.remove('visible');
    videoErrorBox.textContent = '⚠ ' + e.message;
    videoErrorBox.classList.add('visible');
    btnVideoAnalyze.disabled = false;
  }
});

function showVideoResult(data) {
  const isFake = data.label === 'FAKE';

  vverdictIcon.textContent  = isFake ? '🔴' : '🟢';
  vverdictIcon.className    = `verdict-icon ${isFake ? 'fake' : 'real'}`;
  vverdictLabel.textContent = data.label;
  vverdictLabel.className   = `verdict-label ${isFake ? 'fake' : 'real'}`;
  vverdictConf.textContent  = `${data.confidence}% confidence`;
  vdemoNote.style.display   = data.demo_mode ? 'flex' : 'none';

  statFrames.textContent   = data.frames_analysed + ' frames';
  statDuration.textContent = data.duration_sec + 's';

  videoResultPanel.classList.add('visible');

  requestAnimationFrame(() => {
    vrealBar.style.width = data.real_prob + '%';
    vfakeBar.style.width = data.fake_prob + '%';
    vrealPct.textContent = data.real_prob + '%';
    vfakePct.textContent = data.fake_prob + '%';
  });

  btnVideoAnalyze.disabled = false;
}

function hideVideoResults() {
  videoLoader.classList.remove('visible');
  videoResultPanel.classList.remove('visible');
  vrealBar.style.width = '0';
  vfakeBar.style.width = '0';
}

btnVideoReset.addEventListener('click', () => {
  currentVideo = null;
  videoInput.value = '';
  videoPreviewArea.classList.remove('visible');
  hideVideoResults();
  videoErrorBox.classList.remove('visible');
  btnVideoAnalyze.disabled = true;
  videoPreview.src = '';
});

// ─────────────────────────────────────────────────────────────────────────────
// SHARED HISTORY
// ─────────────────────────────────────────────────────────────────────────────
function addToHistory(src, data, type) {
  history.unshift({ src, data, type });
  if (history.length > 12) history.pop();

  historySection.classList.add('visible');
  historyList.innerHTML = '';

  history.forEach(item => {
    const isFake = item.data.label === 'FAKE';
    const div    = document.createElement('div');
    div.className = 'hist-item';

    const imgTag = item.src
      ? `<img src="${item.src}" alt="history"/>`
      : `<div style="width:100%;height:80px;background:var(--bg3);display:flex;align-items:center;justify-content:center;font-size:1.5rem;">🎬</div>`;

    div.innerHTML = `
      ${imgTag}
      <div class="hist-info">
        <span class="hist-label ${isFake ? 'fake' : 'real'}">${item.data.label}</span>
        <span class="hist-pct">${item.data.confidence}%</span>
      </div>`;
    historyList.appendChild(div);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────────────────────────────────────────
function formatBytes(b) {
  if (b < 1024)    return b + ' B';
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
  return (b / 1048576).toFixed(2) + ' MB';
}
