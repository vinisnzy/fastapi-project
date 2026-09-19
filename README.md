# FastAPI Project

Uma API de piadas criada como continuação do tutorial introdutório [**Learn FastAPI In Only 10 Minutes**](https://youtu.be/v6G_JJK01zU), do canal **Indently**, para aprender FastAPI. O projeto amplia o exemplo com persistência de dados, autenticação e uma organização em camadas.

## Stack

**Python 3.14** · **FastAPI** · **Pydantic** · **SQLAlchemy** · **PostgreSQL** · **Alembic** · **uv** · **Docker Compose**

## Funcionalidades

- Cadastro e login de usuários com JWT, renovação de tokens e logout.
- Criação, listagem paginada, consulta, edição e exclusão de piadas; as rotas de piadas exigem autenticação.
- Sorteio de piada, com filtro opcional por tag.
- Documentação interativa da API em `/docs`.

## Arquitetura

As requisições passam por **routers**, que usam **schemas** para validar os dados e **services** para aplicar as regras de negócio. Os **repositories** acessam o PostgreSQL por meio dos **models** e do SQLAlchemy; o Alembic gerencia as migrações. O código da aplicação fica em `src/fastapi_project/`.

## Como rodar

Pré-requisitos: **Python 3.14**, **uv** e **Docker Compose**.

1. Copie o arquivo de configuração e defina um valor próprio para `JWT_SECRET` em `.env`:

   ```bash
   cp .env.example .env
   ```

2. Instale as dependências e inicie o banco de dados:

   ```bash
   uv sync
   docker compose up -d --wait db
   ```

3. Aplique as migrações e inicie a API:

   ```bash
   uv run alembic upgrade head
   uv run uvicorn fastapi_project.main:create_app --factory --reload
   ```

Acesse **http://127.0.0.1:8000/docs** para explorar e testar os endpoints.
