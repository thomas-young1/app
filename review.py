from source import State, main_menu
from helpers import *
from pymysql import DatabaseError


class Review:
    """
    Represents a Review of a recipe and the data associated with it
    """

    def __init__(self, rev_dict: dict[str,]):
        self.id = rev_dict.get("review_id")
        self.recipe_name = rev_dict.get("recipe_name")
        self.rating = rev_dict.get("rating")
        self.creator_id = rev_dict.get("user_id")
        self.creator_name = rev_dict.get("creator_name")
        self.review_text = rev_dict.get("review_text")

    def print_self(self):
        print(f"Recipe: {self.recipe_name}")
        print(f"Rating: {self.rating}/10")
        print(f"Review: {self.review_text}")
        print(f"Creator: {self.creator_name}")


def review_module(state: State):
    """
    Top level menu to interact with reviews
    """
    clear_screen()

    state.print_message_reset()

    cur = state.cur

    print_menu("Choose an action", ["View all reviews", "Create new review", "Go back"])
    choice = get_num_input(1, 3, "Go to")

    match choice:
        case 1:
            # View all reviews
            try:
                reviews = call_proc(cur, "get_all_reviews")
            except DatabaseError as e:
                print(e)
                print("Error occurred when trying to fetch all reviews")
                review_module(state)
                return

            review_table_data = [
                (
                    row.get("review_id"),
                    row.get("recipe_name"),
                    str(row.get("rating")) + "/10",
                    row.get("creator_name"),
                )
                for row in reviews
            ]

            review_ids = [row.get("review_id") for row in reviews]

            print_table(
                ["ID", "Recipe Name", "Rating", "Creator Name"], review_table_data
            )

            choice = num_input_list_neg_one(
                review_ids, "Select a review ID or -1 to go back"
            )

            match choice:
                case -1:
                    review_module(state)
                    return
                case _:
                    r_obj = Review(
                        [row for row in reviews if row.get("review_id") == choice][0]
                    )

                    review_action(r_obj, state)

        case 2:
            # Create a new review
            recipe_ids = print_recipe_table(cur, state.user_id)

            while True:
                r_id = safe_num_input("Choose a recipe to review or -1 to cancel")

                if r_id not in recipe_ids:
                    print("Invalid ID, try again")
                    continue

                break

            if r_id == -1:
                review_module(state)
                return

            while True:
                rating = safe_num_input("Enter a rating out of ten")

                if rating >= 0 and rating <= 10:
                    break

                print("Rating must be between 0 and 10")

            text = input("Enter the body of your review: ")

            try:
                new_rev_id = call_proc(
                    cur, "create_review", [r_id, rating, text, state.user_id]
                )
            except DatabaseError as e:
                print("Error creating review")
            finally:
                new_rev_id = new_rev_id[0].get("review_id")
                state.update_message(f"Created new review with ID {new_rev_id}")

            review_module(state)
        case 3:
            # Go back the main menu
            main_menu(state)


def review_action(review: Review, state: State):
    """
    Menu to interact with a specific review that is given
    """
    clear_screen()

    state.print_message_reset()

    review.print_self()

    # Only allow the user to edit or delete a review if they are the creator
    if review.creator_id == state.user_id:
        print_menu("\nSelect an action", ["Edit", "Delete", "Go back"])
        choice = get_num_input(1, 3, "Go to")

        update_msg = f"Updated review for {review.recipe_name}"
        edited = False

        match choice:
            case 1:
                # Edit the review
                while True:
                    print_menu(
                        "\nSelect an action", ["Edit rating", "Edit text", "Go back"]
                    )
                    choice = get_num_input(1, 3, "Go to")
                    match choice:
                        case 1:
                            # Edit the review's rating
                            while True:
                                new_rating = safe_num_input(
                                    f"Change rating for {review.recipe_name} from {review.rating} to"
                                )
                                if new_rating >= 0 and new_rating <= 10:
                                    break

                                print("Rating must be between 0 and 10")

                            try:
                                call_proc(
                                    state.cur,
                                    "update_review_rating",
                                    [review.id, new_rating],
                                )
                            except DatabaseError as e:
                                print(e)
                                print(
                                    "An error occurred when trying to update the review's rating"
                                )
                            finally:
                                edited = True
                                if " with a new rating" not in update_msg:
                                    update_msg += " with a new rating"

                        case 2:
                            # Edit the review's text
                            new_text = input(f"Change text for review to: ")

                            try:
                                call_proc(
                                    state.cur,
                                    "update_review_text",
                                    [review.id, new_text],
                                )
                            except DatabaseError as e:
                                print(e)
                                print(
                                    "An error occurred when trying to update the review's rating"
                                )
                            finally:
                                edited = True
                                if " with different text" not in update_msg:
                                    update_msg += " with different text"
                        case 3:
                            # Return to this review's menu
                            break

                if not edited:
                    review_action(review, state)
                else:
                    new_rev = Review(
                        {
                            "review_id": review.id,
                            "recipe_name": review.recipe_name,
                            "rating": new_rating or review.rating,
                            "user_id": review.creator_id,
                            "creator_name": review.creator_name,
                            "review_text": new_text or review.review_text,
                        }
                    )
                    state.update_message(update_msg)
                    review_action(new_rev, state)
            case 2:
                # Delete this review
                confirm = input(
                    f"Are you sure you want to delete your review for '{review.recipe_name}'? Y/N: "
                )
                if confirm == "Y" or confirm == "y":
                    try:
                        call_proc(state.cur, "delete_review", [review.id])
                    except DatabaseError as e:
                        print(e)
                        print("Error occurred when trying to delete this review")
                    finally:
                        state.update_message(
                            f"Deleted review for '{review.recipe_name}'"
                        )

                review_module(state)
            case 3:
                # Return to the top level review menu
                review_module(state)

    # Menu for a user who did not create this review
    else:
        print_menu("\nChoose an action", ["Go back"])
        choice = get_num_input(1, 1, "Go to")
        match choice:
            case 1:
                review_module(state)
