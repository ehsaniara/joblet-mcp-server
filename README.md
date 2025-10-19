# Joblet MCP Server

MCP server for [Joblet](https://github.com/ehsaniara/joblet) job orchestration - enables AI assistants to manage distributed computing jobs through the Joblet platform.

## Quick Start

```bash
# Install (SDK mode - recommended)
pip install joblet-mcp-server[sdk]

# Configure (~/.rnx/rnx-config.yml)
mkdir -p ~/.rnx
cp sample_config.yaml ~/.rnx/rnx-config.yml
# Edit with your Joblet server credentials

# Run (SDK mode)
joblet-mcp-server
```

## Features

- **Jobs** - Run, monitor, and manage compute jobs
- **Workflows** - Orchestrate multi-job pipelines
- **Storage** - Create and manage persistent volumes
- **Networks** - Configure isolated networks
- **Monitoring** - Real-time metrics and GPU status

## Implementation Modes

The MCP server provides two implementations for communicating with Joblet:

### 1. SDK Mode (Recommended)

**Command**: `joblet-mcp-server`

Uses [joblet-sdk-python](https://github.com/ehsaniara/joblet-sdk-python) for direct gRPC communication with the Joblet server.

**Advantages**:
- Better performance (direct gRPC, no subprocess overhead)
- Type safety and error handling
- Automatic connection management
- Streams data efficiently

**Requirements**:
- Install with SDK: `pip install joblet-mcp-server[sdk]`
- Requires joblet-sdk-python >= 2.0.0 (proto v2.3.0+)

### 2. CLI Mode (Alternative)

**Command**: `joblet-mcp-server-cli`

Uses subprocess calls to the `rnx` CLI binary.

**Advantages**:
- Works without Python SDK
- Uses existing CLI tools
- Simpler deployment if `rnx` already installed

**Requirements**:
- Install without SDK: `pip install joblet-mcp-server`
- Requires `rnx` binary in PATH or specify with `--rnx-binary`
- Configure via `~/.rnx/rnx-config.yml`

**Usage**:
```bash
# Use rnx from PATH
joblet-mcp-server-cli

# Specify custom rnx binary location
joblet-mcp-server-cli --rnx-binary /path/to/rnx
```

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

### Common Requirements
- Python 3.10+
- [Joblet server](https://github.com/ehsaniara/joblet) with TLS certificates
- Configuration file at `~/.rnx/rnx-config.yml`

### SDK Mode (Recommended)
- [joblet-sdk-python](https://github.com/ehsaniara/joblet-sdk-python) >= 2.0.0 (installed automatically with `[sdk]` extra)
- Direct gRPC communication (port 50051)

### CLI Mode (Alternative)
- `rnx` binary installed and in PATH
- No Python SDK required

## Documentation

- [Sample Config](sample_config.yaml)
- [Usage Examples](examples/usage_examples.md)

## License

MIT
