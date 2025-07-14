# k8s-image (Python)

This Python project scans a Kubernetes cluster for all container images, saves them to `live.txt`, and generates SHA1 values for each image in `sha1-live.csv`.

## Usage
1. Ensure you have access to your Kubernetes cluster (via kubeconfig).
2. Install dependencies:
   ```bash
   pip install kubernetes
   ```
3. Run the project:
   ```bash
   python main.py
   ```
4. Check `live.txt` and `sha1-live.csv` for results.

## Requirements
- Python 3.7+
- Access to a Kubernetes cluster
- `kubernetes` Python package
