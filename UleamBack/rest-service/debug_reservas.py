#!/usr/bin/env python3
"""Script de diagnóstico para verificar datos de reservas pendientes"""
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://Reservas_ULEAM:123456@localhost:5432/reservasuleam"

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Primero verificar qué tablas existen
        query_tables = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        result_tables = conn.execute(query_tables)
        tables = [row[0] for row in result_tables.fetchall()]
        
        print("=" * 80)
        print("TABLAS EN LA BASE DE DATOS:")
        print("=" * 80)
        for table in tables:
            print(f"  📦 {table}")
        
        if not tables:
            print("❌ NO HAY TABLAS EN LA BASE DE DATOS")
            print("💡 Ejecuta: cd database && psql -U Reservas_ULEAM -d reservasuleam -f init.sql")
            sys.exit(1)
        
        # Si no existe la tabla reserva, salir
        if 'reserva' not in tables:
            print("\n❌ LA TABLA 'reserva' NO EXISTE")
            print("💡 Ejecuta el script de inicialización de la base de datos")
            sys.exit(1)
        
        print(f"\n✅ Base de datos correctamente inicializada\n")
        
        # Consultar reservas pendientes con JOIN
        query = text("""
            SELECT 
                r.id,
                r.usuario_id,
                r.espacio_id,
                r.fecha,
                r.hora_inicio,
                r.hora_fin,
                r.titulo,
                u.nombre as usuario_nombre,
                u.apellido as usuario_apellido,
                e.nombre as espacio_nombre
            FROM reserva r
            LEFT JOIN usuario u ON r.usuario_id = u.id
            LEFT JOIN espacio e ON r.espacio_id = e.id
            WHERE r.estado_id = 1
            ORDER BY r.fecha DESC
            LIMIT 5
        """)
        
        result = conn.execute(query)
        rows = result.fetchall()
        
        print("=" * 80)
        print("RESERVAS PENDIENTES EN LA BD:")
        print("=" * 80)
        
        if not rows:
            print("❌ NO HAY RESERVAS PENDIENTES")
        else:
            for row in rows:
                print(f"\n📋 Reserva ID: {row[0]}")
                print(f"   Usuario ID: {row[1]} -> {row[7]} {row[8]}")
                print(f"   Espacio ID: {row[2]} -> {row[9]}")
                print(f"   Fecha: {row[3]}")
                print(f"   Horas: {row[4]} - {row[5]}")
                print(f"   Título: {row[6]}")
                
        # Verificar si hay usuarios
        result_users = conn.execute(text("SELECT COUNT(*) FROM usuario"))
        user_count = result_users.fetchone()[0]
        print(f"\n👥 Total usuarios en BD: {user_count}")
        
        # Verificar si hay espacios
        result_spaces = conn.execute(text("SELECT COUNT(*) FROM espacio"))
        space_count = result_spaces.fetchone()[0]
        print(f"🏢 Total espacios en BD: {space_count}")
        
        print("=" * 80)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    sys.exit(1)
