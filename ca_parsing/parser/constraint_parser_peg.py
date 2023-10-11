from ca_parsing.parser.formula_parser import parse_isla_formula
from ca_parsing.helpers import remove_brackets
from fuzzingbook.Grammars import RE_NONTERMINAL
from isla.derivation_tree import DerivationTree
from isla.evaluator import evaluate
from isla.parser import PEGParser
from isla.solver import SemanticError
from parsimonious.grammar import Grammar
import re

def evaluate_parse_tree(parse_tree, formula, grammar):
        if isinstance(parse_tree, list):
            derivation_tree = DerivationTree.from_parse_tree(parse_tree[0])
        else:
            derivation_tree = DerivationTree.from_parse_tree(parse_tree)
        return evaluate(formula, derivation_tree, grammar)


#The Parsimonious-based constraint parser. Given a grammar in the dictionary-based
#notation that ISLa uses, this parser translates this grammar into a string that
#Grammar objects in Parsimonious can use. Should this approach fail, one can also
#define a spcific Parsimonious grammar through parsim_grammar, though one has to make sure
#that this grammar produces parse trees that match with the dictionary Grammar.
#At the time of writing, however, this Parser passes all 105 tests in 'test_peg_parser.py'
#without making use of this feature.
class PEGConstraintParserParsimonious:
    def __init__(self, grammar, formula = None, parsim_grammar = None):
        self.dict_grammar = grammar
        self.grammar = Grammar(self.convert_grammar(grammar)) if parsim_grammar is None else parsim_grammar
        self.formula = parse_isla_formula(formula, grammar)

    def convert_grammar(self, grammar):
        
        #workaround since parsimonious seems to skip nonterminals 
        # that can only produce a single nonterminal, e.g. "<start>": ["<number>"]
        def convert_redundant_rules(grammar):
            new_grammar = dict(grammar)
            for rule, alternatives in grammar.items():
                if len(alternatives) == 1 and re.fullmatch(RE_NONTERMINAL, alternatives[0]):
                    new_grammar[rule] = [alternatives[0], alternatives[0]]
            return new_grammar

        def convert_alternative(alt):
            split = [c for c in re.split(RE_NONTERMINAL, alt) if c]
            for idx, s in enumerate(split):
                if re.fullmatch(RE_NONTERMINAL, s):
                    split[idx] = remove_brackets(s)
                else:
                    split[idx] = f'"{s}"'
            return " ".join(split)

        def convert_and_merge(g):
            new_g = dict()
            for rule, alternatives in g.items():
                alts = [convert_alternative(alt) for alt in alternatives if alt]
                while(any(a.startswith(alt) and a != alt for a in alts for alt in alts)):
                    mergable_alts = [alt for alt in alts if any(a.startswith(alt) and a != alt for a in alts)]
                    for m in mergable_alts:
                        if m in alts:
                            alts.remove(m)
                        idx = [alts.index(a) for a in alts if a.startswith(m)]
                        for i in idx:
                            old = alts[i]
                            bracket = f" ({old[len(m):]})?"
                            alts[i] = m + bracket
                alts = [f"({alt})" for alt in alts]
                
                new_g[remove_brackets(rule)] = alts
            return new_g
        
        g = convert_redundant_rules(grammar)
        converted_grammar = convert_and_merge(g)
        pm_grammar = ""
        for rule, alternatives in converted_grammar.items():
            pm_grammar += "\n"
            pm_grammar += f"{rule} = {' / '.join(alternatives)}"
        return pm_grammar
    
    def to_tree(self, parse_res):
        nt_name = f"<{parse_res.expr.name}>" if parse_res.expr.name else ""
        if not parse_res.expr.name:
            if not parse_res.children and parse_res.text:
                return (parse_res.text, [])
            if len(parse_res.children) == 1 and not parse_res.children[0].expr.name:
                return self.to_tree(parse_res.children[0])
            return [self.to_tree(c) for c in parse_res.children] 
        if not parse_res.children:
            return (nt_name, [(parse_res.text, [])])
        children = []
        for c in parse_res.children:
            tree = self.to_tree(c)
            if isinstance(tree, list):
                child_list = [t for t in tree if t]
                for l in [t for t in child_list if isinstance(t, list)]:
                    child_list.remove(l)
                    child_list += l
                children += child_list
            else:
                children.append(tree)
        return (nt_name, children)
    
    def get_tree(self, parse_res):
        tree = self.to_tree(parse_res)
        return ("<start>", [tree]) if not tree[0] == "<start>" else tree
    
    def parse(self, inp):
        try:
            node = self.grammar.parse(inp)
        except:
            raise SyntaxError(f"{inp} has invalid syntax")
        
        parse_tree = self.get_tree(node)
        if not evaluate_parse_tree(parse_tree, self.formula, self.dict_grammar):
                raise SemanticError
        return parse_tree
    
    def check(self, inp):
        try:
            self.parse(inp)
            return True
        except:
            return False

        
#a simple implementation that makes use ISLa's PEG Parser, which itself has been taken
#from 'The Fuzzing Book'.
#This version of PEG comes with the advantage that it uses the same grammar structure
#as ISLa and produces parse trees that ISLa can use for evaluation.
#Due to its recursive implementation, it has in testing often exceeded the recursion limit,
#which is why Parsimonious was chosen as the main PEG-based constraint parser for this thesis, since
#it has frugal RAM usage.
class PEGConstraintParser(PEGParser):
    def __init__(self, grammar, formula = None, starting_symbol = "<start>", **kwargs):
        super().__init__(grammar, **kwargs)
        self.standard_grammar = grammar
        self.starting_symbol = starting_symbol
        self.formula = parse_isla_formula(formula, grammar)
    
    def parse(self, text):
        parse_result = super().parse(text)
        if not evaluate_parse_tree(parse_result, self.formula, self.standard_grammar):
            raise SemanticError
        return parse_result

    def check(self, text):
        try:
            self.parse(text)
            return True
        except:
            return False
