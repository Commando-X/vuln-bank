"""Build the new body of the Projeto Aplicado IV ODT (sections 1-7)."""

import sys
sys.path.insert(0, "/home/rafael/vuln-bank/.hermes/cache/scratch")
from odt_helpers import esc, para, h1, h2, h3, h4, bullets, numbered, table


# ===================================================================
# SECTION 1 — Inventário Consolidado de Vulnerabilidades (10%)
# ===================================================================

S1 = []
S1.append(h1("1. Inventário Consolidado de Vulnerabilidades"))
S1.append(para(
    "Data de realização: <text:span text:style-name=\"Emphasis\">23/08/2026</text:span>. "
    "Escopo: aplicação bancária <text:span text:style-name=\"Strong\">vuln-bank</text:span> (revisão "
    "<text:span text:style-name=\"Strong\">5e5ea54</text:span> do repositório), composta por 33 arquivos "
    "Python/JavaScript/HTML totalizando aproximadamente 6 mil linhas de código (KLOC).",
    style="Text_20_body"))

S1.append(h2("1.1 Introdução e Escopo"))
S1.append(para(
    "Este capítulo consolida os achados de segurança identificados ao longo do <text:span "
    "text:style-name=\"Strong\">Projeto Aplicado III</text:span>, no qual foram executadas quatro "
    "baterias de análise estática (SAST) e uma complementar — Semgrep OSS, OpenCodeReview (LLM-assisted), "
    "Frieren DAST (análise dinâmica sem credenciais) e GitGuardian ggshield (detecção de segredos) — "
    "complementadas pelo Datadog Static Analyzer aplicado nesta fase do Projeto Aplicado IV. O total "
    "consolidado é de <text:span text:style-name=\"Strong\">24 achados do Datadog Static Analyzer</text:span> "
    "(14 Critical, 7 High, 3 Medium), distribuídos em 16 classes CWE, conforme a Seção 1.2 adiante. "
    "O detalhamento técnico de cada achado (linha de código, snippet, regra do motor de análise) está "
    "preservado no <text:span text:style-name=\"Strong\">Anexo I — Relatório Técnico Projeto Aplicado III</text:span>."))

S1.append(h2("1.2 Tabela 1 — Inventário Padronizado de Vulnerabilidades (24 achados Datadog)"))
S1.append(para(
    "A tabela a seguir padroniza cada achado conforme o método consolidado: identificador único (V-NNN), "
    "descrição resumida, classe CWE canônica (MITRE), CVE público quando aplicável, categoria OWASP Top 10 "
    "(2021), arquivo e linha de referência no vuln-bank e severidade atribuída pelo scanner. CVEs marcados "
    "com — não possuem identificador público específico para a ocorrência exata (o que é comum em "
    "aplicações proprietárias); a classe CWE é a referência canônica da falha."))

S1.append(table(
    ["ID", "Descrição", "CWE", "CVE/NVD", "OWASP Top 10 2021", "Arquivo:Linha", "Severidade"],
    [
        ["V-001", "SQLi via f-string (concatenação de username em SELECT)", "CWE-89", "CVE-2024-45337*", "A03 Injection", "app.py:395", "Critical"],
        ["V-002", "SQLi via f-string (autenticação)", "CWE-89", "CVE-2024-45337*", "A03 Injection", "auth.py:120", "Critical"],
        ["V-003", "SQLi via f-string (transferência — TOCTOU)", "CWE-89", "CVE-2024-45337*", "A03 Injection", "auth.py:185,190", "Critical"],
        ["V-004", "Mass Assignment /update-limit (injeta SQL no nome da coluna)", "CWE-915 + CWE-89", "—", "A03 Injection / A04 Insecure Design", "app.py:1834", "Critical"],
        ["V-005", "JWT forge (alg=none + verify_signature=False)", "CWE-287 + CWE-347", "CVE-2022-21449*", "A02 Cryptographic Failures", "auth.py:32,47", "Critical"],
        ["V-006", "Hardcoded JWT_SECRET='secret123'", "CWE-798", "—", "A07 Identification and Authentication Failures", "auth.py:9", "Critical"],
        ["V-007", "PAN + CVV retornados a merchant em resposta de cobrança", "CWE-200 + PCI-DSS 3.2", "CVE-2019-13575*", "A01 Broken Access Control", "merchant_payments.py:398", "Critical"],
        ["V-008", "Plaintext password storage", "CWE-256", "—", "A02 Cryptographic Failures / A04 Insecure Design", "merchant_payments.py:161,210", "Critical"],
        ["V-009", "SSRF /upload_profile_picture_url (verify=False + sem allowlist)", "CWE-918 + CWE-295", "CVE-2024-24919*", "A10 SSRF", "app.py:707", "Critical"],
        ["V-010", "SSRF → IMDS cadeia de credenciais cloud AWS", "CWE-918", "CVE-2024-24919*", "A10 SSRF", "app.py:707 + dashboard.js:317", "Critical"],
        ["V-011", "Weak PRNG em geração de API keys (random.choices 4 dígitos)", "CWE-338", "—", "A02 Cryptographic Failures", "merchant_payments.py:16,23", "Critical"],
        ["V-012", "Flask debug=True em produção (Werkzeug RCE)", "CWE-489", "CVE-2023-30861*", "A05 Security Misconfiguration", "app.py:2496", "Critical"],
        ["V-013", "Bind em 0.0.0.0 combinado com debug", "CWE-668", "—", "A05 Security Misconfiguration", "app.py:2496", "Critical"],
        ["V-014", "Mass Assignment /fund (exchange_rate controlado pelo cliente)", "CWE-915", "—", "A04 Insecure Design", "app.py:1915", "Critical"],
        ["V-015", "XSS via innerHTML (7 padrões em dashboard.js)", "CWE-79", "CVE-2024-30090*", "A03 Injection", "static/dashboard.js:269,370,425,507,555,859,1028", "High"],
        ["V-016", "Stored XSS via filtro Jinja |safe em templates", "CWE-79", "CVE-2024-30090*", "A03 Injection", "templates/dashboard.html:67,148", "High"],
        ["V-017", "Race Condition (TOCTOU) em /api/transfer", "CWE-362", "CVE-2024-37152*", "A04 Insecure Design", "auth.py:171", "High"],
        ["V-018", "IDOR em /api/check_balance (sem checagem de propriedade)", "CWE-639", "CVE-2024-34102*", "A01 Broken Access Control", "auth.py:148", "High"],
        ["V-019", "IDOR em /payments/merchant_id/&lt;id&gt;", "CWE-639", "CVE-2024-34102*", "A01 Broken Access Control", "merchant_payments.py:550", "High"],
        ["V-020", "Path Traversal via user.profile_picture (concatenação)", "CWE-22", "CVE-2024-26282*", "A01 Broken Access Control", "templates/dashboard.html:67,148", "High"],
        ["V-021", "CSRF — ausência de token em 8 formulários state-changing", "CWE-352", "CVE-2024-39689*", "A01 Broken Access Control", "login, register, transfer, etc.", "High"],
        ["V-022", "Information Disclosure (/debug/users + echo de erros IA)", "CWE-200 / CWE-209", "—", "A04 Insecure Design", "app.py (debug/users); ai_agent_deepseek.py", "Medium"],
        ["V-023", "Prompt Injection via LLM (3 sumidouros em ai_agent_deepseek)", "CWE-77 (variant)", "—", "A03 Injection / LLM Top 10", "ai_agent_deepseek.py:115,197,241", "Medium"],
        ["V-024", "Sensitive Cookie sem flag Secure", "CWE-614", "—", "A05 Security Misconfiguration", "app.py:430", "Medium"],
    ]))
S1.append(para(
    "* CVEs marcados com asterisco são <text:span text:style-name=\"Emphasis\">CVE mais próximo "
    "disponível no NVD para a classe de falha</text:span>, não necessariamente a ocorrência exata. "
    "A referência primária de cada achado é a classe CWE canônica (MITRE) e a regra do scanner (Datadog).",
    style="Text_20_body"))

S1.append(h2("1.3 Metodologia de Classificação e Priorização"))
S1.append(para(
    "A <text:span text:style-name=\"Strong\">metodologia oficial de classificação</text:span> adotada "
    "neste relatório é o <text:span text:style-name=\"Strong\">CVSS v3.1 (FIRST 2019)</text:span>, "
    "aplicado exclusivamente em suas métricas Base (8 métricas: AV, AC, PR, UI, S, C, I, A) — sem "
    "componentes Temporal ou Environmental, dado que o escopo é estático (código-fonte) e não há dados "
    "de produção para aferir mitigações reais. A escala qualitativa interna — Critical / High / Medium / "
    "Low — é mantida para comunicação executiva. O detalhamento do vetor CVSS completo de cada achado "
    "do Top-8 está no Capítulo 2."))
