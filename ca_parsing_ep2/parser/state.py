from ca_parsing_ep2.formula.alias import Alias, AliasFinder
from isla.parser import State
from ca_parsing.helpers import update_dict

class State(State):
    def __init__(self, 
                 name,
                 expr, 
                 dot, 
                 s_col, 
                 e_col=None, 
                 parents=None,
                 children=None,
                 env=None,
                 text=''):
        super().__init__(name, expr, dot, s_col, e_col)
        self.aliases = {"assigned": [], "bind": []}
        self.parents = parents if parents else set()
        self.children = children if children else []
        self.env = env if env else {}
        self.text = text
    
    def copy(self):
        copy = State(self.name, self.expr, self.dot, self.s_col, e_col=self.e_col, 
                     parents=set(self.parents), children=list(self.children), 
                     env=dict(self.env), text=self.text)
        copy.aliases = dict(self.aliases)
        return copy
        
    def advance(self, complete_child):
        text = complete_child.text if isinstance(complete_child, State) else complete_child
        adv = State(self.name, self.expr, self.dot + 1, self.s_col, 
                    parents=set(self.parents), children=list(self.children),
                    env=dict(self.env), text=self.text + text)
        adv.aliases = dict(self.aliases)
        adv.add_child(complete_child)
        return adv
                     
    def update_env(self, state):
        if not isinstance(state, State):
            raise TypeError("Only states can be used to update State environment.")
        for alias in state.get_aliases():
            update_dict(self.env, alias.name, state.text)

    def add_parent(self, parent_state):
        if not isinstance(parent_state, State):
            raise TypeError("Given parent must be a State.")
        self.parents.add(parent_state)

    def remove_parent(self, parent_state):
        if not isinstance(parent_state, State):
            raise TypeError("Given parent must be a State.")
        self.parents.remove(parent_state)

    def add_alias(self, alias, bind=False):
        if not isinstance(alias, Alias):
            raise TypeError("Given value must be Alias.")
        if bind:
            self.aliases["bind"].append(alias)
        else:
            self.aliases["assigned"].append(alias)

    def add_child(self, child):
        if not isinstance(child, (State, str)):
            raise TypeError("Child must be a literal string or a State representing a nonterminal")
        self.children.append(child)

        #unittest TODO remove
        if self.expr is None:
            return
        #sanity check
        assert len(self.children) <= len(self.expr)
        for idx, child in enumerate(self.children):
            if isinstance(child, str):
                assert child == self.expr[idx]
            else:
                assert child.name == self.expr[idx]

    def all_children_of(self, nonterminal=None):
        state_children = [child for child in self.children if isinstance(child, State)]

        result = []
        for child in state_children:
            if nonterminal is None or child.name == nonterminal:
                result.append(child)
            result += child.all_children_of(nonterminal)
        return result
    
    def is_equivalent(self, nonterminal):
        if self.name == nonterminal:
            return True
        
        if not self.children or any(isinstance(child, str) and child for child in self.children):
            return False
        
        if len(self.children) == 1:
            eq_child = self.children[0]
        else:
            eq_child = [child for child in self.children if isinstance(child, State) and child.text]
            if len(eq_child) != 1:
                return False
            eq_child = eq_child[0]
        return eq_child.is_equivalent(nonterminal)
    
    def is_child_of(self, alias):
        return any([alias in parent.get_aliases() for parent in self.parents])
    
    def get_aliases(self):
        return list(self.aliases["assigned"])
    
    def get_bound_aliases(self):
        return list(self.aliases["bind"])
    
    def move_bound_alias(self, alias):
        if alias in self.aliases["bind"]:
            move_alias = self.aliases["bind"][self.aliases["bind"].index(alias)]
            self.add_alias(move_alias)
            self.aliases["bind"].remove(move_alias)

    def add_match_alias(self, name):
        self.add_alias(Alias(name, "f"))

    def update_alias(self, formula):
        finder = AliasFinder(formula)
        finder.set_aliases(self)
