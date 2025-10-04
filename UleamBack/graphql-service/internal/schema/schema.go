package schema

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/graphql-go/graphql"
	"graphql-service/internal/auth"
	"graphql-service/internal/config"
	"graphql-service/internal/services"
)

type Dependencies struct {
	Reservations  *services.ReservationsService
	Availability  *services.AvailabilityService
	Stats         *services.StatsService
	Users         services.UserService
	Webhook       *services.WebhookClient
}

func Build(db *sql.DB, cfg config.Config, users *services.UserService) (graphql.Schema, error) {
	deps := Dependencies{
		Reservations: services.NewReservationsService(db),
		Availability: services.NewAvailabilityService(db),
		Stats:        services.NewStatsService(db),
		Users:        *users,
	}
	if cfg.WebsocketURL != "" {
		deps.Webhook = services.NewWebhookClient(cfg.WebsocketURL)
	}
	root := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"reservas":              reservasField(deps),
			"reserva":               reservaDetailField(deps),
			"estadisticas":          estadisticasField(deps),
			"espaciosMasReservados": espaciosTopField(deps),
			"usuariosMasActivos":    usuariosTopField(deps),
			"reservasPorEstado":     reservasPorEstadoField(deps),
			"reservasPorTipoEvento": reservasPorTipoEventoField(deps),
			"disponibilidad":        disponibilidadField(deps),
		},
	})
	return graphql.NewSchema(graphql.SchemaConfig{Query: root})
}

// Types
var reservaType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Reserva",
	Fields: graphql.Fields{
		"id":          &graphql.Field{Type: graphql.Int},
		"codigo":      &graphql.Field{Type: graphql.String},
		"usuario_id":  &graphql.Field{Type: graphql.Int},
		"espacio_id":  &graphql.Field{Type: graphql.Int},
		"tipo_evento": &graphql.Field{Type: graphql.String},
		"estado":      &graphql.Field{Type: graphql.String},
		"fecha":       &graphql.Field{Type: graphql.String},
		"hora_inicio": &graphql.Field{Type: graphql.String},
		"hora_fin":    &graphql.Field{Type: graphql.String},
		"titulo":      &graphql.Field{Type: graphql.String},
		"descripcion": &graphql.Field{Type: graphql.String},
		"es_bloqueo":  &graphql.Field{Type: graphql.Boolean},
	},
})

var estadisticasType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Estadisticas",
	Fields: graphql.Fields{
		"totalReservas":      &graphql.Field{Type: graphql.Int},
		"reservasPendientes": &graphql.Field{Type: graphql.Int},
		"reservasAprobadas":  &graphql.Field{Type: graphql.Int},
		"reservasRechazadas": &graphql.Field{Type: graphql.Int},
		"reservasCanceladas": &graphql.Field{Type: graphql.Int},
		"espaciosActivos":    &graphql.Field{Type: graphql.Int},
		"usuariosActivos":    &graphql.Field{Type: graphql.Int},
	},
})

var groupedMetricType = graphql.NewObject(graphql.ObjectConfig{
	Name: "GroupedMetric",
	Fields: graphql.Fields{
		"label":    &graphql.Field{Type: graphql.String},
		"cantidad": &graphql.Field{Type: graphql.Int},
	},
})

var disponibilidadType = graphql.NewObject(graphql.ObjectConfig{
	Name: "Disponibilidad",
	Fields: graphql.Fields{
		"espacio_id":     &graphql.Field{Type: graphql.Int},
		"espacio_nombre": &graphql.Field{Type: graphql.String},
		"fecha":          &graphql.Field{Type: graphql.String},
		"dia_semana":     &graphql.Field{Type: graphql.String},
		"ocupados":       &graphql.Field{Type: graphql.NewList(reservaSlotType)},
		"libres":         &graphql.Field{Type: graphql.NewList(libresSlotType)},
	},
})

