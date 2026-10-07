# Homelab Automation

<mark style="background-color: #e8f5e9; color: #1b5e20;">Controle o homelab pelo Telegram: consulte o estado do host, opere containers e execute deploys por comandos ou pedidos em linguagem natural.</mark>

## Ficha do projeto

| Campo | Descrição |
| --- | --- |
| **Projeto** | Homelab Automation |
| **Objetivo** | Centralizar consultas e operações do homelab e automatizar tarefas de manutenção. |
| **Interface** | Bot do Telegram com comandos e suporte a linguagem natural por IA. |
| **Camada de execução** | Servidor MCP via HTTP, integrado a serviços do sistema, Docker e scripts locais. |
| **Ambiente principal** | Raspberry Pi / host local do homelab. |
| **Áreas cobertas** | Saúde do sistema, Docker, deploy, sincronização de configurações e finanças. |
| **Controle de acesso** | ID permitido configurado em `TELEGRAM_ALLOWED_USER_ID`. |

## Resumo operacional

<mark style="background-color: #e8f5e9; color: #1b5e20;">Envie um comando para executar uma rotina conhecida ou descreva a tarefa em uma mensagem. O bot valida o acesso, encaminha a operação ao MCP e devolve o resultado real no Telegram.</mark>

1. **Solicite uma ação** no Telegram, por comando ou texto livre.
2. **O bot valida sua identidade** usando o ID permitido.
3. **A solicitação é encaminhada:** comandos conhecidos seguem para seus handlers; texto livre segue para a IA com a lista atual de ferramentas MCP.
4. **A ferramenta executa a operação** no host — por exemplo, consultar métricas, gerir um container ou iniciar um deploy.
5. **O bot retorna o resultado** ou informa claramente a falha.

Para texto livre, a IA pode solicitar ferramentas MCP e usar as respostas reais dessas ferramentas para formular a resposta. A integração usa um provedor compatível com `POST /chat/completions` e tool calling.

## Ações disponíveis

| Preciso... | Use |
| --- | --- |
| Consultar CPU, memória, disco, uptime e containers ativos | `/status` |
| Atualizar o repositório e aplicar o deploy geral | `/deploy` |
| Sincronizar somente os arquivos de configuração | `/deploy_sync` |
| Publicar/reiniciar a aplicação financeira | `/deploy_finance` |
| Consultar dados financeiros ou iniciar backup | `/finance`, `/finance_invest`, `/finance_contas`, `/finance_bkp` |
| Reiniciar um serviço permitido | `/restart_service` |
| Iniciar, parar ou reiniciar um container Docker | `/start_docker`, `/stop_docker`, `/restart_docker` |
| Criar/iniciar um container via Compose | `/create_docker` |
| Ver a lista de comandos | `/options` |

Também é possível descrever o pedido em linguagem natural. A IA só deve afirmar que uma ação ocorreu quando a ferramenta retornar esse resultado.

## Como o fluxo se organiza

```text
Telegram → bot e validação de acesso → handler ou IA
                                      ↓
                               cliente MCP via HTTP
                                      ↓
                    ferramentas de saúde, Docker, deploy e finanças
                                      ↓
                 host local: systemd, containers, arquivos e scripts
                                      ↓
                         resultado de volta ao Telegram
```

O bot está em [homelab-telegram-bot](homelab-telegram-bot). O servidor MCP em [homelab-mcp](homelab-mcp) registra as ferramentas e delega a execução aos serviços locais.

### O que cada ação de deploy faz

- **`/deploy`:** executa `git pull --ff-only`, aplica a configuração do serviço de sincronização, atualiza o systemd e reinicia os serviços permitidos (por padrão, bot e MCP).
- **`/deploy_sync`:** inicia `app-config-sync.service` para copiar os arquivos definidos, sem atualizar o repositório nem reiniciar todos os serviços.
- **`/deploy_finance`:** atualiza o repositório e reinicia os containers financeiros configurados.

Deploy e sincronização usam um bloqueio para impedir operações simultâneas. As configurações de sincronização ficam em [configs-apps/app-config-sync](configs-apps/app-config-sync).

### Deploy pelo GitHub Actions

O workflow manual [Deploy homelab](.github/workflows/deploy-homelab.yml) oferece uma alternativa ao comando `/deploy`, sem remover o deploy pelo Telegram. Ele roda no próprio servidor por meio de um runner self-hosted e chama a mesma rotina de deploy do MCP; o servidor busca as atualizações com `git pull --ff-only`.

Para habilitá-lo:

1. Instale no servidor um runner self-hosted Linux registrado neste repositório, com o rótulo adicional `homelab`.
2. Execute o serviço do runner com o usuário que tem acesso de escrita ao checkout e as permissões `sudo` já necessárias ao deploy do MCP.
3. Em **Settings → Secrets and variables → Actions → Variables**, crie `HOMELAB_REPOSITORY_DIR` com o caminho absoluto do checkout no servidor, por exemplo `/home/dalves/automation`.
4. No GitHub, abra **Actions → Deploy homelab → Run workflow** e selecione `main`.

O workflow não roda em pull requests e só aceita execução na branch `main`. Restrinja o acesso de escrita ao repositório: um runner self-hosted executa código no servidor. A concorrência entre execuções deste workflow é serializada; não inicie ao mesmo tempo `/deploy` no bot e o deploy pelo GitHub.

## Componentes

| Diretório | Papel no fluxo |
| --- | --- |
| [homelab-telegram-bot](homelab-telegram-bot) | Recebe solicitações, valida acesso, executa comandos e integra a IA e o cliente MCP. |
| [homelab-mcp](homelab-mcp) | Expõe ferramentas MCP para consultar e operar os serviços do homelab. |
| [configs-apps](configs-apps) | Mantém configurações compartilhadas, sincronização e aplicação financeira. |
| [dc-local](dc-local) | Guarda arquivos Docker Compose usados para subir serviços locais. |
| [raspberry-scripts](raspberry-scripts) | Reúne rotinas de manutenção, alertas, backups e tarefas agendadas. |

## Configuração e acesso

Configure os arquivos de ambiente usados pelo bot e pelo MCP antes de iniciar os serviços. O bot precisa do token do Telegram, do ID de usuário permitido, da URL do MCP e, para linguagem natural, dos dados do provedor de IA:

- `TELEGRAM_BOT_TOKEN` e `TELEGRAM_ALLOWED_USER_ID`
- `MCP_URL`
- `AI_API_URL`, `AI_API_KEY` e `AI_MODEL`

Os módulos de configuração estão em [homelab-telegram-bot/config.py](homelab-telegram-bot/config.py) e [homelab-mcp/app/config.py](homelab-mcp/app/config.py). Não publique tokens ou chaves em documentação ou no Git.

<mark style="background-color: #e8f5e9; color: #1b5e20;">As ações privilegiadas dependem das permissões do host. Mantenha os serviços, containers e caminhos autorizados restritos às configurações necessárias.</mark>

## Referências

- [Servidor MCP](homelab-mcp/README.md)
- [Bot do Telegram](homelab-telegram-bot/README.md)
- [Sincronização de configurações](configs-apps/app-config-sync/README.md)
