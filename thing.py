#! /usr/bin/env python

# Monte Carlo simulator for The Thing.
# Copyright (C) 2012 Paul Brook 
# Released under the GNU GPL v3.

import random

start_night = True

do_debug = False
#do_debug = True

class GameConfig(object):
    # tie_break is True if ties result in a test
    # bloodlust is probability of humans voting for a test
    def __init__(self, players, tie_break, bloodlust, retries):
	self.players = players
	self.tie_break = 1 if tie_break else 0
	self.bloodlust = bloodlust
	self.retries = retries
    def retry_count(self, n):
	if n >= len(self.retries):
	    return 0
	return self.retries[n]

class Histogram(object):
    def __init__(self):
	self.array = []
	self.total = 0
    def add(self, n):
	if len(self.array) <= n:
	    self.array.extend([0] * (n + 1 - len(self.array)))
	self.array[n] += 1
	self.total += 1
    def output(self):
	ftot = float(self.total)
	for i in xrange(1, len(self.array)):
	    print "%2d: %.2f" % (i, self.array[i] / ftot)

def popcount(v):
    c = 0
    while v:
	v &= v - 1
	c += 1
    return c

def debug(msg, args=()):
    if do_debug:
	print msg % args

# nk is number of knowning things
# nh is number of humans
# Return True if the things won
def play_game(config):
    def random_votes(n):
	res = 0
	while n > 0:
	    if random.random() < config.bloodlust:
		res += 1
	    n -= 1
	return res

    def is_human(n):
	return n >= nt
    def knows_things(n):
	return n < nk

    rounds = 1
    ntot = config.players
    nk = 1
    nt = nk
    if start_night:
	nt += 1
    nh = ntot - nt
    new_round = False
    tested = 0
	
    retry_count = config.retry_count(0)

    while True:
	if (nk * 2) >= ntot:
	    debug("Things win")
	    return (True, rounds, ntot)
	if nt == 0:
	    debug("Humans win")
	    return (False, rounds, ntot)
	if ntot == 2:
	    debug("Tie")
	    return (True, rounds, ntot)
	if new_round:
	    rounds += 1
	    new_round = False
	    if tested > 0:
		tested = 0
		#tested -= 1
	debug("%d things%s, %d humans(%d tested).  Discuss...",
	    (nt, " (1 new)" if nt != nk else "", nh, tested))
	# Pick someone at random to make a nomination
	nom = random.randint(0, ntot - 1)
	if knows_things(nom):
	    if nh == tested:
		# All humans have been tested
		test = random.randint(0, nt - 1)
	    else:
		# Pick a human
		test = nt
	else:
	    # Pick at random
	    test = random.randint(0, ntot - (2 + tested))
	    if test >= nom:
		test += 1

	debug("%d nominated %d", (nom, test))
	if is_human(test):
	    # Knowing things vote yes
	    # Everyone else votes randomly
	    yes = nk + random_votes(ntot - (nk + 1))
	elif knows_things(test):
	    # Knowing things vote no
	    # Everyone else votes randomly
	    yes = random_votes(ntot - nk)
	else: # New thing noninated
	    # Knowing things vote no
	    # Humans vote randomly
	    yes = random_votes(nh)
	debug("%d votes", yes)
	if (yes * 2) + config.tie_break <= ntot:
	    debug("Vote failed")
	    # Vote failed.  Go again.
	    continue
	# Vote passed
	if is_human(test):
	    debug("Tested Human")
	    tested += 1
	    if retry_count > 0:
		debug("Retry")
		retry_count -= 1;
	    else:
		debug("End of Round %d", (rounds))
		# End of round
		nk = nt
		nt = nk + 1
		nh -= 1
		retry_count = config.retry_count(rounds)
		new_round = True
	elif knows_things(test):
	    debug("Flushed Thing")
	    nk -= 1
	    nt -= 1
	    ntot -= 1
	    retry_count = 0
	else: # New thing
	    debug("Flushed new Thing")
	    nt -= 1
	    ntot -= 1
	    retry_count = 0

def montecarlo(config, niter):
    human = 0
    thing = 0
    hlen = Histogram()
    tlen = Histogram()
    for i in xrange(0, niter):
	(won, rounds, left) = play_game(config)
	if won:
	    thing += 1
	    tlen.add(rounds)
	else:
	    human += 1
	    hlen.add(rounds)
    return (human / float(human + thing), hlen, tlen)

config = GameConfig(10, True, 0.7, [2, 2, 2, 1, 1])
(percent, hlen, tlen) = montecarlo(config, 5000)
print "Humans win %.2f" % percent
hlen.output()
print
tlen.output()
