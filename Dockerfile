FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime

WORKDIR /kalemna_app

COPY requirements.txt .

RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn","src.presentation.api.app:app","--host", "0.0.0.0" ,"--port","8000"]


