import pygame
import pygame.freetype  # Import the freetype module.

import time
import numpy as np

from copium import Copium;
from parameters import XCOLS, YROWS, CELLSIZE
from colors import COLOR_GRID


cope = Copium(XCOLS, YROWS, initial_genesis_plots=[(22, 22), (5, 5)])
owner = list(cope.bears.items())[0][0]
# genesis_plots = np.random.choice(a=[1, 0], p=[0.02, 0.98])


def main(xcols, yrows, cellsize):
    pygame.init()
    surface = pygame.display.set_mode((xcols * cellsize, yrows * cellsize))
    pygame.display.set_caption("Copium Battle")

    ## delay init
    time.sleep(3)

    for i in range(0, 1000):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        surface.fill(COLOR_GRID)
        print("\n===== Block {} =====".format(i))
        ##
        cope.updateGameState(block=i)
        cope.renderUpdate(surface, cellsize)
        print(cope)
        ##
        pygame.display.update()
        time.sleep(1)


main(XCOLS, YROWS, CELLSIZE)