from ca_parsing.isla_formalizations.scriptsizec import (
    SCRIPTSIZE_C_DEF_USE_CONSTR,
    SCRIPTSIZE_C_NO_REDEF_CONSTR)
from ca_parsing.parser.constraint_parser_peg import PEGConstraintParser, PEGConstraintParserParsimonious
from ca_parsing.parser.formula_parser import parse_isla_formula
from fuzzingbook.Timer import Timer
from isla.helpers import srange
from isla.solver import ISLaSolver
from math import inf
import string
from time import time
from statistics import mean, median


class TimeMeasurements:
    def __init__(self, valid_isla, invalid_isla, valid_parser, invalid_parser):
        self.valid_isla = valid_isla
        self.invalid_isla = invalid_isla
        self.valid_parser = valid_parser
        self.invalid_parser = invalid_parser

    def __str__(self):
        def get_time(time_data):
            return [data[1] for data in time_data]
        
        string = "VALID RESULTS:\n"
        for idx, isla_data in enumerate(self.valid_isla):
            parser_data = self.valid_parser[idx]
            test_str, isla_time = isla_data
            assert test_str == parser_data[0]
            parser_time = parser_data[1]

            string += f"Test {idx+1}: '{test_str}': ISLa: {isla_time} | Parser: {parser_time}\n"

        string += "\n"
        string += "INVALID RESULTS:\n"

        for idx, isla_data in enumerate(self.invalid_isla):
            parser_data = self.invalid_parser[idx]
            test_str, isla_time = isla_data
            assert test_str == parser_data[0]
            parser_time = parser_data[1]

            string += f"Test {idx+1}: '{test_str}': ISLa: {isla_time} | Parser: {parser_time}\n"
        
        string += "\n"
        string += "STATISTICS:\n"

        time_valid_isla = get_time(self.valid_isla)
        time_invalid_isla = get_time(self.invalid_isla)
        time_valid_parser = get_time(self.valid_parser)
        time_invalid_parser = get_time(self.invalid_parser)
        string += f"AVERAGE TIME valid ISLa: {mean(time_valid_isla)}\n"
        string += f"MEDIAN TIME valid ISLa: {median(time_valid_isla)}\n"
        string += f"AVERAGE TIME invalid ISLa: {mean(time_invalid_isla)}\n"
        string += f"MEDIAN TIME invalid ISLa: {median(time_invalid_isla)}\n"
        string += "\n"
        string += f"AVERAGE TIME valid parser: {mean(time_valid_parser)}\n"
        string += f"MEDIAN TIME valid parser: {median(time_valid_parser)}\n"
        string += f"AVERAGE TIME invalid parser: {mean(time_invalid_parser)}\n"
        string += f"MEDIAN TIME invalid parser: {median(time_invalid_parser)}\n"
        return string

class TestInputGenerator:
    def __init__(self, 
                 name, 
                 grammar, 
                 complete_formula, 
                 incomplete_formulas, 
                 timeout,
                 max_free_inst,
                 max_smt_inst,
                 cost_computer):
        self.name = name
        self.complete_solver = ISLaSolver(grammar, 
                                          complete_formula, 
                                          max_number_free_instantiations=max_free_inst,
                                          max_number_smt_instantiations=max_smt_inst,
                                          timeout_seconds=60,
                                          cost_computer=cost_computer)
        self.incomplete_solvers = self.init_inv_solvers(grammar, 
                                                        incomplete_formulas,
                                                        timeout,
                                                        max_free_inst,
                                                        max_smt_inst,
                                                        cost_computer)
        self.timeout = timeout

    def init_inv_solvers(self, grammar, formulas, timeout, free, smt, cost_c):
        t = 60
        solvers = [ISLaSolver(grammar, 
                              f,
                              max_number_free_instantiations=free,
                              max_number_smt_instantiations=smt,
                              timeout_seconds=t,
                              cost_computer=cost_c) for f in formulas]
        grammar_fuzzer = ISLaSolver(grammar, timeout_seconds=t)
        return [grammar_fuzzer] + solvers

    
    def generate_valid_inputs(self):
        inp = set()
        t = time()
        while time() - t < self.timeout/2:
            try:
                inp.add(str(self.complete_solver.solve()))
            except TimeoutError:
                pass
            except StopIteration:
                break
        return inp
    
    def generate_invalid_inputs(self, max_len=inf):
        inp = set()
        t = time()
        solvers = list(self.incomplete_solvers)
        while time() - t < self.timeout/2 and len(inp) < max_len:
            solvers_iter = list(solvers)
            for id, solver in enumerate(solvers_iter):
                if isinstance(solver, str):
                    continue
                try:
                    gen_inp = str(solver.solve())
                except TimeoutError:
                    continue
                except StopIteration:
                    if all([isinstance(s, str) for s in solvers]):
                        break
                    idx = solvers.index(solver)
                    solvers[idx] = "StopIteration"
                if not self.complete_solver.check(gen_inp):
                    inp.add((id, gen_inp))
        return inp
    
    def store_inputs(self, valid_inputs, invalid_inputs):
        input_str = "USED FORMULAS:\n"
        input_str += "-------------------------------------------------\n"
        for id, solver in enumerate(self.incomplete_solvers):
            input_str += f"{id} {solver.formula}\n"
            input_str += "-------------------------------------------------\n"
        input_str += "\n"
        input_str += "VALID TEST INPUTS\n"
        for idx, input in enumerate(valid_inputs):
            input_str += f"{idx+1}: '{input}'\n"
        input_str += "-------------------------------------------------\n"
        input_str += "INVALID TEST INPUTS\n"
        for idx, input in enumerate(invalid_inputs):
            input_str += f"{idx+1}: '{input[1]}' | Formula id: {input[0]}\n"
        with open(f"{self.name}_generated_inputs.txt", "w") as file:
            file.write(input_str)

    def generate_and_store(self):
        valid_inputs = self.generate_valid_inputs()
        invalid_inputs = self.generate_invalid_inputs(max_len=len(valid_inputs))
        self.store_inputs(valid_inputs, invalid_inputs)

        invalid_inputs = [i[1] for i in invalid_inputs]
        return valid_inputs, invalid_inputs

