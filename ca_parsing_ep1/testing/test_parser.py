from ca_parsing_ep1.parser.constraint_parser import ConstraintParser
from html import escape
from isla.helpers import srange
from isla.parser import EarleyParser
from isla.solver import ISLaSolver
import string
import unittest

LANG_GRAMMAR = {"<start>": ["<stmt>"],
               "<stmt>": ["<assgn>", "<assgn>; <stmt>"],
               "<assgn>": ["<var> := <rhs>"],
               "<rhs>": ["<var>", "<digit>"],
               "<var>": [c for c in string.ascii_lowercase],
               "<digit>": [c for c in string.digits]}
               
CONFIG_GRAMMAR = {"<start>": ["<config>"],
                  "<config>": ["pagesize=<pagesize>\nbufsize=<bufsize>"],
                  "<pagesize>": ["<int>"],
                  "<bufsize>": ["<int>"],
                  "<int>": ["<leaddigit><digits>"],
                  "<digits>": ["", "<digit><digits>"],
                  "<digit>": [c for c in string.digits],
                  "<leaddigit>": [c for c in string.digits[1:]]}
                  

XML_GRAMMAR = {
    "<start>": ["<xml-tree>"],
    "<xml-tree>": [
        "<xml-open-tag><inner-xml-tree><xml-close-tag>",
        "<xml-openclose-tag>",
    ],
    "<inner-xml-tree>": [
        "<xml-tree><inner-xml-tree>",
        "<xml-tree>",
        "<text>",
    ],
    "<xml-open-tag>": ["<<id> <xml-attribute>>", "<<id>>"],
    "<xml-openclose-tag>": ["<<id> <xml-attribute>/>", "<<id>/>"],
    "<xml-close-tag>": ["</<id>>"],
    "<xml-attribute>": ["<xml-attribute> <xml-attribute>", '<id>="<text>"'],
    "<id>": [
        "<id-start-char><id-chars>",
        "<id-start-char>",
    ],
    "<id-start-char>": srange("_" + string.ascii_letters),
    "<id-chars>": ["<id-char><id-chars>", "<id-char>"],
    "<id-char>": ["<id-start-char>"] + srange("-." + string.digits),
    "<text>": ["<text-char><text>", "<text-char>"],
    "<text-char>": [
        escape(c)
        for c in srange(string.ascii_letters + string.digits + "\"'. \t/?-,=:+")
    ],
}

SSC_GRAMMAR = SCRIPTSIZE_C_GRAMMAR = {
    "<start>": ["<statement>"],
    "<statement>": [
        "<block>",
        "if<paren_expr> <statement> else <statement>",
        "if<paren_expr> <statement>",
        "while<paren_expr> <statement>",
        "do <statement> while<paren_expr>;",
        "<expr>;",
        ";",
    ],
    "<block>": ["{<statements>}"],
    "<statements>": ["<block_statement><statements>", ""],
    "<block_statement>": ["<statement>", "<declaration>"],
    "<declaration>": ["int <id> = <expr>;", "int <id>;"],
    "<paren_expr>": ["(<expr>)"],
    "<expr>": [
        "<id> = <expr>",
        "<test>",
    ],
    "<test>": [
        "<sum> < <sum>",
        "<sum>",
    ],
    "<sum>": [
        "<sum> + <term>",
        "<sum> - <term>",
        "<term>",
    ],
    "<term>": [
        "<paren_expr>",
        "<id>",
        "<int>",
    ],
    "<id>": srange(string.ascii_lowercase),
    "<int>": [
        "<digit_nonzero><digits>",
        "<digit>",
    ],
    "<digits>": [
        "<digit><int>",
        "<digit>",
    ],
    "<digit>": srange(string.digits),
    "<digit_nonzero>": list(set(srange(string.digits)) - {"0"}),
}

class ConstraintParserTest(object):
    grammar: dict
    formula: str
    
    def setUp(self):
        #self.isla = ISLaSolver(self.grammar, self.formula)
        self.constraint = ConstraintParser(self.grammar, formula = self.formula)
        self.earley = EarleyParser(self.grammar)
        
    @classmethod
    def setUpClass(cls):
        cls.constraint = ConstraintParser(cls.grammar, formula = cls.formula)
        cls.earley = EarleyParser(cls.grammar)
        
    def assertCorrect(self, inp):
        #self.assertTrue(self.isla.check(inp))
        self.assertEqual(next(self.constraint.parse(inp)), next(self.earley.parse(inp)))
        
    def assertSemanticError(self, inp):
        self.assertTrue(next(self.earley.parse(inp)))
        #self.assertFalse(self.isla.check(inp))
        with self.assertRaises(SyntaxError):
            next(self.constraint.parse(inp))
            
