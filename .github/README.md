# GitHub Actions Workflows - Documentation

Este diretório contém workflows refatorados e melhorados para automação do projeto OpenVPN Manager.

## 📁 Estrutura dos Workflows

### 1. `release-new.yml` - Workflow de Release Refatorado

**Objetivo:** Substitui o workflow original com uma arquitetura modular e validações robustas.

**Features:**
- ✅ **Validação completa:** Verifica consistência de versões e estrutura do projeto
- ✅ **Datas corretas:** Corrige automaticamente timestamps futuros
- ✅ **Build modular:** Separado em jobs independentes
- ✅ **Dry run:** Permite testar sem criar release
- ✅ **Validação de artefatos:** Verifica integridade dos pacotes gerados

**Como usar:**
```bash
# Release patch (0.2.6 → 0.2.7)
gh workflow run release-new.yml -f version_type=patch

# Release minor (0.2.6 → 0.3.0)
gh workflow run release-new.yml -f version_type=minor

# Release major (0.2.6 → 1.0.0)
gh workflow run release-new.yml -f version_type=major

# Release com versão customizada
gh workflow run release-new.yml -f custom_version=1.0.0

# Dry run (testar sem criar release)
gh workflow run release-new.yml -f version_type=patch -f dry_run=true

# Pre-release
gh workflow run release-new.yml -f version_type=patch -f prerelease=true
```

**Jobs:**
1. **validate-and-prepare:** Valida projeto e calcula nova versão
2. **update-version:** Atualiza arquivos de versão
3. **build-packages:** Constrói pacotes .deb, .whl e .tar.gz
4. **create-release:** Cria release no GitHub
5. **dry-run-summary:** Mostra o que seria feito (modo dry-run)

### 2. `validate.yml` - Validação Contínua

**Objetivo:** Executa validações automáticas em push/PR.

**Features:**
- ✅ Validação de estrutura do projeto
- ✅ Consistência de versões
- ✅ Sintaxe Python
- ✅ Estilo de código
- ✅ Metadados Debian
- ✅ Teste de build

**Execução:** Automática em push/PR para main/develop

### 3. `maintenance.yml` - Manutenção Automática

**Objetivo:** Tarefas de manutenção automática e limpeza.

**Features:**
- ✅ Correção automática de datas futuras
- ✅ Limpeza de artefatos antigos
- ✅ Validação de consistência
- ✅ Verificação de dependências
- ✅ Relatório de manutenção

**Execução:**
- **Automática:** Domingos às 02:00 UTC
- **Manual:** Via workflow_dispatch

**Como executar manualmente:**
```bash
# Manutenção completa
gh workflow run maintenance.yml

# Apenas corrigir datas
gh workflow run maintenance.yml -f fix_dates=true -f cleanup_artifacts=false

# Verificar dependências
gh workflow run maintenance.yml -f update_dependencies=true
```

## 🔧 Principais Melhorias

### Problemas Corrigidos

1. **❌ Datas futuras:** O workflow original criava timestamps de 2025
   - **✅ Solução:** Validação e correção automática de datas

2. **❌ Estrutura monolítica:** Tudo em um job gigante
   - **✅ Solução:** Jobs modulares com dependências claras

3. **❌ Falta de validação:** Build podia falhar silenciosamente
   - **✅ Solução:** Validações extensivas em cada etapa

4. **❌ Sem rollback:** Falhas deixavam o projeto em estado inconsistente
   - **✅ Solução:** Validação prévia e transações atômicas

5. **❌ Dificuldade de debug:** Logs confusos e longos
   - **✅ Solução:** Logs estruturados e step summary

### Melhorias de Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  validate.yml   │    │ release-new.yml  │    │ maintenance.yml │
│                 │    │                  │    │                 │
│ • Syntax check  │───▶│ • Version calc   │◀───│ • Fix dates     │
│ • Style check   │    │ • Build packages │    │ • Clean artifacts│
│ • Structure     │    │ • Create release │    │ • Consistency   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
       ▲                         │                       ▲
       │                         ▼                       │
   On Push/PR            Manual/Auto Trigger      Weekly Schedule
```

## 📋 Checklist de Migração

### Passo 1: Backup
```bash
# Backup do workflow atual
cp .github/workflows/release.yml .github/workflows/release-backup.yml
```

### Passo 2: Teste o Novo Workflow
```bash
# Teste em modo dry-run
gh workflow run release-new.yml -f version_type=patch -f dry_run=true
```

### Passo 3: Validação
```bash
# Execute validação manual
gh workflow run validate.yml
```

### Passo 4: Primeira Release
```bash
# Primeira release com novo workflow
gh workflow run release-new.yml -f version_type=patch
```

### Passo 5: Limpeza (Opcional)
```bash
# Remover workflow antigo após confirmação
rm .github/workflows/release.yml
mv .github/workflows/release-new.yml .github/workflows/release.yml
```

## 🚨 Pontos de Atenção

### Permissões Necessárias
O repositório precisa das seguintes permissões:
- `contents: write` - Para criar tags e commits
- `actions: write` - Para gerenciar artifacts

### Secrets Necessários
- `GITHUB_TOKEN` - Automático, não precisa configurar

### Configurações Recomendadas

#### Branch Protection
```yaml
# .github/branch-protection.yml
main:
  required_status_checks:
    - validate-structure
    - test-build
  enforce_admins: false
  required_pull_request_reviews:
    required_approving_review_count: 1
```

#### Dependabot (Opcional)
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## 🔍 Monitoramento e Debug

### Logs Estruturados
Cada job gera logs organizados com emojis para fácil identificação:
- 🔍 Validação
- 📝 Atualização
- 🔨 Build
- 🚀 Release
- 🧹 Limpeza

### Step Summary
Todos os workflows geram resumos estruturados visíveis na interface do GitHub.

### Artifacts
- **version-files:** Arquivos atualizados (1 dia)
- **build-artifacts:** Pacotes gerados (7 dias)
- **test-build-artifacts:** Builds de teste (1 dia)

## 📞 Suporte e Contribuição

### Problemas Comuns

1. **Erro de permissão no push:**
   ```bash
   # Verificar se o token tem permissões suficientes
   git config --list | grep user
   ```

2. **Build falhando:**
   ```bash
   # Executar localmente primeiro
   ./build.sh
   ```

3. **Versões inconsistentes:**
   ```bash
   # Usar o script de versão
   ./version.sh set 0.2.7
   ```

### Contribuindo

Para melhorar os workflows:
1. Teste localmente com `act` (GitHub Actions local runner)
2. Use dry-run mode para validar mudanças
3. Documente novas features neste README
4. Adicione testes quando aplicável

---

**Última atualização:** September 2025
**Versão dos workflows:** 2.0
**Compatibilidade:** GitHub Actions v4+