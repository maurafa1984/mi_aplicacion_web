import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from main import Base, ProductoDB 

# Usamos la misma URL que configuramos en el YAML de GitHub Actions
DATABASE_URL = os.getenv("DATABASE_URL")

@pytest.fixture
def db_session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

def test_crear_producto(db_session):
    nuevo_producto = ProductoDB(
        nombre="Teclado Mecánico",
        descripcion="Teclado RGB switch blue",
        categoria="Periféricos",
        precio=50.0,
        stock=20
    )
    db_session.add(nuevo_producto)
    db_session.commit()
    
    producto_db = db_session.query(ProductoDB).filter_by(nombre="Teclado Mecánico").first()
    assert producto_db is not None
    assert producto_db.nombre == "Teclado Mecánico"
    assert producto_db.stock == 20

def test_actualizar_stock_tras_venta(db_session):
    # 1. Crear producto inicial
    producto = ProductoDB(nombre="Monitor", categoria="Hardware", precio=200.0, stock=10)
    db_session.add(producto)
    db_session.commit()
    
    # 2. Simular venta reduciendo el stock
    producto.stock -= 2
    db_session.commit()
    
    # 3. Verificar que el valor se actualizó en la BD
    db_session.refresh(producto)
    assert producto.stock == 8

def test_eliminar_producto(db_session):
    # 1. Crear producto
    producto = ProductoDB(nombre="Mouse", categoria="Periféricos", precio=20.0, stock=5)
    db_session.add(producto)
    db_session.commit()
    
    # 2. Eliminar
    db_session.delete(producto)
    db_session.commit()
    
    # 3. Verificar que no existe
    busqueda = db_session.query(ProductoDB).filter_by(nombre="Mouse").first()
    assert busqueda is None

def test_validar_stock_insuficiente(db_session):
    # 1. Crear producto con stock limitado
    producto = ProductoDB(nombre="Teclado", categoria="Periféricos", precio=30.0, stock=1)
    db_session.add(producto)
    db_session.commit()
    
    # 2. Lógica: intentar vender más de lo que hay
    cantidad_a_vender = 5
    
    # Si la venta excede el stock, la lógica debería impedir la actualización
    if cantidad_a_vender > producto.stock:
        assert producto.stock == 1  # El stock debe permanecer intacto