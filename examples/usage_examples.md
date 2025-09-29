# Joblet MCP Server Usage Examples

This document provides examples of how to use the Joblet MCP Server tools through an MCP client.

## Configuration

Before using the MCP server, ensure your rnx configuration is properly set up with embedded TLS certificates.

### Example Configuration (`~/.rnx/rnx-config.yml`)

```yaml
version: "3.0"

nodes:
  default:
    address: "192.168.1.161:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      MIIEUTCCAjkCFEhzcjY/SBRHyd3wCq4PYjNiNfYAMA0GCSqGSIb3DQEBCwUAMGIx
      # ... your complete client certificate content ...
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCty2xspct1gYk9
      # ... your complete private key content ...
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      MIIFpTCCA42gAwIBAgIUI2WnxZcIMNk7eBxeBmOU5dXgk50wDQYJKoZIhvcNAQEL
      # ... your complete CA certificate content ...
      -----END CERTIFICATE-----

  viewer:
    address: "192.168.1.161:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      # ... viewer client certificate content ...
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      # ... viewer private key content ...
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      # ... CA certificate content (same as above) ...
      -----END CERTIFICATE-----
```

**Important Notes:**
- TLS certificates are embedded as string content using YAML's multiline string syntax (`|`)
- This is the same format used by joblet-sdk-python
- Certificates are not referenced as file paths but included directly in the configuration
- The `address` field includes both hostname/IP and port

## Job Management

### Running a Simple Job

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "echo",
    "args": ["Hello, World!"],
    "name": "hello-world-job",
    "max_cpu": 25,
    "max_memory": 512
  }
}
```

### Running a Python Script with GPU

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": ["train_model.py", "--epochs", "100"],
    "name": "ml-training",
    "max_cpu": 80,
    "max_memory": 8192,
    "gpu_count": 1,
    "gpu_memory_mb": 4096,
    "runtime": "python-3.11-ml",
    "environment": {
      "CUDA_VISIBLE_DEVICES": "0",
      "PYTHONPATH": "/workspace"
    }
  }
}
```

### Scheduling a Job for Later

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "backup.sh",
    "schedule": "2024-01-01T02:00:00Z",
    "name": "nightly-backup",
    "max_cpu": 50,
    "max_memory": 2048
  }
}
```

### Listing All Jobs

```json
{
  "tool": "joblet_list_jobs",
  "arguments": {}
}
```

### Getting Job Status

```json
{
  "tool": "joblet_get_job_status",
  "arguments": {
    "job_uuid": "abc12345-6789-def0-1234-567890abcdef"
  }
}
```

Note: You can use short UUIDs (first 8 characters) if they're unique:

```json
{
  "tool": "joblet_get_job_status",
  "arguments": {
    "job_uuid": "abc12345"
  }
}
```

### Streaming Job Logs

```json
{
  "tool": "joblet_get_job_logs",
  "arguments": {
    "job_uuid": "abc12345",
    "lines": 100
  }
}
```

### Stopping a Running Job

```json
{
  "tool": "joblet_stop_job",
  "arguments": {
    "job_uuid": "abc12345"
  }
}
```

### Canceling a Scheduled Job

```json
{
  "tool": "joblet_cancel_job",
  "arguments": {
    "job_uuid": "abc12345"
  }
}
```

### Deleting a Job

```json
{
  "tool": "joblet_delete_job",
  "arguments": {
    "job_uuid": "abc12345"
  }
}
```

### Bulk Delete All Non-Running Jobs

```json
{
  "tool": "joblet_delete_all_jobs",
  "arguments": {}
}
```

## Workflow Management

### Running a Workflow

```json
{
  "tool": "joblet_run_workflow",
  "arguments": {
    "workflow_file": "/path/to/workflow.yaml"
  }
}
```

### Listing Workflows

```json
{
  "tool": "joblet_list_workflows",
  "arguments": {
    "include_completed": true
  }
}
```

### Getting Workflow Status

```json
{
  "tool": "joblet_get_workflow_status",
  "arguments": {
    "workflow_uuid": "workflow-123"
  }
}
```

## Resource Management

### Creating a Volume

```json
{
  "tool": "joblet_create_volume",
  "arguments": {
    "name": "data-volume",
    "size": "10GB",
    "type": "filesystem"
  }
}
```

### Listing Volumes

```json
{
  "tool": "joblet_list_volumes",
  "arguments": {}
}
```

### Removing a Volume

```json
{
  "tool": "joblet_remove_volume",
  "arguments": {
    "name": "data-volume"
  }
}
```

### Creating a Network

```json
{
  "tool": "joblet_create_network",
  "arguments": {
    "name": "ml-network",
    "cidr": "10.0.1.0/24"
  }
}
```

### Listing Networks

```json
{
  "tool": "joblet_list_networks",
  "arguments": {}
}
```

### Removing a Network

```json
{
  "tool": "joblet_remove_network",
  "arguments": {
    "name": "ml-network"
  }
}
```

## System Monitoring

### Getting System Status

```json
{
  "tool": "joblet_get_system_status",
  "arguments": {}
}
```

### Getting Real-time System Metrics

```json
{
  "tool": "joblet_get_system_metrics",
  "arguments": {
    "interval": 5
  }
}
```

### Monitoring GPU Status

```json
{
  "tool": "joblet_get_gpu_status",
  "arguments": {}
}
```

### Listing Available Nodes

```json
{
  "tool": "joblet_list_nodes",
  "arguments": {}
}
```

## Runtime Management

### Listing Available Runtimes

```json
{
  "tool": "joblet_list_runtimes",
  "arguments": {}
}
```

### Installing a Runtime

```json
{
  "tool": "joblet_install_runtime",
  "arguments": {
    "runtime_spec": "python:3.11-cuda",
    "repository": "https://github.com/example/runtime-repo",
    "branch": "main",
    "force_reinstall": false
  }
}
```

### Removing a Runtime

```json
{
  "tool": "joblet_remove_runtime",
  "arguments": {
    "runtime": "python:3.11-cuda"
  }
}
```

## Runtime-Specific Examples

### Python 3.11 Basic Runtime

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": ["-c", "import requests; print(f'Requests version: {requests.__version__}')"],
    "name": "python-basic-test",
    "runtime": "python-3.11",
    "max_cpu": 25,
    "max_memory": 512
  }
}
```

