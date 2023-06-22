from helpers import *
from source import main_menu, State
from pymysql import DatabaseError


class Recipe:
    """
    Represents a Recipe object
    """

    def __init__(self, recipe_dict: dict[str,]) -> None:
        self.id = recipe_dict.get("recipe_id")
        self.name = recipe_dict.get("name")
        self.instructions = recipe_dict.get("instructions")
        # number of seconds it takes to cook this recipe
        self.cooking_time = recipe_dict.get("cooking_time")
        # a list of categories this recipe belongs to
        self.categories = (
            recipe_dict.get("category_names").split(",")
            if recipe_dict.get("category_names")
            else []
        )

    def print_self(self) -> None:
        """
        Prints the textual information about this recipe
        """
        print(f"Name: {self.name}")
        print(f"Instructions: {self.instructions}")
        print(f"Cooking time: {self.cooking_time}")
        print(f"Categories: {self.categories}")


class Category:
    """
    Represents a category of recipes
    """

    def __init__(self, cat_dict: dict[str,]):
        self.id = cat_dict.get("category_id")
        self.name = cat_dict.get("name")
        self.num_recipes = cat_dict.get("recipe_num")

    def print_self(self):
        """
        Prints information about this category
        """
        print(f"Category Name: {self.name}")
        print(f"Number of recipes: {self.num_recipes}")


def recipe_module(state: State):
    """
    The top level menu to interact with recipes
    """
    cur = state.cur
    user_id = state.user_id
    clear_screen()

    state.print_message_reset()

    print_menu(
        "Select an action",
        [
            "Open existing recipe",
            "Create new recipe",
            "Categories",
            "Return to main menu",
        ],
    )

    choice = get_num_input(1, 4, "Go to")

    match choice:
        case 1:
            # Open an existing recipe
            recipes = call_proc(cur, "get_all_recipes_for_user", [user_id])

            recipe_ids = [row.get("recipe_id") for row in recipes]

            print_recipe_table(cur, user_id)

            choice = num_input_list_neg_one(
                recipe_ids, "Select a recipe ID or -1 to go back"
            )

            match choice:
                case -1:
                    recipe_module(state)
                    return
                case _:
                    recipe = Recipe(
                        [row for row in recipes if row.get("recipe_id") == choice][0]
                    )
                    recipe_action(recipe, state)

        case 2:
            # Create a new recipe
            name = input("Enter a name for the recipe: ")
            instructions = input("Enter the instructions for the recipe: ")
            cooking_time = safe_num_input(
                "Enter a cooking time (in seconds) for the recipe"
            )

            try:
                new_recipe = call_proc(
                    cur,
                    "create_recipe",
                    [name, instructions, cooking_time, user_id],
                )
            except DatabaseError as e:
                print(e)
                print("Could not create new recipe")
                recipe_module(state)
                return

            print("Add ingredients to the recipe")

            try:
                ingredients = call_proc(
                    cur, "get_all_ingredients_for_user", [state.user_id]
                )
            except DatabaseError as e:
                print(e)
                print("Error occurred when trying to fetch all of user's ingredients")

            ing_table_data = [row.values() for row in ingredients]

            print_table(["ID", "Name"], ing_table_data)

            # Loop for adding ingredients and amounts to the recipe
            while True:
                ing_id = safe_num_input(
                    "Enter an ingredient ID or -1 for no more ingredients"
                )
                if ing_id == -1:
                    break
                ing_amt = input(f"Enter an amount for ingredient ID {ing_id}: ")

                try:
                    call_proc(
                        cur,
                        "add_ingredient_to_recipe",
                        [ing_id, ing_amt, new_recipe[0].get("recipe_id")],
                    )
                except DatabaseError as e:
                    if e.args[0] == DUPLICATE_CODE:
                        print("Duplicate ingredient in the recipe is not allowed")
                    elif e.args[0] == NOT_FOUND_CODE:
                        print("This ingredient does not exist")
                    else:
                        print(e)
                        print("Could not add ingredient to recipe")

            print("\nAdd the recipe to categories")
            try:
                categories = call_proc(cur, "get_categories_for_user", [state.user_id])
            except DatabaseError as e:
                print(e)
                print("Error occurred when trying to fetch user's categories")

            print_table(["ID", "Name"], [row.values() for row in categories])

            # Loop for adding recipe to categories
            while True:
                cat_id = safe_num_input(
                    "Enter a category ID or -1 for no more categories"
                )

                if cat_id == -1:
                    break

                try:
                    call_proc(
                        cur,
                        "add_recipe_to_category",
                        [new_recipe[0].get("recipe_id"), cat_id],
                    )
                except DatabaseError as e:
                    if e.args[0] == DUPLICATE_CODE:
                        print("Duplicate recipe in a category is not allowed")
                    elif e.args[0] == NOT_FOUND_CODE:
                        print("This category does not exist")
                    else:
                        print(e)
                        print("Could not add recipe to category")

            state.update_message(
                f"Created new recipe with ID {new_recipe[0].get('recipe_id')}"
            )
            recipe_module(state)
            return
        case 3:
            # Category Menu
            print_menu(
                "\nSelect an action",
                ["View all categories", "Create new category", "Go back"],
            )
            choice = get_num_input(1, 3, "Go to")
            match choice:
                case 1:
                    # View all categories
                    clear_screen()
                    try:
                        categories = call_proc(
                            cur, "get_all_categories_for_user", [user_id]
                        )
                    except DatabaseError as e:
                        print(e)
                        print("Error occurred when trying to fetch user's categories")
                        recipe_module(state)
                        return

                    category_ids = [row.get("category_id") for row in categories]

                    print("Categories")
                    print_table(
                        ["ID", "Name", "Number of recipes"],
                        [row.values() for row in categories],
                    )

                    choice = num_input_list_neg_one(
                        category_ids,
                        "Choose a category to interact with or -1 to go back",
                    )
                    match choice:
                        case -1:
                            # Go back to recipe main menu
                            recipe_module(state)
                        case _:
                            # Enter a category
                            category = [
                                row
                                for row in categories
                                if row.get("category_id") == choice
                            ][0]
                            category_action(Category(category), state)

                case 2:
                    # Create a new category
                    name = input("Enter name for new category: ")

                    try:
                        new_cat_id = call_proc(cur, "create_category", [name, user_id])
                        new_cat_id = new_cat_id[0].get("category_id")
                    except DatabaseError as e:
                        if e.args[0] == DUPLICATE_CODE:
                            print("Cannot have duplicate category names")
                        else:
                            print("Error creating new category")
                        recipe_module(state)
                        return

                    print_recipe_table(cur, user_id)

                    # Loop for adding recipes to categories
                    while True:
                        choice = safe_num_input(
                            "Select a recipe ID or -1 to add no recipes to category"
                        )

                        if choice == -1:
                            break

                        try:
                            call_proc(
                                cur, "add_recipe_to_category", [choice, new_cat_id]
                            )
                        except DatabaseError as e:
                            if e.args[0] == DUPLICATE_CODE:
                                print("Duplicate recipe in a category is not allowed")
                            elif e.args[0] == NOT_FOUND_CODE:
                                print("This recipe does not exist")
                            else:
                                print("Could not add recipe to category")

                    recipe_module(state)
                    return
                case 3:
                    # Go back to the main recipe menu
                    recipe_module(state)
        case 4:
            # Go back to the main menu
            main_menu(state)


