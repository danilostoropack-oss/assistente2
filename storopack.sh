#!/bin/bash
# Storopack - Assistente Técnico com IA
# Instalador e Gerenciador para Linux/Mac

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

PID_FILE=".storopack.pid"

show_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   ${BOLD}STOROPACK - Assistente Técnico com IA${NC}${BLUE}      ║${NC}"
    echo -e "${BLUE}║          Instalador e Gerenciador            ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
    echo ""
}

show_menu() {
    echo -e "  ${BOLD}1.${NC} Instalar / Configurar"
    echo -e "  ${BOLD}2.${NC} Iniciar o Aplicativo"
    echo -e "  ${BOLD}3.${NC} Parar o Aplicativo"
    echo -e "  ${BOLD}4.${NC} Verificar Status"
    echo -e "  ${BOLD}5.${NC} Configurar Chaves de API"
    echo -e "  ${BOLD}6.${NC} Abrir Painel Admin"
    echo -e "  ${BOLD}7.${NC} Sair"
    echo ""
    read -p "  Escolha uma opção: " opcao
}

instalar() {
    echo ""
    echo -e "${YELLOW}[1/5] Verificando Python...${NC}"
    if command -v python3 &> /dev/null; then
        python3 --version
        echo -e "${GREEN}✅ Python encontrado!${NC}"
    else
        echo -e "${RED}❌ Python3 não encontrado!${NC}"
        echo "Instale com: sudo apt install python3 python3-venv python3-pip"
        return
    fi

    echo ""
    echo -e "${YELLOW}[2/5] Criando ambiente virtual...${NC}"
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        echo -e "${GREEN}✅ Ambiente virtual criado!${NC}"
    else
        echo -e "${GREEN}✅ Ambiente virtual já existe.${NC}"
    fi

    echo ""
    echo -e "${YELLOW}[3/5] Ativando ambiente virtual...${NC}"
    source .venv/bin/activate

    echo ""
    echo -e "${YELLOW}[4/5] Instalando dependências...${NC}"
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✅ Dependências instaladas!${NC}"

    echo ""
    echo -e "${YELLOW}[5/5] Verificando arquivo .env...${NC}"
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
OPENAI_API_KEY=sua_chave_openai_aqui
GOOGLE_API_KEY=sua_chave_google_aqui
VECTOR_STORE_ID=
ASSISTANT_ID=
ADMIN_PASSWORD=storopack2024
SECRET_KEY=storopack-secret-2024
EOF
        echo -e "${GREEN}✅ Arquivo .env criado!${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANTE: Edite o arquivo .env com suas chaves!${NC}"
    else
        echo -e "${GREEN}✅ Arquivo .env encontrado.${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ Instalação concluída!${NC}"
}

iniciar() {
    echo ""
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  O aplicativo já está rodando! (PID: $pid)${NC}"
            echo "  Acesse: http://localhost:5000"
            return
        fi
    fi

    source .venv/bin/activate 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Ambiente virtual não encontrado. Execute a opção 1 primeiro.${NC}"
        return
    fi

    echo -e "${BLUE}🚀 Iniciando servidor na porta 5000...${NC}"
    echo -e "  📱 Chat:  http://localhost:5000"
    echo -e "  📊 Admin: http://localhost:5000/admin"

    nohup python3 app.py > logs/server.log 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    echo -e "${GREEN}✅ Servidor iniciado! (PID: $(cat $PID_FILE))${NC}"

    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:5000 2>/dev/null &
    elif command -v open &> /dev/null; then
        open http://localhost:5000 2>/dev/null &
    fi
}

parar() {
    echo ""
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$PID_FILE"
            echo -e "${GREEN}✅ Servidor parado!${NC}"
        else
            rm -f "$PID_FILE"
            echo -e "${YELLOW}Servidor já estava parado.${NC}"
        fi
    else
        echo -e "${YELLOW}Servidor não está rodando.${NC}"
    fi
}

status() {
    echo ""
    # Python
    if command -v python3 &> /dev/null; then
        echo -e "  Python:   ${GREEN}✅ $(python3 --version)${NC}"
    else
        echo -e "  Python:   ${RED}❌ Não instalado${NC}"
    fi

    # Venv
    if [ -d ".venv" ]; then
        echo -e "  Ambiente: ${GREEN}✅ Configurado${NC}"
    else
        echo -e "  Ambiente: ${RED}❌ Não configurado${NC}"
    fi

    # .env
    if [ -f ".env" ]; then
        echo -e "  Config:   ${GREEN}✅ .env existe${NC}"
    else
        echo -e "  Config:   ${RED}❌ .env não encontrado${NC}"
    fi

    # Database
    if [ -f "data/storopack.db" ]; then
        echo -e "  Banco:    ${GREEN}✅ Banco de dados existe${NC}"
    else
        echo -e "  Banco:    ${YELLOW}⚠️  Será criado ao iniciar${NC}"
    fi

    # Server
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        echo -e "  Servidor: ${GREEN}✅ Rodando (PID: $(cat $PID_FILE))${NC}"
    else
        echo -e "  Servidor: ${RED}❌ Parado${NC}"
    fi
    echo ""
}

config() {
    echo ""
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ Arquivo .env não encontrado. Execute a instalação primeiro.${NC}"
        return
    fi
    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vi &> /dev/null; then
        vi .env
    else
        echo "Edite manualmente o arquivo .env"
        cat .env
    fi
}

admin() {
    echo ""
    echo -e "${BLUE}Abrindo painel administrativo...${NC}"
    echo "  Senha padrão: storopack2024"
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:5000/admin 2>/dev/null &
    elif command -v open &> /dev/null; then
        open http://localhost:5000/admin 2>/dev/null &
    else
        echo "  Acesse: http://localhost:5000/admin"
    fi
}

# Create logs directory
mkdir -p logs

# Main loop
while true; do
    show_header
    show_menu
    case $opcao in
        1) instalar ;;
        2) iniciar ;;
        3) parar ;;
        4) status ;;
        5) config ;;
        6) admin ;;
        7) echo -e "${GREEN}Até logo! 👋${NC}"; exit 0 ;;
        *) echo -e "${RED}Opção inválida!${NC}" ;;
    esac
    echo ""
    read -p "  Pressione Enter para continuar..." dummy
done
