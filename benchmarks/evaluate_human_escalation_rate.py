import datetime
import json
import os
import re
from langsmith import Client
import pandas as pd
from src.config.settings import settings

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

folder_path = os.path.join(root_dir, "metrics")
file_path = os.path.join(folder_path, "calculate_human_escalation_rate.json")

client = Client(api_key=settings.langchain_api_key)


PROJECT_NAME = "kalemna_customer_service"

traces  = client.list_runs(project_name=PROJECT_NAME,
    is_root=True,

                           filter='and(eq(name, "LangGraph"), eq(status, "success"))'
                           , limit=None ,
                           start_time=datetime.datetime(2025, 1, 1))


all_runs =[]
for  run in traces:

    all_runs.append({'user_query': run.inputs.get('user_query') ,
                     'action' : run.outputs.get('action') ,
                     'final_response' : run.outputs.get('messages')[-1].get('content') })

eval_data = pd.DataFrame(all_runs)



def is_transfered_to_human(row):

    if row['action'] == 'human_escalation':
        return 1



    text = row['final_response']


    pattern = r"(?i)\bhuman\b|\btransfer(r?ing)?\b|ممثلي خدمة العملاء"

    matches = re.findall(pattern, text)

    if matches:
        return 1


    return 0


eval_data['is_transfered_to_human'] = eval_data.apply(lambda x: is_transfered_to_human(x), axis=1)


eval_data.to_csv('human_escalation_rate.csv', index=False)

rate = ((eval_data['is_transfered_to_human'] == 1).sum() / len(eval_data))* 100

data = {'human_escalation_rate' : rate  ,
        'task_completion' : 100 - rate}

with open(file_path, 'w') as outfile:
    json.dump(data, outfile , indent=4)

print(f"data saved to {file_path} successfully")