#the evaluator takes a grammar and a formula as well as various incomplete formulas
#to first produce passing and failing test inputs. For generating failing inputs,
#an ISLa solver with the formula "true" is always used, which is equivalent to 
#a Grammar Fuzzer. These inputs are stored in a text file along with some information 
#like if they are valid/invalid or which formulas have been used to generate them if they
# are invalid.
#Evaluation results are stored in a seperate file, with data for each test case and
#average/median times as seen in the thesis paper.
#In cases where the parser fails to produce the correct result for an input, data is
#written to a seperate error file. These values are ignored for the evaluation.
#During the evaluation this only happened for the ScriptsizeC Grammar. Nevertheless,
#the vast majority of inputs were still valid.
class Evaluator:
    #name: used as id for files
    #grammar: the grammar
    #c_formula: the full formula
    #parser_class: the parser used for evaluation
    #i_formulas: incomplete formulas used for producing invalid inputs
    #timeout: A upper limit on how long the evaluator produces test inputs
    #max_free_inst, max_smt_inst, cost_computer: like in ISLa
    def __init__(self, 
                 name, 
                 grammar, 
                 c_formula, 
                 parser_class, 
                 i_formulas=None, 
                 timeout=60,
                 max_free_inst=10,
                 max_smt_inst=10,
                 cost_computer=None
                 ):
        self.name = name
        self.grammar = grammar
        self.complete_formula = c_formula
        self.incomplete_formulas = [] if i_formulas is None else i_formulas 
        self.parser_class = parser_class
        self.input_gen = TestInputGenerator(name=name, grammar=grammar, 
                                            complete_formula =c_formula, 
                                            incomplete_formulas=self.incomplete_formulas, 
                                            timeout=timeout,
                                            max_free_inst=max_free_inst,
                                            max_smt_inst=max_smt_inst,
                                            cost_computer=cost_computer)

    def store_result(self, result):
        result_str = "EVALUATION RESULTS\n"
        result_str += str(result)
        with open(f"{self.name}_evaluation_results.txt", "w") as file:
            file.write(result_str)
            
    def evaluate(self):
        valid, invalid = self.input_gen.generate_and_store()
            
        isla = ISLaSolver(self.grammar, self.complete_formula)
        parser = self.parser_class(self.grammar, self.complete_formula)
        result = self.evaluate_one(isla, parser, valid, invalid)
        self.store_result(result)


    def evaluate_one(self, isla, parser, valid_test_inputs, invalid_test_inputs):
        parser_errors = []
        valid_time_isla = []
        valid_time_parser = []
        for i in valid_test_inputs:
            with Timer() as isla_time:
                assert isla.check(i)
            with Timer() as parser_time:
                try:
                    assert parser.check(i)
                except AssertionError:
                    parser_errors.append(("VALID", i))
                    continue
            valid_time_isla.append((i, isla_time.elapsed_time()))
            valid_time_parser.append((i, parser_time.elapsed_time()))
        
        invalid_time_isla = []
        invalid_time_parser = []
        for i in invalid_test_inputs:
            with Timer() as isla_time:
                assert not isla.check(i)
            with Timer() as parser_time:
                try:
                    assert not parser.check(i)
                except AssertionError:
                    parser_errors.append(("INVALID", i))
            invalid_time_isla.append((i, isla_time.elapsed_time()))
            invalid_time_parser.append((i, parser_time.elapsed_time()))
        
        if parser_errors:
            error_str = "Parser check error for following inputs:\n"
            for e in parser_errors:
                error_str += "----------------\n"
                error_str += str(e) + "\n"
                error_str += "----------------\n"
            with open(f"{self.name}_parser_errors.txt", "w") as file:
                file.write(error_str)

        return TimeMeasurements(valid_time_isla, 
                                invalid_time_isla, 
                                valid_time_parser, 
                                invalid_time_parser) 
    
