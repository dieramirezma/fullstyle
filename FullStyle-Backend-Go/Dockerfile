# Etapa 1: build
FROM golang:1.24-alpine AS builder


WORKDIR /app

# Instalar dependencias necesarias
COPY go.mod go.sum ./
RUN go mod download

# Copiar el resto del proyecto
COPY . .

# Compilar el proyecto
RUN go build -o main .

# Etapa 2: ejecución
FROM alpine:latest

# Instalar certificados CA
RUN apk --no-cache add ca-certificates && \
    update-ca-certificates

WORKDIR /app

# Copiar el binario y archivos necesarios
COPY --from=builder /app/main .
COPY .env .

# Asegurarse que el contenedor pueda usar el puerto 80
USER root

EXPOSE 80

CMD ["./main"]
