# uni-rag

学生用的通用 RAG 助手。上传文档，问问题，得到带高亮引用的答案，支持多轮追问。

## 启动

```bash
# 安装
uv sync

# 配 .env
cp .env.example .env
# 编辑 .env 填 ANTHROPIC_API_KEY

# 起 Web
uv run uni-rag serve

# CLI
uv run uni-rag ingest ./paper.pdf
uv run uni-rag ask "第三章讲什么"
uv run uni-rag ask "详细说说" -s <session-id>
```

## 测试

```bash
uv run pytest                                  # 跑全部
uv run pytest --cov=src/uni_rag --cov-report=term-missing  # 带 coverage
```

测试分层：
- `tests/unit/` — 各模块的单元测试（parsers, chunker, embedder, vector, bm25, retriever, reranker, client, session, locator, config, logging）
- `tests/integration/` — 端到端管线（ingest, query, API, CLI）
- `tests/bdd/` — BDD 行为用例（B1 上传 / B2 单文件问答 / B2+ 多轮追问 / B3 多文件 / B4 答不上来）

v0.1 coverage: **96%**（target 70%, 实际跑 `pytest --cov=src/uni_rag`）。

## Docker

```bash
# 1) 复制环境变量样板并填 ANTHROPIC_API_KEY
cp .env.example .env
# 编辑 .env

# 2) 一键起服务（首跑会构建镜像，~5-10 分钟下载模型）
docker compose up -d

# 3) 看日志
docker compose logs -f

# 4) 停服务
docker compose down
```

访问 `http://127.0.0.1:8766/`。

数据持久化到 named volume `uni-rag-data`；删除容器不丢数据。

## 路线图

- v0.1：PDF + Markdown 上传，单文件/多文件 Q&A，Notion AI 风格引用，多轮对话，Web + CLI
- v0.2：DOCX 支持，BM25 混合检索增强，reranker 优化
- v0.3：导出答案为 PDF/MD，跨 session 知识库，Docker 打包
