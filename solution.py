import copy

assignments = []

puzzle = None

class SudokuPuzzle:
    def __init__(self, row_labels, col_labels):
        """
        Initializes the sudoku puzzle
        :param row_labels(string) -  Labels for the rows of the sudoku grid
        :param col_labels(string) - Labels for the columns of the sudoku grid
        """
        assert len(row_labels) == len(col_labels) and len(row_labels) == 9, "Invalid Sudoku Configuration, there should be 9 rows and 9 columns"
        self.row_labels = row_labels
        self.col_labels = col_labels
        self.boxes = cross(row_labels, col_labels)
        row_units = [cross(row_label, col_labels) for row_label in row_labels]
        col_units = [cross(row_labels, col_label) for col_label in col_labels]
        square_units = [cross(rows, cols) for rows in [row_labels[:3], row_labels[3:6], row_labels[6:]] \
                for cols in [col_labels[:3], col_labels[3:6], col_labels[6:]]]
        diagonal_units = [[row + col for row, col in zip(row_labels, col_labels)]] + \
                         [[row + col for row, col in zip(row_labels, col_labels[-1::-1])]]
        self.unitlist = row_units + col_units + square_units + diagonal_units
        self.units = dict([(box, [u for u in self.unitlist if box in u]) for box in self.boxes])
        self.peers = dict([(box , set(sum(self.units[box], [])) - set([box])) for box in self.boxes])

def assign_value(values, box, value):
    """
    Please use this function to update your values dictionary!
    Assigns a value to a given box. If it updates the board record it.
    """

    # Don't waste memory appending actions that don't actually change any values
    if values[box] == value:
        return values

    values[box] = value
    if len(value) == 1:
        assignments.append(values.copy())
    return values

def naked_twins(values):
    """Eliminate values using the naked twins strategy.
    Args:
        values(dict): a dictionary of the form {'box_name': '123456789', ...}

    Returns:
        the values dictionary with the naked twins eliminated from peers.
    """
    global puzzle
    # initialize puzzle if not done so
    if not puzzle:
        puzzle = SudokuPuzzle('ABCDEFGHI', '123456789')
    for unit in puzzle.unitlist:
        # Find all instances of naked twins
        pairs_boxes = {}
        for box in unit:
            candidates = values[box]
            if len(candidates) == 2:
                # sort the candidates for the box so that order is maintained
                sorted_pair = ''.join(sorted(candidates))
                # populate the dictionary with pair counts
                if sorted_pair in pairs_boxes:
                    pairs_boxes[sorted_pair] += [box]
                else:
                    pairs_boxes[sorted_pair] = [box]
        # Eliminate possible values for other boxes in the same unit based on the naked twins
        for (pair, boxes) in pairs_boxes.items():
            if len(boxes) == 2:
                for box in unit:
                    # for all boxes in unit except the twin boxes
                    if box not in boxes:
                        candidates = values[box]
                        candidates = candidates.replace(pair[0], '')
                        candidates = candidates.replace(pair[1], '')
                        assign_value(values, box, candidates)
    return values

def cross(A, B):
    "Cross product of elements in A and elements in B."
    return [a + b for a in A for b in B]

