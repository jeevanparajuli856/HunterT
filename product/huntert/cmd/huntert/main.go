package main

import (
	"os"

	"huntert/internal/cli"
)

func main() {
	os.Exit(cli.Execute(os.Args[1:]))
}
