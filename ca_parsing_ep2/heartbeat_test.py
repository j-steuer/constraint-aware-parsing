from ca_parsing_ep2.parser.constraint_parser import ConstraintParser
from fuzzingbook.Timer import Timer
from isla.solver import ISLaSolver
from string import printable

grammar = {"<start>": ["<payload-length> <payload>"],
               "<payload-length>": ["<number>"],
               "<number>": ["<leaddigit><digits>", "<leaddigit>"],
               "<digits>": ["<digit><digits>", "<digit>"],
               "<payload>": ["<word>"],
               "<word>": ["<char><word>", "<char>"],
               "<leaddigit>": [str(i) for i in range(1, 10)],
               "<digit>": [str(i) for i in range(10)],
               "<char>": [c for c in printable]}
           
constraint = '''
str.to.int(<payload-length>) = str.len(<payload>)
'''

def test():
    parser = ConstraintParser(grammar, constraint)
    isla = ISLaSolver(grammar, constraint)
    inp = "200 " + "xy"*100
    with Timer() as tparse:
        next(parser.parse(inp))
    with Timer() as tisla:
        isla.check(inp)
    print("PARSER:", tparse.elapsed_time())
    print("ISLA:", tisla.elapsed_time())     

if __name__ == "__main__":
    test()
    
