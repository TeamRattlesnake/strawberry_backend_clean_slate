FROM adefe/strawberry_env:v4

WORKDIR /home

COPY . /home

CMD ["uvicorn", "--app-dir", "./src/", "--host", "0.0.0.0", "--port", "14565", "server:app"]
