import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["POLIGPT_BASE_URL"],
    api_key=os.environ["POLIGPT_API_KEY"],
)

models = client.models.list()

for model in models.data:
    print(model.id)