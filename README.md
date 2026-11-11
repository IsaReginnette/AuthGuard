# 🛡️ AuthGuard
### Autenticação segura, simples e confiável para aplicações Python

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange)](#-status-do-projeto)
[![Projeto acadêmico](https://img.shields.io/badge/projeto-acad%C3%AAmico-6C5CE7)](#-equipe)

> Uma API de autenticação e controle de acesso com foco na proteção de credenciais, validação de entradas e prevenção contra tentativas indevidas de login.

---

## 📌 Sobre o projeto

O **AuthGuard** é um projeto acadêmico desenvolvido para a disciplina com o objetivo de construir uma solução de autenticação por API. A proposta é permitir que outras aplicações utilizem um serviço responsável por cadastrar usuários, validar credenciais e aplicar regras básicas de segurança durante o login.

O projeto prioriza boas práticas desde a concepção: senhas armazenadas somente em formato protegido, respostas de autenticação que não exponham informações sensíveis, validação dos dados recebidos e testes automatizados para verificar os comportamentos esperados.

## 🎯 Objetivos

- Implementar um fluxo de cadastro e autenticação por API.
- Proteger senhas utilizando algoritmo de hash apropriado.
- Validar os dados de entrada antes de realizar operações no banco.
- Reduzir a exposição de informações em respostas de falha de autenticação.
- Bloquear temporariamente contas após sucessivas tentativas inválidas.
- Comprovar os requisitos por meio de testes automatizados.

## 🔐 Requisitos funcionais e de segurança

A tabela apresenta o escopo definido para o trabalho. Os itens não devem ser considerados concluídos até que estejam implementados e cobertos pelos testes.

| ID | Requisito | Comportamento esperado |
|---|---|---|
| L1 | Cadastro seguro | Aceitar e-mail e senha válidos e armazenar somente o hash da senha. |
| L2 | Login válido | Autenticar credenciais corretas e retornar uma identificação de autenticação (token ou mecanismo equivalente). |
| L3 | Falha genérica | Retornar mensagem genérica quando as credenciais estiverem incorretas, sem indicar se o e-mail ou a senha falhou. |
| L4 | Validação de e-mail | Rejeitar e-mail vazio ou sem o caractere `@` antes de consultar o banco de dados. |
| L5 | Bloqueio temporário | Após 3 senhas incorretas consecutivas, bloquear a conta por 10 minutos, inclusive para uma tentativa com a senha correta durante o bloqueio. |
| L6 | Política de senha | Rejeitar senhas com menos de 8 caracteres no cadastro. |

## 🧰 Tecnologias previstas

A seleção abaixo representa a proposta técnica inicial e poderá ser ajustada conforme a implementação e as decisões da equipe.

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem principal |
| FastAPI | Construção da API HTTP |
| SQLite | Persistência de dados no ambiente acadêmico |
| SQLAlchemy | Mapeamento objeto-relacional |
| Pydantic | Validação e estruturação dos dados |
| Argon2 | Hash seguro de senhas |
| Pytest | Execução dos testes automatizados |
| HTTPX | Testes das rotas da API |

## 🏗️ Arquitetura proposta

A solução será organizada em camadas para separar responsabilidades e facilitar a manutenção:

```text
Cliente / Aplicação consumidora
            |
            v
       API (FastAPI)
            |
            v
 Validação de dados (Pydantic)
            |
            v
 Serviço de autenticação
   |                 |
   v                 v
Hash de senha   Regras de bloqueio
   |                 |
   +--------+--------+
            |
            v
      Persistência
        (SQLite)
            |
            v
   Testes automatizados
   (Pytest + HTTPX)
```

Essa estrutura é uma referência de organização; os módulos e diretórios definitivos serão documentados quando forem criados no repositório.

## 🌐 API — contrato planejado

A interface será HTTP/JSON. Os caminhos abaixo são uma proposta inicial de contrato e só devem ser tratados como disponíveis depois de implementados.

| Método | Rota planejada | Finalidade |
|---|---|---|
| POST | `/auth/register` | Cadastrar usuário |
| POST | `/auth/login` | Validar credenciais e iniciar autenticação |
| GET | `/health` | Verificar disponibilidade do serviço |

### Exemplo de cadastro

Requisição ilustrativa:

```json
{
  "email": "usuario@exemplo.com",
  "password": "SenhaSegura123"
}
```

### Exemplo de login

Requisição ilustrativa:

```json
{
  "email": "usuario@exemplo.com",
  "password": "SenhaSegura123"
}
```

Os formatos definitivos de resposta, códigos HTTP, esquema de token e mensagens de erro serão registrados aqui após a implementação.

## 🧪 Estratégia de testes

Os testes automatizados deverão validar, no mínimo, os seguintes cenários:

| Teste | Cenário | Resultado esperado |
|---|---|---|
| T1 | Cadastro de usuário | A senha persistida é diferente da senha original, pois está armazenada como hash. |
| T2 | Login com credenciais corretas | Autenticação concluída com sucesso. |
| T3 | Login com senha incorreta | Falha com mensagem genérica. |
| T4 | Cadastro/login com e-mail inválido | Entrada rejeitada antes da consulta ao banco. |
| T5 | Quarta tentativa após três erros | Tentativa recusada mesmo com a senha correta, durante o bloqueio. |
| T6 | Cadastro com senha menor que 8 caracteres | Cadastro rejeitado. |

### Executar os testes

Quando a estrutura e as dependências estiverem implementadas, o comando de referência será:

```bash
pytest -v
```

O comando definitivo e as instruções de ambiente serão atualizados de acordo com os arquivos reais do projeto.

## ▶️ Como executar

**Status atual:** a estrutura executável da API ainda não foi adicionada ao repositório. Portanto, ainda não há um comando funcional de inicialização para documentar.

Após a implementação, esta seção deverá conter:
1. Pré-requisitos e versão do Python.
2. Clonagem do repositório.
3. Criação e ativação de ambiente virtual.
4. Instalação das dependências.
5. Configuração das variáveis de ambiente, se necessárias.
6. Comando para iniciar a API.
7. Endereço da documentação interativa e comando para executar os testes.

## 📋 Organização do trabalho

O desenvolvimento será acompanhado por meio de GitHub Projects, utilizando fluxo Kanban e práticas de Scrum.

- **Backlog:** demandas identificadas e ainda não priorizadas para execução.
- **Ready:** histórias priorizadas e preparadas para desenvolvimento.
- **In progress:** atividades em execução, respeitando o limite de trabalho em andamento (WIP).
- **In review:** alterações aguardando revisão por Pull Request, também com limite WIP.
- **Done:** itens concluídos e integrados à branch principal.

### Fluxo de contribuição

1. Criar uma Issue descrevendo a história e seus critérios de aceite.
2. Criar uma branch vinculada à Issue.
3. Implementar a alteração e registrar commits na própria branch.
4. Abrir um Pull Request com resumo e instruções de teste.
5. Solicitar revisão de outro integrante.
6. Integrar à `main` somente após aprovação.

## 👥 Equipe

| Integrante | GitHub | Papel |
|---|---|---|
| Isabelle | [@IsaReginnette](https://github.com/IsaReginnette) | Product Owner (PO) |
| Gustavo | [@Guoriguella](https://github.com/Guoriguella) | Scrum Master (SM) |
| Lukas | [@zzelpz](https://github.com/zzelpz) | Developer (DEV) |

## 📍 Status do projeto

<sub>Este README documenta o escopo e a proposta técnica. A implementação está em desenvolvimento; funcionalidades, rotas e comandos só serão marcados como concluídos após validação no código e nos testes.</sub>

---

<div align="center">

**AuthGuard** · Projeto acadêmico de Engenharia da Computação

*Segurança começa na autenticação.*

</div>
