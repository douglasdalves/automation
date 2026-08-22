# Homelab MCP

Servidor MCP do homelab. Ele disponibiliza ferramentas de saude, Docker, deploy e reinicio de servicos por HTTP.

## Requisitos

- Python 3
- Acesso ao Docker, se as ferramentas Docker forem utilizadas
- `sudo` sem prompt de senha para os comandos de deploy e restart

## Configuracao

Crie o arquivo `../.env` na raiz de `automation`:

```env
MCP_NAME=Health Check
MCP_HOST=0.0.0.0
MCP_PORT=5080
ENVIRONMENT=development
DEPLOY_REPOSITORY_DIR=/home/dalves/automation
DEPLOY_COMMAND_TIMEOUT=300
DEPLOY_SERVICES=homelab-telegram-bot,homelab-mcp
```

O arquivo e carregado por `app/config.py` e pelo servico de deploy.

## Instalacao

Na raiz do projeto:

```bash
cd /home/dalves/automation/homelab-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execucao manual

```bash
cd /home/dalves/automation/homelab-mcp
source .venv/bin/activate
python run.py
```

O endpoint MCP fica disponivel em:

```text
http://localhost:5080/mcp
```

## Ferramentas

- `get_health`: consulta CPU, memoria, disco, uptime e containers.
- Ferramentas Docker: consulta e gerencia containers conforme os tools registrados.
- `deploy_homelab`: executa `git pull`, instala o app-config-sync e reinicia os servicos configurados.
- `restart_homelab_service`: reinicia um servico listado em `DEPLOY_SERVICES`.

## O que o deploy faz

Quando `deploy_homelab` e chamado, as etapas sao executadas nesta ordem:

1. Verifica se `DEPLOY_REPOSITORY_DIR` existe.
2. Executa `git pull --ff-only` nesse repositorio. O modo `--ff-only` evita criar merge automatico.
3. Copia `sync.conf` para `/etc/app-config-sync/`.
4. Copia `sync-configs.sh` para `/usr/local/bin/` e garante permissao de execucao.
5. Copia as unidades `app-config-sync.service` e `app-config-sync.path` para o systemd.
6. Executa `systemctl daemon-reload` e ativa o observador `app-config-sync.path`.
7. Executa imediatamente `app-config-sync.service` para sincronizar os arquivos.
8. Reinicia, em ordem, cada servico definido em `DEPLOY_SERVICES`.

O deploy nao executa se ja houver outro deploy em andamento. Se qualquer etapa falhar, ele para naquele ponto e retorna a etapa, o servico envolvido e o erro. Os comandos possuem o limite definido por `DEPLOY_COMMAND_TIMEOUT`.

Por padrao, os servicos reiniciados sao `homelab-telegram-bot` e `homelab-mcp`. Essa lista pode ser alterada no `.env`:

```env
DEPLOY_SERVICES=homelab-telegram-bot,homelab-mcp
```

O `/deploy` do bot apenas chama essa ferramenta MCP e mostra o resultado no Telegram.

## systemd

```bash
sudo cp scripts-services/homelab-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable homelab-mcp
sudo systemctl start homelab-mcp
sudo systemctl status homelab-mcp
```

Para acompanhar os logs:

```bash
journalctl -u homelab-mcp -f
```

## Permissoes do sudo

O usuario do servico precisa executar os comandos usados pelo deploy e pelo restart sem prompt de senha. Configure uma regra em:

```bash
sudo visudo -f /etc/sudoers.d/homelab-deploy
```

Inclua os comandos necessarios para `mkdir`, `cp`, `chmod` e `systemctl`, sempre usando caminhos absolutos e somente os servicos permitidos.

## Testes

```bash
cd /home/dalves/automation/homelab-mcp
source .venv/bin/activate
pytest -q
```
