# IDA-MAS — Intelligent Document Analysis Multi-Agent System

> 面向非结构化文档的智能分析系统（MVP 阶段：RAG 检索增强生成）

IDA-MAS 是一个基于 **RAG（检索增强生成）** 的文档智能问答系统。上传 PDF / DOCX / TXT 文档后，即可用自然语言对文档内容进行提问，系统会基于原文给出精准回答并标注引用来源。

---

## 架构概览

```
┌──────────────────────────────────────┐
│           Frontend (HTML/JS)         │
│     Chat UI  +  Upload  +  Sources   │
└────────────────┬─────────────────────┘
                 │  REST API (/api/*)
┌────────────────▼─────────────────────┐
│        FastAPI Backend               │
│  ┌─────────────────────────────────┐│
│  │  RAG Pipeline                   ││
│  │  Query → Retrieve → Generate    ││
│  └───────────┬─────────────────────┘│
│              │                       │
│  ┌───────────▼──────┐ ┌────────────┐│
│  │ ChromaDB         │ │ LLM APIs   ││
│  │ (Vector Store)   │ │ DeepSeek    ││
│  │ 1024-dim (bge-m3)│ │ (Chat)      ││
│  └──────────────────┘ │ SiliconFlow ││
│                       │ (Embedding) ││
│                       └────────────┘│
└──────────────────────────────────────┘
```

### 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| RAG 框架 | LangChain |
| 向量数据库 | ChromaDB（本地持久化） |
| LLM（生成） | DeepSeek API (`deepseek-chat`) |
| Embedding | 硅基流动 API `BAAI/bge-m3`（免费，1024 维） |
| 前端 | 纯 HTML/CSS/JS（零框架依赖） |
| 文档解析 | PyPDF2 / python-docx |
| 容器化 | Docker + Docker Compose |

### 检索策略（MVP）

- **分块**：800 字符 / 150 字符重叠，中文语义分隔符优先
- **向量化**：BAAI/bge-m3（1024 维，8192 token 输入上限）
- **检索**：余弦相似度 Top-5
- **引用**：回答末尾标注 [来源文档名, 第X段]

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/ida-mas.git
cd ida-mas
```

### 2. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Key：

```env
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
SILICONFLOW_API_KEY=sk-your-siliconflow-api-key
```

> 两个 Key 都可以免费获取：
> - [DeepSeek API](https://platform.deepseek.com/) — 新用户有赠送额度
> - [硅基流动](https://www.siliconflow.cn/) — `BAAI/bge-m3` 完全免费

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

```bash
cd backend && uvicorn backend.main:app --reload --port 8000
```

或使用 Docker：

```bash
docker-compose up --build
```

### 5. 打开界面

浏览器访问 **http://localhost:8000**

---

## 使用方式

1. **上传文档**：在左侧面板拖拽或点击上传 PDF / DOCX / TXT 文件
2. **提问**：在右侧对话框输入自然语言问题
3. **查看来源**：回答下方的"引用来源"可展开查看原文片段

### 示例文档

`data/samples/` 目录下包含两份示例文档：

- `保险条款_示例.txt` — 人身意外伤害保险条款
- `金融监管法规_示例.txt` — 商业银行互联网贷款管理暂行办法

---

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/upload` | 上传文档（multipart/form-data） |
| `GET` | `/api/documents` | 列出已上传文档 |
| `DELETE` | `/api/documents/{name}` | 删除文档 |
| `POST` | `/api/chat` | 文档问答 |

### Chat 请求示例

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "保险理赔需要提供哪些材料？"}'
```

### 响应示例

```json
{
  "response": "根据保险条款第八条，被保险人申请理赔时需提供以下材料：\n1. 保险金给付申请书\n2. 保险单或保险凭证\n3. 有效身份证件\n4. 诊断证明、病历及医疗费用收据\n5. 如涉及身故，需提供死亡证明及户籍注销证明\n\n[来源: 保险条款_示例.txt, 第1段]",
  "sources": [
    {
      "document": "保险条款_示例.txt",
      "chunk_preview": "第八条 保险金申请...",
      "chunk_index": 0,
      "distance": 0.2183
    }
  ]
}
```

---

## 项目结构

```
ida-mas/
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理（环境变量）
│   ├── api/                     # API 端点
│   │   ├── chat.py              # POST /api/chat
│   │   ├── upload.py            # POST /api/upload
│   │   └── documents.py         # GET/DELETE /api/documents
│   ├── core/                    # 核心模块
│   │   ├── llm_client.py        # 双 API 客户端（DeepSeek + SiliconFlow）
│   │   ├── document_processor.py # PDF/DOCX/TXT 解析
│   │   ├── text_chunker.py      # 文本分块
│   │   ├── vector_store.py      # ChromaDB 操作
│   │   └── rag_pipeline.py      # RAG 检索与生成
│   ├── models/                  # Pydantic 模型
│   ├── utils/                   # 工具模块
│   └── static/                  # 前端静态文件
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
├── data/
│   ├── uploads/                 # 上传文件存储
│   ├── chroma/                  # 向量数据库
│   └── samples/                 # 示例文档
├── Dockerfile.backend
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 后续路线图

- [ ] **Phase 2** — 多 Agent 编排（路由/解析/检索/生成/校验）
- [ ] **Phase 2** — 混合检索（BM25 + Dense + Cross-Encoder Reranker）
- [ ] **Phase 2** — 自反思（Self-Reflection）与幻觉检测
- [ ] **Phase 3** — RAGAS 自动化评估
- [ ] **Phase 3** — 流式输出 + Redis 语义缓存
- [ ] **Phase 3** — 对话记忆与上下文管理

---

## 作者

**白祐丞** — 华中科技大学 人工智能与自动化学院 大三

- 技术栈：Python / PyTorch / CUDA / LLM / Agent / RAG
- GitHub：[your-username](https://github.com/your-username)

---

## License

MIT
