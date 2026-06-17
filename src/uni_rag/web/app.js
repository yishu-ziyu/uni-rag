// src/uni_rag/web/app.js
const fileList = document.getElementById('file-list');
const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('dropzone');
const chat = document.getElementById('chat');
const form = document.getElementById('query-form');
const questionInput = document.getElementById('question-input');

let sessionId = null;
const sources = new Map();  // filename → source_id

// Upload
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const r = await fetch('/api/ingest', { method: 'POST', body: formData });
  if (!r.ok) {
    alert('上传失败');
    return;
  }
  const data = await r.json();
  sources.set(file.name, data.source_id);
  const li = document.createElement('li');
  li.textContent = `${file.name} · ${data.chunks} 块`;
  fileList.appendChild(li);
}

fileInput.addEventListener('change', (e) => {
  for (const f of e.target.files) uploadFile(f);
});

dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('dragging');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragging'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragging');
  for (const f of e.dataTransfer.files) uploadFile(f);
});

// Query
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;
  addMessage('user', question);
  questionInput.value = '';
  const r = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId }),
  });
  const data = await r.json();
  sessionId = data.session_id;
  addMessage('assistant', data.answer, data.citations);
});

function addMessage(role, text, citations = []) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  const content = document.createElement('div');
  content.className = 'content';
  content.textContent = text;
  div.appendChild(content);
  if (citations.length) {
    const cits = document.createElement('div');
    cits.className = 'citations';
    cits.textContent = '引用：' + citations.map(c => `${c.source}${c.section ? ' · ' + c.section : ''}`).join(' | ');
    div.appendChild(cits);
  }
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
