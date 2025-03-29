'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random,eval7

class QLearningAgent():
    def __init__(self,epsilon=0.05,discount=0.80,alpha=0.2,numTraining=20,weights=False):
        self.epsilon=epsilon
        self.discount=discount
        self.alpha=alpha
        #self.reader = 
        self.numTraining=numTraining
        #self.values = util.Counter()
        if(weights==False):
            self.weights = {}
        else:
           self.weights=weights

    def getWeights(self):
        return self.weights

    def getLegalActions(self,state):
        if(state==False or state[1]==False):
           return[CheckAction(),FoldAction(),CallAction()]
        thisState=list(state)
        game_state = thisState[0]
        round_state = thisState[1]
        active = thisState[2]
        legal_actions = round_state.legal_actions()
        myActions=[]
        my_pip = round_state.pips[active]
        if RaiseAction in legal_actions:
            min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
            min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
            max_cost = max_raise - my_pip  # the cost of a maximum bet/raise
            myActions+=[RaiseAction(min_raise+(max_raise-min_raise)*.1)]
            myActions+=[RaiseAction(min_raise+(max_raise-min_raise)*.5)]
            myActions+=[RaiseAction(min_raise+(max_raise-min_raise)*.8)]
        if CheckAction in legal_actions:  # check-call
            myActions+=[CheckAction()]
        if random.random() < 0.25:
            myActions+=[FoldAction()]
        myActions+=[CallAction()]
        return myActions

    def evaluateHandStrength(self, my_cards, board_cards, num_simulations=10):
        """ 
        Monte Carlo simulation to estimate hand strength using eval7.
        """
        deck = [eval7.Card(str(c)) for c in eval7.Deck() if str(c) not in my_cards + board_cards]
        my_hand = [eval7.Card(str(c)) for c in my_cards]
        board = [eval7.Card(str(c)) for c in board_cards]

        wins = 0
        for _ in range(num_simulations):
            random.shuffle(deck)
            opp_hand = deck[:2]
            remaining_board = deck[2: 7 - len(board)]  # Fill the board to 5 cards

            full_board = board + remaining_board
            my_strength = eval7.evaluate(my_hand + full_board)
            opp_strength = eval7.evaluate(opp_hand + full_board)

            if my_strength > opp_strength:
                wins += 1

        return wins / num_simulations  # Returns estimated win probability

    def getFeatures(self,state):
        features = {}
        if(state==False or state[1]==False):
           features["hand_strength"] =0
           features["pot_odds"] =0
           features["effective_stack"] =0
           features["opp_aggression"] =0
           features["position"] =0
           features["street"] =0
           features["bluff_potential"] =0
           return features
        thisState=list(state)
        game_state = thisState[0]
        round_state = thisState[1]
        active = thisState[2]


        # 1. Hand Strength (Placeholder: Should be calculated using a hand evaluator)
        my_cards = round_state.hands[active]
        board_cards = round_state.deck[:round_state.street]  # Cards revealed so far
        features["hand_strength"] = self.evaluateHandStrength(my_cards, board_cards)

        # 2. Pot Odds
        my_pip = round_state.pips[active]
        opp_pip = round_state.pips[1 - active]
        pot_size = sum(round_state.pips)
        continue_cost = opp_pip - my_pip
        features["pot_odds"] = continue_cost / (pot_size + continue_cost) if continue_cost > 0 else 0

        # 3. Effective Stack Size (Relative to Big Blind)
        my_stack = round_state.stacks[active]
        features["effective_stack"] = my_stack / BIG_BLIND

        # 4. Opponent's Betting Behavior (Aggression Factor)
        opp_contribution = STARTING_STACK - round_state.stacks[1 - active]
        features["opp_aggression"] = opp_contribution / (pot_size + 1)  # +1 to avoid division by zero

        # 5. Position (1 if acting last, 0 if first)
        features["position"] = 1 if active == 1 else 0

        # 6. Street (Pre-Flop = 0, Flop = 1, Turn = 2, River = 3)
        features["street"] = round_state.street / 5  # Normalize between 0 and 1

        # 7. Bluff Potential (Simple metric: If opponent has checked, it might be a bluff spot)
        features["bluff_potential"] = 1 if CheckAction in round_state.legal_actions() else 0

        return features

    def update(self, state, action, nextState, reward):
        if(self.numTraining>0):
           self.numTraining-=1
        else:
           self.epsilon=0
        difference = reward + self.discount*self.computeValueFromQValues(nextState) - self.getQValue(state,action)
        features = self.getFeatures(state)
        #newWeights=[]
        for i,feature in enumerate(features):
          thisWeight=0
          if(feature in self.weights):
            thisWeight=self.weights[feature]
          self.weights[feature] = thisWeight - self.alpha*difference*features[feature]

    def getQValue(self, state, action):
        features = self.getFeatures(state)
        output=0
        for i,feature in enumerate(features):
          thisWeight=0
          if(feature in self.weights):
            thisWeight=self.weights[feature]
          output += thisWeight*features[feature]
        return output
    
    def computeActionFromQValues(self, state):
        legalActions = [action for action in self.getLegalActions(state)]
        #print(legalActions)
        if(len(legalActions)==0):
          return None
        else:
          bestAction = [legalActions[0]]
          bestActionScore=-9999999999999999999
          for action in legalActions:
            thisActionScore=self.getQValue(state,action)
            #print(thisActionScore)
            if(thisActionScore==bestActionScore):
              bestAction+=[action]
            elif(thisActionScore>bestActionScore):
              bestActionScore=thisActionScore
              bestAction=[action]
          if(random.random()<self.epsilon):
             return random.choice(legalActions)
          return random.choice(bestAction)
    
    def computeValueFromQValues(self, state):
        if(len([self.getQValue(state,action) for action in self.getLegalActions(state)])==0):
          return 0.0
        else:
          return max([self.getQValue(state,action) for action in self.getLegalActions(state)])


