import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';
import { User } from '../../users/entities/user.entity';

@Entity('refresh_token')
@Index(['token'], { unique: true })
@Index(['usuarioId', 'revocado'])
export class RefreshToken {
  @PrimaryGeneratedColumn({ name: 'id' })
  id: number;

  @Column({ name: 'token', type: 'text', unique: true })
  token: string;

  @Column({ name: 'usuario_id', type: 'integer' })
  usuarioId: number;

  @Column({ name: 'expira_en', type: 'timestamp with time zone' })
  expiraEn: Date;

  @Column({ name: 'revocado', type: 'boolean', default: false })
  revocado: boolean;

  @Column({ name: 'ip_address', type: 'varchar', length: 45, nullable: true })
  ipAddress: string | null;

  @Column({ name: 'user_agent', type: 'text', nullable: true })
  userAgent: string | null;

  @CreateDateColumn({ name: 'fecha_creacion', type: 'timestamp with time zone' })
  fechaCreacion: Date;

  @ManyToOne(() => User, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'usuario_id' })
  usuario: User;
}
