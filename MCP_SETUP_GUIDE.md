# Joblet MCP Server Setup Guide

Quick setup guide for the Joblet MCP Server.

## Prerequisites

- **Python 3.10+**
- **Joblet server** with TLS certificates
- **Client certificate, private key, and CA certificate**

## Installation

```bash
# Install MCP server
pip install joblet-mcp-server

# Verify installation
joblet-mcp-server --help
```

## Configuration

### 1. Create Configuration Directory

```bash
mkdir -p ~/.rnx
```

### 2. Create Configuration File

Create `~/.rnx/rnx-config.yml`:

```yaml
version: "3.0"

nodes:
  default:
    address: "your-joblet-server.example.com:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      # Copy your complete client certificate here
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      # Copy your complete private key here
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      # Copy your complete CA certificate here
      -----END CERTIFICATE-----

  # Optional: viewer node for read-only access
  viewer:
    address: "your-joblet-server.example.com:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      # Viewer client certificate
      -----END CERTIFICATE-----
    # ... (same format as above)
```

### 3. Secure Configuration

```bash
chmod 600 ~/.rnx/rnx-config.yml
```

**Important Notes:**
- Use `|` for multiline certificate strings
- Include complete certificates with BEGIN/END lines
- Replace placeholder content with actual certificates

## Usage

### Start Server

```bash
# Default (SDK-based)
joblet-mcp-server

# CLI-based alternative
joblet-mcp-server-cli

# Custom config
joblet-mcp-server --config /path/to/config.yml

# Specific node
joblet-mcp-server --node viewer

# Debug mode
joblet-mcp-server --debug
```

### Integration with Claude Desktop

Add to Claude Desktop config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "joblet": {
      "command": "joblet-mcp-server",
      "args": [],
      "env": {}
    }
  }
}
```

For custom configuration:

```json
{
  "mcpServers": {
    "joblet": {
      "command": "joblet-mcp-server",
      "args": ["--config", "/path/to/config.yml"],
      "env": {}
    },
    "joblet-viewer": {
      "command": "joblet-mcp-server",
      "args": ["--node", "viewer"],
      "env": {}
    }
  }
}
```

## Testing

### Test Configuration

```bash
# Test config syntax
python -c "import yaml; yaml.safe_load(open('~/.rnx/rnx-config.yml'.replace('~', '$(echo $HOME)')))"

# Test server startup
joblet-mcp-server
# Press Ctrl+C to exit
```

### Test Connection

```bash
# If you have rnx binary
rnx node list

# Test with SDK
python -c "from joblet import JobletClient; client = JobletClient(node_name='default'); print('✓ Connection successful')"
```

### Test MCP Tools

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run interactive tests
python scripts/test-mcp-tools.py --interactive

# Test specific tools
python scripts/test-mcp-tools.py --tool joblet_list_nodes
```

## Troubleshooting

### Common Issues

**Configuration file not found:**
```bash
ls -la ~/.rnx/rnx-config.yml
mkdir -p ~/.rnx  # Create if missing
```

**Connection failed:**
```bash
# Check server connectivity
ping your-joblet-server.example.com
telnet your-joblet-server.example.com 50051

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('$(echo $HOME)/.rnx/rnx-config.yml'))"
```

**Module not found:**
```bash
# Reinstall dependencies
pip uninstall joblet-mcp-server
pip install joblet-mcp-server

# Verify installation
python -c "from joblet_mcp_server.server_sdk import JobletMCPServerSDK; print('✓ SDK server available')"
```

**No response from MCP server:**
```bash
# Test server directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "list_tools", "params": {}}' | joblet-mcp-server

# Check debug output
joblet-mcp-server --debug
```

### Debug Mode

Enable detailed logging:

```bash
# Debug output
joblet-mcp-server --debug

# Environment variable
export JOBLET_DEBUG=1
joblet-mcp-server
```

## Multiple Environments

```bash
# Development
joblet-mcp-server --config ~/.rnx/dev-config.yml

# Production
joblet-mcp-server --config ~/.rnx/prod-config.yml
```

## Docker Deployment

```dockerfile
FROM python:3.11-slim

RUN pip install joblet-mcp-server

COPY rnx-config.yml /root/.rnx/rnx-config.yml
RUN chmod 600 /root/.rnx/rnx-config.yml

CMD ["joblet-mcp-server"]
```

## Security Best Practices

1. **Certificate Management**
   - Use separate certificates per environment
   - Monitor certificate expiration
   - Rotate certificates regularly

2. **File Permissions**
   ```bash
   chmod 600 ~/.rnx/rnx-config.yml
   chmod 700 ~/.rnx/
   ```

3. **Access Control**
   - Use viewer nodes for read-only access
   - Validate server certificates
   - Use VPN or private networks when possible

## Support

- **Repository**: https://github.com/ehsaniara/joblet-mcp-server
- **Issues**: https://github.com/ehsaniara/joblet-mcp-server/issues
- **Documentation**: See README and examples in repository