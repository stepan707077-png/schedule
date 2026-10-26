import pdfplumber, re, json, sys, os, datetime
DAYS = ["Пн","Вт","Ср","Чт","Пт","Сб"]
INI = re.compile(r'[А-ЯЁ]\.[А-ЯЁ]\.')
def clean(s): return re.sub(r'([а-яё])([А-ЯЁ]\.)', r'\1 \2', s).strip()
def cell(box):
    ch = [c for c in box.chars if c["text"].strip()]
    if not ch: return None
    small = sorted([c for c in box.chars if c["size"] < 6.5], key=lambda c: c["x0"])
    big = [c for c in box.chars if c["size"] >= 6.5]
    lines = []
    for c in sorted(big, key=lambda c: c["top"]):
        if lines and abs(lines[-1][0] - c["top"]) < 4: lines[-1][1].append(c)
        else: lines.append([c["top"], [c]])
    s = " ".join("".join(c["text"] for c in sorted(l[1], key=lambda c: c["x0"])).strip() for l in lines)
    ttxt = clean("".join(c["text"] for c in small)); ttxt = re.sub(r"([А-ЯЁ]\.[А-ЯЁ])(\d)\.(\d)", r"\1.\2\3", ttxt)
    t = r = ""
    m = INI.search(ttxt)
    if m: t, r = ttxt[:m.end()].strip(), ttxt[m.end():].strip()
    elif ttxt: t, _, r = ttxt.rpartition(" ")
    return {"s": s, "t": t, "r": r} if s or t else None
def merge_practice(ls):
    """Практика в PDF - одна ячейка на 3 пары: препод. в 1-й строке, название в другой. Склеиваем."""
    t = next((x for x in ls if not x["s"] and x["t"]), None)
    pr = next((x for x in ls if "практика" in x["s"].lower()), None)
    if not (t and pr): return ls
    m = {"s": pr["s"], "t": t["t"], "r": t["r"], "p": t["p"], "e": t["p"] + 2}
    rest = [x for x in ls if x is not t and x is not pr]
    return sorted(rest + [m], key=lambda x: x["p"])
def parse(path, year):
    out, week = {}, None
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            if pg.width > pg.height: return None, {}
            m = re.search(r'(\d\d)\.(\d\d)-(\d\d)\.(\d\d)', pg.extract_text() or "")
            if m: week = (m.group(0), f"{year}-{m.group(2)}-{m.group(1)}")
            vs = sorted({round(l['x0']) for l in pg.lines if abs(l['x0']-l['x1']) < 1})
            hs = sorted({round(l['top']) for l in pg.lines if abs(l['top']-l['bottom']) < 1})
            cols = list(zip(vs[2:], vs[3:])); rows = list(zip(hs[1:], hs[2:]))
            for x0, x1 in cols:
                g = " ".join(pg.crop((x0+1, hs[0], x1-1, hs[1])).extract_text().split())
                days = {}
                for i, (y0, y1) in enumerate(rows[:30]):
                    if i == 29: continue  # 5-я пара субботы: там только вертикальная надпись "Расписание"
                    c = cell(pg.crop((x0+1, y0+1, x1-1, y1-1)))
                    if c:
                        c["p"] = i % 5 + 1; days.setdefault(DAYS[i//5], []).append(c)
                if g: out[g] = {d: merge_practice(v) for d, v in days.items()}
    return week, out
if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    year = datetime.date.today().year
    data = json.load(open(dst)) if os.path.exists(dst) else {"weeks": {}}
    for f in sorted(os.listdir(src)):
        if not f.endswith(".pdf"): continue
        week, groups = parse(os.path.join(src, f), year)
        if week:
            w = data["weeks"].setdefault(week[1], {"label": week[0], "groups": {}})
            w["groups"].update(groups)
    json.dump(data, open(dst, "w"), ensure_ascii=False)
    for k, w in data["weeks"].items(): print(k, w["label"], len(w["groups"]), "групп")
