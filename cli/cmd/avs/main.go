// AVS CLI — Go skeleton (build-spec §1).
package main

import (
	"fmt"
	"os"
)

const usage = `avs — AutoScan / Sentry-AI command-line client

Usage:
  avs scope sign <file.json>
  avs scan start <roe-id>
  avs scan status <scan-id>
  avs report <scan-id>
  avs version

Environment:
  AVS_API_URL   Default API base URL
  AVS_TOKEN     OIDC bearer token
`

func main() {
	if len(os.Args) < 2 {
		fmt.Print(usage)
		os.Exit(2)
	}
	switch os.Args[1] {
	case "scope":
		fmt.Println("[stub] scope:", os.Args[2:])
	case "scan":
		fmt.Println("[stub] scan:", os.Args[2:])
	case "report":
		fmt.Println("[stub] report:", os.Args[2:])
	case "version":
		fmt.Println("avs v0.1.0")
	default:
		fmt.Print(usage)
		os.Exit(2)
	}
}
