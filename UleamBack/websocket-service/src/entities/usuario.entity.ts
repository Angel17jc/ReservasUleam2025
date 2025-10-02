import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';
import { TipoUsuario } from './tipo-usuario.entity';

@Entity('usuario')
export class Usuario {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column({ name: 'password_hash' })
  passwordHash: string;

  @Column()
  nombre: string;

  @Column()
  apellido: string;

  @Column({ nullable: true })
  telefono?: string;

  @Column({ name: 'tipo_usuario_id' })
  tipoUsuarioId: number;

  @Column({ default: 'activo' })
  estado: string;

  @Column({ name: 'avatar_url', nullable: true })
  avatarUrl?: string;

  @ManyToOne(() => TipoUsuario, (tipo) => tipo.usuarios, { eager: false })
  @JoinColumn({ name: 'tipo_usuario_id' })
  tipoUsuario?: TipoUsuario;

  @CreateDateColumn({ name: 'creado_en' })
  creadoEn: Date;

  @UpdateDateColumn({ name: 'actualizado_en' })
  actualizadoEn: Date;
}
