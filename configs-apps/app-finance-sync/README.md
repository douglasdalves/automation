# Finance Sync

Este diretório reúne o painel financeiro local, a interface de lançamentos e o servidor SQLite usado pelo dashboard.

## Estrutura

- `dashboard.html`: painel estático em HTML/SVG
- `dashboard-insert.html`: interface para inserir dados sem planilhas
- `finance.db`: banco SQLite usado pelo servidor em desenvolvimento local

## Persistência

O servidor usa SQLite como fonte principal. No Compose, o banco fica no volume persistente `finance_data`.
O `dashboard-insert.html` grava os lançamentos pela API e o `dashboard.html` consulta os mesmos dados.

## Uso no Raspberry

O painel pode ser servido em um container Docker Compose com a pasta deste diretório montada em `/usr/share/nginx/html`.

O arquivo [`dc-finan-dashboard.yaml`](../../dc-local/dc-finan-dashboard.yaml) já está preparado para essa finalidade.
