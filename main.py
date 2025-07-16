import os
import hashlib
import csv
import requests
from kubernetes import client, config
from urllib.parse import urlparse

# Load kubeconfig
config.load_kube_config()
v1 = client.CoreV1Api()

images = set()
image_digests = dict()

# List all pods in all namespaces
ret = v1.list_pod_for_all_namespaces(watch=False)
for pod in ret.items:
    for container_status in pod.status.container_statuses or []:
        image = container_status.image
        digest = None
        if container_status.image_id and container_status.image_id.startswith("docker-pullable://"):
            digest = container_status.image_id.split("@sha256:")[-1] if "@sha256:" in container_status.image_id else None
        images.add(image)
        if digest:
            image_digests[image] = digest
    for container_status in pod.status.init_container_statuses or []:
        image = container_status.image
        digest = None
        if container_status.image_id and container_status.image_id.startswith("docker-pullable://"):
            digest = container_status.image_id.split("@sha256:")[-1] if "@sha256:" in container_status.image_id else None
        images.add(image)
        if digest:
            image_digests[image] = digest

# Write images to live.txt
with open("live.txt", "w") as f:
    for img in images:
        f.write(f"{img}\n")

def get_registry_digest(image, registry, username=None, password=None):
    # Parse image name
    repo = image
    tag = "latest"
    if "/" not in image:
        repo = f"library/{image}"
    if ":" in repo:
        repo, tag = repo.split(":", 1)
    # Build URLs
    if registry == "docker.io":
        manifest_url = f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}"
        headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        if username and password:
            resp = requests.get(manifest_url, headers=headers, auth=(username, password))
        else:
            resp = requests.get(manifest_url, headers=headers)
        if resp.status_code == 401:
            return ""
        if resp.status_code != 200:
            return ""
        digest = resp.headers.get("Docker-Content-Digest", "")
        if digest.startswith("sha256:"):
            return digest.split(":", 1)[1]
        return ""
    else:
        manifest_url = f"https://{registry}/v2/{repo}/manifests/{tag}"
        headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        if username and password:
            resp = requests.get(manifest_url, headers=headers, auth=(username, password))
        else:
            resp = requests.get(manifest_url, headers=headers)
        if resp.status_code == 401:
            return ""
        if resp.status_code != 200:
            return ""
        digest = resp.headers.get("Docker-Content-Digest", "")
        if digest.startswith("sha256:"):
            return digest.split(":", 1)[1]
        return ""

# Read registries
with open("registry-local.txt") as f:
    local_registries = [line.strip() for line in f if line.strip() and not line.startswith("//")]
with open("docker-remote.txt") as f:
    remote_registries = [line.strip() for line in f if line.strip() and not line.startswith("//")]

# When calling get_registry_digest for docker.io, pass username and token if available
DOCKER_USERNAME = os.getenv("DOCKER_USERNAME")
DOCKER_TOKEN = os.getenv("DOCKER_TOKEN")

# Write sha1-live.csv
with open("sha1-live.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["image", "sha256_digest", "registry-internal", "registry-remote"])
    for img in images:
        digest = image_digests.get(img, "")
        internal_digests = []
        for reg in local_registries:
            internal_digests.append(get_registry_digest(img, reg))
        remote_digests = []
        for reg in remote_registries:
            if reg == "docker.io":
                remote_digests.append(get_registry_digest(img, reg, DOCKER_USERNAME, DOCKER_TOKEN))
            else:
                remote_digests.append(get_registry_digest(img, reg))
        writer.writerow([img, digest, ";".join(internal_digests), ";".join(remote_digests)])
