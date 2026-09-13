FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime

WORKDIR /kalemna_app

COPY requirements.txt .


FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime AS runner

WORKDIR /kalemna_app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


COPY . .

EXPOSE 8000

CMD ["uvicorn","src.presentation.api.app:app","--host", "0.0.0.0" ,"--port","8000"]


