From python:3.10-slim

WORKDIR /kalemna_app

COPY requirements.txt .

RUN pip install -r requirements.txt

copy . .

CMD ["uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

