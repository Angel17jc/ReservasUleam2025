package config

import (
	"log"
	"os"
)

type Config struct {
	DatabaseURL  string
	JWTSecret    string
	Port         string
	WebsocketURL string
}

func Load() Config {
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Fatal("DATABASE_URL is required")
	}
	secret := os.Getenv("SECRET_KEY")
	if secret == "" {
		secret = os.Getenv("JWT_SECRET")
	}
	if secret == "" {
		log.Fatal("SECRET_KEY or JWT_SECRET is required")
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}
	return Config{
		DatabaseURL:  dbURL,
		JWTSecret:    secret,
		Port:         port,
		WebsocketURL: os.Getenv("WEBSOCKET_SERVICE_URL"),
	}
}
