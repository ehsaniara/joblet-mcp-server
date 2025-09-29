# Joblet Runtime Examples for MCP Server

This document provides specific examples using the actual Joblet runtime environments available in the core project.

## Configuration Setup

Before running these examples, ensure your rnx configuration is properly set up:

**Example `~/.rnx/rnx-config.yml`:**

```yaml
version: "3.0"

nodes:
  default:
    address: "your-joblet-server:50051"
    cert: |
      -----BEGIN CERTIFICATE-----
      # ... your client certificate content ...
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      # ... your private key content ...
      -----END PRIVATE KEY-----
    ca: |
      -----BEGIN CERTIFICATE-----
      # ... your CA certificate content ...
      -----END CERTIFICATE-----
```

**Note:** TLS certificates are embedded as string content, not file paths. This is consistent with joblet-sdk-python
configuration format.

## Available Joblet Runtimes

Based on the Joblet runtime manifest, the following pre-built runtimes are available:

| Runtime          | Version | Description                          | Min RAM | Languages/Libraries                            |
|------------------|---------|--------------------------------------|---------|------------------------------------------------|
| `python-3.11`    | 3.11.9  | Basic Python with essential packages | 512MB   | Python, pip, requests                          |
| `python-3.11-ml` | 3.11.7  | Python with ML libraries             | 2GB     | NumPy, Pandas, SciPy, Scikit-learn, Matplotlib |
| `openjdk-21`     | 21.0.1  | OpenJDK with development tools       | 512MB   | Java, javac, jar                               |
| `graalvmjdk-21`  | 21.0.1  | GraalVM with native-image support    | 1GB     | Java, native-image, GraalVM tools              |

## Python Runtime Examples

### Basic Python Runtime (`python-3.11`)

Perfect for lightweight scripts, AI agents, and general automation:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "--version"
    ],
    "name": "python-version-check",
    "runtime": "python-3.11",
    "max_cpu": 25,
    "max_memory": 512
  }
}
```

### HTTP Request with Python Basic Runtime

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "-c",
      "import requests; response = requests.get('https://httpbin.org/json'); print(f'Status: {response.status_code}, Data: {response.json()}')"
    ],
    "name": "http-request-test",
    "runtime": "python-3.11",
    "max_cpu": 30,
    "max_memory": 512,
    "environment": {
      "PYTHONUNBUFFERED": "1"
    }
  }
}
```

### Machine Learning Runtime (`python-3.11-ml`)

For data science, machine learning, and scientific computing:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "-c",
      "import numpy as np; import pandas as pd; import sklearn; print(f'NumPy: {np.__version__}, Pandas: {pd.__version__}, Scikit-learn: {sklearn.__version__}')"
    ],
    "name": "ml-libraries-check",
    "runtime": "python-3.11-ml",
    "max_cpu": 50,
    "max_memory": 2048
  }
}
```

### Data Processing with Pandas

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "-c",
      "import pandas as pd; import numpy as np; df = pd.DataFrame({'A': np.random.randn(100), 'B': np.random.randn(100)}); print(f'Created DataFrame with shape: {df.shape}'); print(df.describe())"
    ],
    "name": "data-processing-demo",
    "runtime": "python-3.11-ml",
    "max_cpu": 60,
    "max_memory": 2048
  }
}
```

### Machine Learning Training Simulation

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "-c",
      "from sklearn.datasets import make_classification; from sklearn.ensemble import RandomForestClassifier; from sklearn.model_selection import train_test_split; from sklearn.metrics import accuracy_score; import numpy as np; X, y = make_classification(n_samples=1000, n_features=20, n_informative=10, n_redundant=10, random_state=42); X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42); clf = RandomForestClassifier(n_estimators=100, random_state=42); clf.fit(X_train, y_train); y_pred = clf.predict(X_test); print(f'Model trained! Accuracy: {accuracy_score(y_test, y_pred):.4f}')"
    ],
    "name": "ml-training-simulation",
    "runtime": "python-3.11-ml",
    "max_cpu": 80,
    "max_memory": 4096,
    "gpu_count": 1,
    "environment": {
      "MODEL_TYPE": "RandomForest",
      "N_ESTIMATORS": "100"
    }
  }
}
```

## Java Runtime Examples

### OpenJDK 21 Runtime (`openjdk-21`)

Standard Java development and runtime environment:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "java",
    "args": [
      "-version"
    ],
    "name": "java-version-check",
    "runtime": "openjdk-21",
    "max_cpu": 30,
    "max_memory": 1024
  }
}
```

### Java Hello World Compilation and Execution

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "bash",
    "args": [
      "-c",
      "echo 'public class HelloWorld { public static void main(String[] args) { System.out.println(\"Hello from Java 21!\"); } }' > HelloWorld.java && javac HelloWorld.java && java HelloWorld"
    ],
    "name": "java-hello-world",
    "runtime": "openjdk-21",
    "max_cpu": 40,
    "max_memory": 1024,
    "work_dir": "/tmp"
  }
}
```

### GraalVM Runtime (`graalvmjdk-21`)

High-performance Java with native compilation:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "native-image",
    "args": [
      "--version"
    ],
    "name": "graalvm-native-version",
    "runtime": "graalvmjdk-21",
    "max_cpu": 40,
    "max_memory": 2048
  }
}
```

