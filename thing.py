#! /usr/bin/env python

# Monte Carlo simulator for The Thing.
# Copyright (C) 2012 Paul Brook 
# Released under the GNU GPL v3.

import random

start_night = True

do_debug = False
#do_debug = True

class GameConfig(object):
    # players is total number of players (including things)
    # start_things is number of things at start of game
    # tie_break is True if ties result in a test
    # bloodlust is probability of humans voting for a test
    # retries is array of number of retries for each round (or 1 if not included)
    def __init__(self, players, start_things, tie_break, bloodlust, retries):
        self.players = players
        self.start_things = start_things
        self.tie_break = 1 if tie_break else 0
        self.bloodlust = bloodlust
        self.retries = retries
    def retry_count(self, n):
        if n >= len(self.retries):
            return 1
        return self.retries[n]

    def __str__(self):
        return "Players: %i Tie_break: %i Start Things: %i Bloodlust: %f Retries: %s" % (self.players, self.tie_break, self.start_things, self.bloodlust, str(self.retries))

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

class Player(object):
    def __init__(self, is_human, config):
        self.type = is_human
        self.is_knowing_thing = False
        self.config = config

    def is_human(self):
        return self.type

    def is_thing(self):
        return not self.type

    def become_thing(self):
        self.type = False
        self.is_knowing_thing = True

    def new_turn(self):
        self.is_knowing_thing = False

    def vote(self, player):
# Always vote
        return True

    def __repr__(self):
        return str(self.type)

class GameState(object):
    def __init__(self, config):
        self.no_players = config.players
        self.players = []
        for x in range(0,config.players):
            self.players.append(Player(True,config))

        for x in range(0,config.start_things):
            self.players[x].become_thing()

    def number_things(self):
        debug(repr(self.players))
        things = 0
        for x in self.players:
            if x.is_thing():
                things+=1
        return things

    def test_for_thing(self, index):
        if self.players[index].is_thing():
            debug("Thing found")
            self.players.pop(index)
            return True
        debug("Human found")
        return False

    def night_phase(self):
        things = self.number_things()
        for x in self.players:
            x.new_turn()
        # Choose new thing from current humans
        new_thing = random.randrange(len(self.players)-things)
        idx = 0
        while new_thing > 0:
            if self.players[idx].is_human():
                new_thing-=1
            else:
                idx +=1
        self.players[idx].become_thing()

    def nominate(self,playerno):
        # Assume that the first and seconding succeds
        debug("Testing player "+str(playerno))
        testing_player = self.players[playerno]
        votes = len(self.players)-1
        votes_yes = 0
        for x in self.players:
            # TODO: Can people vote for themselves?
            if x!=testing_player:
              vote = x.vote(testing_player)
              if vote:
                votes_yes=votes_yes+1
        debug("Vote result %i/%i %f" % (votes_yes, votes, votes_yes/votes))
        if ((votes_yes+config.tie_break) > (votes)/2):
          return self.test_for_thing(playerno)
        # Test did not take place.
        return True

    def run_vote(self):
        return self.nominate(random.randrange(len(self.players)))

    def win_condition(self):
        things = self.number_things()
        if (things == 0):
            debug("Humans win")
            return (True, False)
        if (things * 2 > len(self.players)):
            debug("Things win")
            return (True, True)
        return (False, False)


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

    state = GameState(config)
    rounds = 0
    votes = 0
    while True:
       if votes == 0:
           (win, whowon) = state.win_condition()
           if (win):
                debug("Won "+str(whowon)+" "+str(rounds))
                return (whowon, rounds, state.number_things())
# Night phase
           state.night_phase()
           rounds+=1
           debug( "Round %i" % rounds)
           votes = config.retry_count(rounds)
           debug("At retry "+str(votes))
       if (state.run_vote()==False):
#           print "Votes %i" % votes
           votes = votes-1
       else:
# Check win conditions
           (win, whowon) = state.win_condition()
           if (win):
              debug("Won "+str(whowon)+" "+str(rounds))
              return (whowon, rounds, state.number_things())

        


    return



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

config = GameConfig(10, 2, True, 0.7, [2]*3)
if do_debug==False:
 (percent, hlen, tlen) = montecarlo(config, 5000)
else:
 (percent, hlen, tlen) = montecarlo(config, 1)

print config
print "Humans win %.2f%%" % (percent * 100)
hlen.output()
print "Things"
tlen.output()
