from ca_parsing_ep1.parser.state import State
from ca_parsing_ep1.helpers import update_dict, nonterminal_reachable
from isla.helpers import chain_functions
from isla.derivation_tree import DerivationTree
from isla.evaluator import *
from isla.language import *
from ca_parsing_ep1.formula.alias import AliasFinder

from time import time #delete

#TODO check reachable exists
class Entry:
    def __init__(self, formulas, tree):
        self.formulas = formulas
        self.tree = tree

class SymbolTable:
    def __init__(self, formula):
        self.formula = formula
        self.alias_finder = AliasFinder(formula)
        self.entries = dict()

    def still_reachable(self, state, nonterminal, in_var, grammar_graph):
        if not nonterminal_reachable(grammar_graph, state, nonterminal):
            if in_var in state.aliases:
                return False
            return self.still_reachable(state.ancestors[-1], nonterminal, in_var, grammar_graph)
        return True

    def formulas(self, formulas, state):
        new_formulas = []
        for formula in formulas:
            if isinstance(formula, QuantifiedFormula):
                current_formula = formula
                add = False
                while isinstance(current_formula, QuantifiedFormula):
                    if formula.bound_variable.name in state.aliases and state.is_child_of(formula.in_variable.name):
                        add = True
                    current_formula = current_formula.inner_formula
                if add:
                    new_formulas.append(current_formula)
            new_formulas.append(formula)
        return new_formulas

    def add_entry(self, state, from_state=None, predict=None, tree=None):
        aliases, formulas = self.alias_finder.get_data(state)
        state.aliases = aliases
        entry = Entry([self.formula], None) #default
        if predict:
            from_state_entry = self.entries[from_state]
            from_formulas = from_state_entry.formulas
            
            #TODO any order of nested forall / exists
            new_formulas = self.formulas(from_formulas, state)

            entry = Entry(new_formulas, tree)
        elif not predict is None: #complete
            entry = self.entries[from_state]
            entry = Entry(entry.formulas, tree)
        self.entries[state] = entry

    
    def check(self, state, grammar_graph, reference_tree):
        def convert_dict(dictionary):
            l = []
            for key, value_list in dictionary.items():
                l.append([(key, value) for value in value_list])
            return l
        
        def check_quantified(formulas):
            for formula in [formula for formula in formulas if formula.in_variable == state.name]:
                assignment = {Constant(formula.in_variable.name, formula.in_variable.n_type): ((), reference_tree)}
                evaluation = evaluate_legacy(formula, grammar_graph.grammar, assignment, reference_tree)
                if not evaluation:
                    return False
                
                if isinstance(formula, ExistsFormula):
                    #TODO set exists to found / remove exists
                    pass
            return True
        
        def check_inner(formulas):
            for formula in formulas:
                free_var_names = set([free.name for free in formula.free_variables()])
                aliases_in_z3 = [alias for alias in state.get_aliases() if alias in free_var_names]
                if not aliases_in_z3:
                    continue
            
                for alias in aliases_in_z3:
                    try:
                        remaining_vals = {k: state.env[k] for k in free_var_names - {alias}}
                    except KeyError:
                        continue
                    remaining_vals = convert_dict(remaining_vals)

                    for combination in itertools.product(*remaining_vals):
                        assignments = {BoundVariable(alias, state.name): ((), reference_tree)}
                        for assignment in combination:
                            alias, assgn_state = assignment
                            tree = self.entries.get(assgn_state).tree
                            n_type = self.alias_finder.get_n_type(alias)
                            assignments[BoundVariable(alias, n_type)] = ((), tree)
                        dummy = DerivationTree("dummy")
                        is_forall = self.alias_finder.is_forall(alias)
                        if not evaluate_legacy(formula, grammar_graph.grammar, assignments, dummy):
                            in_var = self.alias_finder.get_in_var(alias)
                            return not is_forall and self.still_reachable(state, state.name, in_var)
                        if not is_forall:
                            #TODO set exists to found / remove exists
                            pass
            return True
                            
        entry = self.entries.get(state)
        assert entry
    
        quantified = [q for q in entry.formulas if isinstance(q, QuantifiedFormula)]
        inner = [q for q in entry.formulas if not isinstance(q, QuantifiedFormula)]
        return check_quantified(quantified) and check_inner(inner)
            
        

    
    """
    def check_eval(self, formula, grammar,  assignments, tree, graph=None, trie=None):
        def close(eval_func):
            return lambda f: eval_func(formula, assignments, tree, graph, grammar, trie)
        
        def raise_not_implemented_error(_0, _1, _2, _3, _4, _5):
            raise NotImplementedError
        


        monad = chain_functions(map(close, [
            evaluate_smt_formula,
            evaluate_quantified_formula,
            evaluate_structural_predicate_formula,
            evaluate_semantic_predicate_formula,
            evaluate_negated_formula_formula,
            evaluate_conjunctive_formula_formula,
            evaluate_disjunctive_formula,
            raise_not_implemented_error
        ]), formula)

        return monad.a
    """