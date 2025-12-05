#gemini-2.5-flash-lite
# --- main.py ---
import os
import json
import google.generativeai as genai
from uuid import uuid4, UUID
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from supabase import create_async_client, AsyncClient
import fitz  # PyMuPDF

print(">>> MAIN CARREGADO EM:", os.path.abspath(__file__))


# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações Auxiliares ---
EMBEDDING_MODEL = "models/text-embedding-004" 

# --- Configuração do Lifespan (Inicialização e Encerramento) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Configuração do Modelo Gemini
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
    
    genai.configure(api_key=google_api_key)
    
    # Armazena o modelo de chat no estado da aplicação
    app.state.model = genai.GenerativeModel('gemini-2.5-flash-lite')
    print("Modelo Gemini (Chat) carregado.")

    # 2. Configuração do Cliente Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Variáveis de ambiente SUPABASE_URL ou SUPABASE_SERVICE_KEY não definidas.")
    
    # Cria o cliente Supabase (aguardando a conexão assíncrona corretamente)
    app.state.supabase = await create_async_client(supabase_url, supabase_key)
    print("Cliente Supabase (Async) conectado.")
    
    yield
    
    # Código de limpeza (se necessário)
    print("Aplicação encerrada.")

# --- Criação da Aplicação FastAPI ---
app = FastAPI(
    title="Auxilium IA API (RAG + Voz)",
    description="API com suporte a RAG, Chat Contextual e Simulador de Entrevistas.",
    version="0.6.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # pode restringir depois
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modelos de Dados (Chat) ---
class ChatRequest(BaseModel):
    pergunta: str
    id_usuario: UUID
    id_sessao: UUID | None = None 
    class Config:
        populate_by_name = True

class ChatResponse(BaseModel):
    resposta: str
    id_sessao: UUID

# --- Modelos de Dados (Entrevista) ---
class InterviewRequest(BaseModel):
    topico: str # Ex: "React Junior", "História do Brasil"
    id_usuario: UUID
    dificuldade: str = "Média" # Fácil, Média, Difícil

class InterviewResponse(BaseModel):
    id_entrevista: str
    perguntas: list[str]

class FeedbackRequest(BaseModel):
    id_entrevista: UUID
    id_usuario: UUID
    transcript: str # O texto completo da conversa vinda do Vapi

# --- Funções Auxiliares ---
def get_embedding(text: str):
    """Gera o vetor numérico para um texto (documento) usando o Gemini."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']

def get_query_embedding(text: str):
    """Gera o vetor para a PERGUNTA (task_type diferente para otimizar busca)."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']

# --- Endpoint de Upload de PDF (RAG - Ingestão) ---
@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...), 
    id_usuario: UUID = Form(...), # Recebe o ID via formulário
    request: Request = None
):
    """
    Lê PDF, quebra em pedaços (chunks), vetoriza e salva na tabela 'documentos_contexto'.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Apenas arquivos PDF são permitidos.")

    supabase: AsyncClient = request.app.state.supabase
    
    try:
        # 1. Ler o PDF da memória
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        
        full_text = ""
        for page in doc:
            full_text += page.get_text()
            
        # 2. Chunking (Dividir o texto em pedaços menores)
        chunk_size = 1000
        overlap = 200
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size - overlap)]

        # 3. Processar cada pedaço
        count = 0
        for chunk in chunks:
            if len(chunk.strip()) < 50: continue 

            # Gera o vetor (Embedding)
            embedding = get_embedding(chunk)
            
            # Prepara dados para salvar
            data = {
                "user_id": str(id_usuario), 
                "conteudo": chunk,
                "embedding": embedding,
                "metadata": {"filename": file.filename}
            }
            
            # Salva no Supabase (Tabela documentos_contexto sem acento)
            await supabase.table("documentos_contexto").insert(data).execute()
            count += 1
            
        return {
            "status": "sucesso", 
            "chunks_processados": count, 
            "arquivo": file.filename
        }

    except Exception as e:
        print(f"Erro no upload: {e}")
        raise HTTPException(500, f"Erro ao processar documento: {str(e)}")

# --- Endpoint de Chat (RAG - Recuperação e Geração) ---
@app.post("/chat", response_model=ChatResponse)
async def handle_chat(chat_request: ChatRequest, request: Request):
    """
    Fluxo RAG Híbrido:
    1. Busca contexto relevante no Supabase.
    2. Se encontrar contexto, usa. Se não, usa conhecimento geral.
    3. Gera resposta e salva.
    """
    try:
        model = request.app.state.model
        supabase: AsyncClient = request.app.state.supabase
        
        id_usuario = chat_request.id_usuario
        # Se não vier sessão, cria uma nova
        id_sessao = chat_request.id_sessao or uuid4()
        pergunta = chat_request.pergunta

        # --- PASSO RAG 1: Buscar Contexto Relevante ---
        query_vector = get_query_embedding(pergunta)
        
        # Chama a função RPC 'match_documents' no Supabase
        rpc_params = {
            "query_embedding": query_vector,
            "match_threshold": 0.5, 
            "match_count": 4,       
            "filter_user_id": str(id_usuario) # SEGURANÇA: Filtra pelo usuário
        }
        response_rag = await supabase.rpc("match_documents", rpc_params).execute()
        
        # Monta o texto do contexto
        contexto_texto = ""
        if response_rag.data:
            contexto_texto = "\n\n".join([item['conteudo'] for item in response_rag.data])
        
        # --- PASSO RAG 2: Montar o Prompt HÍBRIDO ---
        prompt_sistema = f"""
        Você é o Auxilium, um assistente acadêmico inteligente.
        
        INSTRUÇÕES DE RESPOSTA:
        1. Analise o CONTEXTO abaixo (trechos de documentos do aluno).
        2. Se a resposta para a pergunta estiver no contexto, use-o como sua fonte principal e cite o documento se possível.
        3. Se a resposta NÃO estiver no contexto (ou se o contexto for vazio), use seu próprio conhecimento para responder de forma completa e útil.
        4. Mantenha um tom educacional e prestativo.
        
        CONTEXTO ENCONTRADO NO BANCO DE DADOS:
        {contexto_texto if contexto_texto else "Nenhum documento relevante encontrado para este tópico."}
        
        PERGUNTA DO ALUNO:
        {pergunta}
        """

        # --- PASSO RAG 3: Recuperar Histórico e Gerar Resposta ---
        history = []
        
        # Busca histórico anterior no Supabase
        # ATENÇÃO: Certifique-se de que a coluna no banco se chama 'created_at'
        response_hist = await supabase.table('interacao_ia') \
                           .select('pergunta, resposta') \
                           .eq('id_sessao', str(id_sessao)) \
                           .eq('id_usuario', str(id_usuario)) \
                           .order('data_interacao', desc=False) \
                           .execute() 
        
        if response_hist.data:
            for row in response_hist.data:
                history.append({"role": "user", "parts": [{"text": row['pergunta']}]})
                history.append({"role": "model", "parts": [{"text": row['resposta']}]})

        # Inicia o chat (com histórico)
        chat_session = model.start_chat(history=history)
        
        # Envia o prompt enriquecido com o contexto RAG
        ai_response = await chat_session.send_message_async(prompt_sistema)

        # --- PASSO RAG 4: Salvar a Interação ---
        # Certifique-se de que a tabela 'interacao_ia' e colunas 'tipo_ia', 'id_usuario' existem sem acento
        await supabase.table('interacao_ia').insert({
            'id_usuario': str(id_usuario),
            'id_sessao': str(id_sessao),
            'pergunta': pergunta,
            'resposta': ai_response.text,
            'tipo_ia': 'rag_chat' 
        }).execute()

        return ChatResponse(resposta=ai_response.text, id_sessao=id_sessao)

    except Exception as e:
        print(f"Erro no chat: {e}")
        # Retorna erro 500 com detalhes para facilitar o debug
        raise HTTPException(status_code=500, detail=str(e))

# ... (Todo o código anterior permanece igual até a linha 237) ...

# --- NOVOS ENDPOINTS PARA ENTREVISTA POR VOZ (CORRIGIDOS) ---

@app.post("/interview/generate", response_model=InterviewResponse)
async def generate_interview(request_data: InterviewRequest, request: Request):
    """
    Gera perguntas usando o 'JSON Mode' do Gemini para evitar erros de formatação.
    """
    try:
        model = request.app.state.model
        supabase: AsyncClient = request.app.state.supabase

        # Prompt ajustado
        prompt = f"""
        Atue como um entrevistador técnico sênior.
        Tarefa: Criar 5 perguntas técnicas sobre: {request_data.topico}.
        Nível de Dificuldade: {request_data.dificuldade}.
        
        Requisito: Retorne APENAS um array JSON de strings contendo as perguntas.
        Exemplo: ["Pergunta 1?", "Pergunta 2?", ...]
        """
        
        # AQUI ESTA A CORREÇÃO: Forçamos o tipo de resposta para JSON
        response = await model.generate_content_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Agora o texto é garantido ser JSON válido
        perguntas_lista = json.loads(response.text)

        # Salva no Supabase
        data = {
            "id_usuario": str(request_data.id_usuario),
            "topico": request_data.topico,
            "dificuldade": request_data.dificuldade,
            "perguntas": perguntas_lista
        }
        
        res_db = await supabase.table("entrevistas").insert(data).execute()
        
        # Tratamento de erro caso o Supabase não retorne dados (segurança extra)
        if not res_db.data:
             raise HTTPException(status_code=500, detail="Erro ao salvar entrevista no banco.")
             
        id_entrevista = res_db.data[0]['id']

        return InterviewResponse(id_entrevista=id_entrevista, perguntas=perguntas_lista)

    except Exception as e:
        print(f"Erro ao gerar entrevista: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/interview/feedback")
async def generate_feedback(request_data: FeedbackRequest, request: Request):
    """
    Gera feedback usando o 'JSON Mode' do Gemini.
    """
    try:
        model = request.app.state.model
        supabase: AsyncClient = request.app.state.supabase

        prompt = f"""
        Analise o seguinte transcript de uma entrevista técnica.
        
        TRANSCRIPT:
        {request_data.transcript}
        
        Gere um objeto JSON com os seguintes campos:
        - nota (integer, 0 a 100)
        - pontos_fortes (array de strings)
        - pontos_melhoria (array de strings)
        - veredito_final (string)
        """
        
        # CORREÇÃO: Forçando JSON Mode aqui também
        response = await model.generate_content_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        analise_json = json.loads(response.text)

        # Salva o feedback
        data = {
            "id_entrevista": str(request_data.id_entrevista),
            "id_usuario": str(request_data.id_usuario),
            "transcript": request_data.transcript,
            "analise_json": analise_json
        }
        
        await supabase.table("feedbacks").insert(data).execute()

        return analise_json

    except Exception as e:
        print(f"Erro ao gerar feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "Auxilium IA API (RAG Híbrido + Voz) está funcionando!"}