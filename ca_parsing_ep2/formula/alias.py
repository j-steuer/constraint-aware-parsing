from ca_parsing.helpers import remove_brackets, update_dict
from isla.language import *

class Alias:
    def __init__(self, name, type):
        assert name and isinstance(name, str)
        self.name = name
        assert type == "f" or type == "e"
        self.type = type
        self.found = False
    
    def __eq__(self, val):
        if isinstance(val, Alias):
            return self.name == val.name and self.type == val.type
        if isinstance(val, str):
            return self.name == val
        return False

    def is_forall(self):
        return self.type == "f"
    
    def is_exists(self):
        return self.type == "e"
    
    def set_found(self):
        if self.is_exists():
            self.found = True

class AliasFinder(FormulaVisitor):
    def __init__(self, formula):
        super().__init__()
        self.binds = dict()
        formula.accept(self)

    def insert_bind(self, formula):
        nonterminal = formula.bound_variable.n_type
        typing = "f" if isinstance(formula, ForallFormula) else "e"
        info = (formula.in_variable.name, bool(formula.bind_expression), formula.bound_variable.name, typing)
        update_dict(self.binds, nonterminal, info)
    
    def visit_forall_formula(self, formula):
        self.insert_bind(formula)

    def visit_exists_formula(self, formula):
        self.insert_bind(formula)

    def set_aliases(self, state, starting_symbol="<start>"):
        if state.name == starting_symbol:
            alias = Alias(remove_brackets(starting_symbol), "f")
            state.add_alias(alias)
            return

        for info in self.binds.get(state.name, set()):
            in_variable, bound, name, typing = info

            if any(in_variable in p.get_aliases() for p in state.parents):
                alias = Alias(name, typing)
                state.add_alias(alias, bound)
