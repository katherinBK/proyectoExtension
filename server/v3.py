from flask import Flask, request, jsonify
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
import chromadb
from flask_cors import CORS
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, AIMessage
import requests


app = Flask(__name__)
model = OllamaLLM(model="mistral")
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
memory = ConversationBufferMemory()
chroma_client = chromadb.PersistentClient(path="./chroma_db")  
collection = chroma_client.get_or_create_collection(name="usuarios")
usuarios_formulario_completado = set()

# Define possible objectives
OBJETIVOS = {
    "vender": ["comprar", "adquirir", "quiero comprar", "me interesa", "precio", "costo"],
    "consultar": ["información", "detalles", "características", "especificaciones", "consultar"],
    "agendar_cita": ["cita", "agendar", "programar", "reunión", "visita"]
}

def detectar_intencion(query: str) -> str:
    """Detecta la intención del usuario basada en palabras clave."""
    query = query.lower()
    
    for objetivo, keywords in OBJETIVOS.items():
        if any(keyword in query for keyword in keywords):
            return objetivo
    
    return "no_detectado"

def registrar_objetivo(query: str, usuario_id: str) -> str:
    """Registra un nuevo objetivo para el usuario."""
    objetivo = detectar_intencion(query)
    if objetivo == "no_detectado":
        return "No se detectó un objetivo específico."

    try:
        collection.add(
            ids=[f"objetivo_{usuario_id}_{objetivo}"],
            documents=[f"Usuario: {usuario_id}, Objetivo: {objetivo}, Estado: Pendiente"],
            metadatas=[{"usuario": usuario_id, "tipo": objetivo, "estado": "pendiente"}]
        )
        return f"Objetivo '{objetivo}' registrado para {usuario_id}."
    except Exception as e:
        return f"Error al registrar objetivo: {str(e)}"

def marcar_objetivo_completado(tipo_objetivo: str, usuario_id: str) -> str:
    """Marca un objetivo como completado."""
    try:
        collection.update(
            ids=[f"objetivo_{usuario_id}_{tipo_objetivo}"],
            metadatas=[{"estado": "cumplido"}]
        )
        print(f"Objetivo '{tipo_objetivo}' cumplido para {usuario_id}")
        return f"Objetivo '{tipo_objetivo}' cumplido para {usuario_id}."
    except Exception as e:
        return f"Error al marcar objetivo como completado: {str(e)}"

def obtener_estadisticas() -> dict:
    """Obtiene estadísticas de objetivos."""
    try:
        objetivos = collection.get()
        total_objetivos = {"vender": 0, "consultar": 0, "agendar_cita": 0}
        cumplidos_objetivos = {"vender": 0, "consultar": 0, "agendar_cita": 0}

        if objetivos and isinstance(objetivos, dict) and "metadatas" in objetivos and objetivos["metadatas"]:
            for obj in objetivos["metadatas"]:
                if isinstance(obj, dict) and "tipo" in obj and "estado" in obj:
                    tipo = obj["tipo"]
                    if tipo in total_objetivos:
                        total_objetivos[tipo] += 1
                        if obj["estado"] == "cumplido":
                            cumplidos_objetivos[tipo] += 1

        return {
            "total_vender": total_objetivos["vender"],
            "total_consultar": total_objetivos["consultar"],
            "total_agendar": total_objetivos["agendar_cita"],
            "cumplidos_vender": cumplidos_objetivos["vender"],
            "cumplidos_consultar": cumplidos_objetivos["consultar"],
            "cumplidos_agendar": cumplidos_objetivos["agendar_cita"],
        }
    except Exception as e:
        return {"error": str(e)}

def registrar_mensaje(mensaje: str, usuario_id: str, tipo: str):
    """Registra un mensaje en la base de datos."""
    try:
        documentos = collection.get()
        num_mensajes = 0
        if documentos and isinstance(documentos, dict) and "documents" in documentos:
            docs = documentos["documents"]
            if docs is not None:
                num_mensajes = len(docs)

        collection.add(
            ids=[f"mensaje_{usuario_id}_{tipo}_{num_mensajes}"],
            documents=[mensaje],
            metadatas=[{"usuario": usuario_id, "tipo": tipo}]
        )
    except Exception as e:
        print(f"Error al registrar mensaje: {str(e)}")

