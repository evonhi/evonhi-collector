# Contributing to evonhi-collector

## Workflow

- Work on a short-lived branch (`feat/...`, `fix/...`, `chore/...`) and open a pull request against `main`.
- A pull request needs a green CI run before it is merged.
- Keep pull requests small: one theme, ideally under ~400 changed lines.

## Commits

- One logical change per commit; every commit builds and passes the tests.
- One-line message in [Conventional Commits](https://www.conventionalcommits.org) style, in the imperative,
  under 72 characters: `fix(ingest): reject snapshots that violate the contract`.
- Add a body only when the reason for the change is not obvious from the diff.

## Checks

```bash
go vet ./... && gofmt -l . && go test -race ./...
```

The agent is read-only. Any new resource it lists must be added to the chart's ClusterRole (a test enforces it), and any payload change must update `internal/k8s/testdata/snapshot.golden.json` and stay valid against the contract in `evonhi-core`.
