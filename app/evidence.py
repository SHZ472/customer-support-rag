"""按课程支持的问题类型，从已检索到的片段中选择证据。"""

import re


def evidence_patterns(question):
    if "退款" in question and "到账" in question:
        return (r"退款[^。！？]*\d+\s*(?:个工作日|工作日|天|小时)[^。！？]*到账",)
    if "发货" in question and ("多久" in question or "时间" in question):
        return (r"付款后\s*\d+\s*(?:小时|天)内发货",)
    if "退货" in question and "条件" in question:
        return (r"签收后\s*\d+\s*天内.*未拆封.*可申请退货", r"申请时需要提供订单编号")
    return ()


def select_evidence(question, candidates):
    patterns = evidence_patterns(question)
    if not patterns:
        return None

    # 一份来源要能支持这类问题要求的全部信息。
    for source in dict.fromkeys(chunk["source"] for chunk in candidates):
        source_chunks = [chunk for chunk in candidates if chunk["source"] == source]
        selected = []
        for pattern in patterns:
            match = next((chunk for chunk in source_chunks if re.search(pattern, chunk["text"])), None)
            if match is None:
                break
            if match not in selected:
                selected.append(match)
        else:
            return source, selected
    return None
