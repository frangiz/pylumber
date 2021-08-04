# collects all prices and stores in db. Should be run nightly. 

import requests
import json
from pathlib import Path


Path("dumps").mkdir(exist_ok=True)

urls = []
with open("sources.txt", "r") as f:
    urls = f.readlines()

for url in urls:
    if url.startswith("#"):
        continue
    cached_name = url.strip().split("/")[-1]
    if not Path("dumps", cached_name).exists():
        with open(Path("dumps", cached_name), "w") as f:
            f.writelines(requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
).text)


def print_price(filename: str) -> None:
    content = ""
    with open(Path("dumps", filename), "r") as f:
        content = "".join(f.readlines())

    marker = r"'products':["
    try:
        start = content.index(marker)
        end = content.index("}", start)
        product = json.loads(content[start + len(marker): end + 1].replace("'", "\""))
        print(product)
    except ValueError as e:
        print(f"{e} for file {filename}")
        raise e


for file in Path("dumps").glob("*"):
    print_price(file.name)