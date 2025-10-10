# --- main.py ---
import os
import google.generativeai as genai
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
        raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")

    # Configura a API do Google e inicializa o modelo
    genai.configure(api_key=google_api_key)
    app.state.model = genai.GenerativeModel('gemini-1.5-flash-latest')
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

class ChatResponse(BaseModel):
    reply: str

# --- Endpoints da API ---
@app.post("/chat", response_model=ChatResponse)
async def handle_chat(chat_request: ChatRequest, request: Request):
    """
    Recebe uma mensagem do usuário e retorna a resposta da IA.
    """
    try:
        model = request.app.state.model
        response = model.generate_content(chat_request.message)
        return ChatResponse(reply=response.text)
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar a mensagem.")

@app.get("/")
def read_root():
    return {"status": "Auxilium IA API está funcionando!"}