### GraalVM Native Image Demo

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "bash",
    "args": [
      "-c",
      "echo 'public class FastApp { public static void main(String[] args) { System.out.println(\"Fast startup with GraalVM!\"); } }' > FastApp.java && javac FastApp.java && native-image FastApp && ./fastapp"
    ],
    "name": "graalvm-native-demo",
    "runtime": "graalvmjdk-21",
    "max_cpu": 80,
    "max_memory": 4096,
    "work_dir": "/tmp"
  }
}
```

## Runtime Management Examples

### List Available Runtimes

```json
{
  "tool": "joblet_list_runtimes",
  "arguments": {}
}
```

### Install a Runtime (if not already available)

```json
{
  "tool": "joblet_install_runtime",
  "arguments": {
    "runtime_spec": "python-3.11-ml",
    "force_reinstall": false
  }
}
```

### Remove a Runtime

```json
{
  "tool": "joblet_remove_runtime",
  "arguments": {
    "runtime": "python-3.11-ml"
  }
}
```

## Complex Workflow Examples

### Multi-Runtime Data Pipeline

First, create the necessary volumes:

```json
{
  "tool": "joblet_create_volume",
  "arguments": {
    "name": "pipeline-data",
    "size": "10GB"
  }
}
```

Then run the data preparation in Python:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "-c",
      "import pandas as pd; import numpy as np; np.random.seed(42); data = pd.DataFrame({'feature1': np.random.randn(1000), 'feature2': np.random.randn(1000), 'target': np.random.randint(0, 2, 1000)}); data.to_csv('/data/training_data.csv', index=False); print(f'Generated training data: {data.shape}')"
    ],
    "name": "data-preparation",
    "runtime": "python-3.11-ml",
    "volumes": [
      "pipeline-data:/data"
    ],
    "max_cpu": 50,
    "max_memory": 2048
  }
}
```

Finally, train a model:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "-c",
      "import pandas as pd; from sklearn.ensemble import RandomForestClassifier; from sklearn.model_selection import train_test_split; from sklearn.metrics import accuracy_score; import joblib; data = pd.read_csv('/data/training_data.csv'); X = data[['feature1', 'feature2']]; y = data['target']; X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42); model = RandomForestClassifier(random_state=42); model.fit(X_train, y_train); accuracy = accuracy_score(y_test, model.predict(X_test)); joblib.dump(model, '/data/model.pkl'); print(f'Model trained with accuracy: {accuracy:.4f}, saved to /data/model.pkl')"
    ],
    "name": "model-training",
    "runtime": "python-3.11-ml",
    "volumes": [
      "pipeline-data:/data"
    ],
    "max_cpu": 80,
    "max_memory": 4096,
    "gpu_count": 1
  }
}
```

### Cross-Language Workflow

Process data with Python, then analyze with Java:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "python",
    "args": [
      "-c",
      "import json; data = {'results': [1, 2, 3, 4, 5], 'status': 'completed', 'processing_time': 1.23}; with open('/data/results.json', 'w') as f: json.dump(data, f); print('Data processed and saved')"
    ],
    "name": "python-data-processing",
    "runtime": "python-3.11",
    "volumes": [
      "pipeline-data:/data"
    ],
    "max_cpu": 30,
    "max_memory": 512
  }
}
```

Then process with Java:

```json
{
  "tool": "joblet_run_job",
  "arguments": {
    "command": "bash",
    "args": [
      "-c",
      "echo 'import java.nio.file.*; import java.util.*; public class DataProcessor { public static void main(String[] args) throws Exception { String content = Files.readString(Paths.get(\"/data/results.json\")); System.out.println(\"Java processed: \" + content); } }' > DataProcessor.java && javac DataProcessor.java && java DataProcessor"
    ],
    "name": "java-data-analysis",
    "runtime": "openjdk-21",
    "volumes": [
      "pipeline-data:/data"
    ],
    "max_cpu": 40,
    "max_memory": 1024,
    "work_dir": "/tmp"
  }
}
```

## Performance Considerations

### Resource Requirements by Runtime

- **python-3.11**: Lightweight, 512MB RAM minimum, fast startup
- **python-3.11-ml**: ML-optimized, 2GB RAM minimum, includes NumPy/Pandas
- **openjdk-21**: Standard Java, 512MB RAM minimum, JVM startup overhead
- **graalvmjdk-21**: High-performance, 1GB RAM minimum, native compilation capabilities

### Best Practices

1. **Choose the Right Runtime**: Use `python-3.11` for simple scripts, `python-3.11-ml` for data science
2. **Resource Allocation**: Allocate sufficient memory based on runtime requirements
3. **GPU Usage**: Only request GPUs for workloads that can utilize them (ML training, etc.)
4. **Volume Management**: Use persistent volumes for data that needs to persist across jobs
5. **Environment Variables**: Set appropriate environment variables for reproducible execution

## Troubleshooting

### Common Issues

**Runtime not available:**

```json
{
  "tool": "joblet_list_runtimes",
  "arguments": {}
}
```

**Check runtime requirements:**

```json
{
  "tool": "joblet_get_system_status",
  "arguments": {}
}
```

**Install missing runtime:**

```json
{
  "tool": "joblet_install_runtime",
  "arguments": {
    "runtime_spec": "python-3.11-ml"
  }
}
```