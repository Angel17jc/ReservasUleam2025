# 🧪 Testing Guide - UleamFront

## 📋 Índice
- [Setup](#setup)
- [Ejecutar Tests](#ejecutar-tests)
- [Estructura de Tests](#estructura-de-tests)
- [Ejemplos](#ejemplos)
- [Best Practices](#best-practices)
- [Coverage](#coverage)

---

## Setup

### Instalación (ya hecho)
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @vitest/ui @vitest/coverage-v8
```

### Configuración
- `vitest.config.ts` - Configuración principal
- `client/src/test/setup.ts` - Setup global (mocks, matchers)

---

## Ejecutar Tests

```bash
# Modo watch (recomendado para desarrollo)
npm run test

# UI interactiva
npm run test:ui

# Una vez (para CI/CD)
npm run test:run

# Con coverage
npm run test:coverage
```

### UI Interactiva
```bash
npm run test:ui
```
Abre interfaz web en `http://localhost:51204/__vitest__/`

---

## Estructura de Tests

```
client/src/
├── api/
│   └── rest/
│       ├── authApi.ts
│       └── __tests__/
│           └── authApi.test.ts        ✅
├── hooks/
│   ├── useWebSocketStatus.ts
│   └── __tests__/
│       └── useWebSocketStatus.test.ts ✅
├── components/
│   ├── ErrorBoundary.tsx
│   └── __tests__/
│       └── ErrorBoundary.test.tsx     ✅
└── config/
    ├── env.validated.ts
    └── __tests__/
        └── env.validated.test.ts      ✅
```

---

## Ejemplos

### Test de función/API

```typescript
// api/rest/__tests__/reservasApi.test.ts
import { describe, it, expect, vi } from 'vitest';
import { reservasApi } from '../reservasApi';

describe('reservasApi', () => {
  it('debe obtener lista de reservas', async () => {
    // Arrange - Mock de fetch
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          { id: 1, titulo: 'Reunión' },
          { id: 2, titulo: 'Clase' },
        ]),
      } as Response)
    );

    // Act - Ejecutar función
    const reservas = await reservasApi.getReservas();

    // Assert - Verificar resultado
    expect(reservas).toHaveLength(2);
    expect(reservas[0].titulo).toBe('Reunión');
  });

  it('debe manejar errores correctamente', async () => {
    // Arrange - Mock de error
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      } as Response)
    );

    // Act & Assert
    await expect(reservasApi.getReservas()).rejects.toThrow();
  });
});
```

### Test de Hook

```typescript
// hooks/__tests__/useMiHook.test.ts
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useMiHook } from '../useMiHook';

describe('useMiHook', () => {
  it('debe retornar valor inicial', () => {
    const { result } = renderHook(() => useMiHook());
    
    expect(result.current.valor).toBe(0);
    expect(result.current.loading).toBe(false);
  });

  it('debe actualizar valor al llamar setter', () => {
    const { result } = renderHook(() => useMiHook());
    
    // Act
    result.current.setValor(10);
    
    // Assert
    expect(result.current.valor).toBe(10);
  });

  it('debe manejar operaciones async', async () => {
    const { result } = renderHook(() => useMiHook());
    
    // Act
    result.current.fetchData();
    
    // Assert - Esperar a que termine
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeDefined();
    });
  });
});
```

### Test de Componente

```typescript
// components/__tests__/MiComponente.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import MiComponente from '../MiComponente';

describe('MiComponente', () => {
  it('debe renderizar correctamente', () => {
    render(<MiComponente titulo="Hola" />);
    
    expect(screen.getByText('Hola')).toBeInTheDocument();
  });

  it('debe responder a clicks', () => {
    const handleClick = vi.fn();
    render(<MiComponente onClick={handleClick} />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('debe mostrar loading state', () => {
    render(<MiComponente loading={true} />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

### Test con Contexto (AuthContext)

```typescript
// components/__tests__/ProtectedComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '@/contexts/AuthContext';
import ProtectedComponent from '../ProtectedComponent';

// Helper para wrappear con provider
function renderWithAuth(ui: React.ReactElement, { user = null } = {}) {
  // Mock del AuthContext
  const mockAuthContext = {
    user,
    isAuthenticated: user !== null,
    isAdmin: user?.role === 'admin',
    login: vi.fn(),
    logout: vi.fn(),
  };

  return render(
    <AuthContext.Provider value={mockAuthContext}>
      {ui}
    </AuthContext.Provider>
  );
}

describe('ProtectedComponent', () => {
  it('debe mostrar contenido si está autenticado', () => {
    const user = { id: '1', email: 'test@test.com', role: 'user' };
    
    renderWithAuth(<ProtectedComponent />, { user });
    
    expect(screen.getByText('Contenido protegido')).toBeInTheDocument();
  });

  it('debe redirigir si no está autenticado', () => {
    renderWithAuth(<ProtectedComponent />, { user: null });
    
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument();
  });
});
```

---

## Best Practices

### 1. Organización

✅ **DO:**
```
MiComponente.tsx
__tests__/
  └── MiComponente.test.tsx
```

❌ **DON'T:**
```
tests/components/MiComponente.test.tsx  // Lejos del componente
```

### 2. Nomenclatura

```typescript
// ✅ Descriptivo
describe('authApi', () => {
  it('debe hacer login exitosamente con credenciales válidas', () => {});
  it('debe lanzar error 401 con credenciales inválidas', () => {});
});

// ❌ Poco claro
describe('auth', () => {
  it('funciona', () => {});
  it('falla', () => {});
});
```

### 3. Arrange-Act-Assert (AAA)

```typescript
it('debe actualizar contador', () => {
  // Arrange (preparar)
  const { result } = renderHook(() => useCounter(0));
  
  // Act (ejecutar)
  result.current.increment();
  
  // Assert (verificar)
  expect(result.current.count).toBe(1);
});
```

### 4. Evitar implementación en tests

```typescript
// ❌ MAL - Testea implementación
it('debe llamar setState', () => {
  const spy = vi.spyOn(component, 'setState');
  component.handleClick();
  expect(spy).toHaveBeenCalled();
});

// ✅ BIEN - Testea comportamiento
it('debe mostrar mensaje de éxito al hacer click', () => {
  render(<Component />);
  fireEvent.click(screen.getByRole('button'));
  expect(screen.getByText('¡Éxito!')).toBeInTheDocument();
});
```

### 5. Usar screen queries correctamente

```typescript
// ✅ Prefer accessibility queries
screen.getByRole('button', { name: 'Enviar' });
screen.getByLabelText('Email');
screen.getByPlaceholderText('Ingresa tu nombre');

// ⚠️ Usar solo si no hay alternativa
screen.getByTestId('custom-element');

// ❌ Evitar
screen.getByClassName('btn-primary');
```

### 6. Queries: get vs query vs find

```typescript
// getBy* - Lanza error si no encuentra (para elementos que DEBEN existir)
const button = screen.getByRole('button');

// queryBy* - Retorna null si no encuentra (para verificar ausencia)
expect(screen.queryByText('Oculto')).not.toBeInTheDocument();

// findBy* - Async, espera a que aparezca (para elementos que cargan)
const title = await screen.findByText('Cargado');
```

### 7. Cleanup automático

```typescript
// ✅ Ya configurado en setup.ts
afterEach(() => {
  cleanup(); // Limpia DOM después de cada test
});

// No necesitas hacerlo manualmente
```

### 8. Mock de fetch

```typescript
// Global mock para todos los tests de un archivo
beforeEach(() => {
  global.fetch = vi.fn();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// Mock específico por test
it('debe fetchear datos', async () => {
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    } as Response)
  );
  
  const result = await miApi.getData();
  expect(result.data).toBe('test');
});
```

---

## Coverage

### Ver coverage
```bash
npm run test:coverage
```

### Output
```
coverage/
├── index.html        # Reporte visual (abrir en browser)
├── coverage.json     # Datos JSON
└── lcov.info         # Para CI/CD
```

### Umbrales configurados
```typescript
// vitest.config.ts
coverage: {
  statements: 30,
  branches: 30,
  functions: 30,
  lines: 30,
}
```

### Qué cubrir:
- ✅ Lógica de negocio
- ✅ Funciones críticas (auth, API)
- ✅ Componentes complejos
- ✅ Hooks personalizados
- ❌ UI components simples (opcional)
- ❌ Tipos/interfaces
- ❌ Archivos de config

---

## Debugging Tests

### Ver console.log
```bash
npm run test -- --reporter=verbose
```

### Debuggear en VSCode

`.vscode/launch.json`:
```json
{
  "type": "node",
  "request": "launch",
  "name": "Debug Vitest",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "test"],
  "console": "integratedTerminal"
}
```

### Screenshot en test fallido

```typescript
import { render, screen } from '@testing-library/react';

it('debe hacer algo', () => {
  const { container } = render(<MiComponente />);
  
  // Si falla, inspecciona HTML
  console.log(container.innerHTML);
  
  // O usa debug()
  screen.debug();
});
```

---

## CI/CD Integration

### GitHub Actions

`.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - run: npm ci
      - run: npm run test:run
      - run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Error: "Cannot find module '@/...'"

**Solución:** Verifica alias en `vitest.config.ts`:
```typescript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './client/src'),
  },
}
```

### Error: "ReferenceError: fetch is not defined"

**Solución:** Mock fetch:
```typescript
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  } as Response)
);
```

### Tests lentos

**Solución:** Ejecuta solo un archivo:
```bash
npm run test -- client/src/hooks/__tests__/useMiHook.test.ts
```

### Mock no funciona

**Solución:** Asegúrate de restaurar:
```typescript
afterEach(() => {
  vi.restoreAllMocks();
  vi.clearAllMocks();
});
```

---

## Resources

- [Vitest Docs](https://vitest.dev/)
- [Testing Library Cheatsheet](https://testing-library.com/docs/react-testing-library/cheatsheet)
- [Common mistakes](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

---

## Checklist para Nuevos Tests

Antes de crear un test:

- [ ] Identifica el comportamiento a testear (no la implementación)
- [ ] Usa AAA pattern (Arrange-Act-Assert)
- [ ] Nombre descriptivo
- [ ] Mock solo lo necesario
- [ ] Cleanup automático
- [ ] Coverage > 30% en archivos críticos

**Happy testing!** 🧪✨
