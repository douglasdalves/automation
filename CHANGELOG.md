# Changelog

Todas as mudanças relevantes do projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e a versão segue o [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Adicionado
- Documentação principal do projeto em [README.md](README.md)
- Suporte para listar arquivos Docker Compose em `dc-local`
- Comando Telegram `/create_docker` para iniciar um compose selecionado
- Ferramentas MCP para listar e iniciar compose locais
- Validação de nomes de arquivos YAML para evitar uso indevido de caminhos
- Comando Telegram `/options` para listar rapidamente todas as ações disponíveis no bot
- Painel financeiro local com conversão da planilha Excel para JSON em [configs-apps/app-finance-sync](configs-apps/app-finance-sync)
- Compose de dashboard financeiro em [dc-local/dc-finan-dashboard.yaml](dc-local/dc-finan-dashboard.yaml)

### Ajustado
- Reorganização das seções do painel financeiro entre evolução de contas e composição de investimentos
- Melhor organização da documentação e arquitetura do homelab
- Ajuste de memória do compose do Filebrowser para uso mais estável em Raspberry Pi 4
- Gráficos de composição e evolução do painel financeiro passam a abrir no mês atual
- Total de investimentos passa a ser calculado pela soma de `investimentos_itens`
- Persistência do painel financeiro migrada para SQLite, mantendo inserções pelo `dashboard-insert`
- Removidos cache do navegador, fallback JSON e ferramentas antigas de importação por planilha

### Removido
- Exclusão das pastas de testes e dos artefatos de cache do projeto, sem impacto na execução principal do homelab

### Corrigido
- Ordenação cronológica dos meses no gráfico de receitas e despesas do painel financeiro
- Soma dos itens de `investimentos_recentes` no campo mensal `investimentos`
- Cálculo de `contas_mensais` pela soma das categorias e remoção do campo das interfaces de entrada e fluxo
- Ajustes de segurança na execução de compose para aceitar somente arquivos válidos dentro da pasta permitida
- Correção do caminho de resolução do diretório `dc-local`, evitando erro ao procurar o compose fora da pasta correta do projeto

## [0.1.0] - 2026-08-29

### Adicionado
- Estrutura inicial do repositório para automação do homelab
- Servidor MCP com ferramentas de saúde, Docker e deploy
- Bot Telegram para status, deploy e reinício de serviços
- Integração com IA via API compatível com OpenAI para consultas no homelab
- Configuração inicial de serviços e scripts do Raspberry Pi

### Documentado
- Guia de uso do projeto em [README.md](README.md)
- Descrição dos comandos do bot e da arquitetura do sistema

