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

	// Step 4.5. Pull data file using DVC with fallback to direct download
	// Try DVC first, but if it fails (e.g., remote not configured properly), download directly
	image = executeStep(ctx, image, "pull data with DVC",
		[]string{
			"bash", "-c",
			"mkdir -p data/raw && " +
				"git init && " +
				"git config user.email 'ci@example.com' && " +
				"git config user.name 'CI' && " +
				"(dvc update data/raw/raw_data.csv.dvc && dvc pull data/raw/raw_data.csv || " +
				"curl -fsSL https://raw.githubusercontent.com/Jeppe-T-K/itu-sdse-project-data/refs/heads/main/raw_data.csv -o data/raw/raw_data.csv) && " +
				"ls -lh data/raw/raw_data.csv",
		})

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

	//Step 7. Model selection
	image = executeStep(ctx, image, "model selection",
		[]string{
			"python", "-m", "src.models.model_selection",
		})

	//Step 8. Model deployment
	image = executeStep(ctx, image, "model deployment",
		[]string{
			"python", "-m", "src.models.model_deploy",
		})

	//Step 9. Package model into /app/model directory
	image = executeStep(ctx, image, "package model",
		[]string{
			"bash", "-c",
			"mkdir -p model && " +
				"cp artifacts/lead_model_lr.pkl model/model.pkl && " +
				"cp artifacts/columns_list.json model/columns_list.json && " +
				"cp artifacts/scaler.pkl model/scaler.pkl",
		})

	//Step 10. Export model directory from container to host
	fmt.Println("\n=== Exporting model directory ===")
	modelDir := image.Directory("/app/model")
	_, err = modelDir.Export(ctx, "./model")
	if err != nil {
		panic(fmt.Sprintf("Failed to export model directory: %v", err))
	}
	fmt.Println("Model directory exported successfully to ./model")

	fmt.Println("\n=== Dagger pipeline completed successfully ===")
}

// executeStep executes a command in the container with logging and error handling
func executeStep(ctx context.Context, c *dagger.Container, name string, cmd []string) *dagger.Container {
	fmt.Printf("\n=== Running step: %s ===\n", name)
	next := c.WithExec(cmd)
	_, err := next.Sync(ctx)
	if err != nil {
		// try to get both stdout and stderr for better debugging
		stdout, stdoutErr := next.Stdout(ctx)
		stderr, stderrErr := next.Stderr(ctx)
		errorMsg := fmt.Sprintf("step %s failed: %v", name, err)
		if stdoutErr == nil && stdout != "" {
			errorMsg += fmt.Sprintf("\nStdout: %s", stdout)
		}
		if stderrErr == nil && stderr != "" {
			errorMsg += fmt.Sprintf("\nStderr: %s", stderr)
		}
		panic(errorMsg)
	}
	// Print stdout if available for successful steps
	stdout, _ := next.Stdout(ctx)
	if stdout != "" {
		fmt.Print(stdout)
	}
	fmt.Printf("Step %s completed successfully\n", name)
	return next
}
