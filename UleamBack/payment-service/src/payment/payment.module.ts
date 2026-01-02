/**
 * Payment Module - Módulo de funcionalidad de pagos
 */
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Payment } from './entities/payment.entity';
import { PaymentService } from './payment.service';
import { PaymentController } from './payment.controller';
import { MockAdapter } from './adapters/mock.adapter';

@Module({
  imports: [TypeOrmModule.forFeature([Payment])],
  providers: [PaymentService, MockAdapter],
  controllers: [PaymentController],
  exports: [PaymentService],
})
export class PaymentModule {}
