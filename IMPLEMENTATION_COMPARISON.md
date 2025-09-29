# Joblet MCP Server Implementation Comparison

This document compares the two implementations of the Joblet MCP Server and explains when to use each.

## Overview

The Joblet MCP Server is available in two implementations:

1. **SDK-based Server** (`joblet-mcp-server-sdk`) - **Recommended**
2. **CLI-based Server** (`joblet-mcp-server`) - Legacy

## SDK-based Server (Recommended)

### Features
- **Direct Integration**: Uses `joblet-sdk-python` directly for gRPC communication
- **Better Performance**: No subprocess overhead, native async operations
- **Type Safety**: Full Python type checking and validation
- **Rich Error Handling**: Detailed error messages and stack traces
- **Native Configuration**: Reads `~/.rnx/rnx-config.yml` directly
- **Better Resource Management**: Efficient connection pooling and cleanup

### Configuration
The SDK-based server reads configuration directly from `~/.rnx/rnx-config.yml`:

```yaml
version: "3.0"

nodes:
  default:
    address: "your-server:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      # ... embedded client certificate ...
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      # ... embedded private key ...
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      # ... embedded CA certificate ...
      -----END CERTIFICATE-----
```

### Usage
```bash
# Default configuration (~/.rnx/rnx-config.yml)
joblet-mcp-server-sdk

# Custom configuration file
joblet-mcp-server-sdk --config /path/to/config.yml

# Use specific node
joblet-mcp-server-sdk --node viewer

# Debug mode
joblet-mcp-server-sdk --debug
```

### Dependencies
- `joblet-sdk-python` - Direct SDK integration
- `mcp>=1.0.0` - Model Context Protocol support
- `pydantic>=2.0.0` - Data validation

### Advantages
- ✅ **Native Performance**: Direct gRPC calls without subprocess overhead
- ✅ **Better Error Handling**: Python exceptions with full stack traces
- ✅ **Type Safety**: Full type checking and validation
- ✅ **Resource Efficiency**: Connection pooling and proper cleanup
- ✅ **Async Native**: True async/await support throughout
- ✅ **Configuration Validation**: Built-in validation of config file format
- ✅ **Debugging**: Easy to debug with Python debuggers

### Disadvantages
- ❌ **Dependency**: Requires joblet-sdk-python installation
- ❌ **Python Only**: Limited to Python environment

## CLI-based Server (Legacy)

### Features
- **Binary Calls**: Uses subprocess calls to `rnx` binary
- **No SDK Dependency**: Works with any rnx installation
- **Cross-language**: Can work with rnx binaries from any language
- **JSON Output**: Parses JSON output from rnx commands

### Configuration
Requires `rnx` binary in PATH and uses the same `~/.rnx/rnx-config.yml` file.

### Usage
```bash
# Default rnx binary and configuration
joblet-mcp-server

# Custom rnx binary path
joblet-mcp-server --rnx-binary /path/to/rnx

# Custom configuration file
joblet-mcp-server --config /path/to/config.yml

# Use specific node
joblet-mcp-server --node viewer
```

### Dependencies
- `rnx` binary in PATH
- `asyncio-subprocess` - Subprocess handling
- `mcp>=1.0.0` - Model Context Protocol support

### Advantages
- ✅ **No SDK Dependency**: Works with standalone rnx binary
- ✅ **Language Agnostic**: Can use rnx binaries from any implementation
- ✅ **Simpler Deployment**: Just needs rnx binary
- ✅ **CLI Compatibility**: Uses exact same CLI interface as manual usage

### Disadvantages
- ❌ **Performance Overhead**: Subprocess creation and JSON parsing
- ❌ **Error Handling**: Limited to CLI error messages
- ❌ **Resource Usage**: Higher memory and CPU usage
- ❌ **Debugging Difficulty**: Harder to debug subprocess calls
- ❌ **Type Safety**: String-based parsing without validation

## When to Use Each

### Use SDK-based Server When:
- ✅ You want the **best performance** and resource efficiency
- ✅ You need **detailed error handling** and debugging capabilities
- ✅ You're developing in a **Python environment**
- ✅ You want **type safety** and validation
- ✅ You need **long-running** server instances
- ✅ You want **native async/await** support

### Use CLI-based Server When:
- ✅ You **cannot install** joblet-sdk-python
- ✅ You have **existing rnx deployments** to reuse
- ✅ You need **exact CLI compatibility** with manual usage
- ✅ You're in a **constrained environment** where SDK installation is difficult
- ✅ You want to **minimize Python dependencies**

## Performance Comparison

| Feature | SDK-based | CLI-based |
|---------|-----------|-----------|
| **Job Submission** | ~10ms | ~50-100ms |
| **Status Check** | ~5ms | ~30-50ms |
| **Memory Usage** | Low | Medium |
| **CPU Overhead** | Minimal | Process creation overhead |
| **Error Response Time** | Immediate | After subprocess completion |
| **Connection Reuse** | Yes | No (new process each time) |

## Migration Guide

### From CLI-based to SDK-based

1. **Install SDK dependency**:
   ```bash
   pip install joblet-sdk-python
   ```

2. **Update start command**:
   ```bash
   # Old
   joblet-mcp-server --config ~/.rnx/rnx-config.yml

   # New
   joblet-mcp-server-sdk --config ~/.rnx/rnx-config.yml
   ```

3. **Configuration remains the same**: No changes needed to `~/.rnx/rnx-config.yml`

4. **Test thoroughly**: Verify all functionality works as expected

### Configuration Migration

Both implementations use the same configuration format, so no configuration changes are needed:

```yaml
# ~/.rnx/rnx-config.yml - Same for both implementations
version: "3.0"
nodes:
  default:
    address: "server:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      # ... certificate content ...
      -----END CERTIFICATE-----
    # ... rest of configuration
```

## Development and Testing

### Testing Both Implementations

The E2E test suite automatically detects which implementation is available:

```bash
# Test with SDK-based server (if available)
python scripts/run-e2e-tests.py --type quick

# Force CLI-based server testing
pip uninstall joblet-sdk-python
python scripts/run-e2e-tests.py --type quick
```

### Docker Support

Both implementations can be containerized:

```dockerfile
# SDK-based server
FROM python:3.11-slim
RUN pip install joblet-mcp-server[sdk]
CMD ["joblet-mcp-server-sdk"]

# CLI-based server
FROM python:3.11-slim
RUN pip install joblet-mcp-server
# Install rnx binary
COPY rnx /usr/local/bin/rnx
CMD ["joblet-mcp-server"]
```

## Recommendation

**Use the SDK-based server (`joblet-mcp-server-sdk`) for all new deployments.** It provides better performance, error handling, and development experience while using the same configuration format.

The CLI-based server remains available for compatibility and specific use cases where the SDK cannot be installed.