package main

import (
	"context"
	"crypto/sha1"
	"encoding/csv"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/tools/clientcmd"
)

func main() {
	// Load kubeconfig
	kubeconfig := filepath.Join(os.Getenv("HOME"), ".kube", "config")
	config, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
	if err != nil {
		panic(err)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		panic(err)
	}

	images := make(map[string]struct{})

	// List all pods in all namespaces
	pods, err := clientset.CoreV1().Pods("").List(context.Background(), metav1.ListOptions{})
	if err != nil {
		panic(err)
	}

	for _, pod := range pods.Items {
		for _, container := range pod.Spec.Containers {
			images[container.Image] = struct{}{}
		}
		for _, container := range pod.Spec.InitContainers {
			images[container.Image] = struct{}{}
		}
	}

	// Write images to live.txt
	var imageList []string
	for img := range images {
		imageList = append(imageList, img)
	}
	if err := ioutil.WriteFile("live.txt", []byte(fmt.Sprintf("%s\n", imageList)), 0644); err != nil {
		panic(err)
	}

	// Write sha1-live.csv
	csvFile, err := os.Create("sha1-live.csv")
	if err != nil {
		panic(err)
	}
	defer csvFile.Close()
	writer := csv.NewWriter(csvFile)
	defer writer.Flush()
	writer.Write([]string{"image", "sha1"})
	for _, img := range imageList {
		hash := fmt.Sprintf("%x", sha1.Sum([]byte(img)))
		writer.Write([]string{img, hash})
	}
}
