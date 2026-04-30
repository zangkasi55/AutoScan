// CLI wired to the API. Authenticates with AVS_TOKEN.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
)

const usage = `avs — AutoScan / Sentry-AI command-line client

Usage:
  avs scope create <draft.json>
  avs scope sign   <roe-id> <jws-file>
  avs scan start   <roe-id>
  avs scan status  <scan-id>
  avs report       <scan-id>
  avs version

Environment:
  AVS_API_URL  Default API base URL
  AVS_TOKEN    OIDC bearer token
`

func apiBase() string {
	if v := os.Getenv("AVS_API_URL"); v != "" {
		return v
	}
	return "http://localhost:8080"
}

func req(method, path string, body any) (map[string]any, error) {
	var buf io.Reader
	if body != nil {
		b, _ := json.Marshal(body)
		buf = bytes.NewReader(b)
	}
	r, err := http.NewRequest(method, apiBase()+path, buf)
	if err != nil {
		return nil, err
	}
	if t := os.Getenv("AVS_TOKEN"); t != "" {
		r.Header.Set("Authorization", "Bearer "+t)
	}
	if body != nil {
		r.Header.Set("Content-Type", "application/json")
	}
	resp, err := http.DefaultClient.Do(r)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	out, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("API %d: %s", resp.StatusCode, string(out))
	}
	var m map[string]any
	json.Unmarshal(out, &m)
	return m, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Print(usage)
		os.Exit(2)
	}
	switch os.Args[1] {
	case "scope":
		scopeCmd(os.Args[2:])
	case "scan":
		scanCmd(os.Args[2:])
	case "report":
		if len(os.Args) < 3 {
			fmt.Println("usage: avs report <scan-id>")
			os.Exit(2)
		}
		printJSON(req("GET", "/api/v1/scans/"+os.Args[2], nil))
	case "version":
		fmt.Println("avs v0.1.0")
	default:
		fmt.Print(usage)
		os.Exit(2)
	}
}

func scopeCmd(a []string) {
	if len(a) == 0 {
		fmt.Println(usage)
		os.Exit(2)
	}
	switch a[0] {
	case "create":
		if len(a) < 2 {
			fmt.Println("usage: avs scope create <draft.json>")
			os.Exit(2)
		}
		f, err := os.ReadFile(filepath.Clean(a[1]))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		var draft any
		json.Unmarshal(f, &draft)
		printJSON(req("POST", "/api/v1/scopes", draft))
	case "sign":
		if len(a) < 3 {
			fmt.Println("usage: avs scope sign <roe-id> <jws-file>")
			os.Exit(2)
		}
		jws, _ := os.ReadFile(filepath.Clean(a[2]))
		printJSON(req("POST", "/api/v1/scopes/"+a[1]+"/sign", map[string]any{"jws": string(jws)}))
	default:
		fmt.Println(usage)
		os.Exit(2)
	}
}

func scanCmd(a []string) {
	if len(a) == 0 {
		fmt.Println(usage)
		os.Exit(2)
	}
	switch a[0] {
	case "start":
		if len(a) < 2 {
			fmt.Println("usage: avs scan start <roe-id>")
			os.Exit(2)
		}
		printJSON(req("POST", "/api/v1/scans", map[string]any{"roeId": a[1]}))
	case "status":
		if len(a) < 2 {
			fmt.Println("usage: avs scan status <scan-id>")
			os.Exit(2)
		}
		printJSON(req("GET", "/api/v1/scans/"+a[1], nil))
	default:
		fmt.Println(usage)
		os.Exit(2)
	}
}

func printJSON(m map[string]any, err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	b, _ := json.MarshalIndent(m, "", "  ")
	fmt.Println(string(b))
}
