# Task Manager MCP

## 项目简介

Task Manager MCP 是一个基于 Model Context Protocol (MCP) 的任务管理服务器。它提供了创建、管理和跟踪任务的完整解决方案，适用于各种需要任务管理的应用场景。

主要功能包括：
- 创建和管理主任务
- 添加和跟踪子任务
- 任务状态管理
- 任务优先级设置\[待开发\]
- 任务进度跟踪\[待开发\]

## README.md
- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

## 快速开始

### 安装要求
- Python 3.10 或更高版本

### 使用 uv 工具安装
1. 安装 uv 工具：
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. 克隆项目：
   ```bash
   git clone https://github.com/your-repo/task-manager-mcp.git
   cd task-manager-mcp
   ```

3. 安装依赖：
   ```bash
   uv sync
   ```

4. 运行项目：
   ```bash
   uv run mcp run main.py
   ```

## 项目结构

```
task-manager-mcp/
├── models/               # 数据模型
│   ├── __init__.py
│   ├── metadata.py       # 元数据管理
│   └── task.py           # 任务模型
├── server/               # 服务器实现
│   ├── __init__.py
│   ├── mcp.py            # MCP 服务器
│   └── tools.py          # 工具实现
├── tests/                # 测试代码
│   ├── test_models/      # 模型测试
│   └── test_server/      # 服务器测试
├── .gitignore
├── LICENSE.md
├── main.py               # 入口文件
├── pyproject.toml        # 项目配置
└── uv.lock               # 依赖锁定文件
```

## 配置说明

### 使用 uv.lock 管理依赖
uv.lock 文件用于锁定项目依赖，确保在不同环境下安装的一致性。不要手动编辑此文件。

## 使用指南

## MCP Integration

Add the server to your MCP settings

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/libingxi/Documents/Projects/task-manager-mcp",
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


### 添加主任务
使用 `add_main_task` 工具添加主任务：
```json
{
  "project_dir": "/path/to/project",
  "name": "项目开发",
  "description": "完成项目开发任务"
}
```

### 添加子任务
使用 `add_sub_task` 工具为主任务添加子任务：
```json
{
  "project_dir": "/path/to/project",
  "main_task_id": 1,
  "sub_task_number": 1,
  "sub_task_name": "需求分析"
}
```

### 获取任务列表
使用 `list_main_tasks` 工具获取所有主任务：
```json
{
  "project_dir": "/path/to/project"
}
```

## 开发指南

运行测试：
   ```bash
   uv test
   ```

## 贡献指南

我们欢迎任何形式的贡献！请遵循以下步骤：

1. Fork 项目仓库
2. 创建特性分支 (`git checkout -b feat/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feat/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE.md](LICENSE.md) 文件。

## 支持

如果您遇到任何问题或有任何建议，请通过以下方式联系我们：
- 在 GitHub 上提交 issue

## 关于

Task Manager MCP 由 druid0523 创建并维护。
