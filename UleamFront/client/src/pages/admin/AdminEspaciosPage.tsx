import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { espaciosApi, type EspacioInput } from '@/api/rest/espaciosApi';
import { categoriasApi } from '@/api/rest/categoriasApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Edit3, Save, Trash2, XCircle } from 'lucide-react';

export default function AdminEspaciosPage() {
  const queryClient = useQueryClient();
  const { data: espaciosData, isLoading } = useQuery({
    queryKey: ['admin-espacios'],
    queryFn: () => espaciosApi.list(),
  });
  const { data: categoriasData } = useQuery({
    queryKey: ['admin-categorias'],
    queryFn: () => categoriasApi.list(),
  });

  const categorias = useMemo(() => categoriasData ?? [], [categoriasData]);
  const espacios = useMemo(() => espaciosData?.items ?? [], [espaciosData]);

  const [form, setForm] = useState<EspacioInput>({
    codigo: '',
    nombre: '',
    categoria_id: categorias[0]?.id ?? 0,
    capacidad_maxima: 0,
    imagen_url: '',
    estado: 'activo',
  });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EspacioInput | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: EspacioInput) => espaciosApi.create(payload),
    onSuccess: () => {
      setSuccessMsg('Espacio creado correctamente.');
      setErrorMsg(null);
      setForm({
        codigo: '',
        nombre: '',
        categoria_id: categorias[0]?.id ?? 0,
        capacidad_maxima: 0,
        imagen_url: '',
        estado: 'activo',
      });
      queryClient.invalidateQueries({ queryKey: ['admin-espacios'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo crear el espacio';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<EspacioInput> }) =>
      espaciosApi.update(id, payload),
    onSuccess: () => {
      setSuccessMsg('Espacio actualizado.');
      setErrorMsg(null);
      setEditingId(null);
      setEditForm(null);
      queryClient.invalidateQueries({ queryKey: ['admin-espacios'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo actualizar el espacio';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => espaciosApi.remove(id),
    onSuccess: () => {
      setSuccessMsg('Espacio eliminado.');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['admin-espacios'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo eliminar el espacio';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Gestión de Espacios</h1>
        <p className="text-muted-foreground">Lista de espacios y creación de nuevos registros.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Espacios existentes</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading && <p className="text-muted-foreground">Cargando espacios...</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {espacios.map((esp) => (
                <Card key={esp.id} className="border border-muted">
                  <CardContent className="p-4 space-y-2">
                    {editingId === esp.id ? (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold">Editando: {esp.nombre}</h3>
                          <Badge>{editForm?.estado ?? esp.estado}</Badge>
                        </div>
                        <Label>Código</Label>
                        <Input
                          value={editForm?.codigo ?? ''}
                          onChange={(e) => setEditForm((f) => ({ ...(f ?? {}), codigo: e.target.value } as EspacioInput))}
                        />
                        <Label>Nombre</Label>
                        <Input
                          value={editForm?.nombre ?? ''}
                          onChange={(e) => setEditForm((f) => ({ ...(f ?? {}), nombre: e.target.value } as EspacioInput))}
                        />
                        <Label>Categoría</Label>
                        <Select
                          value={String(editForm?.categoria_id ?? esp.categoriaId ?? '')}
                          onValueChange={(v) =>
                            setEditForm((f) => ({ ...(f ?? {}), categoria_id: Number(v) } as EspacioInput))
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Categoría" />
                          </SelectTrigger>
                          <SelectContent>
                            {categorias.map((cat) => (
                              <SelectItem key={cat.id} value={String(cat.id)}>
                                {cat.nombre}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Label>Capacidad</Label>
                        <Input
                          type="number"
                          value={editForm?.capacidad_maxima ?? 0}
                          onChange={(e) =>
                            setEditForm((f) => ({ ...(f ?? {}), capacidad_maxima: Number(e.target.value) } as EspacioInput))
                          }
                        />
                        <Label>Imagen URL</Label>
                        <Input
                          value={editForm?.imagen_url ?? ''}
                          onChange={(e) => setEditForm((f) => ({ ...(f ?? {}), imagen_url: e.target.value } as EspacioInput))}
                        />
                        <Label>Estado</Label>
                        <Select
                          value={editForm?.estado ?? esp.estado ?? 'activo'}
                          onValueChange={(v) => setEditForm((f) => ({ ...(f ?? {}), estado: v } as EspacioInput))}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Estado" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="activo">Activo</SelectItem>
                            <SelectItem value="inactivo">Inactivo</SelectItem>
                          </SelectContent>
                        </Select>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => editForm && updateMutation.mutate({ id: esp.id, payload: editForm })}
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
                          <h3 className="font-semibold">{esp.nombre}</h3>
                          <Badge>{esp.estado}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">Código: {esp.codigo}</p>
                        <p className="text-sm text-muted-foreground">
                          Categoría: {categorias.find((c) => c.id === esp.categoriaId)?.nombre ?? esp.categoriaId}
                        </p>
                        <p className="text-sm text-muted-foreground">Capacidad: {esp.capacidadMaxima}</p>
                        {esp.imagenUrl && <p className="text-xs text-muted-foreground break-all">Imagen: {esp.imagenUrl}</p>}
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingId(esp.id);
                              setEditForm({
                                codigo: esp.codigo,
                                nombre: esp.nombre,
                                categoria_id: esp.categoriaId,
                                capacidad_maxima: esp.capacidadMaxima,
                                imagen_url: esp.imagenUrl ?? '',
                                estado: esp.estado ?? 'activo',
                              });
                            }}
                          >
                            <Edit3 className="w-4 h-4 mr-1" /> Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => deleteMutation.mutate(esp.id)}
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
              {espacios.length === 0 && !isLoading && (
                <p className="text-muted-foreground">No hay espacios registrados.</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Crear nuevo espacio</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>Código</Label>
              <Input
                value={form.codigo}
                onChange={(e) => setForm((f) => ({ ...f, codigo: e.target.value }))}
                placeholder="Código único"
              />
            </div>
            <div>
              <Label>Nombre</Label>
              <Input
                value={form.nombre}
                onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                placeholder="Nombre del espacio"
              />
            </div>
            <div>
              <Label>Categoría</Label>
              <Select
                value={String(form.categoria_id ?? '')}
                onValueChange={(v) => setForm((f) => ({ ...f, categoria_id: Number(v) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecciona categoría" />
                </SelectTrigger>
                <SelectContent>
                  {categorias.map((cat) => (
                    <SelectItem key={cat.id} value={String(cat.id)}>
                      {cat.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Capacidad máxima</Label>
              <Input
                type="number"
                value={form.capacidad_maxima}
                onChange={(e) => setForm((f) => ({ ...f, capacidad_maxima: Number(e.target.value) }))}
                placeholder="Capacidad numérica"
              />
            </div>
            <div>
              <Label>URL de imagen (opcional)</Label>
              <Input
                value={form.imagen_url ?? ''}
                onChange={(e) => setForm((f) => ({ ...f, imagen_url: e.target.value }))}
                placeholder="http://..."
              />
            </div>
            <div>
              <Label>Estado</Label>
              <Select
                value={form.estado ?? 'activo'}
                onValueChange={(v) => setForm((f) => ({ ...f, estado: v } as EspacioInput))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Estado" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="activo">Activo</SelectItem>
                  <SelectItem value="inactivo">Inactivo</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => createMutation.mutate(form)} disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creando...' : 'Crear espacio'}
            </Button>
            {successMsg && <p className="text-green-600 text-sm">{successMsg}</p>}
            {errorMsg && <p className="text-destructive text-sm">{errorMsg}</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
