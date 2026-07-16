import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Importamos los modelos directamente de tu archivo main
from main import Base, ProductoDB, DetalleHardwareDB

# Configuración de la conexión (usa la misma URL que tu contenedor)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:techsecure2026@localhost:5432/techcommerce_db")
engine = create_engine(DATABASE_URL)

# --- INICIO DE MODIFICACIÓN ---
# CUIDADO: Esto borra TODAS las tablas existentes y las recrea vacías
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
# --- FIN DE MODIFICACIÓN ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def poblar_base_de_datos():
    db = SessionLocal()
    try:
        # Limpiar datos previos para evitar duplicados en las pruebas
        print("🧹 Limpiando datos antiguos...")
        db.query(DetalleHardwareDB).delete()
        db.query(ProductoDB).delete()
        db.commit()

        print("📦 Insertando catálogo de hardware real...")

        # --- PRODUCTOS ---
        productos_hardware = [
            # Procesadores
            {"nombre": "AMD Ryzen 7 5700X", "categoria": "Partes", "precio": 190.00, "stock": 10, "descripcion": "8 núcleos, AM4", "socket": "AM4", "watts": 65},
            {"nombre": "Intel Core i5-13400F", "categoria": "Partes", "precio": 210.00, "stock": 8, "descripcion": "10 núcleos, LGA1700", "socket": "LGA1700", "watts": 65},
            {"nombre": "AMD Ryzen 9 7900X", "categoria": "Partes", "precio": 420.00, "stock": 0, "descripcion": "12 núcleos, AM5 (SIN STOCK)", "socket": "AM5", "watts": 170},

            # Placas Madre
            {"nombre": "ASUS TUF Gaming B550-PLUS", "categoria": "Partes", "precio": 145.00, "stock": 5, "descripcion": "Placa ATX para AMD Ryzen", "socket": "AM4", "watts": 50},
            {"nombre": "MSI PRO Z790-P Wi-Fi", "categoria": "Partes", "precio": 220.00, "stock": 4, "descripcion": "Placa para Intel 12/13/14 Gen", "socket": "LGA1700", "watts": 60},

            # Memorias RAM
            {"nombre": "Kingston Fury Beast 16GB DDR4", "categoria": "Partes", "precio": 45.00, "stock": 20, "descripcion": "3200MHz CL16", "socket": "DDR4", "watts": 5},
            {"nombre": "Corsair Vengeance 32GB DDR5", "categoria": "Partes", "precio": 115.00, "stock": 15, "descripcion": "5600MHz CL36", "socket": "DDR5", "watts": 7},

            # Tarjetas de Video
            {"nombre": "NVIDIA RTX 4070 Ti Super 16GB", "categoria": "Partes", "precio": 850.00, "stock": 3, "descripcion": "Arquitectura Ada Lovelace", "socket": "PCIe", "watts": 285},
            {"nombre": "AMD Radeon RX 7600 8GB", "categoria": "Partes", "precio": 270.00, "stock": 6, "descripcion": "Arquitectura RDNA 3", "socket": "PCIe", "watts": 165},
        ]

        for item in productos_hardware:
            # 1. Crear el producto base
            nuevo_prod = ProductoDB(
                nombre=item["nombre"],
                categoria=item["categoria"],
                precio=item["precio"],
                stock=item["stock"],
                descripcion=item["descripcion"]
            )
            db.add(nuevo_prod)
            db.commit() # Commiteamos para generar el ID
            db.refresh(nuevo_prod)

            # 2. Asociar sus especificaciones técnicas de hardware
            nuevas_specs = DetalleHardwareDB(
                producto_id=nuevo_prod.id,
                socket=item["socket"],
                consumo_watts=item["watts"]
            )
            db.add(nuevas_specs)
            
        db.commit()
        print("🚀 ¡Base de datos poblada exitosamente al 100%!")

    except Exception as e:
        print(f"❌ Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    poblar_base_de_datos()