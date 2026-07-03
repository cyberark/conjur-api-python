FROM golang:1.26 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 go build -o /mock-oidc-server .

FROM gcr.io/distroless/static-debian12
COPY --from=build /mock-oidc-server /mock-oidc-server
EXPOSE 80
ENTRYPOINT ["/mock-oidc-server"]
