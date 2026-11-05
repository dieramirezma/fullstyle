FROM golang:1.27.3-bookworm@sha256:d9b6a1beb9474adc2a1ce842573639b44b2a0dd49b6669f51d3821baf9ec37c9 AS build
WORKDIR /src
COPY FullStyle-Backend-Go/go.mod FullStyle-Backend-Go/go.sum ./
RUN --mount=type=cache,id=fullstyle-portfolio-go,target=/go/pkg/mod go mod download
COPY FullStyle-Backend-Go .
RUN --mount=type=cache,id=fullstyle-portfolio-go,target=/go/pkg/mod --mount=type=cache,id=fullstyle-portfolio-go-build,target=/root/.cache/go-build go install golang.org/x/vuln/cmd/govulncheck@v1.9.0 && govulncheck -show verbose ./...
RUN --mount=type=cache,id=fullstyle-portfolio-go,target=/go/pkg/mod --mount=type=cache,id=fullstyle-portfolio-go-build,target=/root/.cache/go-build test -z "$(gofmt -l .)" && go vet ./... && go test ./... && CGO_ENABLED=0 go build -trimpath -o /auth . && CGO_ENABLED=0 go test -c -o /integration-tests ./test
FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3 AS checks
COPY --from=build /integration-tests /integration-tests
USER 65532:65532
CMD ["/integration-tests", "-test.v"]
FROM debian:bookworm-slim@sha256:99c0b25c46d0214d5a2091092e7908907dcaecd6a962cde0ac700acee222b6f3
COPY --from=build /auth /auth
USER 65532:65532
CMD ["/auth"]
