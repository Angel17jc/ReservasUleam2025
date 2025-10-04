package main

import (
	"log"
	"net/http"

	"graphql-service/internal/auth"
	"graphql-service/internal/config"
	"graphql-service/internal/db"
	"graphql-service/internal/schema"
	"graphql-service/internal/services"
)

func main() {
	cfg := config.Load()

	pg, err := db.Connect(cfg.DatabaseURL)
	if err != nil {
		log.Fatal(err)
	}
	defer pg.Close()

	userSvc := services.NewUserService(pg)

	schemaGraphQL, err := schema.Build(pg, cfg, userSvc)
	if err != nil {
		log.Fatal("failed to build schema: ", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/", schema.HandleRoot)
	mux.Handle("/graphql", auth.Middleware(cfg.JWTSecret, userSvc, schema.GraphQLHandler(schemaGraphQL)))

	log.Printf("GraphQL API server running on http://0.0.0.0:%s", cfg.Port)
	if err := http.ListenAndServe("0.0.0.0:"+cfg.Port, auth.EnableCORS(mux)); err != nil {
		log.Fatal(err)
	}
}
