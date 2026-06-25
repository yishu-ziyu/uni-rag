import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MatrixBackground from './components/MatrixBackground';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import "katex/dist/katex.min.css";
import {
  Home,
  Search,
  FolderOpen,
  Settings,
  FileText,
  File,
  ChevronDown,
  Layout,
  MessageSquare,
  BookOpen,
  Layers,
  HelpCircle,
  Network,
  Send,
  Wand2,
  Image as ImageIcon,
  Loader2,
  PlayCircle,
  Tv,
  Globe,
  Link2
} from 'lucide-react';

function App() {
  const [isWorkspaceMode, setIsWorkspaceMode] = useState(false);
  const [showHome, setShowHome] = useState(false);
  const [activeTab, setActiveTab] = useState('files');
  const [files, setFiles] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [documentContent, setDocumentContent] = useState<string>('');
  const [isLoadingDoc, setIsLoadingDoc] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => {
    const stored = localStorage.getItem('uni-rag-session-id');
    if (stored) return stored;
    const newId = Math.random().toString(36).substring(2, 15);
    localStorage.setItem('uni-rag-session-id', newId);
    return newId;
  });
  const [messages, setMessages] = useState<{role: 'user'|'assistant', text: string, citations?: any[]}[]>([
    { role: 'assistant', text: '你好！我是你的 AI 助手，已阅读选中的文档。你可以向我提问，或者生成测验、总结。' }
  ]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('uni-rag-api-key') || '');
  const [showDiscover, setShowDiscover] = useState(false);
  const [providers, setProviders] = useState<{id: string, name: string, model: string}[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>(() => localStorage.getItem('uni-rag-provider') || 'minimax');
  const [urlInput, setUrlInput] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [urlJobs, setUrlJobs] = useState<Map<string, {status: string; percent: number; message: string; filename: string; error?: string}>>(new Map());

  useEffect(() => {
    localStorage.setItem('uni-rag-provider', selectedProvider);
  }, [selectedProvider]);

  useEffect(() => {
    fetch('/api/providers')
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.providers)) {
          setProviders(data.providers);
          const valid = data.providers.find((p: any) => p.id === selectedProvider);
          if (!valid) {
            setSelectedProvider(data.providers[0]?.id || 'minimax');
          }
        }
      })
      .catch(() => {});
  }, []);

  const fetchFiles = () => {
    fetch('/api/sources')
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.documents)) {
          setFiles(data.documents);
        } else if (Array.isArray(data)) {
          setFiles(data);
        } else if (data && Array.isArray(data.files)) {
          setFiles(data.files);
        }
      })
      .catch(err => console.error('Failed to fetch files:', err));
  };

  const getPlatformIcon = (url: string) => {
    if (/youtube\.com|youtu\.be/.test(url)) return <PlayCircle size={16} className="text-red-500" />;
    if (/bilibili\.com/.test(url)) return <Tv size={16} className="text-pink-500" />;
    return <Globe size={16} className="text-slate-500" />;
  };

  const getPlatformLabel = (url: string) => {
    if (/youtube\.com|youtu\.be/.test(url)) return 'YouTube 视频';
    if (/bilibili\.com/.test(url)) return 'Bilibili 视频';
    return '网页内容';
  };

  const fetchDocumentContent = async (filename: string) => {
    setIsLoadingDoc(true);
    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}/chunks`);
      if (!res.ok) throw new Error('获取文档内容失败');
      const data = await res.json();
      const text = data.chunks?.map((c: any) => c.text).join('\n\n') || '';
      setDocumentContent(text);
    } catch (err: any) {
      console.error('Fetch document error:', err);
      setDocumentContent('');
    } finally {
      setIsLoadingDoc(false);
    }
  };

  const handleFileSelect = (filename: string) => {
    setSelectedFile(filename);
    fetchDocumentContent(filename);
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/ingest', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`上传失败: ${res.status}`);
      }
      // 上传成功后刷新文件列表
      fetchFiles();
    } catch (err: any) {
      console.error('File upload error:', err);
      alert(err.message || '上传文件时发生错误');
    } finally {
      setIsUploading(false);
      // 清空 input，以便可以重复上传同一文件
      if (e.target) {
        e.target.value = '';
      }
    }
  };

  const handleUrlIngest = async () => {
    const url = urlInput.trim();
    if (!url || isUploading) return;

    setIsUploading(true);
    setUrlInput('');
    // 不立即收起输入框，让 job card 能渲染

    try {
      const res = await fetch('/api/ingest/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      if (!res.ok) {
        let errText = '';
        try { errText = await res.text(); } catch(e) {}
        throw new Error(errText || `请求失败: ${res.status}`);
      }
      const data = await res.json();
      const jobId = data.job_id;

      setUrlJobs(prev => {
        const next = new Map(prev);
        next.set(jobId, {
          status: 'queued',
          percent: 1,
          message: '已收到链接，准备开始提取。',
          filename: url,
        });
        return next;
      });

      // 首轮轮询后再收起输入框
      setShowUrlInput(false);

      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(`/api/ingest/jobs/${jobId}`);
          if (!statusRes.ok) throw new Error('轮询失败');
          const job = await statusRes.json();

          setUrlJobs(prev => {
            const next = new Map(prev);
            if (job.status === 'completed' || job.status === 'failed') {
              clearInterval(pollInterval);
              if (job.status === 'completed') {
                next.set(jobId, {
                  status: job.status,
                  percent: job.percent,
                  message: job.message,
                  filename: job.filename || url,
                });
                fetchFiles();
                // 成功状态延迟 2 秒后清理
                setTimeout(() => {
                  setUrlJobs(p => {
                    const n = new Map(p);
                    n.delete(jobId);
                    return n;
                  });
                }, 2000);
              } else {
                // 失败状态保持可见，等用户再次提交时再清除
                next.set(jobId, {
                  status: job.status,
                  percent: job.percent,
                  message: job.message,
                  filename: job.filename || url,
                  error: job.error,
                });
              }
              return next;
            }
            next.set(jobId, {
              status: job.status,
              percent: job.percent,
              message: job.message,
              filename: job.filename || url,
            });
            return next;
          });
        } catch {
          clearInterval(pollInterval);
        }
      }, 1500);

    } catch (err: any) {
      alert(err.message || '链接入站时发生错误');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSend = async () => {
    if (!query.trim() || isLoading) return;

    const userMessage = query.trim();
    setQuery('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setIsLoading(true);

    let style = 'casual';
    if (activeTab === 'notes') style = 'concise';
    else if (activeTab === 'flashcards') style = 'academic';
    else if (activeTab === 'quiz') style = 'concise';
    else if (activeTab === 'graph') style = 'academic';

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage, style, session_id: sessionId, provider: selectedProvider })
      });

      if (!res.ok) {
        let errText = '';
        try { errText = await res.text(); } catch(e) {}
        throw new Error(errText || `请求失败: ${res.status}`);
      }

      const data = await res.json();
      const answer = data.answer || data.response || data.text || JSON.stringify(data);
      const citations = data.citations || [];
      setMessages(prev => [...prev, { role: 'assistant', text: answer, citations }]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: `抱歉，模型调用失败。这通常是因为未配置该模型的 API Key，或网络问题。\n\n**错误详情**：\`${err.message || err}\`\n\n💡 **提示**：请点击左下角「设置」检查是否已正确配置。`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleModeSend = async (mode: string) => {
    if (!selectedFile) return;
    setIsLoading(true);
    try {
      const body: any = {
        question: documentContent.slice(0, 3000),
        mode,
        session_id: sessionId,
        provider: selectedProvider
      };
      if (apiKey) body.api_key = apiKey;
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`请求失败: ${res.status}`);
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.answer || '',
        citations: mode === 'chat' ? (data.citations || []) : []
      }]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: `抱歉，模型调用失败。\n\n**错误详情**：\`${err.message}\`\n\n💡 **提示**：请点击左下角「设置」检查 API Key。`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSuggestQuestions = async () => {
    if (!documentContent) return [];
    try {
      const res = await fetch('/api/suggest-questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: documentContent.slice(0, 5000), provider: selectedProvider }),
      });
      if (!res.ok) return [];
      const data = await res.json();
      return data.questions || [];
    } catch {
      return [];
    }
  };

  const hasFiles = files.length > 0 || urlJobs.size > 0;

  return (
    <div className="flex h-screen w-full overflow-hidden bg-white text-slate-800 font-sans relative">
      <AnimatePresence mode="wait">
        {!isWorkspaceMode ? (
          <motion.div
            key="landing"
            className="absolute inset-0 z-50 flex items-center justify-center bg-black"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            <motion.div
              layoutId="hero-banner"
              className="relative w-full h-full flex flex-col items-center justify-center overflow-hidden"
            >
              <div className="absolute inset-0">
                <MatrixBackground />
              </div>
              <div className="absolute inset-0 flex flex-col items-center justify-center z-20 bg-black/40">
                <motion.h1
                  layoutId="hero-title"
                  className="text-7xl md:text-[120px] font-bold tracking-tighter mb-4 text-white drop-shadow-2xl"
                >
                  uni-rag
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="text-xl md:text-2xl text-slate-300 font-light tracking-wide mb-2 max-w-2xl mx-auto px-4"
                >
                  面向中文研究者的私有文档工作站
                </motion.p>
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                  className="text-sm md:text-base text-slate-400 max-w-xl mx-auto mb-10 px-4"
                >
                  数据不出域的本地 RAG · 模型自由选择 · 国内直连可用
                </motion.p>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="flex flex-col sm:flex-row items-center justify-center gap-6 mb-12 text-sm text-slate-300"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center border border-slate-700/50 backdrop-blur-sm">
                      <FolderOpen size={18} className="text-indigo-400" />
                    </div>
                    <span className="text-left leading-tight font-medium">数据主权<br/><span className="text-slate-500 text-xs font-normal">文档永远存本地杜绝泄露</span></span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center border border-slate-700/50 backdrop-blur-sm">
                      <Wand2 size={18} className="text-purple-400" />
                    </div>
                    <span className="text-left leading-tight font-medium">模型自由<br/><span className="text-slate-500 text-xs font-normal">MiniMax / StepFun / 本地模型</span></span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center border border-slate-700/50 backdrop-blur-sm">
                      <Globe size={18} className="text-emerald-400" />
                    </div>
                    <span className="text-left leading-tight font-medium">多源直连<br/><span className="text-slate-500 text-xs font-normal">PDF / YouTube / B站 无缝混合</span></span>
                  </div>
                </motion.div>

                <motion.button
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  onClick={() => setIsWorkspaceMode(true)}
                  className="px-8 py-3 bg-white text-black font-semibold rounded-full hover:bg-slate-200 transition-colors shadow-lg cursor-pointer text-lg flex items-center gap-2"
                >
                  进入工作区
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        ) : (
          <motion.div
            key="workspace"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex h-screen w-full relative z-10"
          >
            {/* 左栏 - 导航 (260px) */}
            <motion.div
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="w-[260px] flex flex-col border-r border-slate-200 bg-[#F9F9F9] h-full flex-shrink-0"
            >
              {/* 缩小版的 hero-banner */}
              <motion.div
                layoutId="hero-banner"
                className="relative h-20 border-b border-slate-200 overflow-hidden cursor-pointer flex-shrink-0"
                onClick={() => setIsWorkspaceMode(false)}
                title="返回首页"
              >
                <div className="absolute inset-0 pointer-events-none opacity-50">
                  <MatrixBackground />
                </div>
                <div className="absolute inset-0 flex items-center justify-center z-20 bg-black/60 hover:bg-black/50 transition-colors">
                  <motion.h1
                    layoutId="hero-title"
                    className="text-2xl font-bold text-white tracking-tighter drop-shadow-md"
                  >
                    uni-rag
                  </motion.h1>
                </div>
              </motion.div>

              {/* 顶部功能分类 */}
              <div className="p-3 flex-1 overflow-y-auto">
                <div className="space-y-1 mb-6">
                  <div className="block cursor-pointer" onClick={() => setShowHome(true)}><NavItem icon={<Home size={18} />} label="主页" /></div>
                  <NavItem icon={<Search size={18} />} label="发现" onClick={() => setShowDiscover(true)} />
                  <NavItem icon={<FolderOpen size={18} />} label="我的文件夹" active={!showHome && activeTab === 'files'} />
                  <NavItem icon={<Layout size={18} />} label="工作台" />
                </div>

                {/* 来源入口 */}
                <div className="mb-6">
                  {/* URL 输入 */}
                  <AnimatePresence>
                    {showUrlInput && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-2 overflow-hidden"
                      >
                        <div className="flex gap-1.5 px-2">
                          <input
                            type="text"
                            value={urlInput}
                            onChange={e => setUrlInput(e.target.value)}
                            onKeyDown={e => { if (e.key === 'Enter') handleUrlIngest(); }}
                            placeholder="粘贴链接..."
                            className="flex-1 text-xs border border-slate-200 rounded-lg px-2.5 py-1.5 bg-white focus:border-indigo-400 focus:outline-none"
                            autoFocus
                          />
                          <button
                            onClick={handleUrlIngest}
                            disabled={isUploading || !urlInput.trim()}
                            className="px-2.5 py-1.5 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors"
                          >
                            添加
                          </button>
                          <button
                            onClick={() => { setShowUrlInput(false); setUrlInput(''); }}
                            className="px-2 py-1.5 text-slate-400 hover:text-slate-600 text-xs"
                          >
                            ✕
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* 上传按钮行 */}
                  <div className="flex items-center justify-between px-2 mb-2">
                    <span className="text-xs font-semibold text-slate-500">来源</span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setShowUrlInput(!showUrlInput)}
                        className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                        title="添加链接"
                      >
                        <Link2 size={13} />
                      </button>
                      <motion.label
                        className="text-xs text-indigo-600 cursor-pointer hover:underline flex items-center gap-1.5"
                        whileTap={{ scale: 0.95 }}
                      >
                        <AnimatePresence mode="wait">
                          {isUploading ? (
                            <motion.span
                              key="uploading"
                              initial={{ opacity: 0, y: -4 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: 4 }}
                              transition={{ duration: 0.2 }}
                              className="flex items-center gap-1.5"
                            >
                              <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                              >
                                <Loader2 size={14} />
                              </motion.div>
                              <span>处理中</span>
                            </motion.span>
                          ) : (
                            <motion.span
                              key="upload"
                              initial={{ opacity: 0, y: -4 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: 4 }}
                              transition={{ duration: 0.2 }}
                            >
                              上传文件
                            </motion.span>
                          )}
                        </AnimatePresence>
                        <input
                          id="file-upload-input"
                          type="file"
                          className="hidden"
                          onChange={handleFileUpload}
                          disabled={isUploading}
                        />
                      </motion.label>
                    </div>
                  </div>

                  {/* 来源列表 */}
                  <div className="space-y-1">
                    {files.length === 0 && [...urlJobs.values()].filter(j => j.status === 'queued' || j.status === 'running').length === 0 ? (
                      <div className="px-3 py-2 text-sm text-slate-400">暂无来源</div>
                    ) : (
                      <>
                        {/* 文件 + URL 来源 */}
                        {files.map((file, i) => {
                          const fileName = typeof file === 'string' ? file : file.filename || file.name || `File ${i}`;
                          const isUrl = typeof file === 'object' && file.format === 'url';
                          const platform = typeof file === 'object' ? file.platform : '';
                          const icon = isUrl
                            ? getPlatformIcon(platform)
                            : fileName.toLowerCase().endsWith('.pdf')
                              ? <FileText size={16} className="text-red-500" />
                              : <File size={16} className="text-blue-500" />;
                          return (
                            <FileItem
                              key={`src-${i}-${fileName}`}
                              icon={icon}
                              label={fileName}
                              active={selectedFile === fileName}
                              onClick={() => handleFileSelect(fileName)}
                            />
                          );
                        })}
                        {/* 处理中的链接任务 */}
                        {[...urlJobs.entries()].map(([jobId, job]) => {
                          if (job.status === 'completed') return null;
                          const isRunning = job.status === 'queued' || job.status === 'running';
                          return (
                            <div key={`url-${jobId}`} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${isRunning ? 'bg-indigo-50 border border-indigo-100' : 'bg-red-50 border border-red-100'}`}>
                              {isRunning ? (
                                <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
                                  <Loader2 size={16} className="text-indigo-500" />
                                </motion.div>
                              ) : (
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                              )}
                              {isRunning && getPlatformIcon(job.filename)}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1.5">
                                  {isRunning && (
                                    <span className="text-[10px] font-medium text-indigo-600 bg-indigo-100 px-1 rounded">{getPlatformLabel(job.filename)}</span>
                                  )}
                                  <span className={`truncate text-xs ${isRunning ? 'text-indigo-700' : 'text-red-600'}`}>
                                    {isRunning ? job.message : (job.error || '处理失败')}
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* 底部设置 */}
              <div className="p-3 border-t border-slate-200">
                <NavItem icon={<Settings size={18} />} label="设置" onClick={() => setSettingsOpen(true)} />
              </div>
            </motion.div>

            {/* 中栏 - 预览 (flex-1) */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex-1 flex flex-col bg-white h-full relative border-r border-slate-200 min-w-0"
            >
              {showHome ? (
                /* 欢迎引导页 */
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex-1 overflow-y-auto p-8"
                >
                  <div className="max-w-2xl mx-auto">
                    <h2 className="text-2xl font-bold text-slate-800 mb-2">你的文档，你的模型，你的规则。</h2>
                    <p className="text-slate-500 mb-8 font-medium">NotebookLM 把文件上传到 Google？uni-rag 不。</p>

                    <div className="space-y-6">
                      {/* 步骤 1 */}
                      <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-semibold text-sm shrink-0">1</div>
                        <div>
                          <h3 className="font-semibold text-slate-800 mb-1">上传文档</h3>
                          <p className="text-sm text-slate-500 leading-relaxed">在左侧「我的文件夹」面板点击「上传文件」，选择一份 PDF 或 Markdown 文档。系统会自动解析、切分并建立索引。</p>
                        </div>
                      </div>

                      {/* 步骤 2 */}
                      <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-semibold text-sm shrink-0">2</div>
                        <div>
                          <h3 className="font-semibold text-slate-800 mb-1">选择来源</h3>
                          <p className="text-sm text-slate-500 leading-relaxed">上传完成后，文档会出现在左侧文件列表中。点击选中它，AI 就会基于这份文档来回答你的问题。</p>
                        </div>
                      </div>

                      {/* 步骤 3 */}
                      <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-semibold text-sm shrink-0">3</div>
                        <div>
                          <h3 className="font-semibold text-slate-800 mb-1">开始提问</h3>
                          <p className="text-sm text-slate-500 leading-relaxed">在右侧对话框输入你的问题，AI 会从文档中找到相关内容并给出答案，同时标注引用来源。你可以继续追问，对话上下文会保留。</p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-10 pt-6 border-t border-slate-200">
                      <button
                        onClick={() => setShowHome(false)}
                        className="px-5 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        去上传文档
                      </button>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="flex flex-col h-full">
                  {/* 工具条 */}
                  <div className="h-14 border-b border-slate-200 flex items-center px-4 justify-center bg-white shrink-0">
                    <div className="flex bg-slate-100 rounded-lg p-1 space-x-1">
                      <ToolBtn label="原版" active />
                      {hasFiles && (
                        <>
                          <ToolBtn label="翻译" onClick={() => handleModeSend('translate')} />
                          <ToolBtn label="文件转信息图" icon={<ImageIcon size={14} className="mr-1" />} />
                        </>
                      )}
                    </div>
                  </div>

                  {selectedFile ? (
                    <div className="flex-1 overflow-y-auto bg-slate-50 flex flex-col">
                      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white shrink-0">
                        <span className="text-sm font-medium text-slate-700 truncate">{selectedFile}</span>
                        <button
                          onClick={() => { setSelectedFile(null); setDocumentContent(''); }}
                          className="text-slate-400 hover:text-slate-600 transition-colors p-1"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                      </div>
                      <div className="flex-1 overflow-y-auto p-6">
                        {isLoadingDoc ? (
                          <div className="flex items-center justify-center h-full text-slate-400 text-sm">加载中...</div>
                        ) : selectedFile.toLowerCase().endsWith('.md') ? (
                          <div className="prose prose-slate max-w-none text-sm leading-relaxed">
                            <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>
                              {documentContent}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-relaxed font-mono">{documentContent}</pre>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 overflow-y-auto bg-slate-50 flex items-center justify-center p-8">
                      <div className="bg-white w-full max-w-3xl h-full shadow-sm border border-slate-200 rounded-md flex flex-col items-center justify-center text-slate-400">
                        <FolderOpen size={48} className="mb-4 text-slate-300" strokeWidth={1.5} />
                        <p className="text-lg font-medium text-slate-500 mb-6">
                          你的第一个知识库
                        </p>

                        <button
                          onClick={() => document.getElementById('file-upload-input')?.click()}
                          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium flex items-center gap-2 mb-8 transition-colors shadow-sm"
                        >
                          <FileText size={18} />
                          上传第一份文档
                        </button>

                        <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-xs font-medium border border-green-100">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                          所有数据仅存于本地，不上传任何第三方服务器
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>

            {/* 右栏 - 聊天与工具 (400px) */}
            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="w-[400px] flex flex-col bg-white h-full flex-shrink-0"
            >
              {showHome ? (
                /* 引导页右侧 - 产品说明 */
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex-1 overflow-y-auto p-6"
                >
                  <div className="max-w-sm">
                    <h3 className="text-lg font-semibold text-slate-800 mb-4">为什么选 uni-rag？</h3>
                    <div className="space-y-4">
                      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-3 opacity-10">
                          <FolderOpen size={48} />
                        </div>
                        <div className="flex items-center gap-2 mb-1.5 relative z-10">
                          <div className="w-6 h-6 rounded-md bg-indigo-100 flex items-center justify-center">
                            <FolderOpen size={14} className="text-indigo-600" />
                          </div>
                          <span className="font-medium text-sm text-slate-800">数据不出域</span>
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed relative z-10">
                          你的论文、商业合同永远停留在你自己的机器上，不会上传到任何第三方平台。这是你的私有知识库。
                        </p>
                      </div>
                      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-3 opacity-10">
                          <Wand2 size={48} />
                        </div>
                        <div className="flex items-center gap-2 mb-1.5 relative z-10">
                          <div className="w-6 h-6 rounded-md bg-purple-100 flex items-center justify-center">
                            <Wand2 size={14} className="text-purple-600" />
                          </div>
                          <span className="font-medium text-sm text-slate-800">模型选择自由</span>
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed relative z-10">
                          根据需求无缝切换 MiniMax、StepFun 甚至本地模型。学术推理用聪明的，日常问答用便宜的。
                        </p>
                      </div>
                      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-3 opacity-10">
                          <Globe size={48} />
                        </div>
                        <div className="flex items-center gap-2 mb-1.5 relative z-10">
                          <div className="w-6 h-6 rounded-md bg-emerald-100 flex items-center justify-center">
                            <Globe size={14} className="text-emerald-600" />
                          </div>
                          <span className="font-medium text-sm text-slate-800">国内直连可用</span>
                        </div>
                        <p className="text-xs text-slate-500 leading-relaxed relative z-10">
                          无需繁琐的网络配置。原生接入国内领先大模型 API，速度快且稳定，告别网络连接烦恼。
                        </p>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="flex flex-col h-full">
                  {/* Tabs */}
                  <div className="h-14 border-b border-slate-200 flex items-center px-2 shrink-0 overflow-x-auto no-scrollbar">
                    <TabItem active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} icon={<MessageSquare size={16} />} label="聊天" />
                    {hasFiles && (
                      <>
                        <TabItem active={activeTab === 'notes'} onClick={() => setActiveTab('notes')} icon={<BookOpen size={16} />} label="笔记" />
                        <TabItem active={activeTab === 'flashcards'} onClick={() => setActiveTab('flashcards')} icon={<Layers size={16} />} label="闪卡" />
                        <TabItem active={activeTab === 'quiz'} onClick={() => setActiveTab('quiz')} icon={<HelpCircle size={16} />} label="测验" />
                        <TabItem active={activeTab === 'graph'} onClick={() => setActiveTab('graph')} icon={<Network size={16} />} label="知识图谱" />
                      </>
                    )}
                  </div>
                  <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-white">
                    {messages.map((msg, idx) => (
                      <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'self-end max-w-[85%]' : 'self-start max-w-[85%]'}`}>
                        <div
                          className={
                            msg.role === 'user'
                              ? "bg-indigo-50 border border-indigo-100 rounded-2xl rounded-tr-sm p-3 text-sm text-indigo-900"
                              : "bg-slate-100 rounded-2xl rounded-tl-sm p-3 text-sm text-slate-700 leading-relaxed markdown-content"
                          }
                        >
                          {msg.role === 'user' ? (
                            msg.text
                          ) : (
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm, remarkMath]}
                              rehypePlugins={[rehypeKatex]}
                            >
                              {msg.text}
                            </ReactMarkdown>
                          )}
                        </div>
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="mt-2 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200 self-start w-full">
                            <div className="font-semibold mb-1 text-slate-600 flex items-center">
                              <BookOpen size={12} className="mr-1" />
                              来源参考
                            </div>
                            <ul className="space-y-2 mt-2">
                              {msg.citations.map((c: any, i: number) => (
                                <li key={i} className="bg-white p-2 rounded border border-slate-100 shadow-sm">
                                  <div className="font-medium text-indigo-600 mb-0.5 flex justify-between items-center">
                                    <span className="truncate pr-2">{c.source || '未知文档'}</span>
                                    {c.page && <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-500 whitespace-nowrap">第 {c.page} 页</span>}
                                  </div>
                                  <div className="text-slate-500 line-clamp-2 leading-relaxed" title={c.text}>"{c.text}"</div>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                    {isLoading && (
                      <div className="bg-slate-100 rounded-2xl rounded-tl-sm p-3 text-sm max-w-[85%] self-start text-slate-500">
                        处理中...
                      </div>
                    )}

                    {/* Tab-specific content */}
                    {activeTab === 'flashcards' && messages.length > 1 && (() => {
                      try {
                        const cards = JSON.parse(messages[messages.length - 1].text);
                        if (Array.isArray(cards)) {
                          return (
                            <div className="grid grid-cols-2 gap-3">
                              {cards.map((card: any, i: number) => (
                                <div key={i} className="bg-white border border-slate-200 rounded-lg p-3 text-sm">
                                  <div className="font-medium text-slate-700 mb-1">{card.question || card.q || '卡片'}</div>
                                  <div className="text-slate-500 text-xs">{card.answer || card.a || ''}</div>
                                </div>
                              ))}
                            </div>
                          );
                        }
                      } catch {}
                      return null;
                    })()}

                    {activeTab === 'quiz' && messages.length > 1 && (() => {
                      try {
                        const quiz = JSON.parse(messages[messages.length - 1].text);
                        if (Array.isArray(quiz)) {
                          return (
                            <div className="space-y-3">
                              {quiz.map((q: any, i: number) => (
                                <div key={i} className="bg-white border border-slate-200 rounded-lg p-3 text-sm">
                                  <div className="font-medium text-slate-700 mb-2">{q.question || q.q}</div>
                                  <div className="space-y-1">
                                    {(q.options || q.choices || []).map((opt: string, j: number) => (
                                      <div key={j} className={`px-2 py-1 rounded text-xs ${j === (q.correct ?? q.answer) ? 'bg-green-50 text-green-700 font-medium' : 'text-slate-500'}`}>
                                        {opt}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          );
                        }
                      } catch {}
                      return null;
                    })()}

                    {activeTab === 'graph' && messages.length > 1 && (() => {
                      try {
                        const graphData = JSON.parse(messages[messages.length - 1].text);
                        const nodes = graphData.nodes || graphData.entities || [];
                        const edges = graphData.edges || graphData.relations || [];
                        if (nodes.length > 0) {
                          const cx = 200, cy = 150;
                          const radius = Math.min(cx, cy) - 20;
                          const positions = nodes.map((_: any, i: number) => ({
                            x: cx + radius * Math.cos(2 * Math.PI * i / nodes.length - Math.PI / 2),
                            y: cy + radius * Math.sin(2 * Math.PI * i / nodes.length - Math.PI / 2)
                          }));
                          return (
                            <div className="bg-white border border-slate-200 rounded-lg p-2 overflow-auto">
                              <svg viewBox="0 0 400 300" className="w-full max-w-md mx-auto">
                                {edges.map((e: any, i: number) => {
                                  const srcIdx = nodes.findIndex((n: any) => n.id === e.source || n === e.source);
                                  const tgtIdx = nodes.findIndex((n: any) => n.id === e.target || n === e.target);
                                  if (srcIdx >= 0 && tgtIdx >= 0 && positions[srcIdx] && positions[tgtIdx]) {
                                    return <line key={i} x1={positions[srcIdx].x} y1={positions[srcIdx].y} x2={positions[tgtIdx].x} y2={positions[tgtIdx].y} stroke="#94a3b8" strokeWidth="1.5" />;
                                  }
                                  return null;
                                })}
                                {nodes.map((n: any, i: number) => {
                                  const label = n.name || n.label || n.id || '';
                                  const short = String(label).slice(0, 6);
                                  if (!positions[i]) return null;
                                  return (
                                    <g key={i}>
                                      <circle cx={positions[i].x} cy={positions[i].y} r="22" fill="#eef2ff" stroke="#6366f1" strokeWidth="1.5" />
                                      <text x={positions[i].x} y={positions[i].y + 1} textAnchor="middle" fontSize="10" fill="#334155" dominantBaseline="middle">{short}</text>
                                    </g>
                                  );
                                })}
                              </svg>
                            </div>
                          );
                        }
                      } catch {}
                      return null;
                    })()}

                  </div>

                  {/* 底部输入框与模型切换 */}
                  <div className="p-4 border-t border-slate-100 bg-white">
                    <div className="mb-2 flex items-center">
                      <button className="flex items-center text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors bg-slate-50 px-2 py-1 rounded-md border border-slate-200">
                        <Wand2 size={12} className="mr-1 text-indigo-500" />
                        {providers.find(p => p.id === selectedProvider)?.name || selectedProvider}
                        <ChevronDown size={12} className="ml-1 opacity-70" />
                      </button>
                    </div>
                    <div className="relative flex items-end border border-slate-300 rounded-xl bg-white shadow-sm focus-within:border-indigo-400 focus-within:ring-1 focus-within:ring-indigo-400 transition-all overflow-hidden">
                      <textarea
                        className="w-full max-h-32 min-h-[44px] py-3 pl-4 pr-12 bg-transparent text-sm resize-none outline-none"
                        placeholder="向文档提问..."
                        rows={1}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSend();
                          }
                        }}
                      />
                      <button
                        onClick={handleSend}
                        disabled={isLoading || !query.trim()}
                        className="absolute right-2 bottom-2 p-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-lg transition-colors"
                      >
                        <Send size={16} />
                      </button>
                    </div>
                    <div className="mt-2 text-center text-[10px] text-slate-400">
                      AI 可能会犯错，请核对重要信息。
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Settings Modal */}
      {settingsOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center" onClick={() => setSettingsOpen(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-semibold mb-4">设置</h3>
            <label className="block mb-4">
              <span className="text-sm text-slate-600">模型</span>
              <select
                value={selectedProvider}
                onChange={e => setSelectedProvider(e.target.value)}
                className="mt-1 w-full border rounded-lg px-3 py-2 text-sm bg-white"
              >
                {providers.map(p => (
                  <option key={p.id} value={p.id}>{p.name} ({p.model})</option>
                ))}
              </select>
            </label>
            <label className="block mb-4">
              <span className="text-sm text-slate-600">API Key（选填，留空则用服务端默认配置）</span>
              <input
                type="password"
                value={apiKey}
                onChange={e => { setApiKey(e.target.value); localStorage.setItem('uni-rag-api-key', e.target.value); }}
                className="mt-1 w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="输入你的 API Key"
              />
            </label>
            <div className="flex justify-end">
              <button onClick={() => setSettingsOpen(false)} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm">关闭</button>
            </div>
          </div>
        </div>
      )}

      {/* Discover Overlay */}
      {showDiscover && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center" onClick={() => setShowDiscover(false)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-lg shadow-xl max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">发现可能的问题</h3>
              <button onClick={() => setShowDiscover(false)} className="text-slate-400 hover:text-slate-600 text-xl">&times;</button>
            </div>
            {selectedFile ? (
              <DiscoverPanel documentContent={documentContent} selectedProvider={selectedProvider} />
            ) : (
              <p className="text-sm text-slate-500">请先选择一个文件</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// 辅助组件
function NavItem({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
  return (
    <div onClick={onClick} className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm ${active ? 'bg-slate-200/60 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-200/40'}`}>
      <div className={active ? 'text-indigo-600' : 'text-slate-500'}>
        {icon}
      </div>
      <span>{label}</span>
    </div>
  );
}

function FileItem({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
  return (
    <div onClick={onClick} className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm ${active ? 'bg-indigo-50 border border-indigo-100 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-200/40 border border-transparent'}`}>
      {icon}
      <span className="truncate">{label}</span>
    </div>
  );
}

function ToolBtn({ label, active = false, icon = null, onClick }: { label: string, active?: boolean, icon?: React.ReactNode, onClick?: () => void }) {
  return (
    <button onClick={onClick} className={`flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-all ${active ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'}`}>
      {icon}
      {label}
    </button>
  );
}

function TabItem({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${active ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'}`}
    >
      {icon}
      {label}
    </button>
  );
}

function DiscoverPanel({ documentContent, selectedProvider }: { documentContent: string, selectedProvider: string }) {
  const [questions, setQuestions] = React.useState<string[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (!documentContent) return;
    setLoading(true);
    fetch('/api/suggest-questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: documentContent.slice(0, 5000), provider: selectedProvider }),
    })
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data && data.questions) setQuestions(data.questions); })
      .finally(() => setLoading(false));
  }, [documentContent]);

  if (loading) return <div className="text-sm text-slate-500 py-4">正在分析文档...</div>;
  if (questions.length === 0) return <p className="text-sm text-slate-500">暂无可推荐问题</p>;

  return (
    <ul className="space-y-2">
      {questions.map((q, i) => (
        <li key={i} className="bg-slate-50 p-2.5 rounded-lg text-sm text-slate-700 border border-slate-100">{q}</li>
      ))}
    </ul>
  );
}

export default App;
