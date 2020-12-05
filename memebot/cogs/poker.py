import random
from discord.ext import commands
from discord import User
from typing import List, Dict, Optional

class RaiseUnderActiveBet(Exception):
    def __init__(self):
        self.message = "Attempt to raise was underneath amount of previous bet."

class RaiseUnderLatestRaise(Exception):
    def __init__(self):
        self.message = "Player attempting to raise must raise by at least as much as the previous raise."

class PokerGame():
    def __init__(self, context: Optional[commands.Context] = None):
        # Fundamental rules of the world
        self.SUITS = [
            "Hearts",
            "Diamonds",
            "Clubs",
            "Spades"
        ]

        self.ROYAL_CARDS = {
            0: "Ace",
            10: "Jack",
            11: "Queen",
            12: "King"
        }

        # Things that have to do with the players
        self.creator: User = context.author() if context else None
        self.players: Dict[User: dict] = {}
        self.order: List[User] = []
        self.current_button_index: int = 0
        self.current_player_on_the_action: int = 0

        # Necessities for the game
        self.deck: List[int] = [i for i in range(52)]
        self.flop_turn_and_river: List[int] = []
        self.bet_to_call: int = 0
        self.latest_raise: int = 0
        self.current_pot: int = 0

        # Things that have to do with game continuation or outcome
        self.can_start: bool = False
        self.has_started: bool = False
        self.betting_round_over: bool = False
        self.hand_winner_decided: bool = False
        self.hand_winner: User = None
        self.game_winner_decided: bool = False
        self.game_winner: bool = False

        if context:
            self.add_player(context.author())

    def add_player(self, player: User):
        self.players[player] = {
            "hand": [],
            "wins": 0,
            "bet": 0,
            "dollars": 50,
        }

        if len(self.players.keys()) > 1:
            self.can_start = True


    def remove_player(self, player: User):
        if player in self.players.keys():
            if self.order:
                if len(self.order) == 1:
                    del self.players
                else:
                    if player == self.creator:
                        self.creator = list(self.players.keys())[-1]
                    
                    self.order.remove(player)
                    self.players.pop(player)

                    if self.has_started:
                        self.determine_winner()
                    else:
                        self.can_start = False

    def establish_order(self):
        self.order = random.shuffle(self.players.keys())
    
    def deal(self):
        """
        5 for the flop, turn and river
        2 for each player
        """
        total_deal: List[int] = random.sample(self.deck, 5 + 2 * (len(self.players)))

        for player in self.order:
            self.players[player]["hand"] = total_deal[2:]
            del total_deal[2:]

        self.flop_turn_and_river = total_deal

    def determine_friendly_card_name(self, card: int):
        return f"{self.ROYAL_CARDS.get(card % 13, str(card + 1))} of {self.SUITS[card // 13]}"

    def retrieve_hands(self):
        hand_to_message = {}
        for player, attributes in self.players.items():
            hand_to_message[player.id] = [self.determine_friendly_card_name(card) for card in attributes["hand"]]

        return hand_to_message

    def place_opening_bet(self, player: User, amount: int):
        if amount > self.players[player]["dollars"]:
            self.players[player]["bet"] += self.players[player]["dollars"]
            self.bet_to_call = self.players[player]["dollars"]
            self.current_pot += self.players[player]["dollars"]
            self.players["dollars"] = 0
        else:
            self.players[player]["bet"] += amount
            self.bet_to_call = amount
            self.current_pot += amount
            self.players[player]["dollars"] -= amount

    def raise_previous(self, player: User, amount: int):
        if amount < self.bet_to_call:
            raise RaiseUnderActiveBet
        elif amount < self.latest_raise:
            raise RaiseUnderLatestRaise
        elif amount > self.players[player]["dollars"]:
            self.players[player]["bet"] += self.players[player]["dollars"]
            self.bet_to_call = self.players[player]["dollars"]
            self.current_pot += self.players[player]["dollars"]
            self.players["dollars"] = 0
        else:
            self.players[player]["bet"] += amount
            self.bet_to_call = amount
            self.current_pot += amount
            self.players[player]["dollars"] -= amount

    def fold(self, player: User):
        self.players[player]["hand"] = []
        self.order.remove(player)

    def determine_winner(self):
        if len(self.order) == 1:
            self.hand_winner_decided = True
            self.hand_winner = self.order[0]
        
        if len(self.players.keys()) == 1:
            self.game_winner_decided = True
            self.game_winner = self.players.keys()[0]

    def check(self, player: User):
        pass

    def call(self, player: User):
        if self.bet_to_call > self.players[player]["dollars"]:
            self.players[player]["bet"] += self.players[player]["dollars"]
            self.bet_to_call = self.players[player]["dollars"]
            self.current_pot += self.players[player]["dollars"]
            self.players["dollars"] = 0
        else:
            difference = self.bet_to_call - self.players[player]["bet"]
            self.players[player]["bet"] = self.bet_to_call
            self.current_pot += difference
            self.players[player]["dollars"] -= difference

    def determine_available_actions(self):
        available_actions = [self.fold]
        if self.current_pot == 0:
            available_actions.append(self.place_opening_bet, self.check)
        if self.latest_raise != 0:
            available_actions.append(self.raise_previous, self.call)

        return available_actions

    def current_standings(self):
        standings_string = ""
        for player, attributes in self.players:
            standings_string += f"**{player}** has **{attributes.dollars}**\n"

        return standings_string

    def winner(self):
        if len(self.order) == 1:
            return self.order[0]
        else:
            return None

class PokerGameCommand(commands.Cog):
    @commands.command()
    async def poker(self, context: commands.Context, arg: str):
        """starts a game of Hold 'em Poker."""
        if not arg and not self.game:
            self.game = PokerGame(context)
            await context.send(f"{context.author()} has elected to start a Poker game. Who's in?")
        elif not arg and self.game:
            await context.send("There is already a game going on.")

    async def poker_join(self, context: commands.Context):
        if context.author() not in self.game.players:
            self.game.add_player(context.author())
            await context.send(f"{context.author()} has joined the game.")
        else:
            await context.send("You're already in the game.")

    async def poker_leave(self, context: commands.Context):
        if context.author() not in self.game.players:
            await context.send("You're not in the game.")
        else:
            await context.send(f"{context.author()} has elected to leave with ${self.game.players[context.author()]['dollars']}!")
            self.game.remove_player(context.author())

    async def poker_start(self, context: commands.Context):
        if len(self.game.players) < 2:
            await context.send("You need at least 2 players to play poker.")
        elif context.author() != self.game.creator:
            await context.send(f"Only {self.game.creator}, the creator of the game, may start it.")
        else:
            self.game.establish_order()
            await context.send(f"Order for this table: {[player for player in self.game.order]}")

    async def poker_end(self, context: commands.Context):
        if context.guild().owner_id == context.author().id:
            await context.send(f"The server owner has elected to end the game.")
            del self.game
        if context.author() != self.game.creator:
            await context.send(f"Only {self.game.creator}, the creator of the game, may end it.")
        else:
            await context.send(f"{self.game.creator} has elected to end the game!")
            del self.game
        