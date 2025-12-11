package main

import (
	"context"
	"fmt"
	"os"

	"dagger.io/dagger"
)

func main() {
	// Step 1. Initialize Dagger Client
	ctx := context.Background()
	client, err := dagger.Connect(ctx, dagger.WithLogOutput(os.Stderr))
	if err != nil {
		panic(err)
	}
	defer client.Close()

	//Step 2. Prepare source code directory: exclude files that are not needed in the container
	source := client.Host().Directory(".", dagger.HostDirectoryOpts{
		Exclude: []string{
			".git",
			".github",
			"artifacts",
			"mlruns",
			"__pycache__",
			"original_files",
			"venv",
			"env",
			"ENV",
			".venv",
		},
	})

	//Step 3. Build Docker image from Dockerfile
	image := source.DockerBuild()

	_ = image //to avoid unused variable error
	_, err = image.Sync(ctx)
	if err != nil {
		panic(err)
	}
	fmt.Println("Docker image built successfully")
}
