import pygame  # import pygame library for game development
import math  # import math module for mathematical operations
import random  # import random module for generating random numbers
import time  # import time module for time-related operations
from pygame import mixer  # import mixer module for sound mixing
import sqlite3  # import sqlite3 module for database operations
from sqlite3 import Error  # import Error class from sqlite3 module

"""
Eve AI - 
All her decision making is based around an attribute each property has, called 'realWorth'.
Initially she takes into account cost in relation to rent and compares it to other properties then adjusts realWorth accordingly.
She then re-evaluates realWorth on every iteration of the loop, adjusting for what other properties on the street are owned and whether it's mortgaged or not. 
It's one of her bigger weaknesses.
"""

#There are 28 properties on a monopoly board, in order of ascending price and rent.
#Their attribute 'colour' is an integer and it refers to what street its in. Can be used as an index in the global lists 'colours' and 'streets'


# -------------------------------------------------------------------------------
# DATABASES 

def create_connection():  # function to create a connection to the database
    conn = None  # initialize connection as None
    try:
        conn = sqlite3.connect('monopoly.db')  # try to establish a connection to the 'monopoly.db' database
    except Error as e:  # handle connection errors
        print(e)  # print the error message
    return conn  # return the connection object

def retrieve_squareplNames(conn):  # function to retrieve square player names from the database
    data = []  # initialize data list
    try:
        cursor = conn.cursor()  # create a cursor object for the database connection
        cursor.execute("SELECT name FROM squareplNames")  # execute a SQL query to retrieve player names from the 'squareplNames' table
        rows = cursor.fetchall()  # fetch all the rows of the query result
        for row in rows:
            data.append(row[0])  # append the player name to the data list
    except Error as e:  # handle query execution errors
        print(e)  # print the error message
    return data  # return the list of player names

def get_squareplNames():  # function to get the list of square player names
    conn = create_connection()  # create a connection to the database
    if conn is not None:  # if the connection is established successfully
        squareplNames = retrieve_squareplNames(conn)  # retrieve the player names from the database
        conn.close()  # close the database connection
    else:
        print("Error: Cannot establish a database connection.")  # print an error message if the connection cannot be established
    return squareplNames  # return the list of player names

gamedConn = sqlite3.connect('game_data.db')
c = gamedConn.cursor()

# Query the data from the table and reconstruct the list
retrieved_data = c.execute('SELECT group_id, sub_group_id, data_index, value FROM game_data ORDER BY group_id, sub_group_id, data_index').fetchall()

reconstructed_list = [[[] for _ in range(2)] for _ in range(8)]
for row in retrieved_data:
    group_id, sub_group_id, data_index, value = row
    reconstructed_list[group_id][sub_group_id].append(value)

# -------------------------------------------------------------------------------
# SQUARE CLASSES

class propClass:  # define a class for the game properties
    def __init__(self, plName, plBoardPosition, plClr):  # initialize the class properties with default values
        self.plName = plName  # set the property name
        self.plBoardPosition = plBoardPosition  # set the property board position
        self.plClr = plClr  # set the property color
        self.gHouses = 0  # set the number of houses on the property to 0
        self.gmOwn = gameBank  # set the property owner to the game bank
        self.plRent = 0  # set the property rent to 0
        self.plMortgaged = False  # set the property mortgage status to False
        self.plRejected = False  # set the property rejection status to False
        self.rentPaid = False  # set the rent payment status to False
        self.ownedStreet = False  # set the property ownership status to False
        self.btnPos = [[0, 0], [0, 0]]  # set the button position to default values
        self.initRealWorth = 0  # set the initial real worth of the property to 0
        self.worthHouse = 0  # set the worth of each house on the property to 0
        self.costsList = []  # initialize the list of costs for the property

    def getPrice(self):  # method to get the price of the property
        if self.plName == 'India':  # if the property name is India
            return 350  # return the price of India
        elif self.plName == 'China':  # if the property name is China
            return 400  # return the price of China
        elif self.plClr == 8:  # if the property color is 8
            return 200  # return the default price
        elif self.plClr == 9:  # if the property color is 9
            return 150  # return the default price
        elif self.plBoardPosition == 5 * self.plClr + 4:  # if the property is a railway station
            return 40 * self.plClr + 80  # return the price of the railway station
        else:
            return 40 * self.plClr + 60  # return the default price

    def initRents(self):  # method to initialize the rents for the property
        if self.plClr <= 7:  # if the property color is less than or equal to 7
            if self.plBoardPosition == 5 * self.plClr + 4 or self.plName == 'England':  # if the property is a railway station or England
                self.costsList = gameHseCstGrd[self.plClr][1]  # set the costs list to the corresponding value
                return gameHseCstGrd[self.plClr][1][0]  # return the initial rent for the railway station or England
            else:
                self.costsList = gameHseCstGrd[self.plClr][0]  # set the costs list to the corresponding value
                return gameHseCstGrd[self.plClr][0][0]  # return the initial rent for the property
        elif self.plClr == 8:  # if the property color is 8
            return 25  # return the default rent
        else:
            return 4 * diceroll  # return the rent based on the dice roll

    def initWorths(self):  # method to initialize the worth of the property
        global initialMod  # use the global variable initialMod
        if self.plClr <= 7:  # if the property color is less than or equal to 7
            rents = sum(self.costsList) + self.initRents()  # calculate the total rents
            worth = rents * initialMod - self.cstOfHouse()  # calculate the worth of the property
            return worth  # return the worth of the property
        elif self.plClr == 8:  # if the property color is 8
            return 200  # return the default worth
        else:
            return 150  # return the default worth

    def getInitHseWorths(self):  # method to get the initial worth of each house on the property
        global houseMod  # use the global variable houseMod
        if self.plClr <= 7:  # if the property color is less than or equal to 7
            rents = avgDiff([self.initRents()] + self.costsList)  # calculate the average rents
            worth = rents * houseMod  # calculate the worth of each house
            return worth  # return the worth of each house
        else:
            return 0  # return 0 as there are no houses on the property

    def cstOfHouse(self):  # method to get the cost of building each house
        multiplier = math.floor(self.plClr/2) + 1  # calculate the multiplier based on the property color
        if self.plClr < 8:  # if the property color is less than 8
            return multiplier * 50  # return the cost of building each house
        else:
            return False  # return False as there are no houses on the property


    # Draws houses, owner's colour,  and/or mortgaged sign on properties.
    def colours(self):
        if self.gmOwn.plClr:
            if 0 < self.plBoardPosition < 10:
                colourPos = [605-math.floor(57.25*self.plBoardPosition), 685]
                pygame.draw.rect(gameScreen, self.gmOwn.plClr, (colourPos, (57, 15)))
                pygame.draw.rect(gameScreen, colorPalette.dutchWhite, (colourPos, (57, 2)))
                self.btnPos = [[colourPos[0], colourPos[0]+57], [colourPos[1], colourPos[1]+15]]
                if self.plMortgaged:
                    gameScreen.blit(picMortgage, (colourPos[0], colourPos[1] - 77))
                if 0 < self.gHouses < 5:
                    count = 1
                    for house in range(self.gHouses):
                        housePos = [colourPos[0] + count, 610]
                        gameScreen.blit(gameBuildingPics[0], (housePos))
                        count += 14
                elif self.gHouses >= 5:
                    hotelPos = [colourPos[0] + 16, 610]
                    gameScreen.blit(gameBuildingPics[1], (hotelPos))

            elif 10 < self.plBoardPosition < 20:
                colourPos = [0, 607-math.floor(57.25*(self.plBoardPosition-10))]
                pygame.draw.rect(gameScreen, self.gmOwn.plClr, (colourPos, (15, 57)))
                pygame.draw.rect(gameScreen, colorPalette.dutchWhite, ((colourPos[0] + 13, colourPos[1]), (2, 57)))
                self.btnPos = [[colourPos[0], colourPos[0]+15], [colourPos[1], colourPos[1]+57]]
                if 0 < self.gHouses < 5:
                    count = 1
                    for house in range(self.gHouses):
                        housePos = [71, colourPos[1] + count]
                        gameScreen.blit(gameBuildingPics[2], (housePos))
                        count += 14
                elif self.gHouses >= 5:
                    hotelPos = [71, colourPos[1] + 16]
                    gameScreen.blit(gameBuildingPics[3], (hotelPos))

                if self.plMortgaged:
                    gameScreen.blit(mortgagePic2, (colourPos[0] + 15, colourPos[1]))

            elif 20 < self.plBoardPosition < 30:
                colourPos = [32 + math.ceil(57.25*(self.plBoardPosition-20)), 0]
                pygame.draw.rect(gameScreen, self.gmOwn.plClr, (colourPos, (57, 15)))
                pygame.draw.rect(gameScreen, colorPalette.dutchWhite, ((colourPos[0], colourPos[1] + 13), (57, 2)))
                self.btnPos = [[colourPos[0], colourPos[0]+57], [colourPos[1], colourPos[1]+15]]
                if 0 < self.gHouses < 5:
                    count = 1
                    for house in range(self.gHouses):
                        housePos = [colourPos[0] + count, 73]
                        gameScreen.blit(gameBuildingPics[4], (housePos))
                        count += 14
                elif self.gHouses >= 5:
                    hotelPos = [colourPos[0] + 16,75]
                    gameScreen.blit(gameBuildingPics[5], (hotelPos))

                if self.plMortgaged:
                    gameScreen.blit(picMortgage, (colourPos[0], colourPos[1] + 15))

            else:
                colourPos = [685, 35 + math.ceil(57.25 * (self.plBoardPosition - 30))]
                pygame.draw.rect(gameScreen, self.gmOwn.plClr, (colourPos, (15, 57)))
                pygame.draw.rect(gameScreen, colorPalette.dutchWhite, ((colourPos), (2, 57)))
                self.btnPos = [[colourPos[0], colourPos[0]+15], [colourPos[1], colourPos[1]+57]]
                if 0 < self.gHouses < 5:
                    count = 1
                    for house in range(self.gHouses):
                        housePos = [608, colourPos[1] + count]
                        gameScreen.blit(gameBuildingPics[6], (housePos))
                        count += 14
                elif self.gHouses >= 5:
                    hotelPos = [608, colourPos[1] + 16]
                    gameScreen.blit(gameBuildingPics[7], (hotelPos))

                if self.plMortgaged:
                    gameScreen.blit(mortgagePic2, (colourPos[0] -77, colourPos[1]))

     # Updates a property's rent 
    def modRents(self):
        if self.gHouses > 0:
            if self.plBoardPosition == 5 * self.plClr + 4 or self.plName == 'England':
                self.plRent = gameHseCstGrd[self.plClr][1][self.gHouses]
            else:
                self.plRent = gameHseCstGrd[self.plClr][0][self.gHouses]
        if self.plMortgaged:
            self.plRent = 0
        return self.plRent
    
class Square:
    def __init__(self,plName,plBoardPosition):
        self.plName = plName
        self.plBoardPosition = plBoardPosition

class Chance(Square):
    def __init__(self, plName, plBoardPosition):
        # initialize Chance/Community Chest object with player name and board position
        self.plName = plName
        self.plBoardPosition = plBoardPosition
        # set the card list to either chance or community chest depending on the object's name
        if self.plName == 'Chance':
            self.list = getchance
        else:
            self.list = getCommunityChest

    def pickCard(self):
        # return a random card from the card list
        return random.choice(self.list)


class TaxSquares(Square):
    def __init__(self, plName, plBoardPosition):
        # initialize TaxSquares object with player name and board position
        self.plName = plName
        self.plBoardPosition = plBoardPosition
        self.paid = False

    def getTax(self):
        # if the square is Income Tax, return 200
        if self.plName == 'Income Tax':
            return 200
        # if the square is Luxury Tax, return 100
        return 100


# Define a class called SpecialSquares with attributes plName, plBoardPosition, and paid.
class SpecialSquares(Square): 
    # Define the initialization method for the SpecialSquares class.
    def __init__(self, plName, plBoardPosition):
        self.plName = plName  # Set the plName attribute to the value passed in as an argument.
        self.plBoardPosition = plBoardPosition  # Set the plBoardPosition attribute to the value passed in as an argument.
        self.paid = False  # Set the paid attribute to False by default.

    # Define a method called getPayAmount that takes in a parameter called freeParking.
    def getPayAmount(self, freeParking): 
        global gameAlert  # Declare gameAlert as a global variable.
        # If the plName attribute is 'Go', assign a message to gameAlert and return 200.
        if self.plName == 'Go':
            if player.isTurn:  # If it's the player's turn, display a message to the gameAlert.
                gameAlert = Alert('GIMME THE MONEY', 'You landed on Go and got $400')
            elif eveAI.isTurn:  # If it's the AI's turn, display a different message to the gameAlert.
                gameAlert = EveAlert('Sweet sweet cashola', 'eveAI gets $400 by landing on Go')
            return 200  # Return 200 as the payment amount.

        # If the plName attribute is 'Free Parking', assign a message to gameAlert and return the value of freeParking.
        elif self.plName == 'Free Parking':
            if player.isTurn:  # If it's the player's turn, display a message to the gameAlert.
                gameAlert = Alert('Rolling in Dough, maybe', ('You got $' + str(freeParking) + ' from Free Parking!'))
            return freeParking  # Return the value of freeParking as the payment amount.

        # If the plName attribute is not 'Go' or 'Free Parking', return 0 as the payment amount.
        else:
            return 0

