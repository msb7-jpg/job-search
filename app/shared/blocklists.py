import re

PADRAO_SENIORIDADE_BLOQUEADA_TITULO = re.compile(
    r"\b(?:"
    r"senior|sênior|sr|ssr|pleno|pl|staff|lead|tech\s+lead|"
    r"líder|lider|liderança|lideranca|principal|architect|arquiteto|arqueto|"
    r"especialista|middle|mid-level|mid/senior|founding|iii|ii|"
    r"engineer\s+2|developer\s+2|desenvolvedor\s+2"
    r")\b",
    re.IGNORECASE,
)

BLOQUEADOS_RESTRICAO_VAGA = [
    "c2c",
    "us based",
    "us only",
    "no visa",
    "citizens only",
    "security clearance",
    "top secret",
    "polygraph",
    "sci access",
    "(m/w/d)",
    "(f/m/d)",
    "(m/ž)",
    "(h/f)",
]

BLOQUEADOS_LOCALIZACAO_INCOMPATIVEL = [
    "vietnã",
    "vietnam",
    "hanói",
    "hanoi",
    "ho chi minh",
    "índia",
    "india",
    "bangalore",
    "bengaluru",
    "pune",
    "hyderabad",
    "chennai",
    "madras",
    "mumbai",
    "delhi",
    "noida",
    "gurugram",
    "itanagar",
    "carnataca",
    "maharashtra",
    "telanganá",
    "tamil nadu",
    "filipinas",
    "philippines",
    "manila",
    "makati",
    "cebu",
    "nigéria",
    "nigeria",
    "paquistão",
    "pakistan",
    "bangladesh",
    "cazaquistão",
    "kazakhstan",
    "almaty",
    "sérvia",
    "serbia",
    "novi sad",
    "polônia",
    "poland",
    "varsóvia",
    "poznan",
    "croácia",
    "croatia",
    "zagreb",
    "zagrebe",
    "alemanha",
    "germany",
    "munique",
    "bona",
    "suíça",
    "lugano",
    "frança",
    "paris",
    "ilha de frança",
    "altos do sena",
    "reino unido",
    "inglaterra",
    "birmingham",
    "espanha",
    "madri",
    "barcelona",
    "cuenca",
]

BLOQUEADOS_PRESENCIAL = [
    "presencial",
    "100% presencial",
    "onsite",
    "on-site",
    "híbrido",
    "hibrido",
    "hybrid",
    "local only",
    "must be located",
]

EMPRESAS_BLOQUEADAS = [
    "micro1",
    "micro 1",
    "invisible technologies",
    "invisible tech",
    "dataannotation",
    "data annotation",
    "alignerr",
    "outlier",
    "mindrift",
    "turing",
]

BLOQUEADOS_TREINAMENTO_IA = [
    "ai trainer",
    "train ai",
    "ai training",
    "trainer",
    "training ai",
    "model training",
    "rlhf",
    "data annotat",
    "data annotation",
    "prompt engineer",
    "prompt evaluation",
    "evaluate ai",
    "evaluating ai",
    "ai tutor",
    "ai model evaluation",
    "annotation",
    "ai data annotator",
    "human data platforms",
]

PADRAO_ANOS_EXPERIENCIA_ALTA = re.compile(
    r"(?:\b([3-9]|1[0-9])\s*\+?\s*(?:anos|years)\s+(?:de\s+)?(?:experiência|experience))"
    r"|(?:\b(?:experiência|experience)\s*(?:mínima|minima|of|:\s*)?\s*([3-9]|1[0-9])\s*\+?\s*(?:anos|years))",
    re.IGNORECASE,
)

PADRAO_TITULO_FLEXIVEL_TI = re.compile(
    r"\b(?:"
    r"dev|developer|desenvolvedor(?:a)?|programador(?:a)?|"
    r"engineer|engenheiro(?:a)?|software|sistemas|systems|"
    r"full[\s\-]?stack|back[\s\-]?end|front[\s\-]?end|"
    r"ai|ia|ml|llm|machine\s+learning|dados|data|"
    r"analista|analyst|python|django|fastapi|flask|react|vue|typescript|javascript|node|"
    r"cloud|devops|sre|qa|automação|automation|tech|tecnologia|"
    r"estágio|estagio|intern|trainee|architect|arquiteto(?:a)?"
    r")\b",
    re.IGNORECASE,
)
