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

	fmt.Println("Connected to Dagger!")
}