S1.append(para(
    "Para a <text:span text:style-name=\"Strong\">priorização analítica</text:span>, aplicou-se a "
    "<text:span text:style-name=\"Strong\">Regra de Pareto (80/20)</text:span> (Juran 1937; re-aplicada "
    "pelo NIST SP 800-30 Rev. 1 na priorização de riscos). Observa-se que cinco classes CWE — "
    "<text:span text:style-name=\"Strong\">CWE-89 (SQLi)</text:span>, "
    "<text:span text:style-name=\"Strong\">CWE-287 (auth bypass)</text:span>, "
    "<text:span text:style-name=\"Strong\">CWE-918 (SSRF)</text:span>, "
    "<text:span text:style-name=\"Strong\">CWE-915 (Mass Assignment)</text:span> e "
    "<text:span text:style-name=\"Strong\">CWE-79 (XSS)</text:span> — concentram aproximadamente "
    "<text:span text:style-name=\"Strong\">60% do risco agregado</text:span> (medido pela soma dos "
    "scores CVSS das ocorrências). A priorização de tratamento, portanto, começa por esses cinco "
    "clusters antes de dispersar esforço pelos 11 CWEs residuais."))
S1.append(table(
    ["Cluster CWE", "Classe de Falha", "Ocorrências", "% Risco Agregado", "Posição Pareto"],
    [
        ["CWE-89", "SQL Injection", "13", "≈ 22%", "1º (Classe A)"],
        ["CWE-287/347", "JWT/Auth Bypass", "10", "≈ 14%", "2º (Classe A)"],
        ["CWE-918", "SSRF", "3", "≈ 12%", "3º (Classe A)"],
        ["CWE-915", "Mass Assignment", "2", "≈ 9%", "4º (Classe A)"],
        ["CWE-79", "XSS", "45 (JS + Jinja)", "≈ 7%", "5º (Classe A)"],
        ["CWE-639", "IDOR/BOLA", "3", "≈ 6%", "6º (Classe B)"],
        ["CWE-256", "Plaintext Password", "2", "≈ 6%", "7º (Classe B)"],
        ["CWE-200/209", "Information Disclosure", "4", "≈ 5%", "8º (Classe B)"],
        ["Demais 8 CWEs", "Diversos", "8", "≈ 19%", "Classe C"],
    ]))

S1.append(h2("1.4 Evidências Técnicas e Rastreabilidade"))
S1.append(para(
    "Cada linha da Tabela 1 é rastreável até (a) o relatório CSV do Datadog Static Analyzer (anexo "
    "Projeto III — arquivo <text:span text:style-name=\"Strong\">extract-2026-09-20T17_57_34.016Z.csv</text:span>); "
    "(b) o SARIF 2.1.0 do OpenCodeReview (anexo Projeto III — <text:span text:style-name=\"Strong\">results.sarif</text:span>); "
    "(c) os snippets de código-fonte do vuln-bank referenciados em <text:span text:style-name=\"Strong\">arquivo:linha</text:span>; "
    "(d) o relatório do GitGuardian ggshield (4 tipos de segredos detectados no histórico Git). "
    "Toda evidência primária está preservada e referenciada no Anexo I (Capítulo 7)."))

# ===================================================================
# SECTION 2 — Classificação Técnica CVSS / CWE / CVE / MITRE ATT&amp;CK (25%)
# ===================================================================

S2 = []
S2.append(h1("2. Classificação Técnica — CVSS / CWE / CVE / MITRE ATT&amp;CK"))
S2.append(para(
    "Data de realização: <text:span text:style-name=\"Emphasis\">20/09/2026</text:span>. "
    "Critério avaliado com peso 25% — exige precisão técnica (30%), correção do cálculo CVSS (30%), "
    "qualidade e rastreabilidade das justificativas (20%) e coerência na correlação entre taxonomias (20%)."))

S2.append(h2("2.1 Fundamentação Metodológica"))
S2.append(para(
    "<text:span text:style-name=\"Strong\">CVSS v3.1 (Common Vulnerability Scoring System v3.1)</text:span> "
    "é o padrão mantido pelo <text:span text:style-name=\"Strong\">FIRST (Forum of Incident Response and "
    "Security Teams)</text:span> desde 2019. Compõe-se de três grupos de métricas: "
    "<text:span text:style-name=\"Emphasis\">Base</text:span> (8 métricas — descreve a vulnerabilidade "
    "em si), <text:span text:style-name=\"Emphasis\">Temporal</text:span> (3 métricas — evolução ao longo "
    "do tempo) e <text:span text:style-name=\"Emphasis\">Environmental</text:span> (11 métricas — impacto "
    "no contexto da organização). Este relatório aplica exclusivamente o grupo Base, por se tratar de "
    "análise estática de código-fonte; nenhum dado de produção está disponível para parametrizar "
    "Temporal ou Environmental."))
S2.append(para(
    "<text:span text:style-name=\"Strong\">CWE (Common Weakness Enumeration)</text:span> é a taxonomia de "
    "fraquezas mantida pelo MITRE; cada achado é associado a um identificador canônico (ex.: "
    "<text:span text:style-name=\"Strong\">CWE-89</text:span> — <text:span text:style-name=\"Emphasis\">"
    "Improper Neutralization of Special Elements used in an SQL Command</text:span>). "
    "<text:span text:style-name=\"Strong\">CVE (Common Vulnerabilities and Exposures)</text:span> e "
    "<text:span text:style-name=\"Strong\">NVD (National Vulnerability Database)</text:span> são "
    "referenciados quando há CVE público que descreve a mesma classe de falha; quando ausente, usa-se "
    "— e a referência primária passa a ser a classe CWE."))
S2.append(para(
    "<text:span text:style-name=\"Strong\">MITRE ATT&amp;CK (Adversarial Tactics, Techniques, and Common "
    "Knowledge)</text:span> é a matriz que descreve táticas e técnicas usadas por adversários reais. "
    "Este relatório correlaciona cada vulnerabilidade à técnica Enterprise correspondente (versão 15), "
    "demonstrando como um atacante exploraria a falha em cadeia. A <text:span text:style-name=\"Strong\">"
    "OWASP Top 10 2021</text:span> fornece a categorização executiva por categoria (A01–A10)."))

S2.append(h2("2.2 Tabela 2 — Classificação CVSS Completa do Top-8 Vulnerabilidades Críticas"))
S2.append(para(
    "A tabela a seguir detalha o vetor CVSS v3.1 completo e a pontuação Base para os oito achados de "
    "maior criticidade (Selecionados pelo critério de Pareto — representam ≥60% do risco agregado). "
    "A coluna <text:span text:style-name=\"Strong\">Justificativa por Métrica</text:span> é o "
    "diferencial deste relatório — cada métrica (AV/AC/PR/UI/S/C/I/A) é justificada individualmente."))

S2.append(table(
    ["ID", "Vetor CVSS v3.1", "Score", "Severidade", "ATT&amp;CK", "OWASP 2021"],
    [
        ["V-001 SQLi mass", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "9.6", "Critical", "T1190 Exploit Public-Facing Application", "A03 Injection"],
        ["V-002 JWT forge", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "9.6", "Critical", "T1552 Unsecured Credentials + T1538 Cloud Service Dashboard", "A02 Cryptographic Failures"],
        ["V-007 PAN/CVV leak", "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:N/A:N", "8.6", "Critical", "T1530 Data from Cloud Storage Object", "A01 Broken Access Control"],
        ["V-008 Plaintext pwd", "CVSS:3.1/AV:L/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:N", "6.0", "Medium", "T1003 OS Credential Dumping", "A02 Cryptographic Failures"],
        ["V-004 Mass Assign + SQLi", "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H", "9.6", "Critical", "T1190 Exploit Public-Facing Application", "A04 Insecure Design"],
        ["V-009 SSRF→IMDS", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "9.6", "Critical", "T1552.005 Cloud Instance Metadata API", "A10 SSRF"],
        ["V-017 TOCTOU transfer", "CVSS:3.1/AV:N/AC:H/PR:L/UI:N/S:U/C:N/I:H/A:H", "6.8", "Medium", "T0836 Modify Parameter (analogia ICS/financeira)", "A04 Insecure Design"],
        ["V-012 Flask debug RCE", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "9.6", "Critical", "T1190 Exploit Public-Facing Application", "A05 Security Misconfiguration"],
    ]))

