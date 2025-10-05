export interface SocketEvent {
    event: string;
    data: any;
}

export interface SubscriptionRequest {
    channels: string[];
}

export interface NotificationPayload {
    id: number;
    titulo: string;
    mensaje: string;
    usuario_id: number;
    reserva_id?: number;
    espacio_id?: number;
    metadata?: any;
}

export interface ReservaCreatedPayload {
    reserva_id: number;
    espacio_id: number;
    espacio_nombre: string;
    usuario: string;
    usuario_id: number;
    fecha: string;
    hora_inicio: string;
    hora_fin: string;
    estado: string;
}

export interface ReservaUpdatedPayload {
    reserva_id: number;
    nuevo_estado: string;
    espacio_id: number;
    fecha: string;
    motivo?: string;
    usuario_id?: number;
}

export interface StatsUpdatePayload {
    reservas_pendientes: number;
    reservas_hoy: number;
    espacios_ocupados: number;
    espacios_disponibles: number;
    usuarios_online?: number;
}

export interface DisponibilidadPayload {
    espacio_id: number;
    espacio_nombre: string;
    dia_semana: string;
    horarios: {
        hora_inicio: string;
        hora_fin: string;
        activo: boolean;
    }[];
}

export interface RecordatorioPayload {
    reserva_id: number;
    usuario_id: number;
    titulo: string;
    espacio: string;
    hora_inicio: string;
    minutos_restantes: number;
}

export interface ConnectedUser {
    id: number;
    email: string;
    nombre: string;
    apellido: string;
    tipoUsuarioId: number;
    nivelPrioridad: number;
    role: 'admin' | 'user';
    avatarUrl?: string;
}

export interface PresenceSnapshot {
    online_users: number;
    active_connections: number;
    tracked_channels: number;
}

export interface JwtPayload {
    sub: number | string;
    exp?: number;
    iat?: number;
    [key: string]: any;
}
