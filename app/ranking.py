"""第9天的中文分词和 RRF 排名融合。"""

import re

import jieba


def tokenize(text):
    return [word for word in jieba.lcut(text.lower()) if re.search(r"[\w]", word)]


def fuse(rankings, constant=60):
    scores = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(dict.fromkeys(ranking), start=1):
            scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (constant + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