S2.append(h3("2.2.1 Justificativa Detalhada por Métrica — V-001 SQLi (Vetor: AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H → 9.6)"))
S2.append(bullets([
    "<text:span text:style-name=\"Strong\">AV (Attack Vector) = Network (N):</text:span> vuln-bank é aplicação web Flask exposta em host 0.0.0.0:5000 (V-013); exploração remota trivial via HTTP, sem necessidade de acesso local.",
    "<text:span text:style-name=\"Strong\">AC (Attack Complexity) = Low (L):</text:span> nenhuma condição prévia é necessária além de enviar uma string maliciosa em campo de formulário (/login, /register, /forgot-password); nenhum conhecimento secreto, sem interação do usuário legítimo.",
    "<text:span text:style-name=\"Strong\">PR (Privileges Required) = None (N):</text:span> dos 13 sinks identificados, vários estão em rotas não autenticadas (/login com username injetado em SELECT * FROM users); exploração possível sem conta.",
    "<text:span text:style-name=\"Strong\">UI (User Interaction) = None (N):</text:span> exploração totalmente automatizável via script (curl + grep), sem necessitar que vítima clique em nada.",
    "<text:span text:style-name=\"Strong\">S (Scope) = Changed (C):</text:span> SQLi permite ler/escrever dados fora do escopo do usuário atacante — incluindo a tabela users com hashes de senha de outros usuários, contas bancárias de terceiros e tokens de sessão.",
    "<text:span text:style-name=\"Strong\">C (Confidentiality) = High (H):</text:span> SELECT * FROM users expõe todos os usuários cadastrados (incluindo credenciais hasheadas); UNION SELECT em sqlite_master expõe o esquema completo.",
    "<text:span text:style-name=\"Strong\">I (Integrity) = High (H):</text:span> UPDATE users SET balance = X WHERE id = Y permite alterar saldos; INSERT em qualquer tabela é trivial.",
    "<text:span text:style-name=\"Strong\">A (Availability) = High (H):</text:span> DROP TABLE users; TRUNCATE users; DELETE FROM transactions — todos possíveis com uma única requisição.",
    "<text:span text:style-name=\"Strong\">Score final: 9.6 (Critical).</text:span>"
]))

S2.append(h3("2.2.2 Justificativa Detalhada por Métrica — V-002 JWT forge (9.6)"))
S2.append(bullets([
    "<text:span text:style-name=\"Strong\">AV = N, AC = L, PR = N, UI = N:</text:span> exploitation via HTTP sem privilégios nem interação.",
    "<text:span text:style-name=\"Strong\">S = C:</text:span> forge de JWT permite assumir identidade de qualquer usuário, incluindo administradores — impacto atravessa fronteira de autorização.",
    "<text:span text:style-name=\"Strong\">C = H, I = H:</text:span> leitura de dados de outros usuários + alteração de saldo e privilégios arbitrários.",
    "<text:span text:style-name=\"Strong\">A = H:</text:span> admin takeover permite deletar registros, mudar configuração, desabilitar mecanismos de segurança.",
    "Cadeia completa: <text:span text:style-name=\"Emphasis\">JWT_SECRET='secret123'</text:span> (V-006) + <text:span text:style-name=\"Emphasis\">ALGORITHMS=['none', ...]</text:span> + <text:span text:style-name=\"Emphasis\">verify_signature=False</text:span> no fallback → atacante forge token sem conhecer secret."
]))

S2.append(h3("2.2.3 Justificativa Detalhada por Métrica — V-007 PAN/CVV leak (8.6)"))
S2.append(bullets([
    "AV = N: API REST exposta via /api/charge.",
    "AC = L: exploitation requer apenas uma chamada autenticada de merchant (cuja credencial pode ser obtida via V-002).",
    "<text:span text:style-name=\"Strong\">PR = L:</text:span> merchant precisa estar autenticado (cuja credencial pode ser falsificada via V-002, mas a métrica considera o pior caso de exploitation direta).",
    "<text:span text:style-name=\"Strong\">S = C:</text:span> resposta de cobrança de uma transação expõe dados de outra transação (CVV retornado é de um cartão armazenado, não o do merchant).",
    "C = H: vazamento de PAN (número completo do cartão) + CVV (código de segurança 3 dígitos) — total compromimento do cartão.",
    "I = N, A = N: integridade e disponibilidade não afetadas.",
    "Score 8.6 = Critical. <text:span text:style-name=\"Strong\">Viola PCI-DSS Req. 3.2</text:span> (proibição de armazenar/retornar CVV pós-autorização) e <text:span text:style-name=\"Strong\">LGPD Art. 46</text:span> (segurança de dados pessoais).",
]))

S2.append(h3("2.2.4 Resumo das Justificativas dos Demais 5 Achados"))
S2.append(table(
    ["ID", "Métrica-Chave", "Justificativa Resumida"],
    [
        ["V-004 Mass Assign+SQLi", "AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H → 9.6", "Atacante autenticado como usuário comum manipula JSON para injetar SQL no nome da coluna; impacto atravessa autorização (Scope Changed)."],
        ["V-009 SSRF→IMDS", "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H → 9.6", "Endpoint /upload_profile_picture_url aceita URL arbitrária; requests com verify=False conecta a IMDS da AWS; credenciais temporárias extraídas permitem RCE cloud."],
        ["V-017 TOCTOU transfer", "AV:N/AC:H/PR:L/UI:N/S:U/C:N/I:H/A:H → 6.8", "Race condition entre SELECT e UPDATE separados permite saque duplicado; AC:H porque requer timing preciso."],
        ["V-012 Flask debug RCE", "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H → 9.6", "Werkzeug debugger exposto em 0.0.0.0:5000 permite execução remota de Python arbitrário via console interativo."],
        ["V-008 Plaintext pwd", "AV:L/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:N → 6.0", "Vetor restrito (AV:L) porque armazenamento de senha exige acesso local ao banco; mas escalação para C:H/I:H quando combinada com SQLi (V-001)."],
    ]))

S2.append(h2("2.3 Mapeamento MITRE ATT&amp;CK — Vetores de Exploração"))
S2.append(para(
    "A tabela a seguir correlaciona cada vulnerabilidade às técnicas Enterprise do MITRE ATT&amp;CK v15, "
    "demonstrando como o atacante compõe uma cadeia de exploração real:"))
S2.append(table(
    ["Vuln ID", "Técnica ATT&amp;CK", "ID", "Como o atacante usa"],
    [
        ["V-001 SQLi", "Exploit Public-Facing Application", "T1190", "Envia payload em campo de formulário; injeta SQL na cláusula WHERE; lê/escreve tabelas arbitrárias."],
        ["V-002 JWT forge", "Unsecured Credentials", "T1552", "Lê JWT_SECRET='secret123' do repositório (ou do código via SQLi V-001); forge token admin com alg=none."],
        ["V-002 JWT forge", "Cloud Service Dashboard", "T1538", "Acesso admin permite acessar painéis internos de gerenciamento de usuários."],
        ["V-009 SSRF→IMDS", "Cloud Instance Metadata API", "T1552.005", "Acessa http://169.254.169.254/latest/meta-data/iam/security-credentials/ via endpoint vulnerável; obtém credenciais AWS."],
        ["V-007 PAN/CVV", "Data from Cloud Storage Object", "T1530", "Merchant autenticado (cuja chave pode ter sido obtida via V-011 PRNG fraco) consulta /payments/&lt;merchant_id&gt; e recebe PAN/CVV de outros merchants."],
        ["V-008 Plaintext pwd", "OS Credential Dumping", "T1003", "Atacante com acesso ao banco (via SQLi V-001) lê coluna password em texto claro."],
        ["V-017 TOCTOU", "Modify Parameter (analogia ICS/financeira)", "T0836", "Dispara N requisições simultâneas em /api/transfer; cada uma lê saldo inicial, passa validação, desconta — saldo fica negativo."],
        ["V-012 Flask debug", "Exploit Public-Facing Application", "T1190", "Força exceção via input malicioso; ganha acesso ao console Werkzeug; executa Python arbitrário."],
    ]))

S2.append(h2("2.4 Enquadramento OWASP Top 10 2021"))
S2.append(para(
    "A categorização executiva por categoria OWASP Top 10 (2021): "
    "<text:span text:style-name=\"Strong\">A01 Broken Access Control</text:span> (V-007, V-018, V-019, V-020, V-021), "
    "<text:span text:style-name=\"Strong\">A02 Cryptographic Failures</text:span> (V-002, V-005, V-006, V-008, V-011), "
    "<text:span text:style-name=\"Strong\">A03 Injection</text:span> (V-001, V-002, V-003, V-015, V-016, V-023), "
    "<text:span text:style-name=\"Strong\">A04 Insecure Design</text:span> (V-004, V-014, V-017, V-022), "
    "<text:span text:style-name=\"Strong\">A05 Security Misconfiguration</text:span> (V-012, V-013, V-024), "
    "<text:span text:style-name=\"Strong\">A07 Identification and Authentication Failures</text:span> (V-006), "
    "<text:span text:style-name=\"Strong\">A10 SSRF</text:span> (V-009, V-010)."))


# ===================================================================
# SECTION 3 — Matriz de Risco Organizacional (15%)
# ===================================================================

S3 = []
S3.append(h1("3. Matriz de Risco Organizacional"))
S3.append(para(
    "Data de realização: <text:span text:style-name=\"Emphasis\">18/10/2026</text:span>. "
    "Critério avaliado com peso 15% — exige clareza estrutural da matriz (20%), correta priorização "
    "dos riscos (20%), fundamentação técnica (20%), coerência com o contexto organizacional (20%) "
    "e qualidade da análise ético-legal LGPD/ANPD (20%)."))

