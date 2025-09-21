# GitHub Actions Workflows - Documentation

## 🚨 Problemas Resolvidos

### ✅ Actions Depreciadas (CORRIGIDO)
- **Problema:** `actions/upload-artifact@v3` estava depreciado
- **Solução:** Atualizado para `@v4` em todos os workflows
- **Status:** ✅ RESOLVIDO

### ✅ Triggers Limitados (CORRIGIDO)  
- **Problema:** Só funcionava manual ou PR na main
- **Solução:** Expandido para múltiplas branches e triggers
- **Status:** ✅ RESOLVIDO

### ✅ Datas Futuras (CORRIGIDO)
- **Problema:** Timestamps de 2025 causavam falhas no deploy
- **Solução:** Correção automática de datas + validação
- **Status:** ✅ RESOLVIDO

## 📁 Estrutura dos Workflows

### 1. `release.yml` - Release Principal 🚀

**Triggers:**
- ✅ Manual (workflow_dispatch)
- ✅ Push em tags (v*.*.*)
- ✅ PR merged (main, develop, release/*, hotfix/*)

**Uso:**
```bash
# Release normal
gh workflow run release.yml -f version_type=patch

# Teste sem release
gh workflow run release.yml -f version_type=patch -f dry_run=true

# Release personalizado
gh workflow run release.yml -f custom_version=1.0.0

# Pre-release
gh workflow run release.yml -f version_type=patch -f prerelease=true
```

### 2. `hotfix.yml` - Release Rápido ⚡

**Para:** Correções urgentes que precisam de release imediato

**Triggers:**
- ✅ Push automático em branches `hotfix/*`
- ✅ Manual (workflow_dispatch)

**Uso:**
```bash
# Automático ao criar branch hotfix
git checkout -b hotfix/critical-bug
git push -u origin hotfix/critical-bug  # Dispara automaticamente!

# Manual
gh workflow run hotfix.yml

# Forçar release mesmo com problemas
gh workflow run hotfix.yml -f force_release=true
```

### 3. `validate.yml` - Validação Contínua ✅

**Para:** Validar código em pushes e PRs

**Triggers:** Automático em:
- Push: main, develop, feature/*, bugfix/*, hotfix/*, release/*
- PR: para main, develop

### 4. `maintenance.yml` - Manutenção 🧹

**Para:** Limpeza automática e correções

**Execução:** Domingos às 02:00 UTC + manual

## 🎯 Como Usar Agora

### Situação Normal - Release Planejado
```bash
# 1. Desenvolvimento normal
git checkout -b feature/nova-funcionalidade
# ... trabalhar ...
git push origin feature/nova-funcionalidade

# 2. Criar PR (validação automática executa)
gh pr create --title "Nova funcionalidade"

# 3. Após merge, criar release
gh workflow run release.yml -f version_type=patch
```

### Situação Urgente - Hotfix
```bash
# 1. Criar branch de hotfix (dispara release automático!)
git checkout -b hotfix/bug-critico
# ... corrigir bug ...
git push -u origin hotfix/bug-critico  # 🚀 Release automático!

# 2. Ou manual se precisar de controle
gh workflow run hotfix.yml -f version_type=patch
```

### Testar Antes de Release
```bash
# Dry run - simula tudo sem criar release
gh workflow run release.yml -f version_type=patch -f dry_run=true
```

## 🔄 Fluxo de Trabalho Recomendado

```
Development → Hotfix (se urgente) → Release
     ↓              ↓                   ↓
   feature/*    hotfix/*          release.yml
     ↓              ↓                   ↓  
  validate.yml   hotfix.yml        Full Release
     ↓              ↓                   ↓
   PR → main    Auto Release      Manual Release
```

## 🚨 Troubleshooting

### Erro: "deprecated version of actions/upload-artifact"
✅ **RESOLVIDO:** Atualizado para v4 em todos os workflows

### Erro: "This workflow can only be triggered manually"
✅ **RESOLVIDO:** Adicionados triggers para múltiplas branches

### Erro: "Future date in changelog"
✅ **RESOLVIDO:** Correção automática de datas implementada

### Workflow não executa
**Verificar:**
1. Branch está na lista de triggers?
2. Arquivo workflow tem sintaxe correta?
3. Permissões do repositório estão OK?

**Solução rápida:**
```bash
# Forçar execução manual
gh workflow run release.yml
gh workflow run hotfix.yml  # Para urgências
```

## 📊 Status dos Workflows

| Workflow | Status | Última Atualização | Actions Version |
|----------|--------|-------------------|-----------------|
| release.yml | ✅ Funcionando | Sept 2025 | v4 |
| hotfix.yml | ✅ Funcionando | Sept 2025 | v4 |
| validate.yml | ✅ Funcionando | Sept 2025 | v4 |
| maintenance.yml | ✅ Funcionando | Sept 2025 | v2 |

## 🎉 Resumo das Melhorias

### Antes (Problemas)
- ❌ Actions depreciadas (v3)
- ❌ Só funcionava manual/PR main
- ❌ Datas futuras quebravam deploy
- ❌ Sem opção de hotfix rápido
- ❌ Validação limitada

### Agora (Soluções)
- ✅ Actions atualizadas (v4)
- ✅ Funciona em qualquer branch
- ✅ Datas corrigidas automaticamente
- ✅ Hotfix automático em segundos
- ✅ Validação robusta + dry-run

---

**💡 Dica:** Para releases urgentes, use `hotfix/*` branches que disparam release automático!

**🔗 Links Úteis:**
- [GitHub Actions docs](https://docs.github.com/en/actions)
- [Workflows do projeto](./workflows/)

**Última atualização:** September 21, 2025