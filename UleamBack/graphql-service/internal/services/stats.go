package services

import (
	"database/sql"
	"fmt"
)

type StatsService struct {
	db *sql.DB
}

func NewStatsService(db *sql.DB) *StatsService {
	return &StatsService{db: db}
}

type GroupedMetric struct {
	Label    string
	Cantidad int
}

type Stats struct {
	TotalReservas      int
	ReservasPendientes int
	ReservasAprobadas  int
	ReservasRechazadas int
	ReservasCanceladas int
	EspaciosActivos    int
	UsuariosActivos    int
}

func (s *StatsService) Totals() (Stats, error) {
	var stats Stats
	s.db.QueryRow("SELECT COUNT(*) FROM reserva").Scan(&stats.TotalReservas)
	s.db.QueryRow("SELECT COUNT(*) FROM reserva WHERE estado_id = 1").Scan(&stats.ReservasPendientes)
	// Estados según init.sql:
	// 1 Pendiente, 2 Aprobada, 3 Rechazada, 4 Completada, 5 Cancelada
	s.db.QueryRow("SELECT COUNT(*) FROM reserva WHERE estado_id = 2").Scan(&stats.ReservasAprobadas)
	s.db.QueryRow("SELECT COUNT(*) FROM reserva WHERE estado_id = 3").Scan(&stats.ReservasRechazadas)
	s.db.QueryRow("SELECT COUNT(*) FROM reserva WHERE estado_id = 5").Scan(&stats.ReservasCanceladas)
	s.db.QueryRow("SELECT COUNT(*) FROM espacio WHERE estado = 'activo'").Scan(&stats.EspaciosActivos)
	s.db.QueryRow("SELECT COUNT(*) FROM usuario WHERE estado = 'activo'").Scan(&stats.UsuariosActivos)
	return stats, nil
}

func (s *StatsService) TopEspacios(fechaDesde, fechaHasta *string, limit int) ([]GroupedMetric, error) {
	query := `SELECT e.nombre, COUNT(*) as total
	          FROM reserva r
	          JOIN espacio e ON e.id = r.espacio_id
	          WHERE 1=1`
	args := []interface{}{}
	argCount := 1
	if fechaDesde != nil {
		query += fmt.Sprintf(" AND r.fecha >= $%d", argCount)
		args = append(args, *fechaDesde)
		argCount++
	}
	if fechaHasta != nil {
		query += fmt.Sprintf(" AND r.fecha <= $%d", argCount)
		args = append(args, *fechaHasta)
		argCount++
	}
	query += " GROUP BY e.nombre ORDER BY total DESC"
	if limit <= 0 {
		limit = 10
	}
	query += fmt.Sprintf(" LIMIT %d", limit)
	return s.queryGrouped(query, args...)
}

func (s *StatsService) TopUsuarios(fechaDesde, fechaHasta *string, limit int) ([]GroupedMetric, error) {
	query := `SELECT u.email, COUNT(*) as total
	          FROM reserva r
	          JOIN usuario u ON u.id = r.usuario_id
	          WHERE 1=1`
	args := []interface{}{}
	argCount := 1
	if fechaDesde != nil {
		query += fmt.Sprintf(" AND r.fecha >= $%d", argCount)
		args = append(args, *fechaDesde)
		argCount++
	}
	if fechaHasta != nil {
		query += fmt.Sprintf(" AND r.fecha <= $%d", argCount)
		args = append(args, *fechaHasta)
		argCount++
	}
	query += " GROUP BY u.email ORDER BY total DESC"
	if limit <= 0 {
		limit = 10
	}
	query += fmt.Sprintf(" LIMIT %d", limit)
	return s.queryGrouped(query, args...)
}

func (s *StatsService) ReservasPorEstado(fechaDesde, fechaHasta *string) ([]GroupedMetric, error) {
	query := `SELECT es.nombre, COUNT(*) as total
	          FROM reserva r
	          JOIN estado_reserva es ON es.id = r.estado_id
	          WHERE 1=1`
	args := []interface{}{}
	argCount := 1
	if fechaDesde != nil {
		query += fmt.Sprintf(" AND r.fecha >= $%d", argCount)
		args = append(args, *fechaDesde)
		argCount++
	}
	if fechaHasta != nil {
		query += fmt.Sprintf(" AND r.fecha <= $%d", argCount)
		args = append(args, *fechaHasta)
		argCount++
	}
	query += " GROUP BY es.nombre ORDER BY total DESC"
	return s.queryGrouped(query, args...)
}

func (s *StatsService) ReservasPorTipoEvento(fechaDesde, fechaHasta *string) ([]GroupedMetric, error) {
	query := `SELECT COALESCE(te.nombre,'SinTipo') as nombre, COUNT(*) as total
	          FROM reserva r
	          LEFT JOIN tipo_evento te ON te.id = r.tipo_evento_id
	          WHERE 1=1`
	args := []interface{}{}
	argCount := 1
	if fechaDesde != nil {
		query += fmt.Sprintf(" AND r.fecha >= $%d", argCount)
		args = append(args, *fechaDesde)
		argCount++
	}
	if fechaHasta != nil {
		query += fmt.Sprintf(" AND r.fecha <= $%d", argCount)
		args = append(args, *fechaHasta)
		argCount++
	}
	query += " GROUP BY nombre ORDER BY total DESC"
	return s.queryGrouped(query, args...)
}

func (s *StatsService) queryGrouped(query string, args ...interface{}) ([]GroupedMetric, error) {
	rows, err := s.db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []GroupedMetric
	for rows.Next() {
		var gm GroupedMetric
		if err := rows.Scan(&gm.Label, &gm.Cantidad); err == nil {
			out = append(out, gm)
		}
	}
	return out, nil
}
