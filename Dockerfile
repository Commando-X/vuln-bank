FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install wrapper SDK from vendor
COPY vendor/swigdojo-target /tmp/swigdojo-target
RUN pip install --no-cache-dir /tmp/swigdojo-target && rm -rf /tmp/swigdojo-target

RUN mkdir -p static/uploads templates data

COPY . .

RUN chmod 777 static/uploads data

EXPOSE 5000

CMD ["python", "wrapper.py"]
