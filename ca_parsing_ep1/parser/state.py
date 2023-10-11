from ca_parsing_ep1.helpers import update_dict
from isla.parser import State

class State(State):
    def __init__(self, 
                 name,
                 expr, 
                 dot, 
                 s_col, 
                 e_col=None, 
                 aliases=None,
                 ancestors=None,
                 env=None,
                 text=''):
        super().__init__(name, expr, dot, s_col, e_col)
        self.aliases = aliases if aliases else set()
        self.ancestors = ancestors if ancestors else set()
        self.env = env if env else {}
        self.text = text
    
    def copy(self):
        copy = State(self.name, self.expr, self.dot, self.s_col, e_col=self.e_col, 
                     aliases = set(self.aliases), ancestors=set(self.ancestors), 
                     env = dict(self.env), text=self.text)
        return copy
        
    def advance(self, complete_child):
        text = complete_child.text if isinstance(complete_child, State) else complete_child
        adv = State(self.name, self.expr, self.dot + 1, self.s_col, 
                    aliases=set(self.aliases), ancestors=set(self.ancestors), 
                    env=dict(self.env), text=self.text + text)
        return adv
    
    def update_env(self, state):
        if not isinstance(state, State):
            raise TypeError("State must be used to update State env")
        for alias in state.aliases:
            update_dict(self.env, alias, state)

    def add_ancestor(self, ancestor):
        if not isinstance(ancestor, State):
            raise TypeError("Given ancestor must be a State.")
        self.ancestors.add(ancestor)

    def remove_ancestor(self, ancestor):
        if not isinstance(ancestor, State):
            raise TypeError("Given parent must be a State.")
        self.parents.remove(ancestor)
    
    def is_child_of(self, alias):
        return any([alias in ancestor.get_aliases() for ancestor in self.ancestors])
    
    def get_aliases(self):
        return self.aliases