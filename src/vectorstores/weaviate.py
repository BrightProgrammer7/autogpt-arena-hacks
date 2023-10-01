import os
import weaviate
from dotenv import load_dotenv


auth_config = weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY"))

client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=auth_config
)
 