def recipe_action(recipe: Recipe, state: State):
    """
    Menu to interact with a specific Recipe that is given
    """
    cur = state.cur

    clear_screen()

    state.print_message_reset()

    try:
        ingredients = call_proc(cur, "get_ingredients_for_recipe", [recipe.id])
    except DatabaseError as e:
        print(e)
        print("Error occurred when trying to fetch all of user's ingredients")

    print("Recipe\n")
    recipe.print_self()

    print("\nIngredients:")
    print_table(
        ["Name", "Amount"],
        [(row.get("name"), row.get("amount")) for row in ingredients],
    )

    print_menu("Select an action", ["Edit", "Delete", "Go back"])
    choice = get_num_input(1, 3, "Go to")

    match choice:
        case 1:
            # Edit this recipe
            new_name = recipe.name
            new_instructions = recipe.instructions
            new_time = recipe.cooking_time

            edit_name = input(f"Edit {recipe.name}'s name? Y/N: ")
            if edit_name == "y" or edit_name == "Y":
                new_name = input(f"Enter a new name for {recipe.name}: ")

            edit_instructions = input(f"Edit {recipe.name}'s instructions? Y/N: ")
            if edit_instructions == "y" or edit_instructions == "Y":
                new_instructions = input(f"Enter new instructions for {recipe.name}: ")

            edit_time = input(f"Edit {recipe.name}'s cooking time? Y/N: ")
            if edit_time == "y" or edit_time == "Y":
                new_time = input(f"Enter new cooking time for {recipe.name}: ")

            try:
                call_proc(
                    cur,
                    "update_recipe",
                    [new_name, new_instructions, new_time, recipe.id],
                )
            except DatabaseError as e:
                if e.args[0] == DUPLICATE_CODE:
                    print("Duplicated recipe names are not allowed")
                else:
                    print(e)
                    print("Error updating recipe")
            finally:
                update_msg = f"Updated recipe '{recipe.name}'"

            if new_name != recipe.name:
                update_msg += f" to '{new_name}'"

            if new_instructions != recipe.instructions:
                update_msg += " with new instructions"

            if new_time != recipe.cooking_time:
                update_msg += " to have a new cooking time"

            print("\nUpdate the ingredients in this recipe")

            try:
                ingredients = call_proc(cur, "get_ingredients_for_recipe", [recipe.id])
            except DatabaseError as e:
                print(e)
                print("Error occurred when trying to fetch recipe's ingredients")

            print_table(
                ["ID", "Name", "Amount"],
                [
                    (row.get("ingredient_id"), row.get("name"), row.get("amount"))
                    for row in ingredients
                ],
            )

            # Updating ingredients loop
            while True:
                print_menu(
                    "\nChoose an action",
                    [
                        "Add ingredients",
                        "Remove ingredients",
                        "Update ingredients",
                        "Skip",
                    ],
                )
                choice = get_num_input(1, 4, "Do")

                match choice:
                    case 1:
                        # Add ingredient to recipe
                        print_ingredient_table(cur, state.user_id)

                        # Loop to input ingredients + amounts
                        while True:
                            ing_id = safe_num_input(
                                f"Choose an ingredient ID to add to {new_name} or -1 to cancel"
                            )

                            if ing_id == -1:
                                break

                            amt = input("Enter an amount: ")

                            try:
                                call_proc(
                                    cur,
                                    "add_ingredient_to_recipe",
                                    [ing_id, amt, recipe.id],
                                )
                            except DatabaseError as e:
                                if e.args[0] == DUPLICATE_CODE:
                                    print(
                                        "Duplicate ingredients are not allowed in a recipe"
                                    )
                                if e.args[0] == NOT_FOUND_CODE:
                                    print("Entered ingredient ID does not exist")
                                else:
                                    print("Error adding ingredient to recipe")
                            finally:
                                if not " to have different ingredients" in update_msg:
                                    update_msg += " to have different ingredients"

                        continue

                    case 2:
                        # Remove ingredients from recipe
                        while True:
                            print_table(
                                ["ID", "Name", "Amount"],
                                [
                                    (
                                        row.get("ingredient_id"),
                                        row.get("name"),
                                        row.get("amount"),
                                    )
                                    for row in ingredients
                                ],
                            )

                            ing_id = safe_num_input(
                                f"Choose an ingredient ID to remove from {new_name} or -1 to cancel"
                            )

                            if ing_id == -1:
                                break

                            try:
                                call_proc(
                                    cur,
                                    "remove_ingredient_from_recipe",
                                    [recipe.id, ing_id],
                                )
                            except DatabaseError as e:
                                print(e)
                                print("Error removing ingredient from recipe")
                            finally:
                                if not " to have different ingredients" in update_msg:
                                    update_msg += " to have different ingredients"

                        continue
                    case 3:
                        # Update ingredients in recipe

                        # Flag for determining if this is the first time adding ingredients
                        first_time_add_ing = True

                        for row in ingredients:
                            edit = input(
                                f"Would you like to edit {row.get('name')}? Y/N: "
                            )
                            if edit == "y" or edit == "Y":
                                if first_time_add_ing:
                                    if (
                                        not " to have different ingredients"
                                        in update_msg
                                    ):
                                        update_msg += " to have different ingredients"
                                    first_time_add_ing = False
                                    print_ingredient_table(cur, state.user_id)
                                new_ing_id = safe_num_input(
                                    f"Choose an ingredient ID to replace {row.get('name')} with"
                                )
                                new_amt = input(
                                    f"Enter a new amount for ingredient ID {new_ing_id}: "
                                )

                                try:
                                    call_proc(
                                        cur,
                                        "update_recipe_ingredient",
                                        [
                                            recipe.id,
                                            row.get("ingredient_id"),
                                            new_ing_id,
                                            new_amt,
                                        ],
                                    )
                                except DatabaseError as e:
                                    if e.args[0] == NOT_FOUND_CODE:
                                        print(
                                            "The newly entered ingredient ID does not exist"
                                        )
                                    else:
                                        print(e)
                                        print("Error updating this recipe ingredient")

                        continue
                    case 4:
                        # Skip or stop updating ingredients
                        break

            print("\nUpdate the categories this recipe is in\n")

            try:
                categories = call_proc(
                    cur, "get_all_categories_for_user", [state.user_id]
                )
            except DatabaseError as e:
                print(e)
                print("Error occurred when trying to fetch all of user's categories")

            print_table(
                ["ID", "Name", "Number of recipes"],
                [row.values() for row in categories],
            )

            while True:
                print_menu(
                    "Choose an action",
                    [
                        f"Add {new_name} to category",
                        f"Remove {new_name} from category",
                        "Skip",
                    ],
                )
                choice = get_num_input(1, 3, "Go to")

                match choice:
                    case 1:
                        # Add recipe to category
                        while True:
                            choice = safe_num_input(
                                f"Enter a category ID to add {new_name} to or -1 to cancel"
                            )

                            if choice == -1:
                                break

                            try:
                                call_proc(
                                    cur, "add_recipe_to_category", [recipe.id, choice]
                                )
                            except DatabaseError as e:
                                if e.args[0] == DUPLICATE_CODE:
                                    print("Cannot have duplicate recipes in a category")
                                elif e.args[0] == NOT_FOUND_CODE:
                                    print("Category ID not found")
                                else:
                                    print(e)
                                    print(
                                        "There was an error adding this recipe to the category"
                                    )

                            if " with different categories" not in update_msg:
                                update_msg += " with different categories"

                    case 2:
                        # Remove recipe from category
                        try:
                            categories = call_proc(
                                cur, "get_categories_for_recipe", [recipe.id]
                            )
                        except DatabaseError as e:
                            print(e)
                            print(
                                "Error occurred when trying to fetch this recipe's categories"
                            )

                        print_table(
                            ["ID", "Name"], [row.values() for row in categories]
                        )

                        while True:
                            choice = safe_num_input(
                                f"Enter a category ID to remove {new_name} from or -1 to cancel"
                            )

                            if choice == -1:
                                break

                            try:
                                call_proc(
                                    cur,
                                    "remove_recipe_from_category",
                                    [recipe.id, choice],
                                )
                            except DatabaseError as e:
                                if e.args[0] == NOT_FOUND_CODE:
                                    print(
                                        "Recipe is already not in the category or the category does not exist"
                                    )
                                else:
                                    print(e)
                                    print(
                                        "There was an error removing this recipe from the category"
                                    )

                            if " with different categories" not in update_msg:
                                update_msg += " with different categories"

                        continue

                    case 3:
                        # Skip changing categories for recipe
                        break

            state.update_message(update_msg)
            try:
                categories = call_proc(cur, "get_categories_for_recipe", [recipe.id])
            except DatabaseError as e:
                print(e)
                print(
                    "Error occurred when trying to fetch all the categories for this recipe"
                )

            # New recipe with updated attributes
            new_recipe = Recipe(
                {
                    "recipe_id": recipe.id,
                    "name": new_name,
                    "instructions": new_instructions,
                    "cooking_time": new_time,
                    "category_names": ",".join([row.get("name") for row in categories]),
                }
            )
            recipe_action(new_recipe, state)
        case 2:
            # Delete a recipe
            confirm = input(f"Are you sure you want to delete '{recipe.name}'? Y/N: ")
            if confirm == "Y" or confirm == "y":
                try:
                    call_proc(cur, "delete_recipe", [recipe.id])
                except DatabaseError as e:
                    print(e)
                    print("Error occurred when trying to delete this recipe")
                finally:
                    state.update_message(f"Deleted recipe '{recipe.name}'")

            recipe_module(state)
        case 3:
            recipe_module(state)


def category_action(category: Category, state: State):
    """
    Menu to interact with a specific category that is given
    """
    clear_screen()

    state.print_message_reset()

    category.print_self()

    print_menu("Choose an action", ["Edit", "Delete", "Go back"])
    choice = get_num_input(1, 3, "Go to")
    match choice:
        case 1:
            # Edit this category's name
            new_name = input(f"Enter a new name for category '{category.name}': ")

            try:
                call_proc(state.cur, "update_category_name", [category.id, new_name])
            except DatabaseError as e:
                if e.args == DUPLICATE_CODE:
                    print("Duplicate category names are not allowed")
                else:
                    print("Error updating category")

            state.update_message(f"Changed category '{category.name}' to '{new_name}'")

            recipe_module(state)

        case 2:
            # Delete this category
            confirm = input(f"Are you sure you want to delete '{category.name}'? Y/N: ")
            if confirm == "Y" or confirm == "y":
                try:
                    call_proc(state.cur, "delete_category", [category.id])
                except DatabaseError as e:
                    print(e)
                    print("Error occurred when trying to delete this category")
                finally:
                    state.update_message(f"Deleted category '{category.name}'")

            recipe_module(state)

        case 3:
            # Go back to the main recipe menu
            recipe_module(state)
