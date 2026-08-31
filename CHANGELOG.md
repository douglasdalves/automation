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

### Ajustado
- Melhor organização da documentação e arquitetura do homelab
- Ajuste de memória do compose do Filebrowser para uso mais estável em Raspberry Pi 4

### Removido
- Exclusão das pastas de testes e dos artefatos de cache do projeto, sem impacto na execução principal do homelab

### Corrigido
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

