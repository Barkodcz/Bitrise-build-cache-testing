package main

import (
	"fmt"

	"github.com/bitrise-build-cache-showcase/projects/go/pkg/core"
	"github.com/bitrise-build-cache-showcase/projects/go/pkg/leaf"
)

func main() {
	fmt.Println(core.Greeting())
	fmt.Println(leaf.Label())
}