var reservaSlotType = graphql.NewObject(graphql.ObjectConfig{
	Name: "ReservaSlot",
	Fields: graphql.Fields{
		"id":          &graphql.Field{Type: graphql.Int},
		"estado":      &graphql.Field{Type: graphql.String},
		"hora_inicio": &graphql.Field{Type: graphql.String},
		"hora_fin":    &graphql.Field{Type: graphql.String},
		"titulo":      &graphql.Field{Type: graphql.String},
		"usuario_id":  &graphql.Field{Type: graphql.Int},
	},
})

var libresSlotType = graphql.NewObject(graphql.ObjectConfig{
	Name: "LibreSlot",
	Fields: graphql.Fields{
		"hora_inicio": &graphql.Field{Type: graphql.String},
		"hora_fin":    &graphql.Field{Type: graphql.String},
	},
})

// Fields
func reservasField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: graphql.NewList(reservaType),
		Args: graphql.FieldConfigArgument{
			"limit":          &graphql.ArgumentConfig{Type: graphql.Int, DefaultValue: 100},
			"offset":         &graphql.ArgumentConfig{Type: graphql.Int, DefaultValue: 0},
			"usuario_id":     &graphql.ArgumentConfig{Type: graphql.Int},
			"espacio_id":     &graphql.ArgumentConfig{Type: graphql.Int},
			"estado_id":      &graphql.ArgumentConfig{Type: graphql.Int},
			"tipo_evento_id": &graphql.ArgumentConfig{Type: graphql.Int},
			"fecha_desde":    &graphql.ArgumentConfig{Type: graphql.String},
			"fecha_hasta":    &graphql.ArgumentConfig{Type: graphql.String},
		},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil {
				return nil, fmt.Errorf("unauthorized")
			}
			filter := services.ReservationFilter{
				Limit:  p.Args["limit"].(int),
				Offset: p.Args["offset"].(int),
			}
			if v, ok := p.Args["usuario_id"]; ok {
				val := v.(int)
				filter.UsuarioID = &val
			} else if !authInfo.IsAdmin {
				filter.ForceUserID = &authInfo.UserID
			}
			if v, ok := p.Args["espacio_id"]; ok {
				val := v.(int)
				filter.EspacioID = &val
			}
			if v, ok := p.Args["estado_id"]; ok {
				val := v.(int)
				filter.EstadoID = &val
			}
			if v, ok := p.Args["tipo_evento_id"]; ok {
				val := v.(int)
				filter.TipoEventoID = &val
			}
			if v, ok := p.Args["fecha_desde"]; ok {
				val := v.(string)
				filter.FechaDesde = &val
			}
			if v, ok := p.Args["fecha_hasta"]; ok {
				val := v.(string)
				filter.FechaHasta = &val
			}
			return deps.Reservations.List(filter)
		},
	}
}

func reservaDetailField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: reservaType,
		Args: graphql.FieldConfigArgument{
			"id": &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.Int)},
		},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil {
				return nil, fmt.Errorf("unauthorized")
			}
			id := p.Args["id"].(int)
			return deps.Reservations.Detail(id, &authInfo.UserID, authInfo.IsAdmin)
		},
	}
}

func estadisticasField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: estadisticasType,
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil || !authInfo.IsAdmin {
				return nil, fmt.Errorf("admin only")
			}
			stats, err := deps.Stats.Totals()
			if err != nil {
				return nil, err
			}
			payload := map[string]interface{}{
				"totalReservas":      stats.TotalReservas,
				"reservasPendientes": stats.ReservasPendientes,
				"reservasAprobadas":  stats.ReservasAprobadas,
				"reservasRechazadas": stats.ReservasRechazadas,
				"reservasCanceladas": stats.ReservasCanceladas,
				"espaciosActivos":    stats.EspaciosActivos,
				"usuariosActivos":    stats.UsuariosActivos,
			}
			// Emitir webhook de stats_update si está configurado
			if deps.Webhook != nil {
				_ = deps.Webhook.SendStatsUpdate(payload)
			}
			return payload, nil
		},
	}
}

