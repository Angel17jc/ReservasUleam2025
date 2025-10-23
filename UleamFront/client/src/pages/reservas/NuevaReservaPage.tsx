import { useMutation } from '@tanstack/react-query';
import { reservasApi } from '@/api/rest/reservasApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useState } from 'react';

export default function NuevaReservaPage() {
  const [espacioId, setEspacioId] = useState('1');
  const [fecha, setFecha] = useState('2025-11-15');
  const [horaInicio, setHoraInicio] = useState('10:00');
  const [horaFin, setHoraFin] = useState('12:00');

  const { mutateAsync, isPending, isSuccess } = useMutation({
    mutationFn: () =>
      reservasApi.create({
        espacioId,
        usuarioId: 'mock-user',
        fecha,
        horaInicio,
        horaFin,
        tipoEvento: 'Demo',
        descripcion: 'Reserva desde frontend',
      }),
  });

  return (
    <div className="p-6 space-y-4 max-w-xl">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Nueva Reserva</h1>
        <p className="text-muted-foreground">
          Envía la solicitud al servicio REST externo (Python). Campos son placeholders que debes reemplazar cuando el
          backend esté disponible.
        </p>
      </div>

      <div className="grid gap-3">
        <Input value={espacioId} onChange={(e) => setEspacioId(e.target.value)} placeholder="ID de espacio" />
        <Input value={fecha} onChange={(e) => setFecha(e.target.value)} placeholder="Fecha" type="date" />
        <div className="grid grid-cols-2 gap-2">
          <Input value={horaInicio} onChange={(e) => setHoraInicio(e.target.value)} placeholder="Hora inicio" type="time" />
          <Input value={horaFin} onChange={(e) => setHoraFin(e.target.value)} placeholder="Hora fin" type="time" />
        </div>
        <Button onClick={() => mutateAsync()} disabled={isPending} data-testid="button-create-reservation">
          {isPending ? 'Enviando...' : 'Crear Reserva'}
        </Button>
        {isSuccess && <p className="text-green-600">Reserva enviada (mock si no hay backend configurado).</p>}
      </div>
    </div>
  );
}
