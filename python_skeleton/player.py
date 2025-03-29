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
    
    def evaluate_hand_strength(self, hole_cards, board_cards, num_simulations=1000):
        '''
        Evaluate the strength of a hand using Monte Carlo simulations.

        Arguments:
        hole_cards: a list of two eval7.Card objects representing your hole cards.
        board_cards: a list of eval7.Card objects representing the board cards.
        num_simulations: the number of Monte Carlo simulations to run.

        Returns:
        A float representing the win probability (0.0 to 1.0).
        '''
        deck = eval7.Deck()
        for card in hole_cards + board_cards:
            deck.cards.remove(card)  # Remove known cards from the deck

        wins = 0

        for i in range(num_simulations):
            deck.shuffle()

            # Deal remaining board cards
            remaining_board = board_cards + [deck.pop() for _ in range(5 - len(board_cards))]

            # Deal opponent's hole cards
            opp_hole = [deck.pop(), deck.pop()]

            # Evaluate hands
            my_hand = hole_cards + remaining_board
            opp_hand = opp_hole + remaining_board

            my_score = eval7.evaluate(my_hand)
            opp_score = eval7.evaluate(opp_hand)

            if my_score > opp_score:
                wins += 1
            elif my_score == opp_score:
                wins += 0.5  # Split pot
            
            # Early stopping condition
            if (i > 150) and (wins / (i + 1) > 0.9):  # High confidence in win
                break

        return wins / num_simulations

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

        my_cards = [eval7.Card(card) for card in round_state.hands[active]]
        board_cards = [eval7.Card(card) for card in round_state.deck[:round_state.street]]

        theres_no_time = False
        hand_strength = 0
        if theres_no_time:
            full_hand = my_cards + board_cards
            hand_strength = eval7.evaluate(full_hand)
        else:
            if len(board_cards) < 3: # Pre-flop or Flop
                hand_strength = self.evaluate_hand_strength(my_cards, board_cards, num_simulations=500)
            else: # Turn or River
                hand_strength = self.evaluate_hand_strength(my_cards, board_cards)

        if hand_strength > 5000 and RaiseAction in legal_actions:  # Strong hand
            min_raise, max_raise = round_state.raise_bounds()
            return RaiseAction(min_raise)
        elif hand_strength > 3000 and CallAction in legal_actions:  # Decent hand
            return CallAction()
        else:  # Weak hand
            if FoldAction in legal_actions:
                return FoldAction()
            return CheckAction()


if __name__ == '__main__':
    run_bot(Player(), parse_args())
