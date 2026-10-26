# Finance Sync

Este diretório reúne o painel financeiro local, a interface de lançamentos e o servidor SQLite usado pelo dashboard.

## Estrutura

- `dashboard.html`: painel estático em HTML/SVG
- `dashboard-insert.html`: interface para inserir dados sem planilhas
- `cart-invest.html`: carteira de investimentos, acessível pelo painel principal
- `dashboard.css`, `dashboard-insert.css` e `cart-invest.css`: estilos separados para cada interface
- `finance.db`: banco SQLite local, ignorado pelo Git
- `finance.db-wal` e `finance.db-shm`: arquivos auxiliares do modo WAL, também ignorados pelo Git
- `investments.json`: operações importadas, salvo localmente e ignorado pelo Git
- `fixed_income.json`: snapshots de posições importados dos PDFs, salvo localmente e ignorado pelo Git

## Persistência

O servidor usa SQLite como fonte principal. No Compose, o banco fica no volume persistente `finance_data`.
O `dashboard-insert.html` grava os lançamentos pela API e o `dashboard.html` consulta os mesmos dados.
O `cart-invest.html` importa planilhas `.xlsx` ou `.csv` pela API, que salva os dados em
`investments.json` no servidor. A carteira lê esse arquivo pela API com cache desativado;
o arquivo não é servido diretamente pelo Nginx e não deve ser versionado.

Na seção Carteira do PDF, importe um ou mais relatórios consolidados do BTG (PDF). O relatório
deve conter as posições de renda fixa, renda variável e previdência apresentadas no consolidado.
O PDF é processado no navegador; apenas os dados extraídos (instituição, produto, emissor,
vencimento, taxa e saldos) são enviados para `fixed_income.json`. Cada relatório alimenta
o histórico pela data de atualização impressa no documento; importar novamente a mesma data
substitui aquele snapshot. Para montar a evolução desde o início, selecione os relatórios
mensais anteriores junto com o atual. O painel não estima saldos de meses sem relatório.
Somente CDB e RDB do PDF entram no gráfico e nas métricas anuais, com a opção
“Estimar CDB/RDB nas abas anuais”. A data de aporte é estimada como vencimento menos dois
anos, e o valor usado é o saldo bruto atual informado no PDF. Como o relatório não informa
data/valor original da aplicação nem os resgates, essas linhas aparecem como estimativas,
não como movimentações confirmadas. As demais classes do relatório permanecem apenas no
histórico de posições do PDF.

## Uso no Raspberry

O painel pode ser servido em um container Docker Compose com a pasta deste diretório montada em `/usr/share/nginx/html`.

O arquivo [`dc-finan-dashboard.yaml`](../../dc-local/dc-finan-dashboard.yaml) já está preparado para essa finalidade.

## Backup

O script [`finance-backup.sh`](../../raspberry-scripts/scripts-bin/finance-backup.sh)
cria um snapshot consistente do SQLite dentro do container `dc-finance-api`, valida o
arquivo, compacta e envia para OneDrive ou Google Drive usando `rclone`.

Antes de ativar o cron:

1. Configure o remote no `rclone`.

2. Copie `finance.conf.example` para `/etc/finance-backup.conf` e ajuste `RCLONE_REMOTE`.
3. Instale o script em `/usr/local/bin/finance-backup.sh` com permissao de execucao.
4. Descomente a linha correspondente em `raspberry-scripts/cron.config`.

O backup remoto usa os arquivos `.db.gz`; os arquivos `finance.db-wal` e `finance.db-shm`
nao precisam ser copiados separadamente.
