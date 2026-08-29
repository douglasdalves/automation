# Homelab Automation

Este repositório reúne a automação do meu homelab para:

- monitorar o Raspberry Pi
- executar deploys locais
- reiniciar serviços
- controlar containers Docker
- rodar um bot do Telegram com IA
- orquestrar arquivos de configuração em `dc-local`

A ideia é manter tudo organizado em Git e controlar o ambiente de forma simples, segura e reprodutível.

## Estrutura do projeto

- [homelab-mcp](homelab-mcp): servidor MCP que expõe ferramentas para saúde do sistema, Docker e deploy.
- [homelab-telegram-bot](homelab-telegram-bot): bot do Telegram que chama o MCP e também usa IA para responder perguntas e operar o ambiente.
- [dc-local](dc-local): arquivos Docker Compose locais usados para subir serviços na máquina.
- [configs-apps](configs-apps): configurações compartilhadas e sincronização de apps.
- [raspberry-scripts](raspberry-scripts): scripts do Raspberry Pi para manutenção e tarefas de sistema.

## Como o sistema funciona

### 1. MCP como camada de controle
O diretório [homelab-mcp](homelab-mcp) oferece uma API MCP (Model Context Protocol) com ferramentas como:

- `get_health`: consulta CPU, memória, disco, uptime e containers ativos
- `list_docker_containers`: lista containers Docker
- `inspect_docker_container`: inspeciona um container
- `manage_docker_container`: inicia, para, reinicia ou remove um container
- `deploy_homelab`: executa o fluxo de deploy do homelab
- `restart_homelab_service`: reinicia um serviço configurado

Essas ferramentas são registradas em [homelab-mcp/app/tools](homelab-mcp/app/tools) e executadas pelo servidor em [homelab-mcp/app/server.py](homelab-mcp/app/server.py).

### 2. Bot do Telegram como interface
O bot em [homelab-telegram-bot](homelab-telegram-bot) conecta com o MCP via HTTP e oferece comandos do Telegram, como:

- `/status`
- `/deploy`
- `/restart_service`
- `/restart_docker`
- `/start_docker`
- `/stop_docker`
- `/create_docker`

O arquivo principal é [homelab-telegram-bot/bot.py](homelab-telegram-bot/bot.py), e a lógica de ferramentas do MCP fica em [homelab-telegram-bot/mcp_client.py](homelab-telegram-bot/mcp_client.py).

### 3. IA no bot
A IA do bot fica em [homelab-telegram-bot/ai_client.py](homelab-telegram-bot/ai_client.py).

A lógica principal é:

- buscar as ferramentas disponibilizadas pelo MCP
- transformar cada ferramenta em uma definição de função compatível com modelos OpenAI-like
- enviar um prompt do sistema para orientar a IA
- perguntar ao modelo o que o usuário quer
- se a pergunta exigir ação no homelab, o modelo chama as ferramentas MCP
- o retorno da ferramenta é enviado de volta ao modelo
- a resposta final é montada e entregue ao Telegram

O prompt do sistema está em `SYSTEM_PROMPT` dentro de [homelab-telegram-bot/ai_client.py](homelab-telegram-bot/ai_client.py) e diz, em resumo:

- responder em português
- ser curto e objetivo
- usar ferramentas MCP quando houver necessidade de consultar ou agir no ambiente
- não inventar resultados
- explicar falhas de forma clara

## Provedor de IA

O bot usa uma API compatível com OpenAI, configurada pelas variáveis:

- `AI_API_URL`
- `AI_API_KEY`
- `AI_MODEL`

Isso pode ser qualquer provedor que aceite o padrão `POST /chat/completions` e suporte tool calling, por exemplo:

- Groq

A configuração do bot e do MCP fica em arquivos `.env` e `.env.token` na raiz do projeto.

## Como a IA aprende o funcionamento

A IA não "aprende" internamente a partir do código do repositório automaticamente. Ela aprende o funcionamento porque:

1. o bot lista as ferramentas MCP disponíveis
2. o modelo recebe a descrição de cada ferramenta na estrutura JSON
3. o modelo entende as capacidades do sistema por meio dessas funções
4. quando o usuário pergunta algo, a IA decide se precisa invocar uma ferramenta
5. o retorno real dos comandos do MCP vira base para a resposta final

Em outras palavras, o projeto ensina a IA sobre o ambiente através de ferramentas explícitas, e não por memória implícita do código.

## Fluxo de uma conversa típica

1. Usuário manda uma mensagem no Telegram
2. O bot verifica se o usuário tem permissão
3. Se a mensagem for um comando, ele executa a rotina correspondente
4. Se não for comando, a mensagem vai para a IA
5. A IA consulta as ferramentas MCP que forem necessárias
6. A resposta é montada com o resultado real retornado pelo sistema

## Segurança

Algumas regras importantes:

- o acesso ao bot é limitado por `TELEGRAM_ALLOWED_USER_ID`
- a execução de deploy/restart exige permissões do sistema
- o controle de Docker e comandos do sistema deve ser feito com cuidado
- os arquivos de compose são validados antes de execução para evitar uso indevido de caminhos

## Arquivos de configuração

Os principais arquivos de configuração do projeto são:

- [.env](.env): variáveis compartilhadas do ambiente
- [.env.token](.env.token): token do Telegram e chave da API de IA
- [homelab-mcp/app/config.py](homelab-mcp/app/config.py)
- [homelab-telegram-bot/config.py](homelab-telegram-bot/config.py)

## Observação prática

Este projeto foi pensado para funcionar como uma automação de homelab local, com controle via Telegram e uso de IA para facilitar consultas e ações sem expor o sistema diretamente.

O foco é combinar:

- automação de infraestrutura
- controle por interface simples
- IA orientada a ações
- manutenção em Git

## Próximo passo recomendado

Se você quiser evoluir o projeto, os pontos mais úteis são:

- adicionar mais ferramentas MCP para serviços específicos
- documentar cada comando do bot
- criar um fluxo de deploy mais seguro por ambiente
- permitir mais ações de Docker via comandos específicos
- separar melhor permissões por funcionalidade

---

Este documento serve como guia de referência para entender a arquitetura do projeto, o papel do MCP e como a IA é usada pelo bot para operar o homelab.
