"""Page parsing and checksum lists: the helpers recipes share."""
import pytest

import requests

from veim_definitions.common import hrefs, published_sha256, sha256_in, table_rows
from tests.freshness import Resp, StrictSession

ISO = "distro-1.2-x86_64.iso"
H = "ab" * 32


def test_hrefs_are_every_link_target_decoded():
    page = '<a href="../">..</a><a name="top"></a><A HREF="a&amp;b.iso"/><link href="x.css">'
    assert hrefs(page) == ["../", "a&b.iso"]


def test_table_rows_are_the_text_of_each_cell():
    """The shape of linuxmint.com's release table: the version is a row's first cell."""
    page = ('<table><tr><th>Version</th></tr>'
            '<tr><td rowspan="3">22.3</td><td><a href="edition.php?id=326">Cinnamon </a></td></tr>'
            '<tr><td><a href="edition.php?id=328">MATE </a></td></tr></table><p>22.2</p>')
    assert table_rows(page) == [[], ["22.3", "Cinnamon"], ["MATE"]]


@pytest.mark.parametrize("sums", [
    f"{H}  {ISO}\n",                                      # GNU
    f"{H} *{ISO}\n",                                      # GNU, binary mode
    f"{H}  ./{ISO}\n",                                    # find . | sha256sum
    f"{H}  v1.2/{ISO}\n",                                 # summed from the folder above
    f"SHA256 ({ISO}) = {H}\n",                            # BSD
    f"# {ISO}: 123 bytes\nSHA256 ({ISO}) = {H}\n",        # Rocky's .CHECKSUM
    f"{'cd' * 32}  other.iso\n{H}  {ISO}\n",              # a list of several
    f"{H.upper()}  {ISO}\r\n",                            # upper case, CRLF
    f"{H}\n",                                             # a bare .sha256
])
def test_sha256_in_reads_the_common_layouts(sums):
    assert sha256_in(sums, ISO) == H


@pytest.mark.parametrize("sums", [
    f"{H}  other.iso\n",                                  # names another file
    f"{H}  {ISO}.zip\n",                                  # names a longer one
    f"{H}  x{ISO}\n",                                     # or one that ends the same
    f"{'ab' * 64}  {ISO}\n",                              # a SHA-512
    f"SHA512 ({ISO}) = {'ab' * 64}\n",
    "",
])
def test_sha256_in_takes_only_a_sha256_of_exactly_that_file(sums):
    assert sha256_in(sums, ISO) == ""


def test_published_sha256_fetches_the_list():
    session = StrictSession({"https://x/SHA256SUMS": f"{H}  {ISO}\n"})
    assert published_sha256(session, "https://x/SHA256SUMS", ISO, "Distro") == H


@pytest.mark.parametrize("answer", [
    Resp("", 404), Resp("", 503), Resp(f"{H}  {ISO}\n", 403), requests.ConnectionError("down"),
    f"{H}  other.iso\n"])
def test_published_sha256_is_empty_rather_than_a_failure(answer, caplog):
    """A checksum is a bonus: without it the download goes ahead unverified."""
    session = StrictSession({"https://x/SHA256SUMS": answer})
    assert published_sha256(session, "https://x/SHA256SUMS", ISO, "Distro") == ""
    assert "[Distro]" in caplog.text
