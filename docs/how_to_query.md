
### 1. Primeiro: definir o Top 3

A base vem nesta ordem:

1. **Top 3 hard skills da Regra das 10 Vagas**
2. **Cargo/objetivo informado pelo aluno**
3. **Hard skills presentes no currículo/perfil atualizado**

O Top 3 precisa ser **hard skill**. Não entram idioma, localização, senioridade, soft skill ou modelo de trabalho. 

Exemplo:

> Objetivo: Full Stack Ruby on Rails com React

Top 3:

**Ruby on Rails + React + PostgreSQL**

---

### 2. Depois: normalizar `/`

Se houver alternativas, `/` vira `OR`.

Exemplo:

`Ruby on Rails / Rails + React / React.js + PostgreSQL`

vira:

`("Ruby on Rails" OR "Rails") AND ("React" OR "React.js") AND "PostgreSQL"`

Nunca vou pesquisar a barra literalmente quando ela representar alternativas. 

---

# Cenário 1 — Vaga gringa: Posts do LinkedIn

É a **primeira query obrigatória** e tem prioridade máxima.

Modelo:

```text
site:linkedin.com/posts ("hiring" OR "we are hiring" OR "looking for" OR "open role" OR "opportunity" OR "contractor") AND "[KEYWORD 1]" AND "[KEYWORD 2]" AND ("Brazil" OR "LATAM" OR "remote") -Staff -Lead -C2C -"US Based" -Hybrid -Site -"US Only" -"No Visa" -"Citizens Only" -"Security Clearance" -"site" -"Local Only" -"Must be located" -"based"
```

Exemplo com Ruby/Rails + React + PostgreSQL:

```text
site:linkedin.com/posts ("hiring" OR "we are hiring" OR "looking for" OR "open role" OR "opportunity" OR "contractor") AND ("Ruby on Rails" OR "Rails") AND "React" AND "PostgreSQL" AND ("Brazil" OR "LATAM" OR "remote") -Staff -Lead -C2C -"US Based" -Hybrid -Site -"US Only" -"No Visa" -"Citizens Only" -"Security Clearance" -"site" -"Local Only" -"Must be located" -"based"
```

O modelo gringo também deve considerar sinais como `remote`, `LATAM`, `Brazil`, `hiring`, `looking for`, `open role` etc. 

---

# Cenário 2 — Vaga BR: Posts do LinkedIn

Quando o objetivo for Brasil, muda o conjunto de termos de contratação.

Modelo:

```text
site:linkedin.com/posts ("vaga" OR "contratando" OR "contrata" OR "procura" OR "procurando" OR "oportunidade") AND "[KEYWORD 1]" AND "[KEYWORD 2]" AND ("remoto" OR "remota") -"hibrido" -"presencial"
```

Exemplo:

```text
site:linkedin.com/posts ("vaga" OR "contratando" OR "contrata" OR "procura" OR "procurando" OR "oportunidade") AND ("Java" OR "Java Backend") AND "Spring Boot" AND "AWS" AND ("remoto" OR "remota") -"hibrido" -"presencial"
```



---

# Cenário 3 — Vagas formais do LinkedIn

**Sempre é a segunda query.**

Modelo:

```text
site:linkedin.com/jobs "[KEYWORD 1]" AND "[KEYWORD 2]" AND ("Remote" OR "LATAM" OR "Remote Latin America" OR "Brazil" OR "Brasil")
```

Exemplo:

```text
site:linkedin.com/jobs ("Ruby on Rails" OR "Rails") AND "React" AND "PostgreSQL" AND ("Remote" OR "LATAM" OR "Remote Latin America" OR "Brazil" OR "Brasil")
```

A regra é importante: **usar o mesmo Top 3** da query de posts. Não trocar as skills para criar uma segunda combinação. 

---
