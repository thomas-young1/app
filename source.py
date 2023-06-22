import pymysql
from pymysql import cursors, DatabaseError
import sys
from helpers import *
from getpass import getpass


class State:
    """
    A class that holds commonly used data across the whole program such as the database
    cursor and information about the user as well as any messages that could be printed
    by different areas of the program
    """

    def __init__(self, cur: cursors.DictCursor, user_id: int, username: str):
        self.cur = cur
        self.user_id = user_id
        self.username = username
        self.message = ""

    def update_message(self, m: str):
        self.message = m

    def clear_message(self):
        self.message = ""

    def print_message_reset(self):
        """
        Prints and resets the previously entered message
        """
        if self.message:
            print(self.message + "\n")
            self.clear_message()


def main():
    print("Please log in to the local MySQL server:")
    username = input("Username: ")
    password = getpass("Password: ")

    try:
        cnx = pymysql.connect(
            host="localhost",
            user=username,
            password=password,
            db="recipemaster",
            charset="utf8mb4",
        )
    except pymysql.err.OperationalError as e:
        print(e)
        print("Could not connect... shutting down")
        sys.exit()

    cur = cnx.cursor(cursor=cursors.DictCursor)

    print_menu("Log in or create a new user for RecipeMaster", ["Log in", "New user"])
    choice = get_num_input(1, 2, "Go to")
    match choice:
        case 1:
            # Logging into an already existing account
            while True:
                username = input("Username: ")
                password = getpass("Password: ")

                cur.execute("SELECT get_user_id(%s, %s)", [username, password])

                user_id = cur.fetchone().get(f"get_user_id('{username}', '{password}')")

                if user_id != -1:
                    new_user = False
                    break

                print("Invalid credentials, try again\n")
        case 2:
            # Creating a new user
            while True:
                username = input("Username: ")
                password = getpass("Password: ")

                try:
                    user_id = call_proc(cur, "create_user", [username, password])
                    user_id = user_id[0].get("user_id")
                except DatabaseError as e:
                    if e.args[0] == DUPLICATE_CODE:
                        print("User already exists with that username, try again")
                    else:
                        print("Error creating new user, try again")
                finally:
                    new_user = True
                    break

    clear_screen()

    state = State(cur, user_id, username)
    if new_user:
        state.update_message(f"Created new user with ID {user_id}")

    # Entering point for the rest of the application, once this function returns, the program ends
    main_menu(state)

    print("Shutting down...")
    cnx.close()


def main_menu(state: State):
    clear_screen()

    state.print_message_reset()

    print_menu(
        f"Welcome to RecipeMaster, {state.username}! To get started, choose one of the options below",
        ["Recipes", "Ingredients", "Lists", "Reviews", "Exit"],
    )

    choice = get_num_input(1, 5, "Go to")

    match choice:
        case 1:
            # Opens the recipe menu
            from recipe import recipe_module

            recipe_module(state)
        case 2:
            # Opens the ingredient menu
            from ingredient import ingredient_module

            ingredient_module(state)
        case 3:
            # Opens the list menu
            from list import list_module

            list_module(state)
        case 4:
            # Opens the review menu
            from review import review_module

            review_module(state)
        case 5:
            # Exits the program
            return


if __name__ == "__main__":
    main()
