from copy import deepcopy
from ca_parsing_ep2.parser.formula_parser import parse_isla_formula
from functools import lru_cache
from ca_parsing_ep2.helpers import remove_brackets
from grammar_graph import gg
from isla.helpers import is_nonterminal, nonterminals
from isla.parser import Column, EarleyParser
from ca_parsing_ep2.parser.state import State
from ca_parsing_ep2.formula.alias import AliasFinder
import isla.language as lang

class ConstraintParser(EarleyParser):

    def __init__(self,
                 grammar,
                 formula = None,
                 starting_symbol = "<start>",
                 **kwargs):
        super().__init__(grammar, **kwargs)
        self.formula = parse_isla_formula(formula, grammar)
        self.grammar_graph = gg.GrammarGraph.from_grammar(grammar)
        self.starting_symbol = starting_symbol
        self.alias_finder = AliasFinder(self.formula)
        
    def predict(self, col, sym, state):
        for alt in self.cgrammar[sym]:
            new_state = State(sym, tuple(alt), 0, col, 
                              parents=set(state.parents), 
                              env=dict(state.env))
            new_state.add_parent(state)
            self.alias_finder.set_aliases(new_state)
            col.add(new_state)
            
    def scan(self, col, state, letter):
        if letter == col.letter:
            col.add(state.advance(letter))
      
          
    def parent_states(self, col, state):
        return [st for st in state.s_col.states if st.at_dot() == state.name]
        
    def complete(self, col, state):
        return self.earley_complete(col, state)
           
    def earley_complete(self, col, state):
        for st in self.parent_states(col, state):
            adv_state = st.advance(state)
            adv_state.update_env(state)
            
            if self.formula.check(state, adv_state, self.grammar_graph):
                 col.add(adv_state)
            
    def chart_parse(self, words, start):
        alt = tuple(*self.cgrammar[start])
        chart = [Column(i, tok) for i, tok in enumerate([None, *words])]
        
        first_state = State(start, alt, 0, chart[0])
        self.alias_finder.set_aliases(first_state)
        
        chart[0].add(first_state)
        return self.fill_chart(chart)
        
    def nonterminal_in_smt(self, nonterminal, smt):
        return nonterminal in [nt.n_type for nt in smt.free_variables()]