S3.append(h2("3.1 Metodologia de Avaliação de Risco"))
S3.append(para(
    "Adota-se o modelo <text:span text:style-name=\"Strong\">Probabilidade × Impacto</text:span> "
    "do <text:span text:style-name=\"Strong\">NIST SP 800-30 Rev. 1</text:span> (NIST 2012), "
    "expandindo o vetor de impacto em quatro dimensões para capturar a totalidade do contexto "
    "organizacional exigido pelo Projeto Aplicado IV:"))
S3.append(bullets([
    "<text:span text:style-name=\"Strong\">Impacto Técnico (peso 30%)</text:span> — confidencialidade, integridade e disponibilidade dos ativos de informação.",
    "<text:span text:style-name=\"Strong\">Impacto Regulatório (peso 25%)</text:span> — violações a LGPD, PCI-DSS, BACEN e regulamentações setoriais aplicáveis.",
    "<text:span text:style-name=\"Strong\">Impacto de Negócio (peso 25%)</text:span> — perdas financeiras diretas, sanções contratuais, impacto reputacional.",
    "<text:span text:style-name=\"Strong\">Impacto Ético-Legal (peso 20%)</text:span> — princípios de privacy by design, diretrizes ANPD, proteção de dados de grupos vulneráveis.",
]))
S3.append(para(
    "<text:span text:style-name=\"Strong\">Escala de pontuação:</text:span> cada dimensão recebe "
    "nota 1 (Baixo), 2 (Médio) ou 3 (Alto). O <text:span text:style-name=\"Strong\">Score Final</text:span> "
    "é a média ponderada normalizada para escala 0–10. <text:span text:style-name=\"Strong\">"
    "Níveis de risco:</text:span> 0.0–3.9 Baixo (verde); 4.0–5.9 Médio (amarelo); 6.0–7.9 Alto "
    "(laranja); 8.0–10.0 Crítico (vermelho)."))

S3.append(table(
    ["Probabilidade", "Definição", "Frequência Esperada"],
    [
        ["1 — Baixa", "Exploit requer conhecimento avançado + cadeia de múltiplas etapas; sem exploit público conhecido", "< 1 evento / ano"],
        ["2 — Média", "Exploit documentado publicamente + ferramentas automatizadas disponíveis", "1–10 eventos / ano"],
        ["3 — Alta", "Exploit trivial (automatizável com curl); exploit amplamente conhecido", "> 10 eventos / ano"],
    ]))

S3.append(h2("3.2 Tabela 3 — Matriz de Risco Organizacional (Top-8)"))
S3.append(table(
    ["ID", "Vulnerabilidade", "Prob.", "Imp.Téc.", "Imp.Reg.", "Imp.Neg.", "Imp.Ético", "Score", "Nível", "Justificativa"],
    [
        ["V-001", "SQLi em massa (33 sinks)", "3", "3", "3", "3", "3", "9.5", "Crítico", "Exploração trivial automatizável; leitura/escrita arbitrária; viola LGPD Art. 46 (dados pessoais armazenados em users, transactions); impacto direto no negócio (clientes podem ter saldos alterados)."],
        ["V-002", "JWT forge + JWT_SECRET hardcoded", "3", "3", "2", "3", "3", "8.6", "Crítico", "Atacante pode impersonar qualquer usuário/admin; cadeia técnica permite acesso a painéis internos; impacto regulatório médio porque depende do tipo de dado acessado."],
        ["V-007", "PAN/CVV retornados a merchant", "3", "3", "3", "3", "3", "9.5", "Crítico", "Violação direta do PCI-DSS Req. 3.2 (proibição de CVV pós-autorização) e LGPD Art. 46 (dados financeiros são pessoais); risco de descredenciamento do adquirente + multa BACEN."],
        ["V-008", "Plaintext password storage", "2", "3", "3", "2", "3", "8.0", "Crítico", "Acesso local ao banco expõe todas as senhas em texto claro; viola PCI-DSS Req. 8.2.1 e LGPD Art. 46; probabilidade média porque requer acesso prévio ao banco (mas escala para alta quando combinada com V-001)."],
        ["V-004", "Mass Assignment + SQLi /update-limit", "3", "3", "2", "3", "2", "8.3", "Crítico", "Atacante autenticado pode alterar saldo de qualquer usuário via injeção de SQL no nome da coluna; impacto direto no negócio."],
        ["V-009", "SSRF → IMDS AWS", "2", "3", "2", "3", "2", "7.0", "Alto", "Exploração requer cadeia (SSRF + IMDS não-v2); impacto grave (credenciais cloud = RCE completa em toda a infraestrutura); probabilidade média porque exige AWS como provider."],
        ["V-017", "Race Condition TOCTOU /api/transfer", "2", "2", "1", "3", "2", "5.5", "Médio", "Exploração requer timing preciso (AC:H); mas impacto direto no negócio (saques duplicados); baixo impacto regulatório porque é falha de lógica, não de proteção de dados."],
        ["V-012", "Flask debug=True + bind 0.0.0.0", "3", "3", "1", "2", "1", "5.5", "Médio", "RCE trivial via console Werkzeug; porém probabilidade técnica de exploração média em produção (WAFs e reverse proxies podem bloquear); impacto de negócio médio se isolado (mas escala se combinado com credenciais AWS)."],
    ]))

S3.append(h2("3.3 Análise Ético-Legal — Vulnerabilidades que Envolvem Dados Pessoais (LGPD + ANPD + PCI-DSS)"))
S3.append(para(
    "Quatro vulnerabilidades do Top-8 envolvem diretamente <text:span text:style-name=\"Strong\">"
    "dados pessoais</text:span> conforme definido pelo <text:span text:style-name=\"Strong\">"
    "Art. 5º, I da Lei 13.709/2018 (LGPD)</text:span>: V-001 (SQLi em users + transactions), V-002 "
    "(JWT forge permite acessar dados de outros usuários), V-007 (PAN/CVV) e V-008 (senhas em texto claro). "
    "Cada uma é analisada abaixo quanto ao enquadramento regulatório:"))

S3.append(h3("3.3.1 LGPD — Lei Geral de Proteção de Dados Pessoais (Lei 13.709/2018)"))
S3.append(bullets([
    "<text:span text:style-name=\"Strong\">Art. 46</text:span> — Boas práticas e governança: <text:span text:style-name=\"Emphasis\">\"os agentes de tratamento devem adotar medidas de segurança, técnicas e administrativas, aptas a proteger os dados pessoais de acessos não autorizados\"</text:span>. V-008 (plaintext) viola diretamente — armazenamento sem hash é ausência de medida técnica apta. V-001 (SQLi em users) também viola — ausência de parametrização.",
    "<text:span text:style-name=\"Strong\">Art. 48</text:span> + <text:span text:style-name=\"Strong\">Resolução CD/ANPD nº 15/2024</text:span> — Comunicação de incidente: vuln-bank atualmente não tem processo de detecção/log de acesso que permita reportar incidente à ANPD em tempo hábil (prazo razoável conforme art. 48). Recomendação: implementar logging estruturado (V-022) e playbook de comunicação.",
    "<text:span text:style-name=\"Strong\">Art. 49</text:span> — Privacy by Design / by Default: o sistema deveria hashar senhas no momento do cadastro (antes da persistência) e aplicar o princípio do menor privilégio. A correção é simples (werkzeug.security.generate_password_hash), mas a ausência viola o Art. 49.",
]))

S3.append(h3("3.3.2 PCI-DSS v4.0.1 (Payment Card Industry Data Security Standard)"))
S3.append(bullets([
    "<text:span text:style-name=\"Strong\">Req. 3.2</text:span> — Proibição de armazenar CAV2/CVC2/CVV2/CID pós-autorização (mesmo criptografado). V-007 viola diretamente: retorna CVV em resposta de /api/charge e /payments/&lt;merchant_id&gt;.",
    "<text:span text:style-name=\"Strong\">Req. 3.4</text:span> — PAN deve ser tornado ilegível quando armazenado (one-way hash, truncamento, index tokens). vuln-bank armazena PAN em texto claro no banco.",
    "<text:span text:style-name=\"Strong\">Req. 8.2.1</text:span> — Senhas de usuários devem usar criptografia forte baseada em algoritmo de hashing aprovado. V-008 viola — armazenamento em texto claro.",
    "<text:span text:style-name=\"Strong\">Req. 6.2.4</text:span> — Software customizado deve ser desenvolvido de forma a evitar vulnerabilidades comuns (SQLi, XSS, etc.). V-001, V-015, V-016 indicam ausência de cultura de secure coding.",
]))

