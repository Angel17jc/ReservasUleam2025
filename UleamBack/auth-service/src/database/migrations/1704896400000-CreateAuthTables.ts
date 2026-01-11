import { MigrationInterface, QueryRunner, Table, TableIndex, TableForeignKey } from 'typeorm';

export class CreateAuthTables1704896400000 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // 1) Crear tabla usuario (pilar 1: BD propia de auth)
    await queryRunner.createTable(
      new Table({
        name: 'usuario',
        columns: [
          { name: 'id', type: 'serial', isPrimary: true },
          { name: 'nombre', type: 'varchar', length: '100' },
          { name: 'apellido', type: 'varchar', length: '100' },
          { name: 'email', type: 'varchar', length: '255', isUnique: true },
          { name: 'password_hash', type: 'text' },
          { name: 'tipo_usuario_id', type: 'integer' },
          { name: 'telefono', type: 'varchar', length: '20', isNullable: true },
          { name: 'avatar_url', type: 'text', isNullable: true },
          { name: 'estado', type: 'varchar', length: '20', default: "'activo'" },
          { name: 'creado_en', type: 'timestamp', default: 'CURRENT_TIMESTAMP' },
          { name: 'actualizado_en', type: 'timestamp', default: 'CURRENT_TIMESTAMP' },
          { name: 'ultimo_login', type: 'timestamp', isNullable: true },
          { name: 'intentos_fallidos_login', type: 'integer', default: 0, isNullable: true },
          { name: 'bloqueado_hasta', type: 'timestamp', isNullable: true },
        ],
      }),
      true,
    );

    // Índice único email (ya marcado en la columna, pero explícito por claridad)
    await queryRunner.createIndex(
      'usuario',
      new TableIndex({
        name: 'IDX_USUARIO_EMAIL',
        columnNames: ['email'],
        isUnique: true,
      }),
    );

    // 2) Crear tabla refresh_token
    await queryRunner.createTable(
      new Table({
        name: 'refresh_token',
        columns: [
          { name: 'id', type: 'serial', isPrimary: true },
          { name: 'token', type: 'text', isUnique: true },
          { name: 'usuario_id', type: 'integer' },
          { name: 'expira_en', type: 'timestamp with time zone' },
          { name: 'revocado', type: 'boolean', default: false },
          { name: 'ip_address', type: 'varchar', length: '45', isNullable: true },
          { name: 'user_agent', type: 'text', isNullable: true },
          { name: 'fecha_creacion', type: 'timestamp with time zone', default: 'CURRENT_TIMESTAMP' },
        ],
      }),
      true,
    );

    // Crear índice único para token
    await queryRunner.createIndex(
      'refresh_token',
      new TableIndex({
        name: 'IDX_REFRESH_TOKEN_TOKEN',
        columnNames: ['token'],
        isUnique: true,
      }),
    );

    // Crear índice compuesto para usuario_id y revocado
    await queryRunner.createIndex(
      'refresh_token',
      new TableIndex({
        name: 'IDX_REFRESH_TOKEN_USER_REVOKED',
        columnNames: ['usuario_id', 'revocado'],
      }),
    );

    // Crear foreign key hacia tabla usuario
    await queryRunner.createForeignKey(
      'refresh_token',
      new TableForeignKey({
        columnNames: ['usuario_id'],
        referencedColumnNames: ['id'],
        referencedTableName: 'usuario',
        onDelete: 'CASCADE',
        name: 'FK_REFRESH_TOKEN_USUARIO',
      }),
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Eliminar foreign key
    await queryRunner.dropForeignKey('refresh_token', 'FK_REFRESH_TOKEN_USUARIO');

    // Eliminar índices
    await queryRunner.dropIndex('refresh_token', 'IDX_REFRESH_TOKEN_USER_REVOKED');
    await queryRunner.dropIndex('refresh_token', 'IDX_REFRESH_TOKEN_TOKEN');

    // Eliminar tabla
    await queryRunner.dropTable('refresh_token', true);

    // Eliminar índice y tabla usuario
    await queryRunner.dropIndex('usuario', 'IDX_USUARIO_EMAIL');
    await queryRunner.dropTable('usuario', true);
  }
}
