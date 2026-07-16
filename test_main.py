import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
import os
# He añadido VentaDB a la importación
from main import Base, ProductoDB, LicenciaSoftwareDB, VentaDB 

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

# --- TESTS ORIGINALES ---
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
    producto = ProductoDB(nombre="Monitor", categoria="Hardware", precio=200.0, stock=10)
    db_session.add(producto)
    db_session.commit()
    producto.stock -= 2
    db_session.commit()
    db_session.refresh(producto)
    assert producto.stock == 8

def test_eliminar_producto(db_session):
    producto = ProductoDB(nombre="Mouse", categoria="Periféricos", precio=20.0, stock=5)
    db_session.add(producto)
    db_session.commit()
    db_session.delete(producto)
    db_session.commit()
    busqueda = db_session.query(ProductoDB).filter_by(nombre="Mouse").first()
    assert busqueda is None

def test_validar_stock_insuficiente(db_session):
    producto = ProductoDB(nombre="Teclado", categoria="Periféricos", precio=30.0, stock=1)
    db_session.add(producto)
    db_session.commit()
    cantidad_a_vender = 5
    if cantidad_a_vender > producto.stock:
        assert producto.stock == 1

# --- NUEVOS TESTS ADICIONALES ---

def test_crear_producto_sin_nombre_falla(db_session):
    producto_incompleto = ProductoDB(descripcion="Falta nombre", categoria="Test", precio=10.0, stock=1)
    db_session.add(producto_incompleto)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_eliminacion_en_cascada_de_licencias(db_session):
    prod = ProductoDB(nombre="Software Pro", categoria="Software", precio=100.0)
    db_session.add(prod)
    db_session.commit()
    
    lic = LicenciaSoftwareDB(producto_id=prod.id, clave_activacion="ABC-123")
    db_session.add(lic)
    db_session.commit()
    
    db_session.delete(prod)
    db_session.commit()
    
    licencia_buscada = db_session.query(LicenciaSoftwareDB).filter_by(clave_activacion="ABC-123").first()
    assert licencia_buscada is None

def test_consultar_producto_por_id(db_session):
    p1 = ProductoDB(nombre="Producto A", categoria="Cat", precio=10.0)
    p2 = ProductoDB(nombre="Producto B", categoria="Cat", precio=20.0)
    db_session.add_all([p1, p2])
    db_session.commit()
    
    resultado = db_session.query(ProductoDB).filter(ProductoDB.id == p2.id).first()
    assert resultado is not None
    assert resultado.nombre == "Producto B"
    assert resultado.id == p2.id

# --- TEST DE VENTAS ---
def test_realizar_venta_exitosamente(db_session):
    # 1. Crear producto con stock suficiente
    producto = ProductoDB(nombre="Laptop", categoria="Hardware", precio=1000.0, stock=5)
    db_session.add(producto)
    db_session.commit()
    
    # 2. Realizar venta de 2 unidades
    cantidad = 2
    total_venta = producto.precio * cantidad
    nueva_venta = VentaDB(
        producto_id=producto.id,
        cantidad=cantidad,
        total=total_venta,
        fecha="2026-07-15"
    )
    db_session.add(nueva_venta)
    
    # 3. Actualizar stock
    producto.stock -= cantidad
    db_session.commit()
    
    # 4. Verificar
    venta_db = db_session.query(VentaDB).filter_by(producto_id=producto.id).first()
    producto_db = db_session.query(ProductoDB).filter_by(id=producto.id).first()
    
    assert venta_db is not None
    assert venta_db.cantidad == 2
    assert venta_db.total == 2000.0
    assert producto_db.stock == 3