# 🚀 Greedy [metasearch]

[![Python >= 3.10](https://img.shields.io/badge/python->=3.10-red.svg)](https://www.python.org/)
[![Build Native Extensions](https://github.com/RUSTxPY/greedy/actions/workflows/build-native.yml/badge.svg)](https://github.com/RUSTxPY/greedy/actions/workflows/build-native.yml)
[![Publish Docker Image](https://github.com/RUSTxPY/greedy/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/RUSTxPY/greedy/actions/workflows/docker-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Greedy [metasearch]** (Legacy: DDGS) is a high-performance, distributed metasearch engine and library. It aggregates results from dozens of search providers, optimized with a **Rust-native core** for blazing fast text normalization and ranking.

---

## ✨ Key Features

- 🏎️ **High Performance**: Native Rust extensions for heavy-duty text processing.
- 🌐 **Distributed (DHT)**: Optional P2P distributed cache network to share results and bypass rate limits.
- 🔌 **Versatile**: Use as a Python library, a standalone CLI, a FastAPI-powered REST API, or an MCP server.
- 📦 **Zero-Config Docker**: Official prebuilt images with native binaries included.
- 🔍 **Multi-Engine**: Aggregates Bing, Google, DuckDuckGo, Brave, Wikipedia, and more.

---

## ⚡ Quick Start

### Python Library
```bash
pip install -U ddgs
```
```python
from ddgs import DDGS

results = DDGS().text("python programming", max_results=5)
for r in results:
    print(f"{r['title']} -> {r['href']}")
```

### Docker (Recommended)
Run the full API server instantly with zero local dependencies:
```bash
docker run -p 8000:8000 ghcr.io/rustxpy/greedy:main
```

---

## 🛠️ Installation & Usage

### 1. CLI Usage
The `greedy` command is your entry point for all operations.
```bash
greedy --help

# Search directly from terminal
greedy text -q "future of AI" --max-results 5

# Start API server
greedy api --host 0.0.0.0 --port 8000
```

### 2. API Server
Greedy includes a production-ready FastAPI server with built-in Swagger documentation.

- **Endpoints**: `/search/text`, `/search/images`, `/search/news`, `/search/videos`, `/extract`
- **Documentation**: Access `/docs` or `/redoc` on your running server.

### 3. MCP Server (AI Agent Tool)
Integrate Greedy into AI tools like Claude Desktop or Cursor:
```json
{
  "mcpServers": {
    "greedy": {
      "command": "greedy",
      "args": ["mcp"]
    }
  }
}
```

---

## 🌐 DHT Network (Beta)
Greedy features an optional P2P cache. When enabled, nodes share search results anonymously.
- **Why?**: Avoid engine rate limits and get **50ms** response times for common queries.
- **Setup**: `pip install ddgs[dht]` (Requires Linux/macOS).

---

## 🧩 Supported Engines

| Category | Providers |
|----------|-----------|
| **Text** | Bing, Brave, DuckDuckGo, Google, Grokipedia, Mojeek, Yandex, Wikipedia |
| **Media**| Bing (Images/News), DuckDuckGo (Images/Videos/News), Yahoo (News) |
| **Books**| Anna's Archive |

---

## 🤝 Credits & Disclaimer
Greedy is built upon the excellent foundation of **DDGS** (Dux Distributed Global Search) by [deedy5](https://github.com/deedy5/ddgs). This project maintains the core vision while adding modern CI/CD, Rust-native optimizations, and streamlined deployment.

*This library is for educational purposes only. Always respect the Terms of Service of the search providers.*

---
[Go to Top](#top)
