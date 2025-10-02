import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity('notificacion')
export class Notification {
    @PrimaryGeneratedColumn()
    id: number;

    @Column({ name: 'usuario_id' })
    userId: number;

    @Column()
    titulo: string;

    @Column()
    mensaje: string;

    @Column({ default: false })
    leida: boolean;

    @Column({ name: 'reserva_id', nullable: true })
    reservaId?: number;

    @Column({ name: 'espacio_id', nullable: true })
    espacioId?: number;

    @Column('jsonb', { nullable: true })
    metadata: any;

    @Column({ name: 'leida_at', type: 'timestamp', nullable: true })
    leidaAt?: Date;

    @CreateDateColumn({ name: 'creado_en' })
    creadoEn: Date;

    @UpdateDateColumn({ name: 'actualizado_en' })
    actualizadoEn: Date;
}