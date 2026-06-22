// src/uni_rag/web/app.js
const folderView = document.getElementById('folder-view');
const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('dropzone');
const chat = document.getElementById('chat');
const form = document.getElementById('query-form');
const questionInput = document.getElementById('question-input');
const kbSelect = document.getElementById('kb-select');
const kbNewName = document.getElementById('kb-new-name');
const kbCreateBtn = document.getElementById('kb-create-btn');
const ingestStatus = document.getElementById('ingest-status');
const ingestStep = document.getElementById('ingest-step');
const ingestPercent = document.getElementById('ingest-percent');
const ingestProgress = document.getElementById('ingest-progress');
const ingestMessage = document.getElementById('ingest-message');
const submitButton = form.querySelector('button');

let sessionId = null;
let currentKbId = '';
let msgCounter = 0;  // tracks 1-based session message index for assistant export links
let indexedFileCount = 0;
const sources = new Map();  // filename → source_id

// ── Settings (localStorage) ─────────────────────
const SETTINGS_KEY = 'uni-rag-settings';

function loadSettings() {
  try {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {};
  } catch {
    return {};
  }
}

function saveSettings(obj) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(obj));
}

function getApiHeaders() {
  const s = loadSettings();
  const h = { 'Content-Type': 'application/json' };
  if (s.api_key) h['X-API-Key'] = s.api_key;
  return h;
}

function getApiOverrides() {
  const s = loadSettings();
  const overrides = {};
  if (s.base_url) overrides.base_url = s.base_url;
  if (s.model) overrides.model = s.model;
  return overrides;
}

// Settings modal
const settingsModal = document.getElementById('settings-modal');
const settingsBtn = document.getElementById('settings-btn');
const settingsClose = document.getElementById('settings-close');
const settingsSave = document.getElementById('settings-save');
const settingsCancel = document.getElementById('settings-cancel');
const settingApiKey = document.getElementById('setting-api-key');
const settingBaseUrl = document.getElementById('setting-base-url');
const settingModel = document.getElementById('setting-model');

function openSettings() {
  const s = loadSettings();
  settingApiKey.value = s.api_key || '';
  settingBaseUrl.value = s.base_url || '';
  settingModel.value = s.model || '';
  settingsModal.classList.remove('hidden');
  settingsModal.setAttribute('aria-hidden', 'false');
}

function closeSettings() {
  settingsModal.classList.add('hidden');
  settingsModal.setAttribute('aria-hidden', 'true');
}

if (settingsBtn) settingsBtn.addEventListener('click', openSettings);
if (settingsClose) settingsClose.addEventListener('click', closeSettings);
if (settingsCancel) settingsCancel.addEventListener('click', closeSettings);
settingsModal?.querySelector('.modal-backdrop')?.addEventListener('click', closeSettings);
if (settingsSave) settingsSave.addEventListener('click', () => {
  saveSettings({
    api_key: settingApiKey.value.trim(),
    base_url: settingBaseUrl.value.trim(),
    model: settingModel.value.trim(),
  });
  closeSettings();
});

// ── Theme toggle ────────────────────────────────
const THEME_KEY = 'uni-rag-theme';

function getTheme() {
  return localStorage.getItem(THEME_KEY) || 'light';
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = theme === 'dark' ? '☀ 亮色' : '◐ 暗色';
}

const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
  applyTheme(getTheme());
  themeToggle.addEventListener('click', () => {
    applyTheme(getTheme() === 'dark' ? 'light' : 'dark');
  });
}

