# Task Manager MCP

## 项目简介

Task Manager MCP 是一个任务管理MCP(Model Context Protocol)服务，提供完整的任务生命周期管理能力，适用于复杂任务编排场景。

核心特性：
- 主任务/子任务层级化建模
- 任务状态机与全链路追踪
- 优先级调度机制（TODO）
- 实时进度监控（TODO）

## 多语言文档
- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

## 快速入门

### 环境要求
- Python 3.10+

### 通过 uv 安装
1. 安装 uv 包管理器：
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. 克隆仓库：
   ```bash
   git clone https://github.com/your-repo/task-manager-mcp.git
   cd task-manager-mcp
   ```

3. 同步依赖：
   ```bash
   uv sync
   ```

4. 启动服务：
   ```bash
   uv run mcp run main.py
   ```

## 使用指南

### MCP 服务集成

在 MCP 配置文件中注册服务：

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/task-manager-mcp",
        "run",
        "--with",
        "mcp",
        "mcp",
        "run",
        "main.py"
      ],
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

### Roo Code 扩展

项目提供 `.roomodes` 扩展定义文件，包含以下模式：

1. **TaskDecomposer**：复杂任务拆解与依赖分析
2. **TaskPlanner**：任务调度与执行跟踪

将本项目的 `.roomodes` 内容合并至您的项目配置中即可启用。

## 开发指南

### 项目结构

```
task-manager-mcp/
├── models/               # 数据模型层
│   ├── __init__.py
│   ├── metadata.py       # 元数据模型
│   └── task.py           # 任务领域模型
├── server/               # 服务端实现
│   ├── __init__.py
│   ├── mcp.py            # MCP 协议适配层
│   └── tools.py          # MCP 工具集
├── tests/                # 测试套件
│   ├── test_models/      # 模型单元测试
│   └── test_server/      # 服务集成测试
├── .gitignore
├── LICENSE.md
├── main.py               # 服务入口点
├── pyproject.toml        # 项目元数据
└── uv.lock               # 依赖版本锁
```

### 依赖版本控制

项目使用 `uv.lock` 文件进行确定性依赖安装，该文件由 uv 工具自动维护，请勿手动修改。

### 测试

```bash
uv test
```

## 贡献指引

欢迎通过 GitHub 协作流程参与贡献：

1. Fork 主仓库
2. 创建特性分支 (`git checkout -b feat/NewFeature`)
3. 提交原子化修改 (`git commit -m 'feat: Implement NewFeature'`)
4. 推送至远程仓库 (`git push origin feat/NewFeature`)
5. 创建 Pull Request

## 开源协议

本项目基于 [Apache 2.0 协议](LICENSE.md) 开源。

## 技术支持

发现问题或建议改进？请通过以下渠道反馈：
- 提交 GitHub Issue

## 项目维护

Task Manager MCP 由 [@druid0523](https://github.com/druid0523) 开发和维护。
