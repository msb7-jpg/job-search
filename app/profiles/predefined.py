from app.profiles.base import Profile, ScoringRule

SKILLS_BACKEND: dict[str, str] = {
    "python": "Python",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sql": "SQL",
    "redis": "Redis",
    "rabbitmq": "RabbitMQ",
    "celery": "Celery",
    "docker": "Docker",
    "linux": "Linux",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "pytest": "Pytest",
    "selenium": "Selenium",
    "jenkins": "Jenkins",
    "gitlab": "GitLab CI",
    "rest": "REST APIs",
    "api": "REST APIs",
    "microservices": "Microservices",
    "microsserviços": "Microservices",
    "git": "Git",
    "vertex ai": "Vertex AI",
    "langchain": "LangChain",
    "pandas": "Pandas",
}

SKILLS_FULLSTACK: dict[str, str] = {
    "python": "Python",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vue 2": "Vue.js",
    "vue 3": "Vue.js",
    "react": "React.js",
    "react.js": "React.js",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "html": "HTML/CSS",
    "css": "HTML/CSS",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "sql": "SQL",
    "redis": "Redis",
    "rabbitmq": "RabbitMQ",
    "celery": "Celery",
    "docker": "Docker",
    "jenkins": "Jenkins",
    "gitlab": "GitLab CI",
    "pytest": "Pytest",
    "jest": "Jest",
    "rest": "REST APIs",
    "api": "REST APIs",
    "aws": "AWS",
    "gcp": "GCP",
    "vertex ai": "Vertex AI",
    "langchain": "LangChain",
}

PROFILE_BACKEND = Profile(
    name="backend",
    display_name="Backend Python",
    skills_map=SKILLS_BACKEND,
    primary_skill="Python",
    regras_pontuacao=[
        ScoringRule(skills=["Python"], pontos=25),
        ScoringRule(skills=["Django", "FastAPI"], pontos=20),
        ScoringRule(skills=["PostgreSQL", "MySQL", "SQL"], pontos=15),
        ScoringRule(skills=["Docker", "AWS", "GCP", "Linux"], pontos=15),
        ScoringRule(skills=["REST APIs", "Pytest", "Git"], pontos=10),
        ScoringRule(skills=["Redis", "RabbitMQ", "Celery", "Microservices"], pontos=15),
    ],
    queries_jobs_nacionais=[
        ("Python FastAPI Django PostgreSQL", "Brazil"),
        ("Desenvolvedor Python Junior", "Brazil"),
        ("Python FastAPI Django PostgreSQL", "Brazil"),

    ],
    queries_jobs_internacionais=[
        (
            '"python" ("back" OR "backend")  AND NOT ("pleno" OR "pl" OR "senior" OR "sr" OR "ssr" OR "staff" OR "lead" OR "principal" OR "architect")',
            "Remote",
        ), # Busca Principal
        (
            '"Python" "Django" ("Back" OR "Backend")  AND NOT ("Pleno" OR "PL" OR "Senior" OR "Sr" OR "SSR" OR "Staff" OR "Lead" OR "Principal" OR "Architect")',
            "Remote",
        ), # Busca com Django
        (
            '"Python" "Django" "Flask" ("Back" OR "Backend")  AND NOT ("Pleno" OR "PL" OR "Senior" OR "Sr" OR "SSR" OR "Staff" OR "Lead" OR "Principal" OR "Architect")',
            "Remote",
        ) # Busca Avançada
    ],
    queries_posts_nacionais=[
        'site:linkedin.com/posts/ ("vaga" OR "oportunidade") "Python" ("Back" OR "Backend") ("remoto" OR "remota")',
        'site:linkedin.com/posts/ ("contrata" OR "contratando") "Python" ("Back" OR "Backend")',
        'site:linkedin.com/posts/ "vaga" "Python" "Django" ("remoto" OR "remota")',
        'site:linkedin.com/posts/ "vaga" "Python" "FastAPI" ("remoto" OR "remota")',
    ],
    queries_posts_internacionais=[
        'site:linkedin.com/posts/ ("hiring" OR "job opening" OR "we are hiring") (Python OR Django OR FastAPI) (Junior OR "Entry Level" OR Jr) (Remote OR LATAM OR Brazil)',
        'site:linkedin.com/posts/ "hiring" "Python" "LATAM"',
        'site:linkedin.com/posts/ "hiring" "Python" "Django" "remote"',
        'site:linkedin.com/posts/ "hiring" "Python" ("Back" OR "Backend") "remote"',
        'site:linkedin.com/posts/ "Python" "vaga" ("Back" OR "Backend") "Internacional"',
    ],
)

