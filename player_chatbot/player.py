"""
Simple example pokerbot, written in Python.
"""

from skeleton.actions import CallAction, CheckAction, FoldAction, RaiseAction
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
from skeleton.states import (
    BIG_BLIND,
    NUM_ROUNDS,
    SMALL_BLIND,
    STARTING_STACK,
    GameState,
    RoundState,
    TerminalState,
)
from dotenv import load_dotenv
import os
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"  # Path to .env file

# Set to True if you want to use GPT-4 to generate responses,
# and False if you want to manually input responses.
USE_GPT = True

if USE_GPT:
    import openai
    # Load environment variables from .env file
    load_dotenv(dotenv_path=env_path)
    openai.api_key = os.getenv("API_KEY") # Enter your API key here


def chat(messages):
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview", messages=messages
    )
    return response.choices[0].message.content.strip()


ROLE = "You are an expert Poker player who is also good at playing different variants."

GAME_RULES = """
I want you to play a variant of Poker with me.
How the variant goes is that it is very similar to Texas Hold'em with 2 players. However, in this variant, there is one less round of betting.
You will initially recieve 3 cards. There will be a round of betting, then 2 card will be revealed on the flop. There will be another round of betting,
then the final 2 cards will be revealed. After this final round of betting, the two players will have a showdown, where standard Texas Hold'em rules 
will determine the winner. Whenever it is your action, I will give you information about your current
cards, the current cards on deck, your remaining stack, your contribution to the pot, and the legal
actions you can take (Raise, Fold, Call, Check). The cards will be formated as 'ab', where b is the
suite (h = heart, d = diamond, s = spade, c = club), and a is the type (can be numbers from 2-9, or T (10),
J (jack), Q (Queen), K (King)). The starting stack for a round is 400, with the small blind being 1 and big
blind equal 2. I want you to format your response as the following: If you want to Fold, Call or Check,
then just respond as Fold, Call or Check respectively (1 word). If you want to Raise, format
your response as 'Raise x' where x is an integer. For example, if Call is a
legal action and you want to call, then respond with 'Call'. If Raise is in legal action and you want
to raise by 10, then respond 'Raise 10'. We can play one round and see how it goes
""".replace(
    "\n", " "
).strip()

ASSISTANT_AGREES = """
Of course, let's play this variant of Poker. Please provide me with the current game scenario,
including my hole cards, the visible community cards on the flop, my chip stack, and my current
contribution to the pot, and the legal actions available to me.
""".replace(
    "\n", " "
).strip()


