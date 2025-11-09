import argparse
from collections import abc
import csv
import io
import itertools
import typing


parser = argparse.ArgumentParser(
    description=(
        "This program allows you to set up a series of flashcards to test "
        "your memory recall."
    )
)

parser.add_argument("--import_from", help="Filename of initial card set.")
parser.add_argument(
    "--export_to", help="Filename in which to save cards to memory."
)

output = io.StringIO()


def log_message(message: str, end: str = "\n") -> None:
    print(message, end=end)
    output.write(f"{message}{end}")


def get_user_input(prompt: str) -> str:
    output.write(f"{prompt}\n")
    user_input: str = input(f"{prompt}\n").strip()
    output.write(f"{user_input}\n")
    return user_input


def check_input_for_duplicates(
    obj: typing.Literal["card", "definition"],
    set_to_check: abc.KeysView | abc.ValuesView,
) -> str:
    prompt: str
    if obj == "card":
        prompt = "The card:"
    else:
        prompt = "The definition of the card:"

    while True:
        user_input: str = get_user_input(prompt)
        if user_input not in set_to_check:
            return user_input

        prompt = f'The {obj} "{user_input}" already exists. Try again:'


def save_log() -> None:
    filename: str = get_user_input("File name:")

    with open(filename, "w", encoding="utf-8") as file:
        file.write(output.getvalue())

    log_message("The log has been saved.")


class Card:
    def __init__(self, definition: str, error_count: int = 0) -> None:
        self.definition = definition
        self.error_count = error_count

    def __repr__(self) -> str:
        return self.definition

    def __eq__(self, other) -> bool:
        return self.definition == other


class Flashcards(dict):
    def __init__(self, import_from: str | None, export_to: str | None) -> None:
        super().__init__()
        self.import_from = import_from
        self.export_to = export_to

        if self.import_from:
            self.import_file(self.import_from)

        while True:
            self.main_menu()

    def main_menu(self) -> None | typing.NoReturn:
        while True:
            user_input: str = get_user_input(
                (
                    "Input the action (add, remove, import, export, ask, "
                    "exit, log, hardest card, reset stats):"
                )
            )
            if user_input == "add":
                return self.add_card()
            if user_input == "remove":
                return self.remove_card()
            if user_input == "import":
                return self.import_file()
            if user_input == "export":
                return self.export_file()
            if user_input == "ask":
                return self.ask_user()
            if user_input == "log":
                return save_log()
            if user_input == "hardest card":
                return self.hardest_card()
            if user_input == "reset stats":
                return self.reset_stats()
            if user_input == "exit":
                log_message("Bye bye!")

                if self.export_to:
                    self.export_file(self.export_to)

                exit()

            log_message("Unknown command!")

    def add_card(self) -> None:
        term: str = check_input_for_duplicates("card", self.keys())
        definition: str = check_input_for_duplicates(
            "definition", self.values()
        )

        self[term] = Card(definition)

        log_message(f'The pair ("{term}":"{definition}") has been added.')

    def remove_card(self) -> None:
        card_to_remove: str = get_user_input("Which card?")

        try:
            del self[card_to_remove]
            log_message("The card has been removed.")
        except KeyError:
            log_message(
                f"Can't remove \"{card_to_remove}\": there is no such card."
            )

    def import_file(self, filename: str | None = None) -> None:
        if filename is None:
            filename = get_user_input("File name:")

        try:
            file: io.TextIOWrapper
            with open(filename, "r", encoding="utf-8") as file:
                file_reader = csv.DictReader(
                    file, fieldnames=("Term", "Definition", "Error Count")
                )

                n: int = 0

                line: dict
                for line in file_reader:
                    self[line["Term"]] = Card(
                        line["Definition"],
                        error_count=int(line["Error Count"]),
                    )
                    n += 1

                log_message(f"{n} cards have been loaded.")

        except FileNotFoundError:
            log_message("File not found.")

    def export_file(self, filename: str | None = None) -> None:
        if filename is None:
            filename: str = get_user_input("File name:")

        file: io.TextIOWrapper
        with open(filename, "w", encoding="utf-8") as file:
            file_writer = csv.writer(file)

            term: str
            card: Card
            for term, card in self.items():
                file_writer.writerow((term, card.definition, card.error_count))

            log_message(f"{len(self)} cards have been saved.")

    def ask_user(self) -> None:
        number_of_times: int = int(get_user_input("How many times to ask?"))

        card: Card
        for __, card in zip(range(number_of_times), itertools.cycle(self)):
            answer: str = get_user_input(f'Print the definition of "{card}":')

            if answer == self[card]:
                log_message("Correct!")
                continue

            self[card].error_count += 1
            log_message(
                f'Wrong. The right answer is "{self[card]}"', end=""
            )

            other_card: str
            for other_card in self:
                if card != other_card and answer == self[other_card]:
                    log_message(
                        f', but your definition is correct for "{other_card}"',
                        end="",
                    )
                    break

            log_message(".")

    def hardest_card(self) -> None:
        max_error_count: int = 0

        if self:
            max_error_count = max(
                card.error_count for card in self.values()
            )

        if max_error_count == 0:
            return log_message("There are no cards with errors.")

        hardest_cards: list[str] = [
            card
            for card in self
            if self[card].error_count == max_error_count
        ]

        if len(hardest_cards) == 1:
            return log_message(
                (
                    f'The hardest card is "{hardest_cards[0]}". You have '
                    f"{max_error_count} errors answering it."
                )
            )

        return log_message(
            (
                'The hardest cards are '
                f'{", ".join(f"{card}" for card in hardest_cards)}. '
                f"You have {max_error_count} errors answering them."
            )
        )

    def reset_stats(self) -> None:
        card: Card
        for card in self.values():
            card.error_count = 0

        log_message("Card statistics have been reset.")


if __name__ == "__main__":
    args: argparse.Namespace = parser.parse_args()

    flashcards = Flashcards(args.import_from, args.export_to)
