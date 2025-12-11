package main

import (
	"context"
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

	//Step 2. Prepare source code directory
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

}
