import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = 'Creates the PostgreSQL database programmatically using individual DB environment variables.'

    def handle(self, *args, **options):
        dbname = os.getenv('DB_NAME')
        if not dbname:
            self.stdout.write(self.style.ERROR("DB_NAME not found in environment."))
            return

        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')

        self.stdout.write(f"Connecting to PostgreSQL server at {host}:{port} as user '{user}'...")

        try:
            # Connect to default 'postgres' database to create the new DB
            conn = psycopg2.connect(
                dbname='postgres',
                user=user,
                password=password,
                host=host,
                port=port
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (dbname,)
            )
            exists = cursor.fetchone()

            if exists:
                self.stdout.write(self.style.SUCCESS(f"Database '{dbname}' already exists."))
            else:
                cursor.execute(f'CREATE DATABASE "{dbname}";')
                self.stdout.write(self.style.SUCCESS(f"Database '{dbname}' created successfully!"))

            cursor.close()
            conn.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating database: {e}"))
