import { useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { reservasApi } from '@/api/rest/reservasApi';
import { espaciosApi } from '@/api/rest/espaciosApi';
import { tiposEventoApi } from '@/api/rest/tiposEventoApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function NuevaReservaPage() {
  const [espacioId, setEspacioId] = useState<string>('');
  const [fecha, setFecha] = useState(() => new Date().toISOString().slice(0, 10));
  const [horaInicio, setHoraInicio] = useState('09:00');
  const [horaFin, setHoraFin] = useState('11:00');
  const [titulo, setTitulo] = useState('Reserva desde frontend');
  const [descripcion, setDescripcion] = useState('Prueba de integración REST');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [tipoEventoId, setTipoEventoId] = useState<string>('');

  const { data: espaciosData } = useQuery({
    queryKey: ['espacios-para-reservar'],
    queryFn: () => espaciosApi.list(),
  });
  const { data: tiposEventoData } = useQuery({
    queryKey: ['tipos-evento'],
    queryFn: () => tiposEventoApi.list(),
  });

  const espacios = useMemo(() => espaciosData?.items ?? [], [espaciosData]);
  const defaultEspacioId = espacios[0]?.id ? String(espacios[0].id) : '';
  const tiposEvento = useMemo(() => tiposEventoData ?? [], [tiposEventoData]);
  const defaultTipoEventoId = tiposEvento[0]?.id ? String(tiposEvento[0].id) : '';

  const { mutateAsync, isPending, isSuccess } = useMutation({
    mutationFn: () =>
      reservasApi.create({
        espacio_id: Number(espacioId || defaultEspacioId),
        tipo_evento_id: Number(tipoEventoId || defaultTipoEventoId) || undefined,
        fecha,
        hora_inicio: horaInicio,
        hora_fin: horaFin,
        titulo,
        descripcion,
      }),
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo crear la reserva';
      setErrorMsg(String(msg));
    },
    onSuccess: () => setErrorMsg(null),
  });

  return (
    <div className="p-6 space-y-4 max-w-xl">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Nueva Reserva</h1>
        <p className="text-muted-foreground">
          Envía la solicitud al servicio REST (Python). Selecciona un espacio válido para evitar errores 404.
        </p>
      </div>

      <div className="grid gap-3">
        <div>
          <Label>Espacio</Label>
          <Select value={espacioId || defaultEspacioId} onValueChange={setEspacioId}>
            <SelectTrigger>
              <SelectValue placeholder="Selecciona un espacio" />
            </SelectTrigger>
            <SelectContent>
              {espacios.map((esp) => (
                <SelectItem key={esp.id} value={String(esp.id)}>
                  #{esp.id} — {esp.nombre} (cap. {esp.capacidadMaxima})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Fecha</Label>
          <Input value={fecha} onChange={(e) => setFecha(e.target.value)} placeholder="Fecha" type="date" />
        </div>
        <div>
          <Label>Tipo de evento</Label>
          <Select value={tipoEventoId || defaultTipoEventoId} onValueChange={setTipoEventoId}>
            <SelectTrigger>
              <SelectValue placeholder="Selecciona un tipo de evento" />
            </SelectTrigger>
            <SelectContent>
              {tiposEvento.map((te) => (
                <SelectItem key={te.id} value={String(te.id)}>
                  {te.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div>
          <Label>Título</Label>
          <Input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título de la reserva" />
        </div>
        <div>
          <Label>Descripción</Label>
          <Input value={descripcion} onChange={(e) => setDescripcion(e.target.value)} placeholder="Descripción" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label>Hora inicio</Label>
            <Select value={horaInicio} onValueChange={setHoraInicio}>
              <SelectTrigger>
                <SelectValue placeholder="Selecciona hora de inicio" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="09:00">09:00</SelectItem>
                <SelectItem value="11:00">11:00</SelectItem>
                <SelectItem value="14:00">14:00</SelectItem>
                <SelectItem value="16:00">16:00</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Hora fin</Label>
            <Select value={horaFin} onValueChange={setHoraFin}>
              <SelectTrigger>
                <SelectValue placeholder="Selecciona hora de fin" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="11:00">11:00</SelectItem>
                <SelectItem value="13:00">13:00</SelectItem>
                <SelectItem value="16:00">16:00</SelectItem>
                <SelectItem value="18:00">18:00</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button onClick={() => mutateAsync()} disabled={isPending} data-testid="button-create-reservation">
          {isPending ? 'Enviando...' : 'Crear Reserva'}
        </Button>
        {errorMsg && <p className="text-destructive text-sm">{errorMsg}</p>}
        {isSuccess && !errorMsg && <p className="text-green-600">Reserva enviada al servicio REST.</p>}
      </div>
    </div>
  );
}
