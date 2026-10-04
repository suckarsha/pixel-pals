#!/usr/bin/env python3
"""Generative collection builder.

Picks unique trait combinations using rarity weights and compatibility rules,
then renders the images and writes metadata, a CSV and a rarity report.

    python generate.py --count 1000 --seed 2026
    python generate.py --count 50 --out samples      # preview batch
"""
import argparse
import csv
import hashlib
import json
import os
import random
from collections import Counter
from functools import lru_cache
from multiprocessing import Pool

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = {}


def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["layers_path"] = os.path.join(os.path.dirname(os.path.abspath(path)), cfg["layers_dir"])
    missing = [f"{g}/{t}.png" for g in cfg["layer_order"] for t in cfg["traits"][g]
               if t != "None" and not os.path.exists(os.path.join(cfg["layers_path"], g, t + ".png"))]
    if missing:
        raise SystemExit("Missing layer files:\n  " + "\n  ".join(missing))
    return cfg


def broken_rule(combo, rules):
    """Return the first compatibility rule this combination breaks, or None."""
    for rule in rules:
        if all(combo[g] == v for g, v in rule["if"].items()):
            if any(combo[g] in banned for g, banned in rule["not"].items()):
                return rule
    return None


def dna_of(combo, order):
    return hashlib.sha1("|".join(f"{g}:{combo[g]}" for g in order).encode()).hexdigest()


def pick_combos(cfg, count, seed):
    rng = random.Random(seed)
    order = cfg["layer_order"]
    names = {g: list(cfg["traits"][g]) for g in order}
    weights = {g: list(cfg["traits"][g].values()) for g in order}
    seen, combos, attempts = set(), [], 0
    while len(combos) < count:
        attempts += 1
        if attempts > count * 500:
            raise SystemExit(f"Only {len(combos)} unique combinations found - add traits or relax rules.")
        combo = {g: rng.choices(names[g], weights=weights[g])[0] for g in order}
        if broken_rule(combo, cfg["incompatible"]):
            continue
        dna = dna_of(combo, order)
        if dna in seen:
            continue
        seen.add(dna)
        combos.append({"edition": len(combos) + 1, "dna": dna, "traits": combo})
    return combos


def add_rarity(combos, order):
    total = len(combos)
    counts = {g: Counter(c["traits"][g] for c in combos) for g in order}
    for c in combos:
        c["rarity_score"] = round(sum(total / counts[g][c["traits"][g]] for g in order), 2)
    for rank, c in enumerate(sorted(combos, key=lambda c: -c["rarity_score"]), 1):
        c["rarity_rank"] = rank
    return counts


# ------------------------------------------------------------------ rendering
def _init(cfg):
    CFG.update(cfg)


@lru_cache(maxsize=None)
def _layer(rel_path):
    img = Image.open(os.path.join(CFG["layers_path"], rel_path)).convert("RGBA")
    size = (CFG["size"], CFG["size"])
    return img if img.size == size else img.resize(size, Image.LANCZOS)


def render(job):
    item, out_dir = job
    img = Image.new("RGBA", (CFG["size"], CFG["size"]), (255, 255, 255, 255))
    for group in CFG["layer_order"]:
        trait = item["traits"][group]
        if trait != "None":
            img.alpha_composite(_layer(f"{group}/{trait}.png"))
    for overlay in CFG.get("overlays", []):      # logo etc. always on top
        img.alpha_composite(_layer(overlay))
    img.convert("RGB").save(os.path.join(out_dir, "images", f"{item['edition']}.png"), optimize=True)
    return item["edition"]