def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.
    Args:
        grid(string) - A grid in string form.
    Returns:
        A grid in dictionary form
            Keys: The boxes, e.g., 'A1'
            Values: The value in each box, e.g., '8'. If the box has no value, then the value will be '123456789'.
    """
    assert len(grid) == 81, "Invalid Sudoku Grid Initialization, there should be 81 boxes"
    transform = lambda v: v if v != '.' else puzzle.col_labels
    return dict([(box, transform(value)) for box, value in zip(puzzle.boxes, grid)])

def display(values):
    """
    Display the values as a 2-D grid.
    Args:
        values(dict): The sudoku in dictionary form
    """
    global puzzle
    width = 1 + max(len(values[s]) for s in puzzle.boxes)
    line = '+'.join(['-' * (width * 3)] * 3)
    for r in puzzle.row_labels:
        print(''.join(values[r + c].center(width) + ('|' if c in '36' else '')
                      for c in puzzle.col_labels))
        if r in 'CF': print(line)
    return

def eliminate(values):
    """
    Eliminates assigned value for a box from all its peers
    :param values(dict): A dictionary of the form {'box_name': '123456789', ...}
    :return: A grid in dictionary form
            Keys: The boxes, e.g., 'A1', 'B2', etc.
            Values: The possible value that can be filled in each box, e.g., '8', '145', '39', etc.
    """
    for box in values.keys():
        candidates = values[box]
        if len(candidates) == 1:
            peers = puzzle.peers[box]
            for peer in peers:
                peer_candidates = values[peer]
                assign_value(values, peer, peer_candidates.replace(candidates[0], ''))
    return values

def only_choice(values):
    """
    Assigns those values to boxes that occur only once in a box in a given unit.
    Here a unit may refer to a row, a column, a 3x3 subsquare or a diagonal
    :param values(dict): A dictionary of the form {'box_name': '123456789', ...}
    :return: A grid in dictionary form
            Keys: The boxes, e.g., 'A1', 'B2', etc.
            Values: The possible value that can be filled in each box, e.g., '8', '145', '39', etc.
    """
    for unit in puzzle.unitlist:
        candidates_count = {}
        # count occurence of all candidate values in all boxes in a particular unit
        for candidate in ''.join([values[box] for box in unit]):
            if candidate in candidates_count:
                candidates_count[candidate] += 1
            else:
                candidates_count[candidate] = 1
        for box in unit:
            for candidate in values[box]:
                # if a particular candidate value occurs only once in an unit, assign it to the box
                if candidates_count[candidate] == 1:
                    assign_value(values, box, candidate)
                    break
    return values

def reduce_puzzle(values):
    """
    Reduces the number of unassigned boxes in the grid by applying various constraint propagation techniques iteratively
    such as elimination, only choice and naked twins. If suppose in a particular iteration there is no reduction in the 
    number of unassigned boxes, the method returns the current grid
    :param values(dict): A dictionary of the form {'box_name': '123456789', ...}
    :return: A grid in dictionary form or an empty grid in case the grid is reduced to an invalid grid (no values available
    to fill a particular box)
            Keys: The boxes, e.g., 'A1', 'B2', etc.
            Values: The possible value that can be filled in each box, e.g., '8', '145', '39', etc.
    """
    stalled = False
    while not stalled:
        filled_count_before = sum([1 for box in values.keys() if len(values[box]) == 1])
        values = eliminate(values)
        values = only_choice(values)
        values = naked_twins(values)
        filled_count_after = sum([1 for box in values.keys() if len(values[box]) == 1])
        if filled_count_after == filled_count_before:
            stalled = True
        if any([len(values[box]) == 0 for box in values.keys()]):
            return {}
    return values

def search(values):
    """
    Searches for a valid solution to the sudoku puzzle (one among many possible).
    Use contraint propagation along with DFS based backtracking to find the solution for every sudoku puzzle.
    :param values: a dictionary of the form {'box_name': '123456789', ...} 
    :return: A grid in dictionary form in which all boxes are assigned values according to constraints
            Keys: The boxes, e.g., 'A1', 'B2', etc.
            Values: The value assigned to each box, e.g., '8', '1', '9', etc.
    """
    values = reduce_puzzle(values)
    if not values or all([len(values[box]) == 1 for box in values]):
        return values
    least_unfilled_box, _ = min([(box, len(values[box])) for box in values.keys() if len(values[box]) > 1], key = lambda x: x[1])
    for candidate in values[least_unfilled_box]:
        copy_values = copy.deepcopy(values)
        copy_values[least_unfilled_box] = candidate
        solution = search(copy_values)
        if solution:
            return solution
    return {}

def solve(grid):
    """
    Find the solution to a Sudoku grid.
    Args:
        grid(string): a string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        The dictionary representation of the final sudoku grid. False if no solution exists.
    """
    global puzzle
    puzzle = SudokuPuzzle('ABCDEFGHI', '123456789')
    solution = search(grid_values(grid))
    print(display(solution))
    return solution

if __name__ == '__main__':
    #diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    diag_sudoku_grid = '....4......1...3...2.....5....7.5...8.......6...2.8....5.....8...4...5......1....'
    solve(diag_sudoku_grid)
    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
