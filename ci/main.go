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

	// _ = image //to avoid unused variable error
	_, err = image.Sync(ctx)
	if err != nil {
		panic(err)
	}
	fmt.Println("Docker image built successfully")

	// Step 4. Test the Docker image to ensure it is working
	output, err := image.WithExec([]string{"python", "-c", "import sys; from src.data import make_dataset; print('Python imports working')"}).Stdout(ctx)
	if err != nil {
		panic(err)
	}
	fmt.Print(output)

	//Step 5. Run data processing
	image = executeStep(ctx, image, "data processing",
		[]string{
			"python", "-m", "src.data.make_dataset",
			"data/raw/raw_data.csv",
			"artifacts/train_data_gold.csv",
		})

	//Step 6. Model training
	image = executeStep(ctx, image, "model training",
		[]string{
			"python", "-m", "src.models.train_model",
		})

	//step 7.

}

// executeStep executes a command in the container with logging and error handling
func executeStep(ctx context.Context, c *dagger.Container, name string, cmd []string) *dagger.Container {
	fmt.Printf("\n=== Running step: %s ===\n", name)
	next := c.WithExec(cmd)
	_, err := next.Sync(ctx)
	if err != nil {
		panic(fmt.Sprintf("step %s failed: %v", name, err))
	}
	fmt.Printf("Step %s completed successfully\n", name)
	return next
}
