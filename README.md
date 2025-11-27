# Auxilium IA API  
**Versão 0.6.0 — RAG Híbrido + Suporte a Voz**

API desenvolvida para o assistente de Inteligência Artificial da plataforma **Auxilium**.  
Este microserviço, implementado em **Python (FastAPI)**, atua como o núcleo lógico da aplicação, integrando:

- Google Gemini → Inferência cognitiva
- Supabase → Persistência de dados e memória vetorial
- Vapi → Infraestrutura para agentes de voz

---

## 📝 Sumário Executivo

- 🎯 Objetivo Geral  
- ⚙️ Arquitetura do Sistema  
- 🚀 Funcionalidades Implementadas  
- 🛠️ Stack Tecnológico  
- ⚙️ Instruções para Execução Local  
- 📱 Guia de Integração do Frontend  
- 🔗 Especificação dos Endpoints  
- 🌐 Procedimentos de Implantação  

---

## 🎯 Objetivo Geral

Este projeto constitui o **backend inteligente** da plataforma Auxilium, indo além de simples interações textuais e abrangendo:

- Gerenciamento de sessões de estudo.
- Leitura, indexação e interpretação de documentos PDF.
- Simulações de entrevistas técnicas por voz com avaliação automatizada.

---

## ⚙️ Arquitetura do Sistema

A aplicação opera sobre três fluxos principais:

### 1. Chat Acadêmico (RAG Híbrido)

**Fluxo:**

- Entrada: Pergunta do usuário.
- Busca semântica nos PDFs armazenados (Supabase + embeddings).
- Prioridade de resposta baseada nos documentos.
- Fallback para conhecimento geral quando necessário.
- Armazenamento completo do histórico para preservação do contexto.

---

### 2. Ingestão e Processamento de Documentos

**Fluxo:**

- Upload de arquivos PDF.
- Leitura e fragmentação (chunking).
- Geração de vetores matemáticos.
- Armazenamento no Supabase para consultas futuras.

---

### 3. Simulador de Entrevistas Técnicas por Voz

**Fluxo:**

- Geração automática de pauta técnica.
- Integração com Vapi no Frontend (voz).
- Recebimento da transcrição da entrevista.
- Correção automática e geração de nota.

> ⚠️ A API não processa áudio diretamente, somente inteligência e avaliação.

---

## 🚀 Funcionalidades Implementadas

- ✅ Persistência de memória no Supabase  
- ✅ RAG híbrido com PDFs  
- ✅ Extração de texto com PyMuPDF  
- ✅ Geração automática de entrevistas  
- ✅ Avaliação técnica com nota e feedback qualitativo  

---

## 🛠️ Stack Tecnológico

| Tecnologia      | Descrição |
|----------------|-----------|
| Python 3.10+   | Linguagem base |
| FastAPI        | Framework de API |
| Google Gemini  | IA e embeddings |
| Supabase       | Banco relacional + vetorial |
| PyMuPDF        | Leitura de PDFs |
| Pydantic       | Validação de dados |

---

## ⚙️ Instruções para Execução Local

### 1. Clonagem e Instalação

```bash
git clone <url-do-repositorio>
cd ia_auxilium

python -m venv venv

# Ativação do ambiente virtual:
# Windows
.\venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Instalação das dependências
pip install "fastapi[all]" uvicorn python-dotenv google-generativeai supabase pymupdf python-multipart
```


---

### 2. Configuração do .env

## Crie o arquivo .env na raiz:

```bash
GOOGLE_API_KEY="sua_chave_google"
SUPABASE_URL="url_do_projeto"
SUPABASE_SERVICE_KEY="chave_secreta"
```

---

### 3. Preparação do Supabase

## Criar as tabelas:

- interacao_ia
- documentos_contexto
- entrevistas
- feedbacks

---

### 4. Execução do Servidor

```bash
uvicorn main:app --reload
```

# Acesse:
```bash
http://127.0.0.1:8000/docs
```

---

### 📱 Integração do Frontend
## 1. Instalação do SDK Vapi
```bash
npm install @vapi-ai/web
```
---

## 2. Fluxo da Entrevista
# Obter perguntas:
```bash
npm install @vapi-ai/web
```
Salvar:

- id_entrevista
- Lista de perguntas

# Iniciar chamada de voz:
```bash
vapi.start({
  systemPrompt: perguntas
})
```
# Enviar feedback:
```bash
POST /interview/feedback
```

Payload:
- id_entrevista
- transcript

Resposta:
- Nota (0–100)
- Análise técnica
- Sugestões de melhoria

---

### 🔗 Endpoints
## 📄 Documentos e Chat

```POST /upload```

Upload de documentos PDF para RAG.
Entrada: PDF, id_usuario

```POST /chat```

Chat com memória e documentos contextuais.
Entrada: pergunta, id_usuario, id_sessao (opcional)

### 🎙️ Entrevistas
```POST /interview/generate```

Gera roteiro técnico.
Entrada:

- topico
- dificuldade

Saída:
- Perguntas
- id_entrevista

```POST /interview/feedback```

# Corrige a entrevista.

Entrada:
- id_entrevista
- transcript

Saída:
- Nota
- Pontos fortes
- Melhorias

---

### 🌐 Deployment
## Opção A — Ngrok (Teste local)
```ngrok http 8000```

Usar a URL fornecida para integração externa.

## Opção B — Render (Produção)
# Build:

``` pip install -r requirements.txt ```


# Start:

``` uvicorn main:app --host 0.0.0.0 --port $PORT ```


Configurar variáveis:

- GOOGLE_API_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_KEY