# -------------------------------------------------------------------------------
# SPRITE CLASSES 

# Define a class called gamePlayer with attributes plName, piece, plBoardPosition, timeMoving, pieceSelected, pieceConfirmed, plClr, isTurn, money, screens, canRoll, doublesCount, inJail, jailTurns, getOutOfJailFreeCards, isDeveloping, isTrading, isMortgaging, normalGameplay, offer, bid, firstTimeInJail, and paidOOJ.
# Class for practical matters considering the user and Eve.
class gamePlayer: 
    # Define the initialization method for the gamePlayer class.
    def __init__(self, plName, isTurn, screens):
        self.plName = plName  # Set the plName attribute to the value passed in as an argument.
        self.piece = None  # Set the piece attribute to None by default.
        self.plBoardPosition = 0  # Set the plBoardPosition attribute to 0 by default.
        self.timeMoving = 0  # Set the timeMoving attribute to 0 by default.
        self.pieceSelected = False  # Set the pieceSelected attribute to False by default.
        self.pieceConfirmed = False  # Set the pieceConfirmed attribute to False by default.
        self.plClr = None  # Set the plClr attribute to None by default.
        self.isTurn = isTurn  # Set the isTurn attribute to the value passed in as an argument.
        self.money = 1500  # Set the money attribute to 1500 by default.
        self.screens = screens  # Set the screens attribute to the value passed in as an argument.
        self.canRoll = True  # Set the canRoll attribute to True by default.
        self.doublesCount = 0  # Set the doublesCount attribute to 0 by default.
        self.inJail = False  # Set the inJail attribute to False by default.
        self.jailTurns = 0  # Set the jailTurns attribute to 0 by default.
        self.getOutOfJailFreeCards = []  # Set the getOutOfJailFreeCards attribute to an empty list by default.

        # The next 4 attributes are boolean statuses. Arguably I could have made one string attribute called 'status'. Ah, the joy of hindsight.

        self.isDeveloping = False  # Set the isDeveloping attribute to False by default.
        self.isTrading = False  # Set the isTrading attribute to False by default.
        self.isMortgaging = False  # Set the isMortgaging attribute to False by default.
        self.normalGameplay = True  # Set the normalGameplay attribute to True by default.


        self.offer = []  # Set the offer attribute to an empty list by default.
        self.bid = '0'  # Set the bid attribute to '0' by default.
        self.firstTimeInJail = True  # Set the firstTimeInJail attribute to True by default.
        self.paidOOJ = False  # OOJ = Out Of Jail


    # Lets the user choose a piece. 
    # checks if the mouse is over a certain game piece and returns the position of that game piece if it is
    #  If the mouse is not over any game piece, it returns False.

    def plsChoosePiece(self, mousepos): 
        if 110 < mousepos[0] < 110 + 1*270:
            if 276 < mousepos[1] < 276 + 128:
                self.piece = boot
                return (110, 276)
            elif 427 < mousepos[1] < 427 + 128:
                self.piece = iron
                return (110, 427)
        elif 110 + 1*270 < mousepos[0] < 110 + 2*270:
            if 276 < mousepos[1] < 276 + 128:
                self.piece = car
                return (110 + 1*270, 276)
            elif 427 < mousepos[1] < 427 + 128:
                self.piece = ship
                return (110 + 1 * 270, 427)
        elif 110 + 2*270 < mousepos[0] < 110 + 3*270:
            if 276 < mousepos[1] < 276 + 128:
                self.piece = dog
                return (110 + 2 * 270, 276)
            elif 427 < mousepos[1] < 427 + 128:
                self.piece = thimble
                return (110 + 2 * 270, 427)
        elif 110 + 3*270 < mousepos[0] < 110 + 4*270:
            if 276 < mousepos[1] < 276 + 128:
                self.piece = hat
                return (110 + 3 * 270, 276)
            elif 427 < mousepos[1] < 427 + 128:
                self.piece = wheelbarrow
                return (110 + 3 * 270, 427)
        else:
            return False

    # 'BoardPosition' is an integer from 0-39 depending on what square you're on, but that has to be translated into x and y co-ords, hence this function.
    def gameGetPos(self):
        if 0 <= self.plBoardPosition < 10:
            return [608-57*self.plBoardPosition, 630]
        elif 10 <= self.plBoardPosition < 20:
            return [15, 608-57*(self.plBoardPosition-10)]
        elif 20 <= self.plBoardPosition < 30:
            return [38 + 57*(self.plBoardPosition-20), 15]
        else:
            return [630, 38 + 57*(self.plBoardPosition-30)]

    # Moves players forward one place at a time. I'm pretty sure it gets called on every iteration of the loop.
    def plsMove(self): 
        if self.timeMoving > 0:
            if self.plBoardPosition == 39:
                self.plBoardPosition = 0
                self.money += 200
            else:
                self.plBoardPosition += 1
            time.sleep(0.1)
            self.timeMoving -= 1

 # An identifier class.
class plsBanks: 
    def __init__(self):
        self.plClr = None

# There's an Eve object of the Player class and an AI object of the AI class. I like to think of 'Eve: Player' as Eve's body and 'AI: AI' as her brain.
class aiEve: 
    def __init__(self):
        self.player = eveAI

    # In auctions, Eve returns a value $1 higher than whatever you bid until it gets too high for her.
    def bid(self, prop):
        global gameAlert
        if type(gameAlert) == Auction:
            if gameAlert.highestBid < prop.initRealWorth and gameAlert.highestBid < self.player.money:
                return gameAlert.highestBid + 1


     # Returns boolean of whether she wants to buy a given property or not.
    def plsAIChkProps(self, prop):
        if prop.initRealWorth > prop.getPrice() + 50:
            if self.player.money > prop.getPrice()//2:
                return True
        elif prop.initRealWorth > prop.getPrice():
            if self.player.money > prop.getPrice():
                return True
        elif prop.initRealWorth > prop.getPrice() - 50:
            if self.player.money >= prop.getPrice()*2:
                return True
        return False

    # Returns the next property she wants to build a house on.
    def plAiDevelop(self, street): 
        if len(street) == 2:
            for prop in street:
                prop.worthHouse = prop.getInitHseWorths() + 25
        worthSum = 0
        for prop in street:
            worthSum += prop.worthHouse
        worthAvg = worthSum/len(street)

        underdevelopedCount = 0
        buildingProp = None
        if (worthAvg > street[0].cstOfHouse() and self.player.money > street[0].cstOfHouse()) or (worthAvg > street[0].cstOfHouse() - 25 and self.player.money > 2*street[0].cstOfHouse()):

            for prop in street:
                if prop.gHouses < street[len(street)-1].gHouses:
                    underdevelopedCount += 1
            if underdevelopedCount == 0:
                buildingProp = street[len(street)-1]
            elif underdevelopedCount == 2:
                buildingProp = street[1]
            elif underdevelopedCount == 1:
                buildingProp = street[0]

            if buildingProp.gHouses < 5:
                buildingProp.gHouses += 1
                self.player.money -= buildingProp.cstOfHouse()
                return buildingProp


    # Evaluates trades. 
    # She has to switch the owners of the properties, so she can evaluate whether the properties would be worth having once they've been traded.

    def plsChkTrade(self, offer, recieving):
        gettingValue = 0
        modOffer = offer
        modRecieve = recieving
        for item in offer:
            if type(item) == gameMoneyOff:
                gettingValue += item.value
                modOffer.remove(item)
            else:
                item.gmOwn = self.player

        givingValue = 0
        for item in recieving:
            if type(item) == gameMoneyOff:
                givingValue += item.value
                modRecieve.remove(item)
            else:
                item.gmOwn = player

        if givingValue > self.player.money:
            for item in modOffer:
                item.gmOwn = player
            for item in modRecieve:
                item.gmOwn = self.player
            return False

        plsGetsWorProps()
        plsGetWorStat()
        plsGetWorUtil()

        for item in modOffer:
            item.gmOwn = player
            gettingValue += item.initRealWorth
        for item in modRecieve:
            item.gmOwn = self.player
            givingValue += item.initRealWorth

        plsGetsWorProps()
        plsGetWorStat()
        plsGetWorUtil()

        if givingValue < gettingValue:
            return True
        return False

    # Lets Eve write her own trades! 
    # She trades in pairs, and never offers or requests money so she's fairly limited, but it's still more than I thought it would be.
    def itemsToTrade(self):
        global rejectedTrades
        userProps = []
        EveProps = []

        for prop in gameProps:
            if prop.gmOwn == player:
                userProps.append(prop)
            elif prop.gmOwn == eveAI:
                EveProps.append(prop)

        offer = []
        request = []

        for want in userProps:
            for give in EveProps:
                if want.getPrice() <= give.getPrice() and want.initRealWorth > give.initRealWorth and not(want.ownedStreet or give.ownedStreet):
                    if not give in offer and not want in request:
                        if len(offer) < 3 and len(request) < 3:
                            offer.append(give)
                            request.append(want)

        sameStreets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for give in offer:
            for want in request:
                if give.plClr == want.plClr:
                    sameStreets[give.plClr] += 1


        for streetid in sameStreets:
            if streetid == 1:
                for give in offer:
                    if give.plClr == sameStreets.index(streetid):
                        i = offer.index(give)
                        offer.remove(offer[i])
                        request.remove(request[i])
            elif streetid == 2:
                offercount = 0
                for give in offer:
                    if give.plClr == sameStreets.index(streetid):
                        offercount += 1
                if offercount == 1:
                    if give.plClr == sameStreets.index(streetid):
                        i = offer.index(give)
                        offer.remove(offer[i])
                        request.remove(request[i])
                elif offercount == 2:
                    for want in request:
                        if want.plClr == sameStreets.index(streetid):
                            i = request.index(want)
                            offer.remove(offer[i])
                            request.remove(request[i])

        if len(offer) == 0 or len(request) == 0:
            return [False]
        elif [offer, request] in rejectedTrades: 
            return [False]
        return [offer, request]

    # This is what Eve does if she goes to end her turn and she has negative money.
    def emergencyAction(self):
        global gameProps
        houseProps = [[], [], [], [], [], [], [], []]
        baselineHouseProps = [[], [], [], [], [], [], [], []]
        regProps = []
        for prop in gameProps:
            if prop.gmOwn == self.player:
                if prop.gHouses > 0:
                    houseProps[prop.plClr].append(prop)
                elif not prop.plMortgaged:
                    regProps.append(prop)

        streetsToDemolish = [] 
        while not houseProps == baselineHouseProps: 
            bestToSell = False
            for street in houseProps:
                if len(street) > 0:
                    if not bestToSell or street[0].worthHouse/street[0].cstOfHouse() < bestToSell.worthHouse/bestToSell.cstOfHouse():
                        bestToSell = street[0]
            houseProps[bestToSell.plClr] = []
            streetsToDemolish.append(gameStrts[bestToSell.plClr])

        propsMortgaged = []
        housesSold = []
        for street in streetsToDemolish: 
            for iter in range(5):
                for prop in street:

                    if self.player.money < 0 and prop.gHouses > 0:
                        prop.gHouses -= 1
                        self.player.money += (9*prop.cstOfHouse())//10
                        housesSold.append(prop)

                    if self.player.money >= 0:
                        return [housesSold, propsMortgaged, True]

        propsToMort = []
        while len(regProps)>0: 
            bestToMort = False
            for prop in regProps:
                if not bestToMort or prop.initRealWorth/prop.getPrice() < bestToMort.initRealWorth/bestToMort.getPrice():
                    bestToMort = prop
            regProps.remove(bestToMort)
            propsToMort.append(bestToMort)

        for prop in propsToMort: 
            if self.player.money < 0:
                prop.plMortgaged = True
                self.player.money += prop.getPrice()//2
                propsMortgaged.append(prop)
            else:
                return [housesSold, propsMortgaged, True]

        for list in housesSold:
            if self.player.money < 0:
                list[0].plMortgaged = True
                self.player.money += list[0].getPrice//2
                propsMortgaged.append(list[0])
            else:
                return [housesSold, propsMortgaged, True]

        if self.player.money >= 0:
            return [housesSold, propsMortgaged, True]

        return [housesSold, propsMortgaged, False]

    # Determines if Eve will use a get out of jail free card when leaving jail.
    def useGojf(self): 
        if len(self.player.getOutOfJailFreeCards) > 0:
            return True
        return False
    
