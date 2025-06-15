from fastapi import fastAPI, request
from pydantic import BaseModel

class datosCliente(BaseModel):
    nombre: str
    email: str
    numero: str
    producto: str

@app.post('/enviardatos')
async def datosCliente(cliente: datosClientes)

