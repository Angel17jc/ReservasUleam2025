import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { usuariosApi } from '@/api/rest/usuariosApi';
import { tiposUsuarioApi } from '@/api/rest/tiposUsuarioApi';

type Draft = { tipo_usuario_id: number; estado?: string };

export default function AdminUsuariosPage() {
  const queryClient = useQueryClient();
  const { data: usuariosData, isLoading } = useQuery({
    queryKey: ['admin-usuarios'],
    queryFn: () => usuariosApi.list(),
  });
  const { data: tiposData } = useQuery({
    queryKey: ['admin-tipos-usuario'],
    queryFn: () => tiposUsuarioApi.list(),
  });

  const usuarios = useMemo(() => usuariosData?.items ?? [], [usuariosData]);
  const tiposById = useMemo(() => {
    const map = new Map<number, string>();
    (tiposData ?? []).forEach((t) => map.set(t.id, t.nombre));
    return map;
  }, [tiposData]);

  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Draft }) => usuariosApi.update(id, payload),
    onSuccess: () => {
      setFeedback('Usuario actualizado correctamente.');
      setErrorMsg(null);
      setDrafts({});
      queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] });
    },
    onError: (err: any) => {
      const msg = err?.body?.detail || err?.message || 'No se pudo actualizar el usuario';
      setErrorMsg(String(msg));
      setFeedback(null);
    },
  });

  const getDraft = (id: string, tipoUsuarioId: number, estado?: string): Draft => {
    return drafts[id] ?? { tipo_usuario_id: tipoUsuarioId, estado };
  };

  const handleChange = (id: string, field: keyof Draft, value: string) => {
    setDrafts((prev) => ({
      ...prev,
      [id]: {
        ...(prev[id] ?? {}),
        [field]: field === 'tipo_usuario_id' ? Number(value) : value,
      },
    }));
  };

  const hasChanges = (user: any, draft: Draft) => {
    return draft.tipo_usuario_id !== user.tipoUsuarioId || (draft.estado ?? user.estado) !== user.estado;
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Gestión de Usuarios</h1>
        <p className="text-muted-foreground">
          Consulta y actualiza los roles y estados de los usuarios. Datos servidos desde /api/usuarios y /api/tipos-usuario.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Usuarios registrados</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {feedback && <p className="text-sm text-green-600">{feedback}</p>}
          {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}
          {isLoading && <p className="text-muted-foreground">Cargando usuarios...</p>}
          {!isLoading && usuarios.length === 0 && <p className="text-muted-foreground">No hay usuarios registrados.</p>}

          {usuarios.length > 0 && (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nombre</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {usuarios.map((user) => {
                    const draft = getDraft(user.id, user.tipoUsuarioId ?? 3, user.estado ?? 'activo');
                    const roleLabel = tiposById.get(draft.tipo_usuario_id) ?? 'N/D';
                    return (
                      <TableRow key={user.id}>
                        <TableCell>
                          <div className="font-semibold">{user.nombre}</div>
                          <div className="text-xs text-muted-foreground">ID {user.id}</div>
                        </TableCell>
                        <TableCell>
                          <div>{user.email}</div>
                          <Badge variant="outline">{roleLabel}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="space-y-1">
                            <Label className="sr-only">Rol</Label>
                            <Select
                              value={String(draft.tipo_usuario_id)}
                              onValueChange={(val) => handleChange(user.id, 'tipo_usuario_id', val)}
                            >
                              <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Selecciona rol" />
                              </SelectTrigger>
                              <SelectContent>
                                {(tiposData ?? []).map((tipo) => (
                                  <SelectItem key={tipo.id} value={String(tipo.id)}>
                                    {tipo.nombre}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Select
                            value={draft.estado ?? 'activo'}
                            onValueChange={(val) => handleChange(user.id, 'estado', val)}
                          >
                            <SelectTrigger className="w-[150px]">
                              <SelectValue placeholder="Estado" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="activo">Activo</SelectItem>
                              <SelectItem value="inactivo">Inactivo</SelectItem>
                              <SelectItem value="suspendido">Suspendido</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            disabled={!hasChanges(user, draft) || updateMutation.isPending}
                            onClick={() =>
                              updateMutation.mutate({
                                id: user.id,
                                payload: { tipo_usuario_id: draft.tipo_usuario_id, estado: draft.estado },
                              })
                            }
                          >
                            Guardar
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
