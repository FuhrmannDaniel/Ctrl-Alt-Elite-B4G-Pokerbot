'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import random
import eval7
import time


class Player(Bot):
    '''
    A pokerbot.
    '''

    def regression_line_val(self, x, multiplier):
        u = 4
        return 100 * (x / 100) ** u * multiplier

    def get_combinations(self, cards, n):
        """Generate all combinations of n cards from the list of cards."""
        if n == 1:
            return [[card] for card in cards]
        
        combinations = []
        for i in range(len(cards)):
            for sub_comb in self.get_combinations(cards[i+1:], n-1):
                combinations.append([cards[i]] + sub_comb)
        return combinations

    def monte_carlo_simulation(self, hole_cards, community_cards, num_trials=500):
        deck = [eval7.Card(rank + suit) for rank in "23456789TJQKA" for suit in "shdc"]
        used_cards = set(hole_cards + community_cards)

        # Remove used cards from the deck
        deck = [card for card in deck if card not in used_cards]

        wins = 0

        for _ in range(num_trials):
            random.shuffle(deck)
            opponent_hole = deck[:3]  # Opponent's 3 hole cards (like player)
            remaining_board = deck[3: 5 - len(community_cards)]  # Fill in the board

            full_board = community_cards + remaining_board

            # Get all 5-card combinations for both hands
            my_combinations = self.get_combinations(hole_cards + full_board, 5)
            opp_combinations = self.get_combinations(opponent_hole + full_board, 5)

            # Evaluate the best hand for both the player and the opponent
            my_best = max(my_combinations, key=eval7.evaluate)
            opp_best = max(opp_combinations, key=eval7.evaluate)

            if eval7.evaluate(my_best) > eval7.evaluate(opp_best):
                wins += 1

        return wins / num_trials  # Win probability


    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        pass

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
        #my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
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
        
        my_cards_card_form = [eval7.Card(card) for card in my_cards]
        board_cards_card_form = [eval7.Card(card) for card in board_cards]
        
        win_percentage = self.monte_carlo_simulation(my_cards_card_form, board_cards_card_form)

        # actions; RaiseAction, CallAction, CheckAction, FoldAction

        raise_multipler = 0.26
        if(street == 3):
            raise_multipler = 0.5
        if(street == 4):
            raise_multipler = 0.75
        if(street == 5):
            raise_multipler = 1.0

        call_multiplier = 1.4
        if(street == 3):
            call_multiplier = 1.6
        if(street == 4):    
            call_multiplier = 1.8
        if(street == 5):
            call_multiplier = 2.0

        raise_amount_total = my_stack * self.regression_line_val(100 * win_percentage, raise_multipler)
        call_max_total = my_stack * self.regression_line_val(100 * win_percentage, call_multiplier)

        raise_amount = raise_amount_total - my_pip # the amount needed to raise to get to raise_amount_total
        if(raise_amount > my_stack):
            raise_amount = my_stack

        print(raise_amount_total)

        if CallAction in legal_actions:
            if opp_pip > call_max_total:
                return FoldAction()
            elif opp_pip < raise_amount_total:
                return RaiseAction(raise_amount)
            else:
                return CheckAction()

        if raise_amount > 0:
        #    min_raise, max_raise = round_state.raise_bounds() # the smallest and largest numbers of chips for a legal bet/raise
           return RaiseAction(raise_amount_total)
        if CheckAction in legal_actions and raise_amount < 0:
            return CheckAction()

        # if RaiseAction in legal_actions:
        #    min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
        #    min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
        #    max_cost = max_raise - my_pip  # the cost of a maximum bet/raise
        # if RaiseAction in legal_actions:
        #     if random.random() < 0.5:
        #         return RaiseAction(min_raise)
        # if CheckAction in legal_actions:  # check-call
        #     return CheckAction()
        # if random.random() < 0.25:
        #     return FoldAction()
        return CallAction()  # If we can't raise, call if possible


if __name__ == '__main__':
    run_bot(Player(), parse_args())