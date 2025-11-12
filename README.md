# Auxilium IA API

**Versão 0.3.0**

API para o assistente de Inteligência Artificial do aplicativo Auxilium. Este é um microserviço em Python (FastAPI) que se conecta aos modelos Google Gemini para processamento de linguagem e ao Supabase para persistência de dados.

## 📝 Sumário

- [Propósito](#-propósito)
- [Como Funciona (Arquitetura)](#-como-funciona-arquitetura)
- [Fase do Projeto](#-fase-do-projeto)
- [Próximos Passos](#-próximos-passos)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Como Executar o Projeto](#-como-executar-o-projeto)
- [Endpoints da API](#-endpoints-da-api)
- [Scripts Utilitários](#-scripts-utilitários)

---

### 🎯 Propósito

A função deste projeto é servir como o *backend* (a lógica do servidor) para o assistente de IA do app Auxilium. Ele expõe uma API RESTful que:
1.  Recebe mensagens de um usuário.
2.  Processa as mensagens usando o modelo `gemini-2.5-flash-lite` do Google.
3.  Usa o **Supabase** para persistir o histórico da conversa.
4.  Retorna a resposta da IA, mantendo o contexto de sessões anteriores.

### ⚙️ Como Funciona (Arquitetura)

Este serviço funciona como um cérebro de IA com memória externa. O fluxo de dados para o chat é o seguinte:



1.  **Requisição:** O App (Frontend) envia um JSON para o endpoint `POST /chat` contendo `pergunta`, `id_usuario` e um `id_sessao` (que pode ser `null` se for uma nova conversa).
2.  **Validação:** A API (FastAPI/Pydantic) valida os dados. `id_usuario` e `id_sessao` são validados como `UUID`s.
3.  **Busca de Histórico:** Se um `id_sessao` é fornecido, o servidor consulta o **Supabase** na tabela `interacao_ia` e busca todas as perguntas e respostas anteriores para aquela sessão e usuário.
4.  **Processamento:** O histórico é montado e enviado ao **Gemini** junto com a nova pergunta.
5.  **Geração:** O Gemini gera a resposta (`ai_response`).
6.  **Persistência:** O servidor salva a nova `pergunta` do usuário e a `resposta` da IA como uma **nova linha** na tabela `interacao_ia` do Supabase.
7.  **Resposta:** A API retorna a `resposta` e o `id_sessao` para o App.

### 🚀 Fase do Projeto

**Fase: Funcional (Memória Persistente Concluída)**

O projeto está estável e funcional. A Prova de Conceito (MVP) da memória de chat está completa.

**Última Atualização (v0.2.6 -> v0.3.0):**
* **Memória Persistente:** A API agora está 100% integrada com o Supabase. A memória do chat não é mais perdida quando o servidor reinicia.
* **Conexão Assíncrona:** Corrigido o bug de inicialização (`'coroutine' object has no attribute 'table'`). A API agora usa `create_async_client` corretamente com `await` no `lifespan` do FastAPI.
* **Validação de UUID:** A API agora é robusta e rejeita requisições (com erro 422) se `id_usuario` ou `id_sessao` não forem UUIDs válidos, protegendo o banco de dados contra entradas malformadas.

### 🏁 Próximos Passos

Agora que a fundação (chat e memória) está sólida, podemos focar nas funcionalidades de IA mais avançadas:

1.  **RAG (Retrieval-Augmented Generation):**
    * **Objetivo:** Fazer a IA responder perguntas com base em documentos da faculdade (PDFs, docs).
    * **Ação:** Criar novos endpoints (ex: `POST /upload-document`) e usar um Banco deDados Vetorial (como o pgvector do Supabase) para armazenar e consultar o conteúdo dos materiais.

2.  **Chat de Voz (Entrevistas Simuladas):**
    * **Objetivo:** Implementar os requisitos `RF016` e `RF017`.
    * **Ação:**
        * Criar endpoints (`POST /interview/generate` e `POST /interview/feedback`).
        * Usar o Gemini para gerar perguntas (salvar na tabela `interviews`).
        * Integrar com um serviço de voz (como Vapi) no frontend.
        * Receber o *transcript* da entrevista de voz, analisá-lo com o Gemini e salvar na tabela `feedbacks`.

3.  **Funções Multimodais:**
    * **Objetivo:** Permitir que o usuário envie imagens (ex: foto de um exercício).
    * **Ação:** Criar um endpoint que aceite upload de imagens e o envie ao Gemini (que é multimodal) para análise.

### 🛠️ Tecnologias Utilizadas

-   **Python 3.10+**
-   **FastAPI:** Para a construção da API.
-   **Uvicorn:** Servidor ASGI para rodar a aplicação.
-   **Google Generative AI (`gemini-1.5-flash-latest`):** O cérebro da IA.
-   **Supabase (`supabase-py` v2):** Para persistência de dados (histórico de chat).
-   **Pydantic:** Para validação de dados.
-   **python-dotenv:** Para gerenciamento de variáveis de ambiente.

### ⚙️ Como Executar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone <url-do-seu-repositorio>
    cd ia_auxilium
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux / macOS
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install "fastapi[all]" uvicorn python-dotenv google-generativeai "supabase[async]"
    ```
    (Após instalar, atualize seu `requirements.txt`: `pip freeze > requirements.txt`)

4.  **Configure as chaves da API:**
    Crie um arquivo chamado `.env` na raiz do projeto. Ele **precisa** destas 3 chaves:
    ```
    GOOGLE_API_KEY="sua_chave_google_aqui"
    SUPABASE_URL="url_do_seu_projeto_supabase_aqui"
    SUPABASE_SERVICE_KEY="sua_chave_service_role_secreta_aqui"
    ```

5.  **Execute o servidor:**
    ```bash
    uvicorn main:app --reload
    ```
    A API estará disponível em `http://127.0.0.1:8000`.

### 🔗 Endpoints da API

#### GET /

Verifica se a API está em execução.

**Exemplo de Resposta (JSON):**
```json
{ "status": "Auxilium IA API está funcionando com Supabase!" }