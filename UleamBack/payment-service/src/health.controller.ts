/**
 * Health Controller - Endpoint de verificación de estado del servicio
 */
import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';

@ApiTags('health')
@Controller('health')
export class HealthController {
  constructor(
    @InjectDataSource()
    private dataSource: DataSource,
  ) {}

  @Get()
  @ApiOperation({ summary: 'Health check del servicio' })
  async check() {
    // Verificar conexión a base de datos
    let dbStatus = 'disconnected';
    try {
      await this.dataSource.query('SELECT 1');
      dbStatus = 'connected';
    } catch (error) {
      dbStatus = `error: ${error.message}`;
    }

    // Obtener providers habilitados desde ENV
    const providersEnabled = [];
    if (process.env.MOCK_ADAPTER_ENABLED === 'true') {
      providersEnabled.push('mock');
    }
    if (process.env.STRIPE_ENABLED === 'true') {
      providersEnabled.push('stripe');
    }
    if (process.env.MERCADOPAGO_ENABLED === 'true') {
      providersEnabled.push('mercadopago');
    }

    return {
      status: 'healthy',
      service: 'payment-service',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      database: dbStatus,
      providers_enabled: providersEnabled,
    };
  }
}