// ── Staggered Menu ──────────────────────────────
(function () {
  const overlay = document.getElementById('sm-overlay');
  const toggle = document.getElementById('menu-toggle');
  const textInner = toggle ? toggle.querySelector('.sm-toggle-textInner') : null;
  let isOpen = false;
  let busy = false;

  if (!overlay || !toggle) return;

  function openMenu() {
    if (busy) return;
    busy = true;
    isOpen = true;
    overlay.setAttribute('data-open', '');
    overlay.setAttribute('aria-hidden', 'false');
    toggle.setAttribute('aria-expanded', 'true');
    toggle.setAttribute('aria-label', '关闭菜单');
    document.body.style.overflow = 'hidden';
    setTimeout(() => { busy = false; }, 600);
  }

  function closeMenu() {
    if (busy) return;
    busy = true;
    isOpen = false;
    overlay.removeAttribute('data-open');
    overlay.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', '打开菜单');
    document.body.style.overflow = '';
    setTimeout(() => { busy = false; }, 500);
  }

  function toggleMenu() {
    isOpen ? closeMenu() : openMenu();
  }

  toggle.addEventListener('click', toggleMenu);

  // Close on backdrop click
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeMenu();
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen) closeMenu();
  });

  // Navigation item clicks
  const navItems = overlay.querySelectorAll('.sm-nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = item.getAttribute('href')?.replace('#', '');
      closeMenu();
      // Scroll to target section after menu closes
      setTimeout(() => {
        const target = document.getElementById(targetId);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          // Highlight the target section briefly
          target.style.transition = 'box-shadow 0.5s ease';
          target.style.boxShadow = '0 0 0 4px var(--accent-glow)';
          setTimeout(() => {
            target.style.boxShadow = '';
          }, 1500);
        }
      }, 400);
    });
  });
})();

// ── Folder Component ────────────────────────────
const FOLDER_COLORS = [
  '#6366f1', '#8b5cf6', '#a855f7', '#d946ef',
  '#ec4899', '#f43f5e', '#f97316', '#eab308',
  '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6',
];

function hashColor(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return FOLDER_COLORS[Math.abs(hash) % FOLDER_COLORS.length];
}

function hexToRgb(hex) {
  const c = hex.replace('#', '');
  return {
    r: parseInt(c.substring(0, 2), 16),
    g: parseInt(c.substring(2, 4), 16),
    b: parseInt(c.substring(4, 6), 16),
  };
}

function rgbToHex(r, g, b) {
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
}

function darken(hex, pct) {
  const { r, g, b } = hexToRgb(hex);
  return rgbToHex(
    Math.max(0, Math.floor(r * (1 - pct))),
    Math.max(0, Math.floor(g * (1 - pct))),
    Math.max(0, Math.floor(b * (1 - pct))),
  );
}

function lighten(hex, pct) {
  const { r, g, b } = hexToRgb(hex);
  return rgbToHex(
    Math.min(255, Math.floor(r + (255 - r) * pct)),
    Math.min(255, Math.floor(g + (255 - g) * pct)),
    Math.min(255, Math.floor(b + (255 - b) * pct)),
  );
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const map = { pdf: 'PDF', md: 'MD', markdown: 'MD', docx: 'DOC', txt: 'TXT', url: 'URL' };
  return map[ext] || '?';
}

function getFileIconClass(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const map = { pdf: 'pdf', md: 'md', markdown: 'md', docx: 'docx', txt: 'txt' };
  return map[ext] || 'txt';
}

function createFolderElement(kbId, kbName, documents, isActive) {
  const color = hashColor(kbId);
  const backColor = darken(color, 0.18);
  const paper1 = lighten('#ffffff', 0.06);
  const paper2 = lighten('#ffffff', 0.03);
  const paper3 = '#ffffff';

  const folder = document.createElement('div');
  folder.className = 'folder';
  folder.dataset.kbId = kbId;
  if (isActive) folder.classList.add('open');

  const totalChunks = documents.reduce((s, d) => s + d.chunks, 0);
  const arrow = isActive ? '▾' : '▸';

  folder.innerHTML = `
    <div class="folder__back" style="--folder-color:${color};--folder-back-color:${backColor};--paper-1:${paper1};--paper-2:${paper2};--paper-3:${paper3};">
      <div class="folder__front"></div>
      <div class="folder__front right"></div>
      <div class="folder__header">
        <span class="folder__title">${escapeHtml(kbName)}</span>
        <div class="folder__meta">
          <span class="folder__count">${documents.length} 文件 · ${totalChunks} 块</span>
          <span class="folder__arrow">${arrow}</span>
        </div>
      </div>
      <div class="folder__papers">
        ${documents.length === 0
          ? '<div class="folder__empty">拖拽文件到这里或粘贴链接添加资料</div>'
          : documents.map(doc => `
            <div class="folder__paper">
              <div style="display:flex;align-items:center;overflow:hidden;">
                <span class="file-icon ${getFileIconClass(doc.filename)}">${getFileIcon(doc.filename)}</span>
                <span class="folder__paper-name">${escapeHtml(doc.filename)}</span>
              </div>
              <span class="folder__paper-meta">${doc.chunks} 块</span>
            </div>
          `).join('')
        }
      </div>
    </div>
  `;

  folder.addEventListener('click', () => {
    const wasOpen = folder.classList.contains('open');
    document.querySelectorAll('.folder.open').forEach(f => f.classList.remove('open'));
    if (!wasOpen) {
      folder.classList.add('open');
      currentKbId = kbId;
      kbSelect.value = kbId;
      // Trigger KB switch: reset chat + load documents for this KB
      resetWorkspaceForKb();
      loadDocumentsForCurrentKb();
    } else {
      currentKbId = '';
      kbSelect.value = '';
      resetWorkspaceForKb();
      loadDocumentsForCurrentKb();
    }
  });

  folder.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      folder.click();
    }
  });

  return folder;
}

