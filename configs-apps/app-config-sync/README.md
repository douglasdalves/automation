# App Config Sync

Sincroniza arquivos de configuracao e scripts publicos para os diretorios usados pelos servicos.

O `sync.conf` define quais arquivos sao copiados. O `telegram.conf` nao faz parte da sincronizacao: mantenha os tokens somente no servidor.

## Instalar no Raspberry Pi

```bash
sudo mkdir -p /etc/app-config-sync
sudo cp sync.conf /etc/app-config-sync/sync.conf
sudo cp sync-configs.sh /usr/local/bin/sync-configs.sh
sudo chmod +x /usr/local/bin/sync-configs.sh
sudo cp app-config-sync.service app-config-sync.path /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now app-config-sync.path
```

Para testar imediatamente:

```bash
sudo systemctl start app-config-sync.service
sudo systemctl status app-config-sync.service
```

## Adicionar outra aplicacao

Adicione uma linha em `sync.conf` no formato:

```text
nome|/caminho/dos/arquivos|/caminho/do/destino
```

Depois adicione o diretorio de origem como outro `PathChanged` em `app-config-sync.path` e reinstale a unidade:

```bash
sudo cp sync.conf /etc/app-config-sync/sync.conf
sudo cp app-config-sync.path /etc/systemd/system/app-config-sync.path
sudo systemctl daemon-reload
sudo systemctl restart app-config-sync.path
```

O script sincroniza somente os arquivos definidos em `sync.conf`, preservando outros arquivos nos destinos. Arquivos `.sh` recebem permissao executavel e arquivos `.conf` recebem permissao `644`.