# -------------------------------------------------------------------- outputs
def write_metadata(cfg, combos, out_dir):
    order = cfg["layer_order"]
    everything = []
    for c in combos:
        meta = {
            "name": f"{cfg['collection_name']} #{c['edition']}",
            "description": cfg["description"],
            "image": f"images/{c['edition']}.png",
            "edition": c["edition"],
            "dna": c["dna"],
            "attributes": [{"trait_type": g, "value": c["traits"][g]} for g in order],
            "rarity_score": c["rarity_score"],
            "rarity_rank": c["rarity_rank"],
        }
        with open(os.path.join(out_dir, "metadata", f"{c['edition']}.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        everything.append(meta)
    with open(os.path.join(out_dir, "_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(everything, f, indent=1)
    with open(os.path.join(out_dir, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["edition", "name", "file", *order, "rarity_score", "rarity_rank", "dna"])
        for c in combos:
            w.writerow([c["edition"], f"{cfg['collection_name']} #{c['edition']}", f"{c['edition']}.png",
                        *[c["traits"][g] for g in order], c["rarity_score"], c["rarity_rank"], c["dna"]])


def write_rarity_report(cfg, combos, counts, out_dir, seed):
    total = len(combos)
    lines = [f"# Rarity report - {cfg['collection_name']} collection", "",
             f"- Images: **{total}** (all unique, checked by DNA hash)",
             f"- Seed: `{seed}` (same seed + same config = same collection)", ""]
    rows = []
    for g in cfg["layer_order"]:
        wsum = sum(cfg["traits"][g].values())
        lines += [f"## {g}", "", "| Trait | Target % | Count | Actual % |", "|---|---:|---:|---:|"]
        for t, wt in sorted(cfg["traits"][g].items(), key=lambda kv: -kv[1]):
            n = counts[g][t]
            lines.append(f"| {t} | {wt / wsum * 100:.1f} | {n} | {n / total * 100:.1f} |")
            rows.append([g, t, round(wt / wsum * 100, 2), n, round(n / total * 100, 2)])
        lines.append("")
    lines += ["## Top 10 rarest", "", "| Rank | Edition | Score | Traits |", "|---:|---:|---:|---|"]
    for c in sorted(combos, key=lambda c: c["rarity_rank"])[:10]:
        traits = ", ".join(f"{g}: {v}" for g, v in c["traits"].items())
        lines.append(f"| {c['rarity_rank']} | #{c['edition']} | {c['rarity_score']} | {traits} |")
    lines += ["", "## Compatibility rules applied", ""]
    lines += [f"- {r['reason']}" for r in cfg["incompatible"]]
    with open(os.path.join(out_dir, "rarity_report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out_dir, "rarity.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "trait", "target_pct", "count", "actual_pct"])
        w.writerows(rows)


def contact_sheet(out_dir, editions, cols=10, thumb=200):
    rows = -(-len(editions) // cols)
    sheet = Image.new("RGB", (cols * thumb, rows * thumb), "white")
    for i, ed in enumerate(editions):
        im = Image.open(os.path.join(out_dir, "images", f"{ed}.png")).resize((thumb, thumb), Image.LANCZOS)
        sheet.paste(im, ((i % cols) * thumb, (i // cols) * thumb))
    sheet.save(os.path.join(out_dir, "contact_sheet.png"), optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=os.path.join(HERE, "config.json"))
    ap.add_argument("--count", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=os.path.join(HERE, "output"))
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    cfg = load_config(args.config)
    os.makedirs(os.path.join(args.out, "images"), exist_ok=True)
    os.makedirs(os.path.join(args.out, "metadata"), exist_ok=True)

    combos = pick_combos(cfg, args.count, args.seed)
    counts = add_rarity(combos, cfg["layer_order"])

    # safety checks before spending time on rendering
    assert len({c["dna"] for c in combos}) == len(combos), "duplicate found"
    assert not any(broken_rule(c["traits"], cfg["incompatible"]) for c in combos), "rule broken"

    with Pool(args.workers, initializer=_init, initargs=(cfg,)) as pool:
        for n, _ in enumerate(pool.imap_unordered(render, [(c, args.out) for c in combos], chunksize=20), 1):
            if n % 250 == 0 or n == len(combos):
                print(f"rendered {n}/{len(combos)}")

    write_metadata(cfg, combos, args.out)
    write_rarity_report(cfg, combos, counts, args.out, args.seed)
    contact_sheet(args.out, [c["edition"] for c in combos[:50]])
    print(f"Done: {len(combos)} unique images, 0 duplicates, 0 rule violations -> {args.out}")


if __name__ == "__main__":
    main()
