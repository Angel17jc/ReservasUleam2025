package services

import (
	"database/sql"
	"fmt"

	"graphql-service/internal/auth"
)

type UserService struct {
	db *sql.DB
}

func NewUserService(db *sql.DB) *UserService {
	return &UserService{db: db}
}

func (u *UserService) LoadUser(id int) (*auth.AuthInfo, error) {
	row := u.db.QueryRow(`SELECT id, email, tipo_usuario_id FROM usuario WHERE id = $1`, id)
	var uid int
	var email string
	var tipo int
	if err := row.Scan(&uid, &email, &tipo); err != nil {
		return nil, fmt.Errorf("user not found")
	}
	return &auth.AuthInfo{
		UserID:  uid,
		Email:   email,
		TipoID:  tipo,
		IsAdmin: tipo == 1,
	}, nil
}
