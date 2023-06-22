from source import State, main_menu
from helpers import *
from pymysql import DatabaseError


class List:
    """
    Represents a List of ingredients and the data associated with it
    """

    def __init__(self, l_dict: dict[str,]):
        self.id = l_dict.get("list_id")
        self.name = l_dict.get("name")
        self.date_created = l_dict.get("date_created")

    def print_self(self):
        print(f"Name: {self.name}")
        print(f"Date created: {self.date_created}")


def list_module(state: State):
    """
    Top level menu to interact with Lists
    """
    clear_screen()

    state.print_message_reset()

    # Main menu
    print_menu("Choose an action", ["View all lists", "Create new list", "Go back"])
    choice = get_num_input(1, 3, "Go to")

    cur = state.cur

    match choice:
        case 1:
            # View all lists
            try:
                lists = call_proc(cur, "get_all_lists_for_user", [state.user_id])
            except DatabaseError as e:
                print(e)
                print("Error occurred when trying to fetch all lists")
                list_module(state)
                return

            list_table_data = [row.values() for row in lists]

            list_ids = [row.get("list_id") for row in lists]

            print_table(["ID", "Name", "Date Created"], list_table_data)

            choice = num_input_list_neg_one(
                list_ids, "Choose a list ID or -1 to go back"
            )

            match choice:
                case -1:
                    list_module(state)
                    return
                case _:
                    l_obj = List(
                        [row for row in lists if row.get("list_id") == choice][0]
                    )
                    list_action(l_obj, state)

        case 2:
            # Create a new list
            name = input("Enter name of new list: ")

            try:
                list_id = call_proc(cur, "create_list", [name, state.user_id])
            except DatabaseError as e:
                if e.args[0] == DUPLICATE_CODE:
                    print("Cannot create a list with a duplicated title")
                print("Error creating new list")
                list_module(state)
                return
            finally:
                list_id = list_id[0].get("list_id")

            print_ingredient_table(cur, state.user_id)

            # Loop for adding ingredients to list
            while True:
                ing_id = safe_num_input(
                    "Choose an ingredient ID to add to the list or -1 to stop"
                )

                if ing_id == -1:
                    break

                try:
                    call_proc(cur, "create_list_item", [ing_id, list_id])
                except DatabaseError as e:
                    if e.args[0] == DUPLICATE_CODE:
                        print("Duplicate entries are not allowed")
                    elif e.args[0] == NOT_FOUND_CODE:
                        print("This ingredient does not exist")
                    else:
                        print("Error adding this ingredient to the list")

            state.update_message(f"Created new list with ID {list_id}")
            list_module(state)
            return

        case 3:
            # Return to the main screen
            main_menu(state)