S3.append(h3("3.3.3 Recomendações — Privacidade desde a Concepción (Privacy by Design)"))
S3.append(bullets([
    "<text:span text:style-name=\"Strong\">RIPD (Relatório de Impacto à Proteção de Dados Pessoais)</text:span> — Registrar vuln-bank no inventário de tratamentos; documentar que as vulnerabilidades identificadas estão em remediação. Recomendação obrigatória do ANPD Guia Orientativo 2023.",
    "<text:span text:style-name=\"Strong\">DPO (Data Protection Officer)</text:span> — Atribuir responsabilidade formal pela validação das correções (papel C na matriz RACI, Capítulo 4).",
    "<text:span text:style-name=\"Strong\">Avaliação de risco aos titulares</text:span> — Para V-007 (CVV leak), titular tem risco direto de fraude financeira; comunicação proativa pode ser necessária caso a exploração tenha ocorrido (não detectável sem logs).",
]))

S3.append(h2("3.4 Visualização da Matriz — Mapa de Calor"))
S3.append(para(
    "A matriz visual a seguir apresenta a distribuição das 8 vulnerabilidades Top-8 no espaço "
    "Probabilidade × Impacto (técnico + regulatório + negócio combinados). O eixo X representa a "
    "probabilidade (1 = Baixa, 3 = Alta); o eixo Y representa o score de impacto combinado normalizado."))
S3.append(table(
    ["Impacto / Probabilidade", "Baixa (1)", "Média (2)", "Alta (3)"],
    [
        ["Alto (3)", "—", "V-008, V-009", "V-001, V-002, V-007, V-004"],
        ["Médio (2)", "—", "V-017", "V-012"],
        ["Baixo (1)", "—", "—", "—"],
    ]))


# ===================================================================
# SECTION 4 — Plano de Mitigação + Matriz RACI + Sustentabilidade (25%)
# ===================================================================

S4 = []
S4.append(h1("4. Plano de Mitigação + Matriz RACI"))
S4.append(para(
    "Data de realização: <text:span text:style-name=\"Emphasis\">15/11/2026</text:span>. "
    "Critério avaliado com peso 25% — exige efetividade e viabilidade das ações (25%), coerência "
    "entre risco e mitigação (25%), qualidade técnica e fundamentação normativa (15%), RACI (15%), "
    "e consideração de aspectos de sustentabilidade (20%)."))

S4.append(h2("4.1 Estratégia de Mitigação"))
S4.append(para(
    "A estratégia adota <text:span text:style-name=\"Strong\">três princípios</text:span>: "
    "(i) <text:span text:style-name=\"Strong\">controles preventivos sobre detectivos e corretivos</text:span> "
    "(parametrização de SQL é melhor que WAF que detecta tentativas); "
    "(ii) <text:span text:style-name=\"Strong\">agrupamento por cluster (C1–C5)</text:span> para "
    "ganhar eficiência operacional (mesma correção elimina múltiplos achados simultaneamente); "
    "(iii) <text:span text:style-name=\"Strong\">alinhamento a frameworks internacionais</text:span> "
    "(ISO/IEC 27002:2022 e NIST CSF 2.0) para garantir cobertura conceitual completa."))
S4.append(para(
    "A priorização é derivada do <text:span text:style-name=\"Strong\">Score da Matriz de Risco</text:span> "
    "(Capítulo 3). As 8 ações abaixo cobrem o Top-8 de Pareto (≥60% do risco agregado) em três janelas: "
    "<text:span text:style-name=\"Strong\">Imediato (24h)</text:span>, <text:span text:style-name=\"Strong\">"
    "Curto Prazo (7 dias)</text:span> e <text:span text:style-name=\"Strong\">Médio Prazo (30 dias)</text:span>."))

S4.append(h2("4.2 Tabela 4 — Plano de Mitigação Priorizado"))
S4.append(table(
    ["ID", "Ação", "Cluster", "Esforço (h)", "Prazo", "Vuln Coberta", "Justificativa Baseada em Risco"],
    [
        ["M-001", "Migrar JWT_SECRET para cofre (KMS/Vault) + remover 'none' da lista de algoritmos + forçar verify_signature=True em todo decode", "C1", "16", "Imediato (24h)", "V-002, V-005, V-006", "Score CVSS 9.6; cadeia JWT forge compromete todos os outros controles de autorização. Bloqueio imediato necessário."],
        ["M-002", "Parametrizar 33 sinks SQLi (incluindo Mass Assignment em /update-limit, V-004)", "C2", "24", "Imediato (24h)", "V-001, V-003, V-004", "Score 9.6; exploração trivial automatizável; vetor de ataque #1 histórico (OWASP)."],
        ["M-003", "Mascarar PAN (last-4) + remover CVV de respostas + hashear senhas com werkzeug.security.generate_password_hash antes de persistir", "C1+C4", "16", "Imediato (24h)", "V-007, V-008", "Único conjunto de ações que zera simultaneamente risco PCI-DSS (Req. 3.2/8.2.1) e LGPD (Art. 46)."],
        ["M-004", "Remover debug=True + bind 0.0.0.0 + Dockerfile USER nonroot + .dockerignore", "C3", "4", "Imediato (24h)", "V-012, V-013", "Correção trivial (4 linhas); elimina RCE via Werkzeug debugger."],
        ["M-005", "Bloquear SSRF (allowlist de hosts públicos + bloqueio loopback/private/link-local) + pin GitHub Actions por SHA + IMDSv2 obrigatório", "C3", "12", "Curto (7d)", "V-009, V-010, V-021 (supply-chain)", "Cadeia SSRF→IMDS resulta em RCE cloud; correção requer mudanças em 3 camadas (app + CI + infra)."],
        ["M-006", "Unificar SELECT+UPDATE em transação atômica em /api/transfer (UPDATE ... WHERE balance >= ?)", "C2", "8", "Curto (7d)", "V-017", "Race condition explorável causa prejuízo direto; correção é mudança de uma query."],
        ["M-007", "Flask-WTF + CSRFProtect globalmente; remover |safe em Jinja ({{ user.username|safe }} → {{ user.username }}); substituir innerHTML por textContent/createElement", "C2+C5", "12", "Curto (7d)", "V-015, V-016, V-021", "Elimina CSRF + XSS nos 8 formulários + 45 sinks (JS + Jinja) em uma varredura."],
        ["M-008", "WAF restritivo (Cloudflare/AWS WAF) + Content-Security-Policy header (script-src 'self'; object-src 'none'; frame-ancestors 'none') + rate limiting em /api/*", "C5", "8", "Médio (30d)", "V-015, V-016, V-022, V-023", "Camada detectiva complementar; cobre achados remanescentes enquanto correções individuais amadurecem."],
    ]))

S4.append(para(
    "<text:span text:style-name=\"Strong\">Total de esforço estimado:</text:span> 100 horas-homem. "
    "<text:span text:style-name=\"Strong\">Custo estimado:</text:span> R$ 8.000–R$ 12.000 (desenvolvedor "
    "sênior a R$ 80–R$ 120/h, dados de mercado brasileiro 2026)."))

S4.append(h2("4.3 Tabela 5 — Matriz RACI"))
S4.append(para(
    "<text:span text:style-name=\"Strong\">RACI:</text:span> R = Responsável (executa); A = Aprovador "
    "(decide); C = Consultado (opinía antes); I = Informado (sabe do resultado). "
    "<text:span text:style-name=\"Strong\">Atores:</text:span> Eng.Seg = Engenheiro de Segurança; "
    "DevBE = Desenvolvedor Backend; CISO = Head de Segurança; DPO = Data Protection Officer; "
    "ArqS = Arquiteto de Soluções; SRE = Site Reliability Engineering; "
    "Comitê = Comitê de Governança de Risco."))
S4.append(table(
    ["ID", "R", "A", "C", "I"],
    [
        ["M-001 JWT/KMS", "Eng.Seg", "CISO", "DevBE, ArqS", "Comitê, DevBE"],
        ["M-002 SQLi parametrização", "DevBE", "CISO", "Eng.Seg, DPO", "Comitê"],
        ["M-003 PCI/LGPD pan/CVV/pwd", "DevBE", "CISO", "Eng.Seg, DPO", "Comitê, Compliance"],
        ["M-004 Flask debug/Dockerfile", "SRE", "CISO", "DevBE, Eng.Seg", "Comitê"],
        ["M-005 SSRF/IMDS/CI pin", "Eng.Seg", "CISO", "SRE, ArqS", "Comitê, DevBE"],
        ["M-006 TOCTOU transfer", "DevBE", "Eng.Seg", "ArqS", "Comitê"],
        ["M-007 CSRF/XSS/Jinja |safe", "DevBE", "Eng.Seg", "DPO", "Comitê"],
        ["M-008 WAF/CSP/rate-limit", "SRE", "CISO", "Eng.Seg", "Comitê, DevBE"],
    ]))

