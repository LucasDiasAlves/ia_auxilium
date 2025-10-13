import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carrega a chave da API
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Lista todos os modelos disponíveis
print("📋 Modelos disponíveis:\n")

for model in genai.list_models():
    print(f"🧩 Nome: {model.name}")
    print(f"   • Descrição: {getattr(model, 'display_name', '(sem descrição)')}")
    print(f"   • Suporta generateContent: {'generateContent' in model.supported_generation_methods}")
    print(f"   • Métodos suportados: {model.supported_generation_methods}\n")
