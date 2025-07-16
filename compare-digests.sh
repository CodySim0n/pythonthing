#!/bin/bash
# Get all images from all pods in the cluster and store in images.txt
kubectl get pods --all-namespaces -o json | jq -r '.items[].spec.containers[].image, .items[].spec.initContainers[].image' | sort | uniq > images.txt

# Iterate over images and process each
while read -r image; do
    echo "Processing $image"
    # Pull image using podman
    podman pull "$image"
    # Get local digest
    local_digest=$(podman inspect --format '{{.Digest}}' "$image")
    echo "Local digest: $local_digest"

    # Parse repo and tag
    repo_tag="$image"
    repo="${repo_tag%%:*}"
    tag="${repo_tag##*:}"
    if [ "$repo" = "$tag" ]; then
        tag="latest"
    fi

    # Pull from docker.io and get digest
    podman pull "docker.io/$repo:$tag"
    docker_digest=$(podman inspect --format '{{.Digest}}' "docker.io/$repo:$tag")
    echo "Docker.io digest: $docker_digest"

    # Compare digests
    if [ "$local_digest" = "$docker_digest" ]; then
        echo "$image: digests match" >> digest-compare.txt
    else
        echo "$image: digests differ" >> digest-compare.txt
    fi

done < images.txt
