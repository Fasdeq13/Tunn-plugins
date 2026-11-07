import hashlib, json, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_EXT = {"json", "so", "js", "css", "png", "svg", "txt", "md", "webp", "jpg"}
RULE_KEYS = {"bypassApps", "onlyApps", "directDomains", "proxyDomains", "directIps", "blockDomains"}
SETTING_TYPES = {"text", "switch", "select", "number"}
DOMAIN = re.compile(r"^(?:(?:domain|full|keyword|regexp|geosite|ext):)?[^\s,;]+$")
PKG = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")
CIDR = re.compile(r"^[0-9a-fA-F:.]+(/\d{1,3})?$")


def fail(msg):
    print("ERROR:", msg)
    sys.exit(1)


def validate(pid, path):
    m = json.load(open(os.path.join(path, "plugin.json"), encoding="utf-8"))
    if m.get("id") != pid: fail(f"{pid}: id must equal the folder name")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", m["id"]): fail(f"{pid}: bad id")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", str(m.get("version", ""))): fail(f"{pid}: bad version")
    for k in ("name", "description", "author"):
        if not m.get(k): fail(f"{pid}: missing {k}")
    r = m.get("rules", {})
    for k, v in r.items():
        if k == "fromSettings":
            keys = {s["key"] for s in m.get("settings", [])}
            for rk, sk in v.items():
                if rk not in RULE_KEYS: fail(f"{pid}: fromSettings unknown rule {rk}")
                if sk not in keys: fail(f"{pid}: fromSettings {rk} -> missing setting {sk}")
            continue
        if k not in RULE_KEYS: fail(f"{pid}: unknown rule key {k}")
        if len(set(v)) != len(v): fail(f"{pid}: duplicates in {k}")
        for x in v:
            ok = PKG.match(x) if k in ("bypassApps", "onlyApps") else (CIDR.match(x) if k == "directIps" else DOMAIN.match(x))
            if not ok: fail(f"{pid}: bad value in {k}: {x!r}")
    if "onlyApps" in r and "bypassApps" in r: fail(f"{pid}: onlyApps and bypassApps in one plugin")
    seen = set()
    for s in m.get("settings", []):
        if s.get("type") not in SETTING_TYPES: fail(f"{pid}: bad setting type {s.get('type')}")
        if s["key"] in seen: fail(f"{pid}: duplicate setting {s['key']}")
        seen.add(s["key"])
    return m


def build():
    plugdir = os.path.join(ROOT, "plugins")
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    for f in os.listdir(dist):
        if f.endswith(".zip"): os.remove(os.path.join(dist, f))
    index = []
    for pid in sorted(os.listdir(plugdir)):
        path = os.path.join(plugdir, pid)
        if not os.path.isdir(path): continue
        m = validate(pid, path)
        ui = m.get("uiNative")
        if ui and not os.path.isfile(os.path.join(path, ui["lib"])):
            print("skip", pid, "(no", ui["lib"], "- run tools/build_ui_android.sh)")
            continue
        out = os.path.join(dist, f"{pid}-{m['version']}.zip")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
            for name in sorted(os.listdir(path)):
                ext = name.rsplit(".", 1)[-1].lower()
                if ext not in ALLOWED_EXT: fail(f"{pid}: file {name} would be ignored by Tunn")
                info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = 0o644 << 16
                z.writestr(info, open(os.path.join(path, name), "rb").read())
        data = open(out, "rb").read()
        index.append({"id": pid, "name": m["name"], "version": m["version"], "kinds": m.get("kinds", []), "description": m["description"],
                      "file": f"dist/{os.path.basename(out)}", "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
        print("built", os.path.basename(out))
    th = []
    for f in sorted(os.listdir(os.path.join(ROOT, "themes"))):
        if not f.endswith(".json"): continue
        raw = open(os.path.join(ROOT, "themes", f), "rb").read()
        t = json.loads(raw)
        th.append({"id": t["id"], "name": t.get("name", t["id"]), "version": str(t.get("version", "1")), "description": "Тема оформления",
                   "file": f"themes/{f}", "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)})
    json.dump({"plugins": index, "themes": th}, open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(os.path.join(ROOT, "index.json"), "a").write("\n")


def themes():
    for f in sorted(os.listdir(os.path.join(ROOT, "themes"))):
        if not f.endswith(".json"): continue
        t = json.load(open(os.path.join(ROOT, "themes", f), encoding="utf-8"))
        for side in ("dark", "light"):
            for k, v in t.get(side, {}).items():
                if not re.fullmatch(r"#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})", v): fail(f"theme {f}: bad colour {side}.{k}={v}")
        if not (t.get("dark") or t.get("light") or t.get("tune")): fail(f"theme {f}: empty")
        print("theme ok", f)


if __name__ == "__main__":
    build()
    themes()
