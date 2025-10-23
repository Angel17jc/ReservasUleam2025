interface Props {
  params: { section?: string };
}

export default function AdminPlaceholderPage({ params }: Props) {
  return (
    <div className="p-6 space-y-2">
      <h1 className="text-3xl font-bold text-foreground">Administración</h1>
      <p className="text-muted-foreground">
        Ruta <code>/admin/{params.section ?? ''}</code> pendiente de implementar. Conecta aquí las vistas que usen REST para CRUD,
        GraphQL para consultas agregadas y WebSocket para eventos en vivo.
      </p>
    </div>
  );
}
