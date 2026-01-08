import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("data/inbox")

RANKED = BASE / "ranked.json"
DRAFTS = BASE / "rascunhos.json"
PUBLISHED = BASE / "publicados.json"
DISCARDED = BASE / "descartados.json"


def load(path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ======================
# Comandos
# ======================

def cmd_list(args):
    ranked = load(RANKED)
    top = ranked[: args.top]

    for i, item in enumerate(top, 1):
        print(
            f"{i:02d}. [{item['score']:>3}] {item['id']} | "
            f"{item['title']} | R$ {item['price']}"
        )


def cmd_show(args):
    ranked = load(RANKED)
    item = next((i for i in ranked if i["id"] == args.id), None)

    if not item:
        print("❌ Item não encontrado.")
        return

    print(json.dumps(item, ensure_ascii=False, indent=2))


def move_item(item_id, source, target, action):
    src = load(source)
    tgt = load(target)

    item = next((i for i in src if i["id"] == item_id), None)
    if not item:
        print("❌ Item não encontrado.")
        return

    src = [i for i in src if i["id"] != item_id]

    item["editorial"] = {
        "action": action,
        "at": now()
    }

    tgt.append(item)

    save(source, src)
    save(target, tgt)

    print(f"✅ {item_id} → {action}")


def cmd_publish(args):
    move_item(args.id, RANKED, PUBLISHED, "published")


def cmd_discard(args):
    move_item(args.id, RANKED, DISCARDED, "discarded")


def cmd_pin(args):
    ranked = load(RANKED)

    for item in ranked:
        if item["id"] == args.id:
            item["score"] += 1000
            item.setdefault("editorial", {})["pinned"] = True
            save(RANKED, ranked)
            print(f"📌 {args.id} fixado no topo.")
            return

    print("❌ Item não encontrado.")


def cmd_stats(_):
    print("📊 Estado editorial:")
    print(f"• Ranqueados : {len(load(RANKED))}")
    print(f"• Publicados : {len(load(PUBLISHED))}")
    print(f"• Rascunhos  : {len(load(DRAFTS))}")
    print(f"• Descartados: {len(load(DISCARDED))}")


# ======================
# CLI
# ======================

def main():
    parser = argparse.ArgumentParser(description="CLI Editorial – Dicas")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list")
    p_list.add_argument("--top", type=int, default=10)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show")
    p_show.add_argument("id")
    p_show.set_defaults(func=cmd_show)

    p_pub = sub.add_parser("publish")
    p_pub.add_argument("id")
    p_pub.set_defaults(func=cmd_publish)

    p_dis = sub.add_parser("discard")
    p_dis.add_argument("id")
    p_dis.set_defaults(func=cmd_discard)

    p_pin = sub.add_parser("pin")
    p_pin.add_argument("id")
    p_pin.set_defaults(func=cmd_pin)

    p_stats = sub.add_parser("stats")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
