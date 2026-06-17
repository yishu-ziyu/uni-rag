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
    citations.forEach((c, i) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'cite-chip';
      chip.textContent = `[${i + 1}] ${c.source}${c.section ? ' · ' + c.section : ''}`;
      chip.addEventListener('click', () => openCitation(c.source, c.span, c.text));
      cits.appendChild(chip);
    });
    div.appendChild(cits);
  }
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

// Side panel 控制
const docPanel = document.getElementById('doc-panel');
const panelTitle = document.getElementById('panel-title');
const panelBody = document.getElementById('panel-body');
const panelClose = document.getElementById('panel-close');

panelClose.addEventListener('click', closePanel);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closePanel();
});

function openCitation(filename, span, citedText) {
  panelTitle.textContent = filename;
  panelBody.innerHTML = '<p style="color:var(--accent)">加载中…</p>';
  docPanel.classList.remove('hidden');
  docPanel.classList.add('open');
  docPanel.setAttribute('aria-hidden', 'false');

  fetch(`/api/documents/${encodeURIComponent(filename)}/chunks`)
    .then((r) => {
      if (!r.ok) throw new Error('加载失败');
      return r.json();
    })
    .then((data) => renderDocument(data.chunks, span, citedText))
    .catch((err) => {
      panelBody.innerHTML = `<p style="color:#a44">${err.message}</p>`;
    });
}

function renderDocument(chunks, highlightSpan, highlightText) {
  panelBody.innerHTML = '';
  if (!chunks.length) {
    panelBody.innerHTML = '<p>无内容</p>';
    return;
  }
  // 找到最贴近 highlightSpan 的 chunk 来高亮
  const target = chunks.find((c) =>
    c.span && highlightSpan &&
    c.span[0] <= highlightSpan[0] && c.span[1] >= highlightSpan[1]
  ) || chunks[0];

  chunks.forEach((c) => {
    if (c.section) {
      const t = document.createElement('span');
      t.className = 'section-title';
      t.textContent = c.section;
      panelBody.appendChild(t);
    }
    const p = document.createElement('p');
    if (c.id === target.id && c.text) {
      // 把高亮 span 用 <mark> 包裹
      p.innerHTML = wrapHighlight(c.text, highlightSpan, c.span);
    } else {
      p.textContent = c.text;
    }
    panelBody.appendChild(p);
  });

  // 滚到高亮位置
  const markEl = panelBody.querySelector('mark');
  if (markEl) markEl.scrollIntoView({ block: 'center', behavior: 'smooth' });
}

function wrapHighlight(text, absSpan, chunkSpan) {
  // 把 text 在 chunkSpan 内的 offset 投影到 absolute offset
  // 简化：直接在 text 里找 citedText 第一个出现位置包 <mark>
  if (!absSpan) return escapeHtml(text);
  const esc = escapeHtml(text);
  // 计算相对偏移
  const relStart = Math.max(0, absSpan[0] - chunkSpan[0]);
  const relEnd = Math.min(text.length, absSpan[1] - chunkSpan[0]);
  if (relStart >= relEnd) return esc;
  return (
    escapeHtml(text.slice(0, relStart)) +
    '<mark>' + escapeHtml(text.slice(relStart, relEnd)) + '</mark>' +
    escapeHtml(text.slice(relEnd))
  );
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[ch]);
}

function closePanel() {
  docPanel.classList.remove('open');
  docPanel.classList.add('hidden');
  docPanel.setAttribute('aria-hidden', 'true');
  panelBody.innerHTML = '';
}
