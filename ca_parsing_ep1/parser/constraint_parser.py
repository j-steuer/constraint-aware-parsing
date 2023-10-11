from ca_parsing_ep1.parser.formula_parser import parse_isla_formula
from grammar_graph import gg
from isla.derivation_tree import DerivationTree
from isla.parser import Column, EarleyParser
from ca_parsing_ep1.parser.state import State
from ca_parsing_ep1.formula.symbol_table import SymbolTable
from ca_parsing_ep1.helpers import remove_brackets
from functools import lru_cache

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
        self.symbol_table = SymbolTable(self.formula)

    def check(self, inp):
        try:
            next(self.parse(inp))
            return True
        except SyntaxError:
            return False
        return False

    def fill_chart(self, chart):
        for i, col in enumerate(chart):
            for state in col.states:
                if state.finished():
                    self.complete(col, state, chart)
                else:
                    sym = state.at_dot()
                    if sym in self.cgrammar:
                        self.predict(col, sym, state)
                    else:
                        if i + 1 >= len(chart):
                            continue
                        self.scan(chart[i + 1], state, sym)
            if self.log:
                print(col, '\n')
        return chart

    def predict(self, col, sym, state):
        for alt in self.cgrammar[sym]:
            new_state = State(sym, tuple(alt), 0, col, 
                              ancestors=set(state.ancestors), 
                              env=dict(state.env))
            new_state.add_ancestor(state)
            self.symbol_table.add_entry(new_state, from_state=state, predict=True)
            col.add(new_state)
            
    def scan(self, col, state, letter):
        if letter == col.letter:
            adv_state = state.advance(letter)
            self.symbol_table.add_entry(adv_state, from_state=state, predict=False)
            col.add(adv_state)
      
    def parent_states(self, col, state):
        return [st for st in state.s_col.states if st.at_dot() == state.name]
        
    def complete(self, col, state, chart):
        return self.earley_complete(col, state, chart)
           
    def earley_complete(self, col, state, chart):
        for st in self.parent_states(col, state):
            adv_state = st.advance(state)
            adv_state.update_env(state)
            
            #parsing the state through the chart
            forest = self.parse_forest(chart, state)
            tree = DerivationTree.from_parse_tree(self.extract_a_tree(forest))
            if self.symbol_table.check(state, self.grammar_graph, tree):
                 self.symbol_table.add_entry(adv_state, from_state=state, predict=False, tree=tree)
                 col.add(adv_state)
            
    def chart_parse(self, words, start):
        alt = tuple(*self.cgrammar[start])
        chart = [Column(i, tok) for i, tok in enumerate([None, *words])]
        
        first_state = State(start, alt, 0, chart[0], aliases = {remove_brackets(start)})
        self.symbol_table.add_entry(first_state)
        
        chart[0].add(first_state)
        return self.fill_chart(chart)
        
    def nonterminal_in_smt(self, nonterminal, smt):
        return nonterminal in [nt.n_type for nt in smt.free_variables()]
    
    
    def parse_paths(self, named_expr, chart, frm, til):
        lru_cache(maxsize=None)
        def parse_paths_mem(data):
            named_expr, chart, frm, til = data
            def paths(state, start, k, e):
                if not e:
                    return [[(state, k)]] if start == frm else []
                else:
                    return [[(state, k)] + r
                            for r in self.parse_paths(e, chart, frm, start)]

            *expr, var = named_expr
            starts = None
            if var not in self.cgrammar:
                starts = ([(var, til - len(var),
                            't')] if til > 0 and chart[til].letter == var else [])
            else:
                starts = [(s, s.s_col.index, 'n') for s in chart[til].states
                        if s.finished() and s.name == var]

            return [p for s, start, k in starts for p in paths(s, start, k, expr)]
            
        tup = (named_expr, chart, frm, til)
        return parse_paths_mem(tup)
    
    def parse_forest(self, chart, state):
        lru_cache(maxsize=None)
        def parse_forest_mem(data):
            chart, state = data
            pathexprs = self.parse_paths(state.expr, chart, state.s_col.index,
                                     state.e_col.index) if state.expr else []
            return state.name, [[(v, k, chart) for v, k in reversed(pathexpr)]
                                for pathexpr in pathexprs]
        
        tup = (chart, state)
        return parse_forest_mem(tup)
    
    def extract_a_tree(self, forest_node):
        lru_cache(maxsize=None)
        def extract_a_tree_mem(data):
            forest_node = data[0]
            name, paths = forest_node
            if not paths:
                return (name, [])
            return (name, [self.extract_a_tree(self.forest(*p)) for p in paths[0]])
        
        tup = (forest_node,)
        return extract_a_tree_mem(tup)
    
