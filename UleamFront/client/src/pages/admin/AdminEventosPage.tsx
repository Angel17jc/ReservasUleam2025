import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tiposEventoApi, type TipoEvento } from '@/api/rest/tiposEventoApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Edit3, Save, Trash2, XCircle } from 'lucide-react';

type TipoEventoInput = {
  nombre: string;
  descripcion?: string;
  color_hex?: string;
};

export default function AdminEventosPage() {
  const queryClient = useQueryClient();
  const { data: tiposData, isLoading } = useQuery({
    queryKey: ['admin-tipos-evento'],
    queryFn: () => tiposEventoApi.list(),
  });
  const tipos = useMemo<TipoEvento[]>(() => tiposData ?? [], [tiposData]);

  const [form, setForm] = useState<TipoEventoInput>({
    nombre: '',
    descripcion: '',
    color_hex: '#3B82F6',
  });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<TipoEventoInput | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: TipoEventoInput) => tiposEventoApi.create(payload as any),
    onSuccess: () => {
      setSuccessMsg('Tipo de evento creado.');
      setErrorMsg(null);
      setForm({ nombre: '', descripcion: '', color_hex: '#3B82F6' });
      queryClient.invalidateQueries({ queryKey: ['admin-tipos-evento'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo crear el tipo de evento';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<TipoEventoInput> }) =>
      tiposEventoApi.update(id, payload as any),
    onSuccess: () => {
      setSuccessMsg('Tipo de evento actualizado.');
      setErrorMsg(null);
      setEditingId(null);
      setEditForm(null);
      queryClient.invalidateQueries({ queryKey: ['admin-tipos-evento'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo actualizar el tipo de evento';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => tiposEventoApi.remove(id),
    onSuccess: () => {
      setSuccessMsg('Tipo de evento eliminado.');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['admin-tipos-evento'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo eliminar el tipo de evento';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Gestión de Tipos de Evento</h1>
        <p className="text-muted-foreground">Lista y CRUD completo de tipos de evento.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Tipos de evento existentes</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading && <p className="text-muted-foreground">Cargando tipos de evento...</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tipos.map((te) => (
                <Card key={te.id} className="border border-muted">
                  <CardContent className="p-4 space-y-2">
                    {editingId === te.id ? (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold">Editando: {te.nombre}</h3>
                          <Badge
                            style={{ backgroundColor: editForm?.color_hex ?? te.color_hex ?? '#ddd', color: '#000' }}
                          >
                            {editForm?.color_hex ?? te.color_hex}
                          </Badge>
                        </div>
                        <Label>Nombre</Label>
                        <Input
                          value={editForm?.nombre ?? ''}
                          onChange={(e) => setEditForm((f) => ({ ...(f ?? {}), nombre: e.target.value } as TipoEventoInput))}
                        />
                        <Label>Descripción</Label>
                        <Input
                          value={editForm?.descripcion ?? ''}
                          onChange={(e) =>
                            setEditForm((f) => ({ ...(f ?? {}), descripcion: e.target.value } as TipoEventoInput))
                          }
                        />
                        <Label>Color (hex)</Label>
                        <Input
                          value={editForm?.color_hex ?? '#3B82F6'}
                          onChange={(e) => setEditForm((f) => ({ ...(f ?? {}), color_hex: e.target.value } as TipoEventoInput))}
                          placeholder="#3B82F6"
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => editForm && updateMutation.mutate({ id: te.id, payload: editForm })}
                            disabled={updateMutation.isPending}
                          >
                            <Save className="w-4 h-4 mr-1" /> Guardar
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingId(null);
                              setEditForm(null);
                            }}
                          >
                            <XCircle className="w-4 h-4 mr-1" /> Cancelar
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold">{te.nombre}</h3>
                          <Badge style={{ backgroundColor: te.color_hex ?? '#ddd', color: '#000' }}>
                            {te.color_hex ?? '#ddd'}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{te.descripcion ?? ''}</p>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingId(te.id);
                              setEditForm({
                                nombre: te.nombre,
                                descripcion: te.descripcion ?? '',
                                color_hex: te.color_hex ?? '#3B82F6',
                              });
                            }}
                          >
                            <Edit3 className="w-4 h-4 mr-1" /> Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => deleteMutation.mutate(te.id)}
                            disabled={deleteMutation.isPending}
                          >
                            <Trash2 className="w-4 h-4 mr-1" /> Borrar
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              {tipos.length === 0 && !isLoading && <p className="text-muted-foreground">No hay tipos de evento registrados.</p>}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Crear nuevo tipo de evento</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>Nombre</Label>
              <Input
                value={form.nombre}
                onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                placeholder="Nombre del tipo de evento"
              />
            </div>
            <div>
              <Label>Descripción</Label>
              <Input
                value={form.descripcion ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))}
                placeholder="Descripción (opcional)"
              />
            </div>
            <div>
              <Label>Color (hex)</Label>
              <Input
                value={form.color_hex ?? '#3B82F6'}
                onChange={(e) => setForm((f) => ({ ...f, color_hex: e.target.value }))}
                placeholder="#3B82F6"
              />
            </div>
            <Button onClick={() => createMutation.mutate(form)} disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creando...' : 'Crear tipo de evento'}
            </Button>
            {successMsg && <p className="text-green-600 text-sm">{successMsg}</p>}
            {errorMsg && <p className="text-destructive text-sm">{errorMsg}</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
