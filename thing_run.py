#! /usr/bin/env python

# Monte Carlo simulator for The Thing.
# Copyright (C) 2012 Paul Brook, Jen Freeman
# Released under the GNU GPL v3.

import random,sys

start_night = True

if len(sys.argv) <2:
   print "thing.py <runs>"
   sys.exit(1)

runs = int(sys.argv[1])
if runs == 1:
   do_debug = True
else:
   do_debug = False

class GameConfig(object):
    # players is total number of players (including things)
    # start_things is number of things at start of game
    # tie_break is True if ties result in a test
    # bloodlust_human is probability of humans voting for a test - 1 for always
    # bloodlust_thing is probability of things voting for a test for a human - 1 for always
    # cannibalism is probability of things voting for a thing to be tested - 1 for always
    # retries is array of number of retries for each round (or 1 if not included)
    # prob_weight_nominate is the weight taking the probabilities into account when nominating (+1 for always -1 for never)
    # prob_weight_things is the weight things take the probabilites into account when thinging (+1 is always choose the highest probability, -1 for never choose the highest probability)
    def __init__(self, players, start_things, tie_break, bloodlust_human, bloodlust_thing, cannibalism, retries, prob_weight_nominate, prob_weight_things):
        self.players = players
        self.start_things = start_things
        self.tie_break = 1 if tie_break else 0
        self.bloodlust_human = bloodlust_human
        self.bloodlust_thing = bloodlust_thing
        self.cannibalism = cannibalism
        self.retries = retries
        self.prob_weight_nominate = prob_weight_nominate
        self.prob_weight_things = prob_weight_things
    def retry_count(self, n):
        if n >= len(self.retries):
            return 1
        return self.retries[n]

    def __str__(self):
        return "Players: %i Tie_break: %i Start Things: %i Human Bloodlust: %f ThingBloodlust: %f Thing Cannibalism: %f Retries: %s" % (self.players, self.tie_break, self.start_things, self.bloodlust_human, self.bloodlust_thing, self.cannibalism, str(self.retries))

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
        self.probability = config.start_things / float(config.players)
        self._is_tested = False

    def is_human(self):
        return self.type

    def is_thing(self):
        return not self.type

    def is_tested(self):
        return self._is_tested

    def become_thing(self):
        self.type = False
        self.is_knowing_thing = True

    def new_turn(self, players):
        self._is_tested = False
        self.is_knowing_thing = False
        self.probability += (1.0/players)

    def test(self):
        self.probability = 0
        self._is_tested = True
        return self.is_thing()
        
    def vote(self, player):
        prob = 1
        if self.is_human():
            prob = config.bloodlust_human
        elif self.is_knowing_thing:
            # New thing votes the same as a human
            prob = config.bloodlust_human
        elif player.is_thing():
            prob = config.cannibalism
        else:
            prob = config.bloodlust_thing
        if random.random() < prob:
            return True
        return False

# Always vote yes
#        return True

    def __repr__(self):
        return "%s %f" % (str(self.type),self.probability)

class GameState(object):
    def __init__(self, config):
        self.no_players = config.players
        self.players = []
        self.config = config
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
        debug("Testing %i from %s" %(index,repr(self.players)))
        if self.players[index].test():
            debug("Thing found")
            self.players.pop(index)
            return True
        debug("Human found")
        return False

    def night_phase(self):
        things = self.number_things()
        for x in self.players:
            x.new_turn(len(self.players))
        # Choose new thing from current humans
        humans = []
        for x in self.players:
            if x.is_human():
                humans.append(x)
        debug("Night phase "+repr(humans))
        random.choice(humans).become_thing()

    def nominate(self,playerno):
        # Assume that the first and seconding succeds
        debug("Testing player "+str(playerno))
        testing_player = self.players[playerno]
        # no point retesting
        if testing_player.is_tested():
                return True

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
        if (self.config.prob_weight_nominate != None):
        # Nominate the most likely person
            people = []
            for x in self.players:
                if not x.is_tested():
                     people.append(x)
            # Cause same probability to randomise
            random.shuffle(people)
            people=sorted(people, key=lambda person: person.probability)
            return self.nominate(self.players.index(people[-1]))
        else:
        # Random choice
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
           votes = votes-1
       else:
# Check win conditions
           (win, whowon) = state.win_condition()
           if (win):
              debug("Won "+str(whowon)+" "+str(rounds))
              return (whowon, rounds, state.number_things())

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

config = GameConfig(10, 2, True, 1, 1, 1, [2]*3, None, None)
(percent, hlen, tlen) = montecarlo(config, runs)

print config
print "Humans win %.2f%%" % (percent * 100)
hlen.output()
print "Things"
tlen.output()
