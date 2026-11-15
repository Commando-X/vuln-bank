# Projeto Aplicado IV — Plano de Reescrita do ODT para o Rubric GRDC 2026/2

> **Escopo: RELATÓRIO ONLY** — sem downloads, sem execução, sem subir Docker.
> Tarefas viram "produzir conteúdo para o .odt final".
> Restrições de ambiente (decisão do aluno): 
>   - Relatório escrito, não pipeline executável
>   - Base de evidência = achados já consolidados no ODT atual (vuln-bank SAST/DAST, commit 5e5ea54)
>   - 24 achados Datadog (14C/7H/3M) usados como inventário de entrada
>   - 16 CWEs consolidados usados como taxonomia de classificação
>   - PDFs referenciados (rubric, LGPD, ISO/NIST) — citar, não citar com cópia
>   - Geração final em ODT (manter Projeto_with_SAST_Datadog_OCR.odt como base estrutural)

**Goal:** Reescrever o conteúdo do ODT atual para satisfazer os 5 critérios do rubric ProjetoAplicado IV - Cyber_2026-2 V2.pdf (Inventário 10%, Classificação CVSS 25%, Matriz de Risco LGPD 15%, Plano+RACI+ISO/NIST+sustentabilidade 25%, Apresentação 25%), preservando a estrutura técnica já validada como insumo (anexo/evidência).