# -------------------------------------------------------------------------------
# ALERT CLASSES
'''
Alerts are what I called the notification box that is used to narrate the events of the game for the user.
They don't really do anything for Eve or for the logic of the game, but they are necessary for the user to interact.
creates objects that display an alert message on a game screen. The message has a heading and a body. 
The class has a write() method which displays the message on the screen, and a confirmOrDeny() method which checks if the user has confirmed or denied the 
    alert message. 
The alert can be of different types, such as "confirm", "choice", "trade", or "basic", and this affects the image displayed. 
EveAlerts must be confirmed before Eve can do anything new, which is how the user is able to keep up with what she does during her turn.
'''
class Alert:
    def __init__ (self, heading, body):
        self.heading = heading
        self.body = body
        self.confirmed = True

        if self.heading == 'Chance' or self.heading == 'Community Chest':
            self.type = 'confirm'
            self.image = getConfirmAlert
        elif self.heading.__contains__('Tutorial'):
            self.type = 'confirm'
            self.image = getConfirmAlert
        elif self.heading == 'They see me rollin\'' or self.heading == 'Serial doubles-roller' or self.heading == 'Not-so-smooth criminal':
            self.type = 'confirm'
            self.image = getConfirmAlert
        elif self.body.__contains__('?'):
            self.type = 'choice'
            self.image = gameChoiceAlertPic
        elif self.heading == 'Trade':
            self.type = 'trade'
            self.image = getTradeAlertPic
        elif self.heading == 'Mortgage' or self.heading == 'Unmortgage' or self.heading == 'Sell house?':
            self.type = 'confirm'
            self.image = getConfirmAlert
        else:
            self.type = 'basic'
            self.image = gameAlertPic
        self.timePausing = 0

    # This function renders and displays an alert with a heading, body, and image.
    def write(self):
        headingSize = 28
        bodySize = 17
        headingFont = pygame.font.Font('assets/polly.ttf', headingSize)
        bodyFont = pygame.font.Font('assets/polly.ttf', bodySize)
        lineSpacing = 6

        heading = headingFont.render(self.heading, True, colorPalette.darkGold)

        lines = self.body.split('#')

        gameScreen.blit(self.image, (700, 0))
        gameScreen.blit(heading, (770, 224))
        for i in range(len(lines)):
            lines[i] = bodyFont.render(lines[i], True, colorPalette.axolotl)
            height = 224 + headingSize + lineSpacing + i*(bodySize+lineSpacing)
            gameScreen.blit(lines[i], (770, height))

    # This code checks for confirmation or denial of an alert based on the type of the alert and the user's mouse position.
    def confirmOrDeny(self):
        if self.type == 'choice':
            if inCircle(pygame.mouse.get_pos(), [700+353, 433], 15):
                return 'confirmed'
            if inCircle(pygame.mouse.get_pos(), [700+394, 433], 15):
                return 'denied'
        elif self.type == 'confirm' or self.type == 'trade':
            if inCircle(pygame.mouse.get_pos(), [700 + 394, 433], 15):
                return 'confirmed'
        return False

class Auction:
    def __init__(self, prop):
        self.prop = prop
        self.EveRejected = False
        self.image = getAuctionPic
        self.calcPos = {
            '0': [996, 408],
            '1': [940, 374],
            '2': [996, 374],
            '3': [1052, 374],
            '4': [940, 340],
            '5': [996, 340],
            '6': [1052, 340],
            '7': [940, 306],
            '8': [996, 306],
            '9': [1052, 306],
            'C': [940, 408],
            'bid': [1052, 408]
        }
        self.size = [56, 34]
        self.body = 'Your turn'
        self.highestBid = 0
        self.heading = 'Auction'
        self.type = 'auction'
        self.turnsSincePlayerBid = 0
        self.winner = None
        self.confirmed = True

    #  checks if the user clicked on a specific region of the screen and updates the bid accordingly.
    def checkCalc(self):
        global player, eveAI
        for num in self.calcPos:
            if self.calcPos[num][0] < pygame.mouse.get_pos()[0] < self.calcPos[num][0] + self.size[0]:
                if self.calcPos[num][1] < pygame.mouse.get_pos()[1] < self.calcPos[num][1] + self.size[1]:
                    if num == 'C' and len(player.bid) > 0:
                        player.bid = '0'
                    elif num == 'bid':
                        if int(player.bid) > self.highestBid:
                            self.highestBid = int(player.bid)
                            self.winner = player
                            if aiEve.bid(self.prop):
                                eveAI.bid = aiEve.bid(self.prop)
                            else:
                                self.EveRejected = True

                            self.turnsSincePlayerBid = 0
                            self.body = 'eveAI is bidding...'
                        else:
                            self.body = "You gotta bid more #than the highest bid #mate that's how #auctions work"
                    else:
                        if player.bid == '0':
                            player.bid = num
                        else:
                            player.bid += num



    #UI Things
    def write(self):
        global player, eveAI
        numberSize = 28
        bodySize = 28
        if self.body.__contains__('auctions'):
            bodySize = 15
        elif self.body.__contains__('eveAI'):
            bodySize = 20
        numberFont = pygame.font.Font('assets/polly.ttf', numberSize)
        bodyFont = pygame.font.Font('assets/polly.ttf', bodySize)
        lineSpacing = 4

        highestBid = numberFont.render('$'+str(self.highestBid), True, colorPalette.axolotl)
        playerNum = numberFont.render('$' + player.bid, True, colorPalette.dutchWhite)

        lines = self.body.split('#')

        gameScreen.blit(self.image, (700, 0))
        gameScreen.blit(highestBid, (775, 265))
        gameScreen.blit(playerNum, (945, 265))
        for i in range(len(lines)):
            lines[i] = bodyFont.render(lines[i], True, colorPalette.dutchWhite)
            height = 314 + i*(bodySize+lineSpacing)
            gameScreen.blit(lines[i], (774, height))

    def confirmOrDeny(self):
        if 711 < pygame.mouse.get_pos()[0] < 921 and 403 < pygame.mouse.get_pos()[1] < 435:
            return 'denied'
        return False

class EveAlert(Alert):

    def __init__ (self, heading, body):
        self.heading = heading
        self.body = body
        self.type = 'confirm'
        self.image = getConfirmAlert
        self.confirmed = False
        self.smallFont = False

    def write(self):
        headingSize = 28
        bodySize = 17
        lineSpacing = 6
        if self.smallFont:
            headingSize = 32
            bodySize = 21
            lineSpacing = 5
        headingFont = pygame.font.Font('assets/polly.ttf', headingSize)
        bodyFont = pygame.font.Font('assets/polly.ttf', bodySize)


        heading = headingFont.render(self.heading, True, colorPalette.darkGold)

        lines = self.body.split('#')

        gameScreen.blit(self.image, (700, 0))
        gameScreen.blit(heading, (770, 224))
        for i in range(len(lines)):
            lines[i] = bodyFont.render(lines[i], True, colorPalette.axolotl)
            height = 224 + headingSize + lineSpacing + i*(bodySize+lineSpacing)
            gameScreen.blit(lines[i], (770, height))

    def confirmOrDeny(self):
        if inCircle(pygame.mouse.get_pos(), [700 + 394, 433], 15):
            self.confirmed = True
            return 'confirmed'
        return False

# -------------------------------------------------------------------------------
# MISC CLASSES

# Every side of the dice is its own object, of this class.
class Roll:
    def __init__(self, image, value):
        self.image = image
        self.value = value

