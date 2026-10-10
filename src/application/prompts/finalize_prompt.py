from langsmith import Client

client = Client()

FINALIZE_PROMPT = client.pull_prompt("finalize_prompt")
