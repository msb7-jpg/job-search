class Nacionais:
    POSTS_BE = 'site:linkedin.com/posts/ ("vaga" OR "oportunidade" OR "contratando") (Python OR Django OR FastAPI) (Junior OR Jr OR "Entry Level") -senior -sênior -sr -pleno -pl -lead'
    POSTS_FS = 'site:linkedin.com/posts/ ("vaga" OR "oportunidade" OR "contratando") (Python) (Vue OR React OR TypeScript) (Junior OR Jr OR "Entry Level") -senior -sênior -sr -pleno -pl -lead'

class Gringas:
    POSTS_BE = 'site:linkedin.com/posts/ ("hiring" OR "job opening" OR "we are hiring") (Python OR Django OR FastAPI) (Junior OR "Entry Level" OR Jr) (Remote OR LATAM OR Brazil) -senior -sr -lead -principal'
    POSTS_FS = 'site:linkedin.com/posts/ ("hiring" OR "job opening" OR "we are hiring") (Python) (Vue OR React OR TypeScript) (Junior OR "Entry Level" OR Jr) (Remote OR LATAM OR Brazil) -senior -sr -lead -principal'