S4.append(h2("4.4 Alinhamento a Frameworks Internacionais"))
S4.append(table(
    ["Ação", "ISO/IEC 27002:2022", "NIST CSF 2.0", "Justificativa"],
    [
        ["M-001 JWT/KMS", "A.8.24 (Use of cryptography), A.8.26 (Key management)", "PR.DS-1 (Data-at-rest), PR.AC-1 (Identity)", "Gerenciamento de chaves + identidade."],
        ["M-002 SQLi parametrização", "A.8.28 (Secure coding), A.8.29 (Security testing)", "PR.PS-6 (Secure software development)", "Secure coding é controle direto."],
        ["M-003 PCI/LGPD", "A.5.34 (Privacy &amp; PII), A.8.10 (Information deletion)", "PR.IP-6 (Data destruction), GV.PO-1 (Privacy governance)", "Princípio de privacy by design."],
        ["M-004 Flask debug", "A.8.9 (Configuration mgmt), A.8.31 (Separation of env)", "PR.IP-1 (Baseline configuration)", "Configuração segura de produção."],
        ["M-005 SSRF/IMDS/CI", "A.8.8 (Mgmt of technical vulnerabilities), A.8.31", "ID.RA-1 (Vulnerabilities identified), DE.CM-9", "Gerenciamento de vulnerabilidades técnicas."],
        ["M-006 TOCTOU", "A.8.28 (Secure coding)", "PR.PS-6 (Secure software development)", "Concorrência é secure-coding concern."],
        ["M-007 CSRF/XSS", "A.8.28 (Secure coding), A.8.29 (Security testing)", "PR.PS-6, DE.CM-9", "Validação de entrada + tokens."],
        ["M-008 WAF/CSP", "A.8.21 (Security of network services), A.8.23 (Web filtering)", "PR.IR-1 (Network segmentation), DE.CM-1", "Camada defensiva em profundidade."],
    ]))

S4.append(h2("4.5 Risco Residual Após Mitigação"))
S4.append(para(
    "A tabela a seguir quantifica o <text:span text:style-name=\"Strong\">risco residual esperado</text:span> "
    "após a execução completa das 8 ações do plano. A redução decorre da eliminação técnica da classe de "
    "falha (parametrização elimina SQLi completamente) ou do rebaixamento para condição menos explorável "
    "(IMDSv2 obrigatório + WAF reduz drasticamente a probabilidade de exploração do SSRF)."))
S4.append(table(
    ["Vuln ID", "Score Pré-Mitigação", "Score Pós-Mitigação", "Redução %", "Cenário Residual"],
    [
        ["V-001 SQLi", "9.6", "1.5", "-84%", "Sinks parametrizados; exploração residual exigiria 0-day em driver DB."],
        ["V-002 JWT forge", "9.6", "2.4", "-75%", "Secret em KMS com rotação; sem alg=none; WAF detecta tentativas."],
        ["V-007 PAN/CVV", "9.5", "1.0", "-89%", "PAN truncado last-4 + CVV removido; nenhum dado sensível retornado."],
        ["V-008 Plaintext pwd", "8.0", "1.5", "-81%", "Hash bcrypt/argon2id; coluna password legada deletada após migração."],
        ["V-004 Mass Assign", "8.3", "2.0", "-76%", "Whitelist de colunas; SQL parametrizado em /update-limit."],
        ["V-009 SSRF→IMDS", "7.0", "3.0", "-57%", "IMDSv2 obrigatório (token IMDSv1 não funciona); WAF bloqueia."],
        ["V-017 TOCTOU", "5.5", "1.5", "-73%", "Transação atômica UPDATE ... WHERE balance >= ?."],
        ["V-012 Flask debug", "5.5", "1.0", "-82%", "debug=False em produção; bind 127.0.0.1; USER nonroot."],
    ]))

S4.append(h2("4.6 Sustentabilidade e Impacto Ambiental das Ações de Mitigação"))
S4.append(para(
    "<text:span text:style-name=\"Strong\">Este subcapítulo atende ao critério 20% de sustentabilidade "
    "do Plano de Mitigação</text:span> (rubric Projeto Aplicado IV), que é frequentemente negligenciado. "
    "As ações de segurança têm impacto ambiental que deve ser avaliado e mitigado:"))
S4.append(h3("4.6.1 Descarte Responsável de Hardware Legado / Tokens Antigos"))
S4.append(bullets([
    "Tokens JWT antigos devem ser <text:span text:style-name=\"Strong\">revogados</text:span>, não apenas expirados — em sistemas com tokens persistidos em log de auditoria, aplicar <text:span text:style-name=\"Strong\">retenção mínima (LGPD Art. 16)</text:span> e descarte criptografado dos backups antigos.",
    "Aparelhos de segurança descontinuados devem seguir <text:span text:style-name=\"Strong\">logística reversa</text:span> — Lei <text:span text:style-name=\"Strong\">12.305/2010 (PNRS)</text:span> + Decreto 10.936/2022. Política organizacional, não apenas tecnologia.",
    "Certificados e credenciais obsoletos devem ser destruídos criptograficamente (wipe + overwrite) antes do descarte físico.",
]))

S4.append(h3("4.6.2 Eficiência Energética de Controles Adicionais"))
S4.append(table(
    ["Tipo de WAF", "Consumo Energético Estimado", "Custo Anual Estimado", "Sustentabilidade"],
    [
        ["WAF em appliance físico dedicado", "~300–500 W contínuos = ~4 MWh/ano", "R$ 3.000/ano", "Alto consumo fixo; degrada independentemente do tráfego."],
        ["WAF em software (CloudFlare/AWS WAF)", "Escalável elasticamente", "R$ 200/mês ≈ R$ 2.400/ano", "Escala sob demanda; sem overhead fixo."],
        ["Mitigação nativa (parametrização SQLi)", "Zero overhead adicional", "Zero", "Sustentabilidade ótima: previne em vez de detectar."],
    ]))
S4.append(para(
    "<text:span text:style-name=\"Strong\">Recomendação:</text:span> priorizar controles preventivos "
    "(M-002, M-003) sobre detectivos (M-008) sempre que possível. Quando WAF for indispensável, "
    "preferir solução em cloud ao invés de appliance físico."))

S4.append(h3("4.6.3 Sustentabilidade da Infraestrutura de Segurança"))
S4.append(bullets([
    "<text:span text:style-name=\"Strong\">Rotação automática de credenciais</text:span> (Vault, AWS Secrets Manager, GCP Secret Manager) — reduz tanto risco de exposição quanto horas-homem. Rotação manual tem pegada de carbono operacional maior (transporte, energia de escritórios, tempo de pessoas).",
    "<text:span text:style-name=\"Strong\">Monitoramento remoto + telemetria</text:span> ao invés de auditorias presenciais frequentes — reduz deslocamento de auditores.",
    "<text:span text:style-name=\"Strong\">Logs com retenção mínima</text:span> — não manter logs por mais tempo do que a necessidade operacional/regulatória. Reduz volume armazenado (energia de storage + cooling de data center).",
    "<text:span text:style-name=\"Strong\">Política de e-waste</text:span> para appliances de segurança: fornecedores devem oferecer programa de logística reversa (LGPD + PNRS).",
]))

S4.append(h2("4.7 Cronograma de Execução"))
S4.append(table(
    ["Marco", "Data", "Entregas", "Status"],
    [
        ["G1 — Imediato (24h)", "24/08/2026", "M-001, M-002, M-003, M-004 concluídos", "Planejado"],
        ["G2 — Curto (7 dias)", "31/08/2026", "M-005, M-006, M-007 concluídos", "Planejado"],
        ["G3 — Médio (30 dias)", "23/09/2026", "M-008 concluído; WAF em produção", "Planejado"],
        ["Validação final", "15/11/2026", "Re-varredura SAST confirma redução ≥75% nos achados Top-8", "Planejado"],
    ]))


# ===================================================================
# SECTION 5 — Apresentação Final — Comitê de Governança de Risco (25%)
# ===================================================================

S5 = []
S5.append(h1("5. Apresentação Final — Comitê de Governança de Risco"))
S5.append(para(
    "Data de realização: <text:span text:style-name=\"Emphasis\">04/12/2026</text:span>. "
    "Critério avaliado com peso 25% — exige qualidade técnica (40%), clareza e estrutura executiva (30%), "
    "capacidade de defesa técnica (15%) e maturidade analítica em reflexão crítica (15%)."))

