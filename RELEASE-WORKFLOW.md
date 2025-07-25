# Release Workflow Guide

## 🚀 Como Criar uma Release

Este projeto usa GitHub Actions para automatizar releases, mas respeita as branch protection rules da `main`.

### 📋 Fluxo Recomendado

#### **Opção 1: Release via Branch Main (Recomendado)**
1. **Execute o workflow na `main`**:
   - Vá em **Actions** → **Create Release** → **Run workflow**
   - Branch: `main`
   - Version type: `patch`/`minor`/`major`
   - Execute

2. **O workflow irá**:
   - ✅ Gerar o `.deb` package
   - ✅ Criar a release no GitHub
   - ✅ Fazer upload de todos os artifacts
   - ⚠️ **NÃO fará push** para `main` (protegida)

#### **Opção 2: Release via Branch de Feature**
1. **Crie uma branch para a release**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b release/v0.2.4
   git push origin release/v0.2.4
   ```

2. **Execute o workflow na branch de release**:
   - Branch: `release/v0.2.4`
   - O workflow fará push das mudanças para esta branch

3. **Crie um PR**:
   - De `release/v0.2.4` para `main`
   - Merge após aprovação

### 🎯 Arquivos Gerados

Cada release gera automaticamente:
- 📦 **`.deb` package** - Instalador Debian/Ubuntu
- 🐍 **`.whl` file** - Python wheel
- 📄 **`.tar.gz`** - Source distribution
- 📝 **Release notes** automáticas

### 🔧 Versionamento

O projeto usa [Semantic Versioning](https://semver.org/):
- **patch** (0.2.3 → 0.2.4) - Bug fixes
- **minor** (0.2.3 → 0.3.0) - New features
- **major** (0.2.3 → 1.0.0) - Breaking changes

### 📂 Arquivos Atualizados Automaticamente

O workflow atualiza:
- `VERSION` - Versão principal
- `config.py` - Configuração da aplicação
- `pyproject.toml` - Metadados Python
- `setup.py` - Setup script
- `CHANGELOG.md` - Log de mudanças
- `debian/changelog` - Log Debian

### 💡 Dicas

- ✅ Sempre teste localmente com `./build.sh` antes da release
- ✅ Use `./version.sh show` para ver a versão atual
- ✅ O `.deb` é auto-contido (inclui PyQt6 wheels)
- ✅ Branch protection em `main` é respeitada automaticamente

### 🚨 Troubleshooting

**Se o build falhar**:
1. Verifique logs no GitHub Actions
2. Teste localmente: `./build.sh`
3. Verifique dependências: `python -m build --sdist --wheel`

**Se precisar reverter**:
```bash
git tag -d v0.2.4  # Remove tag local
git push origin :refs/tags/v0.2.4  # Remove tag remota
```
