from gamelogic import *  # importing necessary modules and functions

prevScreen = None  # initialize previous game screen as None
currScreen = None  # initialize current game screen as None

# -------------------------------------------------------------------------------
# GAME OVER SCREEN

while True:  # start the game loop
    gameScreen.fill(winner.plClr)  # fill the screen with the color of the winner

    for event in pygame.event.get():  # handle events
        if event.type == pygame.QUIT:  # if the user quits the game
            pygame.quit()  # quit pygame
            exit(0)  # exit the program

    while currScreen == prevScreen:  # loop until the current screen is different from the previous one
        currScreen = random.choice(winner.screens)  # choose a new random screen to display

    gameScreen.blit(currScreen, (0, 0))  # draw the current screen on the game window
    prevScreen = currScreen  # update the previous screen to the current one

    pygame.display.update()  # update the display
    time.sleep(0.2)  # wait for a short time to slow down the game loop
