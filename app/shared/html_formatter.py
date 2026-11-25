import re

from bs4 import BeautifulSoup, Tag


def html_to_markdown(raw_html: str) -> str:
    """Converte HTML de descrição de vaga em Markdown legível preservando títulos e listas."""
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    for heading_level in ("h1", "h2", "h3", "h4"):
        for heading in soup.find_all(heading_level):
            text = heading.get_text(" ", strip=True)
            if text:
                heading.replace_with(f"\n\n## {text}\n")

    for bold_tag in soup.find_all(["strong", "b"]):
        text = bold_tag.get_text(" ", strip=True)
        if text:
            bold_tag.replace_with(f"**{text}**")

    for li_tag in soup.find_all("li"):
        if isinstance(li_tag, Tag):
            text = li_tag.get_text(" ", strip=True)
            if text:
                li_tag.replace_with(f"\n- {text}")

    for br_tag in soup.find_all("br"):
        br_tag.replace_with("\n")

    for block_tag in soup.find_all(["p", "div", "section", "ul", "ol"]):
        block_tag.insert_before("\n")
        block_tag.insert_after("\n")

    raw_text = soup.get_text()
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw_text.splitlines()]
    joined = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", joined).strip()