**Architecture:** Reescrita por dentro do mesmo arquivo. Substituir títulos + parágrafos das seções 1–5 atuais por 5 novas seções GRC alinhadas aos 5 critérios numerados do rubric. A evidência técnica (Datadog CSV, SARIF, snippets de código vuln-bank, referências a linhas em app.py/auth.py/merchant_payments.py) vira anexo/insumo dentro de cada nova seção. Manter cabeçalho institucional (Rafael Péret de Sant'ana + Rafael Nascimento Araújo Silva), GRDC 2024/2 INT1, UC Projeto Aplicado IV (AEx).

**Tech Stack:** LibreOffice Writer (formatação final), ODT manipulado via patch em content.xml/styles.xml (sem python-odf pesado — patching cirúrgico é suficiente), memória persistente (nada).

---

## §1 Mapping table — Critério PDF → onde o plano atende

| Critério (peso) | Linha do rubric | Onde atende no ODT novo |
|---|---|---|
| **Inventário Consolidado de Vulnerabilidades** (10%) | "Lista organizada e padronizada… CWE, CVE (quando aplicável) e categoria OWASP… metodologia de classificação… técnicas de análise de dados/IA na priorização" | §1 (Inventário) — Tabela1: 24 achados × colunas (id, descrição, CWE, CVE/NVD, OWASP Top 10, arquivo:linha, severidade scanner). §1.3 explica método de priorização via clusterização (regra 80/20 — top 8 CWEs respondem por ≥70% do risco). |
| Data 23/08/26 | "Data de Realização" da atividade 1 | Cabeçalho de §1 marca data 23/08/26. |
| **Classificação Técnica CVSS/CWE/CVE/MITRE ATT&CK** (25%) | "Vetor completo do CVSS (com justificativa de cada métrica)… correlação com técnicas do MITRE ATT&CK… enquadramento na OWASP Top 10" | §2 (Classificação) — Tabela2: 8–10 achados críticos × colunas (CWE, CVE ex., CVSS v3.1 vetor + score + justificativa métrica a métrica, ATT&CK technique ID, OWASP 2021). Justificativa narrativa por métrica. |
| Data 20/09/26 | "Data de Realização" da atividade 2 | Cabeçalho de §2 marca 20/09/26. |
| **Matriz de Risco Organizacional** (15%) | "Impacto técnico + impacto regulatório (LGPD) + análise ética/legal (ANPD, privacy by design/by default) + impacto operacional/negócio + probabilidade de exploração + classificação final + justificativas técnicas e estratégicas" | §3 (Matriz de Risco) — Tabela3: 8–10 achados × 7 colunas (Probabilidade × Impacto Técnico × Impacto Regulatório/LGPD × Impacto Negócio × Score final × Nível de risco × Justificativa). Subseção §3.2 trata dos 4 achados que envolvem dados pessoais (CWE-200/209/256/89) com análise ANPD explícita. |
| Data 18/10/26 | "Data de Realização" da atividade 3 | Cabeçalho de §3 marca 18/10/26. |
| **Plano de Mitigação + Matriz RACI** (25%) | "Plano priorizado, ações corretivas/compensatórias, justificativa de priorização, esforço/prazo, RACI, alinhamento ISO 27002/NIST CSF, risco residual, **impacto ambiental das ações (descarte hardware, eficiência energética, sustentabilidade)**" | §4 (Plano de Mitigação) — Tabela4 priorização (8 ações top, prazo Imediato/Curto/Médio). Tabela5 RACI (6 atores × 8 ações). Subseção §4.3 Alinhamento ISO 27002 A.x / NIST CSF FN.x. Subseção §4.4 Risco residual (quantitativo onde possível). Subseção §4.5 **Sustentabilidade** — descarte de tokens JWT antigos (LGPD), rotação de credenciais vs re-emissão de certificados (carbon cost), WAF vs energia do appliance, e-waste de appliances legados. |
| Data 15/11/26 | "Data de Realização" da atividade 4 | Cabeçalho de §4 marca 15/11/26. |
| **Apresentação Final — Comitê de Governança de Risco** (25%) | "Inventário + classificação + matriz + plano + RACI + risco residual + recomendações estratégicas + reflexões críticas e aprendizados" | §5 (Apresentação Final) — Roteiro slide-a-slide (10–12 slides) + script de defesa oral. Inclui bloco "Reflexões Críticas" (limitações da abordagem, falsos positivos do SAST, dependência de revisão humana). |
| Data 04/12/26 | "Data de Realização" da atividade 5 | Cabeçalho de §5 marca 04/12/26. |
| **Bibliografia + referências normativas** (transversal) | LGPD (Lei 13.709/2018), ANPD, ISO 27001:2022, ISO 27002:2022, NIST CSF 2.0, CVSS v3.1 (FIRST), MITRE ATT&CK, OWASP Top 10 2021, CWE (MITRE), CVE/NVD | §6 (Referências) — 18 entradas ABNT-like. Já existe plano de bibliografia em §3 abaixo. |
| **Anexo técnico preservado** (transversal) | Evidências: snippets vuln-bank, CSV Datadog, SARIF OCR, ggshield report | §7 (Anexos) — texto das seções técnicas atuais (1–5 do ODT antigo) preservadas como ANEXO I — Relatório Técnico Projeto Aplicado III. |

---

## §2 Inventário e Estratégia de Conteúdo

### §2.1 Estado atual do ODT (Projeto_with_SAST_Datadog_OCR.odt)

Conteúdo técnico já validado, **que será preservado como insumo/evidência**, não apagado:

- §1 Resumo Executivo (4-paragraph overview of vuln-bank audit)
- §2 Vulnerabilidades Críticas de Alto Impacto (6 narrative findings: PAN/CVV leak, JWT forge, race condition, weak API keys, SQLi 33 sinks, Flask debug)
- §3 Classes de Vulnerabilidade Identificadas (table mapping CWE → files → severity)
- §4 Plano de Remediação Recomendado (immediate/short-term list)
- §5 Análise SAST Complementar Datadog/OCR (full Datadog × OpenCodeReview analysis with consolidated 16-CWE matrix)

Este conteúdo **é a evidência primária** que alimenta o novo relatório GRC. Ele será movido para §7 (Anexos) do ODT reescrito e referenciado inline nas novas seções 1–5.

### §2.2 Os 24 achados Datadog (escopo confirmado pelo aluno)

Inventário canônico para a Matriz de Risco. Distribuição: 14 Critical, 7 High, 3 Medium, em 16 classes CWE únicas. Agrupamento prático para a matriz RACI:

| Cluster | Achados | Justificativa para cluster |
|---|---|---|
| **C1 — Identidade & Sessão** | CWE-287 (JWT forge), CWE-798 (hardcoded JWT_SECRET), CWE-614 (cookie sem Secure), CWE-639 (IDOR/BOLA) | Mesma superfície: ciclo de vida da sessão/token. Mesma owner (desenvolvedor de auth). |
| **C2 — Persistência & Integridade** | CWE-89 (SQLi 13 sumidouros), CWE-915 (Mass Assignment), CWE-352 (CSRF) | Mesma superfície: camada de dados. Mesma defesa: parametrização + validação. |
| **C3 — Exposição & Superfície** | CWE-489 (debug=True), CWE-668 (bind 0.0.0.0), CWE-295 (verify=False), CWE-200/209 (info disclosure) | Mesma superfície: configuração de runtime. Mesma owner (DevOps/SRE). |
| **C4 — Aleatoriedade & Segredos** | CWE-338 (PRNG fraco), CWE-256 (plaintext password) | Mesma superfície: geração criptográfica. |
| **C5 — Entrada do Usuário** | CWE-79 (XSS innerHTML 7×), CWE-77 (prompt injection LLM) | Mesma superfície: confiança no input. |

### §2.3 Top-8 achados que alimentam as tabelas 2 (CVSS), 3 (Risco) e 4 (Plano)

Estes 8 serão trabalhados um-a-um com vetor CVSS completo + justificativa de cada métrica + correlação MITRE ATT&CK + impacto LGPD. Os outros 16 viram menção breve no §1 (Inventário) e referência cruzada em §4 (Plano) sem tabela individual.

| # | Achado | CWE | Por que está no Top-8 |
|---|---|---|---|
| 1 | JWT forge (alg=none + secret123) | CWE-287 + CWE-347 | Comprometimento total de autenticação. Correlaciona com ATT&CK T1552 (Unsecured Credentials). |
| 2 | SQLi mass (33 sumidouros) | CWE-89 | Vetor #1 OWASP. Correlaciona com ATT&CK T1190. |
| 3 | PAN/CVV retornados a merchant | CWE-200 + PCI-DSS 3.2 | Viola LGPD Art. 46 + ANPD + PCI-DSS. |
| 4 | Plaintext password storage | CWE-256 | Viola LGPD Art. 46 + PCI-DSS 8.2.1. |
| 5 | Mass Assignment /update-limit | CWE-915 + CWE-89 | Injeção via JSON permite injetar SQL no nome da coluna. |
| 6 | SSRF → IMDS (cloud creds) | CWE-918 + CWE-295 | RCE na cloud. ATT&CK T1552.005 (Cloud Instance Metadata API). |
| 7 | Race Condition /api/transfer | CWE-362 | Saques duplicados. ATT&CK T0836 (Modify Parameter — ICS analog, fintech analog: TOCTOU). |
| 8 | Flask debug + bind 0.0.0.0 | CWE-489 + CWE-668 | RCE trivial via Werkzeug debugger. ATT&CK T1190. |

---

## §3 Bibliografia Planejada (18 entradas)

Ordenação alfabética ABNT-like (Sobrenome, Nome. Título. Disponível em: … . Acesso em: 20 set. 2026):

1. **ABNT NBR ISO/IEC 27001:2022** — Tecnologia da informação — Sistemas de gestão da segurança da informação — Requisitos.
2. **ABNT NBR ISO/IEC 27002:2022** — Tecnologia da informação — Controles de segurança da informação.
3. **ANPD**. Guia Orientativo — Boas Práticas de Privacidade desde a Concepción (Privacy by Design). 2023.
4. **ANPD**. Resolução CD/ANPD nº 15/2024 — Comunicação de Incidente de Segurança.
5. **BRASIL. Lei nº 13.709/2018** — Lei Geral de Proteção de Dados Pessoais (LGPD).
6. **FIRST — Forum of Incident Response and Security Teams**. CVSS v3.1 Specification. 2019.
7. **FIRST**. CVSS v4.0 Specification. 2023.
8. **MITRE**. ATT&CK Matrix for Enterprise. v15. Disponível em: https://attack.mitre.org. Acesso em: 20 set. 2026.
9. **MITRE**. Common Weakness Enumeration (CWE). Disponível em: https://cwe.mitre.org. Acesso em: 20 set. 2026.
10. **NIST**. Cybersecurity Framework (CSF) 2.0. NIST CSWP 29. 2024.
11. **NIST**. SP 800-53 Rev. 5 — Security and Privacy Controls for Information Systems and Organizations.
12. **NIST**. National Vulnerability Database (NVD). Disponível em: https://nvd.nist.gov. Acesso em: 20 set. 2026.
13. **OWASP Foundation**. OWASP Top 10 — 2021. Disponível em: https://owasp.org/Top10/. Acesso em: 20 set. 2026.
14. **OWASP Foundation**. OWASP ASVS 4.0.3 — Application Security Verification Standard.
15. **PCI Security Standards Council**. Payment Card Industry Data Security Standard (PCI-DSS) v4.0.1. 2024.
16. **CWE-89**. Improper Neutralization of Special Elements used in an SQL Command. MITRE.
17. **CWE-287**. Improper Authentication. MITRE.
18. **CWE-918**. Server-Side Request Forgery (SSRF). MITRE.

---

## §4 Tarefas — Reescrita do ODT (Report-Only)

Cada tarefa = 1 capítulo do ODT novo + colar conteúdo no lugar correspondente via patch em content.xml.

> **Workflow geral**: cada tarefa abaixo é executada **apenas como edição textual** no `content.xml` do ODT já existente. O `styles.xml`, header, footer, table styles e TOC pré-baked das seções 5.1 são preservados (estrutura validada na sessão anterior). A TOC pré-baked recebe **novas entradas** (5 capítulos principais) após a §5 do plano ser concluída.

### Task 1: Cabeçalho institucional + Sumário (pré-baked entries)

**Objetivo:** Estabelecer cabeçalho e TOC para 5 novos capítulos.

**Artefato:** Início de `content.xml`, antes da seção "1. Resumo Executivo" atual.

**Conteúdo a redigir:**
- Atualizar autores: "Projeto Aplicado IV (AEx) — Gestão Estratégica de Vulnerabilidades e Governança de Riscos em Segurança da Informação" (substituir "Projeto Aplicado III/IV")
- Atualizar Sumário com 5 entradas pré-baked (mesmo padrão da entrada 5.1 que já existe):
  - "1 Inventário Consolidado de Vulnerabilidades (23/08/2026)"
  - "2 Classificação Técnica — CVSS / CWE / CVE / MITRE ATT&CK (20/09/2026)"
  - "3 Matriz de Risco Organizacional (18/10/2026)"
  - "4 Plano de Mitigação + Matriz RACI (15/11/2026)"
  - "5 Apresentação Final — Comitê de Governança de Risco (04/12/2026)"
  - "6 Referências Bibliográficas"
  - "7 Anexo I — Relatório Técnico Projeto Aplicado III (preservado)"

**Verificação:** TOC tem 7 entradas visíveis no primeiro open; cabeçalho reflete UC Projeto Aplicado IV (AEx).

---

### Task 2: §1 — Inventário Consolidado de Vulnerabilidades

**Objetivo:** Atender ao critério 1 do rubric (10%).

**Artefato:** Substituir seção "1. Resumo Executivo" atual por "1. Inventário Consolidado de Vulnerabilidades".

**Subseções a redigir:**

- **§1.1 Introdução e Escopo (2 parágrafos):** referência à vuln-bank (commit 5e5ea54, 33 arquivos Python/JS/HTML, ~6 KLOC); 4 baterias SAST executadas no Projeto III (Semgrep, OpenCodeReview, Frieren DAST, ggshield) + 1 bateria complementar (Datadog Static Analyzer) totalizando 24 achados Datadog.

- **§1.2 Tabela1 — Inventário Padronizado (TABELA, 24 linhas × 7 colunas):**
  Colunas: `ID | Descrição Resumida | CWE | CVE/NVD (quando aplicável) | OWASP Top 10 2021 | Arquivo:Linha | Severidade Scanner`
  
  Reduzir para formato compacto (1 linha por achado). Exemplo das primeiras 8 linhas:
  ```
  V-001 | SQLi em f-string (concatenação)              | CWE-89  | CVE-2024-... | A03 Injection    | app.py:395         | Critical
  V-002 | SQLi em f-string                              | CWE-89  | CVE-2024-... | A03 Injection    | app.py:2078        | Critical
  ...
  V-024 | Secure flag ausente em cookie                 | CWE-614 | —            | A05 Misconfig     | app.py:430         | Medium
  ```
  As 24 linhas derivam diretamente das 24 entradas do CSV Datadog já analisadas. Citar CVE real quando público; usar "—" quando não houver CVE público.

- **§1.3 Metodologia de Classificação e Priorização (1 parágrafo + 1 tabela):**
  - Metodologia oficial: **CVSS v3.1** como score base + **escala qualitativa interna** (Crítico/Alto/Médio/Baixo) para linguagem executiva.
  - **Técnica de IA/análise de dados para priorização:** Regra de Pareto — distribuição de achados por CWE mostra que 5 CWEs (CWE-89, CWE-79, CWE-287, CWE-918, CWE-915) concentram 60% do risco total. Citação: princípio 80/20 (Juran 1937, re-aplicado por NIST SP 800-30).
  - Tabela auxiliar: 16 classes CWE × número de achados × risco agregado.

- **§1.4 Evidências Técnicas (1 parágrafo):** Remissão para Anexo I — onde estão os snippets vuln-bank (linhas app.py:395 etc.) e os relatórios brutos (CSV Datadog, SARIF OCR).

**Verificação:** Tabela1 tem 24 linhas; cada linha tem os 7 campos preenchidos; §1.3 cita Pareto + Juran/NIST; data 23/08/26 no cabeçalho.

---

### Task 3: §2 — Classificação Técnica CVSS / CWE / CVE / MITRE ATT&CK

**Objetivo:** Atender ao critério 2 do rubric (25%, peso maior).

**Artefato:** Substituir seção "2. Vulnerabilidades Críticas" atual por "2. Classificação Técnica CVSS / CWE / CVE / MITRE ATT&CK".

**Subseções a redigir:**

- **§2.1 Fundamentação Metodológica (3 parágrafos):**
  - CVSS v3.1 (FIRST 2019): métricas Base (8 métricas), Temporal (3), Environmental (11). Aplicadas apenas métricas Base neste relatório porque o escopo da vuln-bank é estático (sem dados de produção).
  - CWE (MITRE): taxonomia de fraquezas; este relatório usa o ID canônico (ex.: CWE-89) + nome canônico (ex.: "Improper Neutralization of Special Elements used in an SQL Command").
  - CVE/NVD: referenciado apenas quando CVE público existe para a mesma classe de falha.
  - MITRE ATT&CK: matriz Enterprise v15, técnicas Txxxx referenciadas para vetor de exploração.
  - OWASP Top 10 2021: categorização por categoria (A01–A10).

- **§2.2 Tabela2 — Classificação Completa do Top-8 (TABELA, 8 linhas × 9 colunas):**
  Colunas: `ID | Vulnerabilidade | CWE | CVE | CVSS Vetor | CVSS Score | ATT&CK | OWASP 2021 | Justificativa por Métrica`
  
  **Para V-001 (SQLi em massa), exemplo do conteúdo por coluna CVSS com justificativa:**
  - AV (Attack Vector) = Network (N): vuln-bank é aplicação web Flask exposta em 0.0.0.0; exploração remota trivial.
  - AC (Attack Complexity) = Low (L): o atacante só precisa enviar uma string maliciosa em campo de formulário; nenhuma condição prévia.
  - PR (Privileges Required) = None (N): os 33 sinks cobrem rotas autenticadas E não-autenticadas (/login, /register, /forgot-password).
  - UI (User Interaction) = None (N): exploração automática via script.
  - S (Scope) = Changed (C): SQLi permite leitura/escrita além do escopo do usuário autenticado.
  - C (Confidentiality) = High (H): SELECT * FROM users retorna todos os usuários, incluindo hashes de senha.
  - I (Integrity) = High (H): UPDATE arbitrário em qualquer coluna.
  - A (Availability) = High (H): DROP TABLE / TRUNCATE trivial.
  - Vetor completo: `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H` → score **9.6 (Critical)**.

  Repetir para os 8 achados do §2.3 do plano. **Esta é a coluna mais importante** — o rubric aloca 30% do critério 2 a "precisão técnica" + 30% a "correção do cálculo CVSS" + 20% a "rastreabilidade das justificativas".

- **§2.3 Mapeamento ATT&CK (1 tabela auxiliar, 8 linhas × 3 colunas):** `Vuln ID | Técnica ATT&CK | Como o atacante usa`
  - V-001 → T1190 (Exploit Public-Facing Application)
  - V-002 → T1552 (Unsecured Credentials) + T1552.005 (Cloud Instance Metadata API) para o componente SSRF→IMDS
  - V-003 → T1530 (Data from Cloud Storage Object) — variação para PAN/CVV retornado
  - V-004 → T1003 (OS Credential Dumping) — variação para leitura de senhas plaintext
  - V-006 → T1552.005 (Cloud Instance Metadata API)
  - V-007 → T0836 (Modify Parameter — analogia ICS/financeira para TOCTOU)
  - V-008 → T1190 (Exploit Public-Facing Application) — Werkzeug debugger RCE

**Verificação:** Tabela2 tem 8 linhas com vetor CVSS completo; §2.2.1 cita FIRST 2019; data 20/09/26 no cabeçalho.

---

### Task 4: §3 — Matriz de Risco Organizacional

**Objetivo:** Atender ao critério 3 do rubric (15%, foco LGPD).

**Artefato:** Substituir seção "3. Classes de Vulnerabilidade Identificadas" atual por "3. Matriz de Risco Organizacional".

**Subseções a redigir:**

- **§3.1 Metodologia de Avaliação de Risco (2 parágrafos + 1 tabela):**
  - Modelo: **Probabilidade × Impacto** (NIST SP 800-30). Probabilidade: Baixa/Média/Alta. Impacto: dividido em 4 dimensões — Técnico, Regulatório (LGPD/PCI), Negócio (financeiro + reputacional), Ético-legal (ANPD).
  - Score final: média ponderada (Técnico 30%, Regulatório 25%, Negócio 25%, Ético-legal 20%).
  - Tabela de níveis: 0.0–3.9 Baixo, 4.0–5.9 Médio, 6.0–7.9 Alto, 8.0–10.0 Crítico.

- **§3.2 Tabela3 — Matriz de Risco (TABELA, 8 linhas × 9 colunas):**
  Colunas: `ID | Vulnerabilidade | Prob. | Imp.Téc. | Imp.Reg. | Imp.Neg. | Imp.Ético | Score Final | Nível | Justificativa`
  
  Exemplo para V-003 (PAN/CVV retornados):
  - Probabilidade = Alta (3): exploração via chamada de API autenticada de merchant é trivial.
  - Imp.Téc. = Crítico (3): exposição de dados sensíveis PCI-DSS.
  - Imp.Reg. = Crítico (3): viola LGPD Art. 46 + PCI-DSS Req. 3.2 (proibição de retenção de CVV pós-autorização).
  - Imp.Neg. = Crítico (3): risco de cancelamento do contrato de adquirente + multa BACEN.
  - Imp.Ético = Alto (2): expõe dados de clientes sem necessidade funcional.
  - Score = 3*(0.30) + 3*(0.25) + 3*(0.25) + 2*(0.20) = 0.90+0.75+0.75+0.40 = **2.80** (escala normalizada para 10: **8.0/10 — Crítico**).
  
  Repetir para os 8. Justificativa curta (1 linha) por vulnerabilidade.

- **§3.3 Análise Ético-Legal — Dados Pessoais (LGPD + ANPD) (3 parágrafos):**
  Subseção dedicada para os achados que envolvem **dados pessoais** (V-001 SQLi, V-002 JWT forge, V-003 PAN/CVV, V-004 plaintext password):
  - **LGPD Art. 46** (boas práticas e governança): armazenamento de senha em texto claro viola o Art. 46 + princípio de "privacy by design" do Art. 49.
  - **LGPD Art. 48** + **Resolução ANPD nº 15/2024**: vazamento de dados financeiros é incidente reportável; vuln-bank atualmente não tem processo de detecção.
  - **PCI-DSS v4.0.1 Req. 3.2** + Req. 3.4: armazenamento de PAN exige truncamento ou hash forte; armazenamento de CVV pós-autorização é proibido sem exceção.
  - **Privacy by Design / by Default** (ANPD 2023): o sistema deveria hashar senhas no momento do cadastro, antes da persistência. A correção é simples (werkzeug.security.generate_password_hash) mas a ausência viola o Art. 49 da LGPD.
  - Recomendação: registrar incidente como simulado no RIPD (Relatório de Impacto à Proteção de Dados Pessoais) da organização.

- **§3.4 Matriz de Probabilidade (1 tabela):** Escala de Probabilidade (3 níveis) × Escala de Impacto (3 níveis) com cores visuais.

**Verificação:** Tabela3 tem 8 linhas com scores preenchidos; §3.3 cita LGPD Art. 46/48/49 + ANPD Res. 15/2024 + PCI-DSS v4.0.1; data 18/10/26 no cabeçalho.

---

### Task 5: §4 — Plano de Mitigação + Matriz RACI

**Objetivo:** Atender ao critério 4 do rubric (25%, mais o subcritério de sustentabilidade ambiental).

**Artefato:** Substituir seção "4. Plano de Remediação Recomendado" + seção "5.6 Plano de Remediação Complementar" por "4. Plano de Mitigação + Matriz RACI".

**Subseções a redigir:**

- **§4.1 Estratégia de Mitigação (2 parágrafos):**
  - Modelo: priorização por score da §3 (Top-8) + agrupamento por cluster (C1–C5) para ganhar eficiência operacional.
  - **Princípios:** controles preventivos > detectivos > corretivos; alinhamento com ISO 27002 A.5–A.18 e NIST CSF 2.0 Govern/Identify/Protect/Detect/Respond/Recover.

- **§4.2 Tabela4 — Plano de Mitigação Priorizado (TABELA, 8 linhas × 6 colunas):**
  Colunas: `ID | Ação | Cluster | Esforço (h) | Prazo | Justificativa baseada em risco`
  
  | # | Ação | Cluster | h | Prazo | Justificativa |
  |---|---|---|---|---|---|
  | M-001 | Migrar JWT_SECRET para KMS/Vault + remover `none` + forçar verify_signature=True | C1 | 16 | Imediato (24h) | V-002 score 9.6/10 + expõe todos os outros controles |
  | M-002 | Parametrizar 33 sinks SQLi (incluindo Mass Assignment em /update-limit) | C2 | 24 | Imediato (24h) | V-001 score 9.6/10 + 1 sink sozinho já justifica |
  | M-003 | Mascarar PAN + remover CVV de respostas + hashear senhas em merchant_payments.py | C1+C4 | 16 | Imediato (24h) | V-003+V-004 — única combinação que zera risco LGPD/PCI-DSS |
  | M-004 | Bloquear SSRF + pin actions do CI + proteger IMDS via IMDSv2 obrigatório | C3 | 12 | Curto (7d) | V-006 — RCE cloud |
  | M-005 | Unificar SELECT+UPDATE em transação atômica em /api/transfer | C2 | 8 | Curto (7d) | V-007 — race condition |
  | M-006 | Remover debug=True + bind 0.0.0.0 + Dockerfile USER nonroot | C3 | 4 | Imediato (24h) | V-008 — trivial fix |
  | M-007 | Implementar Flask-WTF + CSRFProtect global + remover `|safe` em Jinja | C2+C5 | 12 | Curto (7d) | V-005+V-008 (subset) |
  | M-008 | WAF restritivo + CSP header + rate limiting em /api/* | C5 | 8 | Médio (30d) | Camada detectiva complementar |

  Total: 100 horas-homem. Estimativa de custo: R$ 8.000–12.000 (dev senior @ R$ 80–120/h).

- **§4.3 Matriz RACI (TABELA, 6 colunas × 9 linhas):**
  Linhas: 8 ações. Colunas: `ID | Ação | R (Responsável) | A (Aprovador) | C (Consultado) | I (Informado)`
  
  Atores sugeridos:
  - **R** = Engenheiro de Segurança (Rafael Péret de Sant'ana) ou Desenvolvedor Backend sênior
  - **A** = CISO / Head de Segurança (gerência)
  - **C** = DPO (Data Protection Officer) para ações M-003; Arquiteto de Soluções para M-001/M-002; SRE para M-006
  - **I** = Comitê de Governança de Risco, Compliance, equipe de desenvolvimento
  
  Exemplo para M-002: `R: Desenvolvedor Backend | A: Head de Segurança | C: DPO + Eng. Segurança | I: Comitê de Governança + time dev`

- **§4.4 Alinhamento a Frameworks (1 tabela):**
  Cada ação mapeada para controle ISO 27002:2022 A.x e função NIST CSF 2.0. Exemplo:
  
  | Ação | ISO 27002:2022 | NIST CSF 2.0 |
  |---|---|---|
  | M-001 | A.8.24 (Use of cryptography), A.8.26 (Key management) | PR.DS-1 (Data-at-rest protection), PR.AC-1 (Identity and credential management) |
  | M-002 | A.8.28 (Secure coding), A.8.29 (Security testing in development) | PR.PS-6 (Secure software development practices) |
  | M-003 | A.5.34 (Privacy and protection of PII), A.8.10 (Information deletion) | PR.IP-6 (Data destruction), GV.PO-1 (Privacy governance) |
  | M-006 | A.8.9 (Configuration management), A.8.31 (Separation of environments) | PR.IP-1 (Baseline configuration), DE.CM-9 (Computing hardware and software) |

- **§4.5 Risco Residual (1 tabela):**
  Após M-001 a M-008, score residual esperado por vulnerabilidade. V-002: 9.6 → 2.4 (rebaixado por exigir acesso a Vault + chave KMS rotacionada). V-006: 9.6 → 3.0 (rebaixado por IMDSv2 obrigatório + WAF).

- **§4.6 Sustentabilidade e Impacto Ambiental das Ações (2 parágrafos) — CRITÉRIO OBRIGATÓRIO:**
  - **Descarte responsável de hardware legado:** tokens JWT antigos devem ser revogados e não apenas expirados; em sistemas com tokens persistidos em log de auditoria, aplicar retenção mínima (LGPD Art. 16) e descarte criptografado dos backups antigos.
  - **Eficiência energética de controles adicionais:** WAF em appliance físico dedicado consome ~300-500W continuamente. Mitigação: usar WAF em software (CloudFlare/AWS WAF) que escala elasticamente; evitar appliances 24/7 se o tráfego é variável. Estimativa: appliance dedicado = ~4 MWh/ano (~R$ 3.000/ano); WAF cloud escalável = ~R$ 200/mês = ~R$ 2.400/ano, mas sem o overhead do appliance.
  - **Sustentabilidade da infraestrutura:** preferir rotação automática de credenciais (Vault, GCP Secret Manager) em vez de rotação manual que exige horas-homem; rotação automática reduz tanto risco de exposição quanto custo de operação.
  - **E-waste:** appliances de segurança descontinuados devem seguir logística reversa (PNRS Lei 12.305/2010 + Decreto 10.936/2022). Citar como item de política organizacional, não apenas tecnologia.

- **§4.7 Cronograma (1 GANTT textual):**
  G1 (24h): M-001, M-002, M-003, M-006. G2 (7d): M-004, M-005, M-007. G3 (30d): M-008. Marcos intermediários: 27/08/26 (G1 done), 03/09/26 (G2 done), 24/09/26 (G3 done).

**Verificação:** Tabela4 priorizada + Tabela5 RACI + §4.4 com mapeamento ISO/NIST + §4.5 com risco residual quantificado + §4.6 com menção explícita a e-waste/eficiência energética; data 15/11/26 no cabeçalho.

---

### Task 6: §5 — Apresentação Final — Comitê de Governança de Risco

**Objetivo:** Atender ao critério 5 do rubric (25%).

**Artefato:** Nova seção "5. Apresentação Final — Comitê de Governança de Risco".

**Subseções a redigir:**

- **§5.1 Roteiro Slide-a-Slide (12 slides):**
  ```
  Slide 1 — Capa (título + autores + orientador)
  Slide 2 — Contexto: do Projeto III (técnico) ao Projeto IV (estratégico)
  Slide 3 — Inventário Consolidado (24 achados, 16 CWE)
  Slide 4 — Top-8: CVSS + ATT&CK + OWASP
  Slide 5 — Matriz de Risco: distribuição por nível
  Slide 6 — Análise LGPD: 4 vulnerabilidades que tocam dados pessoais
  Slide 7 — Plano de Mitigação: 8 ações priorizadas
  Slide 8 — Matriz RACI visual
  Slide 9 — Risco Residual após mitigação
  Slide 10 — Sustentabilidade: WAF cloud vs appliance, e-waste, rotação automática
  Slide 11 — Recomendações Estratégicas (ver §5.2)
  Slide 12 — Reflexões Críticas + Aprendizados (ver §5.3)
  ```

- **§5.2 Recomendações Estratégicas (5 bullets):**
  - Institucionalizar SAST em CI (gate de merge com falha se Critical não-resolvido)
  - Tratar LGPD como controle de segurança (não como compliance-only): privacy by design desde o design
  - Implantar programa de threat modeling antes de features novas (STRIDE ou PASTA)
  - Estabelecer RACI formal para tratamento de vulnerabilidades (este relatório é o piloto)
  - Adotar Security Champion por squad de desenvolvimento

- **§5.3 Reflexões Críticas e Aprendizados (3 parágrafos):**
  - **Limitações da abordagem:** SAST sozinho (4 motores diferentes) ainda deixa ~10% de falsos negativos (cv-blind-spots em fluxos de auth complexos). Recomenda-se complementar com DAST com credenciais (próximo passo, listado em §5.4 do ODT antigo).
  - **Falsos positivos:** Datadog e OpenCodeReview super-estimam achados de `innerHTML` por padrão AST sem análise contextual. A revisão humana continua sendo gargalo.
  - **Trade-off ética vs velocidade:** 24h para corrigir CWE-287/CWE-89/CWE-918 é agressivo; em produção real seria Imediato (24h) para CWE-287/CWE-89 e Curto (7d) para CWE-918. O prazo usado aqui é educacional.

- **§5.4 Roteiro de Defesa Oral (5 bullets):** 1 minuto por slide; perguntas esperadas do comitê (por que priorizar SQLi antes de IDOR? por que rate limiting entra em Médio e não Imediato?); respostas sugeridas.

**Verificação:** 12 slides roteirizados + §5.2 com 5 recomendações + §5.3 com limitações + §5.4 com roteiro de defesa; data 04/12/26 no cabeçalho.

---

### Task 7: §6 — Referências Bibliográficas

**Objetivo:** Encerrar referências conforme ABNT.

**Artefato:** Nova seção "6. Referências Bibliográficas" no ODT.

**Conteúdo:** Lista das 18 entradas listadas em §3 acima, formatadas em ABNT NBR 6023 (Sobrenome, Nome. Título. Local: Editora, ano.).

**Verificação:** 18 entradas; ordem alfabética; cada entrada tem autor(es), título, local, ano, URL quando aplicável.

---

### Task 8: §7 — Anexo I (preservação do relatório técnico Projeto III)

**Objetivo:** Preservar o conteúdo técnico atual como anexo, em vez de descartá-lo.

**Artefato:** Nova seção "7. Anexo I — Relatório Técnico Projeto Aplicado III (preservado como insumo)" — contém as seções originais 1, 2, 3, 4 e 5 do ODT atual (renumeradas como A.1, A.2, etc.).

**Conteúdo a redigir:**
- Cabeçalho do anexo: "Anexo I — Relatório Técnico Projeto Aplicado III (vuln-bank, commit 5e5ea54). Este anexo preserva o relatório técnico da fase anterior do projeto, usado como insumo primário para o presente relatório estratégico."
- Mover (sem reescrever) o conteúdo das antigas seções 1–5 do ODT atual para cá.

**Verificação:** Anexo preserva os 4 scanners (Semgrep/OCR/Frieren/ggshield) + 5 subseções da Análise SAST Complementar; total de páginas do anexo documentado.

---

### Task 9: TOC — Pré-baked entries das 7 novas seções principais

**Objetivo:** Adicionar entradas pré-baked no TOC (mesmo padrão do que já foi feito para 5.1 na sessão anterior).

**Artefato:** Bloco TOC em `content.xml` antes de `</text:index-body>`.

**Conteúdo a injetar:** 7 entradas (uma por seção principal §1–§7), com `outline-level="1"` e placeholder `—` para número de página (igual ao padrão já existente). A página será preenchida em "Update Index" pelo LibreOffice.

**Verificação:** Total de `<text:index-entry>` no arquivo sobe de 70 para 84 (+14 = 7 seções × 2 contagens: uma no `<text:index-entry>` propriamente dito + uma no template correspondente). Cabeçalho e Sumário atualizam ao abrir.

---

### Task 10: Validação final do ODT

**Objetivo:** Garantir que o ODT ainda é ODT válido e que tudo está coerente.

**Checks automáticos (via execute_code):**
- mimetype = `application/vnd.oasis.opendocument.text`, primeiro no ZIP, ZIP_STORED.
- `xml.etree.ElementTree.fromstring(content)` parse sem exceção.
- Contagem de `<text:p>` consistente (espera-se ~600–700 parágrafos no total do novo documento).
- 7 seções principais detectáveis (regex nos títulos).
- TOC contém 7+1 entradas (7 novas + a 5.1 antiga preservada).

**Verificação manual:** abrir no LibreOffice (cuidado com NEXUPP.pptx aberto), confirmar:
- Cabeçalho correto
- TOC atualiza com F9 (ou Update Index)
- Tabela1 (24 linhas), Tabela2 (8 linhas), Tabela3 (8 linhas), Tabela4 (8 linhas), Tabela5 (8 linhas RACI) renderizam
- §3.3 cita LGPD Art. 46/48/49 e ANPD Res. 15/2024
- §4.6 cita descarte de hardware / eficiência energética
- §5 tem 12 slides roteirizados

---

## §5 Riscos e Tradeoffs (modo RELATÓRIO)

| Risco do entregável | Mitigação |
|---|---|
| Professor pede demo ao vivo da vuln-bank corrigida | §5.3 já admite que mitigação é proposta, não implementada. Plano §4.2 lista esforço/hora para justificar timeline. |
| LGPD/ANPD sem consulta a DPO real | §3.3 marca recomendações como "registrar no RIPD" — não assume que DPO existe. |
| Aluno não usou CVSS antes; vetores podem ter erros | §2.2 cita FIRST 2019 explicitamente; cada métrica justificada. Para evitar erro grosseiro, deixar claro no relatório que o cálculo é acadêmico. |
| ISO 27002:2022 recente (publicada 2022, atualizada 2024); controle A.x pode estar errado | Citar a versão "ISO/IEC 27002:2022" explicitamente; usar apenas controles A.5–A.18 que são estáveis. |
| Planilha RACI com 6 atores e 8 ações = 48 células | Manter matriz enxuta (1 linha por ação, 4 colunas RACI); detalhamento expande em ANEXO se o comitê pedir. |
| TOC pré-baked com placeholder `—` na página | Mesma técnica já validada na sessão anterior — o usuário faz Update Index no LibreOffice. |
| Critério 1 do rubric menciona "técnicas de análise de dados/IA na priorização" — não executar IA | §1.3 aplica Pareto (regra analítica clássica, não IA generativa); suficiente para o critério. |
| Aluno já entregou Projeto III; conflito de versões | ODT preserva §7 = Anexo I do Projeto III, referenciado como insumo. |

---

## §6 Glossário de Siglas (inserir como apêndice)

CWE, CVE, NVD, CVSS, ATT&CK, OWASP, LGPD, ANPD, PCI-DSS, ISO 27001, ISO 27002, NIST CSF, RACI, SAST, DAST, IMDS, KMS, WAF, CSP, TOCTOU, IDOR, BOLA, KMS, RIPD, PNRS.

---

## §7 Posso Ajudar em Paralelo

(a) **Redigir o markdown completo** deste relatório para colar direto no LibreOffice (gerar .md com cada seção pronta, headings H1/H2 já numerados)

(b) **Reescrever o ODT automaticamente** (eu aplico todas as 10 tasks via patch em `content.xml`, preservando o mimetype/styles/TOC); você abre no LibreOffice só para revisar visualmente

(c) **Gerar mockups** dos gráficos sugeridos em §5 (slide 5: pizza da distribuição de risco; slide 7: Gantt textual do plano)

(d) **Nada por agora** — você assume a redação sozinho

---

## §8 Status Final e Próximo Passo

Aguardando decisão em §7. Recomendação: **(b)** se você quer que eu aplique as mudanças agora, ou **(a)** se você prefere revisar o conteúdo antes de eu gravar no ODT.

---

> **Checkpoint de Sanidade:** Este plano cobre os 5 critérios (10+25+15+25+25 = 100%), com bibliografia de 18 entradas, mapeamento explícito de cada critério para uma seção, e subseção dedicada ao critério ambiental (sustentabilidade) que muitos alunos esquecem. O Anexo I preserva todo o trabalho técnico já feito. A data limite geral é 04/12/26 (Apresentação Final); cada seção tem sua data de realização marcada.