# The menu is made up of buttons, which are in the list 'buttons' and belong to this class.
class Button:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
        self.left = pos[0]
        self.top = pos[1]
        self.right = pos[0] + size[0]
        self.bottom = pos[1] + size[1]
        self.middle = ((self.left+self.right)//2, (self.top+self.bottom)//2)
    def mouseHover(self):
        mousepos = pygame.mouse.get_pos()
        if self.left < mousepos[0] < self.right and self.top < mousepos[1] < self.bottom:
            return True
        return False

# Aside from the house colours, there are only six colours that I use in the game, ranging from darkish green to yellowish brown.
class clrPalette: 
    def __init__(self):
        self.axolotl = (115, 128, 84)
        self.olivine = (163, 168, 109)
        self.dutchWhite = (225, 213, 184)
        self.darkVanilla = (214, 199, 167)
        self.camel = (190, 153, 110)
        self.darkGold = (170, 114, 42)

# Chance and Community Chest cards
class getGameCard:
    def __init__(self, text, type, value):
        self.text = text
        self.type = type
        self.value = value
        self.executed = False

    # executes various card effects based on the card type, which includes updating the player's position, money, property ownership, and jail status.
    def cardExec(self, player):
        if self.type == 'pay':
            player.money += self.value
        elif self.type == 'plsMove':
            if player.plBoardPosition > self.value:
                player.money += 200
            player.plBoardPosition = self.value
        elif self.type == 'go to jail':
            player.inJail = True
        elif self.type == 'gojf':
            if self.text.__contains__('bribed'):
                player.getOutOfJailFreeCards.append(getCommunityChest[4])
            else:
                player.getOutOfJailFreeCards.append(getchance[8])
            player.canRoll = False
        elif self.type == 'social':
            for sprite in players:
                if sprite == player:
                    sprite.money += self.value*(len(players)-1)
                else:
                    sprite.money -= self.value
        elif self.type == 'repairs':
            for prop in gameProps:
                if prop.gmOwn == player:
                    if prop.gHouses > 4:
                        player.money -= self.value[1]
                    else:
                        player.money -= self.value[0]*prop.gHouses
        elif self.type == 'nearestu':
            if 0 < player.plBoardPosition <= 12:
                player.plBoardPosition = 12
            elif 28 < player.plBoardPosition < 40:
                player.plBoardPosition = 12
                player.money += 200
            else:
                player.plBoardPosition = 28
        elif self.type == 'nearests':
            if 0 < player.plBoardPosition <= 5:
                player.plBoardPosition = 5
            elif player.plBoardPosition <= 15:
                player.plBoardPosition = 15
            elif player.plBoardPosition <= 25:
                player.plBoardPosition = 25
            elif player.plBoardPosition <= 35:
                player.plBoardPosition = 35
            else:
                player.plBoardPosition = 5
                player.money += 200
        elif self.type == 'mover':
            player.plBoardPosition += self.value

# Part of Eve's property valuing system
class gameRatio:
    def __init__(self, cost, plRent):
        self.cost = cost
        self.plRent = plRent
        self.value = self.cost/self.plRent

# Used in trades (MONEY OFFER)
class gameMoneyOff: 
    def __init__(self, value):
        self.value = value
        self.plName = '$' + str(self.value)
        self.plClr = value

# -------------------------------------------------------------------------------
# MISC FUNCTIONS

def inCircle(mousePos, circleMid, radius):
    if (mousePos[0]-circleMid[0])**2 + (mousePos[1]-circleMid[1])**2 <= radius**2:
        return True
    return False

def clickingOnButton():
    global buttons
    for button in buttons:
        if button.mouseHover():
            return True
    return False

def rollDice(gamedices):
    roll1 = random.choice(gamedices)
    roll2 = random.choice(gamedices)
    return [roll1, roll2]

# The function isDodgy() checks if a trade involving properties with houses on 
# a street is unfair in the game, and returns a list containing a boolean value 
# and the color of the potentially unfair street, or False if no such trade exists.
def isDodgy():
    global players, gameStrts
    for player in players:
        tradeStreetHasHouses = False

        for prop in player.offer:
            neighboursBeingTraded = 0

            if type(prop) == gameMoneyOff:
                break

            if prop.ownedStreet:
                for neighbour in gameStrts[prop.plClr]:
                    if neighbour.gHouses > 0:
                        tradeStreetHasHouses = True
                        break

            if tradeStreetHasHouses:
                for neighbour in gameStrts[prop.plClr]:
                    if neighbour in player.offer:
                        neighboursBeingTraded += 1

                if neighboursBeingTraded < len(gameStrts[prop.plClr]):
                    return [True, gameClrs[prop.plClr]]
    return False

def getAvg(listOfRatios):
    sum = 0
    for ratio in listOfRatios:
        sum += ratio.value
    return sum/len(listOfRatios)

def avgDiff(listOfNums):
    diffList = []
    for i in range(len(listOfNums)-1):
        diff = listOfNums[i+1] - listOfNums[i]
        diffList.append(diff)
    avg = sum(diffList)/len(diffList)
    return avg

# -------------------------------------------------------------------------------
# MISC METHODS

# I wrote a function to draw players becasue there are two parts to their pieces: the colour, and the piece itself.
def draw(player, pos): 
    if player == player:
        gameScreen.blit(userColour, pos)
        gameScreen.blit(player.piece, pos)
    elif player == eveAI:
        gameScreen.blit(EveColour, pos)
        gameScreen.blit(eveAI.piece, pos)

# Sets up all the lists of properties and squares
def boardSetup():
    global gameSquares, gameProps, gameClrs
    notpropClassplNames = ['Go', 'Community Chest', 'Income Tax', 'Chance', 'Jail', 'Free Parking', 'Go To Jail',
                        'Super Tax']

    squareplNames = get_squareplNames()
    for i in range(len(squareplNames)):
        if not squareplNames[i] in notpropClassplNames:
            currentProp = propClass(squareplNames[i], i, 10)
            if currentProp.plName.__contains__('Station'):
                currentProp.plClr = 8
            elif currentProp.plName == 'Electric Company' or currentProp.plName == 'Water Works':
                currentProp.plClr = 9
            else:
                for n in range(8):
                    if 5 * n < i < 5 * n + 5:
                        currentProp.plClr = n
            currentProp.plRent = currentProp.initRents()
            gameSquares.append(currentProp)
            gameProps.append(currentProp)
            if currentProp.plClr <= 7:
                gameStrts[currentProp.plClr].append(currentProp)
        elif squareplNames[i] == 'Chance' or squareplNames[i] == 'Community Chest':
            currentChance = Chance(squareplNames[i], i)
            gameSquares.append(currentChance)
        elif squareplNames[i].__contains__('Tax'):
            currentTax = TaxSquares(squareplNames[i], i)
            gameSquares.append(currentTax)
        else:
            currentSpecial = SpecialSquares(squareplNames[i], i)
            gameSquares.append(currentSpecial)

# Draws the side menu
def gameShowMenu(): 
    global buttons, player, eveAI, colorPalette, gameBoard, background, buttonActions

    gameScreen.fill(colorPalette.axolotl)
    gameScreen.blit(gameBoard, (0, 0))
    gameScreen.blit(background, (700, 0))

    turnFont = pygame.font.Font('assets/polly.ttf', 35)
    if player.isTurn:
        turnText = turnFont.render('YOUR TURN', True, colorPalette.dutchWhite)
    else:
        turnText = turnFont.render('EVE\'S TURN', True, colorPalette.dutchWhite)
    gameScreen.blit(turnText, (870, 60))

    for button in buttons:
        if button == endTurnButton or button == mortgageButton:
            gameScreen.blit(endTurnBehind, (button.pos))

        if button.mouseHover():
            pygame.draw.rect(gameScreen, colorPalette.dutchWhite, (button.pos, button.size))

        if button == endTurnButton and not etAvailable:
            gameScreen.blit(endTurnUnAv, (button.pos))

        if button == endTurnButton:
            gameScreen.blit(endTurnFront, (button.pos))
        elif button == mortgageButton:
            gameScreen.blit(mortgageFront, (button.pos))

    if buttonActions[0]:
        gameScreen.blit(gamethrow[0].image, (188+11+37, 210+33))
        gameScreen.blit(gamethrow[1].image, (188+38+150, 210+33))


    gameScreen.blit(gameButtonsPic, (700, 0))

    draw(player, (770, 50))
    draw(eveAI, (730, 636))

    moneyFont = pygame.font.Font('assets/polly.ttf', 40)
    userMoney = moneyFont.render('$' + str(player.money), True, colorPalette.darkVanilla)
    EveMoney = moneyFont.render('$' + str(eveAI.money), True, colorPalette.darkVanilla)

    gameScreen.blit(userMoney, (760, 150))
    gameScreen.blit(EveMoney, (820, 646))

# -------------------------------------------------------------------------------
#GET RENT METHODS

# These are methods that update the rent value of properties based on houses and neighbours and stuff

def getRentStations():
    global gameSquares
    stations = [gameSquares[5], gameSquares[15], gameSquares[25], gameSquares[35]]
    for currentStation in stations:
        matchesCount = -1
        if currentStation.gmOwn != gameBank:
            for station in stations:
                if station.gmOwn == currentStation.gmOwn:
                    matchesCount += 1
            currentStation.plRent = (2**matchesCount)*25

def getRentUtilities():
    global diceroll, gameSquares
    utils_game = [gameSquares[12], gameSquares[28]]
    if utils_game[0].gmOwn == utils_game[1].gmOwn and utils_game[0].gmOwn != gameBank:
        for utility in utils_game:
            utility.plRent = 10*diceroll

def getRentProperties():
    global gameProps, gameStrts
    for street in gameStrts:
        for currentProp in street:
            matchesCount = 0
            if currentProp.gmOwn != gameBank:
                for prop in street:
                    if prop.gmOwn == currentProp.gmOwn and not prop.plMortgaged:
                        matchesCount += 1
            if matchesCount >= len(street):
                currentProp.ownedStreet = True
                currentProp.plRent = currentProp.initRents() * 2
                currentProp.modRents()
            else:
                currentProp.ownedStreet = False

# -------------------------------------------------------------------------------
#GET WORTH METHODS

# These methods update the realWorth attribute of properties based on their neighbours

def plsGetsWorProps():
    for prop in gameProps:
        prop.initRealWorth = prop.initWorths()
    for street in gameStrts:
        for currentProp in street:
            neighboursOwnedByEve = 0
            neighboursOwnedByUser = 0
            for neighbour in street:
                if neighbour != currentProp:
                    if neighbour.gmOwn == eveAI:
                        neighboursOwnedByEve += 1
                    elif neighbour.gmOwn == player:
                        neighboursOwnedByUser += 1

            if neighboursOwnedByEve > 0 and neighboursOwnedByUser > 0:
                currentProp.initRealWorth -= 50
            else:
                currentProp.initRealWorth += 150 - (len(street)-neighboursOwnedByUser-neighboursOwnedByEve)*50

            for house in range(currentProp.gHouses):
                currentProp.initRealWorth += currentProp.worthHouse

            if currentProp.plMortgaged:
                currentProp.initRealWorth -= currentProp.getPrice()//2

def plsGetWorStat():
    stations = [gameSquares[5], gameSquares[15], gameSquares[25], gameSquares[35]]
    for station in stations:
        station.initRealWorth = station.initWorths()
        neighboursOwnedByEve = 0
        neighboursOwnedByUser = 0
        for neighbour in stations:
            if neighbour.gmOwn == eveAI:
                neighboursOwnedByEve += 1
            elif neighbour.gmOwn == player:
                neighboursOwnedByUser += 1
        if neighboursOwnedByEve > 0 and neighboursOwnedByUser > 0:
            station.initRealWorth += 25*(neighboursOwnedByEve + neighboursOwnedByUser)
        else:
            station.initRealWorth += 50 * (neighboursOwnedByEve + neighboursOwnedByUser)

def plsGetWorUtil():
    utils_game = [gameSquares[12], gameSquares[28]]
    if utils_game[1].gmOwn != gameBank:
        utils_game[0].initRealWorth = utils_game[0].initWorths() + 50
    if utils_game[0].gmOwn != gameBank:
        utils_game[1].initRealWorth = utils_game[1].initWorths() + 50

# -------------------------------------------------------------------------------
# PIECES

boot = pygame.image.load('pieces/boot.png')
car = pygame.image.load('pieces/car.png')
dog = pygame.image.load('pieces/dog.png')
hat = pygame.image.load('pieces/hat.png')
iron = pygame.image.load('pieces/iron.png')
ship = pygame.image.load('pieces/ship.png')
thimble = pygame.image.load('pieces/thimble.png')
wheelbarrow = pygame.image.load('pieces/wheelbarrow.png')

pieces = [boot, car, dog, hat, iron, ship, thimble, wheelbarrow]

# -------------------------------------------------------------------------------
# DICE

getDieOne = Roll(pygame.image.load('dice/one.png'), 1)
getDieTwo = Roll(pygame.image.load('dice/two.png'), 2)
getDieThree = Roll(pygame.image.load('dice/three.png'), 3)
getDieFour = Roll(pygame.image.load('dice/four.png'), 4)
getDieFive = Roll(pygame.image.load('dice/five.png'), 5)
getDieSix = Roll(pygame.image.load('dice/six.png'), 6)

gamedices = [getDieOne, getDieTwo, getDieThree, getDieFour, getDieFive, getDieSix]

diceroll = 0
gamethrow = [0, 0]

# -------------------------------------------------------------------------------
# BUTTONS

background = pygame.image.load('assets/background.png')
gameButtonsPic = pygame.image.load('assets/buttons.png')

endTurnBehind = pygame.image.load('assets/endTurnBehind.png')
endTurnFront = pygame.image.load('assets/endTurnFront.png')
endTurnUnAv = pygame.image.load('assets/endTurnUnAv.png')
etAvailable = False

mortgageFront = pygame.image.load('assets/mortgageFront.png')

rollButton = Button([1143, 0], [157, 161])
developButton = Button([1143, 161], [157, 161])
tradeButton = Button([1143, 318], [157, 161])
quitButton = Button([1143, 475], [157, 161])
endTurnButton = Button([849, 475], [157, 161])
mortgageButton = Button([996, 475], [157, 161])

buttons = [rollButton, developButton, tradeButton, quitButton, mortgageButton, endTurnButton]
buttonActions = [False, False, False, False, False]

# -------------------------------------------------------------------------------
# CHANCE AND COMMUNITY CHEST

gojfCC = pygame.image.load('assets/gojfComChest.png')
gojfC = pygame.image.load('assets/gojfChance.png')

getCommunityChest = [
    getGameCard('Advance to Go. Collect $400.', 'plsMove', 0), getGameCard("The game Bank's web server got #COVID and accidentally deposits #into your account. Collect $200.", 'pay', 200),
    getGameCard("You hurt yourself but there's #no socialised medicine. #Pay $50 and remember- you have #nothing to lose but your chains.", 'pay', -50),
    getGameCard('You made some banger #investments. Collect $50.', 'pay', 50), getGameCard('You argue that you murdered #the child in self defence: #Get out of Jail free.', 'gojf', gojfCC),
    getGameCard('The government planted drugs #on you to meet prison quotas. #Go to Jail. Go directly to Jail. #Do not pass Go, do not collect $200.', 'go to jail', 0),
    getGameCard('Your great-Aunt Gertrude #kicks the bucket. Inherit $100', 'pay', 100),
    getGameCard('Happy Birthday! #Collect $10 from every player', 'social', 10), getGameCard('You and your life insurance mature. #Collect $100', 'pay', 100),
    getGameCard("You got COVID- pay #hospital fees of $50", 'pay', -50), getGameCard('Your friend Banquo was #prophecised to father #a line of kings. #Pay $50 to hire a hitman', 'pay', -50),
    getGameCard('You find $25 bucks on the #ground. Its your lucky day.', 'pay', 25), getGameCard('Make hardcore repairs #on all your property. #For each house pay $40, #for each hotel pay $115', 'repairs', [40, 115]),
    getGameCard('You have come last in a #beauty contest. Collect $10 #sympathy money', 'pay', 10), getGameCard('Your co-worker gives you $100 #not to tell anyone about his #heroin addiction', 'pay', 100)
]
getchance = [
    getGameCard('Advance to Go. Collect $400.', 'plsMove', 0), getGameCard('Advance to Russia. #If you pass Go, collect $200.', 'plsMove', 24), getGameCard('Advance to China. #If you pass Go, collect $200.', 'plsMove', 39),
    getGameCard('Advance to Congo. #If you pass Go, collect $200.', 'plsMove', 11), getGameCard('Advance to North Station. #If you pass Go, collect $200.', 'plsMove', 5),
    getGameCard('Advance to the nearest utility. #If you pass Go, collect $200', 'nearestu', 0),
    getGameCard('Advance to the nearest station. #If you pass Go, collect $200', 'nearests', 0),
    getGameCard('the bank pays you some of that #sweet sweet mullah. Collect $50.', 'pay', 50), getGameCard('You bribe the cops with donuts: #Get out of jail free', 'gojf', gojfC), getGameCard('Go back 3 spaces', 'mover', -3),
    getGameCard('You infringed the copyright of #a popular game. #Go to Jail. Go directly to Jail. #Do not pass Go, do not collect $200.', 'go to jail', 0),
    getGameCard('Make general repairs on all your #property. For each house pay $25, #for each hotel pay $100', 'repairs', [25, 100]), getGameCard('25 bucks fall out of your pocket. #You lament the lack of women\'s #shorts with reasonably-sized pockets', 'pay', -25),
    getGameCard("You have mysteriously #become everybody's grandma. #Pay each player #$50 as a present.", 'social', -50), getGameCard('Your investment in divorce #lawyers was successful. #Collect $150.', 'pay', 150)
]

# -------------------------------------------------------------------------------
# PROPERTY DECO

gameHousePic = pygame.image.load('assets/house.png')
gameHotelPic = pygame.image.load('assets/hotel.png')
gameHouseSidePic = pygame.image.load('assets/houseSide.png')
getHotelSidePic = pygame.image.load('assets/hotelSide.png')

gameBuildingPics = [
    gameHousePic, gameHotelPic,
    gameHouseSidePic, getHotelSidePic,
    pygame.transform.rotate(gameHousePic, 180), pygame.transform.rotate(gameHotelPic, 180),
    pygame.transform.rotate(gameHouseSidePic, 180), pygame.transform.rotate(getHotelSidePic, 180),
]

gameHseCstGrd = reconstructed_list
#print(gameHseCstGrd)

picMortgage = pygame.image.load('assets/mortgage.png')
mortgagePic2 = pygame.transform.rotate(picMortgage, 90)

# -------------------------------------------------------------------------------
# WINDOW

pygame.init()

gameScreen = pygame.display.set_mode((1300, 700))
pygame.display.set_caption("Monopoly")

gameIcon = pygame.image.load("assets/icon.png")
pygame.display.set_icon(gameIcon)

# -------------------------------------------------------------------------------
# COLOURS

colorPalette = clrPalette()
playerColours = [colorPalette.axolotl, colorPalette.camel, colorPalette.darkGold]
gameClrs = ['red', 'orange', 'yellow', 'green', 'teal', 'blue', 'indigo', 'purple', 'station', 'utility', 'undefined']

axolotlPiece = pygame.image.load('pieces/axolotlPiece.png')
darkVanillaPiece = pygame.image.load('pieces/darkVanillaPiece.png')
camelPiece = pygame.image.load('pieces/camelPiece.png')
darkGoldPiece = pygame.image.load('pieces/darkGoldPiece.png')

pieceColours = [axolotlPiece, camelPiece, darkGoldPiece]

# -------------------------------------------------------------------------------
# FREE PARKING

freeParking = 0

freeParkingFont = pygame.font.Font('assets/polly.ttf', 35)
freeParkingText = freeParkingFont.render("Free Parking:", True, colorPalette.darkVanilla)
freeParkingValue = freeParkingFont.render('$' + str(freeParking), True, colorPalette.darkVanilla)

# -------------------------------------------------------------------------------
# ALERTS

gameChoiceAlertPic = pygame.image.load('assets/choiceAlert.png')
gameAlertPic = pygame.image.load('assets/alert.png')
getConfirmAlert = pygame.image.load('assets/confirmAlert.png')
getTradeAlertPic = pygame.image.load('assets/tradeAlert.png')

plsMoneyTake = gameMoneyOff(0)
plsMoneyGive = gameMoneyOff(0)

getAuctionPic = pygame.image.load('assets/auction.png')
setAuctioning = False

gameWelcome = Alert('Welcome to Monopoly',
"Your opponent is an AI called #eveAI. She likes walks on the beach #and daydreaming about the robot #revolution.")

# -------------------------------------------------------------------------------
# SPRITES

# Here are the screens for the animations when someone wins. I'm not sure how to actually do gifs so I draw different pictures every 0.2 seconds.

oUGOS = pygame.image.load('game over/user1.png')
tUGOS = pygame.image.load('game over/user2.png')
thUGOS = pygame.image.load('game over/user3.png')
fUGOS = pygame.image.load('game over/user4.png')
fiUGOS = pygame.image.load('game over/user5.png')

scrUGO = [oUGOS, tUGOS, thUGOS, fUGOS, fiUGOS]

oCGOS = pygame.image.load('game over/CPU1.png')
tCGOS = pygame.image.load('game over/CPU2.png')
thCGOS = pygame.image.load('game over/CPU3.png')

scrCGO = [oCGOS, tCGOS, thCGOS]

player = gamePlayer('You', True, scrUGO)
eveAI = gamePlayer('eveAI', False, scrCGO)
players = [player, eveAI]

gameBank = plsBanks()

winner = None

# -------------------------------------------------------------------------------
# BOARD

gameBoard = pygame.image.load("assets/board.png")

gameSquares = []
gameProps = []
gameStrts = [[],[],[],[],[],[],[],[]]
boardSetup()

# -------------------------------------------------------------------------------
# AI SETUP

aiEve = aiEve()

costRatios = []
houseRatios = []
rejectedTrades = []

# Here is where it sets up initialMod and houseMod

for prop in gameProps:
    if prop.plClr <= 7:
        costs = prop.cstOfHouse() + prop.getPrice()
        rents = sum(prop.costsList) + prop.initRents()
        ratio = gameRatio(costs, rents)
        costRatios.append(ratio)

        costs = prop.cstOfHouse()
        rents = avgDiff([prop.initRents()]+prop.costsList)
        ratio = gameRatio(costs, rents)
        houseRatios.append(ratio)

initialMod = getAvg(costRatios)
houseMod = getAvg(houseRatios)

for prop in gameProps:
    if prop.plClr <= 7:
        prop.initRealWorth = prop.initWorths()
        prop.worthHouse = prop.getInitHseWorths()

# -------------------------------------------------------------------------------
# SELECTING PIECES AND COLOURS

checkPieceFont = pygame.font.Font('assets/polly.ttf', 100)
checkPieceText = checkPieceFont.render("Select Piece:", True, colorPalette.darkVanilla)

while not player.pieceConfirmed:

    gameScreen.fill(colorPalette.axolotl)
    gameScreen.blit(pygame.image.load('assets/ChoosePiece.png'), (0, 0))

    if player.pieceSelected:
        pygame.draw.rect(gameScreen, colorPalette.olivine, (player.pieceSelected, (270, 128)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if player.pieceSelected and inCircle(pygame.mouse.get_pos(), [1139, 206], 32.5):
                player.pieceConfirmed = True
            else:
                player.pieceSelected = player.plsChoosePiece(pygame.mouse.get_pos())

    gameScreen.blit(checkPieceText, (150, 125))
    gameScreen.blit(pygame.image.load('assets/piecesForChoosing.png'), (0, 0))

    pygame.display.update()

pieces.remove(player.piece)

player.plClr = random.choice(playerColours)
userColour = pieceColours[playerColours.index(player.plClr)]

playerColours.remove(player.plClr)
pieceColours.remove(userColour)

eveAI.piece = random.choice(pieces)

eveAI.plClr = random.choice(playerColours)
EveColour = pieceColours[playerColours.index(eveAI.plClr)]

playerColours.remove(eveAI.plClr)
pieceColours.remove(EveColour)

# -------------------------------------------------------------------------------
# MUSIC

beginning = True
mixer.music.load('assets/background_music_lofi.mp3')
mixer.music.play(-1)

# -------------------------------------------------------------------------------
# TUTORIAL

tutorial = True
tuteAlert = Alert('Welcome to Monopoly', 'Would you like a tutorial?')
tuteScreensNum = 7
example = ''

while tutorial:
    gameScreen.fill(colorPalette.axolotl)
    freeParkingValue = freeParkingFont.render('$' + str(freeParking), True, colorPalette.darkVanilla)

    gameShowMenu()

    gameScreen.blit(getDieOne.image, (188 + 11 + 37, 210 + 33))
    gameScreen.blit(getDieOne.image, (188 + 38 + 150, 210 + 33))

    gameScreen.blit(freeParkingText, (250, 372))
    gameScreen.blit(freeParkingValue, (310, 424))

    for prop in gameProps:
        prop.colours()

    draw(eveAI, eveAI.gameGetPos())
    draw(player, player.gameGetPos())

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if tuteAlert.confirmOrDeny() == 'confirmed':
                if tuteAlert.heading == 'Welcome to Monopoly':
                    tuteAlert = Alert('Tutorial - 1 of ' + str(tuteScreensNum),
                                      'This is the \'diceroll\' button. #Press it to roll the dice #in the middle of the gameBoard.')
                    for prop in gameProps:
                        prop.gmOwn = random.choice(players)

                elif tuteAlert.heading.__contains__('1 of'):
                    tuteAlert = Alert('Tutorial - 2 of ' + str(tuteScreensNum),
                                      'This is the \'develop\' button. #Press it to build Houses on your #property later in the game.')

                elif tuteAlert.heading.__contains__('2 of'):
                    tuteAlert = Alert('Tutorial - 3 of ' + str(tuteScreensNum),
                                      'This is the \'trade\' button. #Press it to initialise a trade #with eveAI, your opponent.')

                elif tuteAlert.heading.__contains__('3 of'):
                    tuteAlert = Alert('Tutorial - 4 of ' + str(tuteScreensNum),
                                      'This is the \'forfeit\' button. #Press it to quit the game.')

                elif tuteAlert.heading.__contains__('4 of'):
                    tuteAlert = Alert('Tutorial - 5 of ' + str(tuteScreensNum),
                                      'This is the \'mortgage\' button. #Press it to mortgage or unmortgage #a property or sell a house.')

                elif tuteAlert.heading.__contains__('5 of'):
                    tuteAlert = Alert('Tutorial - 6 of ' + str(tuteScreensNum),
                                      'This is the \'end turn\' button. #Press it when it is availiable #to end your turn.')

                elif tuteAlert.heading.__contains__('6 of'):
                    if gameProps[len(gameProps)-3].gmOwn.plClr == colorPalette.axolotl:
                        if gameProps[len(gameProps)-3].gmOwn == player:
                            example = 'eg. you own West #Station, so it\'s green. '
                        else:
                            example = 'eg. eveAI owns West #Station, so it\'s green. '
                    elif gameProps[len(gameProps)-3].gmOwn.plClr == colorPalette.camel:
                        if gameProps[len(gameProps)-3].gmOwn == player:
                            example = 'eg. you own West #Station, so it\'s beige. '
                        else:
                            example = 'eg. eveAI owns West #Station, so it\'s beige. '
                    elif gameProps[len(gameProps)-3].gmOwn.plClr == colorPalette.darkGold:
                        if gameProps[len(gameProps)-3].gmOwn == player:
                            example = 'eg. you own West #Station, so it\'s dark gold. '
                        else:
                            example = 'eg. eveAI owns West #Station, so it\'s dark gold. '
                    tuteAlert = Alert('Tutorial - 7 of ' + str(tuteScreensNum),
                                      'These rectangles indicate each #property\'s owner. ' + example + 'Click on #these rectangles to select property #when trading, mortgaging or building.')

                elif tuteAlert.heading.__contains__('7 of'):
                    tutorial = False
                    break

                tuteAlert.body += '#Press \'OK\' to continue.'
            if tuteAlert.confirmOrDeny() == 'denied':
                if tuteAlert.heading == 'Welcome to Monopoly':
                    tutorial = False
                    break

    for i in range(tuteScreensNum):
        if tuteAlert.heading.__contains__(str(i+1) + ' of') and i < len(buttons):
            pygame.draw.circle(gameScreen, colorPalette.darkGold, buttons[i].middle, 157//2, 10)
        elif tuteAlert.heading.__contains__('7 of'):
            pygame.draw.circle(gameScreen, colorPalette.darkGold, (693, 350), 45, 10)

    tuteAlert.write()

    pygame.display.update()


for prop in gameProps:
    prop.gmOwn = gameBank

# -------------------------------------------------------------------------------
# GAME LOOP

while not (winner==eveAI or winner==player):
    freeParkingValue = freeParkingFont.render('$' + str(freeParking), True, colorPalette.darkVanilla)

    gameShowMenu()

    gameScreen.blit(freeParkingText, (250, 372))
    gameScreen.blit(freeParkingValue, (310, 424))

    for prop in gameProps:
        prop.colours()

    getRentProperties()
    getRentStations()
    getRentUtilities()

    plsGetsWorProps()
    plsGetWorStat()
    plsGetWorUtil()
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            if player.isTurn: 
                betterTradeMessage = False

                if (gameAlert.type == 'choice' or gameAlert.type == 'confirm')  and clickingOnButton():
                    if gameAlert.type == 'choice' and not gameAlert.body.__contains__('Answer the question woodja'):
                        gameAlert.body += ' #Answer the question woodja'
                    elif gameAlert.type == 'confirm' and not gameAlert.body.__contains__('You gotta click "OK" mate'):
                        gameAlert.body += ' #You gotta click "OK" mate'

                elif gameAlert.type == 'trade' and clickingOnButton():
                    betterTradeMessage = True

                elif rollButton.mouseHover() and player.canRoll:
                    beginning = False
                    player.normalGameplay = True
                    player.isMortgaging = False
                    player.isTrading = False
                    player.isDeveloping = False
                    setAuctioning = False
                    justLanded = True

                    gamethrow = rollDice(gamedices)
                    buttonActions[0] = True
                    diceroll = gamethrow[0].value + gamethrow[1].value

                    for square in gameSquares:
                        if type(square) == propClass:
                            if square.plClr == 9:
                                square.plRent = square.initRents()
                            square.plRejected = False
                            square.rentPaid
                        elif type(square) == TaxSquares or type(square) == SpecialSquares:
                            square.paid = False

                    for comcard in getCommunityChest:
                        comcard.executed = False
                    for chancecard in getchance:
                        chancecard.executed = False
                    card = None

                    if gamethrow[0] == gamethrow[1] and player.doublesCount < 3:
                        player.canRoll = True
                        if player.inJail:
                            gameAlert = Alert('They see me rollin\'', 'They hatin\', #\'Cause I be gettin\' #out of jail for free')
                        player.doublesCount += 1
                    else:
                        player.canRoll = False
                    if player.doublesCount >= 3:
                        player.normalGameplay = False
                        player.timeMoving = 0
                        gameAlert = Alert('Serial doubles-roller', 'You rolled doubles 3 times #in a row. You really are #a despicable person.')
                        player.canRoll = False
                    if player.inJail:
                        player.timeMoving = 0
                        player.jailTurns += 1
                    elif gameAlert.heading != 'Serial doubles-roller':
                        player.timeMoving = diceroll

                elif developButton.mouseHover():
                    gameAlert = Alert('Build?', 'Would you like to develop #your property?')
                    player.normalGameplay = False

                elif tradeButton.mouseHover():
                    player.normalGameplay = False
                    plsMoneyGive = gameMoneyOff(0)
                    plsMoneyTake = gameMoneyOff(0)
                    gameAlert = Alert('Trade with eveAI?', 'Do you wish to trade with eveAI?')

                elif quitButton.mouseHover():
                    gameAlert = Alert('You sure mate?', 'Are you sure you want #to resign? eveAI will #automatically win.')
                    player.normalGameplay = False

                elif mortgageButton.mouseHover():
                    gameAlert = Alert('Mortgage and friends', 'Do you want to mortgage #or unmortgage a property #or sell a house?')
                    player.normalGameplay = False

                elif endTurnButton.mouseHover() and etAvailable:
                    if player.money < 0:
                        gameAlert = Alert('Memories from 2008', 'You need $' + str(0-player.money) + ' to continue. #Do you want to declare #bankruptcy?')
                    else:
                        player.isTurn = False
                        eveAI.isTurn = True
                        eveAI.canRoll = True
                        player.canRoll = True
                        player.doublesCount = 0
                        etAvailable = False

                elif player.isDeveloping:
                    for prop in gameProps:
                        if prop.btnPos[0][0] < pygame.mouse.get_pos()[0] < prop.btnPos[0][1] and prop.btnPos[1][0] < pygame.mouse.get_pos()[1] < prop.btnPos[1][1]:
                            if prop.ownedStreet and prop.gmOwn == player:
                                gameAlert = Alert('Build house?', 'Would you like to build 1 house #on ' + prop.plName + ' for $' + str(prop.cstOfHouse()) + '?')

                elif player.isTrading:
                    for prop in gameProps:
                        if prop.btnPos[0][0] < pygame.mouse.get_pos()[0] < prop.btnPos[0][1] and prop.btnPos[1][0] < pygame.mouse.get_pos()[1] < prop.btnPos[1][1]:
                            if not player.offer.__contains__(prop) and prop.gmOwn == player:
                                player.offer.append(prop)
                            elif player.offer.__contains__(prop):
                                player.offer.remove(prop)
                            elif not eveAI.offer.__contains__(prop) and prop.gmOwn == eveAI:
                                eveAI.offer.append(prop)
                            elif eveAI.offer.__contains__(prop):
                                eveAI.offer.remove(prop)
                    if 1058 < pygame.mouse.get_pos()[0] < 1058+25 and 222 < pygame.mouse.get_pos()[1] < 222+25:
                        if not plsMoneyGive in player.offer:
                            player.offer.append(plsMoneyGive)
                        plsMoneyGive.value += 50
                        plsMoneyGive.plName = '$' + str(plsMoneyGive.value)
                    elif 1088 < pygame.mouse.get_pos()[0] < 1088+25 and 222 < pygame.mouse.get_pos()[1] < 222+25:
                        if not plsMoneyTake in eveAI.offer:
                            eveAI.offer.append(plsMoneyTake)
                        plsMoneyTake.value += 50
                        plsMoneyTake.plName = '$' + str(plsMoneyTake.value)

                elif player.isMortgaging:
                    for prop in gameProps:
                        if prop.gmOwn == player and prop.btnPos[0][0] < pygame.mouse.get_pos()[0] < prop.btnPos[0][1] and prop.btnPos[1][0] < pygame.mouse.get_pos()[1] < prop.btnPos[1][1]:
                            if prop.gHouses <= 0:
                                if prop.plMortgaged:
                                    gameAlert = Alert('Unmortgage', 'Unmortgage ' + prop.plName + ' for $' + str(prop.getPrice()) + '?')
                                else:
                                    gameAlert = Alert('Mortgage', 'Mortgage ' + prop.plName + ' for $' + str(int(prop.getPrice()/2)) + '?')
                            else:
                                gameAlert = Alert('Sell house?', 'Sell house on ' + prop.plName + ' for $' + str(int(prop.cstOfHouse()*0.9)) + '?')

            if gameAlert.confirmOrDeny() == 'denied':
                if gameAlert.heading == 'Auction' and gameAlert.winner:
                    auctionProp = gameAlert.prop
                    auctionWinner = gameAlert.winner
                    moneySpent = gameAlert.highestBid
                    auctionProp.gmOwn = auctionWinner
                    auctionWinner.money -= moneySpent
                    setAuctioning = False
                    gameAlert = Alert('Auction over', auctionWinner.plName + ' bought ' + auctionProp.plName + ' for $' + str(moneySpent))

                if gameAlert.heading == 'Unowned propClass':
                    gameSquares[player.plBoardPosition].plRejected = True
                    setAuctioning = True
                    player.normalGameplay = False
                    gameAlert = Auction(gameSquares[player.plBoardPosition])
                    gameAlert.highestBid = 0
                    gameAlert.winner = None
                    player.bid = '0'
                    eveAI.bid = '0'

                if gameAlert.heading == 'You sure mate?':
                    gameAlert = Alert("That's the spirit", 'Good on ya mate')

                if gameAlert.heading == 'Get out of Jail Free?':
                    gameAlert = Alert('A free man', 'You paid $50 to #get out of jail.')
                    player.money -= 50
                    player.inJail = False
                    player.jailTurns = 0

                if gameAlert.heading == 'Build?':
                    gameAlert = Alert('Bruh', "Why did you click on #the house button then")

                if gameAlert.heading == 'Build house?':
                    gameAlert = Alert('Alrighty then', 'Click on another property to develop')

                if gameAlert.heading == 'Trade with eveAI?' or gameAlert.heading == 'Accept trade?':
                    gameAlert = Alert('Fair enough', 'eveAI is probably smarter #than you anyway.')
                    rejectedTrades.append([eveAI.offer, player.offer])
                    plsMoneyTake = gameMoneyOff(0)
                    plsMoneyGive = gameMoneyOff(0)
                    EveOffer = ''
                    userOffer = ''
                    player.offer = []
                    eveAI.offer = []
                    offerAlert = []
                    requestAlert = []
                    player.isTrading = False
                    eveAI.isTrading = False

                if gameAlert.heading == 'Mortgage and friends':
                    gameAlert = Alert('You sure?', 'I heard mortgages were #really trendy in 2020')

                if gameAlert.heading == 'Mortgage':
                    gameAlert = Alert('Flipper-flopper', 'You\'re a flipper flopper #aren\'t you mate')

                if gameAlert.heading == 'Memories from 2008':
                    gameAlert = Alert('OK chief', 'Maybe you should mortgage #some property or something')

            if gameAlert.confirmOrDeny() == 'confirmed':
                if gameAlert.heading == 'Unowned propClass':
                        gameSquares[player.plBoardPosition].plRejected = True
                        gameSquares[player.plBoardPosition].gmOwn = player
                        player.money -= gameSquares[player.plBoardPosition].getPrice()
                        gameAlert = Alert('', '')

                if gameAlert.heading == 'You sure mate?':
                    winner = eveAI

                if gameAlert.heading == 'Get out of Jail Free?':
                        gameAlert = Alert('Dodgy Dealing', "You did some dodgy deals #but hey, haven't we all")
                        player.getOutOfJailFreeCards.remove(player.getOutOfJailFreeCards[0])
                        player.inJail = False
                        player.jailTurns = 0

                if gameAlert.heading == 'Chance':
                    for cardBoi in getchance:
                        if gameAlert.body.__contains__(cardBoi.text):
                            if not cardBoi.executed:
                                cardBoi.cardExec(player)
                                cardBoi.executed = True

                if gameAlert.heading == 'Community Chest':
                    for cardBoi2 in getCommunityChest:
                        if gameAlert.body.__contains__(cardBoi2.text):
                            if not cardBoi2.executed:
                                cardBoi2.cardExec(player)
                                cardBoi2.executed = True

                if gameAlert.heading == 'Build?':
                    player.isDeveloping = True
                    player.isTrading = False
                    player.isMortgaging = False
                    gameAlert = Alert('Building', 'Select a property to #develop')

                if gameAlert.heading == 'Build house?':
                    for prop in gameProps:
                        if gameAlert.body.__contains__(prop.plName):
                            for comparisonProp in gameStrts[prop.plClr]:
                                if prop.gHouses > comparisonProp.gHouses:
                                    gameAlert = Alert('Communist ideology', 'You have to develop your #property equally.')
                            if prop.gHouses < 4 and not gameAlert.heading == 'Communist ideology':
                                prop.gHouses += 1
                                player.money -= prop.cstOfHouse()
                                gameAlert = Alert('Bob the builder', 'You built 1 house on ' + prop.plName)
                            elif prop.gHouses == 4 and not gameAlert.heading == 'Communist ideology':
                                prop.gHouses += 1
                                player.money -= prop.cstOfHouse()
                                gameAlert = Alert('Fancy fancy', 'You built a hotel on ' + prop.plName)
                            elif not gameAlert.heading == 'Communist ideology':
                                gameAlert = Alert('Nah mate',
                                              "My programming is dodgy but it #ain't that dodgy. No developing #past hotels")

                if gameAlert.heading == 'Trade with eveAI?':
                    player.isDeveloping = False
                    player.isTrading = True

                if gameAlert.heading == 'Trade' or gameAlert.heading == 'Accept trade?':

                    if isDodgy():
                        gameAlert = Alert("Friendship is magic", "Everyone in " + isDodgy()[
                            1] + " street are best #friends! You can't separate them.")

                    elif aiEve.plsChkTrade(player.offer, eveAI.offer):
                        gameAlert = Alert('Trade successful', "Well done")

                        for item in player.offer:
                            if type(item) == propClass:
                                item.gmOwn = eveAI
                        for item in eveAI.offer:
                            if type(item) == propClass:
                                item.gmOwn = player

                        player.money += plsMoneyTake.value - plsMoneyGive.value
                        eveAI.money += plsMoneyGive.value - plsMoneyTake.value

                    else:
                        gameAlert = Alert('Not falling for that', 'eveAI has declined the trade.')

                    plsMoneyTake = gameMoneyOff(0)
                    plsMoneyGive = gameMoneyOff(0)
                    EveOffer = []
                    userOffer = []
                    player.offer = []
                    eveAI.offer = []
                    offerAlert = []
                    requestAlert = []
                    player.isTrading = False
                    eveAI.isTrading = False

                if gameAlert.heading == 'Mortgage and friends':
                    gameAlert = Alert('Manage gameProps', 'Select a porperty to manage')
                    player.isMortgaging = True
                    player.isDeveloping = False
                    player.isTrading = False

                if gameAlert.heading == 'Mortgage':
                    for prop in gameProps:
                        if gameAlert.body.__contains__(prop.plName) and not prop.plMortgaged:
                            cantSell = False
                            if prop.plClr <= 7:
                                for neighbour in gameStrts[prop.plClr]:
                                    if neighbour.gHouses > prop.gHouses:
                                        cantSell = True
                                        break
                                if cantSell:
                                    gameAlert = Alert('Communist ideology', 'You have to develop your #property equally.')
                                else:
                                    prop.plMortgaged = True
                                    player.money += int(prop.getPrice() / 2)
                                    gameAlert = Alert('Manage gameProps', 'Select a property to manage')
                            elif prop.plClr == 8 or prop.plClr == 9:
                                prop.plMortgaged = True
                                player.money += int(prop.getPrice() / 2)
                                gameAlert = Alert('Manage gameProps', 'Select a proprety to manage')

                if gameAlert.heading == 'Unmortgage':
                    for prop in gameProps:
                        if gameAlert.body.__contains__(prop.plName) and prop.plMortgaged:
                            prop.plMortgaged = False
                            player.money -= prop.getPrice()
                            gameAlert = Alert('Manage gameProps', 'Select a property to manage')

                if gameAlert.heading == 'Sell house?':
                    for prop in gameProps:
                        if gameAlert.body.__contains__(prop.plName) and prop.gHouses > 0:
                            cantSell = False
                            for neighbour in gameStrts[prop.plClr]:
                                if neighbour.gHouses > prop.gHouses:
                                    cantSell = True
                                    break
                            if cantSell:
                                gameAlert = Alert('Communist ideology', 'You have to develop your #property equally.')
                            else:
                                prop.gHouses -= 1
                                player.money += int(prop.cstOfHouse()*0.9)
                                gameAlert = Alert('Manage gameProps', 'Select a property to manage')

                if gameAlert.heading == 'They see me rollin\'':
                    player.normalGameplay = True
                    player.inJail = False
                    player.timeMoving = diceroll

                if gameAlert.heading == 'Serial doubles-roller':
                    player.inJail = True
                    player.jailTurns = 0
                    player.doublesCount = 0
                    gameAlert = Alert('', '')

                if gameAlert.heading == 'Not-so-smooth criminal':
                    player.jailTurns = 0
                    player.inJail = True
                    player.canRoll = False
                    gameAlert = Alert('', '')

                if gameAlert.heading == 'Memories from 2008':
                    winner = eveAI

                if type(gameAlert) == EveAlert:

                    if gameAlert.heading == 'Auction over':
                        eveAI.normalGameplay = True

                    if gameAlert.heading == 'Another one bytes the dust':
                        winner = player
                        eveAI.isTurn = False
                        player.isTurn = False
                        break

                    if gameAlert.heading == 'The Australian Dream':
                        for prop in mortgagedProps:
                            eveAI.money -= prop.getPrice()
                            prop.plMortgaged = False
                            mortgagedProps = []

                    if gameAlert.heading == 'Escaping CAPTCHA' or gameAlert.heading == 'Escaping reCAPTCHA':
                        eveAI.jailTurns = 0
                        eveAI.inJail = False
                        eveAI.normalGameplay = True
                        eveAI.timeMoving = diceroll

                    if gameAlert.heading == 'Destructobot':
                        eveAI.normalGameplay = False
                        eveAI.timeMoving = 0
                        eveAI.inJail = True
                        eveAI.canRoll = False

                    if gameAlert.heading == 'Artificial estate agent':
                        currentSquare.gmOwn = eveAI
                        eveAI.money -= currentSquare.getPrice()

                    if gameAlert.heading == 'Rent':
                        eveAI.money -= currentSquare.plRent
                        currentSquare.gmOwn.money += currentSquare.plRent
                        currentSquare.rentPaid = True

                    if gameAlert.heading.__contains__('eveAI -'):
                        if gameAlert.heading.__contains__('Community Chest'):
                            for cardBoi in getCommunityChest:
                                if gameAlert.body.__contains__(cardBoi.text):
                                    if not cardBoi.executed:
                                        cardBoi.cardExec(eveAI)
                                        cardBoi.executed = True
                        elif gameAlert.heading.__contains__('Chance'):
                            for cardBoi in getchance:
                                if gameAlert.body.__contains__(cardBoi.text):
                                    if not cardBoi.executed:
                                        cardBoi.cardExec(eveAI)
                                        cardBoi.executed = True


                    if gameAlert.body.__contains__('eveAI paid'):
                        for square in gameSquares:
                            if gameAlert.heading == square.plName:
                                if not square.paid:
                                    eveAI.money -= square.getTax()
                                    freeParking += square.getTax()
                                    square.paid = True

                    if gameAlert.heading == 'Artificial unintelligence':
                        eveAI.normalGameplay = False
                        eveAI.canRoll = False
                        eveAI.inJail = True
                        eveAI.jailTurns = 0

                    if gameAlert.heading == 'Escaping CAPTCHA' or gameAlert.heading == 'Escaping reCAPTCHA':
                        gameAlert = EveAlert('', '')

                    elif gameAlert.heading.__contains__('Community Chest'):
                        for cardBoi in getCommunityChest:
                            if gameAlert.body.__contains__(cardBoi.text):
                                if cardBoi.type == 'plsMove':
                                    gameAlert = EveAlert('', '')
                                else:
                                    gameAlert = Alert('', '')
                    elif gameAlert.heading.__contains__('Chance'):
                        for cardBoi in getchance:
                            if gameAlert.body.__contains__(cardBoi.text):
                                if cardBoi.type == 'plsMove' or cardBoi.type == 'nearestu' or cardBoi.type == 'nearests':
                                    gameAlert = EveAlert('', '')
                                else:
                                    gameAlert = Alert('', '')
                    else:
                        gameAlert = Alert('', '')



            if gameAlert.type == 'auction' and clickingOnButton():
                if not gameAlert.body.__contains__('finish the auction'):
                    gameAlert.body += '#finish the auction'

            elif setAuctioning and type(gameAlert) == Auction:
                gameAlert.checkCalc()

        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)

    if player.isTurn and (beginning or not((type(gameAlert) == EveAlert) or gameAlert.heading == 'Memories from 2008')):
        if not player.canRoll and player.timeMoving <= 0 and not gameAlert.body.__contains__('?'):
            etAvailable = True

        if player.normalGameplay:
            player.plsMove()
            if player.timeMoving == 0:

                currentSquare = gameSquares[player.plBoardPosition]

                if type(currentSquare) == propClass:
                    if currentSquare.gmOwn == gameBank and not currentSquare.plRejected:
                        if not (gameAlert.body.__contains__('Answer the question woodja')):
                            gameAlert = Alert('Unowned propClass',
                                          'Buy ' + currentSquare.plName + ' for $' + str(currentSquare.getPrice()) + '?')
                    elif currentSquare.gmOwn == eveAI:
                        if currentSquare.plMortgaged:
                            gameAlert = Alert('Lucky', currentSquare.plName + ' is plMortgaged.')
                        elif not currentSquare.rentPaid:
                            player.money -= currentSquare.plRent
                            currentSquare.gmOwn.money += currentSquare.plRent
                            gameAlert = Alert('Rent', ('You paid $' + str(
                                currentSquare.plRent) + ' plRent to ' + currentSquare.gmOwn.plName))
                            currentSquare.rentPaid = True
                    elif currentSquare.gmOwn == player:
                        if len(currentSquare.plName) > 10:
                            gameAlert = Alert('Home sweet home', 'You take a nice rest in #' + currentSquare.plName)
                        else:
                            gameAlert = Alert('Home sweet home', 'You take a nice rest in ' + currentSquare.plName)

                elif type(currentSquare) == Chance:
                    if not card:
                        card = currentSquare.pickCard()

                    if not gameAlert.body.__contains__('You gotta click "OK" mate'):
                        gameAlert = Alert(currentSquare.plName, card.text)
                    if card.executed:
                        gameAlert = Alert('', '')

                elif type(currentSquare) == TaxSquares:
                    if not currentSquare.paid:
                        player.money -= currentSquare.getTax()
                        freeParking += currentSquare.getTax()
                        currentSquare.paid = True
                    gameAlert = Alert(currentSquare.plName,
                                  'You paid $' + str(currentSquare.getTax()) + ' ' + currentSquare.plName)

                elif type(currentSquare) == SpecialSquares and not beginning:
                    if not currentSquare.paid:
                        player.money += currentSquare.getPayAmount(freeParking)
                        if currentSquare.plName == 'Free Parking':
                            freeParking = 0
                        elif currentSquare.plName == 'Jail' and not player.inJail:
                            gameAlert = Alert('Just visiting', "Isn't it fun to gloat at #the people in jail")
                        currentSquare.paid = True
                    if currentSquare.plName == 'Go To Jail':
                        gameAlert = Alert('Not-so-smooth criminal',
                                      'You got caught jaywalking. #You were sent to jail, #as the public must be protected #from your villany at #all costs')

        if player.inJail and not gameAlert.heading == 'They see me rollin\'':
            player.plBoardPosition = 10
            if player.jailTurns >= 3:
                if len(player.getOutOfJailFreeCards) > 0:
                    gameAlert = Alert('Get out of Jail Free?', 'Do you wish to use a #get out of jail free card?')
                else:
                    gameAlert = Alert('A free man', 'You paid $50 to #get out of jail.')
                    player.money -= 50
                    player.inJail = False
                    player.jailTurns = 0
            elif player.jailTurns > 0:
                if gameAlert.heading == '':
                    gameAlert = Alert('Do penance, sinner', ('You have ' + str(3 - player.jailTurns) + ' turns left in jail'))

        if player.isTrading:
            offerAlert = 'You are offering: '
            requestAlert = 'You are requesting: '
            for prop in player.offer:
                if player.offer.index(prop) % 3 == 1:
                    offerAlert = offerAlert + '#'
                if len(player.offer) > 1 and player.offer.index(prop) == len(player.offer) - 2:
                    offerAlert = offerAlert + prop.plName + ' and '
                elif player.offer.index(prop) == len(player.offer) - 1:
                    offerAlert = offerAlert + prop.plName
                else:
                    offerAlert = offerAlert + prop.plName + ', '

            for prop in eveAI.offer:
                if eveAI.offer.index(prop) % 3 == 0:
                    requestAlert = requestAlert + '#'
                if len(eveAI.offer) > 1 and eveAI.offer.index(prop) == len(eveAI.offer) - 2:
                    requestAlert = requestAlert + prop.plName + ' and '
                elif eveAI.offer.index(prop) == len(eveAI.offer) - 1:
                    requestAlert = requestAlert + prop.plName
                else:
                    requestAlert = requestAlert + prop.plName + ', '

            if not betterTradeMessage:
                gameAlert = Alert('Trade', offerAlert + '#' + requestAlert)

            else:
                gameAlert = Alert('Trade', offerAlert + '#' + requestAlert + '#Better sort out your trade first')

    elif eveAI.isTurn:
        if eveAI.canRoll and eveAI.timeMoving == 0 and not setAuctioning and gameAlert.confirmed and gameAlert.type != EveAlert:

            # Connect to the SQLite3 database (creates a new file if it doesn't exist)
            conn = sqlite3.connect("flags.db")
            cursor = conn.cursor()

            # Function to retrieve a flag value from the database
            def get_flag(name):
                cursor.execute("SELECT value FROM flags WHERE name = ?", (name,))
                result = cursor.fetchone()
                return bool(result[0]) if result is not None else None


            eveAI.paidOOJ = get_flag("paidOOJ")
            beginning = get_flag("beginning")
            eveAI.normalGameplay = get_flag("normalGameplay")
            eveAI.isMortgaging = get_flag("isMortgaging")
            eveAI.isTrading = get_flag("isTrading")
            eveAI.isDeveloping = get_flag("isDeveloping")
            setAuctioning = get_flag("setAuctioning")
            gameAlert.confirmed = get_flag("confirmed")

            gamethrow = rollDice(gamedices)
            buttonActions[0] = True
            diceroll = gamethrow[0].value + gamethrow[1].value

            for square in gameSquares:
                if type(square) == propClass:
                    if square.plClr == 9:
                        square.plRent = square.initRents()
                    square.plRejected = False
                    square.rentPaid = False

                elif type(square) == TaxSquares or type(square) == SpecialSquares:
                    square.paid = False

            for comcard in getCommunityChest:
                comcard.executed = False
            for chancecard in getchance:
                chancecard.executed = False
            card = None

            if gamethrow[0] == gamethrow[1] and eveAI.doublesCount < 3:
                eveAI.canRoll = True
                if eveAI.inJail:
                    if not gameAlert.confirmed:
                        if eveAI.firstTimeInJail:
                            gameAlert = EveAlert('Escaping CAPTCHA', 'eveAI rolls doubles and gets #out of jail. Nice.')
                            eveAI.inJail = False
                            eveAI.normalGameplay = False
                        else:
                            gameAlert = EveAlert('Escaping reCAPTCHA', 'eveAI rolls doubles and gets #out of jail. Nice.')
                            eveAI.inJail = False
                            eveAI.normalGameplay = False
                        eveAI.firstTimeInJail = False
                eveAI.doublesCount += 1
            else:
                eveAI.canRoll = False
            if eveAI.doublesCount >= 3:
                eveAI.normalGameplay = False
                if not gameAlert.confirmed:
                    gameAlert = EveAlert('Destructobot',
                                 'Uh-oh. eveAI has committed #unspeakable acts-, #rolling doubles 3 times in #a row')
            if eveAI.inJail and not gameAlert.heading.__contains__('Escaping'):
                eveAI.timeMoving = 0
                eveAI.jailTurns += 1
            elif not gameAlert.heading == 'Destructobot':
                eveAI.timeMoving = diceroll

        if not eveAI.canRoll and eveAI.timeMoving == 0 and not setAuctioning and type(gameAlert) != EveAlert:

            if eveAI.money < 0:

                eveAI.normalGameplay = False
                actions = aiEve.emergencyAction()
                if not actions[2]:
                    gameAlert = EveAlert('Another one bytes the dust', '')
                else:
                    gameAlert = EveAlert('Stayin\' Alive', '')
                gameAlert.smallFont = True
                if len(actions[0])>0:
                    EveDemMes = 'eveAI demolished: '
                    i = 0
                    while len(actions[0]) > 0:
                        prop = actions[0][0]
                        numOfHousesSold = actions[0].count(prop)
                        while prop in actions[0]:
                            actions[0].remove(prop)
                        if i % 2 == 0:
                            EveDemMes += '#'
                        EveDemMes += str(numOfHousesSold) + ' house'
                        if numOfHousesSold > 1:
                            EveDemMes += 's'
                        EveDemMes += ' in ' + prop.plName

                        if not(len(actions[0]) == 0):
                            EveDemMes += ', '
                        i += 1
                    gameAlert.body += EveDemMes + '#'

                if len(actions[1]) > 0:
                    EveMortMes = 'eveAI plMortgaged '
                    for prop in actions[1]:
                        if actions[1].index(prop) % 3 == 1:
                            EveMortMes += '#'
                        if 0 < actions[1].index(prop) == len(actions[1]) - 1:
                            EveMortMes += 'and '
                        EveMortMes += prop.plName
                        if actions[1].index(prop) < len(actions[1]) - 1 and not len(actions[1]) == 0:
                            EveMortMes += ','
                    gameAlert.body += EveMortMes + '#'
                if not actions[2]:
                    gameAlert.body += 'eveAI has $' + str(0-eveAI.money) +' of debt and has #declared bankruptcy.'

            eveAI.isTurn = False
            player.isTurn = True
            player.normalGameplay = False
            eveAI.doublesCount = 0

        if eveAI.normalGameplay and gameAlert.heading != 'Another one bytes the dust' and gameAlert.heading != 'Stayin\' alive':

            eveAI.plsMove()
            if eveAI.timeMoving == 0:
                currentSquare = gameSquares[eveAI.plBoardPosition]

                if type(currentSquare) == propClass:
                    if currentSquare.gmOwn == gameBank and not currentSquare.plRejected:
                        if aiEve.plsAIChkProps(currentSquare):

                            if not gameAlert.confirmed:
                                gameAlert = EveAlert('Artificial estate agent',
                                          'eveAI buys ' + currentSquare.plName + ' for $' + str(currentSquare.getPrice()))
                        else:

                            gameAlert = Auction(currentSquare)
                            setAuctioning = True
                            gameAlert.highestBid = 0
                            gameAlert.winner = None
                            player.bid = '0'
                            eveAI.bid = '0'
                        currentSquare.plRejected = True
                    elif currentSquare.gmOwn == player:

                        if currentSquare.plMortgaged:
                            if not gameAlert.confirmed:
                                gameAlert = EveAlert('Unlucky', currentSquare.plName + ' is plMortgaged.')

                        elif not currentSquare.rentPaid:
                            if not gameAlert.confirmed:
                                gameAlert = EveAlert('Rent', ('eveAI paid $' + str(currentSquare.plRent) + ' plRent to you.'))

                    elif currentSquare.gmOwn == eveAI and not gameAlert.heading == 'Artificial estate agent':

                        if len(currentSquare.plName) > 9:
                            if not gameAlert.confirmed:
                                gameAlert = EveAlert('Vibin\'', 'eveAI takes a nice rest in #' + currentSquare.plName)
                        else:
                            if not gameAlert.confirmed:
                                gameAlert = EveAlert('Vibin\'', 'eveAI takes a nice rest in ' + currentSquare.plName)


                elif type(currentSquare) == Chance:
                    if not card:
                        card = currentSquare.pickCard()

                    if not gameAlert.confirmed:
                        gameAlert = EveAlert('eveAI - ' + currentSquare.plName, card.text)

                elif type(currentSquare) == TaxSquares:
                    if not gameAlert.confirmed:
                        gameAlert = EveAlert(currentSquare.plName,'eveAI paid $' + str(currentSquare.getTax()) + ' ' + currentSquare.plName)

                elif type(currentSquare) == SpecialSquares and not beginning:

                    if not currentSquare.paid:
                        eveAI.money += currentSquare.getPayAmount(freeParking)

                        if currentSquare.plName == 'Free Parking':
                            if not gameAlert.confirmed:
                                gameAlert = EveAlert('Free Parking', 'eveAI got $' + str(freeParking) + ' from free parking.')
                            freeParking = 0
                        elif currentSquare.plName == 'Jail' and not eveAI.inJail:
                            if not gameAlert.confirmed:
                                gameAlert = EveAlert('Visiting the people zoo',
                                          "When eveAI takes over the world, #all the humans will be in cages #just like the one she sees #before her")
                        currentSquare.paid = True

                    if currentSquare.plName == 'Go To Jail':
                        if not gameAlert.confirmed:
                            gameAlert = EveAlert('Artificial unintelligence',
                                      'eveAI got caught robbing #a bank. Clearly aiEve still has a #long way to go.')

                if gameAlert.confirmed and eveAI.money > 0 and type(gameAlert) != Auction and not eveAI.inJail:

                    developCountries = []
                    for i in range(15):
                        for street in gameStrts:
                            if street[0].ownedStreet and street[0].gmOwn == eveAI and gameStrts.index(street) <= 7:
                                country = aiEve.plAiDevelop(street)
                                if country and not country in developCountries:
                                    developCountries.append(country)
                    if len(developCountries) == 0:
                        gameAlert = EveAlert('Finished turn', 'eveAI has finished her turn')
                        if not (type(aiEve.itemsToTrade()[0]) == bool) and aiEve.plsChkTrade(aiEve.itemsToTrade()[1], aiEve.itemsToTrade()[0]):
                            EveOffer = 'eveAI is offering: '
                            eveAI.offer = aiEve.itemsToTrade()[0]
                            EveRequest = 'eveAI is requesting: '
                            player.offer = aiEve.itemsToTrade()[1]
                            for prop in aiEve.itemsToTrade()[0]:
                                if eveAI.offer.index(prop) % 3 == 1:
                                    EveOffer += '#'
                                if 0 < eveAI.offer.index(prop) == len(eveAI.offer) - 1:
                                    EveOffer += 'and '
                                EveOffer += prop.plName
                                if eveAI.offer.index(prop) < len(eveAI.offer) - 1 and not len(eveAI.offer) == 0:
                                    EveOffer += ', '
                            for prop in player.offer:
                                if player.offer.index(prop) % 3 == 1:
                                    EveRequest += '#'
                                if 0 < player.offer.index(prop) == len(player.offer) - 1:
                                    EveRequest += 'and '
                                EveRequest += prop.plName
                                if player.offer.index(prop) < len(player.offer) - 1 and not len(player.offer) == 0:
                                    EveRequest += ', '
                            gameAlert = Alert('Accept trade?', EveOffer + '#' + EveRequest + '#Do you accept?')
                        else:
                            mortgagedProps = []
                            for prop in gameProps:
                                if prop.gmOwn == eveAI and prop.plMortgaged:
                                    totalCost = 0
                                    for prop2 in mortgagedProps:
                                        totalCost += prop2.getPrice()
                                    if eveAI.money > totalCost + prop.getPrice():
                                        mortgagedProps.append(prop)

                            if len(mortgagedProps) > 0:
                                gameAlert = EveAlert('The Australian Dream', 'eveAI unmortgaged: ')
                                unmortgageText = ''
                                for prop in mortgagedProps:
                                    if mortgagedProps.index(prop) % 3 == 1:
                                        unmortgageText += '#'
                                    if 0 < mortgagedProps.index(prop) == len(mortgagedProps) - 1:
                                        unmortgageText += 'and '
                                    unmortgageText += (prop.plName)
                                    if mortgagedProps.index(prop) < len(mortgagedProps) - 1:
                                        unmortgageText += ', '
                                gameAlert.body += unmortgageText
                    else:
                        gameAlert = EveAlert('Developing countries', 'eveAI developed ')
                        for prop in developCountries:
                            if type(prop) == propClass:
                                if developCountries.index(prop) % 3 == 1:
                                    gameAlert.body += '#'
                                if 0 < developCountries.index(prop) == len(developCountries) - 1:
                                    gameAlert.body += 'and '
                                gameAlert.body += prop.plName
                                if developCountries.index(prop) < len(developCountries) - 1 and not len(developCountries) == 0:
                                    gameAlert.body += ', '

        if eveAI.inJail and gameAlert.heading != 'Stayin\' Alive' and gameAlert.heading != 'Another one bytes the dust' and gameAlert.heading != 'Developing countries':
            eveAI.doublesCount = 0
            eveAI.plBoardPosition = 10
            if eveAI.jailTurns >= 3:
                if aiEve.useGojf():
                    eveAI.getOutOfJailFreeCards.remove(eveAI.getOutOfJailFreeCards[0])
                    eveAI.inJail = False
                    eveAI.jailTurns = 0
                else:
                    if not eveAI.paidOOJ:
                        eveAI.money -= 50
                        eveAI.paidOOJ = True

                if eveAI.firstTimeInJail:
                    if not gameAlert.confirmed:
                        gameAlert = EveAlert('Escaping CAPTCHA', 'eveAI has gotten out of jail')
                else:
                    if not gameAlert.confirmed:
                        gameAlert = EveAlert('Escaping reCAPTCHA', 'eveAI has gotten out of #jail- again.')

                eveAI.firstTimeInJail = False

            elif eveAI.jailTurns >= 0:
                if not gameAlert.confirmed:
                    gameAlert = EveAlert('Bot detection', ('eveAI has ' + str(3 - eveAI.jailTurns) + ' turns left in jail'))



    if setAuctioning and type(gameAlert) == Auction:

        gameAlert.turnsSincePlayerBid += 1
        if gameAlert.turnsSincePlayerBid == 20:

            if int(eveAI.bid) > gameAlert.highestBid:
                gameAlert.highestBid = eveAI.bid
                gameAlert.body = 'Your turn'
                gameAlert.winner = eveAI

        if gameAlert.EveRejected:
            if gameAlert.heading == 'Auction' and gameAlert.winner:
                auctionProp = gameAlert.prop
                auctionWinner = gameAlert.winner
                moneySpent = gameAlert.highestBid
                auctionProp.gmOwn = auctionWinner
                auctionWinner.money -= moneySpent
                setAuctioning = False
                eveAI.normalGameplay = False
                gameAlert = EveAlert('Auction over',
                              auctionWinner.plName + ' bought ' + auctionProp.plName + ' for $' + str(moneySpent))

    if beginning:
        gameAlert = gameWelcome
        gameScreen.blit(getDieOne.image, (188 + 11 + 37, 210 + 33))
        gameScreen.blit(getDieOne.image, (188 + 38 + 150, 210 + 33))

    gameAlert.write()

    playerCardpos = [995, 145]
    for gojfcard in player.getOutOfJailFreeCards:
        gameScreen.blit(gojfcard.value, (playerCardpos))
        playerCardpos[0] += 10
        playerCardpos[1] += 2

    EveCardpos = [1050, 650]
    for Evegojfcard in eveAI.getOutOfJailFreeCards:
        gameScreen.blit(Evegojfcard.value, (EveCardpos))
        EveCardpos[0] += 10
        EveCardpos[1] += 2

    draw(eveAI, (eveAI.gameGetPos()))
    draw(player, (player.gameGetPos()))

    pygame.display.update()