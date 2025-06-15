from flask import Flask, request, jsonify
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
import chromadb
from flask_cors import CORS
from langchain_core.tools import tool
from langchain.agents import AgentExecutor


app = Flask(__name__)
model = OllamaLLM(model="mistral", tool_calling=True)  # Inicializar el modelo (local) de Ollama
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True) #usar la libreria CORS para evitar errores con el FronEnd
# Definir memoria de conversación
memory = ConversationBufferMemory()
chroma_client = chromadb.PersistentClient(path="./chroma_db")  
collection = chroma_client.get_or_create_collection(name="usuarios")
usuarios_formulario_completado = set()


def registrar_objetivo(query: str, usuario_id: str) -> str:
    objetivo = detectar_intencion(query)
    if not objetivo:
        return "No se detectó un objetivo específico."

    collection.add(
        ids=[f"objetivo_{usuario_id}_{objetivo}"],
        documents=[f"Usuario: {usuario_id}, Objetivo: {objetivo}, Estado: Pendiente"],
        metadatas=[{"usuario": usuario_id, "tipo": objetivo, "estado": "pendiente"}]
    )

    return f"Objetivo '{objetivo}' registrado para {usuario_id}."

def marcar_objetivo_completado(tipo_objetivo: str, usuario_id: str) -> str:
    collection.update(
        ids=[f"objetivo_{usuario_id}_{tipo_objetivo}"],
        metadatas=[{"estado": "cumplido"}]
    )
    return f"Objetivo '{tipo_objetivo}' cumplido para {usuario_id}."

def registrar_mensaje(mensaje: str, usuario_id: str, tipo: str):
    collection.add(
        ids=[f"mensaje_{usuario_id}_{tipo}_{len(collection)}"],
        documents=[mensaje],
        metadatas=[{"usuario": usuario_id, "tipo": tipo}]
    )

def obtener_estadisticas() -> dict:
    objetivos = collection.get(include=["metadatas"])
    total_objetivos = {"vender": 0, "consultar": 0, "agendar cita": 0}
    cumplidos_objetivos = {"vender": 0, "consultar": 0, "agendar cita": 0}

    for obj in objetivos["metadatas"]:
        tipo = obj["tipo"]
        total_objetivos[tipo] += 1
        if obj["estado"] == "cumplido":
            cumplidos_objetivos[tipo] += 1
            print(cumplidos_objetivos)

    return {
        "total_vender": total_objetivos["vender"],
        "total_consultar": total_objetivos["consultar"],
        "total_agendar": total_objetivos["agendar cita"],
        "cumplidos_vender": cumplidos_objetivos["vender"],
        "cumplidos_consultar": cumplidos_objetivos["consultar"],
        "cumplidos_agendar": cumplidos_objetivos["agendar cita"],
    }
@tool(description="Base de conocimientos que consume el API de los productos disponibles y responde en base a eso") #herramienta que se le pasa al LLM para consumir un API en caso de que esta este activa
def obtener_productos():
    response = request.get("http://127.0.0.1:5000/productos")
    if response.status_code == 200:
        data = response.json()
        productos = data.get("productos" ,[])
        return "\n".join([f"{p['nombre']} - ${p['precio']} in productos"])


# Inicializar ChromaDB con almacenamiento persistente
chroma_client = chromadb.PersistentClient(path="./chroma_db")  
collection = chroma_client.get_or_create_collection(name="usuarios")

# Definir el prompt con mensaje inicial preprogramado
prompt = ChatPromptTemplate.from_messages([ #prompt y roles asignados al agente
    ("system", "Eres un asistente de ventas en CommerIA."),#el system prompt del bot
    ("user", "{input}"), #se indica que se espera el input del usuario antes de responder
    ("ai", "Para seguir, completa el formulario aquí: [Formulario](http://localhost:3000/#/tabspills). Una vez completado, vuelve al chat para continuar."),
])
# Crear la cadena con memoria
chain = prompt | model 
agent_executor = AgentExecutor(agent=chain,tools=[obtener_productos]) #anidar las cadenas del agente con sus herraminetas y prompts

@app.route("/chat", methods=["POST"]) #definir la ruta del API para conexion al frontEnd
def obtener_respuesta():
    try:
        data = request.get_json(force=True) #se fuerza una respuesta json
        pregunta = data.get("message", "")
        usuario_id = "usuario_generico"

        if not pregunta:
            return jsonify({"error": "El campo 'message' está vacío o ausente"}), 400

        respuesta = model.invoke(pregunta)

        # Registrar mensajes en ChromaDB
        registrar_mensaje(pregunta, usuario_id, "usuario")
        registrar_mensaje(respuesta, usuario_id, "bot")

        return jsonify({"response": respuesta})

    except Exception as e:
        print("Error en el servidor:", e)
        return jsonify({"error": str(e)}), 500 #mensajes de depuracion


@app.route("/enviar_formulario", methods=["POST"]) #API para enviar el formulario
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

        print(f"Datos guardados en ChromaDB: {data}")

        return jsonify({"message": "Formulario recibido y almacenado correctamente en ChromaDB"})

    except Exception as e:
        print("Error en el servidor:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/estadisticas_citas", methods=["GET"]) #Api para obtener las citas agendadas
def obtener_estadisticas_citas():
    try:
        citas = collection.get(include=["metadatas"])
        total_citas = sum(1 for cita in citas["metadatas"] if cita.get("agendarCita") == "sí")
        print("total de citas:")
        print(total_citas)

        return jsonify({"total_citas": total_citas})

    except Exception as e:
        print("Error en el servidor:", e)
        return jsonify({"error": str(e)}), 500
"""@app.route("/mensajes_totales" , methods=["POST"])
def obtener_mensajes_totales():
"""


if __name__ == "__main__":
    app.run(debug=True, port=3009) #se deja activo el modo debug para el ambiente de preprod