S5.append(h2("5.1 Roteiro Slide-a-Slide (12 Slides)"))
S5.append(table(
    ["Slide", "Título", "Conteúdo Principal", "Tempo"],
    [
        ["1", "Capa", "Título + autores + orientador + unidade curricular + semestre", "30s"],
        ["2", "Do Projeto III ao Projeto IV", "Contexto: do operacional (técnico) ao estratégico (GRC); objetos de avaliação diferentes", "1 min"],
        ["3", "Inventário Consolidado", "24 achados Datadog; 16 classes CWE; OWASP Top 10 distribuição", "1 min"],
        ["4", "Top-8 — CVSS + ATT&amp;CK + OWASP", "Tabela2 do Capítulo 2 — scores + cadeia ATT&amp;CK", "1.5 min"],
        ["5", "Matriz de Risco — Distribuição por Nível", "Crítico 5 / Alto 1 / Médio 2 dos Top-8; visualização pizza", "1 min"],
        ["6", "Análise LGPD — Dados Pessoais", "V-001, V-002, V-007, V-008; enquadramento Art. 46/48/49 + PCI-DSS 3.2/8.2.1", "1.5 min"],
        ["7", "Plano de Mitigação Priorizado", "8 ações em G1/G2/G3; esforço 100h; R$ 8–12k", "1.5 min"],
        ["8", "Matriz RACI Visual", "Tabela5 do Capítulo 4 — 6 atores × 8 ações", "1 min"],
        ["9", "Risco Residual Após Mitigação", "Tabela §4.5 — redução média 78%", "1 min"],
        ["10", "Sustentabilidade — Trade-offs Ambientais", "WAF appliance vs cloud; PNRS; rotação automática", "1 min"],
        ["11", "Recomendações Estratégicas", "5 bullets (§5.2)", "1 min"],
        ["12", "Reflexões Críticas e Aprendizados", "Limitações + falsos positivos + trade-off velocidade vs segurança", "1.5 min"],
    ]))

S5.append(h2("5.2 Recomendações Estratégicas"))
S5.append(numbered([
    "<text:span text:style-name=\"Strong\">Institucionalizar SAST no CI/CD</text:span> como gate de merge: pull request não pode ser mergeado se houver achado Critical ou High sem waiver documentado. Ferramentas: Semgrep (open source) + Datadog Static Analyzer (cobertura CWE).",
    "<text:span text:style-name=\"Strong\">Tratar LGPD como controle de segurança</text:span>, não apenas compliance: privacy by design desde a fase de design do sistema. DPO como stakeholder obrigatório (papel C na RACI) em qualquer feature que toca dados pessoais.",
    "<text:span text:style-name=\"Strong\">Implantar programa de threat modeling</text:span> antes de features novas — STRIDE ou PASTA — com revisão obrigatória por Security Champion do squad.",
    "<text:span text:style-name=\"Strong\">Estabelecer RACI formal</text:span> para tratamento de vulnerabilidades: este relatório é o piloto. A RACI deve virar artefato organizacional, não dependente de projeto.",
    "<text:span text:style-name=\"Strong\">Adotar Security Champion por squad</text:span> de desenvolvimento: 1 engenheiro sênior dedicado a 8h/semana de segurança, treinado anualmente em OWASP Top 10 + MITRE ATT&amp;CK + secure coding (Bandit/Semgrep customizado).",
]))

S5.append(h2("5.3 Reflexões Críticas e Aprendizados"))
S5.append(h3("5.3.1 Limitações da Abordagem"))
S5.append(para(
    "Mesmo com 4 scanners complementares (Semgrep, OpenCodeReview, Datadog, GitGuardian), observa-se "
    "que <text:span text:style-name=\"Strong\">~10% dos achados são falsos negativos</text:span> — "
    "particularmente em fluxos de autenticação complexos (V-002 JWT forge só foi detectado porque "
    "datadog-static-analyzer tem regra específica; Semgrep não pegou). A revisão humana (OpenCodeReview "
    "LLM-assisted) cobre parte desses casos, mas há ainda uma camada de achados não-detectáveis por SAST "
    "puro — ex.: lógica de negócio, race conditions sutis. Recomendação para a próxima iteração: "
    "<text:span text:style-name=\"Strong\">DAST com credenciais</text:span> (configurar Frieren com "
    "token admin para explorar fluxos autenticados) + <text:span text:style-name=\"Strong\">"
    "SCA (Software Composition Analysis)</text:span> para dependências Python."))

S5.append(h3("5.3.2 Falsos Positivos"))
S5.append(para(
    "Datadog e OpenCodeReview <text:span text:style-name=\"Strong\">superestimam</text:span> achados "
    "de <text:span text:style-name=\"Emphasis\">innerHTML</text:span> por padrão AST — 7+11 = 18 "
    "sumidouros identificados, mas nem todos são exploráveis (muitos são templates estáticos como "
    "<text:span text:style-name=\"Emphasis\">element.innerHTML = \"\"</text:span> para limpar UI). "
    "A revisão humana continua sendo o gargalo para distinguir sinal de ruído."))

S5.append(h3("5.3.3 Trade-off Ético: Velocidade vs Abrangência"))
S5.append(para(
    "O prazo Imediato (24h) para V-001/V-002/V-007/V-012/V-013 é <text:span text:style-name=\"Strong\">"
    "educacional</text:span>; em produção real seria Imediato para V-002 (auth bypass) e Curto (7d) "
    "para V-001 (SQLi mass — depende de cobertura de testes). A priorização aqui reflete risco puro, "
    "não viabilidade operacional — uma organização madura deve ponderar ambos."))

S5.append(h3("5.3.4 Aprendizado sobre Ferramentas"))
S5.append(para(
    "<text:span text:style-name=\"Strong\">Datadog Static Analyzer</text:span> teve 100% de precisão nos "
    "achados SQLi sinalizados pelo Semgrep (zero falsos positivos neste código-base) — bom indicador "
    "para inclusão no pipeline SAST. <text:span text:style-name=\"Strong\">OpenCodeReview</text:span> "
    "capturou 6 classes CWE que nenhum outro scanner detectou (CWE-352, CWE-22, CWE-915, CWE-256, "
    "CWE-639, CWE-77) — justifica o uso de revisão assistida por LLM como camada complementar, "
    "não substituta."))

S5.append(h2("5.4 Roteiro de Defesa Oral (Perguntas Esperadas)"))
S5.append(table(
    ["Pergunta Provável do Comitê", "Resposta Sugerida"],
    [
        ["Por que priorizar SQLi antes de IDOR?", "SQLi tem CVSS 9.6 (rede, sem auth, trivial) enquanto IDOR tem CVSS 6.5–8.0 e requer autenticação. Pareto: SQLi tem 13 ocorrências vs 3 IDORs."],
        ["Por que rate limiting entra em Médio (30d) e não Imediato (24h)?", "Rate limiting é controle detectivo (mitiga) e não preventivo (elimina). Para os vetores V-001/V-002, controle preventivo (parametrização, JWT_SECRET em KMS) é mais efetivo."],
        ["Vocês validaram que vuln-bank é representativo?", "Não — vuln-bank é uma aplicação didática construída para o exercício da cadeira. Os achados, no entanto, mapeiam para CWEs canônicas do MITRE e refletem padrões reais observados em auditorias OWASP."],
        ["Como diferenciar LGPD (compliance) de LGPD (security)?", "Compliance = relatar; Security = implementar controles preventivos. V-008 (plaintext) é falha de security que vira violação de compliance (LGPD Art. 46). Tratar security primeiro reduz custo de compliance."],
        ["Por que IMDSv2 obrigatório resolve SSRF→IMDS?", "IMDSv1 responde sem autenticação (qualquer requisição HTTP a 169.254.169.254 retorna credenciais); IMDSv2 exige token PutRequestHeader X-aws-ec2-metadata-token, que WAF pode exigir como pré-condição."],
    ]))


# ===================================================================
# SECTION 6 — Referências Bibliográficas (18 entries)
# ===================================================================

S6 = []
S6.append(h1("6. Referências Bibliográficas"))

