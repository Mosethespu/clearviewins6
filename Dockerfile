FROM python:3.13

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# For iterative development, mount source code with Podman Compose
COPY . .

EXPOSE 5000

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