class FalseTest(ConstraintParserTest, unittest.TestCase):
    grammar = LANG_GRAMMAR
    formula = "false"
    
    def test_simple_false(self):
        self.assertSemanticError("a := 1")
        
        
class SimpleConfigTest(ConstraintParserTest, unittest.TestCase):
    grammar = CONFIG_GRAMMAR
    formula = "<pagesize> = <bufsize>"
    
    def test_config_1(self):
        self.assertCorrect("pagesize=12\nbufsize=12")
    
    def test_config_2(self):
        self.assertSemanticError("pagesize=12\nbufsize=1212")  
        
class ConfigLeaddigitDigitEqualityTest(ConstraintParserTest, unittest.TestCase):
    grammar = CONFIG_GRAMMAR
    formula = 'forall <int> i="<leaddigit><digit>" in <start>: (i = "7")'
    
    def test_leaddigit_digit_config_1(self):
        self.assertCorrect("pagesize=1\nbufsize=7")
    
    def test_leaddigit_digit_config_2(self):
        self.assertCorrect("pagesize=7\nbufsize=1")
        
    def test_leaddigit_digit_config_3(self):
        self.assertCorrect("pagesize=1\nbufsize=2")
        
    def test_leaddigit_digit_config_4(self):
        self.assertSemanticError("pagesize=7\nbufsize=72")
    
    def test_leaddigit_digit_config_4(self):
        self.assertSemanticError("pagesize=72\nbufsize=7")    
        
class SimpleXPathTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num>"], 
               "<num>": ["1", "<zeros>"],
               "<zeros>": ["0<zeros>", "0"]}
    formula = """
    str.len(<num>.<zeros>) = 3
    """
    
    def test_simple_xpath_1(self):
        self.assertCorrect("000")
        
    def test_simple_xpath_2(self):
        self.assertCorrect("1") 
        
    def test_simple_xpath_3(self):
        self.assertSemanticError("00") 

class InMatchExpressionTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> <nums>"], 
               "<nums>": ["<num><nums>", "<num>"],
               "<num>": [str(i) for i in range(10)]}
    
    formula = """
    forall <nums> nums="<num>{<nums> n1}":
        forall <num> in nums:
            str.to.int(<num>) = 1
    """

    def test_in_match_1(self):
        self.assertCorrect("1 11")

    def test_in_match_2(self):
        self.assertCorrect("9 11")

    def test_in_match_3(self):
        self.assertCorrect("1 9")

    def test_in_match_4(self):
        self.assertSemanticError("1 91")

    def test_in_match_5(self):
        self.assertSemanticError("1 19")

class XMLTest(ConstraintParserTest, unittest.TestCase):
    grammar = XML_GRAMMAR
    formula = """
    forall <xml-tree> tree="<{<id> opid}[ <xml-attribute>]><inner-xml-tree></{<id> clid}>" in start:
        (= opid clid)
    """
        
    def test_xml_1(self):
        self.assertCorrect("<x>Y</x>")
        
    def test_xml_2(self):
        self.assertSemanticError("<x>Y</z>")

class SimpleForallTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<A> + <B>"], "<A>": ["a<A>", "a"], "<B>": ["b<A>", "b"]}
    formula = """
    forall <B>:
        str.len(<B>) = 3
    """
    
    def test_simple_forall1(self):
        self.assertCorrect("aa + baa")
    
    def test_simple_forall2(self):
        self.assertSemanticError("aa + ba")
    
class SimpleInVariableTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> + <B>"], "<num>": ["0", "1"], "<B>": ["<num>"]}
    formula = """
    forall <num> in <B>:
        str.to.int(<num>) = 0
    """
    
    def test_simple_in_variable1(self):
        self.assertCorrect("0 + 0")
        
    def test_simple_in_variable2(self):
        self.assertCorrect("1 + 0")
        
    def test_simple_in_variable3(self):
        self.assertSemanticError("0 + 1")


        
class SimpleConjunctiveTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<number>"], "<number>": ["<nums>"], 
               "<nums>": ["<num><nums>", "<num>"], "<num>": [str(i) for i in range(10)]}
    formula = """
    str.to.int(<number>) = 10 and str.len(<number>) = 2
    """
    
    def test_simple_conjunction1(self):
        self.assertCorrect("10")
        
    def test_simple_conjunction2(self):
        self.assertSemanticError("010")
        
    def test_simple_conjunction3(self):
        self.assertSemanticError("42")
        
    def test_simple_conjunction4(self):
        self.assertSemanticError("100")

class NamedInVariablesTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> <float>"], 
               "<num>": ["<float>", "<digit>"],
               "<digit>": [str(i) for i in range(10)],
               "<float>": ["<digit>.<digit>"]}
    
    formula = """
    forall <num> n:
        forall <float> f1 in n:
            forall <digit> d1 in f1:
                str.to.int(d1) < 5
    and
    forall <digit> d2:
        str.to.int(d2) < 9
    """

    def test_named_variables_1(self):
        self.assertCorrect("1 1.1")

    def test_named_variables_2(self):
        self.assertCorrect("4.1 8.8")

    def test_named_variables_3(self):
        self.assertSemanticError("4 9.0")

    def test_named_variables_4(self):
        self.assertSemanticError("1.5 1.5")

class ManyVariablesTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> <a> <b> <a> <b>"], 
               "<num>": ["1<digit>", "2<digit>"],
               "<digit>": [str(i) for i in range(10)],
               "<a>": ["aa", "a"],
               "<b>": ["bb", "b"]}
    
    formula = """
    forall <num> in <start>:
        forall <a> in <start>:
            forall <b> in <start>:
                forall <digit> in <num>: (
                    str.to.int(<num>) > 20 and str.to.int(<digit>) > 5 and
                    str.len(<a>) = 1 and str.len(<b>) = 2)
    """

    def test_many_variables_1(self):
        self.assertCorrect("29 a bb a bb")

    def test_many_variables_2(self):
        self.assertSemanticError("19 a bb a bb")

    def test_many_variables_3(self):
        self.assertSemanticError("25 a bb a bb")

    def test_many_variables_4(self):
        self.assertSemanticError("29 aa bb a bb")

    def test_many_variables_5(self):
        self.assertSemanticError("29 a b a bb")

    def test_many_variables_6(self):
        self.assertSemanticError("29 a bb aa bb")

    def test_many_variables_7(self):
        self.assertSemanticError("29 a bb a b")

class SimpleExistsTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> + <B>"], "<num>": ["0", "1"], "<B>": ["<num>"]}
    formula = """
    exists <num> in <B>:
        str.to.int(<num>) = 1
    """
    
    def test_simple_exists1(self):
        self.assertCorrect("1 + 1")
        
    def test_simple_exists2(self):
        self.assertCorrect("0 + 1")
        
    def test_simple_exists3(self):
        self.assertSemanticError("1 + 0")
        
    def test_simple_exists4(self):
        self.assertSemanticError("0 + 0")
        
class MultipleExistTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> + <A> + <B> + <num>" ], "<num>": ["0", "1"], "<A>": ["<num>"], "<B>": ["b<num>"]}
    formula = """
    exists <num> in <start>:
        str.to.int(<num>) = 1
    """
    
    def test_multiple_exists1(self):
        self.assertCorrect("1 + 0 + b0 + 0")
        
    def test_multiple_exists2(self):
        self.assertCorrect("0 + 0 + b0 + 1")
        
    def test_multiple_exists3(self):
        self.assertCorrect("0 + 1 + b0 + 0")
    
    def test_multiple_exists4(self):
        self.assertCorrect("0 + 0 + b1 + 0")
        
    def test_multiple_exists5(self):
        self.assertSemanticError("0 + 0 + b0 + 0")
        
        
class HeartbeatTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["(<payload-length>)<payload>"],
               "<payload-length>": ["<number>"],
               "<number>": ["<leaddigit><digits>", "<leaddigit>"],
               "<digits>": ["<digit><digits>", "<digit>"],
               "<payload>": ["<word>"],
               "<word>": ["<char><word>", "<char>"],
               "<leaddigit>": [str(i) for i in range(1, 10)],
               "<digit>": [str(i) for i in range(10)],
               "<char>": [c for c in string.printable]}
    formula = "str.to.int(<payload-length>) = str.len(<payload>)"
    
    def test_heartbeat1(self):
        self.assertCorrect("(7)testing")
    
    def test_heartbeat2(self):
        for i in range(1, 7):
            self.assertSemanticError(f"({i})testing")
        for i in range(8, 21):
            self.assertSemanticError(f"({i})testing")
            
    def test_heartbeat3(self):
        self.assertCorrect("(10)xyz123456u")
        
class ForallMultipleFreeVariablesTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<A> <B> <C> <A> <B>"],
               "<A>": ["aa", "a"],
               "<B>": ["bb", "b"],
               "<C>": ["c<A>c", "c<B>c"]}
    formula = "str.len(<A>) = str.len(<B>)"
    
    def test_forall_multiple_free_vars_test1(self):
        self.assertCorrect("a b cac a b")
    
    def test_forall_multiple_free_vars_test2(self):
        self.assertCorrect("aa bb cbbc aa bb")
        
    def test_forall_multiple_free_vars_test3(self):
        self.assertSemanticError("a b cac a bb")   
    
    def test_forall_multiple_free_vars_test4(self):
        self.assertSemanticError("aa b cac a b") 
        
    def test_forall_multiple_free_vars_test5(self):
        self.assertSemanticError("a b cbbc a b")
        
class AssignmentProgramTest(ConstraintParserTest, unittest.TestCase):
    grammar = LANG_GRAMMAR
               
    formula = """
    forall <assgn> assgn:
        exists <assgn> decl:
            (before(decl, assgn) and assgn.<rhs>.<var> = decl.<var>)
    """
    
    def test_assignment_program_1(self):
        self.assertCorrect("a := 1")
    
    def test_assignment_program_2(self):
        self.assertCorrect("a := 1; b := 2; c := 1")
        
    def test_assignment_prgram_3(self):
        self.assertCorrect("a := 1; b := 2; a := 1")
        
    def test_assignment_program_4(self):
        self.assertCorrect("a := 1; b := a; c := a")
        
    def test_assignment_program_5(self):
        self.assertSemanticError("a := a")
        
    def test_assignment_program_6(self):
        self.assertSemanticError("a := b")   
        
    def test_assignment_program_5(self):
        self.assertSemanticError("a := 1; b := c; c := 3") 
        
class ReverseAssignmentProgramTest(ConstraintParserTest, unittest.TestCase):
    grammar = LANG_GRAMMAR
               
    formula = """
    forall <assgn> assgn:
        exists <assgn> decl:
            (after(decl, assgn) and assgn.<rhs>.<var> = decl.<var>)
    """
    
    def test_rev_assignment_program_1(self):
        self.assertCorrect("a := 1")
    
    def test_rev_assignment_program_2(self):
        self.assertCorrect("a := 1; b := 2; c := 1")
        
    def test_rev_assignment_prgram_3(self):
        self.assertCorrect("a := 1; b := 2; a := 1")
        
    def test_rev_assignment_program_4(self):
        self.assertCorrect("a := b; b := c; c := 1")
        
    def test_rev_assignment_program_5(self):
        self.assertSemanticError("a := a")
        
    def test_rev_assignment_program_6(self):
        self.assertSemanticError("a := b")   
        
    def test_rev_assignment_program_5(self):
        self.assertSemanticError("a := 1; b := a; c := 3")
        
class BeforeTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> <mid_num> <num>"],
               "<mid_num>": ["<num>"],
               "<num>": [str(i) for i in range(10)]}
    
    formula = """
    forall <num>:
        (before(<num>, <mid_num>) or <num> = <mid_num>)
    """
    
    def test_before_1(self):
        self.assertCorrect("0 0 0")
        
    def test_before_2(self):
        self.assertCorrect("1 0 0")
        
    def test_before_3(self):
        self.assertSemanticError("0 0 1")

class AfterTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num> <mid_num> <num>"],
               "<mid_num>": ["<num>"],
               "<num>": [str(i) for i in range(10)]}
    
    formula = """
    forall <num>:
        (after(<num>, <mid_num>) or <num> = <mid_num>)
    """
    
    def test_after_1(self):
        self.assertCorrect("0 0 0")
        
    def test_after_2(self):
        self.assertCorrect("0 0 1")
        
    def test_after_3(self):
        self.assertSemanticError("1 0 0")
        
class ConsecutiveTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num><seq><num>;<seq>"],
               "<num>": [str(i) for i in range(10)],
               "<seq>": ["<num><num>"]}
               
    formula = """
    exists <num> num:
        exists <seq> seq:
            (consecutive(num, seq) and str.to.int(num) + 10 = str.to.int(seq))
    """
    
    def test_consecutive_1(self):
        self.assertCorrect("1111;11")
        
    def test_consecutive_2(self):
        self.assertCorrect("1110;00")
        
    def test_consecutive_3(self):
        self.assertSemanticError("0111;00")
        
    def test_consecutive_3(self):
        self.assertSemanticError("0001;11")
        
class SamePositionTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num><num><num><num>"],
               "<num>": [str(i) for i in range(10)]}
               
    formula = """
    forall <num> num1:
        forall <num> num2:
            (same_position(num1, num2) or not str.to.int(num1) = str.to.int(num2))
    """
    
    def test_same_pos_1(self):
        self.assertCorrect("1234")
        
    def test_same_pos_2(self):
        self.assertCorrect("5296")
      
    def test_same_pos_3(self):
        self.assertSemanticError("1111")
        
    def test_same_pos_4(self):
        self.assertSemanticError("5295")
        
class DifferentPositionTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<num><num><num><num>"],
               "<num>": [str(i) for i in range(10)]}
               
    formula = """
    forall <num> num1:
        exists <num> num2:
            (different_position(num1, num2) and str.to.int(num1) = str.to.int(num2))
    """
    
    def test_same_pos_1(self):
        self.assertCorrect("1111")
        
    def test_same_pos_2(self):
        self.assertCorrect("5252")
      
    def test_same_pos_3(self):
        self.assertSemanticError("1234")
        
    def test_same_pos_4(self):
        self.assertSemanticError("5297")
        
class DirectChildTest(ConstraintParserTest, unittest.TestCase):
    grammar = LANG_GRAMMAR
    
    formula = """
    forall <var>:
        exists <assgn>:
            (direct_child(<var>, <assgn>) or <var> = "a")
    """
    
    def test_direct_child_1(self):
        self.assertCorrect("x := 1")
    
    def test_direct_child_2(self):
        self.assertCorrect("x := a; a := a")

    def test_direct_child_3(self):
        self.assertCorrect("x := a; b := 1; y := a")
        
    def test_direct_child_4(self):
        self.assertSemanticError("x := b; b := 1; a := c")
        
    def test_direct_child_5(self):
        self.assertSemanticError("a := b")
        
class InsideTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<seq1> <num> <seq2>"],
               "<seq1>": ["<num><num>"],
               "<seq2>": ["<num><seq1>"],
               "<num>": [str(i) for i in range(10)]}
               
    formula = """
    forall <num>:
        inside(<num>, <seq2>) or <num> = "0")
    """
               
    def test_inside_1(self):
        self.assertCorrect("00 0 000")
        
    def test_inside_2(self):
        self.assertSemanticError("00 0 123") 
        
    def test_inside_3(self):
        self.assertSemanticError("10 0 000")
        
    def test_inside_4(self):
        self.assertSemanticError("00 1 000")
        
class NthTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<seq1> <num> <seq2>"],
               "<seq1>": ["<num><num>"],
               "<seq2>": ["<num><seq1>"],
               "<num>": [str(i) for i in range(10)]}
               
    formula = """
    exists <num>:
        nth("2", <num>, <seq2>) and <num> = "1")
    """
        
    def test_nth_1(self):
        self.assertCorrect("11 1 111")
        
    def test_nth_2(self):
        self.assertSemanticError("01 0 000")
        
    def test_nth_3(self):
        self.assertSemanticError("00 0 100")
        
    def test_nth_4(self):
        self.assertSemanticError("00 0 001")

#TODO ssc_grammar peg friendly
 
class LevelTest(ConstraintParserTest, unittest.TestCase):
    grammar= {'<start>': ['<numblock>'], 
              '<numblock>': ['<nums><block>', "<nums>"], 
              '<nums>': ['<num><nums>', '<num>'], 
              '<num>': ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], 
              '<block>': ['(<numblock>)']}

    
    formula = """
    exists <num> n1:
        exists <num> n2:
            (level("EQ", "<block>", n1, n2) and different_position(n1, n2) and n1 = n2)
    """

    
    def test_level_1(self):
        self.assertCorrect("11")

    def test_level_2(self):
        self.assertCorrect("1(22)")
        
    def test_level_3(self):
        self.assertCorrect("1(1(343))")
        
    def test_level_4(self):
        self.assertSemanticError("1(2(3))")
        
    def test_level_5(self):
        self.assertSemanticError("(1(1(1(1(1)))))")
      
class CountTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<nums>"], 
               "<nums>": ["<num><nums>", "<num>"],
               "<num>": [str(i) for i in range(10)]}
               
    formula = """
    exists <nums>:
        count(<nums>, "<num>", "4")
    """
    
    def test_count_1(self):
        self.assertCorrect("1234")
        
    def test_count_2(self):
        self.assertCorrect("12345")
        
    def test_count_3(self):
        self.assertSemanticError("123")

class VarTest(ConstraintParserTest, unittest.TestCase):
    grammar = {"<start>": ["<a> <b> <a> <b>"],
               "<a>": ["<num>"],
               "<b>": ["<num>"],
               "<num>": ["<digit><num>", "<digit>"],
               "<digit>": ["1", "2", "3"]}
    
    formula = """
    not str.to.int(<a>) = str.to.int(<b>)
    """

    def test_var(self):
        self.assertCorrect("12 123 1 1231")
        

if __name__ == "__main__":
    unittest.main()
