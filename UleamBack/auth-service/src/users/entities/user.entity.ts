import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';

@Entity('usuario')
@Index(['email'], { unique: true })
export class User {
  @PrimaryGeneratedColumn({ name: 'id' })
  id: number;

  @Column({ name: 'nombre', type: 'varchar', length: 100 })
  nombre: string;

  @Column({ name: 'apellido', type: 'varchar', length: 100 })
  apellido: string;

  @Column({ name: 'email', type: 'varchar', length: 255, unique: true })
  email: string;

  @Column({ name: 'password_hash', type: 'text' })
  passwordHash: string;

  @Column({ name: 'tipo_usuario_id', type: 'integer' })
  tipoUsuarioId: number; // 1=admin, 2=profesor, 3=estudiante

  @Column({ name: 'telefono', type: 'varchar', length: 20, nullable: true })
  telefono: string | null;

  @Column({ name: 'avatar_url', type: 'text', nullable: true })
  avatarUrl: string | null;

  @Column({ name: 'activo', type: 'boolean', default: true })
  activo: boolean;

  @CreateDateColumn({ name: 'fecha_creacion', type: 'timestamp with time zone' })
  fechaCreacion: Date;

  @UpdateDateColumn({ name: 'fecha_actualizacion', type: 'timestamp with time zone' })
  fechaActualizacion: Date;

  // Timestamps adicionales opcionales
  @Column({ name: 'ultimo_login', type: 'timestamp with time zone', nullable: true })
  ultimoLogin: Date | null;

  @Column({ name: 'intentos_fallidos_login', type: 'integer', default: 0 })
  intentosFallidosLogin: number;

  @Column({ name: 'bloqueado_hasta', type: 'timestamp with time zone', nullable: true })
  bloqueadoHasta: Date | null;
}
