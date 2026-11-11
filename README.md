# AuthGuard

API desenvolvida em Python com FastAPI para cadastro seguro de usuários. O projeto aplica práticas de validação de dados e proteção de credenciais, utilizando hash Argon2id para armazenar senhas com segurança.

## Tecnologias

- Python
- FastAPI e Uvicorn
- SQLAlchemy e SQLite
- pwdlib com Argon2
- Pytest e HTTPX

## Funcionalidades implementadas

- Cadastro de usuários pelo endpoint `POST /register`.
- Validação de endereço de e-mail.
- Rejeição de senhas com menos de 8 caracteres.
- Verificação de e-mails já cadastrados.
- Armazenamento de senhas com hash Argon2id.
- Respostas de cadastro sem exposição da senha ou do hash.

> Os recursos de login e bloqueio temporário de conta fazem parte dos requisitos do projeto e serão documentados como implementados após sua integração à API.

## Estrutura do projeto

```text
AuthGuard/
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── security.py
├── tests/
│   └── test_register.py
├── requirements.txt
└── README.md
```

## Pré-requisitos

- Python 3.10 ou superior
- pip

## Instalação

1. Clone o repositório e acesse a pasta do projeto.
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Executar a API

Na pasta raiz do projeto, execute:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Documentação interativa

Com a API em execução, acesse [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) para visualizar e testar os endpoints disponíveis.

## Executar os testes

Na pasta raiz do projeto, execute o comando:

```bash
pytest -v
```

O Pytest exibirá o resultado individual de cada teste executado.

## Segurança

As senhas são transformadas em hashes Argon2id antes de serem persistidas no banco de dados. A API não deve retornar credenciais nem hashes nas respostas ao cliente.

## Equipe

Projeto acadêmico desenvolvido em equipe como parte da disciplina de Engenharia de Software.
