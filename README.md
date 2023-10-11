Code for the bachelor's thesis "Constraint-Aware Parsing".

ca-parsing: The PEG implementation

ca-parsing_ep1: The incomplete Earley Parser implementation that creates parse trees during runtime to evaluate them with ISLa

ca-parsing_ep2: The incomplete Earley Parser implementation that uses its own evaluation methods for each formula class


For ca-parsing, the evaluation_results directory includes the evaluation results cited in the thesis paper, which have
been created by running the evaluation methods in evaluator.py.

Both ca-parsing_ep1 and ep2 include a small heartbeat test file which shows that both implementations are inefficient compared to ISLa (while both implementations are incomplete and do not match ISLa in functionality, both are capable of processing simple
constraints like the heartbeat constraint).


To use any of the parsers, their respective directories have to be placed in python's site-packages.


The isla_formalizations and isla_evaluations directory and their contents belong to ISLa.
