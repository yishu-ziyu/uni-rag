import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MatrixBackground from './components/MatrixBackground';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeMathjax from 'rehype-mathjax';
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
  Image as ImageIcon
} from 'lucide-react';

function App() {
  const [isWorkspaceMode, setIsWorkspaceMode] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [files, setFiles] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).substring(2, 15));
  const [messages, setMessages] = useState<{role: 'user'|'assistant', text: string, citations?: any[]}[]>([
    { role: 'assistant', text: '你好！我是你的 AI 助手，已阅读选中的文档。你可以向我提问，或者生成测验、总结。' }
  ]);

  const fetchFiles = () => {
    fetch('/api/files')
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

  const handleSend = async () => {
    if (!query.trim() || isLoading) return;

    const userMessage = query.trim();
    setQuery('');
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setIsLoading(true);

    let style = 'casual';
    if (activeTab === 'notes') style = 'concise';
    else if (activeTab === 'flashcards') style = 'bulleted';
    else if (activeTab === 'quiz') style = 'question';
    else if (activeTab === 'graph') style = 'structured';

    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage, style, session_id: sessionId })
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
      setMessages(prev => [...prev, { role: 'assistant', text: `❌ 错误: ${err.message || err}` }]);
    } finally {
      setIsLoading(false);
    }
  };

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
                  className="text-xl md:text-2xl text-slate-300 mb-12 max-w-2xl text-center drop-shadow-md px-4"
                >
                  万物皆可连接的智能知识库检索增强系统
                </motion.p>
                <motion.button
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  onClick={() => setIsWorkspaceMode(true)}
                  className="px-8 py-3 bg-white text-black font-semibold rounded-full hover:bg-slate-200 transition-colors shadow-lg cursor-pointer text-lg"
                >
                  进入工作区
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
                  <a href="http://127.0.0.1:8000/" className="block"><NavItem icon={<Home size={18} />} label="主页" /></a>
                  <NavItem icon={<Search size={18} />} label="发现" />
                  <NavItem icon={<FolderOpen size={18} />} label="我的文件夹" active />
                  <NavItem icon={<Layout size={18} />} label="工作台" />
                </div>

                {/* 下方来源文件列表 */}
                <div>
                  <div className="flex items-center justify-between px-2 mb-2">
                    <span className="text-xs font-semibold text-slate-500">选择来源 (全部)</span>
                    <label className="text-xs text-indigo-600 cursor-pointer hover:underline flex items-center">
                      <input
                        type="file"
                        className="hidden"
                        onChange={handleFileUpload}
                        disabled={isUploading}
                      />
                      {isUploading ? '正在处理...' : '上传文件'}
                    </label>
                  </div>
                  <div className="space-y-1">
                    {files.length > 0 ? files.map((file, i) => {
                      const fileName = typeof file === 'string' ? file : file.filename || file.name || `File ${i}`;
                      const isPdf = fileName.toLowerCase().endsWith('.pdf');
                      return (
                        <FileItem
                          key={i}
                          icon={isPdf ? <FileText size={16} className="text-red-500" /> : <File size={16} className="text-blue-500" />}
                          label={fileName}
                          active={i === 0}
                        />
                      );
                    }) : (
                      <div className="px-3 py-2 text-sm text-slate-400">加载中...</div>
                    )}
                  </div>
                </div>
              </div>

              {/* 底部设置 */}
              <div className="p-3 border-t border-slate-200">
                <NavItem icon={<Settings size={18} />} label="设置" />
              </div>
            </motion.div>

            {/* 中栏 - 预览 (flex-1) */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex-1 flex flex-col bg-white h-full relative border-r border-slate-200 min-w-0"
            >
              {/* 工具条 */}
              <div className="h-14 border-b border-slate-200 flex items-center px-4 justify-center bg-white shrink-0">
                <div className="flex bg-slate-100 rounded-lg p-1 space-x-1">
                  <ToolBtn label="原版" active />
                  <ToolBtn label="翻译" />
                  <ToolBtn label="文件转信息图" icon={<ImageIcon size={14} className="mr-1" />} />
                </div>
              </div>

              {/* PDF 占位区 */}
              <div className="flex-1 overflow-y-auto bg-slate-50 flex items-center justify-center p-8">
                <div className="bg-white w-full max-w-3xl h-full shadow-sm border border-slate-200 rounded-md flex flex-col items-center justify-center text-slate-400">
                  <FileText size={48} className="mb-4 text-slate-300" strokeWidth={1.5} />
                  <p className="text-lg font-medium text-slate-500">
                    {files.length > 0 ? (typeof files[0] === 'string' ? files[0] : files[0].filename || files[0].name || '文件预览') : '暂无文档预览'}
                  </p>
                  <p className="text-sm mt-2">文档预览占位符...</p>
                </div>
              </div>
            </motion.div>

            {/* 右栏 - 聊天与工具 (400px) */}
            <motion.div
              initial={{ x: 20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="w-[400px] flex flex-col bg-white h-full flex-shrink-0"
            >
              {/* Tabs */}
              <div className="h-14 border-b border-slate-200 flex items-center px-2 shrink-0 overflow-x-auto no-scrollbar">
                <TabItem active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} icon={<MessageSquare size={16} />} label="聊天" />
                <TabItem active={activeTab === 'notes'} onClick={() => setActiveTab('notes')} icon={<BookOpen size={16} />} label="笔记" />
                <TabItem active={activeTab === 'flashcards'} onClick={() => setActiveTab('flashcards')} icon={<Layers size={16} />} label="闪卡" />
                <TabItem active={activeTab === 'quiz'} onClick={() => setActiveTab('quiz')} icon={<HelpCircle size={16} />} label="测验" />
                <TabItem active={activeTab === 'graph'} onClick={() => setActiveTab('graph')} icon={<Network size={16} />} label="知识图谱" />
              </div>

              {/* 聊天内容区 */}
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
                          rehypePlugins={[rehypeMathjax]}
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
                                <span className="truncate pr-2">{c.metadata?.source || c.metadata?.filename || '未知文档'}</span>
                                {c.metadata?.page && <span className="text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-slate-500 whitespace-nowrap">第 {c.metadata.page} 页</span>}
                              </div>
                              <div className="text-slate-500 line-clamp-2 leading-relaxed" title={c.content}>"{c.content}"</div>
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
              </div>

              {/* 底部输入框与模型切换 */}
              <div className="p-4 border-t border-slate-100 bg-white">
                <div className="mb-2 flex items-center">
                  <button className="flex items-center text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors bg-slate-50 px-2 py-1 rounded-md border border-slate-200">
                    <Wand2 size={12} className="mr-1 text-indigo-500" />
                    Claude 3.5 Sonnet
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
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// 辅助组件
function NavItem({ icon, label, active = false }: { icon: React.ReactNode, label: string, active?: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm ${active ? 'bg-slate-200/60 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-200/40'}`}>
      <div className={active ? 'text-indigo-600' : 'text-slate-500'}>
        {icon}
      </div>
      <span>{label}</span>
    </div>
  );
}

function FileItem({ icon, label, active = false }: { icon: React.ReactNode, label: string, active?: boolean }) {
  return (
    <div className={`flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm ${active ? 'bg-indigo-50 border border-indigo-100 text-indigo-700 font-medium' : 'text-slate-600 hover:bg-slate-200/40 border border-transparent'}`}>
      {icon}
      <span className="truncate">{label}</span>
    </div>
  );
}

function ToolBtn({ label, active = false, icon = null }: { label: string, active?: boolean, icon?: React.ReactNode }) {
  return (
    <button className={`flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-all ${active ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'}`}>
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

export default App;