PROFILE_FULLSTACK = Profile(
    name="fullstack",
    display_name="Full-Stack Python",
    skills_map=SKILLS_FULLSTACK,
    primary_skill="Python",
    regras_pontuacao=[
        ScoringRule(skills=["Python"], pontos=25),
        ScoringRule(skills=["Django", "FastAPI"], pontos=20),
        ScoringRule(skills=["PostgreSQL", "MySQL", "SQL"], pontos=15),
        ScoringRule(skills=["Docker", "AWS", "GCP", "Linux"], pontos=15),
        ScoringRule(skills=["REST APIs", "Pytest", "Git"], pontos=10),
        ScoringRule(skills=["Vue.js", "React.js", "TypeScript", "JavaScript"], pontos=15),
    ],
    queries_jobs_nacionais=[
        ("Python Vue React PostgreSQL", "Brazil"),
        ("Desenvolvedor Python Junior", "Brazil"),
    ],
    queries_jobs_internacionais=[
        (
            '"python" and ("react" or "vue") ("full" or "fullstack")  and not ("pleno" or "pl" or "senior" or "sr" or "ssr" or "staff" or "lead" or "principal" or "architect")',
            "Remote",
        ),  # Busca Principal
        (
            '"Python" AND "Vue" "Django" ("Full" OR "Fullstack")  AND NOT ("Pleno" OR "PL" OR "Senior" OR "Sr" OR "SSR" OR "Staff" OR "Lead" OR "Principal" OR "Architect")',
            "Remote",
        ),  # Busca com Django
        (
            '"Python" AND "Vue" "Django" "Flask" ("Full" OR "Fullstack")  AND NOT ("Pleno" OR "PL" OR "Senior" OR "Sr" OR "SSR" OR "Staff" OR "Lead" OR "Principal" OR "Architect")',
            "Remote",
        ),  # Busca avançada
    ],
    queries_posts_nacionais=[
        'site:linkedin.com/posts/ ("vaga" OR "oportunidade") "Python" "Vue" ("remoto" OR "remota")',
        'site:linkedin.com/posts/ ("oportunidade" OR "vaga") "Python" ("Vue" OR "React") ("Full" OR "Fullstack")',
        'site:linkedin.com/posts/ ("contrata" OR "contratando") "Python" "Vue"',
        'site:linkedin.com/posts/ "vaga" "Python" "Vue" "Django"',
    ],
    queries_posts_internacionais=[
        'site:linkedin.com/posts/ ("hiring" OR "job opening" OR "we are hiring") (Python) (Vue OR React OR TypeScript) (Junior OR "Entry Level" OR Jr) (Remote OR LATAM OR Brazil)',
        'site:linkedin.com/posts/ "hiring" "Python" "Vue" "LATAM"',
        'site:linkedin.com/posts/ "hiring" "Python" "Vue" "Django" "remote"',
        'site:linkedin.com/posts/ "hiring" "Python" ("Vue" OR "React") ("Full" OR "Fullstack") "remote"',
    ],
)

DEFAULT_PROFILES: list[Profile] = [PROFILE_BACKEND, PROFILE_FULLSTACK]
