
import pygame
import pygame.freetype  # Import the freetype module.

import numpy as np
import uuid
from parameters import CENTER_COORDS, NUM_GENESIS_LAND
from parameters import PRODUCER_INCOME, PRODUCER_COST, WEAPON_COST
from parameters import XCOLS, YROWS, CELLSIZE

from colors import COLOR_GENESIS_LAND, COLOR_EMPTY, COLOR_BACKGROUND, COLOR_CENTER_BACKGROUND
from colors import BLACK, GREY
from colors import RED, RED_LIGHT
from colors import GREEN, GREEN_LIGHT
from colors import BLUE, BLUE_LIGHT
from colors import PURPLE, PURPLE_LIGHT


STARTX = 20
STARTY = 20




class Copium:

    def __init__(self, xcols, yrows, initial_genesis_plots=[(STARTX, STARTY)]):
        # note x,y flipped to rows, cols
        cells = np.zeros((yrows, xcols))
        cellStats = cells.tolist()
        bears = {}
        # center = CENTER_COORDS
        center = (int(np.round(yrows)), int(np.round(xcols)))

        for r, c in np.ndindex(cells.shape):

            if len(list(filter(lambda g: r == g[0] and c == g[1], initial_genesis_plots))) > 0:
                cstats = endow_land_stats(r, c, is_genesis=True)
            else:
                cstats = endow_land_stats(r, c, is_genesis=False)

            cellStats[r][c] = cstats
            cells[r][c] = cstats['genesis']

            if cstats['genesis'] == 1:
                bear_stats = endow_bear()
                owner = generate_short_addr()
                bears[owner] = {
                    'owner': owner,
                    'genesis_position': (r, c),
                    'copium': bear_stats['copium'],
                    'producers': bear_stats['producers'],
                    'weapons': bear_stats['weapons'],
                    'lands': [(r, c)]
                }
                # import 1 producer from bear to genesis cellstats
                cellStats[r][c]['owner'] = owner
                cellStats[r][c]['producers'] = 10

        self.xcols = xcols
        self.yrows = yrows
        self.cells = cells
        self.cellStats = cellStats
        self.bears = bears
        self.center = center


    def __repr__(self):
        owner = list(self.bears.items())[0][1]
        return """
        owner: {}
        copium: {}
        producers: {}
        weapons: {}
        lands: {}
        """.format(
            owner['owner'],
            owner['copium'],
            owner['producers'],
            owner['weapons'],
            len(owner['lands']),
        )


    def tryMoveWeapons(self, current_cell, adjacent_cell, number_of_weapons, owner):
        c0 = current_cell[0]
        c1 = current_cell[1]
        a0 = adjacent_cell[0]
        a1 = adjacent_cell[1]

        # check you have weapons to explore
        if owner:
            if self.bears[owner]['weapons'] - number_of_weapons < 0:
                return False
        else:
            if self.cellStats[c0][c1]['weapons'] - number_of_weapons < 0:
                return False

        # you must own current cell to move from it
        if self.cellStats[c0][c1]['owner'] == None:
            return False

        # you can only explore land if there is no preexisting owner on it
        if self.cellStats[a0][a1]['owner'] != None:
            return False
        else:
            # 1. either remove weapons from owner's wallet or from adjacent owned cell
            if owner:
                self.bears[owner]['weapons'] -= number_of_weapons
            else:
                self.cellStats[c0][c1]['weapons'] -= number_of_weapons

            # must use self.cellStats when updating state
            # update new cell with weapons, and update owner
            self.cellStats[a0][a1]['weapons'] += number_of_weapons
            self.cellStats[a0][a1]['owner'] = self.cellStats[c0][c1]['owner']
            return True


    def tryStakeProducers(self, cell, number_of_producers, owner):
        a0 = cell[0]
        a1 = cell[1]

        if self.cellStats[a0][a1]['owner'] != owner:
            return False
        else:
            # must use self.cellStats when updating state
            self.cellStats[a0][a1]['producers'] += number_of_producers
            self.bears[owner]['producers'] -= number_of_producers
            return True


    def buy_producers(self, owner):
        # spend half of balance to buy producers
        if self.bears[owner]['copium']/2 > PRODUCER_COST:
            num_producers = np.floor(self.bears[owner]['copium']/2 / 100)
        else:
            num_producers = 0

        total_cost = num_producers * PRODUCER_COST
        self.bears[owner]['copium'] -= total_cost
        self.bears[owner]['producers'] += num_producers
        print("Bought {} producers".format(num_producers))


    def buy_weapons(self, owner):
        # spend half of balance to buy weapons
        if self.bears[owner]['copium'] > WEAPON_COST:
            num_weapons = np.floor(self.bears[owner]['copium']/2 / 100)
        else:
            num_weapons = 0

        total_cost = num_weapons * WEAPON_COST
        self.bears[owner]['copium'] -= total_cost
        self.bears[owner]['weapons'] += num_weapons
        print("Bought {} weapons".format(num_weapons))


    def get_cell_stats(self, coords):
        return self.cellStats[coords[0]][coords[1]]


    def harvest_copium(self, owner):
        print("\nOwner: ", owner)
        print("copium before: ", self.bears[owner]['copium'])
        total_profits = 0
        for row in self.cellStats:
            for cell in row:
                if cell['owner'] == owner:
                    profit = cell['producers'] * PRODUCER_INCOME
                    total_profits += profit

        self.bears[owner]['copium'] += total_profits
        print("copium after: ", self.bears[owner]['copium'])


    def harvest_all_user_copium(self):
        for owner in self.bears.keys():
            self.harvest_copium(owner)

    def distance_from_genesis(self, x, y, owner_addr):
        genesis_position = self.bears[owner_addr]['genesis_position']
        gx = genesis_position[0]
        gy = genesis_position[1]
        return np.sqrt( (x - gx)**2 + (y - gy)**2 )


    def place_producers(self, bear):

        owner = bear['owner']
        strategies_and_scores = []

        # get all lands and their capacities and deployed producers
        for current_land in bear['lands']:
            cell = self.get_cell_stats(current_land)
            if cell['capacity'] > cell['producers']:
                strategies_and_scores.append({
                    'current_cell': current_land,
                    'distance': self.distance_from_genesis(current_land[0], current_land[1], owner),
                })


        # get number of producers you can deploy this round
        budget = bear['producers']
        # sort exploration opportunities by distance from genesis land, lower is better
        strategies_and_scores.sort(key=lambda x: x['distance'], reverse=False)

        # place producers, subject to budget constraints
        for strat in strategies_and_scores:
            c = self.get_cell_stats(strat['current_cell'])
            excess_capacity = cell['capacity'] - cell['producers']

            if self.bears[owner]['producers'] - 1 >= 0:
                placedProducer = self.tryStakeProducers(
                    strat['current_cell'],
                    1, # stake 1 producer
                    owner,
                )


    def explore_with_weapons(self, bear):

        owner = bear['owner']
        strategies_and_scores = []

        # get all adajacent lands and their scores
        for current_land in bear['lands']:
            adj_cells = get_adjacent_cells(current_land[0], current_land[1])
            for adj_coord in adj_cells:
                cell = self.get_cell_stats(adj_coord)
                if cell:
                    cellcapacity = cell['capacity']
                    strategies_and_scores.append({
                        'current_cell': current_land,
                        'destination_cell': adj_coord,
                        'capacity_score': cellcapacity,
                    })


        # get number of producers you can deploy this round
        budget = bear['weapons']
        # sort exploration opportunities by capacity_score, higher is better so reverse it
        strategies_and_scores.sort(key=lambda x: x['capacity_score'], reverse=True)
        bear_new_lands = []

        # start exploring, highest ROI lands first, subject to budget constraints
        for strat in strategies_and_scores:
            # try use adjacent weapons, if none, use weapons in wallet
            ccell = self.get_cell_stats(strat['current_cell'])
            if ccell['owner'] == owner and ccell['weapons'] > 0:
                placedLand = self.tryMoveWeapons(
                    strat['current_cell'],
                    strat['destination_cell'],
                    1, # use 1 weapon to explore
                    None, # not using weapons from owner's wallet,
                    # use weapon from adjacent cell
                )
                if placedLand:
                    bear_new_lands.append(strat['destination_cell'])

            elif self.bears[owner]['weapons'] - 1 >= 0:
                placedLand = self.tryMoveWeapons(
                    strat['current_cell'],
                    strat['destination_cell'],
                    1, # use 1 weapon to explore
                    owner,
                )
                if placedLand:
                    bear_new_lands.append(strat['destination_cell'])

        self.bears[owner]['lands'] += bear_new_lands


    # def find_highest_value_expansions(self, adjacent_cells):


    # def attack_enemy(self):



    def updateGameState(self, block):

        for owner, bear in self.bears.items():

            # harvest copium every block
            if block % 1 == 0:
                self.harvest_copium(owner)

            if block % 5 == 0:
                # need to budget between producers and weapons
                # sometimes spending on producers will stop you from buying weapons
                self.buy_producers(owner)
                self.buy_weapons(owner)

            # allow weapons placement every 5 blocks
            if block % 5 == 0:
                self.explore_with_weapons(bear)
                self.place_producers(bear)

        # 1. define a strategy for the round
        # 2. for all land, calculate the strategy_score for each land
        # 3. get the user's budget for this round
        # 4. execute highest value actions, subject to budget


    def renderUpdate(self, surface, sz):

        font = pygame.font.SysFont(None, 24)

        bear1 = list(self.bears.items())[0][1]
        bear2 = list(self.bears.items())[1][1]

        for r, c in np.ndindex(self.cells.shape):

            cell = self.cells[r, c]
            cellStats = self.cellStats[r][c]

            if cellStats['genesis'] == 1:
                col = COLOR_GENESIS_LAND
            elif cellStats['owner'] == bear1['owner']:
                col = PURPLE_LIGHT
            elif cellStats['owner'] == bear2['owner']:
                col = BLUE_LIGHT
            elif cellStats['owner'] != None:
                col = COLOR_EMPTY
            elif cellStats['producers'] > 0:
                col = BLUE_LIGHT
            elif in_center_of_grid(r, c):
                col = COLOR_CENTER_BACKGROUND
            elif cellStats['genesis'] == 0:
                col = COLOR_BACKGROUND

            pygame.draw.rect(surface, col, (c*sz, r*sz, sz-1, sz-1))

            # render text on top
            if cellStats['genesis'] == 1:
                img = font.render(str(cellStats['capacity']), True, GREY)
                surface.blit(img, (c*sz+6, r*sz+6))
            elif cellStats['weapons'] > 0:
                img = font.render(str(cellStats['weapons']), True, RED)
                surface.blit(img, (c*sz+6, r*sz+6))
            elif cellStats['producers'] > 0:
                img = font.render(str(cellStats['producers']), True, BLUE)
                surface.blit(img, (c*sz+6, r*sz+6))
            else:
                img = font.render(str(cellStats['capacity']), True, GREY)
                surface.blit(img, (c*sz+6, r*sz+6))





