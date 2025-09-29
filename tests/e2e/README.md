# End-to-End Tests for Joblet MCP Server

This directory contains comprehensive end-to-end tests that validate the complete functionality of the Joblet MCP Server with real Joblet runtime environments.

## Overview

The E2E tests are designed to:

- **Validate real-world usage**: Test actual job execution with real runtime environments
- **Test complete workflows**: From job submission to completion and cleanup
- **Verify resource management**: Test volumes, networks, and system monitoring
- **Ensure runtime compatibility**: Test all available runtime environments
- **Test cross-language workflows**: Validate multi-runtime data pipelines

## Prerequisites

Before running E2E tests, ensure you have:

### Required
- **rnx binary**: The Joblet CLI tool must be installed and in your PATH
- **Joblet server**: A running Joblet server with proper configuration
- **Python dependencies**: Install test dependencies with `pip install -e ".[dev]"`

### Optional
- **Runtime environments**: The following runtimes should be available for full test coverage:
  - `python-3.11`: Basic Python with essential packages
  - `python-3.11-ml`: Python with ML libraries (NumPy, Pandas, Scikit-learn)
  - `openjdk-21`: OpenJDK with development tools
  - `graalvmjdk-21`: GraalVM with native-image support

### Configuration
- **Config file**: Create `~/.rnx/rnx-config.yml` with embedded TLS certificates (string format)
- **Node access**: Ensure your configuration points to an accessible Joblet node
- **Certificate format**: TLS certificates should be embedded as strings using YAML's `|` syntax, not file paths

## Test Structure

### Core Test Files

#### `test_job_management.py`
Tests basic job lifecycle operations:
- **Simple job execution**: Echo, bash commands
- **Resource limits**: CPU, memory, I/O constraints
- **Environment variables**: Custom job environments
- **Job control**: Status checking, cancellation, deletion
- **Logging**: Job log retrieval and streaming
- **UUID handling**: Short UUID functionality

```bash
# Run job management tests only
python scripts/run-e2e-tests.py --type job
```

#### `test_resource_management.py`
Tests resource management and system monitoring:
- **Volume management**: Create, use, remove persistent volumes
- **Data persistence**: Multi-job data sharing
- **Network management**: Create, use, remove networks
- **Network isolation**: Test job network separation
- **System monitoring**: Status, metrics, GPU monitoring
- **Node management**: List and monitor nodes

```bash
# Run resource management tests only
python scripts/run-e2e-tests.py --type resource
```

#### `test_runtimes.py`
Tests runtime-specific functionality:
- **Python runtimes**: Basic Python and ML environments
- **Java runtimes**: OpenJDK and GraalVM environments
- **Cross-language workflows**: Multi-runtime data pipelines
- **Runtime management**: Installation and removal
- **Performance validation**: Runtime-specific optimizations

```bash
# Run runtime tests only
python scripts/run-e2e-tests.py --type runtime
```

### Test Categories

#### Quick Tests (Non-slow)
Fast-running tests suitable for CI/CD:
```bash
python scripts/run-e2e-tests.py --type quick
```

#### Full Test Suite
Complete test coverage including slow tests:
```bash
python scripts/run-e2e-tests.py --type all
```

## Running Tests

### Using the Test Runner

The recommended way to run E2E tests is using the provided test runner:

```bash
# Check prerequisites
python scripts/run-e2e-tests.py --check

# List available tests
python scripts/run-e2e-tests.py --list

# Run quick tests (non-slow)
python scripts/run-e2e-tests.py --type quick

# Run all tests with verbose output
python scripts/run-e2e-tests.py --type all --verbose

# Run tests with specific markers
python scripts/run-e2e-tests.py --markers "not slow"

# Run tests in parallel (if pytest-xdist is installed)
python scripts/run-e2e-tests.py --parallel
```

### Using Pytest Directly

You can also run tests directly with pytest:

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test file
pytest tests/e2e/test_job_management.py -v

# Run tests with markers
pytest tests/e2e/ -m "e2e and not slow" -v

# Run specific test class
pytest tests/e2e/test_runtimes.py::TestPythonRuntimes -v

# Run specific test method
pytest tests/e2e/test_job_management.py::TestBasicJobManagement::test_simple_echo_job -v
```

## Test Fixtures and Configuration

### Key Fixtures

- **`e2e_server`**: Configured MCP server instance
- **`server_status`**: Validates server connectivity
- **`available_runtimes`**: Lists available runtime environments
- **`cleanup_jobs`**: Automatically cleans up created jobs
- **`cleanup_volumes`**: Automatically cleans up created volumes
- **`cleanup_networks`**: Automatically cleans up created networks
- **`temp_*_name`**: Generates unique temporary resource names

### Configuration Options

E2E tests use the following configuration precedence:

1. **Command line arguments** (via test runner)
2. **Environment variables**:
   - `RNX_BINARY_PATH`: Path to rnx binary
   - `RNX_CONFIG_FILE`: Path to configuration file
   - `RNX_NODE_NAME`: Node name to use
3. **Default configuration discovery** (standard rnx behavior)

## Example Test Scenarios

### Basic Job Execution
```python
async def test_simple_echo_job(self, e2e_server, cleanup_jobs):
    result = await e2e_server._execute_tool("joblet_run_job", {
        "command": "echo",
        "args": ["Hello, E2E!"],
        "max_cpu": 25,
        "max_memory": 512
    })
    # Test continues with status checking and log verification...
