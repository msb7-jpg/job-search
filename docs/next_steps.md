
# proxies endpoints to support

# via scrapping
https://spys.one/en/https-ssl-proxy/

# via api
https://proxylist.geonode.com/api/proxy-list?page=1&limit=500&sort_by=responseTime&sort_type=asc

# via github raw
https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt

# via github raw
https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt


Engenharia de Ingestão de Proxies Públicos Gratuitos via APIs e Redes EstruturadasA integração automatizada de proxies públicos gratuitos constitui um componente crítico em arquiteturas de recolha de dados distribuída, análise competitiva de mercado e auditoria de sistemas de entrega de conteúdos. No entanto, a efemeridade intrínseca dos nós abertos — cuja disponibilidade operacional oscila com frequência entre poucos minutos e raras horas — transforma a tarefa de ingestão num desafio complexo de engenharia de software. A transição de métodos legados de raspagem direta em tabelas HTML para o consumo de interfaces de programação de aplicações (APIs) estruturadas e redes de entrega contínua baseadas em GitOps representa um salto qualitativo indispensável para conferir estabilidade a pipelines de extração.A construção de coletores resilientes exige o mapeamento minucioso dos vetores de distribuição contemporâneos, a identificação dos requisitos de transporte impostos por firewalls periféricas e a conceção de rotinas tipadas capazes de transformar cargas heterogéneas em estruturas padronizadas de endereçamento.Panorama Arquitetural e Vetores de DistribuiçãoA infraestrutura global de fornecimento de proxies abertos sofreu uma profunda mutação motivada pela saturação de tráfego e pela evolução dos mecanismos de proteção contra negação de serviço. Historicamente, o ecossistema assentava em servidores de aplicação monolíticos que consultavam bases de dados relacionais para servir pedidos HTTP em tempo real. Essa configuração demonstrou uma vulnerabilidade extrema perante a proliferação massiva de scripts automatizados, conduzindo à instabilidade severa ou ao encerramento prático de endpoints outrora consolidados, exemplificado pelas falhas crónicas de gateway (HTTP 502) observadas no proxy-list.download e pelas falhas de conectividade de origem via Cloudflare (HTTP 521) reportadas no openproxy.space.Em contrapartida, a arquitetura moderna de agregação de proxies convergiu para dois modelos dominantes de elevada sustentabilidade. O primeiro modelo baseia-se em APIs públicas empresariais, fornecidas por empresas de extração de dados como a ProxyScrape e a GeoNode. Estas organizações mantêm frotas de agentes distribuídos que sondam continuamente milhares de endereços para alimentar as suas redes comerciais, segregando uma fração dessa infraestrutura para exposição pública gratuita como ferramenta de captação e diagnóstico. O segundo modelo decorre do ecossistema GitOps de código aberto, onde tarefas automatizadas (primordialmente executadas via GitHub Actions) operam pipelines contínuos de varredura, validação com o serviço httpbin.org e publicação direta dos resultados em repositórios abertos. A entrega desses ficheiros estáticos através de redes de difusão de conteúdo como o jsDelivr ou o domínio raw.githubusercontent.com elimina gargalos computacionais e remove restrições severas de quota por endereço IP.A distribuição temporal de sobrevivência dos proxies públicos reflete uma acentuada curva de decaimento exponencial, na qual a taxa de latência média degrada drasticamente à medida que os nós são descobertos e saturados por múltiplos clientes concorrentes. Essa volatilidade reforça a necessidade de consumir preferencialmente fontes que incorporem rotinas internas de validação por lote com cadência horária ou semi-horária, reduzindo a ingestão de nós inoperantes antes mesmo da execução de diagnósticos locais.Fornecedor / OrigemArquitetura de EntregaProtocolos SuportadosFrequência de AtualizaçãoAutenticação / Cabeçalhos CríticosMecanismo de Paginação e VolumeProxyScrape v4[cite: 5, 9]API RESTful (JSON / TXT)HTTP, SOCKS4, SOCKS51 a 15 minutosAberto; sem chave para tier públicoSuporta parâmetros limit (máx. 2000) e skip[cite: 9]GeoNode[cite: 5]API RESTful (JSON)HTTP, HTTPS, SOCKS4, SOCKS5Contínua em tempo realObrigatório User-Agent de navegadorPaginação obrigatória por page e limit[cite: 13, 14]Proxifly[cite: 5, 12]Edge CDN / GitHub RawHTTP, HTTPS, SOCKS4, SOCKS55 minutosTotalmente aberto nos endpoints CDN/RawFicheiro plano unificado sem paginaçãomonosans/proxy-list[cite: 4]Repositório Git / CDNHTTP, SOCKS4, SOCKS560 minutosTotalmente abertoFicheiros completos ordenados por menor latênciaTheSpeedX/PROXY-List[cite: 15]Repositório Git / RawHTTP, SOCKS4, SOCKS5Diária / FrequenteTotalmente abertoGrande volume em ficheiros de texto segregadosSpys.me[cite: 16]Servidor Web / TXTHTTP, HTTPS, SOCKS4, SOCKS5DiáriaAberto; exige expurgo de metadados inlineFicheiro de texto contínuo delimitado por espaçosOpenProxyList[cite: 8, 18]Servidor Dedicado / TXTHTTP, SOCKS4, SOCKS5ContínuaTotalmente abertoEndpoints dedicados por protocoloiplocate/free-proxy-list[cite: 5]Repositório Git / RawHTTP, HTTPS, SOCKS4, SOCKS530 minutosTotalmente abertoListas estáticas segregadas por diretoriaEspecificação Técnica dos Endpoints e Protocolos de ConsultaProxyScrape (Versão 4)O endpoint de quarta geração da ProxyScrape opera em https://api.proxyscrape.com/v4/free-proxy-list/get e consolida a principal referência de API pública direta com parametrização abrangente. Ao contrário das versões legadas que dependiam de rotas descontinuadas, a versão 4 permite selecionar o comportamento de consumo através do parâmetro request, aceitando displayproxies para devolução direta dos nós no corpo da resposta.Os parâmetros de filtragem aceitam valores estritos: protocol admite combinações separadas por vírgula (http, socks4, socks5 ou all), proxy_format controla a presença de esquema via ipport ou protocolipport, e format alterna entre o formato JSON enriquecido e o formato textual plano de uma linha por nó. O parâmetro limit possui um teto máximo de 2000 registos por requisição, o qual pode ser complementado pelo parâmetro skip para fins de paginação sequencial sobre pools mais alargados.GeoNodeO serviço disponibilizado pela GeoNode em https://proxylist.geonode.com/api/proxy-list destaca-se pela devolução de dados em JSON estruturado com atributos operacionais detalhados, tais como tempo de resposta medido em milissegundos, taxa histórica de atividade (upTime) e grau de anonimato. O consumo deste serviço impõe a parametrização explícita de limit (frequentemente fixado em patamares até 500 registos) e page (iniciado em 1), ordenados tipicamente por lastChecked com direção descendente para maximizar a probabilidade de conectividade imediata.Um fator crítico na ingestão via GeoNode reside na presença de um sistema de proteção de perímetro configurado para barrar requisições originadas por bibliotecas de programação que utilizem identificadores de agente padrão. O envio de chamadas sem a substituição explícita do cabeçalho User-Agent por uma cadeia de caracteres equivalente a um navegador web moderno resulta invariavelmente no código de terminação HTTP 403 Forbidden.ProxiflyO projeto Proxifly disponibiliza atualizações completas com intervalo de 5 minutos, garantindo que os nós retidos tenham passado por baterias recentes de testes de ligação. Embora a empresa comercialize uma API de rotação transacional e ofereça uma chamada REST em api.proxifly.dev/get-proxy que devolve nós individualmente, a totalidade do catálogo ativo é sincronizada com repositórios públicos e distribuída via rede jsDelivr.O endpoint https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt e os seus correspondentes segmentados por protocolo fornecem listas brutas no formato canónico de endereço IP e porta, permitindo a leitura e a integração direta sem necessidade de paginação ou descodificação de objetos complexos.Redes de Repositórios GitOps: Monosans, TheSpeedX e iplocateA distribuição via repositórios abertos converteu-se no canal mais fiável contra indisponibilidade de serviços:
O ecossistema monosans/proxy-list disponibiliza dados revalidados a cada hora a partir de ferramentas de varredura executadas em nós dedicados. A lista unificada proxies/all.txt fornece os nós já prefixados com os esquemas protocolares correspondentes, organizados de forma estrita com os nós de resposta mais veloz no topo do ficheiro. Ficheiros dedicados como proxies/http.txt e proxies/socks5.txt fornecem os nós sem prefixo para integração imediata em clientes que assumem o protocolo por configuração.O repositório TheSpeedX/PROXY-List foca-se no volume bruto, agregando milhares de endereços capturados em fontes públicas globais. Os dados são acessíveis em caminhos estáticos como master/http.txt, master/socks4.txt e master/socks5.txt. Devido ao volume massivo e ao ciclo de atualização geralmente diário, esta fonte contém uma proporção mais elevada de nós inativos, sendo ideal para popular bancos de triagem secundária.O projeto iplocate/free-proxy-list adota um ciclo de atualização semi-horário com validação ativa via automação. O acesso aos ficheiros protocols/http.txt e protocols/socks5.txt assegura um compromisso equilibrado entre volume e disponibilidade funcional, apresentando índices consistentemente elevados de sucesso em requisições seguras.Agregadores com Metadados Inline: Spys.me e OpenProxyListO servidor Spys.me mantém uma das mais antigas e consistentes listas textuais da Internet, dividida entre https://spys.me/proxy.txt para proxies web e https://spys.me/socks.txt para protocolos SOCKS. O formato retornado não é puramente composto por linhas de rede; o documento inclui cabeçalhos analíticos e etiquetas de auditoria estruturadas (como código do país, indicadores de anonimato e validação Google) agregadas na mesma linha após um espaço delimitador. A ingestão requer a aplicação de expressões regulares para isolar o segmento correspondente ao endereço e porto.Por sua vez, o serviço OpenProxyList fornece endpoints simplificados de texto puro no domínio api.openproxylist.xyz, disponibilizando rotas como /http.txt, /socks4.txt e /socks5.txt que devolvem diretamente listas limpas de soquetes, amplamente empregues em testes rápidos de infraestrutura distribuída.Implicações de Segurança, Integridade de Tráfego e Validação AtivaO encaminhamento de comunicações de rede através de proxies públicos gratuitos impõe ameaças de integridade que exigem salvaguardas rigorosas no cliente consumidor. Qualquer entidade que opere um proxy aberto possui visibilidade completa sobre pacotes transmitidos em texto claro, o que possibilita a interceção de tráfego HTTP desprovido de camada de transporte cifrada, a leitura não autorizada de cabeçalhos de autenticação e a injeção ativa de scripts maliciosos nas respostas devolvidas pelo servidor de destino.Por conseguinte, a utilização de proxies públicos deve ser estritamente circunscrita a tráfego cifrado via TLS (HTTPS) com recurso ao método de tunelamento CONNECT, ou através de túneis SOCKS5 com resolução de nomes remota. Nestes cenários, o intermediário atua unicamente como um retransmissor cego de fluxo TCP, ficando impedido de violar a privacidade da carga útil sem desencadear exceções de validação de certificados no cliente.Adicionalmente, existe o fenómeno de nós modificadores de saída ou proxies com discrepância de rede, nos quais o tráfego é reencaminhado por redes internas não confiáveis ou sistemas autónomos (ASNs) suspeitos, expondo o cliente a bloqueios por listas de reputação adversa. Uma estratégia sólida de validação em produção requer a execução prévia de testes de rotação contra serviços externos de confirmação de IP, atestando se o endereço de saída apurado coincide de facto com o endereço do intermediário registado, ao mesmo tempo que se quantifica a latência real de transporte.Implementação Modular em Python com Tipagem EstritaO bloco programático apresentado a seguir concretiza as interfaces de ingestão para cada uma das oito fontes consolidadas. A arquitetura foi concebida para utilizar estritamente a biblioteca padrão do ecossistema Python moderno (urllib.request), garantindo compatibilidade e dispensando dependências externas. Todas as funções contam com tipagem estática rigorosa através de typing, expondo assinaturas padronizadas cujo retorno converge exclusivamente para listas de cadeias de caracteres (list[str]).Python"""
Módulo de extração e normalização de proxies públicos gratuitos.
Implementa rotinas estanques e tipadas que retornam coleções estruturadas no tipo list[str].
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Final