def list_action(list: List, state: State):
    """
    Menu to interact with a specific List that is given
    """
    clear_screen()

    state.print_message_reset()

    list.print_self()

    try:
        items = call_proc(state.cur, "get_ingredients_for_list", [list.id])
    except DatabaseError as e:
        print(e)
        print("Error occurred when trying to fetch ingredients for this list")

    item_table_data = [
        (row.get("item_id"), row.get("name"), "x" if row.get("completed") == 1 else "")
        for row in items
    ]

    # Print a table for the ingredients in the list and their statuses
    print_table(["ID", "Item", "Completed"], item_table_data)

    print_menu("Select an action", ["Edit", "Delete", "Go back"])
    choice = get_num_input(1, 3, "Go to")

    match choice:
        case 1:
            # Edit this list
            update_msg = f"Updated list '{list.name}'"

            # Loop to execute different actions (edit name, edit items)
            while True:
                print_menu(
                    "\nSelect an action",
                    ["Edit list's name", "Edit items in list", "Go back"],
                )
                choice = get_num_input(1, 3, "Go to")

                new_name = list.name

                match choice:
                    case 1:
                        # Edit the list's name
                        new_name = input(f"Enter a new name for '{list.name}': ")

                        try:
                            call_proc(
                                state.cur, "update_list_name", [list.id, new_name]
                            )
                        except DatabaseError as e:
                            if e.args[0] == DUPLICATE_CODE:
                                print("Cannot have duplicate list names")
                            else:
                                print(e)
                                print("Error when trying to update list name")
                        if " with a different name" not in update_msg:
                            update_msg += " with a different name"
                    case 2:
                        # Edit the items in the list
                        print_menu(
                            "\nSelect an action",
                            ["Add items", "Delete items", "Update items", "Go back"],
                        )
                        choice = get_num_input(1, 4, "Do")

                        match choice:
                            case 1:
                                # Add items to the list
                                print_ingredient_table(state.cur, state.user_id)
                                while True:
                                    ing_id = safe_num_input(
                                        "Choose an ingredient ID to add to the list or -1 to cancel"
                                    )

                                    if ing_id == -1:
                                        break

                                    try:
                                        call_proc(
                                            state.cur,
                                            "create_list_item",
                                            [ing_id, list.id],
                                        )
                                    except DatabaseError as e:
                                        if e.args[0] == DUPLICATE_CODE:
                                            print("Duplicate entries are not allowed")
                                        elif e.args[0] == NOT_FOUND_CODE:
                                            print("This ingredient does not exist")
                                        else:
                                            print(
                                                "Error adding this ingredient to the list"
                                            )

                                # Ensure the state message is staying up to date
                                if " with different items" not in update_msg:
                                    update_msg += " with different items"
                            case 2:
                                # Delete items from a list
                                while True:
                                    item_id = safe_num_input(
                                        "Choose an item ID from the list to remove or -1 to cancel"
                                    )

                                    if item_id not in [
                                        row.get("item_id") for row in items
                                    ]:
                                        print("Invalid item ID, try again")
                                        continue

                                    if item_id == -1:
                                        break

                                    try:
                                        call_proc(
                                            state.cur,
                                            "remove_item_from_list",
                                            [item_id, list.id],
                                        )
                                    except DatabaseError as e:
                                        if e.args[0] == NOT_FOUND_CODE:
                                            print("Item ID was not found on this list")
                                        else:
                                            print(e)
                                            print("Error removing item from list")

                                if " with different items" not in update_msg:
                                    update_msg += " with different items"

                            case 3:
                                # Update the statuses of items on the list (complete or not)
                                try:
                                    items = call_proc(
                                        state.cur, "get_ingredients_for_list", [list.id]
                                    )
                                except DatabaseError as e:
                                    print(e)
                                    print(
                                        "Error occurred when fetching ingredients for this list"
                                    )

                                item_table_data = [
                                    (
                                        row.get("item_id"),
                                        row.get("name"),
                                        "x" if row.get("completed") == 1 else "",
                                    )
                                    for row in items
                                ]

                                print_table(
                                    ["ID", "Item", "Completed"], item_table_data
                                )

                                while True:
                                    item_id = safe_num_input(
                                        "Enter the ID of an item to switch its completeness or -1 to cancel"
                                    )

                                    if item_id == -1:
                                        break

                                    try:
                                        new_status = (
                                            1
                                            if [
                                                row.get("completed") == 0
                                                for row in items
                                            ]
                                            else 0
                                        )
                                        call_proc(
                                            state.cur,
                                            "toggle_item_status_in_list",
                                            [item_id, list.id, new_status],
                                        )
                                    except DatabaseError as e:
                                        if e.args[0] == NOT_FOUND_CODE:
                                            print("Item ID not found in this list")
                                        else:
                                            print(e)
                                            print(
                                                "Error occurred when trying to update list item"
                                            )

                                if " with updated items" not in update_msg:
                                    update_msg += " with updated items"

                            case 4:
                                # Return to the top main editing menu
                                ()
                    case 3:
                        # Return to main list action menu
                        break

            state.update_message(update_msg)

            # Update the properties of the list after editing it
            new_list = List(
                {
                    "list_id": list.id,
                    "name": new_name,
                    "date_created": list.date_created,
                }
            )
            list_action(new_list, state)

        case 2:
            # Delete a list
            confirm = input(f"Are you sure you want to delete '{list.name}'? Y/N: ")
            if confirm == "Y" or confirm == "y":
                try:
                    call_proc(state.cur, "delete_list", [list.id])
                except DatabaseError as e:
                    print(e)
                    print("Error occurred when trying to delete this list")

                state.update_message(f"Deleted list '{list.name}'")
            list_module(state)

        case 3:
            # Return to the top level menu for all lists
            list_module(state)
