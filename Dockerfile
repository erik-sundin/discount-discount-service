FROM python:3.9-alpine
WORKDIR /discount_service
RUN apk add --no-cache gcc musl-dev linux-headers build-base postgresql-dev 
COPY req.txt req.txt
RUN pip install -r req.txt
EXPOSE 8000
CMD ["uvicorn", "--host", "0.0.0.0", "discount_service.asgi:asgi_app"]