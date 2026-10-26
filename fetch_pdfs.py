import re, sys, pathlib, requests
URL = "https://нэмк.рф/life/schedule/"
out = pathlib.Path(sys.argv[1]); out.mkdir(exist_ok=True)
html = requests.get(URL, timeout=30).text
links = sorted(set(re.findall(r'href="([^"]+\.pdf)"', html, re.I)))
if not links: sys.exit("PDF-ссылки не найдены: проверь вёрстку страницы")
for i, h in enumerate(links):
    u = requests.compat.urljoin(URL, h)
    (out / f"{i}.pdf").write_bytes(requests.get(u, timeout=60).content)
print("скачано:", len(links))