async function renderAllKbFolders() {
  try {
    const [kbsResp, docsResp] = await Promise.all([
      fetch('/api/kbs'),
      fetch(currentKbId ? `/api/kbs/${encodeURIComponent(currentKbId)}/documents` : '/api/documents'),
    ]);

    let kbs = [];
    if (kbsResp.ok) {
      const kbsData = await kbsResp.json();
      kbs = kbsData.kbs || [];
    }

    let currentDocs = [];
    if (docsResp.ok) {
      const docsData = await docsResp.json();
      currentDocs = docsData.documents || [];
    }

    // Build map: kb_id → documents
    const kbDocsMap = {};
    for (const kb of kbs) kbDocsMap[kb.id] = [];

    // Current KB's documents
    if (currentKbId) {
      kbDocsMap[currentKbId] = currentDocs;
    } else if (kbs.length > 0) {
      // Try to load default KB documents
      const defaultKb = kbs.find(k => k.id === 'default') || kbs[0];
      if (defaultKb) {
        try {
          const r = await fetch(`/api/kbs/${encodeURIComponent(defaultKb.id)}/documents`);
          if (r.ok) {
            const d = await r.json();
            kbDocsMap[defaultKb.id] = d.documents || [];
          }
        } catch {}
      }
    }

    // Handle documents not in any KB (legacy "default" without KB API)
    if (!currentKbId && kbs.length === 0) {
      kbDocsMap['_ungrouped'] = currentDocs;
    }

    folderView.innerHTML = '';

    // Header
    const header = document.createElement('div');
    header.className = 'folder-view-header';
    const totalKbs = kbs.length + (kbs.length === 0 && currentDocs.length > 0 ? 1 : 0);
    const totalDocs = Object.values(kbDocsMap).reduce((s, arr) => s + arr.length, 0);
    header.innerHTML = `
      <h3>知识库</h3>
      <span class="count">${totalKbs > 0 ? `${totalKbs} 个库 · ${totalDocs} 个文件` : ''}</span>
    `;
    folderView.appendChild(header);

    // Render each KB as a folder
    const view = document.createElement('div');
    view.className = 'folder-view';

    if (kbs.length === 0 && currentDocs.length > 0) {
      // No KBs yet, show ungrouped documents
      view.appendChild(createFolderElement('_ungrouped', '默认知识库', currentDocs, true));
    } else {
      for (const kb of kbs) {
        const docs = kbDocsMap[kb.id] || [];
        const isActive = kb.id === currentKbId;
        view.appendChild(createFolderElement(kb.id, kb.name, docs, isActive));
      }
    }

    folderView.appendChild(view);

    // Update indexed count
    indexedFileCount = totalDocs;
    if (indexedFileCount === 0) showEmptyState();
  } catch (err) {
    setIngestStatus({
      step: '加载知识库失败',
      percent: 0,
      message: err.message || '无法读取知识库结构。',
      hidden: false,
      error: true,
    });
  }
}

