package routes

import (
	"net/http"

	"github.com/gorilla/mux"
)

// InitializeRoutes sets up the application routes
func InitializeRoutes() *mux.Router {
	router := mux.NewRouter()

	// Define your routes here
	router.HandleFunc("/", HomeHandler).Methods("GET")
	// Add more routes as needed

	return router
}

// HomeHandler handles the home route
func HomeHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Welcome to the Go Web App!"))
}
