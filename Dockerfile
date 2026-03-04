FROM python:3.11.7-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN datamodel-codegen \
    --input src/main/resources/openapi/openapi.yaml \
    --output src/generated.py \
    --input-file-type openapi \
    --output-model-type pydantic_v2.BaseModel \
    --use-annotated \
    --target-python-version 3.11

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