async function loadKbs() {
  kbSelect.innerHTML = '';
  try {
    const r = await fetch('/api/kbs');
    if (!r.ok) throw new Error('加载知识库失败');
    const data = await r.json();
    if (!data.kbs.length) {
      kbSelect.innerHTML = '<option value="">还没有知识库</option>';
      currentKbId = '';
      return;
    }
    data.kbs.forEach((kb) => {
      const opt = document.createElement('option');
      opt.value = kb.id;
      opt.textContent = `${kb.id} — ${kb.name}`;
      kbSelect.appendChild(opt);
    });
    const selected = data.kbs.find((kb) => kb.id === currentKbId)
      || data.kbs.find((kb) => kb.id === 'default')
      || data.kbs[0];
    kbSelect.value = selected.id;
    currentKbId = selected.id;
    await loadDocumentsForCurrentKb();
  } catch (err) {
    kbSelect.innerHTML = '<option value="">加载失败，请刷新</option>';
    currentKbId = '';
  }
}

function resetWorkspaceForKb() {
  sessionId = null;
  msgCounter = 0;
  indexedFileCount = 0;
  chat.innerHTML = '';
  showEmptyState();
  folderView.innerHTML = '';
  sources.clear();
  updateQueryAvailability();
  setIngestStatus({ hidden: true });
  closePanel();
}

function showEmptyState() {
  const empty = document.createElement('div');
  empty.id = 'empty-state';
  empty.className = 'empty-state';
  empty.innerHTML = `
    <div class="empty-title">先放一份材料进来</div>
    <p>上传课程 PDF、讲义或 Markdown 后，再像问助教一样提问。回答会带引用，点击引用可以回到原文。</p>
  `;
  chat.appendChild(empty);
}

function updateQueryAvailability() {
  const canAsk = indexedFileCount > 0;
  questionInput.disabled = !canAsk;
  submitButton.disabled = !canAsk;
  questionInput.placeholder = canAsk
    ? '例如：这篇文章的核心观点是什么？'
    : '先上传材料，然后问：这篇文章的核心观点是什么？';
}

async function loadDocumentsForCurrentKb() {
  // Fetch all KBs + their documents, render as folders
  await renderAllKbFolders();
  updateQueryAvailability();
}

function setIngestStatus({ step = '', percent = 0, message = '', hidden = false, error = false }) {
  ingestStatus.classList.toggle('hidden', hidden);
  ingestStatus.classList.toggle('error', error);
  const safePercent = Math.max(0, Math.min(100, percent));
  ingestStep.textContent = step;
  ingestPercent.textContent = `${safePercent}%`;
  ingestProgress.style.width = `${safePercent}%`;
  ingestMessage.textContent = message;
}

function setBusy(isBusy) {
  fileInput.disabled = isBusy;
  kbSelect.disabled = isBusy;
  kbNewName.disabled = isBusy;
  kbCreateBtn.disabled = isBusy;
  if (isBusy) {
    questionInput.disabled = true;
    submitButton.disabled = true;
  } else {
    updateQueryAvailability();
  }
}

kbSelect.addEventListener('change', async (e) => {
  currentKbId = e.target.value;
  resetWorkspaceForKb();
  await loadDocumentsForCurrentKb();
});

kbCreateBtn.addEventListener('click', async () => {
  const name = kbNewName.value.trim();
  if (!name) return;
  const r = await fetch('/api/kbs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!r.ok) {
    alert('创建知识库失败');
    return;
  }
  const created = await r.json();
  currentKbId = created.id;
  kbNewName.value = '';
  resetWorkspaceForKb();
  await loadKbs();
});

const urlInput = document.getElementById('url-input');
const urlSubmitBtn = document.getElementById('url-submit-btn');

if (urlSubmitBtn) {
  urlSubmitBtn.addEventListener('click', submitUrl);
  urlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); submitUrl(); }
  });
}

