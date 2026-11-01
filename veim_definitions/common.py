"""What recipes share: the session they read pages with, and the helpers that
read a release listing, a table, a checksum list or a release feed.

The contract itself - DistroRecipe, DownloadInfo, FlavorInfo, ScrapeError and
the version helpers - belongs to VEIM (src/core/recipe_base.py) and is
re-exported here, so a recipe imports everything it needs from this module.
Everything else lives here, so that a mirror that starts refusing VEIM's
User-Agent is fixed with a definitions update rather than a VEIM release.
"""
from html.parser import HTMLParser
from typing import List
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core import recipe_base
from src.core.recipe_base import (  # noqa: F401 - re-exported for recipes
    DownloadInfo, FlavorInfo, IsoIdentity, ScrapeError, clean_version, is_older, version_key)
from src.core.logger import log

# A server error is a hiccup, not an answer. Two more tries, a second or two
# apart, cover the kind cdimage.debian.org has; then it is refused.
SERVER_ERROR_STATUSES = (500, 502, 503, 504)
SERVER_ERROR_RETRIES = 2
SERVER_ERROR_BACKOFF = 1.0

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"

# The path of each file a SourceForge RSS feed lists, newest first.
SOURCEFORGE_PATHS = r'<title><!\[CDATA\[(/[^\]]+)\]\]></title>'


def _refuse_server_errors(response, *args, **kwargs):
    """Session hook: a 5xx that survived the retries is raised, never parsed.

    The body of an error page holds no download links, and a recipe that
    searched it reported "no current release" for a release that was there.
    """
    if response.status_code >= 500:
        raise requests.HTTPError(
            f"{response.url.split('//', 1)[-1].split('/', 1)[0]} answered "
            f"HTTP {response.status_code}", response=response)
    return response


class _Page(HTMLParser):
    """The href of every link on a page, and the text in each table row's cells."""

    def __init__(self):
        super().__init__()
        self.hrefs, self.rows, self._in_cell = [], [], False

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href")
        if tag == "a" and href is not None:
            self.hrefs.append(href)
        elif tag == "tr":
            self.rows.append([])
            self._in_cell = False
        elif tag == "td" and self.rows:
            self.rows[-1].append("")
            self._in_cell = True

    def handle_endtag(self, tag):
        if tag in ("td", "tr"):
            self._in_cell = False

    def handle_data(self, data):
        if self._in_cell:
            self.rows[-1][-1] += data


def _parse(html: str) -> _Page:
    page = _Page()
    page.feed(html)
    page.close()
    return page


def hrefs(html: str) -> List[str]:
    """Every link's href, in page order, with entities decoded."""
    return _parse(html).hrefs


def table_rows(html: str) -> List[List[str]]:
    """The stripped text of each table row's cells."""
    return [[cell.strip() for cell in row] for row in _parse(html).rows]


def sourceforge_rss(session, project: str, query: str) -> str:
    """A SourceForge project's RSS feed of its newest files, newest first."""
    r = session.get(f"https://sourceforge.net/projects/{project}/rss?{query}",
                    timeout=25, headers={"User-Agent": "curl/8.4.0"})
    r.raise_for_status()
    return r.text


def sha256_in(sums: str, filename: str) -> str:
    """The SHA-256 a checksum list gives `filename`, or "".

    Lists name the file bare, with a "*", or under a folder ("./name",
    "v8.10/name"), in the GNU layout ("<hash>  name") or the BSD one
    ("SHA256 (name) = <hash>"). A file that holds a single hash and nothing
    else is that hash. Only 64 hex digits count, so a SHA-512 beside it in
    the same list is never taken for it.
    """
    name = r'(?:\S*/)?' + re.escape(filename)
    m = re.search(rf'(?m)^(?:([0-9a-fA-F]{{64}})[ \t]+\*?{name}|SHA256 \({name}\) ?= ?([0-9a-fA-F]{{64}}))\s*$',
                  sums)
    if not m:
        m = re.fullmatch(r'\s*([0-9a-fA-F]{64})\s*', sums)
    return next(g for g in m.groups() if g).lower() if m else ""


def published_sha256(session, url: str, filename: str, who: str, headers: dict = None) -> str:
    """The SHA-256 the checksum file at `url` gives `filename`.

    "" when that cannot be had - unreadable, not a 200, or not naming the
    file. The release is known either way; only the check after download is
    lost, so a checksum is never a reason to refuse one.
    """
    try:
        r = session.get(url, timeout=20, headers=headers)
        if r.status_code != 200:
            raise requests.HTTPError(f"HTTP {r.status_code}")
    except Exception as e:
        log.warning(f"[{who}] No checksum for {filename} at {url}: {e}")
        return ""
    sha256 = sha256_in(r.text, filename)
    if not sha256:
        log.warning(f"[{who}] {url} gives no SHA-256 for {filename}")
    return sha256


class DistroRecipe(recipe_base.DistroRecipe):
    """The contract's recipe, with the means to read release pages."""

    def get_session(self) -> requests.Session:
        """A session for reading release pages.

        A server error is retried, then refused: cdimage.debian.org answers
        500 for a request or two at a time, and a recipe that parsed the
        error page as a listing reported "no current release" for a release
        that was there. A 4xx still comes back as a response - a 404 is an
        answer several recipes read ("that release has no images yet").
        """
        session = requests.Session()
        session.headers.update({
            "User-Agent": BROWSER_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.7",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1"
        })
        adapter = HTTPAdapter(max_retries=Retry(
            total=SERVER_ERROR_RETRIES, status_forcelist=SERVER_ERROR_STATUSES,
            allowed_methods=("GET", "HEAD"), backoff_factor=SERVER_ERROR_BACKOFF,
            raise_on_status=False))
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.hooks["response"].append(_refuse_server_errors)
        return session

    def github_latest(self, repo: str):
        """(tag, assets) of a GitHub project's latest release."""
        try:
            r = self.get_session().get(f"https://api.github.com/repos/{repo}/releases/latest", timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log.warning(f"[{self.name}] GitHub API error: {e}")
            raise ScrapeError(self.name, f"could not read the {self.name} release feed ({e})")
        return str(data.get("tag_name", "")), data.get("assets", [])
