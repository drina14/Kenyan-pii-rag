import re

NUM = re.compile(r"\+?\d[\d\- ]{5,}\d")
TAG = re.compile(r"\[\[(P|ID|PH)\|(.*?)\]\]")


def values(path):
    nums, names = set(), set()
    for line in open(path, encoding="utf-8"):
        if line.startswith("#"):
            continue
        for kind, val in TAG.findall(line):
            if kind == "P":
                names.add(val.lower())
        plain = TAG.sub(lambda m: m.group(2), line)
        nums |= {re.sub(r"\D", "", n) for n in NUM.findall(plain)}
    return nums, names


final_nums, final_names = values("data/handwritten_final.txt")
for other in ["data/handwritten.txt", "data/handwritten_test.txt"]:
    n, p = values(other)
    print(other)
    print("  numbers also in final:", sorted(final_nums & n) or "none")
    print("  names also in final:  ", sorted(final_names & p) or "none")