async function submitUrl() {
  const url = urlInput.value.trim();
  if (!url) return;

  setBusy(true);
  setIngestStatus({
    step: '提取链接内容',
    percent: 3,
    message: '正在识别平台并提取内容，请稍候...',
    hidden: false,
  });

  try {
    const r = await fetch('/api/ingest/url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, kb_id: currentKbId || undefined }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || '提交失败');

    const result = await waitForIngestJob(data.status_url);
    const title = result.result?.filename || url;
    sources.set(title, result.result.source_id);
    indexedFileCount += 1;
    const emptyState = document.getElementById('empty-state');
    if (emptyState) emptyState.remove();
    await renderAllKbFolders();
    setIngestStatus({
      step: '入库完成',
      percent: 100,
      message: `已解析 ${result.result.chunks} 个文本块，可以开始提问。`,
      hidden: false,
    });
    updateQueryAvailability();
    showSuggestedQuestions(title);
    urlInput.value = '';
  } catch (err) {
    setIngestStatus({
      step: '提取失败',
      percent: 100,
      message: err.message || '链接提取失败，请检查链接是否有效后重试。',
      hidden: false,
      error: true,
    });
  } finally {
    setBusy(false);
  }
}

// Upload
async function uploadFile(file) {
  setBusy(true);
  setIngestStatus({
    step: '上传文件',
    percent: 3,
    message: '正在把文件交给本地解析任务。',
    hidden: false,
  });

  try {
    const formData = new FormData();
    formData.append('file', file);
    const url = currentKbId
      ? `/api/kbs/${encodeURIComponent(currentKbId)}/ingest/jobs`
      : '/api/ingest/jobs';
    const started = await fetch(url, { method: 'POST', body: formData });
    const startedData = await started.json();
    if (!started.ok) throw new Error(startedData.detail || '上传失败');

    const data = await waitForIngestJob(startedData.status_url);
    sources.set(file.name, data.result.source_id);
    indexedFileCount += 1;
    const emptyState = document.getElementById('empty-state');
    if (emptyState) emptyState.remove();
    await renderAllKbFolders();
    setIngestStatus({
      step: '入库完成',
      percent: 100,
      message: `已解析 ${data.result.chunks} 个文本块，可以开始提问。`,
      hidden: false,
    });
    updateQueryAvailability();
    showSuggestedQuestions(file.name);
  } catch (err) {
    setIngestStatus({
      step: '入库失败',
      percent: 100,
      message: err.message || '上传或解析失败，请换一个文件再试。',
      hidden: false,
      error: true,
    });
  } finally {
    setBusy(false);
  }
}

const SUGGESTED_QUESTIONS_FALLBACK = [
  '这份材料的核心观点是什么？',
  '有哪些关键概念需要掌握？',
  '能举几个例子说明吗？',
];

async function showSuggestedQuestions(filename) {
  const existing = document.getElementById('suggested-questions');
  if (existing) existing.remove();

  let questions = SUGGESTED_QUESTIONS_FALLBACK;

  // Try LLM-generated questions if we have a filename and API key
  if (filename) {
    try {
      const chunksUrl = currentKbId
        ? `/api/kbs/${encodeURIComponent(currentKbId)}/documents/${encodeURIComponent(filename)}/chunks`
        : `/api/documents/${encodeURIComponent(filename)}/chunks`;
      const chunksResp = await fetch(chunksUrl);
      if (chunksResp.ok) {
        const chunksData = await chunksResp.json();
        if (chunksData.chunks && chunksData.chunks.length > 0) {
          const preview = chunksData.chunks.slice(0, 3).map(c => c.text).join('\n\n');
          const suggestResp = await fetch('/api/suggest-questions', {
            method: 'POST',
            headers: getApiHeaders(),
            body: JSON.stringify({ text: preview }),
          });
          if (suggestResp.ok) {
            const suggestData = await suggestResp.json();
            if (suggestData.questions && suggestData.questions.length > 0) {
              questions = suggestData.questions.slice(0, 3);
            }
          }
        }
      }
    } catch {
      // Fallback to static questions on any error
    }
  }

  const container = document.createElement('div');
  container.id = 'suggested-questions';
  container.className = 'suggested-questions';
  const label = document.createElement('div');
  label.className = 'suggested-label';
  label.textContent = '试试问这些问题：';
  container.appendChild(label);

  questions.forEach((q) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'suggest-chip';
    btn.textContent = q;
    btn.addEventListener('click', () => {
      questionInput.value = q;
      form.dispatchEvent(new Event('submit'));
    });
    container.appendChild(btn);
  });

  chat.appendChild(container);
  chat.scrollTop = chat.scrollHeight;
}

async function waitForIngestJob(statusUrl) {
  for (;;) {
    const r = await fetch(statusUrl);
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || '读取入库进度失败');
    setIngestStatus({
      step: readableIngestStep(data.step),
      percent: data.percent,
      message: data.message,
      hidden: false,
      error: data.status === 'failed',
    });
    if (data.status === 'completed') return data;
    if (data.status === 'failed') throw new Error(data.error || data.message || '入库失败');
    await sleep(650);
  }
}

