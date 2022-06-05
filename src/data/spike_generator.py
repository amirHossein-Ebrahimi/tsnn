import random

import numpy as np

from src import configs
from src.data.constants import letters, words
from src.data.corpus_generator import gen_corpus


def spike_stream_i(char):
    spikes = np.zeros(len(letters), dtype=int)
    if char in letters:
        spikes[letters.index(char)] = 1
    return spikes


def get_data(size, prob=0.7, fixed_size=3):
    corpus = gen_corpus(
        size,
        prob,
        min_length=fixed_size,
        max_length=fixed_size,
        no_common_chars=False,
        letters_to_use=letters,
        words_to_use=words,
    )
    # 7 with reward in reward window
    random.shuffle(corpus)
    sparse_gap = " " * configs.GAP
    joined_corpus = sparse_gap.join(corpus) + sparse_gap
    stream_i = [spike_stream_i(char) for char in joined_corpus]
    stream_j = []

    empty_spike = np.empty(len(words))
    empty_spike[:] = np.NaN

    # NOTE: 🚀 it seems that shifting all spikes won't chane the flow, but has more neuro-scientific effects
    # uncomment line 39 and comment line 49-50 to see the difference
    for word in corpus:
        for _ in word:
            # for _ in range(len(word) - 1):
            stream_j.append(empty_spike)

        word_spike = np.zeros(len(words), dtype=bool)
        if word in words:
            word_index = words.index(word)
            word_spike[word_index] = 1
        stream_j.append(word_spike)  # spike when see hole word!

        for _ in range(configs.GAP - 1):
            stream_j.append(empty_spike)

    if len(stream_i) != len(stream_j):
        raise AssertionError("stream length mismatch")

    return stream_i, stream_j, joined_corpus


if __name__ == "__main__":
    stream_i, stream_j, corpus = get_data(size=100, prob=0.7, fixed_size=3)
    print(stream_i)
    print(stream_j)
    print(corpus)
