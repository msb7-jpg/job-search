
class Gringas:
    POSTS_FS = (
        'site:linkedin.com/posts/ "hiring" and ("vue" or "react") and "python" and "remote" '
        '-pleno -pl -senior -sr -ssr -staff -lead -principal -architect -staff '
        '-lead -c2c -"us based" -hybrid -site -"us only" -"no visa" '
        '-"citizens only" -"security clearance" -"on-site" -"local only" '
        '-"must be located"'
    )

    POSTS_BE = (
        'site:linkedin.com/posts/ "hiring" AND "Python" AND "remote" '
        '-Pleno -PL -Senior -Sr -SSR -Staff -Lead -Principal -Architect '
        '-Staff -Lead -C2C -"US Based" -Hybrid -Site -"US Only" '
        '-"No Visa" -"Citizens Only" -"Security Clearance" '
        '-"On-site" -"Local Only" -"Must be located"'
    )

    JOBS_FS = (
        '"Python" AND "Vue" ("Full" OR "Fullstack")  AND NOT ("Pleno" OR "PL" OR "Senior" OR "Sr" OR "SSR" OR "Staff" OR "Lead" OR "Principal" OR "Architect")'
    )

    JOBS_BE = (
        '"Python" ("Back" OR "Backend")  AND NOT ("Pleno" OR "PL" OR "Senior" OR "Sr" OR "SSR" OR "Staff" OR "Lead" OR "Principal" OR "Architect")'
    )


class Nacionais:
    POSTS_FS = (
        'site:linkedin.com/posts/ "vaga" AND "Python" AND "Vue" AND ("Full" OR "Fullstack") AND ("remoto" OR "remota") -Pleno -PL -Senior -Sr -SSR -Staff -Lead -Principal -Architect'
    )

    POSTS_BE = (
        'site:linkedin.com/posts/ "vaga" "vaga" AND "Python" AND ("Back" OR "Backend") AND ("remoto" OR "remota") -Pleno -PL -Senior -Sr -SSR -Staff -Lead -Principal -Architect'
    )
