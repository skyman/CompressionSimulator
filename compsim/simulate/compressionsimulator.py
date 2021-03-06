# coding=utf-8
import datetime
import random

from . import Directions


class CompressionSimulator(object):
    def __init__(self, grid, bias):
        self.validate_grid(grid)

        self.grid = grid
        self.bias = float(bias)
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.rounds = 0
        self.movements = 0
        self.visited = {}

        self.property1_count = 0
        self.property2_count = 0

        self.iterations_run = 0

        self.probability_series = []

    @staticmethod
    def validate_grid(grid):
        if not (grid.particles_connected() and grid.particle_holes()):
            raise ValueError("CompressionSimulator connectivity conditions not met.")

    def run_iterations(self, iterations, classes_to_move=None):
        particles = list(self.grid.get_all_particles(classes_to_move))
        directions = Directions.ALL

        moves_made = 0
        for n in xrange(iterations):
            if self.move(random.choice(particles), random.choice(directions), random.random()):
                moves_made += 1
            self.iterations_run += 1

        return moves_made

    def get_bias(self, particle):
        return self.bias

    def get_move_probability(self, particle, current_location, new_location):
        current_neighbors = self.grid.neighbor_count(current_location)  # TODO: Check classes to move?
        new_neighbors = self.grid.neighbor_count(new_location) - 1  # TODO: Check classes to move?

        return self.get_bias(particle) ** (new_neighbors - current_neighbors)

    def move(self, random_particle, random_direction, probability, classes_to_move=None):
        # Check if new location is empty
        current_location = random_particle.axial_coordinates
        new_location = self.grid.get_position_in_direction(current_location, random_direction)

        if not self.grid.is_position_in_bounds(new_location):
            # New location out of board bounds
            # print("Bounds")
            return False

        if self.grid.get_particle(new_location) is not None:
            # There already is a particle at this new position
            # print("Existing", current_location, random_direction, new_location)
            return False

        if not self.valid_move(random_particle, current_location, new_location,
                               random_direction):  # TODO: Check classes to move?
            # print("Invalid")
            return False

        prob_move = self.get_move_probability(random_particle, current_location, new_location)
        # print("Prob: " + str(prob_move))
        self.probability_series.append(prob_move)

        if not probability < prob_move:  # Choose with probability
            # print probability
            return False

        self.grid.move_particle(current_location, new_location)

        # Movement counting
        self.movements += 1

        # Round checking
        self.visited[random_particle] = True
        for particle in self.grid.get_all_particles(classes_to_move):
            if not self.visited.get(particle, False):
                return True

        # If this point is reached, a round has completed
        self.rounds += 1
        self.visited = {}

        return True

    def valid_move(self, particle, old_position, new_position, direction):
        a = self.grid.neighbor_count(old_position) < 5
        b = self.property1(old_position, new_position, direction)
        c = self.property2(old_position, new_position, direction)

        if b:
            self.property1_count += 1
        if c:
            self.property2_count += 1

        return a and (b or c)

    def property1(self, old_position, new_position, direction, classes_to_consider=None):
        n1 = self.grid.get_neighbor_in_direction(old_position, Directions.shift_counterclockwise_by(direction, 5), classes_to_consider)
        n2 = self.grid.get_neighbor_in_direction(old_position, Directions.shift_counterclockwise_by(direction, 1), classes_to_consider)
        
        if n1 is not None or n2 is not None:
            neighbors1 = []
            neighbors2 = []

            for i in xrange(5):
                neighbors1.append(
                    self.grid.get_neighbor_in_direction(old_position,
                                                        Directions.shift_counterclockwise_by(direction, i + 1),
                                                        classes_to_consider) is not None)
                neighbors2.append(
                    self.grid.get_neighbor_in_direction(new_position,
                                                        Directions.shift_counterclockwise_by(direction, i + 4),
                                                        classes_to_consider) is not None)

            changes1 = 0
            changes2 = 0

            for n in xrange(4):
                if neighbors1[n] != neighbors1[n + 1]:
                    changes1 += 1

                if neighbors2[n] != neighbors2[n + 1]:
                    changes2 += 1

            return (changes1 < 3) and (changes2 < 3)
        else:
            return False

    def property2(self, old_position, new_position, direction, classes_to_consider=None):
        s1 = self.grid.get_neighbor_in_direction(old_position, Directions.shift_counterclockwise_by(direction, 5),
                                                 classes_to_consider)
        s2 = self.grid.get_neighbor_in_direction(old_position, Directions.shift_counterclockwise_by(direction, 1),
                                                 classes_to_consider)

        if s1 is None and s2 is None:
            if self.grid.neighbor_count(new_position, classes_to_consider) <= 1:
                return False

            if (self.grid.get_neighbor_in_direction(old_position, Directions.shift_counterclockwise_by(direction, 2),
                                                    classes_to_consider) is not None
                ) and (
                        self.grid.get_neighbor_in_direction(old_position,
                                                            Directions.shift_counterclockwise_by(direction, 3),
                                                            classes_to_consider) is None
            ) and (
                        self.grid.get_neighbor_in_direction(old_position,
                                                            Directions.shift_counterclockwise_by(direction, 4),
                                                            classes_to_consider) is not None
            ):
                return False

            if (self.grid.get_neighbor_in_direction(new_position, Directions.shift_counterclockwise_by(direction, 1),
                                                    classes_to_consider) is not None
                ) and (
                        self.grid.get_neighbor_in_direction(new_position,
                                                            Directions.shift_counterclockwise_by(direction, 0),
                                                            classes_to_consider) is None
            ) and (
                        self.grid.get_neighbor_in_direction(new_position,
                                                            Directions.shift_counterclockwise_by(direction, 5),
                                                            classes_to_consider) is not None
            ):
                return False

            return True
        else:
            return False

    def get_metrics(self, classes_to_move=None):
        metrics = [("Bias", "%.2f", self.bias),
                   ("Iterations", "%d", self.iterations_run),
                   ("Movements made", "%d", self.movements),
                   ("Rounds completed:", "%d", self.rounds),
                   ("Perimeter", "%d", self.grid.calculate_perimeter(classes_to_move)),
                   ("Center of mass", "x = %.2f, y = %.2f", tuple(self.grid.find_center_of_mass(classes_to_move)))]

        return metrics
