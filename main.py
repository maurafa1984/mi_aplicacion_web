import os
from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from fastapi.middleware.cors import CORSMiddleware

# --- Configuración de Base de Datos ---
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_HOST = "db" if os.getenv("IS_DOCKER") else "localhost"
    DATABASE_URL = f"postgresql+psycopg2://postgres:techsecure2026@{DB_HOST}:5432/techcommerce_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Modelos de Base de Datos ---
class ProductoDB(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(String(200))
    categoria = Column(String(50), nullable=False)
    precio = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    
    licencias = relationship("LicenciaSoftwareDB", back_populates="producto", cascade="all, delete-orphan")
    detalles_hardware = relationship("DetalleHardwareDB", back_populates="producto", cascade="all, delete-orphan")


class DetalleHardwareDB(Base):
    __tablename__ = "detalle_hardware"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    socket = Column(String(50))
    consumo_watts = Column(Integer)
    
    producto = relationship("ProductoDB", back_populates="detalles_hardware")


class LicenciaSoftwareDB(Base):
    __tablename__ = "licencias_software"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"))
    clave_activacion = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(200), default="Licencia original")
    
    producto = relationship("ProductoDB", back_populates="licencias")

class VentaDB(Base):
    __tablename__ = "ventas"
    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
    fecha = Column(String(50))
    
    producto = relationship("ProductoDB")

# Crear tablas
Base.metadata.create_all(bind=engine)


# --- Schemas Pydantic ---
class ProductoBase(BaseModel):
    nombre: str
    categoria: str
    precio: float
    stock: int


class ProductoCreate(ProductoBase): pass


class ProductoResponse(ProductoBase):
    id: int
    class Config: from_attributes = True


class LicenciaCreate(BaseModel):
    codigo: str
    descripcion: str


class LicenciaResponse(BaseModel):
    id: int
    codigo: str
    descripcion: str
    class Config: from_attributes = True

class VentaCreate(BaseModel):
    producto_id: int
    cantidad: int

class VentaResponse(VentaCreate):
    id: int
    total: float
    fecha: str
    class Config: from_attributes = True


# --- Inicialización App ---
app = FastAPI(title="TechCommerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


# --- Endpoints de Productos ---
@app.post("/productos/", response_model=ProductoResponse, status_code=201)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    db_producto = ProductoDB(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto


@app.get("/productos/", response_model=List[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    return db.query(ProductoDB).all()


@app.get("/productos/{producto_id}/", response_model=ProductoResponse)
def consultar_producto(producto_id: int, db: Session = Depends(get_db)):
    prod = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
    if not prod: raise HTTPException(status_code=404, detail="Producto no encontrado")
    return prod


@app.put("/productos/{producto_id}/", response_model=ProductoResponse)
def editar_producto(producto_id: int, producto_data: ProductoCreate, db: Session = Depends(get_db)):
    db_producto = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
    if not db_producto: raise HTTPException(status_code=404, detail="Producto no encontrado")
    for key, value in producto_data.model_dump().items():
        setattr(db_producto, key, value)
    db.commit()
    db.refresh(db_producto)
    return db_producto


@app.delete("/productos/{producto_id}/")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    db_producto = db.query(ProductoDB).filter(ProductoDB.id == producto_id).first()
    if not db_producto: raise HTTPException(status_code=404, detail="Producto no encontrado")
    db.delete(db_producto)
    db.commit()
    return {"message": "Producto eliminado"}


# --- Endpoints de Licencias ---
@app.get("/productos/{producto_id}/claves/", response_model=List[LicenciaResponse])
def obtener_claves(producto_id: int, db: Session = Depends(get_db)):
    if not db.query(ProductoDB).filter(ProductoDB.id == producto_id).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    licencias = db.query(LicenciaSoftwareDB).filter(LicenciaSoftwareDB.producto_id == producto_id).all()
    return [{"id": l.id, "codigo": l.clave_activacion, "descripcion": l.descripcion} for l in licencias]


@app.post("/productos/{producto_id}/claves/", status_code=201)
def crear_clave(producto_id: int, licencia: LicenciaCreate, db: Session = Depends(get_db)):
    if not db.query(ProductoDB).filter(ProductoDB.id == producto_id).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    nueva_clave = LicenciaSoftwareDB(
        producto_id=producto_id,
        clave_activacion=licencia.codigo,
        descripcion=licencia.descripcion
    )
    db.add(nueva_clave)
    db.commit()
    return {"message": "Licencia registrada correctamente"}


@app.put("/productos/{producto_id}/claves/{clave_id}/", response_model=LicenciaResponse)
def editar_clave(producto_id: int, clave_id: int, lic_data: LicenciaCreate, db: Session = Depends(get_db)):
    db_clave = db.query(LicenciaSoftwareDB).filter(
        LicenciaSoftwareDB.id == clave_id, 
        LicenciaSoftwareDB.producto_id == producto_id
    ).first()
    
    if not db_clave:
        raise HTTPException(status_code=404, detail="Licencia no encontrada para este producto")
    
    db_clave.clave_activacion = lic_data.codigo
    db_clave.descripcion = lic_data.descripcion
    
    db.commit()
    db.refresh(db_clave)
    
    return {"id": db_clave.id, "codigo": db_clave.clave_activacion, "descripcion": db_clave.descripcion}

@app.post("/ventas/", response_model=VentaResponse, status_code=201)
def realizar_venta(venta: VentaCreate, db: Session = Depends(get_db)):
    producto = db.query(ProductoDB).filter(ProductoDB.id == venta.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if producto.stock < venta.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")
    
    total_venta = producto.precio * venta.cantidad
    nueva_venta = VentaDB(
        producto_id=venta.producto_id,
        cantidad=venta.cantidad,
        total=total_venta,
        fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    producto.stock -= venta.cantidad
    db.add(nueva_venta)
    db.commit()
    db.refresh(nueva_venta)
    return nueva_venta
    
@app.get("/ventas/", response_model=List[VentaResponse])
def listar_ventas(db: Session = Depends(get_db)):
     ventas = db.query(VentaDB).all()
     return ventas
    
@app.get("/ventas/{venta_id}/factura/")
def generar_factura(venta_id: int, db: Session = Depends(get_db)):
    venta = db.query(VentaDB).filter(VentaDB.id == venta_id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    producto = db.query(ProductoDB).filter(ProductoDB.id == venta.producto_id).first()
    nombre_producto = producto.nombre if producto else "Producto Desconocido"
    
    return {
        "factura_id": f"FAC-{venta.id}",
        "fecha": venta.fecha,
        "producto_nombre": nombre_producto,
        "cantidad": venta.cantidad,
        "total_pagado": venta.total
    }