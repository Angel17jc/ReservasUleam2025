import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { reservasApi } from '@/api/rest/reservasApi';
import { usuariosApi } from '@/api/rest/usuariosApi';
import { tiposUsuarioApi } from '@/api/rest/tiposUsuarioApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar, Clock, User, Building2 } from 'lucide-react';

const ESTADO_PENDIENTE = 1;
const ESTADO_APROBADA = 2;
const ESTADO_RECHAZADA = 3;

export default function AdminAprobacionesPage() {
  const queryClient = useQueryClient();

  const { data: reservasData } = useQuery({
    queryKey: ['admin-reservas-pendientes'],
    queryFn: () => reservasApi.list({ estado_id: ESTADO_PENDIENTE }),
  });
  const { data: usuariosData } = useQuery({
    queryKey: ['admin-reservas-usuarios'],
    queryFn: () => usuariosApi.list(),
  });
  const { data: tiposUsuarioData } = useQuery({
    queryKey: ['admin-reservas-tipos-usuario'],
    queryFn: () => tiposUsuarioApi.list(),
  });

  const tipoPrioridad = useMemo(() => {
    const map: Record<number, number> = {};
    (tiposUsuarioData ?? []).forEach((t) => (map[t.id] = t.nivel_prioridad));
    return map;
  }, [tiposUsuarioData]);

  const usuariosMap = useMemo(() => {
    const map: Record<string, { nombre: string; prioridad: number }> = {};
    (usuariosData?.items ?? []).forEach((u) => {
      map[String(u.id)] = {
        nombre: `${u.nombre} ${u.apellido ?? ''}`.trim(),
        prioridad: tipoPrioridad[u.tipoUsuarioId ?? 99] ?? 99,
      };
    });
    return map;
  }, [usuariosData, tipoPrioridad]);

  const pendientes = useMemo(() => {
    const items = reservasData?.items ?? [];
    return items
      .slice()
      .sort((a, b) => {
        // fecha asc
        if (a.fecha !== b.fecha) return a.fecha.localeCompare(b.fecha);
        // misma fecha: prioridad menor primero
        const pa = usuariosMap[String(a.usuarioId)]?.prioridad ?? 99;
        const pb = usuariosMap[String(b.usuarioId)]?.prioridad ?? 99;
        return pa - pb;
      });
  }, [reservasData, usuariosMap]);

  const patchEstado = useMutation({
    mutationFn: ({ id, estado_id }: { id: string; estado_id: number }) =>
      reservasApi.updateEstado(id, estado_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-reservas-pendientes'] });
    },
  });

  const handleDecision = (id: string, estado_id: number) => {
    patchEstado.mutate({ id, estado_id });
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Aprobar Reservas</h1>
        <p className="text-muted-foreground">
          Revisa las reservas pendientes y responde según prioridad (Admin &gt; Profesor &gt; Estudiante).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {pendientes.map((res) => {
          const usuario = usuariosMap[String(res.usuarioId)];
          return (
            <Card key={res.id} className="border">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{res.titulo ?? res.tipoEvento ?? 'Reserva'}</span>
                  <Badge>Prioridad {usuario?.prioridad ?? '—'}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <User size={14} /> {usuario?.nombre ?? `Usuario #${res.usuarioId}`}
                </div>
                <div className="flex items-center gap-2">
                  <Building2 size={14} /> Espacio #{res.espacioId}
                </div>
                <div className="flex items-center gap-2">
                  <Calendar size={14} /> {res.fecha}
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={14} /> {res.horaInicio} - {res.horaFin}
                </div>
                <div className="flex gap-2 pt-2">
                  <Button
                    size="sm"
                    className="bg-emerald-600 hover:bg-emerald-700"
                    onClick={() => handleDecision(res.id, ESTADO_APROBADA)}
                    disabled={patchEstado.isPending}
                  >
                    Aprobar
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDecision(res.id, ESTADO_RECHAZADA)}
                    disabled={patchEstado.isPending}
                  >
                    Rechazar
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {pendientes.length === 0 && (
          <p className="text-muted-foreground">No hay reservas pendientes de aprobación.</p>
        )}
      </div>
    </div>
  );
}
