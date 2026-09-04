# ---------- Build ----------
FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/graphql-service ./cmd/...

# ---------- Runtime ----------
FROM alpine:3.20
WORKDIR /app
RUN apk add --no-cache ca-certificates curl
COPY --from=build /out/graphql-service /app/graphql-service
EXPOSE 8081
CMD ["/app/graphql-service"]
