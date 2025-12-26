import { MigrationInterface, QueryRunner, Table, TableIndex, TableForeignKey } from 'typeorm';

export class CreateAuthTables1704896400000 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    // Crear tabla refresh_token
    await queryRunner.createTable(
      new Table({
        name: 'refresh_token',
        columns: [
          {
            name: 'id',
            type: 'serial',
            isPrimary: true,
          },
          {
            name: 'token',
            type: 'text',
            isUnique: true,
          },
          {
            name: 'usuario_id',
            type: 'integer',
          },
          {
            name: 'expira_en',
            type: 'timestamp with time zone',
          },
          {
            name: 'revocado',
            type: 'boolean',
            default: false,
          },
          {
            name: 'ip_address',
            type: 'varchar',
            length: '45',
            isNullable: true,
          },
          {
            name: 'user_agent',
            type: 'text',
            isNullable: true,
          },
          {
            name: 'fecha_creacion',
            type: 'timestamp with time zone',
            default: 'CURRENT_TIMESTAMP',
          },
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

    // Agregar columnas de seguridad a tabla usuario si no existen
    const usuarioTable = await queryRunner.getTable('usuario');
    if (usuarioTable) {
      const ultimoLoginColumn = usuarioTable.findColumnByName('ultimo_login');
      if (!ultimoLoginColumn) {
        await queryRunner.query(`
          ALTER TABLE usuario 
          ADD COLUMN ultimo_login TIMESTAMP WITH TIME ZONE,
          ADD COLUMN intentos_fallidos_login INTEGER DEFAULT 0,
          ADD COLUMN bloqueado_hasta TIMESTAMP WITH TIME ZONE;
        `);
      }
    }
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    // Eliminar foreign key
    await queryRunner.dropForeignKey('refresh_token', 'FK_REFRESH_TOKEN_USUARIO');

    // Eliminar índices
    await queryRunner.dropIndex('refresh_token', 'IDX_REFRESH_TOKEN_USER_REVOKED');
    await queryRunner.dropIndex('refresh_token', 'IDX_REFRESH_TOKEN_TOKEN');

    // Eliminar tabla
    await queryRunner.dropTable('refresh_token', true);

    // Eliminar columnas de seguridad de usuario
    await queryRunner.query(`
      ALTER TABLE usuario 
      DROP COLUMN IF EXISTS ultimo_login,
      DROP COLUMN IF EXISTS intentos_fallidos_login,
      DROP COLUMN IF EXISTS bloqueado_hasta;
    `);
  }
}
