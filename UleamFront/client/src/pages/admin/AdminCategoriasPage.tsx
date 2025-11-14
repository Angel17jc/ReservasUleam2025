import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { categoriasApi, type Categoria } from '@/api/rest/categoriasApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Edit3, Save, Trash2, XCircle } from 'lucide-react';

type CategoriaInput = {
  nombre: string;
  descripcion?: string;
  capacidad_maxima?: number | null;
};

export default function AdminCategoriasPage() {
  const queryClient = useQueryClient();
  const { data: categoriasData, isLoading } = useQuery({
    queryKey: ['admin-categorias'],
    queryFn: () => categoriasApi.list(),
  });
  const categorias = useMemo<Categoria[]>(() => categoriasData ?? [], [categoriasData]);

  const [form, setForm] = useState<CategoriaInput>({
    nombre: '',
    descripcion: '',
    capacidad_maxima: undefined,
  });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<CategoriaInput | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: CategoriaInput) => categoriasApi.create(payload),
    onSuccess: () => {
      setSuccessMsg('Categoría creada.');
      setErrorMsg(null);
      setForm({ nombre: '', descripcion: '', capacidad_maxima: undefined });
      queryClient.invalidateQueries({ queryKey: ['admin-categorias'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo crear la categoría';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<CategoriaInput> }) =>
      categoriasApi.update(id, payload),
    onSuccess: () => {
      setSuccessMsg('Categoría actualizada.');
      setErrorMsg(null);
      setEditingId(null);
      setEditForm(null);
      queryClient.invalidateQueries({ queryKey: ['admin-categorias'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo actualizar la categoría';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => categoriasApi.remove(id),
    onSuccess: () => {
      setSuccessMsg('Categoría eliminada.');
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ['admin-categorias'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo eliminar la categoría';
      setErrorMsg(String(msg));
      setSuccessMsg(null);
    },
  });

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Gestión de Categorías</h1>
        <p className="text-muted-foreground">Lista y CRUD completo de categorías de espacio.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Categorías existentes</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading && <p className="text-muted-foreground">Cargando categorías...</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {categorias.map((cat) => (
                <Card key={cat.id} className="border border-muted">
                  <CardContent className="p-4 space-y-2">
                    {editingId === cat.id ? (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold">Editando: {cat.nombre}</h3>
                          <Badge>Solo admin</Badge>
                        </div>
                        <Label>Nombre</Label>
                        <Input
                          value={editForm?.nombre ?? ''}
                          onChange={(e) => setEditForm((f) => ({ ...(f ?? {}), nombre: e.target.value } as CategoriaInput))}
                        />
                        <Label>Descripción</Label>
                        <Input
                          value={editForm?.descripcion ?? ''}
                          onChange={(e) =>
                            setEditForm((f) => ({ ...(f ?? {}), descripcion: e.target.value } as CategoriaInput))
                          }
                        />
                        <Label>Capacidad máxima (opcional)</Label>
                        <Input
                          type="number"
                          value={editForm?.capacidad_maxima ?? ''}
                          onChange={(e) =>
                            setEditForm((f) => ({
                              ...(f ?? {}),
                              capacidad_maxima: e.target.value ? Number(e.target.value) : undefined,
                            }))
                          }
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => editForm && updateMutation.mutate({ id: cat.id, payload: editForm })}
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
                          <h3 className="font-semibold">{cat.nombre}</h3>
                          <Badge>Solo admin</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{cat.descripcion ?? ''}</p>
                        {cat.capacidad_maxima && (
                          <p className="text-sm text-muted-foreground">Capacidad máxima: {cat.capacidad_maxima}</p>
                        )}
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingId(cat.id);
                              setEditForm({
                                nombre: cat.nombre,
                                descripcion: cat.descripcion ?? '',
                                capacidad_maxima: cat.capacidad_maxima ?? undefined,
                              });
                            }}
                          >
                            <Edit3 className="w-4 h-4 mr-1" /> Editar
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => deleteMutation.mutate(cat.id)}
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
              {categorias.length === 0 && !isLoading && (
                <p className="text-muted-foreground">No hay categorías registradas.</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Crear nueva categoría</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>Nombre</Label>
              <Input
                value={form.nombre}
                onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                placeholder="Nombre de categoría"
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
              <Label>Capacidad máxima (opcional)</Label>
              <Input
                type="number"
                value={form.capacidad_maxima ?? ''}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    capacidad_maxima: e.target.value ? Number(e.target.value) : undefined,
                  }))
                }
                placeholder="Ej. 200"
              />
            </div>
            <Button onClick={() => createMutation.mutate(form)} disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creando...' : 'Crear categoría'}
            </Button>
            {successMsg && <p className="text-green-600 text-sm">{successMsg}</p>}
            {errorMsg && <p className="text-destructive text-sm">{errorMsg}</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
