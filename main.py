import cellpylib as cpl
import numpy as np

cellular_automaton = np.array([[0,0,1,0,0]])

cellular_automaton = cpl.evolve(cellular_automaton, timesteps=5,
memoize=True,
apply_rule=lambda n, c, t: cpl.nks_rule(n, 110))

cpl.plot(cellular_automaton)