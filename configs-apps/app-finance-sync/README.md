# Finance Sync

Este diretório reúne o painel financeiro local, a interface de lançamentos e o servidor SQLite usado pelo dashboard.

## Estrutura

- `dashboard.html`: painel estático em HTML/SVG
- `dashboard-insert.html`: interface para inserir dados sem planilhas
- `finance.db`: banco SQLite local, ignorado pelo Git
- `finance.db-wal` e `finance.db-shm`: arquivos auxiliares do modo WAL, também ignorados pelo Git

## Persistência

O servidor usa SQLite como fonte principal. No Compose, o banco fica no volume persistente `finance_data`.
O `dashboard-insert.html` grava os lançamentos pela API e o `dashboard.html` consulta os mesmos dados.

## Uso no Raspberry

O painel pode ser servido em um container Docker Compose com a pasta deste diretório montada em `/usr/share/nginx/html`.

O arquivo [`dc-finan-dashboard.yaml`](../../dc-local/dc-finan-dashboard.yaml) já está preparado para essa finalidade.

## Backup

O script [`finance-backup.sh`](../../raspberry-scripts/scripts-bin/finance-backup.sh)
cria um snapshot consistente do SQLite dentro do container `dc-finance-api`, valida o
arquivo, compacta e envia para OneDrive ou Google Drive usando `rclone`.

Antes de ativar o cron:

1. Configure o remote no `rclone`.
2. Copie `finance-backup.conf.example` para `/etc/finance-backup.conf` e ajuste `RCLONE_REMOTE`.
3. Instale o script em `/usr/local/bin/finance-backup.sh` com permissao de execucao.
4. Descomente a linha correspondente em `raspberry-scripts/cron.config`.

O backup remoto usa os arquivos `.db.gz`; os arquivos `finance.db-wal` e `finance.db-shm`
nao precisam ser copiados separadamente.
