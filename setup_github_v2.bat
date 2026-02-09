@echo off
chcp 65001 >nul
color 0A
cls

echo ============================================================
echo   SETUP GITHUB - ASSISTENTE STOROPACK V2
echo ============================================================
echo.
echo Pressione qualquer tecla para iniciar...
pause >nul
cls

REM ============================================================================
REM CONFIGURAÇÕES
REM ============================================================================

set REPO_URL=https://github.com/danilostoropack-oss/assistente2.git
set PASTA_PROJETO=C:\Users\Danilo\Downloads\storopack
set PASTA_REPO=C:\Users\Danilo\Downloads\assistente2

echo ============================================================
echo   VERIFICANDO CONFIGURAÇÕES
echo ============================================================
echo.
echo Repositório: %REPO_URL%
echo Pasta projeto: %PASTA_PROJETO%
echo Pasta destino: %PASTA_REPO%
echo.
pause

REM ============================================================================
REM PASSO 1: Verificar pasta do projeto
REM ============================================================================

cls
echo [1/10] Verificando pasta do projeto...
echo.

if not exist "%PASTA_PROJETO%" (
    echo [ERRO] Pasta do projeto NAO encontrada!
    echo.
    echo Esperado: %PASTA_PROJETO%
    echo.
    echo Verifique se a pasta existe e tente novamente.
    echo.
    pause
    exit /b 1
)

echo [OK] Pasta encontrada: %PASTA_PROJETO%
echo.
pause

REM ============================================================================
REM PASSO 2: Verificar Git
REM ============================================================================

cls
echo [2/10] Verificando instalação do Git...
echo.

git --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Git NAO está instalado ou NAO está no PATH!
    echo.
    echo Instale o Git em: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

git --version
echo.
echo [OK] Git instalado
echo.
pause

REM ============================================================================
REM PASSO 3: Limpar pasta antiga
REM ============================================================================

cls
echo [3/10] Limpando repositório antigo (se existir)...
echo.

if exist "%PASTA_REPO%" (
    echo Removendo pasta: %PASTA_REPO%
    rmdir /s /q "%PASTA_REPO%"
    echo [OK] Pasta removida
) else (
    echo [INFO] Nenhuma pasta antiga encontrada
)
echo.
pause

REM ============================================================================
REM PASSO 4: Clonar repositório
REM ============================================================================

cls
echo [4/10] Clonando repositório do GitHub...
echo.
echo Repositório: %REPO_URL%
echo.

cd C:\Users\Danilo\Downloads

git clone %REPO_URL%

if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao clonar repositório!
    echo.
    echo Possíveis causas:
    echo - Sem conexão com internet
    echo - Repositório não existe
    echo - Sem permissão de acesso
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Repositório clonado com sucesso
echo.
pause

REM ============================================================================
REM PASSO 5: Entrar no repositório
REM ============================================================================

cls
echo [5/10] Entrando no repositório...
echo.

cd "%PASTA_REPO%"

if errorlevel 1 (
    echo [ERRO] Não foi possível entrar na pasta do repositório
    pause
    exit /b 1
)

echo Pasta atual: %CD%
echo.
echo [OK] Dentro do repositório
echo.
pause

REM ============================================================================
REM PASSO 6: Copiar arquivos
REM ============================================================================

cls
echo [6/10] Copiando arquivos do projeto...
echo.

echo Copiando app.py...
copy "%PASTA_PROJETO%\app.py" . >nul
if errorlevel 1 (
    echo [AVISO] app.py não encontrado
) else (
    echo [OK] app.py
)

echo Copiando database.py...
copy "%PASTA_PROJETO%\database.py" . >nul
if errorlevel 1 (
    echo [AVISO] database.py não encontrado
) else (
    echo [OK] database.py
)

echo Copiando index.html...
copy "%PASTA_PROJETO%\index.html" . >nul
if errorlevel 1 (
    echo [AVISO] index.html não encontrado
) else (
    echo [OK] index.html
)

echo Copiando admin.html...
copy "%PASTA_PROJETO%\admin.html" . >nul
if errorlevel 1 (
    echo [AVISO] admin.html não encontrado
) else (
    echo [OK] admin.html
)

echo Copiando requirements.txt...
copy "%PASTA_PROJETO%\requirements.txt" . >nul
if errorlevel 1 (
    echo [AVISO] requirements.txt não encontrado
) else (
    echo [OK] requirements.txt
)

echo Copiando assistente.py...
if exist "%PASTA_PROJETO%\assistente_atualizado.py" (
    copy "%PASTA_PROJETO%\assistente_atualizado.py" assistente.py >nul
    echo [OK] assistente.py (versão atualizada)
) else if exist "%PASTA_PROJETO%\assistente.py" (
    copy "%PASTA_PROJETO%\assistente.py" . >nul
    echo [OK] assistente.py
) else (
    echo [AVISO] assistente.py não encontrado
)

echo.
echo Arquivos copiados!
echo.
pause

REM ============================================================================
REM PASSO 7: Criar .gitignore
REM ============================================================================

cls
echo [7/10] Criando .gitignore...
echo.

(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo env/
echo venv/
echo .venv/
echo.
echo # Dados sensíveis
echo .env
echo .env.local
echo .env.*.local
echo.
echo # Banco de dados
echo data/
echo *.db
echo *.sqlite
echo *.sqlite3
echo.
echo # Uploads
echo uploads/
echo temp/
echo.
echo # Logs
echo *.log
echo logs/
echo.
echo # IDEs
echo .vscode/
echo .idea/
echo *.swp
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
) > .gitignore

