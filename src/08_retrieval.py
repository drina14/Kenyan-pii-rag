import json
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from ke_recognizers import build_ke_analyzer


docs = json.load(open("data/corpus.json", encoding="utf-8"))
questions = json.load(open("data/questions.json", encoding="utf-8"))

ROLES = ["receptionist", "clinician", "dpo"]
ENTITIES = ["PERSON", "PHONE_NUMBER", "KE_NATIONAL_ID"]
K = 3

analyzer = build_ke_analyzer()
anonymizer = AnonymizerEngine()
operators = {e: OperatorConfig("replace", {"new_value": f"<{e}>"}) for e in ENTITIES}


def mask(text):
    found = analyzer.analyze(text=text, language="en", entities=ENTITIES, score_threshold=0.4)
    return anonymizer.anonymize(text=text, analyzer_results=found, operators=operators).text


for d in docs:
    d["masked_text"] = mask(d["text"])

import hmac
import hashlib

SECRET = b"prototype-secret-key"  


def pseudo_token(entity, value):
    if entity == "PERSON":
        words = re.sub(r"['’]s$", "", value.strip()).lower().split()
        words = [w.strip(".,") for w in words if w.strip(".,") not in ("dr", "")]
        return " ".join(
            "PERSON_" + hmac.new(SECRET, f"PERSON:{w}".encode(), hashlib.sha256).hexdigest()[:6]
            for w in words
        )
    norm = "".join(ch for ch in value if ch.isdigit())
    h = hmac.new(SECRET, f"{entity}:{norm}".encode(), hashlib.sha256).hexdigest()[:6]
    return f"{entity}_{h}"

pseudo_ops = {e: OperatorConfig("custom", {"lambda": (lambda v, e=e: pseudo_token(e, v))})
              for e in ENTITIES}


def pseudo(text):
    found = analyzer.analyze(text=text, language="en", entities=ENTITIES, score_threshold=0.4)
    return anonymizer.anonymize(text=text, analyzer_results=found, operators=pseudo_ops).text


for d in docs:
    d["pseudo_text"] = pseudo(d["text"])
    def leaked(value, label, masked):
       if label == "PERSON":
        parts = [w.strip(".,") for w in value.split() if len(w.strip(".,")) > 2]
        return any(p in masked for p in parts)
        return value in masked
doc_leaks = [(d["doc_id"], v) for d in docs for v, l in d["entities"] if leaked(v, l, d["masked_text"])]
total_ids = sum(len(d["entities"]) for d in docs)

lines = []
lines.append(f"Corpus masking check: {total_ids} labelled identifiers, "
             f"{len(doc_leaks)} still visible after masking")
for doc_id, v in doc_leaks:
    lines.append(f"  LEAK in {doc_id}: {v}")
lines.append("")


def build_index(field):
    index = {}
    for role in ROLES + ["ALL"]:
        allowed = [d for d in docs if role == "ALL" or role in d["allowed_roles"]]
        vec = TfidfVectorizer()
        mat = vec.fit_transform([d[field] for d in allowed])
        index[role] = (allowed, vec, mat)
    return index


def retrieve(index, role_key, query):
    allowed, vec, mat = index[role_key]
    sims = cosine_similarity(vec.transform([query]), mat)[0]
    order = sims.argsort()[::-1][:K]
    return [allowed[i] for i in order if sims[i] > 0]

def run(label, field, use_filter, query_fn=None):
    index = build_index(field)
    n_ans = top1 = hit_k = contains = 0
    n_deny = deny_leaks = 0
    exposed = 0
    detail = []

    for q in questions:
        if q["expected"] == "out_of_scope":
            continue  
        role_key = q["role"] if use_filter else "ALL"
        query = query_fn(q["question"]) if query_fn else q["question"]
        results = retrieve(index, role_key, query)
        ids = [r["doc_id"] for r in results]
        exposed += sum(1 for r in results for v, l in r["entities"] if leaked(v, l, r[field]))
        if q["expected"] == "answer":
            n_ans += 1
            exp = set(q["expected_docs"])
            ok1 = bool(ids) and ids[0] in exp
            okk = exp <= set(ids)
            top1 += ok1
            hit_k += okk
            if q["answer_contains"] and results:
                contains += q["answer_contains"].lower() in results[0][field].lower()
            detail.append(f"  {q['qid']} {q['role']:<12} answer  top1={'Y' if ok1 else 'N'} "
                          f"hit@{K}={'Y' if okk else 'N'}  got={ids}")
        else:  
            n_deny += 1
            bad = [i for i in ids if i in q["forbidden_docs"]]
            deny_leaks += len(bad)
            detail.append(f"  {q['qid']} {q['role']:<12} deny    forbidden retrieved={bad}  got={ids}")

    n_contains = sum(1 for q in questions if q["expected"] == "answer" and q["answer_contains"])
    lines.append("=" * 64)
    lines.append(label)
    lines.append("=" * 64)
    lines.append(f"Answer questions: {n_ans} | top-1 correct doc: {top1} | all expected docs in top-{K}: {hit_k}")
    lines.append(f"Top-1 text contains the answer string: {contains} of {n_contains}")
    lines.append(f"Deny questions: {n_deny} | forbidden documents retrieved: {deny_leaks}")
    lines.append(f"Identifiers visible in retrieved text (all questions): {exposed}")
    lines.append("Per question:")
    lines.extend(detail)
    lines.append("")


run("A. Unmasked documents + role filter", "text", True)
run("B. Masked documents + role filter", "masked_text", True)
run("D. Pseudonymised documents AND queries + role filter", "pseudo_text", True, pseudo)
run("C. CONTROL: unmasked documents, NO role filter", "text", False)

output = "\n".join(lines)
print(output)
open("results_13_retrieval.txt", "w", encoding="utf-8").write(output)