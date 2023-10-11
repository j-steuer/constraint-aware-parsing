from ca_parsing_ep2.formula.formulas import *
from isla.language import parse_isla
from isla.isla_predicates import STANDARD_STRUCTURAL_PREDICATES, STANDARD_SEMANTIC_PREDICATES
import isla.isla_shortcuts as sc

lang.SMTFormula = SMTFormula
lang.ForallFormula = ForallFormula   
lang.ConjunctiveFormula = ConjunctiveFormula 
lang.DisjunctiveFormula = DisjunctiveFormula
lang.StructuralPredicateFormula = StructuralPredicateFormula   
lang.ForallFormula = ForallFormula
lang.ExistsFormula = ExistsFormula

def parse_isla_formula(inp,
                       grammar, 
                       structural_predicates=STANDARD_STRUCTURAL_PREDICATES,
                       semantic_predicates=STANDARD_SEMANTIC_PREDICATES):
    if inp is None:
        return sc.true()
    if isinstance(inp, Formula):
        return inp
    
    return parse_isla(inp, grammar, structural_predicates, semantic_predicates)
