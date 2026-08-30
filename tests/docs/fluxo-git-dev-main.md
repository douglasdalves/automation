# Fluxo recomendado: testes em desenvolvimento e produção em main

## Objetivo

Proteger a branch `main` para que ela receba apenas código já validado, evitando subir testes, arquivos de validação ou dependências locais por acidente.

## Regra principal

- `main` = produção / servidor
- `develop` = integração / testes / validação
- `feature/*` = trabalho de desenvolvimento

Fluxo ideal:

1. criar branch a partir de `develop`
2. desenvolver e testar localmente
3. abrir PR para `develop`
4. validar os testes
5. quando estiver estável, abrir PR de `develop` para `main`
6. deploy apenas a partir de `main`

---

## Estrutura de branches

```bash
git checkout develop
git pull origin develop
git checkout -b feature/ajuste-docker

# desenvolvimento
# testes locais
# commit

git push origin feature/ajuste-docker
# abrir PR para develop
```

Depois:

```bash
git checkout develop
git pull origin develop
git merge --no-ff feature/ajuste-docker

git push origin develop
# abrir PR para main quando estiver pronto para producao
```

---

## Proteção da branch main

No GitHub, a branch `main` deve estar protegida com:

- Require a pull request before merging
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Do not allow bypassing the above settings
- Restrict who can push to matching branches

Assim, o push direto em `main` fica bloqueado e os testes se tornam parte da validação antes do merge.

---

## Como evitar testes subirem acidentalmente para main

A estratégia correta é separar o ambiente de produção do ambiente de desenvolvimento:

- `main` não recebe testes locais
- `develop` reúne integração e validação
- `main` só recebe releases aprovadas

Se uma branch de feature for aberta diretamente para `main`, os arquivos de teste podem entrar junto. Por isso, o fluxo seguro é:

```text
feature/*  ->  develop  ->  main
```

Nunca:

```text
feature/*  ->  main
```

---

## Uso do .venv no Windows

O ambiente virtual local deve ser usado para os testes e validação no Windows. Ele isola as dependências do projeto e não polui a instalação global do Python.

### Criar ambiente local

```powershell
cd c:\usebash\automation
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Instalar dependências de teste

```powershell
python -m pip install --upgrade pip
pip install pytest
```

Se o projeto tiver dependências da aplicação:

```powershell
pip install -r requirements.txt
```

### Rodar testes

```powershell
cd c:\usebash\automation\homelab-mcp
python -m pytest tests/test_docker.py -q
```

### Desativar ambiente

```powershell
deactivate
```

---

## Vantagem do .venv

- isola bibliotecas de teste do sistema
- evita instalar pacotes no Python global do Windows
- facilita recriar o ambiente quando necessário
- não entra no git
- não vai para a branch de produção

Em resumo:

```text
.venv = ambiente local de teste e desenvolvimento
main = ambiente de produção
```

---

## Recomendação final

Para este repositório, a melhor prática é:

- manter `main` protegida
- usar `develop` como branch de integração
- rodar testes em `.venv` local no Windows
- só depois fazer merge para `main`
- fazer deploy do Raspberry Pi com `main`

Isso garante que a máquina de produção não receba arquivos de teste, dependências locais e validações acidentais.
