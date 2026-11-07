import json, os, re, sys, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = ["bypassApps", "onlyApps", "directDomains", "proxyDomains", "directIps", "blockDomains"]


def merge(manifests, settings=None):
    sets = {k: [] for k in KEYS}
    for m in manifests:
        r = m.get("rules", {})
        vals = (settings or {}).get(m["id"], {})
        for k in KEYS:
            for x in r.get(k, []):
                if x.strip() and x not in sets[k]: sets[k].append(x)
            sk = r.get("fromSettings", {}).get(k)
            if sk:
                for x in re.split(r"[,\s;]+", vals.get(sk, "")):
                    if x and x not in sets[k]: sets[k].append(x)
    return sets


def load():
    out = []
    for f in sorted(os.listdir(os.path.join(ROOT, "dist"))):
        if f.endswith(".zip"):
            with zipfile.ZipFile(os.path.join(ROOT, "dist", f)) as z:
                out.append(json.loads(z.read("plugin.json")))
    return out


def main():
    ms = load()
    assert len(ms) >= 9, "expected the full set in dist/"
    allr = merge([m for m in ms if m["id"] != "tunn-messengers-only"])
    clash = set(allr["blockDomains"]) & set(allr["proxyDomains"])
    assert not clash, clash
    assert "mc.yandex.ru" in allr["blockDomains"] and "ru" in allr["directDomains"]
    s = merge(ms, {"tunn-ru-apps": {"apps": "com.a.b, com.c.d"}, "tunn-ad-shield": {"extra": "x.test;y.test"}})
    assert "com.a.b" in s["bypassApps"] and "com.c.d" in s["bypassApps"]
    assert "x.test" in s["blockDomains"] and "y.test" in s["blockDomains"]
    for f in os.listdir(os.path.join(ROOT, "dist")):
        if f.endswith(".zip"):
            names = zipfile.ZipFile(os.path.join(ROOT, "dist", f)).namelist()
            assert "plugin.json" in names and all("/" not in n for n in names), f
    print("ok:", len(ms), "plugins;", {k: len(v) for k, v in allr.items()})


main()
