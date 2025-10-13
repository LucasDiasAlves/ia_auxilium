# Auxilium IA API

API para o assistente de Inteligência Artificial do aplicativo Auxilium, utilizando o modelo **gemini-2.5-flash-lite-preview-06-17.**

## 📝 Sumário

- [Propósito](#-propósito)
- [Fase do Projeto](#-fase-do-projeto)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Como Executar o Projeto](#-como-executar-o-projeto)
- [Endpoints da API](#-endpoints-da-api)
- [Scripts Utilitários](#-scripts-utilitários)

---

### 🎯 Propósito

A função deste projeto é servir como o *backend* (a lógica do servidor) para um assistente de IA. Ele expõe uma API RESTful que recebe mensagens de um usuário, as processa usando o modelo de linguagem generativa **gemini-2.5-flash-lite-preview-06-17** do Google e retorna a resposta da IA, mantendo o histórico da conversa para dar contexto às interações.

### 🚀 Fase do Projeto

**Fase: Inicial / Prova de Conceito (MVP - Minimum Viable Product)**

O projeto está em sua fase inicial, mas já é funcional. O que foi implementado:

- **Servidor API:** Utilizando FastAPI, um framework web moderno e rápido para Python.
- **Integração com Gemini:** Configuração e comunicação com o modelo `gemini-2.5-flash-lite-preview-06-17`.
- **Gerenciamento de Sessão:** Capacidade de manter conversas separadas e com histórico. As sessões são armazenadas em memória, o que significa que são perdidas se o servidor for reiniciado.
- **Estrutura Básica:** Definição de modelos de dados para requisições e respostas e tratamento básico de erros.

**Próximos Passos Sugeridos:**
- Implementar um banco de dados (como PostgreSQL ou MongoDB) para persistir o histórico das conversas.
- Adicionar autenticação e autorização para proteger a API.
- Criar um sistema de logging mais robusto.
- Implementar testes automatizados.

### 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **FastAPI:** Para a construção da API.
- **Pydantic:** Para validação de dados.
- **Google Generative AI (gemini-2.5-flash-lite-preview-06-17):** O cérebro da IA.
- **Uvicorn:** Servidor ASGI para rodar a aplicação FastAPI.
- **python-dotenv:** Para gerenciamento de variáveis de ambiente.

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

3.  **Instale as dependências do projeto:**
    O arquivo `requirements.txt` já deve estar no projeto. Com o ambiente virtual ativado, execute:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a chave da API:**
    Crie um arquivo chamado `.env` na raiz do projeto e adicione sua chave da API do Google AI Studio, como no exemplo abaixo:
    ```
    GOOGLE_API_KEY="sua_chave_aqui"
    ```

5.  **Execute o servidor:**
    ```bash
    uvicorn main:app --reload
    ```
    A API estará disponível em `http://127.0.0.1:8000`.

### 🔗 Endpoints da API

#### GET /

Verifica se a API está em execução. Útil para testes de saúde (*health checks*).

**Exemplo de Resposta:**
```json
{ "status": "Auxilium IA API está funcionando!" }
```

#### POST /chat

Inicia uma nova conversa ou continua uma existente.

**Exemplo de Requisição (cURL):**
```bash
# Para iniciar uma nova conversa
curl -X POST "http://127.0.0.1:8000/chat" -H "Content-Type: application/json" -d '{"message": "Olá, qual o seu nome?"}'

# Para continuar uma conversa (use o session_id retornado)
curl -X POST "http://127.0.0.1:8000/chat" -H "Content-Type: application/json" -d '{"message": "Do que estávamos falando?", "session_id": "uuid-da-sessao-aqui"}'
```

**Exemplo de Resposta:**
```json
{
  "reply": "Eu sou um modelo de linguagem grande, treinado pelo Google.",
  "session_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

###  Scripts Utilitários

Esta seção descreve scripts auxiliares que podem ser usados durante o desenvolvimento.

#### `listar_modelos.py`

Este script se conecta à API do Google e lista todos os modelos de IA generativos disponíveis para a sua chave de API.

**Utilidade:**
É útil para descobrir novos modelos ou verificar os nomes exatos dos modelos que você pode usar no projeto (por exemplo, `gemini-1.5-flash-latest`, `gemini-1.5-pro-latest`, etc.).

**Como Executar:**
Certifique-se de que seu ambiente virtual está ativado e o arquivo `.env` está configurado.
```bash
python listar_modelos.py
