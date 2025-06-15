from flask import Flask,jsonify
import requests
import json

app = Flask(__name__)
productos = [
    
    {"id": 1, "nombre": "Smartphone Galaxy S22", "descripcion": "Celular de alta gama con pantalla AMOLED de 6.1\", 128GB de almacenamiento y cámara de 50MP.", "precio": 3500000, "tipo": "Celulares"},
    {"id": 2, "nombre": "Laptop Lenovo ThinkPad X1", "descripcion": "Notebook ultradelgada con procesador Intel i7, 16GB RAM y SSD de 512GB.", "precio": 8200000, "tipo": "Informática"},
    {"id": 3, "nombre": "Arduino Uno R3", "descripcion": "Placa de desarrollo basada en ATmega328P, ideal para proyectos de robótica y automatización.", "precio": 300000, "tipo": "Robótica"},
    {"id": 4, "nombre": "Disco Duro Externo 1TB", "descripcion": "Almacenamiento portátil de alta velocidad con conexión USB 3.0.", "precio": 450000, "tipo": "Componentes"},
    {"id": 5, "nombre": "Teclado Mecánico RGB", "descripcion": "Teclado para gaming con switches mecánicos y retroiluminación RGB personalizable.", "precio": 320000, "tipo": "Componentes"},
    {"id": 6, "nombre": "Cable HDMI 2.0 1.5m", "descripcion": "Cable de alta velocidad para transmisión de video en 4K.", "precio": 45000, "tipo": "Cables"},
    {"id": 7, "nombre": "Monitor Samsung 24\" Full HD", "descripcion": "Pantalla LED con resolución 1920x1080 y tecnología antirreflejo.", "precio": 1200000, "tipo": "Informática"},
    {"id": 8, "nombre": "Impresora Multifunción HP", "descripcion": "Impresora con capacidad de escaneo, fotocopia y conexión Wi-Fi.", "precio": 1700000, "tipo": "Informática"},
    {"id": 9, "nombre": "Memoria RAM 8GB DDR4", "descripcion": "Módulo de memoria RAM para mejorar el rendimiento de computadoras y laptops.", "precio": 400000, "tipo": "Componentes"},
    {"id": 10, "nombre": "Parlante Bluetooth JBL", "descripcion": "Altavoz portátil con sonido estéreo y batería de larga duración.", "precio": 650000, "tipo": "Electrónica"},
    {"id": 11, "nombre": "Smartwatch Xiaomi Mi Band 6", "descripcion": "Reloj inteligente con monitoreo de actividad física y sensor de oxígeno en sangre.", "precio": 450000, "tipo": "Electrónica"},
    {"id": 12, "nombre": "Cámara Web Full HD Logitech", "descripcion": "Webcam con resolución 1080p y micrófono integrado para videollamadas.", "precio": 600000, "tipo": "Componentes"},
    {"id": 13, "nombre": "Router Wi-Fi TP-Link", "descripcion": "Dispositivo de red con tecnología dual-band y cobertura amplia.", "precio": 550000, "tipo": "Informática"},
    {"id": 14, "nombre": "SSD NVMe 512GB Kingston", "descripcion": "Unidad de estado sólido de alta velocidad para computadoras.", "precio": 900000, "tipo": "Componentes"},
    {"id": 15, "nombre": "Fuente de Poder 650W Corsair", "descripcion": "Fuente de alimentación para computadoras con certificación 80 Plus Bronze.", "precio": 750000, "tipo": "Componentes"},
    {"id": 16, "nombre": "Kit de Sensores para Arduino", "descripcion": "Conjunto de sensores de temperatura, humedad y movimiento para proyectos de robótica.", "precio": 250000, "tipo": "Robótica"},
    {"id": 17, "nombre": "Mouse inalámbrico Logitech", "descripcion": "Ratón ergonómico con conexión Bluetooth y sensor óptico de alta precisión.", "precio": 280000, "tipo": "Informática"},
    {"id": 18, "nombre": "Tarjeta Gráfica Nvidia RTX 3060", "descripcion": "GPU de alto rendimiento para gaming y edición de video.", "precio": 3500000, "tipo": "Componentes"},
    {"id": 19, "nombre": "Cable de Red Cat6 5m", "descripcion": "Cable Ethernet de alta velocidad para conexiones de Internet.", "precio": 70000, "tipo": "Cables"},
    {"id": 20, "nombre": "Cámara de Seguridad Wi-Fi", "descripcion": "Cámara con visión nocturna y detección de movimiento para monitoreo remoto.", "precio": 1000000, "tipo": "Electrónica"}
]


@app.route('/productos', methods =['GET'])
def get_productos():
    return jsonify(productos) 
if __name__ == '__main__':
    app.run(debug=True)

