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
import { Search, Filter, Building2, Target, BookOpen, Users } from 'lucide-react';
import { espaciosApi } from '@/api/rest/espaciosApi';
import type { Espacio } from '@/api/rest/espaciosApi';

const accentByCategory: Record<string, { from: string; to: string; icon: JSX.Element }> = {
  Auditorio: { from: '#E63946', to: '#C1121F', icon: <Building2 className="text-white" size={20} /> },
  Deportivo: { from: '#0EA5E9', to: '#0284C7', icon: <Target className="text-white" size={20} /> },
  Laboratorio: { from: '#10B981', to: '#0F766E', icon: <Users className="text-white" size={20} /> },
  Sala: { from: '#6366F1', to: '#4338CA', icon: <Building2 className="text-white" size={20} /> },
  Biblioteca: { from: '#F97316', to: '#EA580C', icon: <BookOpen className="text-white" size={20} /> },
};

export default function Espacios() {
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('all');

  const { data, isLoading, error } = useQuery({
    queryKey: ['espacios', category, searchTerm],
    queryFn: () => espaciosApi.list({ categoria: category === 'all' ? undefined : category, search: searchTerm }),
  });

  const spaces = useMemo<Espacio[]>(() => data?.items ?? [], [data]);

  const filteredSpaces = useMemo(() => {
    return spaces.filter((space) => {
      const matchesSearch =
        space.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        space.codigo.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = category === 'all' || space.categoria === category;
      return matchesSearch && matchesCategory;
    });
  }, [spaces, searchTerm, category]);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Explorar Espacios</h1>
        <p className="text-muted-foreground mt-2">
          Consumimos el servicio REST externo (mock mientras no haya endpoint real).
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
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="w-full sm:w-[200px]" data-testid="select-category">
            <Filter size={16} className="mr-2" />
            <SelectValue placeholder="Categoría" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas las categorías</SelectItem>
            <SelectItem value="Auditorio">Auditorio</SelectItem>
            <SelectItem value="Laboratorio">Laboratorio</SelectItem>
            <SelectItem value="Sala">Sala</SelectItem>
            <SelectItem value="Deportivo">Deportivo</SelectItem>
            <SelectItem value="Biblioteca">Biblioteca</SelectItem>
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
        {filteredSpaces.map((space) => {
          const accent = accentByCategory[space.categoria] ?? accentByCategory.Auditorio;
          return (
            <SpaceCard
              key={space.id}
              {...space}
              accentColors={{ from: accent.from, to: accent.to }}
              bannerIcon={accent.icon}
            />
          );
        })}
      </div>
    </div>
  );
}
