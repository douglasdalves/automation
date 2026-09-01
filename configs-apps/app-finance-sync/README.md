# Finance Sync

Este diretório reúne o painel financeiro local e o script que converte a planilha Excel em JSON para uso em um dashboard servido na rede.

## Estrutura

- `dashboard.html`: painel estático em HTML/SVG
- `finance-data.json`: arquivo gerado pela conversão
- `convert_finance_xlsx_to_json.py`: converte a planilha Excel em JSON
- `requirements.txt`: dependências do script

## Requisitos

```bash
python -m pip install -r requirements.txt
```

## Gerar o JSON

### Arquivo local

```bash
python convert_finance_xlsx_to_json.py "C:/Users/SeuUsuario/OneDrive/2026_Contas.xlsx" --output finance-data.json
```

### Link compartilhado do OneDrive

```bash
python convert_finance_xlsx_to_json.py "https://1drv.ms/x/c/SEU_LINK_AQUI?e=SEU_TOKEN" --output finance-data.json
```

O script detecta URLs do OneDrive e faz o download do arquivo antes de ler o Excel. Isso permite usar o link compartilhado diretamente sem precisar baixar o arquivo manualmente.

A planilha esperada deve ter:

- uma aba com colunas: `mes`, `receita`, `contas_mensais`, `extras`, `despesas`, `saldo`, `reserva`, `investimentos`
- uma aba opcional de categorias com colunas: `item`, `total`
- uma aba opcional de carteira com colunas: `item`, `valor` e, quando existir, `mes`

## Uso no Raspberry

O painel pode ser servido em um container Docker Compose com a pasta deste diretório montada em `/usr/share/nginx/html`.

O arquivo [`dc-finan-dashboard.yaml`](../../dc-local/dc-finan-dashboard.yaml) já está preparado para essa finalidade.