# Definição de cabeçalho global simulando navegador para prevenir respostas HTTP 403
USER_AGENT_HEADER: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
SOCKET_TIMEOUT_SECONDS: Final[int] = 15

# Expressão regular para validação e extração do padrão IPv4:Porta
IPV4_SOCKET_REGEX: Final[re.Pattern[str]] = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?):\d{2,5}\b"
)


def _http_get_payload(url: str, custom_headers: dict[str, str] | None = None) -> str:
    """
    Executa uma requisição HTTP GET segura, retornando o corpo decodificado.
    Trata internamente exceções de transporte, devolvendo cadeia vazia em falhas.
    """
    headers = {"User-Agent": USER_AGENT_HEADER}
    if custom_headers:
        headers.update(custom_headers)

    request_spec = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request_spec, timeout=SOCKET_TIMEOUT_SECONDS) as response:
            encoding = response.headers.get_content_charset() or "utf-8"
            raw_data: bytes = response.read()
            return raw_data.decode(encoding, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return ""


def get_proxyscrape_proxies(
    protocol: str = "all",
    proxy_format: str = "protocolipport",
    limit: int = 2000,
) -> list[str]:
    """
    Consome a API ProxyScrape v4 e retorna a lista de proxies ativos.
    
    :param protocol: Protocolo pretendido ('http', 'socks4', 'socks5' ou 'all').
    :param proxy_format: Formatação de saída ('ipport' ou 'protocolipport').
    :param limit: Limite numérico de registos a obter (máximo suportado: 2000).
    :return: Lista de proxies normalizados.
    """
    endpoint = "https://api.proxyscrape.com/v4/free-proxy-list/get"
    query_parameters = {
        "request": "display_proxies",
        "protocol": protocol,
        "proxy_format": proxy_format,
        "format": "text",
        "limit": str(min(limit, 2000)),
        "timeout": "10000",
    }
    query_string = urllib.parse.urlencode(query_parameters)
    payload = _http_get_payload(f"{endpoint}?{query_string}")

    proxies: list[str] = []
    for line in payload.splitlines():
        sanitized = line.strip()
        if sanitized:
            proxies.append(sanitized)
    return proxies


def get_geonode_proxies(
    protocols: str = "http,https,socks4,socks5",
    max_pages: int = 3,
    limit_per_page: int = 100,
) -> list[str]:
    """
    Consome a API paginada da GeoNode, retornando endereços prefixados pelo protocolo.
    Aplica cabeçalhos defensivos para evitar a rejeição por código HTTP 403.
    
    :param protocols: Relação de protocolos separados por vírgula.
    :param max_pages: Quantidade de páginas a percorrer no processo de ingestão.
    :param limit_per_page: Volume de registos solicitados por chamada (limite: 500).
    :return: Lista de nós formatados como 'protocol://ip:porta'.
    """
    base_endpoint = "https://proxylist.geonode.com/api/proxy-list"
    request_headers = {
        "User-Agent": USER_AGENT_HEADER,
        "Accept": "application/json",
        "Referer": "https://proxylist.geonode.com/",
    }
    extracted_proxies: list[str] = []

    for current_page in range(1, max_pages + 1):
        query_parameters = {
            "limit": str(min(limit_per_page, 500)),
            "page": str(current_page),
            "sort_by": "lastChecked",
            "sort_type": "desc",
            "protocols": protocols,
        }
        url = f"{base_endpoint}?{urllib.parse.urlencode(query_parameters)}"
        raw_json = _http_get_payload(url, custom_headers=request_headers)
        if not raw_json:
            break

        try:
            document = json.loads(raw_json)
            records = document.get("data", [])
            if not records:
                break

            for entry in records:
                ip = entry.get("ip")
                port = entry.get("port")
                assigned_protocols: list[str] = entry.get("protocols", [])
                primary_protocol = assigned_protocols[0] if assigned_protocols else "http"
                if ip and port:
                    extracted_proxies.append(f"{primary_protocol}://{ip}:{port}")
        except json.JSONDecodeError:
            break

    return extracted_proxies


def get_proxifly_proxies(protocol: str = "all") -> list[str]:
    """
    Descarrega a relação completa de proxies da Proxifly através da CDN jsDelivr.
    
    :param protocol: Protocolo desejado ('all', 'http', 'socks4' ou 'socks5').
    :return: Lista de proxies no formato 'ip:porta'.
    """
    if protocol == "all":
        target_url = (
            "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt"
        )
    else:
        target_url = (
            f"https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/"
            f"proxies/protocols/{protocol.lower()}/data.txt"
        )

    response_text = _http_get_payload(target_url)
    proxies: list[str] = []
    for line in response_text.splitlines():
        cleaned_line = line.strip()
        if cleaned_line and not cleaned_line.startswith("#"):
            proxies.append(cleaned_line)
    return proxies


def get_monosans_proxies(protocol: str = "all") -> list[str]:
    """
    Recolhe proxies verificados a cada hora pelo repositório monosans/proxy-list.
    
    :param protocol: Filtro selecionado ('all', 'http', 'socks4' ou 'socks5').
    :return: Lista de endereços ordenados pela menor latência.
    """
    if protocol == "all":
        target_url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt"
    else:
        target_url = (
            f"https://raw.githubusercontent.com/monosans/proxy-list/main/"
            f"proxies/{protocol.lower()}.txt"
        )

    response_text = _http_get_payload(target_url)
    proxies: list[str] = []
    for line in response_text.splitlines():
        cleaned_line = line.strip()
        if cleaned_line:
            proxies.append(cleaned_line)
    return proxies


def get_thespeedx_proxies(protocol: str = "http") -> list[str]:
    """
    Consome os ficheiros de grande volume do repositório TheSpeedX/PROXY-List.
    
    :param protocol: 'http', 'socks4' ou 'socks5'.
    :return: Lista de proxies no formato 'ip:porta'.
    """
    normalized_protocol = protocol.lower().strip()
    target_url = (
        f"https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/"
        f"{normalized_protocol}.txt"
    )

    response_text = _http_get_payload(target_url)
    proxies: list[str] = []
    for line in response_text.splitlines():
        cleaned_line = line.strip()
        if cleaned_line:
            proxies.append(cleaned_line)
    return proxies


def get_spys_me_proxies(proxy_type: str = "http") -> list[str]:
    """
    Extrai nós disponibilizados pela Spys.me, expurgando cabeçalhos e metadados inline.
    
    :param proxy_type: 'http' para proxies web ou 'socks' para proxies SOCKS.
    :return: Lista filtrada de sockets no formato 'ip:porta'.
    """
    resource_file = "proxy.txt" if proxy_type.lower() == "http" else "socks.txt"
    target_url = f"https://spys.me/{resource_file}"

    response_text = _http_get_payload(target_url)
    proxies: list[str] = []
    for line in response_text.splitlines():
        match = IPV4_SOCKET_REGEX.search(line)
        if match:
            proxies.append(match.group(0))
    return proxies


def get_openproxylist_proxies(protocol: str = "http") -> list[str]:
    """
    Consulta as listas segmentadas mantidas pelo serviço api.openproxylist.xyz.
    
    :param protocol: Protocolo desejado ('http', 'socks4' ou 'socks5').
    :return: Lista de proxies no formato 'ip:porta'.
    """
    normalized_protocol = protocol.lower().strip()
    target_url = f"https://api.openproxylist.xyz/{normalized_protocol}.txt"

    response_text = _http_get_payload(target_url)
    proxies: list[str] = []
    for line in response_text.splitlines():
        cleaned_line = line.strip()
        if cleaned_line:
            proxies.append(cleaned_line)
    return proxies


def get_iplocate_proxies(protocol: str = "http") -> list[str]:
    """
    Ingere artefactos gerados a cada 30 minutos pelo projeto iplocate/free-proxy-list.
    
    :param protocol: Protocolo escolhido ('http', 'https', 'socks4' ou 'socks5').
    :return: Lista de proxies normalizados como 'ip:porta'.
    """
    normalized_protocol = protocol.lower().strip()
    target_url = (
        f"https://raw.githubusercontent.com/iplocate/free-proxy-list/main/"
        f"protocols/{normalized_protocol}.txt"
    )

    response_text = _http_get_payload(target_url)
    proxies: list[str] = []
    for line in response_text.splitlines():
        cleaned_line = line.strip()
        if cleaned_line:
            proxies.append(cleaned_line)
    return proxies


class UnifiedProxyCollector:
    """
    Coletor agregado concebido para consolidar, desduplicar e normalizar
    o catálogo de múltiplos ecossistemas numa lista única.
    """

    @classmethod
    def fetch_all(cls) -> list[str]:
        """
        Executa a recolha estruturada sobre todas as fontes implementadas,
        aplicando desduplicação através de conjuntos em memória.
        """
        aggregated_pool: set[str] = set()

        aggregated_pool.update(get_proxyscrape_proxies(protocol="all"))
        aggregated_pool.update(get_geonode_proxies(max_pages=2, limit_per_page=100))
        aggregated_pool.update(get_proxifly_proxies(protocol="all"))
        aggregated_pool.update(get_monosans_proxies(protocol="all"))
        aggregated_pool.update(get_thespeedx_proxies(protocol="http"))
        aggregated_pool.update(get_spys_me_proxies(proxy_type="http"))
        aggregated_pool.update(get_openproxylist_proxies(protocol="http"))
        aggregated_pool.update(get_iplocate_proxies(protocol="http"))

        return sorted(aggregated_pool)


if __name__ == "__main__":
    sample_proxyscrape = get_proxyscrape_proxies(limit=5)
    sample_geonode = get_geonode_proxies(max_pages=1, limit_per_page=5)
    total_distinct = UnifiedProxyCollector.fetch_all()

    print(f"ProxyScrape retornou {len(sample_proxyscrape)} entradas de teste.")
    print(f"GeoNode retornou {len(sample_geonode)} entradas de teste.")
    print(f"Total agregado consolidado de proxies únicos: {len(total_distinct)}")

Padrões Arquiteturais para Sistemas de Elevada Disponibilidade

A transposição das rotinas de ingestão de proxies para ambientes de produção contínua requer a dissociação estrita entre o ciclo de recolha dos endereços e o ciclo de consumo operacional pelas aplicações de negócio. Nenhum serviço crítico deve acionar requisições a APIs externas de proxies em momentos de execução transacional, sob pena de transferir latências de rede e indisponibilidades periféricas para o fluxo de entrega final. A arquitetura de referência pressupõe a implementação de processos em segundo plano dedicados exclusivamente à recolha periódica, responsáveis por depositar os nós num armazenamento volátil de acesso imediato, como uma base de dados em memória do tipo Redis.Sobre esse reservatório em memória, deve operar um componente assíncrono de triagem e teste de integridade (health-checking). Utilizando bibliotecas não bloqueantes de rede, este validador submete os nós a requisições de teste com temporizadores agressivos (com janelas de terminação inferiores a 2 ou 3 segundos) direcionadas para endpoints de diagnóstico controlados ou para as próprias APIs de destino da organização. Os nós que falham na resposta, apresentam tempos de retorno proibitivos ou adulteram cabeçalhos são imediatamente removidos do pool de nós viáveis.Por fim, a camada de consumo deve empregar estratégias determinísticas de rotação, alternando entre algoritmos ponderados pela menor latência histórica e modelos circulares baseados em round-robin. Esta lógica de distribuição necessita de estar acoplada a disjuntores de circuito (circuit breakers): caso um proxy previamente validado venha a falhar consecutivamente durante a sessão operacional de uma tarefa de extração, o subsistema deve marcá-lo como indisponível e redirecionar imediatamente o fluxo para outro endereço ativo, mantendo a integridade do pipeline sem intervenção manual.