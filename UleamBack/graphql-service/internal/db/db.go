package db

import (
	"database/sql"

	_ "github.com/lib/pq"
)

func Connect(url string) (*sql.DB, error) {
	pg, err := sql.Open("postgres", url)
	if err != nil {
		return nil, err
	}
	if err := pg.Ping(); err != nil {
		return nil, err
	}
	return pg, nil
}