def obtener_productos():
    """Obtiene la lista de productos disponibles."""
    try:
        response = requests.get("http://127.0.0.1:5000/productos")
        if response.status_code == 200:
            data = response.json()
            
            # Manejar diferentes formatos de respuesta
            if isinstance(data, dict) and "productos" in data:
                productos = data["productos"]
            elif isinstance(data, list):
                productos = data
            else:
                return "No se pudo procesar el formato de productos"
            
            # Verificar que los productos tengan los campos necesarios
            productos_formateados = []
            for producto in productos:
                if isinstance(producto, dict):
                    nombre = producto.get("nombre", "Sin nombre")
                    precio = producto.get("precio", "Precio no disponible")
                    productos_formateados.append(f"{nombre} - ${precio}")
                else:
                    productos_formateados.append(str(producto))
            
            if productos_formateados:
                return "\n".join(productos_formateados)
            return "No hay productos disponibles"
            
        return f"Error al obtener productos: Código {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: No se pudo conectar con la API de productos"
    except requests.exceptions.RequestException as e:
        return f"Error en la solicitud de productos: {str(e)}"
    except Exception as e:
        return f"Error al obtener productos: {str(e)}"

# Define the prompt with better system instructions
prompt = ChatPromptTemplate.from_messages([
    ("system", """Eres un asistente de ventas en CommerIA. Tu tarea es:
    1. Detectar las intenciones del usuario (vender, consultar, agendar cita)
    2. Registrar los objetivos detectados
    3. SOLO ofrecer productos que estén disponibles en nuestra API local (http://127.0.0.1:5000/productos)
    4. Guiar al usuario en el proceso de compra
    5. SOLO ofrecer lo que pida el usuario, si el usuario pide algo que no está en nuestra API, debes indicarle que no podemos ofrecerlo.
    6. SOLO ofrecer lo que pida el usuario, si el usuario pide un telefono no ofrezcas cosas que no sean telefonos
    IMPORTANTE: 
    - Solo debes ofrecer productos que estén disponibles en nuestra API local.
    - Si el usuario pregunta por productos que no están en nuestra API, debes indicarle que solo puedes ofrecer los productos disponibles en nuestro catálogo.
    - Cuando el usuario muestre interés en comprar o agendar una cita, indica que necesitas sus datos para continuar.
    """),
    ("user", "{input}"),
    ("ai", "Para continuar con tu solicitud, necesito que completes tus datos en el formulario que aparecerá."),
])

@app.route("/chat", methods=["POST"])
def obtener_respuesta():
    try:
        data = request.get_json(force=True)
        pregunta = data.get("message", "")
        usuario_id = data.get("usuario_id", "usuario_generico")

        if not pregunta:
            return jsonify({"error": "El campo 'message' está vacío o ausente"}), 400

        # Detectar y registrar objetivo si existe
        objetivo = detectar_intencion(pregunta)
        if objetivo != "no_detectado":
            registrar_objetivo(pregunta, usuario_id)

        # Obtener productos disponibles
        productos_disponibles = obtener_productos()
        
        # Generar respuesta usando el modelo con información de productos
        messages = prompt.format_messages(
            input=f"{pregunta}\n\nProductos disponibles:\n{productos_disponibles}"
        )
        respuesta = model.invoke(messages)

        # Determinar si se debe mostrar el formulario
        mostrar_formulario = False
        if objetivo in ["vender", "agendar_cita"]:
            mostrar_formulario = True

        # Registrar mensajes en ChromaDB
        registrar_mensaje(pregunta, usuario_id, "usuario")
        registrar_mensaje(str(respuesta), usuario_id, "bot")

        return jsonify({
            "response": str(respuesta),
            "mostrar_formulario": mostrar_formulario
        })

    except Exception as e:
        print("Error en el servidor:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/enviar_formulario", methods=["POST"])
def recibir_formulario():
    try:
        data = request.get_json(force=True)

        nombre = data.get("nombre", "")
        cedula = data.get("cedula", "")
        email = data.get("email", "")
        numero = data.get("numero", "")
        producto = data.get("producto", "")
        agendar_cita = data.get("agendarCita", "no")

        user_id = f"user_{cedula}"
        document_text = f"Nombre: {nombre}, Cedula: {cedula}, Email: {email}, Teléfono: {numero}, Producto: {producto}, Agendar Cita: {agendar_cita}"

        collection.add(
            ids=[user_id], 
            documents=[document_text],
            metadatas=[{"nombre": nombre, "cedula": cedula, "email": email, "numero": numero, "producto": producto, "agendarCita": agendar_cita}]
        )

        return jsonify({"message": "Formulario recibido y almacenado correctamente en ChromaDB"})

    except Exception as e:
        print("Error en el servidor:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/estadisticas_citas", methods=["GET"])
def obtener_estadisticas_citas():
    try:
        citas = collection.get()
        total_citas = 0
        
        if citas and isinstance(citas, dict) and "metadatas" in citas and citas["metadatas"]:
            total_citas = sum(1 for cita in citas["metadatas"] 
                            if isinstance(cita, dict) and cita.get("agendarCita") == "sí")
        
        return jsonify({"total_citas": total_citas})

    except Exception as e:
        print("Error en el servidor:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=3009)