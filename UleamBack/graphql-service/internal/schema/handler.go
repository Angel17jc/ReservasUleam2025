package schema

import (
	"encoding/json"
	"net/http"

	"github.com/graphql-go/graphql"
)

// GraphQLHandler returns an http.Handler that executes GraphQL queries against the given schema.
func GraphQLHandler(s graphql.Schema) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Only POST requests are allowed", http.StatusMethodNotAllowed)
			return
		}

		var params struct {
			Query     string                 `json:"query"`
			Variables map[string]interface{} `json:"variables"`
		}
		if err := json.NewDecoder(r.Body).Decode(&params); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		result := graphql.Do(graphql.Params{
			Schema:         s,
			RequestString:  params.Query,
			VariableValues: params.Variables,
			Context:        r.Context(),
		})

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	})
}

// HandleRoot is a simple health/info handler.
func HandleRoot(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"message":          "ULEAM Reservas - GraphQL API",
		"version":          "1.1.0",
		"service":          "GraphQL API (Golang)",
		"status":           "running",
		"graphql_endpoint": "/graphql",
		"requires_auth":    true,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
