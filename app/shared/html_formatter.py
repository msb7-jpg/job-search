import re

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString

_HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
_BLOCK_TAGS = (
    "p",
    "div",
    "section",
    "article",
    "blockquote",
    "header",
    "footer",
    "dt",
    "dd",
    "tr",
    "ul",
    "ol",
)


def _needs_trailing_space(tag: Tag) -> bool:
    """Retorna True se o próximo irmão imediato começa com caractere alfanumérico sem espaço."""
    next_node = tag.next_sibling
    if next_node is None:
        return False
    next_text = next_node.get_text() if isinstance(next_node, Tag) else str(next_node)
    return bool(next_text) and next_text[0].isalnum()


def _collapse_list_gaps(text: str) -> str:
    """Remove linhas em branco extras entre itens consecutivos de lista Markdown."""
    lines = text.splitlines()
    compacted: list[str] = []
    for index, line in enumerate(lines):
        is_blank = line == ""
        prev_is_bullet = bool(compacted) and compacted[-1].startswith("- ")
        next_is_bullet = index + 1 < len(lines) and lines[index + 1].startswith("- ")
        if is_blank and prev_is_bullet and next_is_bullet:
            continue
        compacted.append(line)
    return "\n".join(compacted)


def _replace_headings_and_bold(soup: BeautifulSoup) -> None:
    """Converte cabeçalhos h1-h6 e tags strong/b preservando separação de palavras."""
    for heading in soup.find_all(list(_HEADING_TAGS)):
        text = heading.get_text(" ", strip=True)
        if text:
            heading.replace_with(NavigableString(f"\n\n## {text}\n"))

    for bold_tag in soup.find_all(["strong", "b"]):
        text = bold_tag.get_text(" ", strip=True)
        if text:
            suffix = " " if _needs_trailing_space(bold_tag) else ""
            bold_tag.replace_with(NavigableString(f"**{text}**{suffix}"))


def _replace_lists_and_blocks(soup: BeautifulSoup) -> None:
    """Converte listas, quebras de linha e blocos HTML em quebras Markdown limpas."""
    for li_tag in soup.find_all("li"):
        for nested_p in li_tag.find_all("p"):
            nested_p.unwrap()
        text = li_tag.get_text(" ", strip=True)
        if text:
            li_tag.replace_with(NavigableString(f"\n- {text}\n"))

    for br_tag in soup.find_all("br"):
        br_tag.replace_with(NavigableString("\n"))

    for block_tag in soup.find_all(list(_BLOCK_TAGS)):
        block_tag.insert_before(NavigableString("\n"))
        block_tag.insert_after(NavigableString("\n"))


def html_to_markdown(raw_html: str) -> str:
    """Converte HTML de descrição de vaga em Markdown legível preservando títulos e listas."""
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    _replace_headings_and_bold(soup)
    _replace_lists_and_blocks(soup)

    raw_text = soup.get_text()
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw_text.splitlines()]
    joined = _collapse_list_gaps("\n".join(lines))
    return re.sub(r"\n{3,}", "\n\n", joined).strip()
