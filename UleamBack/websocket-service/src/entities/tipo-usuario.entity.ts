import { Entity, Column, PrimaryGeneratedColumn, OneToMany } from 'typeorm';
import { Usuario } from './usuario.entity';

@Entity('tipo_usuario')
export class TipoUsuario {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  nombre: string;

  @Column({ nullable: true })
  descripcion?: string;

  @Column({ name: 'nivel_prioridad', type: 'int', default: 3 })
  nivelPrioridad: number;

  @Column({ type: 'jsonb', nullable: true })
  permisos?: Record<string, any>;

  @OneToMany(() => Usuario, (usuario) => usuario.tipoUsuario)
  usuarios: Usuario[];
}
