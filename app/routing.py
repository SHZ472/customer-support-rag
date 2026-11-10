"""Choose an exact database answer, a grounded FAQ answer, or an explicit fallback."""

import re

from app.evidence import select_evidence

IDENTIFIER = re.compile(r"(?<![A-Z0-9-])(?:BOOK|ORD)-[0-9]+(?![A-Z0-9-])", re.IGNORECASE | re.ASCII)


def exact_answer(question, lookup):
    match = IDENTIFIER.search(question)
    if match is None:
        return None
    number = match.group().upper()
    kind = "product" if number.startswith("BOOK-") else "order"
    record = lookup(kind, number)
    if record is None:
        return None
    if kind == "product" and any(word in question for word in ("什么书", "书名", "多少钱", "价格")):
        return f"product:{number}", f"{number} 是《{record['title']}》，价格 {record['price_yuan']} 元。"
    if kind == "order" and "发货了吗" in question:
        return f"order:{number}", f"订单 {number} {record['status']}。"
    return None


def answer_question(question, lookup, retriever):
    trace = ["检查精确查询"]
    exact = exact_answer(question, lookup)
    if exact is not None:
        source, answer = exact
        return {"route": "database", "sources": [source], "answer": answer, "trace": trace}

    trace.append("检查 FAQ")
    evidence = select_evidence(question, retriever.search(question))
    if evidence is not None:
        source, chunks = evidence
        return {"route": "faq", "sources": [source], "answer": "\n".join(chunk["text"] for chunk in chunks),
                "trace": trace}

    trace.append("资料不足")
    return {"route": "unknown", "sources": [], "answer": "现有资料无法确认这个问题。", "trace": trace}
