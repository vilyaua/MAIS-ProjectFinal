"""Command-line interface for the password generator."""

from __future__ import annotations

from password_generator import (
    CharacterOptions,
    PasswordGeneratorError,
    evaluate_strength,
    generate_password,
)


def prompt_length() -> int:
    """Prompt until the user enters a valid password length."""
    while True:
        raw_value = input("Enter password length (minimum 1): ").strip()
        try:
            length = int(raw_value)
            if length < 1:
                raise ValueError("length below minimum")
        except ValueError:
            print("Error: please enter a whole number greater than or equal to 1.")
            continue
        return length


def prompt_yes_no(prompt: str) -> bool:
    """Prompt until the user answers yes or no."""
    while True:
        raw_value = input(f"{prompt} [y/n]: ").strip().lower()
        if raw_value in {"y", "yes"}:
            return True
        if raw_value in {"n", "no"}:
            return False
        print("Error: please answer with 'y' or 'n'.")


def prompt_character_options() -> CharacterOptions:
    """Prompt until at least one character category is selected."""
    while True:
        options = CharacterOptions(
            uppercase=prompt_yes_no("Include uppercase letters?"),
            lowercase=prompt_yes_no("Include lowercase letters?"),
            digits=prompt_yes_no("Include digits?"),
            special=prompt_yes_no("Include special characters?"),
        )
        if options.selected_count() > 0:
            return options
        print("Error: at least one character type must be selected. Please try again.")


def run_cli() -> None:
    """Run the interactive password generator CLI."""
    print("Password Generator with Strength Meter")
    print("--------------------------------------")

    while True:
        length = prompt_length()
        options = prompt_character_options()
        try:
            password = generate_password(length, options)
        except PasswordGeneratorError as exc:
            print(f"Error: {exc}")
            continue

        strength = evaluate_strength(password)
        print("\nGenerated password:")
        print(password)
        print(
            f"Strength: {strength.rating.value.capitalize()} "
            f"({strength.score}/{strength.max_score})"
        )
        print(f"Details: {strength.details}")
        break


if __name__ == "__main__":
    run_cli()
