# --- main.py ---
import os
import google.generativeai as genai
import uuid
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from supabase import create_async_client, AsyncClient

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configuração do Lifespan (Inicialização e Encerramento) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 1. Configuração do Modelo Gemini ---
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
    
    genai.configure(api_key=google_api_key)
    # Armazena o modelo no estado da aplicação
    app.state.model = genai.GenerativeModel('gemini-2.5-flash-lite') # Use o modelo que preferir
    print("Modelo Gemini carregado.")

    # --- 2. Configuração do Cliente Supabase ---
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Variáveis de ambiente SUPABASE_URL ou SUPABASE_SERVICE_KEY não definidas.")
    
    # --- A CORREÇÃO ESTÁ AQUI ---
    # Nós devemos "await" (esperar) a criação do cliente assíncrono
    app.state.supabase = await create_async_client(supabase_url, supabase_key)
    print("Cliente Supabase (Async) conectado.")
    
    yield
    
    # Código de limpeza (se necessário)
    print("Aplicação encerrada.")
    # Você poderia adicionar 'await app.state.supabase.close()' aqui se necessário.

# --- Criação da Aplicação FastAPI ---
app = FastAPI(
    title="Auxilium IA API",
    description="API para o assistente de IA do app Auxilium com memória persistente.",
    version="0.2.5", # Versão atualizada
    lifespan=lifespan
)

# --- Modelos de Dados (Contrato da API) ---
class ChatRequest(BaseModel):
    pergunta: str  # O frontend envia "pergunta"
    id_usuario: str  # OBRIGATÓRIO: O frontend deve enviar o ID do usuário logado
    # Opcional: O frontend pode enviar para continuar uma conversa específica
    id_sessao: str | None = None 

    class Config:
        populate_by_name = True

class ChatResponse(BaseModel):
    resposta: str # Devolvemos a "resposta"
    id_sessao: str # Devolve o ID para o frontend guardar

# --- Endpoints da API ---
@app.post("/chat", response_model=ChatResponse)
async def handle_chat(chat_request: ChatRequest, request: Request):
    """
    Recebe uma mensagem do usuário, busca o histórico no Supabase,
    envia para o Gemini e salva a nova interação no Supabase.
    """
    try:
        # Pega o modelo e o cliente Supabase do estado da aplicação
        model = request.app.state.model
        supabase: AsyncClient = request.app.state.supabase
        
        # Pega os dados do request
        id_usuario = chat_request.id_usuario
        id_sessao = chat_request.id_sessao
        pergunta_usuario = chat_request.pergunta
        
        # 1. Preparar a sessão de chat
        history = []
        
        # Se não houver um ID de sessão, cria um novo
        if not id_sessao:
            id_sessao = str(uuid.uuid4())
        else:
            # Se houver um ID, busca o histórico no Supabase
            response = await supabase.table('interacao_ia') \
                               .select('pergunta, resposta') \
                               .eq('id_sessao', id_sessao) \
                               .eq('id_usuario', id_usuario) \
                               .order('data_interacao', desc=False) \
                               .execute()
            
            if response.data:
                for row in response.data:
                    history.append({"role": "user", "parts": [{"text": row['pergunta']}]})
                    history.append({"role": "model", "parts": [{"text": row['resposta']}]})

        # 2. Inicia o chat com o Gemini (com ou sem histórico)
        chat_session = model.start_chat(history=history)
        
        # 3. Envia a nova mensagem para o Gemini (de forma assíncrona)
        ai_response = await chat_session.send_message_async(pergunta_usuario)
        
        # 4. Salva a nova interação no Supabase
        insert_data = {
            'id_usuario': id_usuario,
            'id_sessao': id_sessao,
            'pergunta': pergunta_usuario,
            'resposta': ai_response.text,
            'tipo_ia': 'chat' # Preenchendo a coluna tipo_ia
        }
        
        await supabase.table('interacao_ia').insert(insert_data).execute()
        
        # 5. Retorna a resposta
        return ChatResponse(resposta=ai_response.text, id_sessao=id_sessao)

    except Exception as e:
        # Log do erro detalhado no console para depuração
        error_message = f"Ocorreu um erro interno: {e}"
        print(error_message)
        # Retorna uma mensagem de erro mais informativa
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/")
def read_root():
    return {"status": "Auxilium IA API está funcionando com Supabase!"}