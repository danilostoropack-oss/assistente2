@echo off
title Storopack - Assistente Tecnico
color 0A

echo.
echo  ================================================
echo       STOROPACK - Assistente Tecnico com IA
echo            Instalador e Gerenciador
echo  ================================================
echo.

:MENU
echo.
echo  ----------------------------------------
echo    1. Instalar / Configurar
echo    2. Iniciar o Aplicativo
echo    3. Parar o Aplicativo
echo    4. Verificar Status
echo    5. Configurar Chaves de API
echo    6. Abrir Painel Admin
echo    7. Sair
echo  ----------------------------------------
echo.
set /p "opcao=  Escolha uma opcao: "

if "%opcao%"=="1" goto INSTALAR
if "%opcao%"=="2" goto INICIAR
if "%opcao%"=="3" goto PARAR
if "%opcao%"=="4" goto STATUS
if "%opcao%"=="5" goto CONFIG
if "%opcao%"=="6" goto ADMIN
if "%opcao%"=="7" goto SAIR

echo.
echo  Opcao invalida!
echo.
pause
goto MENU

:INSTALAR
echo.
echo  [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado!
    echo  Instale Python 3.10+ em https://python.org
    echo  Marque "Add Python to PATH" durante a instalacao!
    echo.
    pause
    goto MENU
)
python --version
echo  [OK] Python encontrado!
echo.

echo  [2/5] Criando ambiente virtual...
if not exist ".venv" (
    python -m venv .venv
    echo  [OK] Ambiente virtual criado!
) else (
    echo  [OK] Ambiente virtual ja existe.
)
echo.

echo  [3/5] Ativando ambiente virtual...
call .venv\Scripts\activate.bat
echo  [OK] Ativado.
echo.

echo  [4/5] Instalando dependencias...
pip install -r requirements.txt --quiet
echo  [OK] Dependencias instaladas!
echo.

echo  [5/5] Verificando arquivo .env...
if not exist ".env" (
    echo OPENAI_API_KEY=sua_chave_openai_aqui> .env
    echo GOOGLE_API_KEY=sua_chave_google_aqui>> .env
    echo VECTOR_STORE_ID=>> .env
    echo ASSISTANT_ID=>> .env
    echo ADMIN_PASSWORD=storopack2024>> .env
    echo SECRET_KEY=storopack-secret-2024>> .env
    echo  [OK] Arquivo .env criado!
    echo.
    echo  IMPORTANTE: Edite o arquivo .env com suas chaves de API!
    echo  Use a opcao 5 do menu para editar.
) else (
    echo  [OK] Arquivo .env encontrado.
)

echo.
echo  Criando pastas necessarias...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "uploads\pdfs" mkdir uploads\pdfs
if not exist "uploads\videos" mkdir uploads\videos
echo  [OK] Pastas criadas.

echo.
echo  ================================================
echo    INSTALACAO CONCLUIDA!
echo  ================================================
echo.
pause
goto MENU

:INICIAR
echo.
echo  Iniciando o Assistente Storopack...
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo  [ERRO] Ambiente virtual nao encontrado.
    echo  Execute a opcao 1 primeiro.
    echo.
    pause
    goto MENU
)

call .venv\Scripts\activate.bat

echo  Servidor iniciando na porta 5000...
echo.
echo  Chat:   http://localhost:5000
echo  Admin:  http://localhost:5000/admin
echo.

start "StoropackServer" cmd /c "call .venv\Scripts\activate.bat && python app.py"

echo  Aguardando servidor iniciar...
timeout /t 4 /nobreak >nul

start http://localhost:5000

echo.
echo  [OK] Servidor iniciado! Navegador aberto.
echo.
pause
goto MENU

:PARAR
echo.
echo  Parando o servidor...

taskkill /FI "WINDOWTITLE eq StoropackServer" /F >nul 2>&1

echo  [OK] Servidor parado!
echo.
pause
goto MENU

:STATUS
echo.
echo  Verificando status...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  Python:     [ERRO] Nao instalado
) else (
    echo  Python:     [OK] Instalado
)

if exist ".venv" (
    echo  Ambiente:   [OK] Configurado
) else (
    echo  Ambiente:   [ERRO] Nao configurado
)

if exist ".env" (
    echo  Config:     [OK] Arquivo .env existe
) else (
    echo  Config:     [ERRO] .env nao encontrado
)

if exist "data\storopack.db" (
    echo  Banco:      [OK] Banco de dados existe
) else (
    echo  Banco:      [--] Sera criado ao iniciar
)

echo.
pause
goto MENU

:CONFIG
echo.
echo  ================================================
echo      Configuracao de Chaves de API
echo  ================================================
echo.

if not exist ".env" (
    echo  [ERRO] Arquivo .env nao encontrado.
    echo  Execute a instalacao primeiro - opcao 1.
    echo.
    pause
    goto MENU
)

echo  Abrindo arquivo .env no Bloco de Notas...
echo.
echo  Preencha suas chaves:
echo    OPENAI_API_KEY = Chave da OpenAI - obrigatorio
echo    GOOGLE_API_KEY = Chave do Google Gemini - para video
echo    ADMIN_PASSWORD = Senha do painel admin
echo.

notepad .env

echo.
echo  Salve o arquivo e reinicie o servidor.
echo.
pause
goto MENU

:ADMIN
echo.
echo  Abrindo painel administrativo...
echo.
echo  Senha padrao: storopack2024
echo.

start http://localhost:5000/admin

pause
goto MENU

:SAIR
echo.
echo  Ate logo!
echo.
timeout /t 2 /nobreak >nul
exit
