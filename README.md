# AuthGuard

API de autenticação desenvolvida em Python com FastAPI. O AuthGuard permite cadastrar usuários e realizar autenticação com proteção de credenciais, sessões seguras e bloqueio temporário após tentativas inválidas.

## Tecnologias

- Python 3.10+
- FastAPI e Uvicorn
- SQLAlchemy e SQLite
- Pydantic para validação dos dados
- pwdlib com Argon2id para hash de senhas
- Pytest e HTTPX para testes automatizados

## Funcionalidades

- Cadastro de usuários com validação de e-mail.
- Rejeição de senhas com menos de 8 caracteres.
- Armazenamento de senhas usando Argon2id; a senha original não é persistida.
- Login com credenciais válidas e emissão de token Bearer.
- Consulta do usuário autenticado pelo endpoint `GET /me`.
- Resposta genérica para credenciais inválidas, sem revelar se o e-mail existe.
- Validação do e-mail antes de qualquer consulta ao banco de dados.
- Bloqueio por 10 minutos após 3 tentativas consecutivas de autenticação inválidas.
- Respostas da API sem exposição de senha, hash ou token armazenado.

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Verifica se a API está funcionando |
| POST | `/register` | Cadastra um usuário |
| POST | `/login` | Autentica e retorna um token Bearer |
| GET | `/me` | Retorna os dados do usuário autenticado |

A documentação interativa dos endpoints fica disponível em `/docs` quando a API está em execução.

## Estrutura do projeto

```text
AuthGuard/
├── app/
│   ├── database.py
│   ├── lockout.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── session_auth.py
├── tests/
│   ├── test_api.py
│   ├── test_email_validation.py
│   ├── test_lockout.py
│   ├── test_login.py
│   └── test_register.py
├── requirements.txt
└── README.md
```

## Pré-requisitos

- Python 3.10 ou superior
- pip

## Instalação

Clone o repositório e acesse a pasta do projeto. Em seguida, instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Executar a API

Na raiz do projeto, execute:

```bash
uvicorn app.main:app --reload
```

A API ficará disponível em http://127.0.0.1:8000.

### Documentação interativa

Com a API em execução, acesse http://127.0.0.1:8000/docs.

## Executar os testes

Na raiz do projeto, execute a suíte automatizada completa:

```bash
python -m pytest -v
```

Os testes cobrem cadastro seguro e hash de senha (T1), login válido (T2), credenciais incorretas (T3), validação de e-mail antes de consultas ao banco (T4), bloqueio após três tentativas inválidas (T5) e rejeição de senhas curtas (T6).

## Segurança

- Senhas são armazenadas somente como hashes Argon2id.
- Tokens de sessão são gerados de forma aleatória; somente seu hash é persistido.
- Respostas de autenticação não informam se o e-mail ou a senha está incorreto.
- O bloqueio temporário limita tentativas consecutivas de autenticação.

## Equipe

- [@IsaReginnette](https://github.com/IsaReginnette) — Product Owner
- [@Guoriguella](https://github.com/Guoriguella) — Scrum Master
- [@zzelpz](https://github.com/zzelpz) — Desenvolvedor
