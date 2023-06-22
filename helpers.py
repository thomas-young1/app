import os
import sys
from pymysql import cursors, DatabaseError
from prettytable import PrettyTable

# Error codes from MySQL, used for error checking/custom error messages
DUPLICATE_CODE = 1062
NOT_FOUND_CODE = 1452


def clear_screen():
    """
    Clears the terminal to display cleaner text
    """

    # support for Windows and Unix systems
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def safe_num_input(prompt: str) -> int:
    """
    Returns a number inputted by the user with graceful error handling to ensure
    a number was entered
    """

    while True:
        try:
            choice = int(input(prompt + ": "))
            return choice
        except ValueError:
            print("Please input a valid number")
        except KeyboardInterrupt:
            print("\nQuitting...")
            sys.exit()


def get_num_input(min: int, max: int, prompt: str) -> int:
    """
    Returns a number entered by the user validated between [min, max]
    """

    while True:
        choice = safe_num_input(prompt)

        if choice >= min and choice <= max:
            break

        print("Invalid choice, choose again")

    return choice


def num_input_list_neg_one(valid_nums: list[int], prompt: str) -> int:
    """
    Returns a number entered by the user validated from the provided list or -1
    """

    while True:
        choice = safe_num_input(prompt)

        if choice == -1:
            return -1

        if choice in valid_nums:
            break

        print("Invalid choice, choose again")

    return choice


def print_menu(prompt: str, statements: list[str]):
    """
    Displays a prompt followed by each statement in a numbered list
    """

    print(f"{prompt}:")
    for i, line in enumerate(statements):
        print(f"{i + 1}. {line}")


def call_proc(
    cur: cursors.DictCursor, proc_name: str, args: list = []
) -> tuple[dict[str,], ...]:
    """
    Calls and returns the results of a stored procedure in the database based on the name and arguments provided
    """

    cur.callproc(proc_name, args)
    return cur.fetchall()


def print_table(fields: list[str], data: list):
    """
    Prints a PrettyTable based on the list of field names and data provided
    """
    p = PrettyTable()
    p.field_names = fields
    p.add_rows(data)
    print(p)


def print_recipe_table(cur: cursors.DictCursor, user_id: int) -> list[int]:
    """
    Prints a table of all a user's recipes
    """
    try:
        recipes = call_proc(cur, "get_all_recipes_for_user", [user_id])
    except DatabaseError as e:
        print(e)
        print("Error retrieving user's recipes")
        return

    recipe_table_data = [(row.get("recipe_id"), row.get("name")) for row in recipes]

    print_table(["ID", "Name"], recipe_table_data)

    return [row.get("recipe_id") for row in recipes]


def print_ingredient_table(cur: cursors.DictCursor, user_id: int) -> list[int]:
    """
    Prints a table of all a user's ingredients
    """
    try:
        ingredients = call_proc(cur, "get_all_ingredients_for_user", [user_id])
    except DatabaseError as e:
        print(e)
        print("Error retrieving user's ingredients")
        return

    ing_table_data = [row.values() for row in ingredients]

    print_table(["ID", "Name"], ing_table_data)

    return [row.get("ingredient_id") for row in ingredients]
