from helpers import *
from source import State, main_menu
from pymysql import DatabaseError


class Ingredient:
    """
    Represents an Ingredient and the data that represents it
    """

    def __init__(self, i_dict: dict[str,]):
        self.id = i_dict.get("ingredient_id")
        self.name = i_dict.get("name")

    def print_self(self):
        print(f"Name: {self.name}")


def ingredient_module(state: State):
    clear_screen()

    state.print_message_reset()

    cur = state.cur
    print_menu(
        "Choose an action", ["View all ingredients", "Create new ingredient", "Go back"]
    )
    choice = get_num_input(1, 3, "Go to")

    match choice:
        case 1:
            # View all ingredients
            try:
                ingredients = call_proc(
                    cur, "get_all_ingredients_for_user", [state.user_id]
                )
            except DatabaseError as e:
                print(e)
                print("Error occurred when trying to fetch all of user's ingredients")

            ing_table_data = [row.values() for row in ingredients]

            ingredient_ids = [row.get("ingredient_id") for row in ingredients]

            print_table(["ID", "Name"], ing_table_data)

            choice = num_input_list_neg_one(
                ingredient_ids, "Choose an ingredient ID or go back with -1"
            )

            match choice:
                case -1:
                    ingredient_module(state)
                    return
                case _:
                    ingredient = [
                        row for row in ingredients if row.get("ingredient_id") == choice
                    ]

                    i_obj = Ingredient(ingredient[0])

                    ingredient_action(i_obj, state)

        case 2:
            # Create a new ingredient
            while True:
                name = input("Enter a name for the new ingredient: ")
                if name == "":
                    print("Must enter a valid name")
                    continue
                try:
                    new_ing = call_proc(cur, "create_ingredient", [name, state.user_id])
                except DatabaseError as e:
                    if e.args[0] == DUPLICATE_CODE:
                        print("This ingredient already exists, try again")
                    else:
                        print("Could not create new ingredient, try again")
                finally:
                    break

            state.update_message(
                f"New ingredient with ID {new_ing[0].get('ingredient_id')} created!"
            )
            ingredient_module(state)
        case 3:
            # Return to main menu
            main_menu(state)


def ingredient_action(ingredient: Ingredient, state: State):
    """
    Menu to interact with a specific ingredient that is given
    """
    clear_screen()

    state.print_message_reset()

    ingredient.print_self()

    print_menu("\nChoose an action", ["Edit", "Delete", "Go back"])
    choice = get_num_input(1, 3, "Go to")

    match choice:
        case 1:
            # Edit this ingredient's name
            new_name = input(f"Enter a new name for {ingredient.name}: ")
            try:
                call_proc(
                    state.cur, "update_ingredient_name", [ingredient.id, new_name]
                )
            except DatabaseError as e:
                print(e)
                print("Error updating this ingredient's name")

            state.update_message(
                f"Changed ingredient '{ingredient.name}' to '{new_name}'"
            )

            ingredient_module(state)

        case 2:
            # Delete this ingredient
            confirm = input(
                f"Are you sure you want to delete '{ingredient.name}'? Y/N: "
            )
            if confirm == "Y" or confirm == "y":
                try:
                    call_proc(state.cur, "delete_ingredient", [ingredient.id])
                except DatabaseError as e:
                    print(e)
                    print("Error occurred when trying to delete this ingredient")
                finally:
                    state.update_message(f"Deleted ingredient '{ingredient.name}'")

            ingredient_module(state)
        case 3:
            # Return to ingredient menu
            ingredient_module(state)
