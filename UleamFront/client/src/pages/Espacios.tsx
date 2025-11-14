import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SpaceCard } from '@/components/SpaceCard';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, Filter, Building2 } from 'lucide-react';
import { espaciosApi } from '@/api/rest/espaciosApi';
import type { Espacio } from '@/api/rest/espaciosApi';
import { categoriasApi, type Categoria } from '@/api/rest/categoriasApi';
import { useLocation } from 'wouter';

const accent = { from: '#E63946', to: '#C1121F', icon: <Building2 className="text-white" size={20} /> };

export default function Espacios() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryId, setCategoryId] = useState<string>('all');
  const [, navigate] = useLocation();

  const { data, isLoading, error } = useQuery({
    queryKey: ['espacios', categoryId, searchTerm],
    queryFn: () =>
      espaciosApi.list({
        categoria_id: categoryId === 'all' ? undefined : Number(categoryId),
      }),
  });
  const { data: categoriasData } = useQuery({
    queryKey: ['categorias-espacio'],
    queryFn: () => categoriasApi.list(),
  });

  const spaces = useMemo<Espacio[]>(() => data?.items ?? [], [data]);
  const categorias = useMemo<Categoria[]>(() => categoriasData ?? [], [categoriasData]);
  const categoriaNombre = (id?: number) =>
    categorias.find((c) => c.id === id)?.nombre ?? `Categoría #${id ?? '?'}`;

  const handleReserve = (spaceId: string) => {
    navigate(`/app/reservas/nueva?espacio_id=${spaceId}`);
  };

  const filteredSpaces = useMemo(() => {
    return spaces.filter((space) => {
      const matchesSearch =
        space.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        space.codigo.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = categoryId === 'all' || String(space.categoriaId) === categoryId;
      return matchesSearch && matchesCategory;
    });
  }, [spaces, searchTerm, categoryId]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Explorar Espacios</h1>
        <p className="text-muted-foreground mt-2">
          Consumimos el servicio REST externo para listar espacios reales.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
          <Input
            placeholder="Buscar por nombre o código..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
            data-testid="input-search"
          />
        </div>
        <Select value={categoryId} onValueChange={setCategoryId}>
          <SelectTrigger className="w-full sm:w-[200px]" data-testid="select-category">
            <Filter size={16} className="mr-2" />
            <SelectValue placeholder="Categoría" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas las categorías</SelectItem>
            {categorias.map((cat) => (
              <SelectItem key={cat.id} value={String(cat.id)}>
                {cat.nombre} (#{cat.id})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="outline" data-testid="button-filter">
          <Filter size={16} className="mr-2" />
          Más Filtros
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {isLoading ? 'Cargando espacios...' : `Mostrando ${filteredSpaces.length} de ${spaces.length} espacios`}
        </p>
        {error && <p className="text-destructive text-sm">No se pudieron cargar los espacios.</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSpaces.map((space) => (
          <SpaceCard
            key={space.id}
            id={space.id}
            nombre={space.nombre}
            codigo={space.codigo}
            categoria={categoriaNombre(space.categoriaId)}
            capacidad={space.capacidadMaxima}
            accentColors={{ from: accent.from, to: accent.to }}
            bannerIcon={accent.icon}
            onReserve={handleReserve}
          />
        ))}
      </div>
    </div>
  );
}