### Python 3.11 ML Runtime with Data Science

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": ["-c", "import numpy as np; import pandas as pd; print(f'NumPy: {np.__version__}, Pandas: {pd.__version__}')"],
    "name": "data-science-test",
    "runtime": "python-3.11-ml",
    "max_cpu": 50,
    "max_memory": 2048
  }
}
```

### Java OpenJDK 21 Runtime

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "java",
    "args": ["-version"],
    "name": "java-version-check",
    "runtime": "openjdk-21",
    "max_cpu": 30,
    "max_memory": 1024
  }
}
```

### GraalVM Native Image Compilation

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "native-image",
    "args": ["--version"],
    "name": "graalvm-native-test",
    "runtime": "graalvmjdk-21",
    "max_cpu": 40,
    "max_memory": 2048
  }
}
```

### Machine Learning Training Pipeline

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": ["train_model.py", "--data-path", "/data", "--model-type", "sklearn"],
    "name": "ml-training-pipeline",
    "runtime": "python-3.11-ml",
    "max_cpu": 80,
    "max_memory": 4096,
    "gpu_count": 1,
    "volumes": ["ml-data:/data", "ml-models:/models"],
    "environment": {
      "MODEL_OUTPUT_PATH": "/models",
      "TRAINING_EPOCHS": "100",
      "BATCH_SIZE": "32"
    }
  }
}
```

## Advanced Examples

### Running a Job with Custom Network and Volume

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": ["distributed_training.py"],
    "name": "distributed-ml",
    "max_cpu": 90,
    "max_memory": 16384,
    "gpu_count": 2,
    "gpu_memory_mb": 8192,
    "runtime": "python-3.11-ml",
    "network": "ml-network",
    "volumes": ["data-volume:/data", "models-volume:/models"],
    "work_dir": "/workspace",
    "environment": {
      "MASTER_ADDR": "localhost",
      "MASTER_PORT": "12355",
      "WORLD_SIZE": "2",
      "RANK": "0"
    },
    "secret_environment": {
      "WANDB_API_KEY": "your-secret-key"
    }
  }
}
```

### Complete ML Pipeline Workflow

First, create the necessary resources:

```json
{
  "tool": "joblet_create_volume",
  "arguments": {
    "name": "ml-data",
    "size": "50GB"
  }
}
```

```json
{
  "tool": "joblet_create_network",
  "arguments": {
    "name": "ml-pipeline",
    "cidr": "10.1.0.0/24"
  }
}
```

Then run the workflow:

```json
{
  "tool": "joblet_run_workflow",
  "arguments": {
    "workflow_file": "/path/to/ml_pipeline.yaml"
  }
}
```

Monitor the progress:

```json
{
  "tool": "joblet_list_workflows",
  "arguments": {}
}
```

## Error Handling

The MCP server will return appropriate error messages for various scenarios:

- **Invalid job UUID**: "Job not found"
- **Missing binary**: "rnx binary not found at: /path/to/rnx"
- **Network issues**: "Failed to connect to Joblet server"
- **Resource conflicts**: "Volume already exists"
- **Insufficient resources**: "Not enough GPU memory available"

Always check the response for error messages and handle them appropriately in your application.