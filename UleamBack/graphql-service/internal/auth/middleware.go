package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/golang-jwt/jwt/v5"
)

type contextKey string

const userCtxKey contextKey = "userCtx"

type AuthInfo struct {
	UserID  int
	Email   string
	TipoID  int
	IsAdmin bool
}

type UserProvider interface {
	LoadUser(id int) (*AuthInfo, error)
}

func Middleware(jwtSecret string, users UserProvider, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		tokenStr := extractToken(r)
		if tokenStr == "" {
			http.Error(w, "Missing Authorization token", http.StatusUnauthorized)
			return
		}
		claims := jwt.MapClaims{}
		_, err := jwt.ParseWithClaims(tokenStr, claims, func(token *jwt.Token) (interface{}, error) {
			return []byte(jwtSecret), nil
		})
		if err != nil {
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}
		sub, ok := claims["sub"]
		if !ok {
			http.Error(w, "Token without sub", http.StatusUnauthorized)
			return
		}
		userID, err := toInt(sub)
		if err != nil {
			http.Error(w, "Invalid sub claim", http.StatusUnauthorized)
			return
		}
		user, err := users.LoadUser(userID)
		if err != nil {
			http.Error(w, "User not found", http.StatusUnauthorized)
			return
		}
		ctx := context.WithValue(r.Context(), userCtxKey, user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func EnableCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "http://localhost:5173")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		w.Header().Set("Access-Control-Allow-Credentials", "true")

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func FromContext(ctx context.Context) *AuthInfo {
	val := ctx.Value(userCtxKey)
	if val == nil {
		return nil
	}
	if ai, ok := val.(*AuthInfo); ok {
		return ai
	}
	return nil
}

func extractToken(r *http.Request) string {
	authHeader := r.Header.Get("Authorization")
	if strings.HasPrefix(authHeader, "Bearer ") {
		return strings.TrimSpace(strings.TrimPrefix(authHeader, "Bearer "))
	}
	if t := r.URL.Query().Get("token"); t != "" {
		return t
	}
	return ""
}

func toInt(val interface{}) (int, error) {
	switch v := val.(type) {
	case float64:
		return int(v), nil
	case string:
		return strconv.Atoi(v)
	case json.Number:
		return strconv.Atoi(v.String())
	default:
		return 0, fmt.Errorf("unknown type")
	}
}
