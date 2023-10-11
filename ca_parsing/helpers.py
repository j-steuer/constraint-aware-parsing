from functools import lru_cache
from isla.helpers import is_nonterminal
import string
from isla.solver import ISLaSolver

def update_dict(dictionary, key, val):
    dictionary[key] = dictionary.setdefault(key, {val}).union({val})

def remove_brackets(st):
    return st.replace("<", "").replace(">", "")

@lru_cache(maxsize=None) 
def reachable(grammar_graph, start, nonterminal):
    return grammar_graph.reachable(start, nonterminal)    

def nonterminal_reachable(grammar_graph, from_state, nonterminal):
    starts = [t for t in from_state.expr[from_state.dot:] if is_nonterminal(t)]
    return any(reachable(grammar_graph, start, nonterminal) for start in starts)

if __name__ == "__main__":
    grammar = {"<start>": ["<payload-length> <payload>"],
               "<payload-length>": ["<number>"],
               "<number>": ["<leaddigit><digits>", "<leaddigit>"],
               "<digits>": ["<digit><digits>", "<digit>"],
               "<payload>": ["<word>"],
               "<word>": ["<char><word>", "<char>"],
               "<leaddigit>": [str(i) for i in range(1, 10)],
               "<digit>": [str(i) for i in range(10)],
               "<char>": [c for c in string.printable]}
    solver = ISLaSolver(grammar)