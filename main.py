from fastapi import FastAPI

app = FastAPI(title="Mi Aplicación Web")

@app.get("/")
def inicio():
    return {
        "estado": "Aplicación ejecutándose exitosamente",
        "framework": "FastAPI 0.110.0",
        "lenguaje": "Python 3.11"
    }