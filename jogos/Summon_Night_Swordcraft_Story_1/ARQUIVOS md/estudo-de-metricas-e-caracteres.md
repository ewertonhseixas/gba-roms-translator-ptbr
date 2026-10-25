# 📐 Estudo de Métricas de Caracteres por Linha de Diálogo
**Jogo:** Summon Night Swordcraft Story 1  
**Plataforma:** Game Boy Advance (GBA)  
**Teto Operacional de Caracteres (Hard Limit):** 36 caracteres/linha  
**Gerado por:** `metrics_analyzer.py` (Protocolo de Extração)  

---

## 🎯 1. Resumo Executivo das Métricas

| Métrica | Original (EN/JP) | Tradução (PT-BR) | Diferença (%) |
| :--- | :---: | :---: | :---: |
| **Total de Caixas de Diálogo** | `32,889` | `32,889` | `0%` |
| **Total de Linhas Renderizadas** | `33,189` | `33,188` | `+-0.0%` |
| **Média de Caracteres por Linha** | `21.7` | `21.7` | `+0.0%` |
| **Mínimo de Caracteres em Linha** | `1` | `1` | - |
| **Máximo de Caracteres em Linha** | `50` | `38` | - |
| **Percentil 95 (P95) de Caracteres** | `34` | `33` | - |
| **Média de Linhas por Caixa** | `1.0` | `1.0` | - |

---

## 🚦 2. Zonas de Segurança e Limites Recomendados

| Faixa de Caracteres (PT-BR) | Classificação Visual | Condição de Uso |
| :---: | :---: | :--- |
| **1 a 32 caracteres** | 🟢 **Ideal (Seguro)** | Leitura confortável; sem qualquer risco de encostar na moldura. |
| **33 a 35 caracteres** | 🟡 **Atenção (Soft Limit)** | Permitido se a frase contiver caracteres finos (`i`, `l`, `t`, pontuação). |
| **36+ caracteres** | 🔴 **Crítico (Hard Limit)** | **Overflow potencial**. Exige quebra manual de linha (`<br>`) ou síntese. |

---

## ⚠️ 3. Linhas Acima do Limite Detectadas (1 ocorrências)

| Arquivo | Linha | Falante / Contexto | Texto PT-BR | Comprimento | Excesso |
| :--- | :---: | :--- | :--- | :---: | :---: |
| `09-dialogos-cap1-guardioes-compras-e-labirinto.md` | 63 | **Sugar & Protagonista** | `*(Protagonista:)* Eu… ér… Não precisa.` | **38** | +2 |
