#!/bin/bash

# Script de automação para gerenciar serviços homelab

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Serviços
SERVICES=("homelab-mcp" "homelab-telegram-bot")

# Função para limpar tela e mostrar menu
show_menu() {
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}    GERENCIADOR DE SERVIÇOS HOMELAB${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${GREEN}Opções Principais:${NC}"
    echo "1. Iniciar serviços"
    echo "2. Parar serviços"
    echo "3. Reiniciar serviços"
    echo "4. Ver status dos serviços"
    echo "5. Gerenciar serviço específico"
    echo "6. Editar configuração"
    echo "7. Recarregar daemon systemd"
    echo "8. Ver logs de um serviço"
    echo "0. Sair"
    echo ""
}

# Função para listar e escolher um serviço
select_service() {
    echo -e "${YELLOW}Escolha um serviço:${NC}"
    for i in "${!SERVICES[@]}"; do
        echo "$((i+1)). ${SERVICES[$i]}"
    done
    echo "0. Voltar"
    read -p "Opção: " service_choice
    
    if [ "$service_choice" -eq 0 ]; then
        return 1
    elif [ "$service_choice" -ge 1 ] && [ "$service_choice" -le ${#SERVICES[@]} ]; then
        SELECTED_SERVICE="${SERVICES[$((service_choice-1))]}"
        return 0
    else
        echo -e "${RED}Opção inválida${NC}"
        return 1
    fi
}

# Função para iniciar todos os serviços
start_all() {
    echo -e "${YELLOW}Iniciando serviços...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${BLUE}Iniciando $service...${NC}"
        sudo systemctl start "$service"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $service iniciado com sucesso${NC}"
        else
            echo -e "${RED}✗ Erro ao iniciar $service${NC}"
        fi
    done
    read -p "Pressione Enter para continuar..."
}

# Função para parar todos os serviços
stop_all() {
    echo -e "${YELLOW}Parando serviços...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${BLUE}Parando $service...${NC}"
        sudo systemctl stop "$service"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $service parado com sucesso${NC}"
        else
            echo -e "${RED}✗ Erro ao parar $service${NC}"
        fi
    done
    read -p "Pressione Enter para continuar..."
}

# Função para reiniciar todos os serviços
restart_all() {
    echo -e "${YELLOW}Reiniciando serviços...${NC}"
    for service in "${SERVICES[@]}"; do
        echo -e "${BLUE}Reiniciando $service...${NC}"
        sudo systemctl restart "$service"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $service reiniciado com sucesso${NC}"
        else
            echo -e "${RED}✗ Erro ao reiniciar $service${NC}"
        fi
    done
    read -p "Pressione Enter para continuar..."
}

# Função para ver status de todos os serviços
status_all() {
    echo -e "${YELLOW}Status dos serviços:${NC}"
    echo ""
    for service in "${SERVICES[@]}"; do
        echo -e "${BLUE}--- $service ---${NC}"
        sudo systemctl status "$service" --no-pager
        echo ""
    done
    read -p "Pressione Enter para continuar..."
}

# Função para gerenciar serviço específico
manage_service() {
    select_service
    if [ $? -ne 0 ]; then
        return
    fi
    
    while true; do
        clear
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}    Gerenciando: $SELECTED_SERVICE${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo ""
        echo "1. Iniciar"
        echo "2. Parar"
        echo "3. Reiniciar"
        echo "4. Ver status"
        echo "5. Ver logs"
        echo "0. Voltar"
        echo ""
        read -p "Opção: " service_option
        
        case $service_option in
            1)
                echo -e "${YELLOW}Iniciando $SELECTED_SERVICE...${NC}"
                sudo systemctl start "$SELECTED_SERVICE"
                echo -e "${GREEN}✓ Concluído${NC}"
                ;;
            2)
                echo -e "${YELLOW}Parando $SELECTED_SERVICE...${NC}"
                sudo systemctl stop "$SELECTED_SERVICE"
                echo -e "${GREEN}✓ Concluído${NC}"
                ;;
            3)
                echo -e "${YELLOW}Reiniciando $SELECTED_SERVICE...${NC}"
                sudo systemctl restart "$SELECTED_SERVICE"
                echo -e "${GREEN}✓ Concluído${NC}"
                ;;
            4)
                echo -e "${YELLOW}Status de $SELECTED_SERVICE:${NC}"
                sudo systemctl status "$SELECTED_SERVICE" --no-pager
                ;;
            5)
                echo -e "${YELLOW}Últimas 20 linhas de logs de $SELECTED_SERVICE:${NC}"
                sudo journalctl -u "$SELECTED_SERVICE" -n 20 --no-pager
                ;;
            0)
                return
                ;;
            *)
                echo -e "${RED}Opção inválida${NC}"
                ;;
        esac
        
        read -p "Pressione Enter para continuar..."
    done
}

# Função para editar configuração
edit_config() {
    echo -e "${YELLOW}Escolha qual arquivo editar:${NC}"
    echo "1. homelab-mcp.service"
    echo "2. homelab-telegram-bot.service"
    echo "0. Voltar"
    read -p "Opção: " config_choice
    
    case $config_choice in
        1)
            echo -e "${BLUE}Editando homelab-mcp.service...${NC}"
            sudo nano /etc/systemd/system/homelab-mcp.service
            echo -e "${YELLOW}Recarregando daemon...${NC}"
            sudo systemctl daemon-reload
            echo -e "${GREEN}✓ Concluído${NC}"
            ;;
        2)
            echo -e "${BLUE}Editando homelab-telegram-bot.service...${NC}"
            sudo nano /etc/systemd/system/homelab-telegram-bot.service
            echo -e "${YELLOW}Recarregando daemon...${NC}"
            sudo systemctl daemon-reload
            echo -e "${GREEN}✓ Concluído${NC}"
            ;;
        0)
            return
            ;;
        *)
            echo -e "${RED}Opção inválida${NC}"
            ;;
    esac
    
    read -p "Pressione Enter para continuar..."
}

# Função para recarregar daemon
reload_daemon() {
    echo -e "${YELLOW}Recarregando daemon systemd...${NC}"
    sudo systemctl daemon-reload
    echo -e "${GREEN}✓ Daemon recarregado com sucesso${NC}"
    read -p "Pressione Enter para continuar..."
}

# Função para ver logs
view_logs() {
    select_service
    if [ $? -ne 0 ]; then
        return
    fi
    
    echo -e "${YELLOW}Quantas linhas deseja ver? (padrão: 50)${NC}"
    read -p "Linhas: " lines
    lines=${lines:-50}
    
    echo -e "${YELLOW}Logs de $SELECTED_SERVICE:${NC}"
    sudo journalctl -u "$SELECTED_SERVICE" -n "$lines" --no-pager
    
    read -p "Pressione Enter para continuar..."
}

# Loop principal
while true; do
    show_menu
    read -p "Escolha uma opção: " choice
    
    case $choice in
        1)
            start_all
            ;;
        2)
            stop_all
            ;;
        3)
            restart_all
            ;;
        4)
            status_all
            ;;
        5)
            manage_service
            ;;
        6)
            edit_config
            ;;
        7)
            reload_daemon
            ;;
        8)
            view_logs
            ;;
        0)
            echo -e "${GREEN}Saindo...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Opção inválida. Pressione Enter para tentar novamente.${NC}"
            read -p ""
            ;;
    esac
done