class Player(Bot):
    """
    A pokerbot.
    """

    def __init__(self):
        """
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        """
        self.messages = [
            {"role": "system", "content": ROLE},
            {"role": "user", "content": GAME_RULES},
            {"role": "assistant", "content": ASSISTANT_AGREES},
        ]
        self.new_message = ""
        self.is_gpt = False

    def handle_new_round(self, game_state, round_state, active):
        """
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        """
        # my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        game_clock = (
            game_state.game_clock
        )  # the total number of seconds your bot has left to play this game

        # round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        # my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind
        print(
            "================================NEW ROUND==================================="
        )
        print("You are", "big blind!" if big_blind else "small blind!")
        self.new_message = "You are " + "big blind!" if big_blind else "small blind!"

    def handle_round_over(self, game_state, terminal_state, active):
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        """
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        # street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        # my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[
            1 - active
        ]  # opponent's cards or [] if not revealed
        print()
        if opp_cards:
            print("Your opponent revealed", ", ".join(opp_cards))
            self.new_message += " Your opponent revealed " + ", ".join(opp_cards) + "."

        print("This round, your bankroll changed by", str(my_delta) + "!")
        self.new_message += (
            " This round, your bankroll changed by "
            + str(my_delta)
            + "! Onto the next round - Say yes to continue."
        )
        print()

        if self.is_gpt:
            self.messages.append({"role": "user", "content": self.new_message})
            response = chat(self.messages)
            self.messages.append({"role": "assistant", "content": response})

        ask = input("Press enter to continue, or q to quit!\n")
        if ask in ["q", "quit", "Quit"]:
            exit()

    def get_action(self, game_state, round_state, active):
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        """
        # May be useful, but you may choose to not use.
        legal_actions = (
            round_state.legal_actions()
        )  # the actions you are allowed to take
        street = (
            round_state.street
        )  # 0, 2, or 4 representing pre-flop, flop, or turn, respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[
            active
        ]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[
            1 - active
        ]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[
            1 - active
        ]  # the number of chips your opponent has remaining
        continue_cost = (
            opp_pip - my_pip
        )  # the number of chips needed to stay in the pot
        my_contribution = (
            STARTING_STACK - my_stack
        )  # the number of chips you have contributed to the pot
        opp_contribution = (
            STARTING_STACK - opp_stack
        )  # the number of chips your opponent has contributed to the pot

        print()
        print("Your current cards are:", ", ".join(my_cards))
        self.new_message += " Your current cards are: " + ", ".join(my_cards) + "."
        if board_cards:
            print("The visible community cards are:", ", ".join(board_cards))
            self.new_message += (
                " The visible community cards are: " + ", ".join(board_cards) + "."
            )
        else:
            print("There are no visible community cards.")
            self.new_message += " There are no visible community cards."

        print("Your current contribution to the pot is", my_contribution)
        self.new_message += (
            " Your current contribution to the pot is " + str(my_contribution) + "."
        )
        print("Your remaining stack is", my_stack)
        self.new_message += " Your remaining stack is " + str(my_stack) + "."

        if my_contribution != 1 and continue_cost > 0:
            print("Your opponent raised by", continue_cost)
            self.new_message += " Your opponent raised by " + str(continue_cost) + "."

        poss_actions = "Your legal actions are: "

        if RaiseAction in legal_actions:
            poss_actions += "Raise, "
        if FoldAction in legal_actions:
            poss_actions += "Fold, "
        if CallAction in legal_actions:
            poss_actions += "Call, "
        if CheckAction in legal_actions:
            poss_actions += "Check, "
        print(poss_actions[:-2] + ".\n")
        self.new_message += " " + poss_actions[:-2] + "."

        if RaiseAction in legal_actions:
            min_raise, max_raise = (
                round_state.raise_bounds()
            )  # the smallest and largest numbers of chips for a legal bet/raise
            min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
            max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        if self.is_gpt:
            self.messages.append({"role": "user", "content": self.new_message})
            response = chat(self.messages)
            self.messages.append({"role": "assistant", "content": response})
            print("GPT-4:", response)
            response = response.split()
            if len(response) == 1:
                act = response[0]
            elif len(response) == 2:
                act, num = response
                num = int(num)
            else:
                print("Error: GPT gave too many words.")
                exit()
            self.new_message = ""
        else:
            active = input("Enter your move:\n")
            act = None
            while act is None:
                active = active.split(" ")
                if active[0] in ["Quit", "quit", "q"]:
                    exit()
                if len(active) != 1 and len(active) != 2:
                    active = input("Too many words. Re-enter move: \n")
                elif len(active) == 1:
                    act = active[0].capitalize()
                    if act not in ["Check", "Fold", "Call"]:
                        act = None
                        active = input(
                            "One-word moves are only Check, Fold and Call. Re-enter move: \n"
                        )
                else:
                    act, num = active
                    act = act.capitalize()
                    if act != "Raise":
                        act = None
                        active = input(
                            "Raise is the only 2-word move. Re-enter move: \n"
                        )
                    try:
                        num = int(num)
                    except:
                        act = None
                        active = input(
                            "Integer not entered for Raising. Enter new move: \n"
                        )

        if act == "Raise":
            return RaiseAction(num)
        elif act == "Check":
            return CheckAction()
        elif act == "Call":
            return CallAction()
        else:
            return FoldAction()


if __name__ == "__main__":
    run_bot(Player(), parse_args())
