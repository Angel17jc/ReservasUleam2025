package services

import (
	"database/sql"
	"fmt"
	"time"
)

type ReservationsService struct {
	db *sql.DB
}

func NewReservationsService(db *sql.DB) *ReservationsService {
	return &ReservationsService{db: db}
}

type ReservationFilter struct {
	Limit        int
	Offset       int
	UsuarioID    *int
	EspacioID    *int
	EstadoID     *int
	TipoEventoID *int
	FechaDesde   *string
	FechaHasta   *string
	ForceUserID  *int // for non-admin users
}

type ReservationResult struct {
	ID          int
	Codigo      string
	UsuarioID   int
	EspacioID   int
	TipoEvento  string
	Estado      string
	Fecha       string
	HoraInicio  string
	HoraFin     string
	Titulo      string
	Descripcion string
	EsBloqueo   bool
}

func (r *ReservationsService) List(filter ReservationFilter) ([]ReservationResult, error) {
	query := `SELECT r.id, r.codigo, r.usuario_id, r.espacio_id, 
	             COALESCE(te.nombre,''), COALESCE(es.nombre,''), 
	             r.fecha, r.hora_inicio, r.hora_fin, COALESCE(r.titulo,''), COALESCE(r.descripcion,''), r.es_bloqueo
	          FROM reserva r
	          LEFT JOIN tipo_evento te ON te.id = r.tipo_evento_id
	          LEFT JOIN estado_reserva es ON es.id = r.estado_id
	          WHERE 1=1`
	args := []interface{}{}
	argCount := 1

	if filter.UsuarioID != nil {
		query += fmt.Sprintf(" AND r.usuario_id = $%d", argCount)
		args = append(args, *filter.UsuarioID)
		argCount++
	} else if filter.ForceUserID != nil {
		query += fmt.Sprintf(" AND r.usuario_id = $%d", argCount)
		args = append(args, *filter.ForceUserID)
		argCount++
	}
	if filter.EspacioID != nil {
		query += fmt.Sprintf(" AND r.espacio_id = $%d", argCount)
		args = append(args, *filter.EspacioID)
		argCount++
	}
	if filter.EstadoID != nil {
		query += fmt.Sprintf(" AND r.estado_id = $%d", argCount)
		args = append(args, *filter.EstadoID)
		argCount++
	}
	if filter.TipoEventoID != nil {
		query += fmt.Sprintf(" AND r.tipo_evento_id = $%d", argCount)
		args = append(args, *filter.TipoEventoID)
		argCount++
	}
	if filter.FechaDesde != nil {
		query += fmt.Sprintf(" AND r.fecha >= $%d", argCount)
		args = append(args, *filter.FechaDesde)
		argCount++
	}
	if filter.FechaHasta != nil {
		query += fmt.Sprintf(" AND r.fecha <= $%d", argCount)
		args = append(args, *filter.FechaHasta)
		argCount++
	}

	query += fmt.Sprintf(" ORDER BY r.fecha DESC, r.hora_inicio DESC LIMIT %d OFFSET %d", filter.Limit, filter.Offset)

	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []ReservationResult
	for rows.Next() {
		var res ReservationResult
		var fecha time.Time
		if err := rows.Scan(&res.ID, &res.Codigo, &res.UsuarioID, &res.EspacioID, &res.TipoEvento, &res.Estado,
			&fecha, &res.HoraInicio, &res.HoraFin, &res.Titulo, &res.Descripcion, &res.EsBloqueo); err == nil {
			res.Fecha = fecha.Format("2006-01-02")
			// Debug: Log de datos leídos de BD
			fmt.Printf("[DEBUG] Reserva leída: ID=%d, UsuarioID=%d, EspacioID=%d, Titulo=%s\n", 
				res.ID, res.UsuarioID, res.EspacioID, res.Titulo)
			out = append(out, res)
		}
	}
	return out, nil
}

func (r *ReservationsService) Detail(id int, forceUserID *int, isAdmin bool) (*ReservationResult, error) {
	row := r.db.QueryRow(`SELECT r.id, r.codigo, r.usuario_id, r.espacio_id, 
	             COALESCE(te.nombre,''), COALESCE(es.nombre,''), 
	             r.fecha, r.hora_inicio, r.hora_fin, COALESCE(r.titulo,''), COALESCE(r.descripcion,''), r.es_bloqueo
	          FROM reserva r
	          LEFT JOIN tipo_evento te ON te.id = r.tipo_evento_id
	          LEFT JOIN estado_reserva es ON es.id = r.estado_id
	          WHERE r.id = $1`, id)
	var res ReservationResult
	var fecha time.Time
	if err := row.Scan(&res.ID, &res.Codigo, &res.UsuarioID, &res.EspacioID, &res.TipoEvento, &res.Estado,
		&fecha, &res.HoraInicio, &res.HoraFin, &res.Titulo, &res.Descripcion, &res.EsBloqueo); err != nil {
		return nil, err
	}
	if !isAdmin && forceUserID != nil && *forceUserID != res.UsuarioID {
		return nil, fmt.Errorf("forbidden")
	}
	res.Fecha = fecha.Format("2006-01-02")
	return &res, nil
}
