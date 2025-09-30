# Joblet MCP Server

MCP server for [Joblet](https://github.com/ehsaniara/joblet) job orchestration - enables AI assistants to manage distributed computing jobs through the Joblet platform.

## Quick Start

```bash
# Install
pip install joblet-mcp-server[sdk]

# Configure (~/.rnx/rnx-config.yml)
mkdir -p ~/.rnx
cp sample_config.yaml ~/.rnx/rnx-config.yml
# Edit with your Joblet server credentials

# Run
joblet-mcp-server
```

## Features

- 🚀 **Jobs** - Run, monitor, and manage compute jobs
- 🔄 **Workflows** - Orchestrate multi-job pipelines
- 💾 **Storage** - Create and manage persistent volumes
- 🌐 **Networks** - Configure isolated networks
- 📊 **Monitoring** - Real-time metrics and GPU status

## Configuration

Create `~/.rnx/rnx-config.yml`:

```yaml
version: "3.0"
nodes:
  default:
    address: "joblet-server.com:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      # Your client certificate
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      # Your private key
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      # Your CA certificate
      -----END CERTIFICATE-----
```

## Requirements

- Python 3.10+
- [Joblet server](https://github.com/ehsaniara/joblet) with TLS certificates
- Optional: `joblet-sdk` for better performance

## Documentation

- [Setup Guide](MCP_SETUP_GUIDE.md)
- [Sample Config](sample_config.yaml)

## License

MIT
