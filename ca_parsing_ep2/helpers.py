from functools import lru_cache
from isla.helpers import is_nonterminal

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