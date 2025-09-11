def adjust_workout(prev_sets, prev_reps, prev_load, feedback):
    """
    Adjusts workout based on user feedback.
    feedback: "easy", "just right", "hard"
    """
    new_sets = prev_sets
    new_reps = prev_reps
    new_load = prev_load

    if feedback == "easy":
        new_load += 2.5
        new_reps += 1
    elif feedback == "hard":
        new_load -= 2.5
        new_reps -= 1

    # Ensure values are reasonable
    new_reps = max(1, new_reps)
    new_load = max(0, new_load)

    return new_sets, new_reps, new_load
