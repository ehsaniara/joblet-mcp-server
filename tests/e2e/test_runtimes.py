"""
End-to-end tests for runtime-specific functionality

Tests the actual runtime environments available in Joblet:
- python-3.11: Basic Python with essential packages
- python-3.11-ml: Python with ML libraries (NumPy, Pandas, Scikit-learn)
- openjdk-21: OpenJDK with development tools
- graalvmjdk-21: GraalVM with native-image support
"""

import asyncio
import json
from typing import Any, Dict

import pytest


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestPythonRuntimes:
    """Test Python runtime environments"""

    async def test_python_basic_runtime(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test python-3.11 basic runtime"""
        # Check if runtime is available
        if "python-3.11" not in available_runtimes:
            pytest.skip("python-3.11 runtime not available")

        # Test basic Python functionality
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",
                "args": [
                    "-c",
                    "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}'); import requests; print(f'Requests: {requests.__version__}')",
                ],
                "name": "python-basic-test",
                "runtime": "python-3.11",
                "max_cpu": 25,
                "max_memory": 512,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        # Check logs for expected output
        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Python 3.11" in logs_result
        assert "Requests:" in logs_result

    async def test_python_basic_http_request(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test HTTP request with python-3.11"""
        if "python-3.11" not in available_runtimes:
            pytest.skip("python-3.11 runtime not available")

        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",
                "args": [
                    "-c",
                    "import requests; response = requests.get('https://httpbin.org/json'); print(f'Status: {response.status_code}'); data = response.json(); print(f'Data keys: {list(data.keys())}')",
                ],
                "name": "python-http-test",
                "runtime": "python-3.11",
                "max_cpu": 30,
                "max_memory": 512,
                "environment": {"PYTHONUNBUFFERED": "1"},
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Status: 200" in logs_result
        assert "Data keys:" in logs_result

    async def test_python_ml_runtime(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test python-3.11-ml machine learning runtime"""
        if "python-3.11-ml" not in available_runtimes:
            pytest.skip("python-3.11-ml runtime not available")

        # Test ML libraries availability
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",
                "args": [
                    "-c",
                    "import numpy as np; import pandas as pd; import sklearn; print(f'NumPy: {np.__version__}'); print(f'Pandas: {pd.__version__}'); print(f'Scikit-learn: {sklearn.__version__}')",
                ],
                "name": "python-ml-libraries-test",
                "runtime": "python-3.11-ml",
                "max_cpu": 50,
                "max_memory": 2048,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "NumPy:" in logs_result
        assert "Pandas:" in logs_result
        assert "Scikit-learn:" in logs_result

    async def test_python_ml_data_processing(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test data processing with pandas in ML runtime"""
        if "python-3.11-ml" not in available_runtimes:
            pytest.skip("python-3.11-ml runtime not available")

        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",
                "args": [
                    "-c",
                    "import pandas as pd; import numpy as np; df = pd.DataFrame({'A': np.random.randn(100), 'B': np.random.randn(100)}); print(f'DataFrame shape: {df.shape}'); print(f'Mean A: {df.A.mean():.2f}'); print('Data processing completed')",
                ],
                "name": "python-ml-data-test",
                "runtime": "python-3.11-ml",
                "max_cpu": 60,
                "max_memory": 2048,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "DataFrame shape: (100, 2)" in logs_result
        assert "Mean A:" in logs_result
        assert "Data processing completed" in logs_result

    async def test_python_ml_model_training(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test ML model training simulation"""
        if "python-3.11-ml" not in available_runtimes:
            pytest.skip("python-3.11-ml runtime not available")

        training_script = """
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np

# Generate sample data
X, y = make_classification(n_samples=1000, n_features=20, n_informative=10, n_redundant=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = RandomForestClassifier(n_estimators=50, random_state=42)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f'Model trained successfully!')
print(f'Training samples: {len(X_train)}')
print(f'Test samples: {len(X_test)}')
print(f'Accuracy: {accuracy:.4f}')
print('ML training completed')
        """

        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",
                "args": ["-c", training_script],
                "name": "python-ml-training-test",
                "runtime": "python-3.11-ml",
                "max_cpu": 80,
                "max_memory": 4096,
                "environment": {"MODEL_TYPE": "RandomForest", "N_ESTIMATORS": "50"},
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid, max_wait=60)

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Model trained successfully!" in logs_result
        assert "Training samples: 800" in logs_result
        assert "Test samples: 200" in logs_result
        assert "Accuracy:" in logs_result
        assert "ML training completed" in logs_result

    async def _wait_for_job_completion(self, server, job_uuid, max_wait=30):
        """Helper method to wait for job completion"""
        wait_time = 0

        while wait_time < max_wait:
            status_result = await server._execute_tool(
                "joblet_get_job_status", {"job_uuid": job_uuid}
            )
            status_data = json.loads(status_result)
            final_status = status_data.get("status")

            if final_status in ["completed", "failed", "stopped"]:
                return final_status

            await asyncio.sleep(1)
            wait_time += 1

        raise TimeoutError(f"Job {job_uuid} did not complete within {max_wait} seconds")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestJavaRuntimes:
    """Test Java runtime environments"""

    async def test_openjdk_runtime(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test openjdk-21 runtime"""
        if "openjdk-21" not in available_runtimes:
            pytest.skip("openjdk-21 runtime not available")

        # Test Java version
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "java",
                "args": ["-version"],
                "name": "java-version-test",
                "runtime": "openjdk-21",
                "max_cpu": 30,
                "max_memory": 1024,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "openjdk" in logs_result.lower() or "java" in logs_result.lower()
        assert "21" in logs_result

    async def test_java_hello_world_compilation(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test Java compilation and execution"""
        if "openjdk-21" not in available_runtimes:
            pytest.skip("openjdk-21 runtime not available")

        compile_and_run = """
echo 'public class HelloJoblet {
    public static void main(String[] args) {
        System.out.println("Hello from Java 21 in Joblet!");
        System.out.println("Args: " + java.util.Arrays.toString(args));
        System.out.println("Java version: " + System.getProperty("java.version"));
    }
}' > HelloJoblet.java &&
javac HelloJoblet.java &&
java HelloJoblet "test" "arguments"
        """

        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": ["-c", compile_and_run],
                "name": "java-hello-world-test",
                "runtime": "openjdk-21",
                "max_cpu": 40,
                "max_memory": 1024,
                "work_dir": "/tmp",
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Hello from Java 21 in Joblet!" in logs_result
        assert "Args: [test, arguments]" in logs_result
        assert "Java version:" in logs_result

    async def test_graalvm_runtime(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test graalvmjdk-21 runtime"""
        if "graalvmjdk-21" not in available_runtimes:
            pytest.skip("graalvmjdk-21 runtime not available")

        # Test GraalVM native-image tool
        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "native-image",
                "args": ["--version"],
                "name": "graalvm-version-test",
                "runtime": "graalvmjdk-21",
                "max_cpu": 40,
                "max_memory": 2048,
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(e2e_server, job_uuid)

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "graalvm" in logs_result.lower() or "native" in logs_result.lower()

    async def test_graalvm_native_compilation(
        self, e2e_server, cleanup_jobs, available_runtimes, server_status
    ):
        """Test GraalVM native image compilation"""
        if "graalvmjdk-21" not in available_runtimes:
            pytest.skip("graalvmjdk-21 runtime not available")

        native_compilation = """
echo 'public class FastApp {
    public static void main(String[] args) {
        System.out.println("Fast startup with GraalVM!");
        System.out.println("Compilation successful");
    }
}' > FastApp.java &&
javac FastApp.java &&
native-image FastApp &&
./fastapp
        """

        result = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": ["-c", native_compilation],
                "name": "graalvm-native-test",
                "runtime": "graalvmjdk-21",
                "max_cpu": 80,
                "max_memory": 4096,
                "work_dir": "/tmp",
            },
        )

        job_data = json.loads(result)
        job_uuid = job_data.get("job_uuid") or job_data.get("uuid")
        cleanup_jobs(job_uuid)

        await self._wait_for_job_completion(
            e2e_server, job_uuid, max_wait=120
        )  # Native compilation can be slow

        logs_result = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": job_uuid}
        )

        assert "Fast startup with GraalVM!" in logs_result
        assert "Compilation successful" in logs_result

    async def _wait_for_job_completion(self, server, job_uuid, max_wait=30):
        """Helper method to wait for job completion"""
        wait_time = 0

        while wait_time < max_wait:
            status_result = await server._execute_tool(
                "joblet_get_job_status", {"job_uuid": job_uuid}
            )
            status_data = json.loads(status_result)
            final_status = status_data.get("status")

            if final_status in ["completed", "failed", "stopped"]:
                return final_status

            await asyncio.sleep(1)
            wait_time += 1

        raise TimeoutError(f"Job {job_uuid} did not complete within {max_wait} seconds")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestCrossLanguageWorkflows:
    """Test workflows that use multiple runtime environments"""

    async def test_python_to_java_data_pipeline(
        self,
        e2e_server,
        cleanup_jobs,
        cleanup_volumes,
        available_runtimes,
        server_status,
    ):
        """Test data processing pipeline: Python -> Java"""
        if (
            "python-3.11" not in available_runtimes
            or "openjdk-21" not in available_runtimes
        ):
            pytest.skip("Required runtimes not available")

        # Create shared volume
        volume_name = f"pipeline-vol-{id(self)}"
        await e2e_server._execute_tool(
            "joblet_create_volume", {"name": volume_name, "size": "1GB"}
        )
        cleanup_volumes(volume_name)

        # Step 1: Python job to generate data
        python_job = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",
                "args": [
                    "-c",
                    "import json; data = {'results': [1, 2, 3, 4, 5], 'status': 'completed', 'processing_time': 1.23, 'language': 'python'}; json.dump(data, open('/data/results.json', 'w')); print('Python data processing completed')",
                ],
                "name": "python-data-processor",
                "runtime": "python-3.11",
                "volumes": [f"{volume_name}:/data"],
                "max_cpu": 30,
                "max_memory": 512,
            },
        )

        python_job_data = json.loads(python_job)
        python_uuid = python_job_data.get("job_uuid") or python_job_data.get("uuid")
        cleanup_jobs(python_uuid)

        await self._wait_for_job_completion(e2e_server, python_uuid)

        # Step 2: Java job to process the data
        java_processing = """
import java.nio.file.*;
import java.util.*;

public class DataProcessor {
    public static void main(String[] args) throws Exception {
        String content = Files.readString(Paths.get("/data/results.json"));
        System.out.println("Java received data: " + content);

        // Simple processing simulation
        String processed = content.replace("python", "java-processed");
        Files.writeString(Paths.get("/data/processed.json"), processed);

        System.out.println("Java processing completed");
    }
}
        """

        java_job = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    f"cat > DataProcessor.java << 'EOF'\n{java_processing}\nEOF\njavac DataProcessor.java && java DataProcessor",
                ],
                "name": "java-data-processor",
                "runtime": "openjdk-21",
                "volumes": [f"{volume_name}:/data"],
                "max_cpu": 40,
                "max_memory": 1024,
                "work_dir": "/tmp",
            },
        )

        java_job_data = json.loads(java_job)
        java_uuid = java_job_data.get("job_uuid") or java_job_data.get("uuid")
        cleanup_jobs(java_uuid)

        await self._wait_for_job_completion(e2e_server, java_uuid)

        # Verify both jobs completed successfully
        python_logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": python_uuid}
        )

        java_logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": java_uuid}
        )

        assert "Python data processing completed" in python_logs
        assert "Java processing completed" in java_logs
        assert "Java received data:" in java_logs

    async def test_ml_training_and_java_deployment(
        self,
        e2e_server,
        cleanup_jobs,
        cleanup_volumes,
        available_runtimes,
        server_status,
    ):
        """Test ML training in Python and model deployment simulation in Java"""
        if (
            "python-3.11-ml" not in available_runtimes
            or "openjdk-21" not in available_runtimes
        ):
            pytest.skip("Required runtimes not available")

        # Create shared volume
        volume_name = f"ml-pipeline-{id(self)}"
        await e2e_server._execute_tool(
            "joblet_create_volume", {"name": volume_name, "size": "2GB"}
        )
        cleanup_volumes(volume_name)

        # Step 1: Train model in Python
        training_script = """
import json
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Generate and train
X, y = make_classification(n_samples=500, n_features=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = RandomForestClassifier(n_estimators=10, random_state=42)
clf.fit(X_train, y_train)

accuracy = accuracy_score(y_test, clf.predict(X_test))

# Save model info (simplified)
model_info = {
    "model_type": "RandomForest",
    "accuracy": accuracy,
    "n_features": X.shape[1],
    "training_samples": len(X_train),
    "test_accuracy": accuracy
}

json.dump(model_info, open('/models/model_info.json', 'w'))
print(f'Model trained with accuracy: {accuracy:.4f}')
print('Model info saved for Java deployment')
        """

        ml_job = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "python",
                "args": ["-c", training_script],
                "name": "ml-training-job",
                "runtime": "python-3.11-ml",
                "volumes": [f"{volume_name}:/models"],
                "max_cpu": 60,
                "max_memory": 2048,
            },
        )

        ml_job_data = json.loads(ml_job)
        ml_uuid = ml_job_data.get("job_uuid") or ml_job_data.get("uuid")
        cleanup_jobs(ml_uuid)

        await self._wait_for_job_completion(e2e_server, ml_uuid, max_wait=60)

        # Step 2: Deploy/use model info in Java
        java_deployment = """
import java.nio.file.*;
import java.util.*;

public class ModelDeployment {
    public static void main(String[] args) throws Exception {
        String modelInfo = Files.readString(Paths.get("/models/model_info.json"));
        System.out.println("Loaded model info: " + modelInfo);

        // Simulate deployment
        System.out.println("Model deployment simulation started");
        Thread.sleep(1000); // Simulate deployment time
        System.out.println("Model successfully deployed to Java service");
        System.out.println("Deployment completed");
    }
}
        """

        deploy_job = await e2e_server._execute_tool(
            "joblet_run_job",
            {
                "command": "bash",
                "args": [
                    "-c",
                    f"cat > ModelDeployment.java << 'EOF'\n{java_deployment}\nEOF\njavac ModelDeployment.java && java ModelDeployment",
                ],
                "name": "model-deployment-job",
                "runtime": "openjdk-21",
                "volumes": [f"{volume_name}:/models"],
                "max_cpu": 40,
                "max_memory": 1024,
                "work_dir": "/tmp",
            },
        )

        deploy_job_data = json.loads(deploy_job)
        deploy_uuid = deploy_job_data.get("job_uuid") or deploy_job_data.get("uuid")
        cleanup_jobs(deploy_uuid)

        await self._wait_for_job_completion(e2e_server, deploy_uuid)

        # Verify the pipeline worked
        ml_logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": ml_uuid}
        )

        deploy_logs = await e2e_server._execute_tool(
            "joblet_get_job_logs", {"job_uuid": deploy_uuid}
        )

        assert "Model trained with accuracy:" in ml_logs
        assert "Model info saved for Java deployment" in ml_logs
        assert "Loaded model info:" in deploy_logs
        assert "Model successfully deployed to Java service" in deploy_logs

    async def _wait_for_job_completion(self, server, job_uuid, max_wait=30):
        """Helper method to wait for job completion"""
        wait_time = 0

        while wait_time < max_wait:
            status_result = await server._execute_tool(
                "joblet_get_job_status", {"job_uuid": job_uuid}
            )
            status_data = json.loads(status_result)
            final_status = status_data.get("status")

            if final_status in ["completed", "failed", "stopped"]:
                return final_status

            await asyncio.sleep(1)
            wait_time += 1

        raise TimeoutError(f"Job {job_uuid} did not complete within {max_wait} seconds")


