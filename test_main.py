import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
# Importamos desde main.py. Asegúrate de que este archivo esté en la misma carpeta
from main import Base, ProductoDB 

# Usamos la misma URL que configuramos en el YAML de GitHub Actions
DATABASE_URL = os.getenv("DATABASE_URL")

@pytest.fixture
def db_session():
    # Creamos conexión y tablas temporales para el test
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Limpiamos todo al terminar
    session.close()
    Base.metadata.drop_all(engine)

def test_crear_producto(db_session):
    # 1. Creamos el objeto ProductoDB
    nuevo_producto = ProductoDB(
        nombre="Teclado Mecánico",
        descripcion="Teclado RGB switch blue",
        categoria="Periféricos",
        precio=50.0,
        stock=20
    )
    
    # 2. Insertamos y guardamos
    db_session.add(nuevo_producto)
    db_session.commit()
    
    # 3. Verificamos que realmente se guardó
    producto_db = db_session.query(ProductoDB).filter_by(nombre="Teclado Mecánico").first()
    
    assert producto_db is not None
    assert producto_db.nombre == "Teclado Mecánico"
    assert producto_db.stock == 20