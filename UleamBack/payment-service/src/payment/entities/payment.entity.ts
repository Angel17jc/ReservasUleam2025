/**
 * Payment Entity - Entidad de TypeORM para la tabla payments
 * 
 * Nota importante: La columna se llama 'extra_metadata' en lugar de 'metadata'
 * porque 'metadata' es una palabra reservada de SQLAlchemy y TypeORM.
 */
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';
import { PaymentStatus } from '../interfaces/payment-provider.interface';

@Entity('payments')
@Index('idx_payments_reserva_status', ['reservaId', 'status'])
@Index('idx_payments_usuario_created', ['usuarioId', 'createdAt'])
export class Payment {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'reserva_id', type: 'integer' })
  reservaId: number;

  @Column({ name: 'usuario_id', type: 'integer' })
  usuarioId: number;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  amount: number;

  @Column({ type: 'varchar', length: 3, default: 'USD' })
  currency: string;

  @Column({
    type: 'enum',
    enum: PaymentStatus,
    default: PaymentStatus.PENDING,
  })
  status: PaymentStatus;

  @Column({ name: 'provider_name', type: 'varchar', length: 50 })
  providerName: string;

  @Column({ name: 'transaction_id', type: 'varchar', length: 255, unique: true })
  transactionId: string;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ name: 'extra_metadata', type: 'jsonb', nullable: true })
  extraMetadata: Record<string, any>;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;
}
