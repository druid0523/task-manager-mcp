# Task Manager MCP

## Project Overview

Task Manager MCP is a task management server based on the Model Context Protocol (MCP). It provides a complete solution for creating, managing, and tracking tasks, suitable for various application scenarios that require task management.

Main features include:
- Create and manage main tasks
- Add and track sub-tasks
- Task status management
- Task priority setting [To be developed]
- Task progress tracking [To be developed]

## README.md
- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

## Quick Start

### Installation Requirements
- Python 3.10 or higher

### Installation using uv tool
1. Install uv tool:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the project:
   ```bash
   git clone https://github.com/your-repo/task-manager-mcp.git
   cd task-manager-mcp
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Run the project:
   ```bash
   uv run mcp run main.py
   ```

## Project Structure

```
task-manager-mcp/
├── models/               # Data models
│   ├── __init__.py
│   ├── metadata.py       # Metadata management
│   └── task.py           # Task model
├── server/               # Server implementation
│   ├── __init__.py
│   ├── mcp.py            # MCP server
│   └── tools.py          # Tool implementation
├── tests/                # Test code
│   ├── test_models/      # Model tests
│   └── test_server/      # Server tests
├── .gitignore
├── LICENSE.md
├── main.py               # Entry file
├── pyproject.toml        # Project configuration
└── uv.lock               # Dependency lock file
```

## Configuration Guide

### Using uv.lock for dependency management
The uv.lock file is used to lock project dependencies, ensuring consistency across different environments. Do not edit this file manually.

## Usage Guide

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

### Adding Main Tasks
Use the `add_main_task` tool to add a main task:
```json
{
  "project_dir": "/path/to/project",
  "name": "Project Development",
  "description": "Complete project development tasks"
}
```

### Adding Sub-tasks
Use the `add_sub_task` tool to add sub-tasks to a main task:
```json
{
  "project_dir": "/path/to/project",
  "main_task_id": 1,
  "sub_task_number": 1,
  "sub_task_name": "Requirement Analysis"
}
```

### Getting Task List
Use the `list_main_tasks` tool to get all main tasks:
```json
{
  "project_dir": "/path/to/project"
}
```

## Development Guide

Run tests:
   ```bash
   uv test
   ```

## Contribution Guide

We welcome contributions of all kinds! Please follow these steps:

1. Fork the project repository
2. Create your feature branch (`git checkout -b feat/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feat/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Support

If you encounter any issues or have any suggestions, please contact us through:
- Submit an issue on GitHub

## About

Task Manager MCP is created and maintained by druid0523.
