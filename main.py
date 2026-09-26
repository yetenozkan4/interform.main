import os
from groq import Groq

# API anahtarını otomatik okur (veya doğrudan içine yazabilirsin)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Modelleri listele ve ekrana yazdır
models = client.models.list()
print("Kullanılabilir Modeller:")
for model in models.data:
    print(f"- {model.id}")
