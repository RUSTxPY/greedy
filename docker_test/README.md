# Docker Benchmarking & Resource Monitoring

This folder contains tools to test the performance and resource efficiency of the Greedy API running in a container.

## 🛠️ Prerequisites & Setup

Run the setup script first to ensure all dependencies and permissions are correct:
```bash
./setup.sh
```

## 🏃 How to Run the Test

### 1. Start the API Server
If you have permission issues with Docker, use `sudo`:
```bash
sudo docker-compose up -d
```

### 2. Monitor Resource Usage
Open a new terminal and run:
```bash
sudo docker stats greedy-test-greedy-api-1
```

### 3. Run the Benchmark
**Important**: Use the project's virtual environment python to ensure `httpx` is available:
```bash
../.venv/bin/python benchmark.py
```

## 📊 Troubleshooting

### "Permission denied" on docker.sock
This means your user doesn't have permission to talk to the Docker daemon. 
**Quick Fix**: Run docker commands with `sudo`.
**Permanent Fix**: `sudo usermod -aG docker $USER` (requires a full logout/login to take effect).

### "ModuleNotFoundError: No module named 'httpx'"
This happens if you use the system python instead of the project's virtual environment. Always use `../.venv/bin/python` for tests in this folder.
