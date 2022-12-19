import jsonlines

tml_file = "../corpus/timebank/nt_format/tbd_tml_metadata.jsonl"
annotated_file = "../corpus/timebank/nt_format/tbd_a1.jsonl"

with jsonlines.open(tml_file) as tml:
    with jsonlines.open(annotated_file) as annotation:
        for a in annotation:
            for t in tml:
                if t["id"] == a["id"]:
                    try:
                        a["timex_refs"] = t["timex_refs"]
                        a["event_refs"] = t["event_refs"]
                    except KeyError:
                        pass
            with jsonlines.open(annotated_file.replace(".jsonl", "_tml.jsonl"), mode="a") as f:
                f.write(a)