class Player(Bot):
    '''
    A pokerbot.
    '''
    
    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        self.previousAction=False
        self.previousState=False
        self.myAgent = QLearningAgent()

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        
        #my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        #round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[active]  # your cards
        #big_blind = bool(active)  # True if you are the big blind
        pass

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        thisGameState=game_state,False,active
        self.myAgent.numTraining-=1
        if(self.myAgent.numTraining>0):
           self.myAgent.update(self.previousState,self.previousAction,thisGameState,terminal_state.deltas[active])
        
        print(self.myAgent.getWeights())
        #my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        #previous_state = terminal_state.previous_state  # RoundState before payoffs
        #street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        #my_cards = previous_state.hands[active]  # your cards
        #opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        pass

    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
        #print(game_state)
        #print(round_state)
        #print(active)
        thisGameState=tuple([game_state,round_state,active])
        #print(list(thisGameState))
        if(self.myAgent.numTraining>0):
           self.myAgent.update(self.previousState,self.previousAction,thisGameState,0)

        action = self.myAgent.computeActionFromQValues(thisGameState)
        self.previousAction=action
        self.previousState=thisGameState
        #print(action)
        if isinstance(action, FoldAction):
            return FoldAction()
        elif isinstance(action, CallAction):
            return CallAction()
        elif isinstance(action, CheckAction):
            return CheckAction()
        else:  # isinstance(action, RaiseAction)
            return RaiseAction(int(action.amount))
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot
        if RaiseAction in legal_actions:
           min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
           min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
           max_cost = max_raise - my_pip  # the cost of a maximum bet/raise
        if RaiseAction in legal_actions:
            if random.random() < 0.5:
                return RaiseAction(min_raise)
        if CheckAction in legal_actions:  # check-call
            return CheckAction()
        if random.random() < 0.25:
            return FoldAction()
        return CallAction()  # If we can't raise, call if possible


if __name__ == '__main__':
    run_bot(Player(), parse_args())
