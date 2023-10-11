import isla.language as lang
from abc import abstractmethod
from ca_parsing_ep2.helpers import nonterminal_reachable
from copy import deepcopy
from isla.helpers import is_nonterminal
from isla.z3_helpers import evaluate_z3_expression
import itertools
from ca_parsing_ep2.parser.state import State
import z3
    
class Formula(lang.Formula):
    @abstractmethod
    def check(self, state: State, _0, _1) -> bool:
        raise NotImplementedError()
        
class SMTFormula(lang.SMTFormula):

    def check(self, state: State, adv: State, grammar_graph) -> bool:
        def convert_dict(dictionary):
            l = []
            for key, value_list in dictionary.items():
                l.append([(key, value) for value in value_list])
            return l
        
        if not self.free_variables():
            return evaluate_z3_expression(self.formula)[1] 
        
        free_var_names = set([free.name for free in self.free_variables()])
        aliases_in_z3 = [alias.name for alias in state.get_aliases() if alias.name in free_var_names]
        
        if not aliases_in_z3:
            return True
        
        #Only forall TODO exists
        for alias in aliases_in_z3:
            a, text = z3.String(alias), z3.StringVal(state.text)
            z3_formula_base = z3.substitute(self.formula, (a, text))

            if not free_var_names - {alias}:
                return evaluate_z3_expression(z3_formula_base)[1]
            
            try:
                remaining_vals = {k: state.env[k] for k in free_var_names - {alias}}
            except KeyError:
                return True
            remaining_vals = convert_dict(remaining_vals)
            
            for combination in itertools.product(*remaining_vals):
                z3_formula = deepcopy(z3_formula_base)
                for substitution in combination:
                    to_subst, val = substitution
                    to_subst, val = z3.String(to_subst), z3.StringVal(val)
                    z3_formula = z3.substitute(z3_formula, (to_subst, val))
                    if not evaluate_z3_expression(z3_formula)[1]:
                        return False
        return True


                
            
        """
        z3_formula = z3.substitute(self.formula, (z3.String(val), z3.StringVal(state.text)))
        other_variables = [v.n_type for v in self.free_variables() if not v.n_type == state.name]
        
        if other_variables:
            other_variable = other_variables[0] #TODO for any amount of free variables
            for instance in state.env.get(other_variable):
                    other_variable_n = remove_brackets(other_variable) #TODO
                    z3_formula_inst = z3.substitute(z3_formula, (z3.String(other_variable_n), z3.StringVal(instance)))
                    if not evaluate_z3_expression(z3_formula_inst)[1]:
                        return False
        """
        
class ForallFormula(lang.ForallFormula):

    def check_bind_expr(self, state, _0, _1):

        if not self.bind_expression or not state.name == self.bound_variable.n_type:
            return True

        assignments = set()
        
        for idx, element in enumerate(self.bind_expression.bound_elements):
            try:
                state.children[idx]
            except IndexError:
                return True
            
            if not is_nonterminal(element.n_type):
                if state.children[idx].text == element.n_type:
                    continue
                return True
            if isinstance(state.children[idx], str):
                return True
            if not state.children[idx].is_equivalent(element.n_type):
                return True
            if not isinstance(element, lang.DummyVariable):
                assignments.add((element.name, state.children[idx]))
        
        state.move_bound_alias(self.bound_variable.name)
        for child in state.all_children_of():
            #check for any child in case nonterminal must be in this expression
            if not self.check_with_parent(child, state, _0, _1):
                return False
        for assignment in assignments:
            alias, child = assignment
            copy_child = child.copy()
            copy_child.add_match_alias(alias)
            #check child in match expression
            if not self.check(copy_child, _0, _1):
                return False
            state.update_env(child)
        return True
    
    def check_with_parent(self, state, parent, _0, _1):
        if parent in state.parents:
            return self.check(state, _0, _1)
        copy_state = state.copy()
        copy_state.add_parent(parent)
        return self.check(copy_state, _0, _1)

    def check_alias(self, state):
        nonterminal, alias = self.bound_variable.n_type, self.bound_variable.name
        in_alias = self.in_variable.name
        if not alias in state.get_aliases() and nonterminal == state.name and state.is_child_of(in_alias):
            state.update_alias(self)
            return True
        return False
            
    def check(self, state: State, _0, _1) -> bool:
        if not self.check_bind_expr(state, _0, _1):
            return False
        if not self.bind_expression and self.check_alias(state):
            check = self.inner_formula.check(state, _0, _1)
            state.get_aliases().remove(self.bound_variable.name)
            return check
        return self.inner_formula.check(state, _0, _1)

#TODO found for different paths?
class ExistsFormula(lang.ExistsFormula):
    def __init__(self, bound_variable, in_variable, inner_formula, bind_expression=None):
        super().__init__(bound_variable, in_variable, inner_formula, bind_expression)
        
    def check(self, state, adv, grammar_graph) -> bool:
        return self.inner_formula.check(state, adv, grammar_graph)
          
class ConjunctiveFormula(lang.ConjunctiveFormula):
    def check(self, state: State, _0, _1) -> bool:
        return all(formula.check(state, _0, _1) for formula in self.args)
        
class DisjunctiveFormula(lang.DisjunctiveFormula):
    def check(self, state: State, _0, _1) -> bool:
        return any(formula.check(state, _0, _1) for formula in self.args)
        
class NegatedFormula(lang.NegatedFormula):
    def check(self, state: State, _0, _1) -> bool:
        return not self.arg.check(state, _0, _1)
       
class StructuralPredicateFormula(lang.StructuralPredicateFormula):
    def check_before(self, state):
        try:
            return not (state.name == self.args[0].n_type and state.env[self.args[1].name])
        except KeyError:
            return True
                
    def check_after(self, state):
        self.args[0], self.args[1] = self.args[1], self.args[0]
        self.predicate.name = "before"
        return self.check(state)
                
    def check_same_position(self, state):
        if not all(state.is_equivalent(arg) for arg in self.args):
            return False
        return not any(arg in state.env for arg in self.args)
    
    def check_different_position(self, state):
        return not self.check_same_position(state)
    
    def check_inside(self, state):
        pass

    def check(self, state: State, _0, _1) -> bool:
        if not state.name in [arg.n_type for arg in self.args]:
            return True
        if self.predicate.name == "before":
            return self.check_before(state)
        if self.predicate.name == "after": #TODO
            return self.check_before(state)
        if self.predicate.name == "same_position":
            return self.check_same_position(state)
        if self.predicate.name == "different_position":
            return self.check_different_position(state)
        if self.predicate.name == "inside":
            return self.check_inside(state)
        
        
