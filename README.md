# Kubernetes Horizontal Pod Autoscaling (HPA) CPU Load Test 🧪⚙️

This project demonstrates Horizontal Pod Autoscaling in a local Kubernetes cluster (via Docker Desktop) by simulating CPU load on a simple Python Flask application.

---

## Prerequisites 🛠️

Before you begin, ensure you have the following installed and configured:

**1. Docker Desktop:**
   - Install Docker Desktop for your operating system (macOS, Windows, or Linux).
   - Ensure Docker is running.
   - Download from: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

**2. Kubernetes (via Docker Desktop):**
   - Enable Kubernetes within Docker Desktop settings:
     - Open Docker Desktop > Settings > Kubernetes.
     - Check "Enable Kubernetes".
     - Apply & Restart. Docker Desktop will set up a single-node cluster.
   - Ensure `kubectl` is installed and configured to communicate with your Docker Desktop cluster. Docker Desktop usually handles this automatically. You can verify by running:
     ```bash
     kubectl cluster-info
     ```

**3. Metrics Server:**
   - The Kubernetes HPA relies on the Metrics Server to collect resource usage data (like CPU) from pods.
   - Install/enable the Metrics Server in your Docker Desktop Kubernetes cluster. For many versions of Docker Desktop, it's enabled by default. If not, or to ensure it's correctly configured for Docker Desktop, apply the following manifest after modifying it:
     - Download the manifest:
       ```bash
       curl -Lo metrics-server-components.yaml [https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml](https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml)
       ```
     - Edit `metrics-server-components.yaml`. In the `Deployment` for `metrics-server`, under `spec.template.spec.containers[0].args`, add:
       ```yaml
       - --kubelet-insecure-tls
       ```
     - Ensure the `args` section looks something like (the exact arguments might vary slightly based on the Metrics Server version, the key is to add `--kubelet-insecure-tls`):
       ```yaml
       args:
         - --cert-dir=/tmp
         - --secure-port=4443 # Or the port specified in the downloaded manifest
         - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
         - --kubelet-use-node-status-port
         - --metric-resolution=15s
         - --kubelet-insecure-tls # Crucial for Docker Desktop compatibility
       ```
     - Apply the modified manifest:
       ```bash
       kubectl apply -f metrics-server-components.yaml
       ```
     - Verify it's running:
       ```bash
       kubectl get pods -n kube-system -l k8s-app=metrics-server
       ```
       Wait for the pod to be `1/1 READY`.

**4. `hey` (Optional but Recommended for Load Testing):**
   - A command-line tool for sending HTTP load.
   - Installation (macOS example):
     ```bash
     brew install hey
     ```
   - (For other OS, see `hey` documentation: [https://github.com/rakyll/hey](https://github.com/rakyll/hey))


---


## Execution Steps 🚀

**Step 1: Build the Docker Image** 🐳
   - Navigate to your project directory in the terminal.
   - Build the Docker image for the application. This image will be used by your local Kubernetes cluster.
     ```bash
     docker build -t load-test-app:latest .
     ```

**Step 2: Deploy to Kubernetes** ☸️
   - Apply the Kubernetes manifests to create the Deployment, Service, and HPA.
     ```bash
     kubectl apply -f k8s-manifests.yaml
     ```

**Step 3: Check Initial Status** ✅
   - Verify that the resources are created and the initial pod is running.
     ```bash
     kubectl get deployment load-test-app-deployment
     kubectl get pods -l app=load-test-app
     kubectl get service load-test-app-service
     kubectl get hpa load-test-app-hpa
     ```
   - Initially, you should see `1` pod.
   - The HPA might show `<unknown>/50%` for CPU utilization until the Metrics Server collects initial metrics. This should update to a low percentage (e.g., `1%/50%`) after a minute or two.

**Step 4: Determine Service Access URL** 🌐
   - The service is exposed via `NodePort`. Docker Desktop makes `NodePort` services accessible on `localhost`.
   - Find the allocated `NodePort` and construct the URL:
     ```bash
     NODE_PORT=$(kubectl get service load-test-app-service -o jsonpath='{.spec.ports[0].nodePort}')
     SERVICE_URL="http://localhost:$NODE_PORT"
     echo "Service URL for testing: $SERVICE_URL"
     ```
   - Note this URL for the next step.

**Step 5: Monitor Pods and HPA** 👀
   - Open two new terminal windows to watch the HPA and pods in real-time.
   - **Terminal A - Watch Pods:**
     ```bash
     kubectl get pods -l app=load-test-app -w
     ```
     This will show pod status changes (e.g., new pods being created or terminated).
   - **Terminal B - Watch HPA:**
     ```bash
     kubectl get hpa load-test-app-hpa -w
     ```
     This will show HPA status, including current replicas and CPU utilization targets.

**Step 6: Generate CPU Load** 🔥
   - Use `hey` (or another load testing tool) to send traffic to your application's service URL.
   - This command sends traffic from 50 concurrent users for 30 seconds:
     ```bash
     # Replace $SERVICE_URL with the actual URL from Step 4 if not using the variable
     hey -c 50 -z 30s $SERVICE_URL
     ```
   - **Observe the watch terminals (A and B):**
     - As CPU load increases on the initial pod, the `TARGETS` in the HPA output (Terminal B) should rise above `50%`.
     - The HPA will then increase the `REPLICAS` count.
     - In Terminal A, you will see new pods being created (`Pending` -> `ContainerCreating` -> `Running`).
     - These new pods will help distribute the load.

**Step 7: Observe Scale Down** 📉
   - After the `hey` command finishes (load stops):
     - CPU utilization will drop.
     - The HPA will wait for the `stabilizationWindowSeconds` defined in `behavior.scaleDown` (30 seconds in this config).
     - After this period, the HPA will reduce the `REPLICAS` count back towards `minReplicas` (1).
     - In Terminal A, you will see pods being `Terminating` and then disappearing.

---

## Cleanup 🧹

Once you're done testing, delete the Kubernetes resources:
```bash
kubectl delete -f k8s-manifests.yaml
```

Optionally, remove the Docker image if you no longer need it:
```bash
docker rmi load-test-app:latest
```

This setup provides a clear demonstration of Kubernetes HPA reacting to CPU load by scaling application pods. 🎉