func espaciosTopField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: graphql.NewList(groupedMetricType),
		Args: graphql.FieldConfigArgument{
			"fecha_desde": &graphql.ArgumentConfig{Type: graphql.String},
			"fecha_hasta": &graphql.ArgumentConfig{Type: graphql.String},
			"limit":       &graphql.ArgumentConfig{Type: graphql.Int, DefaultValue: 10},
		},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil || !authInfo.IsAdmin {
				return nil, fmt.Errorf("admin only")
			}
			var fd, fh *string
			if v, ok := p.Args["fecha_desde"]; ok {
				val := v.(string)
				fd = &val
			}
			if v, ok := p.Args["fecha_hasta"]; ok {
				val := v.(string)
				fh = &val
			}
			limit := p.Args["limit"].(int)
			return deps.Stats.TopEspacios(fd, fh, limit)
		},
	}
}

func usuariosTopField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: graphql.NewList(groupedMetricType),
		Args: graphql.FieldConfigArgument{
			"fecha_desde": &graphql.ArgumentConfig{Type: graphql.String},
			"fecha_hasta": &graphql.ArgumentConfig{Type: graphql.String},
			"limit":       &graphql.ArgumentConfig{Type: graphql.Int, DefaultValue: 10},
		},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil || !authInfo.IsAdmin {
				return nil, fmt.Errorf("admin only")
			}
			var fd, fh *string
			if v, ok := p.Args["fecha_desde"]; ok {
				val := v.(string)
				fd = &val
			}
			if v, ok := p.Args["fecha_hasta"]; ok {
				val := v.(string)
				fh = &val
			}
			limit := p.Args["limit"].(int)
			return deps.Stats.TopUsuarios(fd, fh, limit)
		},
	}
}

func reservasPorEstadoField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: graphql.NewList(groupedMetricType),
		Args: graphql.FieldConfigArgument{
			"fecha_desde": &graphql.ArgumentConfig{Type: graphql.String},
			"fecha_hasta": &graphql.ArgumentConfig{Type: graphql.String},
		},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil || !authInfo.IsAdmin {
				return nil, fmt.Errorf("admin only")
			}
			var fd, fh *string
			if v, ok := p.Args["fecha_desde"]; ok {
				val := v.(string)
				fd = &val
			}
			if v, ok := p.Args["fecha_hasta"]; ok {
				val := v.(string)
				fh = &val
			}
			return deps.Stats.ReservasPorEstado(fd, fh)
		},
	}
}

func reservasPorTipoEventoField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: graphql.NewList(groupedMetricType),
		Args: graphql.FieldConfigArgument{
			"fecha_desde": &graphql.ArgumentConfig{Type: graphql.String},
			"fecha_hasta": &graphql.ArgumentConfig{Type: graphql.String},
		},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil || !authInfo.IsAdmin {
				return nil, fmt.Errorf("admin only")
			}
			var fd, fh *string
			if v, ok := p.Args["fecha_desde"]; ok {
				val := v.(string)
				fd = &val
			}
			if v, ok := p.Args["fecha_hasta"]; ok {
				val := v.(string)
				fh = &val
			}
			return deps.Stats.ReservasPorTipoEvento(fd, fh)
		},
	}
}

func disponibilidadField(deps Dependencies) *graphql.Field {
	return &graphql.Field{
		Type: disponibilidadType,
		Args: graphql.FieldConfigArgument{
			"espacio_id":         &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.Int)},
			"fecha":              &graphql.ArgumentConfig{Type: graphql.NewNonNull(graphql.String)},
			"incluir_pendientes": &graphql.ArgumentConfig{Type: graphql.Boolean, DefaultValue: true},
		},
		Resolve: func(p graphql.ResolveParams) (interface{}, error) {
			authInfo := auth.FromContext(p.Context)
			if authInfo == nil {
				return nil, fmt.Errorf("unauthorized")
			}
			espacioID := p.Args["espacio_id"].(int)
			fechaStr := p.Args["fecha"].(string)
			incluir := p.Args["incluir_pendientes"].(bool)
			fecha, err := time.Parse("2006-01-02", fechaStr)
			if err != nil {
				return nil, fmt.Errorf("invalid date format, use YYYY-MM-DD")
			}
			return deps.Availability.CalcAvailability(espacioID, fecha, incluir)
		},
	}
}
