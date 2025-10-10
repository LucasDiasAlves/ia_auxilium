# --- main.py ---
import os
import google.generativeai as genai
import uuid
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Configuração do Modelo Gemini na inicialização ---
    # Pega a chave da API do ambiente
    google_api_key = os.getenv("GOOGLE_API_KEY")

    # Verifica se a chave da API foi configurada
    if not google_api_key:
        print("ERRO CRÍTICO: A variável de ambiente GOOGLE_API_KEY não foi definida.")
        print("Crie um arquivo .env na raiz do projeto e adicione a linha: GOOGLE_API_KEY='sua_chave_aqui'")
        raise ValueError("GOOGLE_API_KEY não encontrada.")

    # Configura a API do Google e inicializa o modelo
    genai.configure(api_key=google_api_key)
    app.state.model = genai.GenerativeModel('gemini-pro')
    # Dicionário para armazenar as sessões de chat em memória
    app.state.chat_sessions = {}
    print("Modelo Gemini carregado com sucesso.")
    yield
    # Código de limpeza (se necessário) ao desligar a aplicação
    print("Aplicação encerrada.")

app = FastAPI(
    title="Auxilium IA API",
    description="API para o assistente de IA do app Auxilium.",
    version="0.1.0",
    lifespan=lifespan
)

# --- Modelos de Dados (O que a API recebe e devolve) ---
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # Opcional. Se não for fornecido, uma nova sessão é criada.

class ChatResponse(BaseModel):
    reply: str
    session_id: str

# --- Endpoints da API ---
@app.post("/chat", response_model=ChatResponse)
async def handle_chat(chat_request: ChatRequest, request: Request):
    """
    Recebe uma mensagem do usuário e retorna a resposta da IA.
    """
    try:
        model = request.app.state.model
        chat_sessions = request.app.state.chat_sessions
        session_id = chat_request.session_id

        # Se não houver session_id, cria uma nova sessão de chat
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            # Inicia um novo chat usando o método do modelo e armazena
            chat_sessions[session_id] = model.start_chat(history=[])

        # Recupera a sessão de chat correta
        chat_session = chat_sessions[session_id]

        # Envia a mensagem para o modelo mantendo o histórico
        response = chat_session.send_message(chat_request.message)

        return ChatResponse(reply=response.text, session_id=session_id)

    except Exception as e:
        # Log do erro detalhado no console para depuração
        error_message = f"Ocorreu um erro interno: {e}"
        print(error_message)
        # Retorna uma mensagem de erro mais informativa se não estiver em produção
        detail_message = error_message if os.getenv("ENV") != "production" else "Erro ao processar a mensagem."
        raise HTTPException(status_code=500, detail=detail_message)

@app.get("/")
def read_root():
    return {"status": "Auxilium IA API está funcionando!"}