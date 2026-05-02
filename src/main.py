"""Interactive command-line password generator."""

from __future__ import annotations

try:  # Support both ``python src/main.py`` and package imports in tests.
    from .password_generator import (
        PasswordInputError,
        calculate_strength,
        generate_password,
        get_selected_character_sets,
        validate_length,
    )
except ImportError:  # pragma: no cover - exercised when run as a script.
    from password_generator import (
        PasswordInputError,
        calculate_strength,
        generate_password,
        get_selected_character_sets,
        validate_length,
    )


def prompt_yes_no(prompt: str) -> bool:
    """Prompt until the user enters a yes/no answer."""
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please enter 'y' for yes or 'n' for no.")


def prompt_length() -> int:
    """Prompt until the user enters a valid password length."""
    while True:
        raw_length = input("Password length (8-128): ")
        try:
            return validate_length(raw_length)
        except PasswordInputError as exc:
            print(f"Error: {exc}")


def prompt_character_sets() -> list[str]:
    """Prompt until at least one character set is selected."""
    while True:
        print("\nChoose character sets to include:")
        selected_sets = get_selected_character_sets(
            uppercase=prompt_yes_no("Include uppercase letters (A-Z)?"),
            lowercase=prompt_yes_no("Include lowercase letters (a-z)?"),
            digits=prompt_yes_no("Include digits (0-9)?"),
            special=prompt_yes_no("Include special characters (!@#...)?"),
        )
        if selected_sets:
            return selected_sets
        print(
            "Error: Select at least one character set before generating a "
            "password."
        )


def display_password_details(password: str) -> None:
    """Print the generated password and strength result."""
    strength = calculate_strength(password)
    print("\nGenerated password:")
    print(password)
    print("\nStrength meter:")
    print(f"{strength.meter} {strength.label} ({strength.score}/10)")
    print(f"Estimated entropy: {strength.entropy_bits:.1f} bits")
    print(f"Character types detected: {strength.character_variety}/4")
    print(strength.feedback)


def run_cli() -> None:
    """Run the interactive CLI loop."""
    print("CLI Password Generator with Strength Meter")
    print("Press Ctrl+C or Ctrl+D at any prompt to exit.\n")
    generated_passwords: set[str] = set()

    while True:
        try:
            length = prompt_length()
            selected_sets = prompt_character_sets()
            password = generate_password(
                length,
                selected_sets,
                avoid_passwords=generated_passwords,
            )
            generated_passwords.add(password)
            display_password_details(password)

            if not prompt_yes_no("\nGenerate another password?"):
                print("Goodbye!")
                return
            print()
        except PasswordInputError as exc:
            print(f"Error: {exc}")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return


if __name__ == "__main__":
    run_cli()
