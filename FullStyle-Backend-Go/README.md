# Go Web Application

This is a simple web application built using Go. The application follows a structured approach with separate directories for configuration, models, routes, services, and utilities.

## Project Structure

```
go-web-app
├── cmd
│   └── app
│       └── main.go          # Entry point of the application
├── internal
│   ├── config
│   │   └── config.go       # Configuration settings
│   ├── models
│   │   └── models.go       # Data models
│   ├── routes
│   │   └── routes.go       # HTTP routes
│   ├── services
│   │   └── services.go     # Business logic and service functions
│   └── utils
│       └── utils.go        # Utility functions
├── Dockerfile               # Docker image instructions
├── docker-compose.yml       # Docker Compose configuration
├── go.mod                   # Module definition
├── go.sum                   # Dependency checksums
└── README.md                # Project documentation
```

## Getting Started

### Prerequisites

- Go (version 1.16 or later)
- Docker (for containerization)

### Installation

1. Install dependencies:
   ```
   go mod tidy
   ```

### Running the Application

To build and run the application using Docker, execute:

```
docker-compose up --build
```

### Generating Documentation

Once documented the routes, execute:

```
swag init 
```
This auto generates the docs.go, swagger.json and swagger.yaml

### Usage

Once the application is running, you can access it at `http://localhost:5000`.