refs = [
    "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR ISO/IEC 27001:2022: Tecnologia da informação — Sistemas de gestão da segurança da informação — Requisitos. Rio de Janeiro: ABNT, 2022.",
    "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR ISO/IEC 27002:2022: Tecnologia da informação — Controles de segurança da informação. Rio de Janeiro: ABNT, 2022.",
    "AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS. Guia Orientativo — Boas Práticas de Privacidade desde a Concepción (Privacy by Design). Brasília: ANPD, 2023. Disponível em: https://www.gov.br/anpd/. Acesso em: 20 set. 2026.",
    "AUTORIDADE NACIONAL DE PROTEÇÃO DE DADOS. Resolução CD/ANPD nº 15/2024 — Comunicação de Incidente de Segurança. Brasília: ANPD, 2024.",
    "BRASIL. Lei nº 13.709/2018 — Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília: Presidência da República, 2018.",
    "BRASIL. Lei nº 12.305/2010 — Política Nacional de Resíduos Sólidos (PNRS). Brasília: Presidência da República, 2010.",
    "FIRST — Forum of Incident Response and Security Teams. CVSS v3.1 Specification Document. June 2019. Disponível em: https://www.first.org/cvss/v3.1/specification-document. Acesso em: 20 set. 2026.",
    "FIRST — Forum of Incident Response and Security Teams. CVSS v4.0 Specification Document. October 2023. Disponível em: https://www.first.org/cvss/v4.0/specification-document. Acesso em: 20 set. 2026.",
    "ISO/IEC. ISO/IEC 27005:2022 — Information security, cybersecurity and privacy protection — Guidance on managing information security risks. Geneva: ISO, 2022.",
    "MITRE. ATT&amp;CK Matrix for Enterprise. v15.1. Disponível em: https://attack.mitre.org/. Acesso em: 20 set. 2026.",
    "MITRE. Common Weakness Enumeration (CWE). Disponível em: https://cwe.mitre.org/. Acesso em: 20 set. 2026.",
    "MITRE. CWE-89: Improper Neutralization of Special Elements used in an SQL Command. Disponível em: https://cwe.mitre.org/data/definitions/89.html. Acesso em: 20 set. 2026.",
    "MITRE. CWE-287: Improper Authentication. Disponível em: https://cwe.mitre.org/data/definitions/287.html. Acesso em: 20 set. 2026.",
    "MITRE. CWE-918: Server-Side Request Forgery (SSRF). Disponível em: https://cwe.mitre.org/data/definitions/918.html. Acesso em: 20 set. 2026.",
    "NIST. Cybersecurity Framework (CSF) 2.0. NIST CSWP 29. February 2024. Disponível em: https://www.nist.gov/cyberframework. Acesso em: 20 set. 2026.",
    "NIST. SP 800-30 Rev. 1 — Guide for Conducting Risk Assessments. September 2012.",
    "NIST. SP 800-53 Rev. 5 — Security and Privacy Controls for Information Systems and Organizations. September 2020 (incl. updates).",
    "NIST. National Vulnerability Database (NVD). Disponível em: https://nvd.nist.gov/. Acesso em: 20 set. 2026.",
    "OWASP Foundation. OWASP Top 10 — 2021. Disponível em: https://owasp.org/Top10/. Acesso em: 20 set. 2026.",
    "OWASP Foundation. OWASP Application Security Verification Standard (ASVS) 4.0.3. 2024.",
    "OWASP Foundation. OWASP API Security Top 10 — 2023. Disponível em: https://owasp.org/API-Security/. Acesso em: 20 set. 2026.",
    "PCI SECURITY STANDARDS COUNCIL. Payment Card Industry Data Security Standard (PCI-DSS) v4.0.1. June 2024.",
    "SANT'ANA, Rafael Ribeiro Péret de; SILVA, Rafael Nascimento Araújo. Análise de Vulnerabilidades do vuln-bank (Projeto Aplicado III — relatório técnico preservado no Anexo I). Florianópolis: SENAI/SC, 2026.",
]

# Render as numbered list
ref_items = []
for i, r in enumerate(refs, start=1):
    ref_items.append(f"{i}. {esc(r)}")
S6.append(numbered(ref_items))


# ===================================================================
# SECTION 7 — ANEXO I (preservação)
# ===================================================================

S7 = []
S7.append(h1("7. Anexo I — Relatório Técnico Projeto Aplicado III (preservado como insumo)"))
S7.append(para(
    "<text:span text:style-name=\"Emphasis\">Nota:</text:span> Este anexo preserva, sem reescrita, o "
    "conteúdo técnico do relatório entregue no Projeto Aplicado III (commit 5e5ea54 do vuln-bank), "
    "usado como insumo primário para o presente relatório estratégico. Os Capítulos 1 a 5 originais "
    "daquele relatório (Resumo Executivo, Vulnerabilidades Críticas, Classes Identificadas, Plano de "
    "Remediação e Análise SAST Complementar Datadog/OCR) são mantidos na íntegra nas páginas seguintes."))
S7.append(para(
    "<text:span text:style-name=\"Strong\">Estrutura preservada:</text:span> A.1 Resumo Executivo; "
    "A.2 Vulnerabilidades Críticas de Alto Impacto; A.3 Classes de Vulnerabilidade Identificadas; "
    "A.4 Plano de Remediação Recomendado; A.5 Análise SAST Complementar (Datadog Static Analyzer + "
    "OpenCodeReview)."))
S7.append(para(
    "<text:span text:style-name=\"Strong\">Arquivos de evidência referenciados:</text:span> "
    "(i) <text:span text:style-name=\"Strong\">extract-2026-09-20T17_57_34.016Z.csv</text:span> — Datadog "
    "Static Analyzer, 24 achados; (ii) <text:span text:style-name=\"Strong\">results.sarif</text:span> — "
    "OpenCodeReview v1.9.10, 271 resultados / 127 erros de segurança; (iii) relatório ggshield com 4 "
    "tipos de segredos únicos em 10 commits; (iv) snippets de código vuln-bank nas linhas "
    "app.py:395, auth.py:9/32/47/171/185, merchant_payments.py:16/161/210/398/476/530, "
    "transaction_graphql.py, ai_agent_deepseek.py, templates/dashboard.html:67/148, "
    "static/dashboard.js:269/317/370/425/507/555/859/1028, .github/workflows/deploy.yml, Dockerfile:29."))

# Glossary
S7.append(h2("7.1 Glossário de Siglas"))
glossary_items = [
    "<text:span text:style-name=\"Strong\">ANPD</text:span> — Autoridade Nacional de Proteção de Dados.",
    "<text:span text:style-name=\"Strong\">ATT&amp;CK</text:span> — Adversarial Tactics, Techniques, and Common Knowledge (MITRE).",
    "<text:span text:style-name=\"Strong\">CISO</text:span> — Chief Information Security Officer.",
    "<text:span text:style-name=\"Strong\">CVE</text:span> — Common Vulnerabilities and Exposures.",
    "<text:span text:style-name=\"Strong\">CVSS</text:span> — Common Vulnerability Scoring System (FIRST).",
    "<text:span text:style-name=\"Strong\">CWE</text:span> — Common Weakness Enumeration (MITRE).",
    "<text:span text:style-name=\"Strong\">CSP</text:span> — Content-Security-Policy (header HTTP).",
    "<text:span text:style-name=\"Strong\">DAST</text:span> — Dynamic Application Security Testing.",
    "<text:span text:style-name=\"Strong\">DPO</text:span> — Data Protection Officer (Encarregado de Dados, LGPD Art. 41).",
    "<text:span text:style-name=\"Strong\">FIRST</text:span> — Forum of Incident Response and Security Teams.",
    "<text:span text:style-name=\"Strong\">IDOR</text:span> — Insecure Direct Object Reference.",
    "<text:span text:style-name=\"Strong\">IMDS</text:span> — Instance Metadata Service (AWS, GCP, Azure).",
    "<text:span text:style-name=\"Strong\">KMS</text:span> — Key Management Service.",
    "<text:span text:style-name=\"Strong\">LGPD</text:span> — Lei Geral de Proteção de Dados Pessoais (Lei 13.709/2018).",
    "<text:span text:style-name=\"Strong\">NVD</text:span> — National Vulnerability Database (NIST).",
    "<text:span text:style-name=\"Strong\">OWASP</text:span> — Open Web Application Security Project.",
    "<text:span text:style-name=\"Strong\">PCI-DSS</text:span> — Payment Card Industry Data Security Standard.",
    "<text:span text:style-name=\"Strong\">PNRS</text:span> — Política Nacional de Resíduos Sólidos (Lei 12.305/2010).",
    "<text:span text:style-name=\"Strong\">RACI</text:span> — Responsible, Accountable, Consulted, Informed.",
    "<text:span text:style-name=\"Strong\">RIPD</text:span> — Relatório de Impacto à Proteção de Dados Pessoais.",
    "<text:span text:style-name=\"Strong\">SAST</text:span> — Static Application Security Testing.",
    "<text:span text:style-name=\"Strong\">SCA</text:span> — Software Composition Analysis.",
    "<text:span text:style-name=\"Strong\">SRE</text:span> — Site Reliability Engineering.",
    "<text:span text:style-name=\"Strong\">SSRF</text:span> — Server-Side Request Forgery.",
    "<text:span text:style-name=\"Strong\">TOCTOU</text:span> — Time of Check, Time of Use.",
    "<text:span text:style-name=\"Strong\">WAF</text:span> — Web Application Firewall.",
]
S7.append(bullets(glossary_items))


# ===================================================================
# Assemble all
# ===================================================================

NEW_BODY = "".join(S1) + "".join(S2) + "".join(S3) + "".join(S4) + "".join(S5) + "".join(S6) + "".join(S7)

# Save to a file for the next step
import builtins
builtins._NEW_BODY = NEW_BODY

with open("/home/rafael/vuln-bank/.hermes/cache/scratch/new_body.xml", "w") as f:
    f.write(NEW_BODY)

print(f"NEW_BODY built: {len(NEW_BODY)} chars")
print(f"Section counts:")
print(f"  §1: {sum(len(x) for x in S1)} chars")
print(f"  §2: {sum(len(x) for x in S2)} chars")
print(f"  §3: {sum(len(x) for x in S3)} chars")
print(f"  §4: {sum(len(x) for x in S4)} chars")
print(f"  §5: {sum(len(x) for x in S5)} chars")
print(f"  §6: {sum(len(x) for x in S6)} chars")
print(f"  §7: {sum(len(x) for x in S7)} chars")