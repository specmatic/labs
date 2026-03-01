FROM python:3.14-alpine

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY processor.py /app/processor.py

CMD ["python", "processor.py"]
