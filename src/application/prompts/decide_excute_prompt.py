from langsmith import Client

client = Client()

decide_execute_prompt = client.pull_prompt("decide_execute_prompt:staging")
