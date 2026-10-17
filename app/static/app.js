const API = '/api/v1';
let activeCase = null;
let evidenceItems = [];

const $ = (selector) => document.querySelector(selector);
const caseForm = $('#case-form');
const uploadForm = $('#upload-form');
const fileInput = $('#evidence-file');
const dropzone = $('#dropzone');
const uploadButton = $('#upload-button');
const uploadStatus = $('#upload-status');

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body.error || body.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message || 'Request failed');
  }
  return body;
}

caseForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = caseForm.querySelector('button');
  button.disabled = true;
  try {
    activeCase = await request(`${API}/cases`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title: $('#case-title').value.trim(), description: $('#case-description').value.trim() || null}),
    });
    $('#case-summary').innerHTML = `<strong></strong><span></span>`;
    $('#case-summary strong').textContent = activeCase.title;
    $('#case-summary span').textContent = `Case ID · ${activeCase.id}`;
    $('#case-summary').classList.remove('hidden');
    uploadStatus.classList.remove('error');
    caseForm.querySelectorAll('input,textarea,button').forEach((el) => { el.disabled = true; });
    uploadButton.disabled = false;
    uploadStatus.textContent = 'Case ready. Add a photo or PDF.';
  } catch (error) {
    uploadStatus.textContent = error.message;
    uploadStatus.classList.add('error');
    button.disabled = false;
  }
});

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  $('#selected-file').textContent = file ? `${file.name} · ${formatBytes(file.size)}` : '';
});

for (const eventName of ['dragenter', 'dragover']) {
  dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.add('dragover'); });
}
for (const eventName of ['dragleave', 'drop']) {
  dropzone.addEventListener(eventName, (event) => { event.preventDefault(); dropzone.classList.remove('dragover'); });
}
dropzone.addEventListener('drop', (event) => {
  if (event.dataTransfer.files.length) {
    fileInput.files = event.dataTransfer.files;
    fileInput.dispatchEvent(new Event('change'));
  }
});

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!activeCase || !file) return;
  uploadButton.disabled = true;
  uploadStatus.classList.remove('error');
  uploadStatus.textContent = 'Saving original and recording metadata…';
  const data = new FormData();
  data.append('file', file);
  try {
    await request(`${API}/cases/${activeCase.id}/evidence`, {method: 'POST', body: data});
    fileInput.value = '';
    $('#selected-file').textContent = '';
    uploadStatus.textContent = 'Evidence saved and linked to the case.';
    await refreshCase();
  } catch (error) {
    uploadStatus.textContent = error.message;
    uploadStatus.classList.add('error');
  } finally {
    uploadButton.disabled = false;
  }
});

async function refreshCase() {
  if (!activeCase) return;
  const [evidence, timeline] = await Promise.all([
    request(`${API}/cases/${activeCase.id}/evidence`),
    request(`${API}/cases/${activeCase.id}/timeline`),
  ]);
  evidenceItems = evidence.items;
  $('#evidence-count').textContent = `${evidenceItems.length} ${evidenceItems.length === 1 ? 'item' : 'items'}`;
  renderTimeline(timeline.items);
}

function renderTimeline(events) {
  const container = $('#timeline');
  if (!events.length) {
    container.className = 'timeline empty-state';
    container.innerHTML = '<div class="empty-symbol">◷</div><strong>Your timeline will appear here</strong><span>Upload a source file to start the record.</span>';
    return;
  }
  container.className = 'timeline timeline-list';
  container.innerHTML = '';
  const evidenceById = new Map(evidenceItems.map((item) => [item.id, item]));
  for (const event of events) {
    const evidence = evidenceById.get(event.evidence_id);
    const row = document.createElement('article');
    row.className = 'timeline-item';
    const rail = document.createElement('div'); rail.className = 'timeline-rail';
    const dot = document.createElement('span'); dot.className = 'timeline-dot'; rail.append(dot);
    const content = document.createElement('div');
    const head = document.createElement('div'); head.className = 'event-head';
    const title = document.createElement('div'); title.className = 'event-title'; title.textContent = event.label;
    const time = document.createElement('time'); time.className = 'event-time'; time.dateTime = event.occurred_at; time.textContent = new Date(event.occurred_at).toLocaleString();
    head.append(title, time);
    const meta = document.createElement('div'); meta.className = 'event-meta'; meta.textContent = `Upload time · ${event.epistemic_status}`;
    content.append(head, meta);
    if (evidence) {
      const source = document.createElement('a'); source.className = 'source-link'; source.href = evidence.file_url; source.target = '_blank'; source.rel = 'noopener'; source.textContent = `↗ Inspect source · ${evidence.original_filename}`;
      content.append(source);
      const observation = evidence.observations?.[0];
      if (observation) {
        const note = document.createElement('div'); note.className = 'observation';
        note.textContent = observation.text;
        const tag = document.createElement('span'); tag.className = 'tag'; tag.textContent = observation.epistemic_status; note.append(tag);
        content.append(note);
      }
    }
    row.append(rail, content); container.append(row);
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
