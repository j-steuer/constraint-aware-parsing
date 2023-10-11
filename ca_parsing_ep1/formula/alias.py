from isla.language import *

class AliasFinder(FormulaVisitor):
    def __init__(self, formula):
        super().__init__()
        self.binds = dict()
        self.forall, self.exists = [], []
        formula.accept(self)
    
    def visit_forall_formula(self, formula):
        self.forall.append(formula)

    def visit_exists_formula(self, formula):
        self.exists.append(formula)

    def is_forall(self, alias):
        for formula in self.forall + self.exists:
            if formula.bound_variable.name == alias:
                return isinstance(formula, ForallFormula)
        raise Exception

    def get_n_type(self, alias):
        for formula in self.forall + self.exists:
            if formula.bound_variable.name == alias:
                return formula.bound_variable.n_type
        raise Exception("Invalid alias")
    
    def get_in_var(self, alias):
        for formula in self.forall + self.exists:
            if formula.bound_variable.name == alias:
                return formula.in_variable.name
        raise Exception("Invalid alias")

    def get_data(self, state):
        in_forall = [f for f in self.forall if f.in_variable.n_type == state.name]
        in_exists = [e for e in self.forall if e.in_variable.n_type == state.name]

        alias_f = [f for f in self.forall + self.exists if f.bound_variable.n_type == state.name
                                                        and state.is_child_of(f.in_variable.name)]
        for f in alias_f:
            state.aliases.add(f.bound_variable.name)
        
        return state.aliases, (in_forall, in_exists)