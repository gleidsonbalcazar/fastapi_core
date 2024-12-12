# Paneas FastApi CleanArch Project

É um projeto base construído com **FastAPI**, projetado para servir como um esqueleto para o desenvolvimento de APIs modernas, escaláveis e de alta performance. Ele segue as melhores práticas, como Clean Architecture, uso de Pydantic para validação, e integração pronta para banco de dados, autenticação e tarefas em background.

---

## 🚀 Pré-requisitos

Certifique-se de ter os seguintes requisitos instalados:

- [Python 3.11+](https://www.python.org/downloads/)
- [Docker e Docker Compose](https://www.docker.com/)
- [Git](https://git-scm.com/)

---

## ⚙️ Configuração do Projeto

### Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # No Windows: venvScriptsactivate
```

### Instale as dependências

```bash
pip install -r requirements.txt
```

### Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

## Inicialize o banco de dados

Rode as migrações para preparar o banco de dados:

```bash
alembic upgrade head
```

---

## 🏃 Executando a Aplicação

### Localmente

```bash
uvicorn main:app --reload
```

Acesse a API em: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Com Docker

```bash
docker-compose up --build
```

Acesse a API em: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📚 Documentação da API

Acesse a documentação interativa (OpenAPI):

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📂 Estrutura do Projeto

```plaintext
faastapi_core/
├── alembic/                 # Gerenciamento de migrações
├── app/
│   ├── api/                 # Rotas da API
│   ├── core/                # Configurações principais (config.py, segurança, etc.)
│   ├── models/              # Modelos do banco de dados
│   ├── repositories/        # Repositórios para acesso ao banco
│   ├── schemas/             # Schemas de validação Pydantic
│   ├── services/            # Lógica de negócios
│   └── utils/               # Funções auxiliares
├── tests/                   # Testes automatizados
├── .env                     # Variáveis de ambiente
├── docker-compose.yml       # Orquestração Docker
├── Dockerfile               # Configuração Docker
├── main.py                  # Ponto de entrada da aplicação
└── requirements.txt         # Dependências do projeto
```

---

## 🧪 Testes

### Executar testes

```bash
pytest
```

### Relatório de cobertura

```bash
pytest --cov=app --cov-report=term-missing
```

---

## 📦 Deploy

### Deploy com Docker

1. Certifique-se de que todas as configurações estão corretas no `.env`.
2. Execute os seguintes comandos:

```bash
docker-compose up --build
```