def within_grid(x, y, xcols=XCOLS, yrows=YROWS):
    return (0 <= x < xcols) and (0 <= y < yrows)

def get_adjacent_cells(x, y):
    acells = [
        (x, y-1),
        (x-1, y-1),
        (x-1, y),
        (x-1, y+1),
        (x, y+1),
        (x+1, y+1),
        (x+1, y),
        (x+1, y-1),
    ]
    return list(filter(lambda coords: within_grid(coords[0], coords[1]), acells))

def in_center_of_grid(x, y):
    """If inside the 1/9 center section of the map"""
    if (9 <= x < 18) and (9 <= y < 18):
        return True
    else:
        return False

def distance_from_center(x, y):
    return np.sqrt( (x - CENTER_COORDS[0])**2 + (y - CENTER_COORDS[1])**2 )

def endow_land_stats(x, y, is_genesis=True):
    position = (x, y)
    capacity = rng_capacity(x, y)
    inCenter = in_center_of_grid(x, y)
    if inCenter:
        genesis = 0
    else:
        if is_genesis:
            genesis = 1
        else:
            genesis = 0

    return {
        "position": position,
        "capacity": capacity,
        "producers": 0,
        "weapons": 0,
        "genesis": genesis,
        "owner": None,
    }


def endow_bear():
    # copium = np.round(np.random.uniform(4,10) * 1000)
    copium = 0
    producers = np.round(np.random.uniform(8, 16))
    weapons = np.round(np.random.uniform(4, 10))
    return {
        "copium": copium,
        "producers": producers,
        "weapons": weapons,
    }

def generate_short_addr():
    return '0x' + str(uuid.uuid4())[-8:]


def rng_capacity(x, y):
    # chances for 1, 2, 3, 4, 5, ... 10 producer capacity
    # use a poisson distribution to alter sampling probabilities
    # as your distance goes further out
    # https://homepage.divms.uiowa.edu/~mbognar/applets/pois.html

    # poisson distribution likely not implementable in solidity
    # in this case just copy the probability distribution over from the link above

    d = distance_from_center(x, y)
    max_distance = 20
    return np.random.poisson((max_distance - d)/6)
    # if distance > 20:
    #     pr = [ 0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05, 0.0, 0.0 ]
    # elif distance > 15:
    #     pr = [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ]
    # elif distance > 10:
    #     pr = [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ]
    # elif distance > 5:
    #     pr = [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ]
    # else:
    #     pr = [ 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1 ]






# cope = Copium(xcols, yrows)
# owner = list(cope.bears.items())[0][0]
# cope.bears

# cope.updateGameState(1)
# cope.bears

# cope.harvest_all_user_copium()
# cope.bears

# cope.buy_weapons(owner)
# cope.bears

# cope.updateGameState(2)
# cope.bears

