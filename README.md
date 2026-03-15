# 手机竞品分析（独立版）

GSMArena 查询、Profile 上传（PDF/DOCX 等）、产品库、价格批量更新、多机型对比与 AI 竞品报告。

## 目录结构

```
phone-competitor/
├── app/                 # 后端（FastAPI）
│   ├── main_phone.py    # 入口，运行此应用
│   ├── api/             # 接口
│   ├── models/          # 数据模型（仅手机相关）
│   ├── schemas/         # 请求/响应模型
│   └── services/        # 业务逻辑
├── frontend/            # 前端（Next.js）
├── data/                # SQLite 数据库目录（自动创建）
├── start.bat            # 一键启动（后端+前端）
├── start_backend.bat    # 仅启动后端 8000
├── start_frontend.bat   # 仅启动前端 3000
├── 创建桌面快捷方式.bat
├── create_shortcut.ps1
├── 安装到固定目录.bat
├── 安装说明.txt
├── requirements.txt
└── .env.example
```

## 快速开始

1. 安装 Python 3.10+、Node.js。
2. 进入本目录，创建虚拟环境并安装依赖：
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   cd frontend && npm install && cd ..
   ```
3. 复制 `.env.example` 为 `.env`，按需填写 `DEEPSEEK_API_KEY` 等。
4. 双击 **start.bat**，或先运行 start_backend.bat、再运行 start_frontend.bat。
5. 浏览器打开 http://localhost:3000。

## 固定安装与桌面图标

- 仅创建桌面图标：双击 **创建桌面快捷方式.bat**。
- 安装到固定目录（如 C:\PhoneCompetitor）并创建图标：双击 **安装到固定目录.bat**。  
详见 **安装说明.txt**。