```

### Volume-based Data Pipeline
```python
async def test_data_persistence(self, e2e_server, cleanup_volumes):
    # Create volume
    await e2e_server._execute_tool("joblet_create_volume", {
        "name": "data-vol",
        "size": "1GB"
    })

    # Job 1: Write data
    await e2e_server._execute_tool("joblet_run_job", {
        "command": "bash",
        "args": ["-c", "echo 'persistent data' > /data/file.txt"],
        "volumes": ["data-vol:/data"]
    })

    # Job 2: Read data
    await e2e_server._execute_tool("joblet_run_job", {
        "command": "cat",
        "args": ["/data/file.txt"],
        "volumes": ["data-vol:/data"]
    })
```

### Cross-Runtime Workflow
```python
async def test_python_to_java_pipeline(self, e2e_server, cleanup_volumes):
    # Python job generates data
    await e2e_server._execute_tool("joblet_run_job", {
        "command": "python",
        "args": ["-c", "import json; json.dump({'data': 'from_python'}, open('/shared/data.json', 'w'))"],
        "runtime": "python-3.11",
        "volumes": ["shared-vol:/shared"]
    })

    # Java job processes data
    await e2e_server._execute_tool("joblet_run_job", {
        "command": "java",
        "args": ["DataProcessor"],  # Assumes compiled Java class
        "runtime": "openjdk-21",
        "volumes": ["shared-vol:/shared"]
    })
```

## Test Markers

E2E tests use pytest markers for categorization:

- **`@pytest.mark.e2e`**: All E2E tests (auto-applied)
- **`@pytest.mark.slow`**: Tests that take significant time (>30 seconds)
- **`@pytest.mark.asyncio`**: Async test functions

## Troubleshooting

### Common Issues

#### "rnx binary not found"
```bash
# Install rnx or add to PATH
export PATH=$PATH:/path/to/rnx/bin

# Or specify directly in test runner
python scripts/run-e2e-tests.py --rnx-path /path/to/rnx
```

#### "Joblet server not available"
```bash
# Check server connection
rnx node list

# Verify configuration
cat ~/.rnx/config.yaml

# Check if server is running
rnx system status
```

#### "Runtime not available"
```bash
# List available runtimes
rnx runtime list

# Install missing runtime
rnx runtime install python-3.11-ml
```

#### "Test timeouts"
- Increase timeout values in test configuration
- Check system resources (CPU, memory)
- Verify network connectivity to Joblet server

### Debug Mode

For detailed debugging, run tests with maximum verbosity:

```bash
# Maximum verbosity with pytest
pytest tests/e2e/ -vvv --tb=long --capture=no

# Or with test runner
python scripts/run-e2e-tests.py --verbose --type all
```

### Selective Test Execution

Run specific test patterns:

```bash
# Tests containing "python" in the name
pytest tests/e2e/ -k "python" -v

# Tests NOT marked as slow
pytest tests/e2e/ -m "not slow" -v

# Specific runtime tests
pytest tests/e2e/test_runtimes.py::TestPythonRuntimes -v
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Install rnx
        run: |
          # Install rnx binary
          curl -L https://github.com/joblet/rnx/releases/latest/download/rnx-linux-amd64 -o rnx
          chmod +x rnx
          sudo mv rnx /usr/local/bin/

      - name: Setup Joblet config
        run: |
          mkdir -p ~/.rnx
          cat > ~/.rnx/rnx-config.yml << 'EOF'
          version: "3.0"
          nodes:
            default:
              address: "${{ secrets.JOBLET_HOST }}:50051"
              cert: |
                ${{ secrets.JOBLET_CLIENT_CERT }}
              key: |
                ${{ secrets.JOBLET_CLIENT_KEY }}
              ca: |
                ${{ secrets.JOBLET_CA_CERT }}
          EOF

      - name: Run E2E tests
        run: python scripts/run-e2e-tests.py --type quick
```

### Docker Testing

```dockerfile
FROM python:3.11-slim

# Install rnx and dependencies
RUN apt-get update && apt-get install -y curl
RUN curl -L https://github.com/joblet/rnx/releases/latest/download/rnx-linux-amd64 -o /usr/local/bin/rnx
RUN chmod +x /usr/local/bin/rnx

# Copy and install project
COPY . /app
WORKDIR /app
RUN pip install -e ".[dev]"

# Run tests
CMD ["python", "scripts/run-e2e-tests.py", "--type", "quick"]
```

## Contributing

When adding new E2E tests:

1. **Follow naming conventions**: `test_*.py` files, `Test*` classes, `test_*` methods
2. **Use appropriate markers**: `@pytest.mark.e2e`, `@pytest.mark.slow` if needed
3. **Include cleanup**: Use cleanup fixtures to avoid resource leaks
4. **Test real scenarios**: Focus on realistic usage patterns
5. **Document test purpose**: Include docstrings explaining what is being tested
6. **Handle failures gracefully**: Tests should be robust against transient failures

### Test Template

```python
@pytest.mark.e2e
@pytest.mark.asyncio
class TestNewFeature:
    """Test description"""

    async def test_feature_functionality(self, e2e_server, cleanup_jobs, server_status):
        """Test specific aspect of the feature"""
        # Test implementation
        result = await e2e_server._execute_tool("tool_name", {
            "param": "value"
        })

        # Verify result
        assert "expected" in result
```

## Performance Benchmarks

E2E tests also serve as performance benchmarks:

- **Job startup time**: Measure time from submission to execution
- **Runtime efficiency**: Compare resource usage across runtimes
- **Volume I/O**: Test data transfer speeds
- **Network latency**: Measure inter-job communication delays

Results can be collected and analyzed for performance regression testing.