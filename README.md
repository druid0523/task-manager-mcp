# Task Manager MCP

## Overview

Task Manager MCP is a task management service based on the MCP (Model Context Protocol), offering full lifecycle management capabilities for complex task orchestration scenarios.

Key Features:
- Hierarchical task/subtask modeling

## Documentation
- en [English](README.md)
- zh_CN [简体中文](README.zh_CN.md)

## Quick Start

### Prerequisites
- Python 3.10+

### Installation via uv
1. Install uv package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone repository:
   ```bash
   git clone https://github.com/your-repo/task-manager-mcp.git
   cd task-manager-mcp
   ```

3. Sync dependencies:
   ```bash
   uv sync
   ```

4. Start service:
   ```bash
   uv run mcp run main.py
   ```

## Usage Guide

### MCP Service Integration

Register service in MCP configuration:

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

### Roo Code Extension

The project provides `.roomodes` configuration with modes:

1. **TaskDecomposer**: Task decomposition & dependency analysis
2. **TaskPlanner**: Task scheduling & execution tracking

Merge the `.roomodes` configuration into your project to enable these modes.

## Development

### Project Structure

```
task-manager-mcp/
├── models/               # Data models
│   ├── __init__.py
│   ├── metadata.py       # Metadata schema
│   └── task.py           # Task domain model
├── server/               # Server implementation
│   ├── __init__.py
│   ├── mcp.py            # MCP protocol adapter
│   └── tools.py          # MCP toolchain
├── tests/                # Test suites
│   ├── test_models/      # Model unit tests
│   └── test_server/      # Server integration tests
├── .gitignore
├── LICENSE.md
├── main.py               # Service entrypoint
├── pyproject.toml        # Project metadata
└── uv.lock               # Dependency lockfile
```

### Dependency Management

The `uv.lock` file ensures deterministic dependency resolution. This file is automatically managed by uv - do not edit manually.

### Testing

```bash
pytest tests/ -v
```

## Contributing

We welcome contributions through GitHub flow:

1. Fork the repository
2. Create feature branch (`git checkout -b feat/NewFeature`)
3. Commit atomic changes (`git commit -m 'feat: Implement NewFeature'`)
4. Push to the branch (`git push origin feat/NewFeature`)
5. Open a Pull Request

## License

Distributed under [Apache 2.0 License](LICENSE.md).

## Support

Found an issue or have suggestions? Please:
- Open a GitHub Issue

## Maintainers

Task Manager MCP is developed and maintained by [@druid0523](https://github.com/druid0523).