def grammar_order(grammar):
    def sortalts(alts):
        return sorted(alts, key=lambda alt: any(alt in a for a in alts if alt != a))
    for key in grammar.keys():
        grammar[key] = sortalts(grammar[key])

def evaluate_heartbeat():
    grammar = {"<start>": ["<payloadlength> <payload>"],
               "<payloadlength>": ["<number>"],
               "<number>": ["<leaddigit><digits>", "<leaddigit>"],
               "<digits>": ["<digit><digits>", "<digit>"],
               "<payload>": ["<word>"],
               "<word>": ["<char><word>", "<char>"],
               "<leaddigit>": [str(i) for i in range(1, 10)],
               "<digit>": [str(i) for i in range(10)],
               "<char>": [c for c in string.ascii_letters+string.digits]}
           
    formula = 'str.len(<payload>) > 20 and str.to.int(<payloadlength>) = str.len(<payload>)'
    
    incomplete_formula = 'str.len(<payload>) > 50'

    evaluator = Evaluator(name="HEARTBEAT", 
                          grammar=grammar, 
                          c_formula=formula,
                          i_formulas=[incomplete_formula],
                          parser_class=PEGConstraintParserParsimonious, 
                          timeout=60*20,
                          max_free_inst=100,
                          max_smt_inst=100)
    evaluator.evaluate()

def evaluate_csv():
    CSV_GRAMMAR = {
    "<start>": ["<csvfile>"],
    "<csvfile>": ["<csvheader><csvrecords>"],
    "<csvheader>": ["<csvrecord>"],
    "<csvrecords>": ["<csvrecord><csvrecords>", "<csvrecord>"],
    "<csvrecord>": ["<csvstringlist> "],
    "<csvstringlist>": ["<rawfield>", "<rawfield>;<csvstringlist>"],
    "<rawfield>": ["<simplefield>", "<quotedfield>"],
    "<simplefield>": ["<simplecharacters>"],
    "<simplecharacters>": [
        "<simplecharacter><simplecharacters>",
        "<simplecharacter>",
    ],
    "<simplecharacter>": [
        c
        for c in srange(string.ascii_letters) + srange(string.digits)
    ],
    "<quotedfield>": ["|<escapedfield>|"],
    "<escapedfield>": ["<escapedcharacters>"],
    "<escapedcharacters>": ["<escapedcharacter><escapedcharacters>", "<escapedcharacter>"],
    "<escapedcharacter>": [c for c in srange(string.ascii_letters) + srange(string.digits)],
}
    csv_colno_property = """
    exists int num:
        forall <csvrecord> elem in start:
            (str.to.int(num) >= 1 and
            count(elem, "<rawfield>", num))
    """

    csv_colno_property = parse_isla_formula(csv_colno_property, CSV_GRAMMAR)

    evaluator = Evaluator(name="CSV",
                          grammar=CSV_GRAMMAR,
                          c_formula=csv_colno_property,
                          parser_class=PEGConstraintParserParsimonious,
                          timeout=60*20,
                          max_free_inst=10,
                          max_smt_inst=5)
    evaluator.evaluate()

def evaluate_scriptsizec():
    SCRIPTSIZE_C_GRAMMAR = {
    "<start>": ["<statement>"],
    "<statement>": [
        "<block>",
        "<expr>;",
        ";",
    ],
    "<block>": ["{}", "{<statements>}"],
    "<statements>": ["<blockstatement><statements>", "<blockstatement>"],
    "<blockstatement>": ["<statement>", "<declaration>"],
    "<declaration>": ["int <id> = <expr>;", "int <id>;"],
    "<parenexpr>": ["|<expr>|"],
    "<expr>": [
        "<id> = <expr>",
        "<test>",
    ],
    "<test>": [
        "<sum> < <sum>",
        "<sum>",
    ],
    "<sum>": [
        "<term> + <sum>",
        "<term> - <sum>",
        "<term>",
    ],
    "<term>": [
        "<parenexpr>",
        "<id>",
        "<int>",
    ],
    "<id>": srange(string.ascii_lowercase),
    "<int>": [
        "<lead><digits>",
        "<digit>",
    ],
    "<digits>": [
        "<digit><int>",
        "<digit>",
    ],
    "<digit>": srange(string.digits),
    "<lead>": list(set(srange(string.digits)) - {"0"}),
    }

    formula = SCRIPTSIZE_C_DEF_USE_CONSTR & SCRIPTSIZE_C_NO_REDEF_CONSTR
    
    incomplete_formulas = [SCRIPTSIZE_C_DEF_USE_CONSTR, SCRIPTSIZE_C_NO_REDEF_CONSTR]

    evaluator = Evaluator(name="SCRIPTPSIZE",
                          grammar=SCRIPTSIZE_C_GRAMMAR,
                          c_formula=formula,
                          parser_class=PEGConstraintParserParsimonious,
                          timeout=60*20,
                          i_formulas=incomplete_formulas,
                          max_free_inst=10,
                          max_smt_inst=2)
    
    evaluator.evaluate()


if __name__ == "__main__":
    evaluate_heartbeat() 
