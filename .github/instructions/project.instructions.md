# Instruções do projeto Homelab Automation

## Objetivo
Este repositório organiza a automação do homelab com foco em Raspberry Pi, Docker, serviços locais, deploy e automação via Telegram com IA.

## Estrutura principal
- `homelab-mcp/`: servidor MCP responsável por expor ferramentas do sistema, Docker e deploy.
- `homelab-telegram-bot/`: bot do Telegram que usa o MCP e uma API de IA para operar o ambiente.
- `dc-local/`: arquivos Docker Compose locais usados para subir serviços na máquina.
- `configs-apps/`: configurações e sincronização de apps.
- `raspberry-scripts/`: scripts de manutenção e automações do Raspberry Pi.

## Regras de operação
- Priorizar segurança e validação antes de executar comandos do sistema.
- Não aceitar caminhos arbitrários, `..`, nomes fora do diretório permitido ou arquivos não YAML em operações de compose.
- O diretório de compose permitido é `dc-local` na raiz do projeto.
- Sempre preferir soluções compatíveis com Docker Compose em vez de comandos ad hoc.
- Quando criar ou ajustar ferramentas MCP, manter nomes claros e retornos consistentes em JSON.
- O bot do Telegram deve ser usado como interface do homelab e não como executor genérico de qualquer comando do sistema.

## Padrões de desenvolvimento
- Manter a lógica de rede/infra em `homelab-mcp` e a lógica de interface em `homelab-telegram-bot`.
- Usar funções pequenas e bem nomeadas.
- Preferir retorno explícito de sucesso/erro em dicionários JSON.
- Tests focados devem cobrir comportamento real de Docker, paths e validação.
- Documentar mudanças relevantes em `CHANGELOG.md`.

## Comandos esperados
- Testes Python: `pytest` em diretórios específicos, preferencialmente em módulos focados.
- Compose local: `docker compose -f <arquivo>.yaml up -d` apenas dentro de `dc-local`.
- Deploy do homelab: via ferramenta MCP e não via execução manual improvisada.

## Segurança e ambiente
- O acesso ao bot e aos comandos do sistema deve continuar restrito ao usuário permitido.
- Arquivos sensíveis como `.env` e `.env.token` não devem ser compartilhados.
- Antes de subir ou reiniciar serviços, verificar se o arquivo origem está dentro da pasta autorizada.

## Objetivo de IA
A IA deve operar como assistente do homelab, não como agente genérico para qualquer tarefa do sistema. Ela deve:
- responder em português
- ser objetiva e curta
- usar ferramentas MCP quando a pergunta envolver estado ou ação no ambiente
- não inventar resultados
- basear a resposta em dados reais do sistema

## Workflow recomendado
1. Entender o problema e a área afetada.
2. Ajustar a parte correta: MCP, bot, Docker, scripts ou documentação.
3. Validar com testes focados e, quando for o caso, com comandos reais de ambiente.
4. Atualizar documentação e changelog quando houver mudança funcional.

## Observação final
O projeto é um conjunto de automação local e deve continuar sendo simples, controlado e fácil de manter por Git.