echo [OK] .gitignore criado
echo.
pause

REM ============================================================================
REM PASSO 8: Criar .env.exemplo
REM ============================================================================

cls
echo [8/10] Criando .env.exemplo...
echo.

(
echo # OPENAI API
echo OPENAI_API_KEY=sk-proj-sua-chave-aqui
echo.
echo # ADMIN
echo ADMIN_PASSWORD=sua-senha-aqui
echo SECRET_KEY=sua-secret-key-aqui
echo.
echo # AIRPLUS
echo ASSISTANT_AIRPLUS_MINI=asst_xxxxx
echo VECTOR_AIRPLUS_MINI=vs_xxxxx
echo.
echo # AIRMOVE
echo ASSISTANT_AIRMOVE_2=asst_xxxxx
echo VECTOR_AIRMOVE_2=vs_xxxxx
echo.
echo # FOAMPLUS
echo ASSISTANT_FOAMPLUS_BAG=asst_xxxxx
echo VECTOR_FOAMPLUS_BAG=vs_xxxxx
echo.
echo # PAPERPLUS
echo ASSISTANT_PAPERPLUS_CLASSIC=asst_xxxxx
echo VECTOR_PAPERPLUS_CLASSIC=vs_xxxxx
echo ASSISTANT_PAPERPLUS_TRACK=asst_xxxxx
echo VECTOR_PAPERPLUS_TRACK=vs_xxxxx
) > .env.exemplo

echo [OK] .env.exemplo criado
echo.
pause

REM ============================================================================
REM PASSO 9: Criar README.md
REM ============================================================================

cls
echo [9/10] Criando README.md...
echo.

(
echo # Assistente Tecnico Storopack v2
echo.
echo Sistema de assistencia tecnica com IA para equipamentos Storopack.
echo.
echo ## Equipamentos Suportados
echo.
echo - AIRplus Mini
echo - AIRmove 2
echo - FOAMplus Bag Packer
echo - PAPERplus Classic
echo - PAPERplus Track
echo.
echo ## Instalacao
echo.
echo ```bash
echo git clone https://github.com/danilostoropack-oss/assistente2.git
echo cd assistente2
echo pip install -r requirements.txt
echo cp .env.exemplo .env
echo python app.py
echo ```
echo.
echo ## Contato
echo.
echo Storopack Brasil
echo - Tel: ^(11^) 5677-4699
echo - Email: packaging.br@storopack.com
) > README.md

echo [OK] README.md criado
echo.
pause

REM ============================================================================
REM PASSO 10: Ver arquivos
REM ============================================================================

cls
echo [10/10] Arquivos preparados:
echo.
dir /b
echo.
pause

REM ============================================================================
REM PASSO 11: Git add
REM ============================================================================

cls
echo Adicionando arquivos ao Git...
echo.

git add .

if errorlevel 1 (
    echo [ERRO] Falha ao adicionar arquivos
    pause
    exit /b 1
)

echo [OK] Arquivos adicionados
echo.

git status
echo.
pause

REM ============================================================================
REM PASSO 12: Git commit
REM ============================================================================

cls
echo Fazendo commit...
echo.

git commit -m "v2.0: Sistema multi-equipamento com manuais especificos"

if errorlevel 1 (
    echo [ERRO] Falha ao fazer commit
    pause
    exit /b 1
)

echo.
echo [OK] Commit criado
echo.
pause

REM ============================================================================
REM PASSO 13: Git push
REM ============================================================================

cls
echo ============================================================
echo   ENVIANDO PARA GITHUB
echo ============================================================
echo.
echo ATENCAO: Voce pode precisar fazer login!
echo.
echo Se pedir senha, use um Personal Access Token
echo (NAO use sua senha normal do GitHub)
echo.
echo Como criar token:
echo 1. GitHub -^> Settings -^> Developer settings
echo 2. Personal access tokens -^> Tokens (classic)
echo 3. Generate new token
echo 4. Marque: repo (full control)
echo 5. Copie o token gerado
echo.
pause

git push origin main

if errorlevel 1 (
    echo.
    echo [AVISO] Tentando com branch master...
    git push origin master
    if errorlevel 1 (
        echo.
        echo [ERRO] Falha ao enviar para GitHub
        echo.
        echo Verifique:
        echo - Conexao com internet
        echo - Credenciais do GitHub
        echo - Permissoes do repositorio
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [OK] Codigo enviado para GitHub!
echo.
pause

REM ============================================================================
REM PASSO 14: Criar tag
REM ============================================================================

cls
echo Criando tag de versao...
echo.

git tag -a v2.0.0 -m "Versao 2.0"
git push origin v2.0.0

echo.

REM ============================================================================
REM SUCESSO!
REM ============================================================================

cls
echo ============================================================
echo   SUCESSO! CODIGO NO GITHUB
echo ============================================================
echo.
echo Repositorio: https://github.com/danilostoropack-oss/assistente2
echo.
echo O que foi feito:
echo - Repositorio clonado
echo - Arquivos copiados
echo - Documentacao criada
echo - Codigo commitado
echo - Enviado para GitHub
echo - Tag v2.0.0 criada
echo.
echo Proximos passos:
echo 1. Acesse o link acima
echo 2. Verifique os arquivos
echo 3. Certifique-se que .env NAO foi enviado
echo.
echo Para futuras atualizacoes:
echo Use o script: atualizar_github.bat
echo.
pause
