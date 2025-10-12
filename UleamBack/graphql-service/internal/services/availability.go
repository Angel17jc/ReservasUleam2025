package services

import (
	"database/sql"
	"fmt"
	"strings"
	"time"
)

type AvailabilityService struct {
	db *sql.DB
}

func NewAvailabilityService(db *sql.DB) *AvailabilityService {
	return &AvailabilityService{db: db}
}

type interval struct {
	Ini string
	Fin string
}

func (a *AvailabilityService) CalcAvailability(espacioID int, fecha time.Time, incluirPendientes bool) (map[string]interface{}, error) {
	blockingNames := []string{"Aprobada"}
	if incluirPendientes {
		blockingNames = append(blockingNames, "Pendiente")
	}
	blockIDs, err := a.fetchEstadoIDs(blockingNames)
	if err != nil {
		return nil, err
	}
	if len(blockIDs) == 0 {
		blockIDs = []int{-1}
	}

	rows, err := a.db.Query(`
		SELECT r.id, es.nombre as estado, r.hora_inicio, r.hora_fin, r.titulo, r.usuario_id
		FROM reserva r
		JOIN estado_reserva es ON es.id = r.estado_id
		WHERE r.espacio_id = $1 AND r.fecha = $2 AND r.estado_id = ANY($3)
		ORDER BY r.hora_inicio
	`, espacioID, fecha.Format("2006-01-02"), pqIntArray(blockIDs))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var intervals []interval
	var ocupados []map[string]interface{}
	for rows.Next() {
		var id int
		var estado, ini, fin string
		var titulo sql.NullString
		var uid int
		if err := rows.Scan(&id, &estado, &ini, &fin, &titulo, &uid); err == nil {
			ocupados = append(ocupados, map[string]interface{}{
				"id":          id,
				"estado":      estado,
				"hora_inicio": ini[:5],
				"hora_fin":    fin[:5],
				"titulo":      nullToString(titulo),
				"usuario_id":  uid,
			})
			intervals = append(intervals, interval{Ini: ini[:5], Fin: fin[:5]})
		}
	}

	libres := computeLibreSlots("08:00", "18:00", intervals)

	var espacioNombre sql.NullString
	a.db.QueryRow(`SELECT nombre FROM espacio WHERE id = $1`, espacioID).Scan(&espacioNombre)

	return map[string]interface{}{
		"espacio_id":     espacioID,
		"espacio_nombre": nullToString(espacioNombre),
		"fecha":          fecha.Format("2006-01-02"),
		"dia_semana":     fecha.Weekday().String(),
		"ocupados":       ocupados,
		"libres":         libres,
	}, nil
}

func (a *AvailabilityService) fetchEstadoIDs(names []string) ([]int, error) {
	rows, err := a.db.Query(`SELECT id FROM estado_reserva WHERE nombre = ANY($1)`, pqStringArray(names))
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := []int{}
	for rows.Next() {
		var id int
		if err := rows.Scan(&id); err == nil {
			out = append(out, id)
		}
	}
	return out, nil
}

// Helper functions
func nullToString(ns sql.NullString) string {
	if ns.Valid {
		return ns.String
	}
	return ""
}

func computeLibreSlots(inicio string, fin string, intervals []interval) []map[string]interface{} {
	parse := func(s string) time.Time {
		t, _ := time.Parse("15:04", s)
		return t
	}
	startDay := parse(inicio)
	endDay := parse(fin)
	libres := []map[string]interface{}{}
	cursor := startDay

	for _, it := range intervals {
		ini := parse(it.Ini)
		fin := parse(it.Fin)
		if ini.After(cursor) {
			libres = append(libres, map[string]interface{}{
				"hora_inicio": cursor.Format("15:04"),
				"hora_fin":    ini.Format("15:04"),
			})
		}
		if fin.After(cursor) {
			cursor = fin
		}
	}
	if cursor.Before(endDay) {
		libres = append(libres, map[string]interface{}{
			"hora_inicio": cursor.Format("15:04"),
			"hora_fin":    endDay.Format("15:04"),
		})
	}
	return libres
}

// helpers to pass arrays into ANY($1)
func pqStringArray(arr []string) interface{} {
	return fmt.Sprintf(`{"%s"}`, strings.Join(arr, `","`))
}

func pqIntArray(arr []int) interface{} {
	var sb strings.Builder
	sb.WriteString("{")
	for i, v := range arr {
		sb.WriteString(fmt.Sprintf("%d", v))
		if i < len(arr)-1 {
			sb.WriteString(",")
		}
	}
	sb.WriteString("}")
	return sb.String()
}