function readableIngestStep(step) {
  return ({
    queued: '排队中',
    loading_model: '加载模型',
    saving: '保存文件',
    parsing: '解析文档',
    chunking: '切分文本',
    embedding: '生成向量',
    indexing: '写入索引',
    done: '入库完成',
    failed: '入库失败',
  })[step] || '处理中';
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

fileInput.addEventListener('change', (e) => {
  for (const f of e.target.files) uploadFile(f);
  fileInput.value = '';
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
  if (indexedFileCount === 0) {
    setIngestStatus({
      step: '请先上传资料',
      percent: 0,
      message: '当前知识库还没有可检索的文档。先上传课程材料，再开始提问。',
      hidden: false,
    });
    return;
  }

  addMessage('user', question);
  questionInput.value = '';
  questionInput.disabled = true;
  submitButton.disabled = true;
  const pending = addMessage('assistant', '正在检索当前知识库，并组织带引用的回答…');

  try {
    const endpoint = currentKbId
      ? `/api/kbs/${encodeURIComponent(currentKbId)}/query`
      : '/api/query';
    const body = { question, session_id: sessionId, top_k: 5, ...getApiOverrides() };
    const r = await fetch(endpoint, {
      method: 'POST',
      headers: getApiHeaders(),
      body: JSON.stringify(body),
    });
    const data = await r.json();
    if (!r.ok) {
      updateMessage(pending, data.detail || '请求失败，请稍后再试。');
      return;
    }
    sessionId = data.session_id;
    msgCounter += 2; // backend stores one user message + one assistant message
    updateMessage(pending, data.answer, data.citations, msgCounter);
  } catch (err) {
    updateMessage(pending, err.message || '请求失败，请检查服务是否仍在运行。');
  } finally {
    updateQueryAvailability();
    questionInput.focus();
  }
});

function addMessage(role, text, citations = []) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  renderMessage(div, role, text, citations);
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function updateMessage(div, text, citations = [], messageIndex = null) {
  renderMessage(div, 'assistant', text, citations, messageIndex);
  chat.scrollTop = chat.scrollHeight;
}

function renderMessage(div, role, text, citations = [], messageIndex = null) {
  div.innerHTML = '';
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
      let label = `[${i + 1}] ${c.source}`;
      if (c.section) {
        label += ` · ${c.section}`;
      } else if (c.page > 0) {
        label += ` · 第${c.page}页`;
      }
      chip.textContent = label;
      chip.addEventListener('click', () => openCitation(c.source, c.span, c.text, currentKbId));
      cits.appendChild(chip);
    });
    div.appendChild(cits);
  } else if (role === 'assistant' && messageIndex) {
    const warning = document.createElement('div');
    warning.className = 'source-warning';
    warning.textContent = '这条回答没有可追溯引用，不建议直接采信。';
    div.appendChild(warning);
  }

  // Export 按钮（仅已写入 session 的 assistant 消息）
  if (role === 'assistant' && sessionId && messageIndex) {
    const actions = document.createElement('div');
    actions.className = 'msg-actions';
    ['md', 'pdf'].forEach((fmt) => {
      const a = document.createElement('a');
      a.className = 'download-link';
      a.textContent = fmt === 'md' ? 'Download .md' : 'Download .pdf';
      a.href = `/api/sessions/${sessionId}/messages/${messageIndex}/export?format=${fmt}`;
      a.setAttribute('download', `uni-rag-msg-${messageIndex}.${fmt}`);
      actions.appendChild(a);
    });
    div.appendChild(actions);
  }
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

function openCitation(filename, span, citedText, kbId = '') {
  panelTitle.textContent = filename;
  panelBody.innerHTML = '<p style="color:var(--accent)">加载中…</p>';
  docPanel.classList.remove('hidden');
  docPanel.classList.add('open');
  docPanel.setAttribute('aria-hidden', 'false');

  const url = kbId
    ? `/api/kbs/${encodeURIComponent(kbId)}/documents/${encodeURIComponent(filename)}/chunks`
    : `/api/documents/${encodeURIComponent(filename)}/chunks`;

  fetch(url)
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

loadKbs();