@pytest.mark.e2e
@pytest.mark.asyncio
class TestRuntimeManagement:
    """Test runtime management operations"""

    async def test_list_runtimes(self, e2e_server, server_status):
        """Test listing available runtimes"""
        result = await e2e_server._execute_tool("joblet_list_runtimes", {})

        # Should contain the expected runtimes
        expected_runtimes = [
            "python-3.11",
            "python-3.11-ml",
            "openjdk-21",
            "graalvmjdk-21",
        ]

        for runtime in expected_runtimes:
            # Check if runtime appears in the output (flexible parsing)
            assert runtime in result, f"Runtime {runtime} not found in output: {result}"

    async def test_runtime_installation_check(self, e2e_server, server_status):
        """Test runtime installation status (without actually installing)"""
        # This test checks if the install command is available and properly formatted
        # We don't actually install to avoid modifying the test environment

        try:
            # This should fail gracefully if runtime already exists
            await e2e_server._execute_tool(
                "joblet_install_runtime",
                {"runtime_spec": "python-3.11", "force_reinstall": False},
            )
        except RuntimeError as e:
            # Expected - runtime likely already installed
            assert (
                "already" in str(e).lower()
                or "exists" in str(e).lower()
                or "installed" in str(e).lower()
            )

    async def test_invalid_runtime_usage(self, e2e_server, cleanup_jobs, server_status):
        """Test error handling with invalid runtime"""
        with pytest.raises(RuntimeError):
            await e2e_server._execute_tool(
                "joblet_run_job",
                {
                    "command": "echo",
                    "args": ["test"],
                    "runtime": "nonexistent-runtime-12345",
                    "max_cpu": 25,
                    "max_memory": 512,
                },
            )
