
# Portal de Empregos SINE

Plataforma web para divulgação e gerenciamento de oportunidades de emprego, desenvolvida como projeto acadêmico do curso de Análise e Desenvolvimento de Sistemas.

## Sobre o projeto

O Portal de Empregos SINE tem como objetivo facilitar a divulgação de vagas de emprego e permitir que os profissionais responsáveis pelo sistema mantenham as oportunidades atualizadas.

Os candidatos podem consultar as vagas disponíveis, verificar requisitos e informações sobre as oportunidades. Para demonstrar interesse, devem comparecer presencialmente ao atendimento do SINE.

## Capturas de tela

### Página inicial
![Página inicial](screenshots/pagina-inicial.png)

### Detalhes de uma vaga
![Detalhes da vaga](screenshots/detalhes-vaga.png)

### Painel administrativo
![Painel administrativo](screenshots/painel-admin.png)

## Funcionalidades

### Área pública
- Visualização de vagas disponíveis.
- Pesquisa de oportunidades.
- Consulta de requisitos e descrição das atividades.
- Exibição de informações sobre as vagas.

### Painel administrativo
- Acesso protegido por autenticação.
- Cadastro de novas vagas.
- Edição de vagas existentes.
- Exclusão de vagas.
- Ativação e encerramento de oportunidades.

## Tecnologias utilizadas

- **Python** — Linguagem principal.
- **Flask** — Framework web.
- **PostgreSQL** — Banco de dados.
- **Neon** — Hospedagem do banco de dados.
- **HTML, CSS e JavaScript** — Interface do usuário.
- **Werkzeug** — Recursos de segurança e autenticação.

## Estrutura do projeto

```text
projetoSINE/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── screenshots/
├── static/
└── templates/
```

## Configuração local

### 1. Clone o repositório

```bash
git clone https://github.com/EduHoffmeister/portal-empregos-sine
cd portal-empregos-sine
```

### 2. Crie um ambiente virtual

```bash
python -m venv .venv
```

### 3. Ative o ambiente virtual

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure:

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD_HASH`
- `DATABASE_URL`

Não compartilhe o arquivo `.env` ou suas credenciais.

### 6. Execute a aplicação

```bash
python app.py
```

A aplicação estará disponível em:

http://127.0.0.1:5001

## Segurança

As credenciais e configurações sensíveis são armazenadas em variáveis de ambiente. O arquivo `.env` não deve ser enviado ao repositório.

## Objetivo acadêmico

Projeto desenvolvido para aplicar conhecimentos de desenvolvimento web, programação com Python, integração com banco de dados relacional e construção de funcionalidades administrativas.
