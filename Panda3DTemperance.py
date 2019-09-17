import math
import random
import sys
#All these remaining imports are from Panda3D
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from direct.gui.DirectGui import *
from panda3d.core import *
from panda3d.ai import *
 

#CONSTANTS
NUMBER_AGENTS = 100 # Number of agents to create
NUMBER_FOOD = 100 # Number of food to create
SIM_AREA = 200 # Area for randomly generating agents and food
FOOD_REGROWTH = 1 # X number of seconds before regrowing food

AGENT_VISION = 15 # The range of vision of agents for food
METABOLISM_RATE = 5 # Agents lose 1 health every x seconds
WANDER_RADIUS = SIM_AREA # How far can the agents wander around from original position
 

class AgentData:
    def __init__(self):
        #The many variables of the agent
        self.isAlive = True
        self.health = 10
        self.timesSick = 0 # i.e. times sick from excess
        self.rules = {"rule1": False, "rule1Strength" : 0, # Whether the agent knows the rule and how strongly
                    "rule2": False, "rule2Strength" : 0,
                    "rule2a": False, "rule2aStrength" : 0,
                    "rule3": False, "rule3Strength" : 0,
                    "rule3a": False, "rule3aStrength" : 0}
                    #"rule3b": False, "rule3bStrength" : 0}
        self.timesPunished2 = 0 # Times punished for eating 2 sugar
        self.timesPunished3 = 0 # Times punished for eating 3 sugar
        self.seeing = [] # All the food seen by the agent
        self.avoiding = [] # The food (integers) that the agent decided to avoid
        self.pursuing = -1  # The food (an integer) that the agent is pursuing
        self.isPursuing = False # Currently in pursuit?
        #These following are for displaying purposes
        self.pursuingScores = {"ID": -1, "Amount": -1, "P": -1, "E": -1, "C": -1, "S": -1, "Total": -1} # A dictionary for PECS
        self.avoiding1Scores = {"ID": -1, "Amount": -1, "P": -1, "E": -1, "C": -1, "S": -1, "Total": -1} # A dictionary for PECS 
        self.avoiding2Scores = {"ID": -1, "Amount": -1, "P": -1, "E": -1, "C": -1, "S": -1, "Total": -1} # A dictionary for PECS 
        self.avoiding3Scores = {"ID": -1, "Amount": -1, "P": -1, "E": -1, "C": -1, "S": -1, "Total": -1} # A dictionary for PECS 

class FoodData:
    def __init__(self):
        self.amount = random.randint(1, 3)
        self.destroyed = False

class MyApp(ShowBase):
    # Macro-like functions used to reduce the amount to code needed to create the
    # on screen text
    def genLabelText(self, text, i):
        return OnscreenText(text=text, pos=(-0.06, -.06 * (i + 0.5)), fg=(1, 1, 1, 1), 
                            parent=base.a2dTopRight, align=TextNode.A_boxed_right, scale=.06)
    
    def selectLabelText(self, text, i):
        return OnscreenText(text=text, pos=(0.06, -.06 * (i + 0.5)), fg=(1, 1, 1, 1),
                            parent=base.a2dTopLeft,align=TextNode.ALeft, scale=.07)

    def RuleTextA(self, text, i):
        return OnscreenText(text=text, pos=(-0.525, .06 * (i + 0.5)), fg=(1, 1, 1, 1),
                            parent=base.a2dBottomCenter, align=TextNode.ALeft, scale=.06)

    def pursuitTextA(self, text, i, foreground):
        return OnscreenText(text=text, pos=(0.06, .06 * (i + 0.5)), fg=foreground,
                            parent=base.a2dBottomLeft,align=TextNode.ALeft, scale=.07)

    def AvoidTextA(self, text, i):
        return OnscreenText(text=text, pos=(0.86, .06 * (i + 0.5)), fg=(1, 1, 1, 1),
                            parent=base.a2dBottomLeft,align=TextNode.ALeft, scale=.06)

    def avoidTextB(self, text, i):
        return OnscreenText(text=text, pos=(1.66, .06 * (i + 0.5)), fg=(1, 1, 1, 1),
                            parent=base.a2dBottomLeft,align=TextNode.ALeft, scale=.06)            

    def avoidTextC(self, text, i):
        return OnscreenText(text=text, pos=(2.46, .06 * (i + 0.5)), fg=(1, 1, 1, 1),
                            parent=base.a2dBottomLeft,align=TextNode.ALeft, scale=.06)             

    def __init__(self):
        ShowBase.__init__(self)
 
       # The standard title text that's in every tutorial
        # Things to note:
        #-fg represents the forground color of the text in (r,g,b,a) format
        #-pos  represents the position of the text on the screen.
        #      The coordinate system is a x-y based wih 0,0 as the center of the
        #      screen
        #-align sets the alingment of the text relative to the pos argument.
        #      Default is center align.
        #-scale set the scale of the text
        #-mayChange argument lets us change the text later in the program.
        #       By default mayChange is set to 0. Trying to change text when
        #       mayChange is set to 0 will cause the program to crash.
        
        #self.title = OnscreenText(
        #    text="Virtue Ethics Simulation",
        #    parent=base.a2dBottomRight, align=TextNode.A_right,
        #    style=1, fg=(0, 0, 255, 1), bg=(255,0,0,1), pos=(-0.1, 0.1), scale=.07)

        self.skeyEventText = self.genLabelText("[S]: Turn on select agent [OFF]", 1)
        self.genLabelText("[A/D]: Choose selected agent", 2)

        self.selectText1 = self.selectLabelText("", 1)
        self.selectText2 = self.selectLabelText("", 2)
        self.selectText3 = self.selectLabelText("", 3)
        self.selectText4 = self.selectLabelText("", 4)
        self.selectText5 = self.selectLabelText("", 5)
        self.selectText6 = self.selectLabelText("", 6)
        self.selectText7 = self.selectLabelText("", 7)
        self.selectText8 = self.selectLabelText("", 8)

        self.selectText9 = self.RuleTextA("", 6)
        self.selectText10 = self.RuleTextA("", 5)
        self.selectText11 = self.RuleTextA("", 4)
        self.selectText12 = self.RuleTextA("", 3)
        self.selectText13 = self.RuleTextA("", 2)
        self.selectText14 = self.RuleTextA("", 1)

        self.pursuitText = self.pursuitTextA("", 7, (1,1,1,1))
        self.pursuitTextP = self.pursuitTextA("", 5, (255, 0, 0, 0.8))
        self.pursuitTextE = self.pursuitTextA("", 4, (0,1,0,0.8))
        self.pursuitTextC = self.pursuitTextA("", 3, (0,1,1,0.8))
        self.pursuitTextS = self.pursuitTextA("", 2, (1,1,0,0.8))
        self.pursuitTextT = self.pursuitTextA("", 1, (1,1,1,1))
    

        #self.RuleText = self.RuleTextA("Rules known:\nTesting", 1)

        #self.avoidText2 = self.avoidTextB("Second object being avoided\nTesting\nTesting\nTesting", 5)
        #self.avoidText3 = self.avoidTextC("Second object being avoided\nTesting\nTesting\nTesting", 5)

        # A dictionary of what keys are currently being pressed
        # The key events update this list, and our task will query it as input
        self.keys = {"s": 0, "a": 0, "d": 0, "up": 0, "down": 0, "left": 0, "right": 0}

        #The keys that will be accepted for input
        self.accept("escape", sys.exit)
        self.accept("s", self.setKey, ["s", 1])
        self.accept("a", self.setKey, ["a", 1])
        self.accept("d", self.setKey, ["d", 1])
        self.accept("arrow_up", self.setKey, ["up", 1])
        self.accept("arrow_down", self.setKey, ["down", 1])
        self.accept("arrow_left", self.setKey, ["left", 1])
        self.accept("arrow_right", self.setKey, ["right", 1])
        self.accept("arrow_up-up", self.setKey, ["up", 0])
        self.accept("arrow_down-up", self.setKey, ["down", 0])
        self.accept("arrow_left-up", self.setKey, ["left", 0])
        self.accept("arrow_right-up", self.setKey, ["right", 0])

        #At the start the select screen is off
        self.selectScreen = False

        #Selected agent when the select screen is turned on
        self.selectAgent = 0

        #Camera control
        self.disableMouse()
        self.cameraDistance = 150
        self.cameraAdjust = 20
        #Isometric view
        self.camera.setPos(int(math.sqrt(3) * self.cameraDistance/2), 0, self.cameraDistance/2)
        self.camera.lookAt(0, 0, 0)

        # Load the environment model.
        #self.scene = self.loader.loadModel("Level")
        # Reparent the model to render.
        #self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        #self.scene.setScale(5, 5, 5)
        #self.scene.setPos(-8, 42, 0)
 
        # The various rules that can be cognitively learned
        self.rule1Text = "Eating 1 food is good for me."
        self.rule2Text = "Eating 2 food is very good for me."
        self.rule2aText = "Eating 2 food is bad for others."
        self.rule3Text = "Eating 3 food is bad for me."
        self.rule3aText = "Eating 3 food is bad for others."
        #self.rule3bText = "Eating 3 food is bad for me."

        #Create the moving agents and their data
        self.agentlist = []
        self.agentDataList = []
        self.agentArrowList = []
        self.agentArrowExpire = [] # To keep track of when the arrows should disappear above 
        for i in range(NUMBER_AGENTS):
            self.agentlist.append(Actor("Ralph", {"walk": "Ralph-Walk"}))
            self.agentlist[i].reparentTo(self.render)
            self.agentlist[i].setScale(8, 8, 8)
            self.agentlist[i].setPos(random.randint(-SIM_AREA, SIM_AREA), random.randint(-SIM_AREA, SIM_AREA), 0)
            self.agentlist[i].loop("walk")
            # Create corresponding agent data object
            self.agentDataList.append(AgentData())
            # Create arrow object to indicate punishment
            self.agentArrowList.append(Actor("squarrow-model", {"anim": "squarrow-anim"}))
            self.agentArrowList[i].reparentTo(self.agentlist[i])
            self.agentArrowList[i].setScale(0.1, 0.1, 0.1)
            self.agentArrowList[i].setColor(1, 0, 0)
            self.agentArrowList[i].setPos(0, 0, 0)
            self.agentArrowList[i].loop("anim")
            self.agentArrowExpire.append(0.0)

        #Create food resource models
        self.foodlist = []
        self.foodDataList = []
        #self.mars_tex = loader.loadTexture("mars_1k_tex.jpg")
        for i in range(NUMBER_FOOD):
            self.foodlist.append(loader.loadModel("package"))
            #self.foodlist[i].setTexture(self.mars_tex, 1)
            self.foodlist[i].reparentTo(self.render)
            self.foodlist[i].setScale(0.03, 0.03, 0.03)
            self.foodlist[i].setPos(random.randint(-SIM_AREA, SIM_AREA), random.randint(-SIM_AREA, SIM_AREA), 0)
            #self.foodlist[i].setColor(0, 0, 1)
            # Create corresponding food data object
            self.foodDataList.append(FoodData())
            # Create instances depending on amount
            if (self.foodDataList[-1].amount > 1):
                for x in range(1, self.foodDataList[-1].amount):
                    duplicate = (loader.loadModel("package"))
                    #duplicate.setTexture(self.mars_tex, 1)
                    #if (self.foodDataList[-1].amount == 3): 
                    #    self.foodlist[i].setColor(1, 1, 0)
                    #else:
                    #    self.foodlist[i].setColor(1, 0, 0)
                    duplicate.reparentTo(self.foodlist[i])
                    duplicate.setPos(0, 0, x * 55) #put it above
        
        # Set AI
        #Creating AI World
        self.AIworld = AIWorld(render)

        # Give AI behaviors to each agent
        self.AIchar = []
        self.AIbehaviors = []
        for i in range(NUMBER_AGENTS):
            self.AIchar.append(AICharacter("wanderer"+str(i),self.agentlist[i], 10, 1, 5))
            self.AIworld.addAiChar(self.AIchar[i])
            self.AIbehaviors.append(self.AIchar[i].getAiBehaviors())
            #The basic behavior is wander
            self.AIbehaviors[i].wander(5, 0, WANDER_RADIUS, 0.3)

        #Stores the time for food regrowth, metabolism(losing health)
        self.nextfoodregrowth = 0.0
        self.nextMetabolize = 0.0

        #Call the main game loop        
        taskMgr.add(self.GameLoop,"GameLoop")
 
    
    # This simply sets a key in the self.keys dictionary
    # to the given value.
    def setKey(self, key, val):
        self.keys[key] = val


    #########################################################
    ## Decision - The crucial function for the agents      ##
    #########################################################
    def decision(self, agent, food):
        # New set of scores
        physicalScore = 0
        emotionalScore = 0
        cognitiveScore = 0
        socialScore = 0
        #agent = agent1

        # Physical Component
        if (agent.health > 10): 
            physicalScore = 0
        elif (agent.health <= 10 and agent.health > 7):
            physicalScore = 1
        elif (agent.health <= 7 and agent.health > 4):
            physicalScore = 2
        elif (agent.health <= 4 and agent.health > 1):
            physicalScore = 3
        elif (agent.health == 1):
            physicalScore = 4

        # Emotional Component - based on appraisal theory of emotion
        if (food.amount == 1):
            emotionalScore = 1
        if (food.amount == 2):
            emotionalScore = 2
        if (food.amount == 3):
            emotionalScore = 3 - agent.timesSick  # Minus times gotten sick from excess

        # Cognitive Component
        if (food.amount == 1 and agent.rules["rule1"]):
            cognitiveScore += 1
        if (food.amount == 2 and agent.rules["rule2"]):
            cognitiveScore += 2 
        if (food.amount == 2 and agent.rules["rule2a"]):
            cognitiveScore -= agent.rules["rule2aStrength"]
        if (food.amount == 3 and agent.rules["rule3"]):
            cognitiveScore -= agent.rules["rule3Strength"]
        if (food.amount == 3 and agent.rules["rule3a"]):
            cognitiveScore -= agent.rules["rule3aStrength"]

        # Social Component
        if (food.amount == 1):
            socialScore = 1
        if (food.amount == 2):
            socialScore = 1 - agent.timesPunished2
        if (food.amount == 3):
            socialScore = 1 - agent.timesPunished3

        # Decision
        decisionScore = physicalScore + emotionalScore + cognitiveScore + socialScore
        decision = True
        if (decisionScore > 0): 
            decision = True
        elif (decisionScore < 0):
            decision = False 
        elif (decisionScore == 0):
            decision = random.randint(0, 1)

        # Whatever the decision, for display purposes, record the scores
        if (decision == True):
            agent.pursuingScores["ID"] = self.foodDataList.index(food)
            agent.pursuingScores["Amount"] = food.amount
            agent.pursuingScores["P"] = physicalScore
            agent.pursuingScores["E"] = emotionalScore
            agent.pursuingScores["C"] = cognitiveScore
            agent.pursuingScores["S"] = socialScore
            agent.pursuingScores["Total"] = decisionScore

        # Return the agent's decision
        return decision


    #########################################################
    ## The main game loop                                  ##
    #########################################################
    def GameLoop(self,task):

        #Update the AI stuff
        self.AIworld.update()    

        #Clock used for camera movement
        dt = globalClock.getDt()

        #This is the main agent-food loop
        for agent in self.agentlist:
            agent.setColor(1, 1, 1) # Bring back to neutral color
            agentInteger = self.agentlist.index(agent) #Used to synchronize agent list with agent data list
            agentData = self.agentDataList[agentInteger] 
            agentData.seeing = [] #Reset the agent's seeing
            #For all food
            for i in range(NUMBER_FOOD):
                #If an agent can see a food...
                if ((agent.getPos() - self.foodlist[i].getPos()).lengthSquared() < AGENT_VISION ** 2):
                    
                    # Then add it to the seeing list
                    if (i not in agentData.seeing):
                        agentData.seeing.append(i)
                    
                    #If an agent touches a food resource then consume it
                    if ((agent.getPos() - self.foodlist[i].getPos()).lengthSquared() < 1):
                        #Food is "destroyed"
                        self.foodDataList[i].destroyed = True
                        # -- which is actually just a matter of moving it very far to oblivion
                        self.foodlist[i].setPos(500, 500, 500) 
                        #The agent gains health
                        amount = self.foodDataList[i].amount
                        agentData.health += amount
                        #Stop everyone's AI that's pursuing this object 
                        for a in self.agentDataList:
                            if (a.pursuing == i):
                                self.AIbehaviors[self.agentDataList.index(a)].removeAi("pursue")
                        #It can regrow x seconds later
                        self.nextfoodregrowth = task.time + FOOD_REGROWTH
                        #Is the agent punished by the community? Only if it is not alone
                        if (len(self.agentlist) > 1):
                            if (amount == 2):
                                agentData.timesPunished2 += 1             
                                agentData.rules["rule2a"] += True
                                agentData.rules["rule2aStrength"] += 1              
                                self.agentArrowExpire[agentInteger] = task.time + 3 
                            if (amount == 3):
                                agentData.timesPunished3 += 1
                                agentData.rules["rule3a"] += True
                                agentData.rules["rule3aStrength"] += 1
                                self.agentArrowExpire[agentInteger] = task.time + 3
                        #Knowledge is updated
                        if (amount == 1):
                            agentData.rules["rule1"] = True
                            agentData.rules["rule1Strength"] += 1
                        if (amount == 2):
                            agentData.rules["rule2"] = True
                            agentData.rules["rule2Strength"] += 1
                        if (amount == 3):
                            agentData.rules["rule3"] = True
                            agentData.rules["rule3Strength"] += 1

            # Then focus again on the agent
            # Punishment marker in case recently punished
            if (self.agentArrowExpire[agentInteger] > task.time):
                self.agentArrowList[agentInteger].setPos(0, 0, 2)
                self.agentArrowList[agentInteger].setColor(1, 0, 0)
            else:
                self.agentArrowList[agentInteger].setPos(0, 0, 100)

            # If in pursuit of food seen and this is not yet consumed/destroyed by another, continue pursuing
            if (agentData.isPursuing == True and self.foodDataList[agentData.pursuing].destroyed == False):
                self.AIbehaviors[agentInteger].pursue(self.foodlist[agentData.pursuing], 0.4)
                agent.setColor(0, 1, 0, 0.5)
            # If the food it was pursuing is destroyed then pursuing nothing:
            elif (agentData.isPursuing == True and self.foodDataList[agentData.pursuing].destroyed == True):
                agentData.isPursuing = False
                agentData.Pursuing = -1
            # else if the agent is not pursuing then decide whether to pursue something seen, first come first serve
            elif (agentData.isPursuing == False):                     
                for foodSeen in agentData.seeing:
                    if (self.decision(agentData, self.foodDataList[foodSeen])):
                        agentData.pursuing = foodSeen
                        agentData.isPursuing = True
                        break

            #Avoiding is here
            for foodSeen in agentData.seeing:
                if (foodSeen not in agentData.avoiding) and (foodSeen != agentData.pursuing):
                    if (not self.decision(agentData, self.foodDataList[foodSeen])):
                        agentData.avoiding.append(foodSeen)

        #Regrowth food if there's not enough - meaning bring it back from oblivion
        if (task.time > self.nextfoodregrowth):
            for foodData in self.foodDataList:
                if (foodData.destroyed == True):
                    foodData.destroyed = False
                    #Place it randomly somewhere
                    self.foodlist[self.foodDataList.index(foodData)].setPos(random.randint(-SIM_AREA, SIM_AREA), random.randint(-SIM_AREA, SIM_AREA), 0)

        #Agent metabolizes (loses health) every number of seconds (METABOLISM_RATE), if health is 0 then agent dies
        if (task.time > self.nextMetabolize):
            self.nextMetabolize = task.time + METABOLISM_RATE
            for agentData in self.agentDataList:
                agentData.health -= 1
                if (agentData.health == 0):
                    i = self.agentDataList.index(agentData)
                    self.agentlist[i].cleanup()
                    self.agentlist[i].removeNode()
                    self.agentlist[i].delete()
                    del self.agentlist[i]
                    del self.agentDataList[i]
                    del self.agentArrowList[i]
                    del self.AIchar[i]
                    del self.AIbehaviors[i]


        #Detect key presses
        #Toggle the select screen on or off
        if (self.keys["s"] and self.selectScreen == True):
            self.selectScreen = False
            self.skeyEventText.setText("[S]: Turn on select agent [OFF]")
            self.keys["s"] = 0
        if (self.keys["s"] and self.selectScreen == False):
            self.selectScreen = True
            self.skeyEventText.setText("[S]: Turn on select agent [ON]")
            self.keys["s"] = 0
        #The selection of agents
        if (self.keys["d"] and self.selectScreen == True):
            self.selectAgent += 1
            if (self.selectAgent > len(self.agentlist) - 1):
                self.selectAgent = 0
            self.keys["d"] = 0
        if (self.keys["a"] and self.selectScreen == True):
            self.selectAgent -= 1
            if (self.selectAgent < 0):
                self.selectAgent = len(self.agentlist) - 1
            self.keys["a"] = 0
        #The control of the camera
        if (self.keys["up"]):
            self.cameraDistance -= self.cameraAdjust
            #self.camera.setPos(int(math.sqrt(3) * self.cameraDistance/2), 0, self.cameraDistance/2)
        if (self.keys["down"]):
            self.cameraDistance += self.cameraAdjust
            #self.camera.setPos(int(math.sqrt(3) * self.cameraDistance/2), 0, self.cameraDistance/2)
        if (self.keys["left"]):
            self.camera.setX(self.camera, -self.cameraAdjust * dt * 10) 
        if (self.keys["right"]):
            self.camera.setX(self.camera, +self.cameraAdjust * dt * 10)
   
        
        #Update and readjusting of camera
        camvec = self.camera.getPos() - (0, 0, 0)
        camdist = camvec.length()
        camvec.normalize()
        if camdist > self.cameraDistance:
            self.camera.setPos(self.camera.getPos() - camvec * self.cameraAdjust)
        if camdist < self.cameraDistance - self.cameraAdjust:
            self.camera.setPos(self.camera.getPos() + camvec * self.cameraAdjust)
        self.camera.lookAt(0, 0, 0)


        #Select agent and display statistics
        #Clear text every frame, important for immediate updates
        self.selectText1.setText("")
        self.selectText2.setText("")
        self.selectText3.setText("")
        self.selectText4.setText("")
        self.selectText5.setText("")
        self.selectText6.setText("")
        self.selectText7.setText("")
        self.selectText8.setText("")
        self.selectText9.setText("")
        self.selectText10.setText("")
        self.selectText11.setText("")
        self.selectText12.setText("")
        self.selectText13.setText("")
        self.selectText14.setText("")
        self.pursuitText.setText("")
        self.pursuitTextP.setText("")
        self.pursuitTextE.setText("")
        self.pursuitTextC.setText("")
        self.pursuitTextS.setText("")
        self.pursuitTextT.setText("")
        #Display following only if selectScreen is enabled
        if (self.selectScreen == True):
            #If agents die then choose the last in the list
            if (self.selectAgent > len(self.agentlist) - 1):
                self.selectAgent = len(self.agentlist) - 1
            #Set selected agent to blue, but not if there are no more agents
            if (self.selectAgent >= 0):
                #self.agentlist[self.selectAgent].setColor(0, 0, 1)
                self.agentArrowList[self.selectAgent].setPos(0, 0, 2)
                self.agentArrowList[self.selectAgent].setColor(1, 1, 0)
                #Text stuff
                self.selectText1.setText("Selected Agent: " + str(self.selectAgent))
                self.selectText2.setText("Health: " + str(self.agentDataList[self.selectAgent].health))
                #self.selectText3.setText("Seeing: " + str(self.agentDataList[self.selectAgent].seeing))
                if (not self.agentDataList[self.selectAgent].seeing):
                    self.selectText3.setText("Seeing: Nothing")
                else:
                    self.selectText3.setText("Seeing: " + str(self.agentDataList[self.selectAgent].seeing))
                if (self.agentDataList[self.selectAgent].isPursuing):
                    self.selectText4.setText("Pursuing: " + str(self.agentDataList[self.selectAgent].pursuing))
                else:
                    self.selectText4.setText("Pursuing: Nothing")

                if (not self.agentDataList[self.selectAgent].avoiding):
                    self.selectText5.setText("Avoiding: Nothing")
                else:
                    self.selectText5.setText("Avoiding: " + str(self.agentDataList[self.selectAgent].avoiding))
                self.selectText6.setText("Times punished for 2: " + str(self.agentDataList[self.selectAgent].timesPunished2))
                self.selectText7.setText("Times punished for 3: " + str(self.agentDataList[self.selectAgent].timesPunished3))
                #######
                if (self.agentDataList[self.selectAgent].rules["rule1"]):
                    self.selectText9.setText("Agent knows rules: ")
                    self.selectText10.setText(self.rule1Text)
                if (self.agentDataList[self.selectAgent].rules["rule2"]):
                    self.selectText9.setText("Agent knows rules: ")
                    self.selectText11.setText(self.rule2Text)
                if (self.agentDataList[self.selectAgent].rules["rule2a"]):
                    self.selectText12.setText(self.rule2aText)
                if (self.agentDataList[self.selectAgent].rules["rule3"]):
                    self.selectText9.setText("Agent knows rules: ")
                    self.selectText13.setText(self.rule3Text)
                if (self.agentDataList[self.selectAgent].rules["rule3a"]):
                    self.selectText14.setText(self.rule3aText)
                #Then the information at the bottom
                #if (self.agentDataList[self.selectAgent].isPursuing):
                if (self.agentDataList[self.selectAgent].pursuingScores["ID"] != -1):
                    self.pursuitText.setText("Last pursued object: " + str(self.agentDataList[self.selectAgent].pursuingScores["ID"]) + "\n" +
                                           "Amount: " + str(self.agentDataList[self.selectAgent].pursuingScores["Amount"]))
                    self.pursuitTextP.setText("Physical Score: " + str(self.agentDataList[self.selectAgent].pursuingScores["P"]))
                    self.pursuitTextE.setText("Emotional Score: " + str(self.agentDataList[self.selectAgent].pursuingScores["E"]))
                    self.pursuitTextC.setText("Cognitive Score: " + str(self.agentDataList[self.selectAgent].pursuingScores["C"]))
                    self.pursuitTextS.setText("Social Score: " + str(self.agentDataList[self.selectAgent].pursuingScores["S"]))
                    self.pursuitTextT.setText("Total Score: " + str(self.agentDataList[self.selectAgent].pursuingScores["Total"]))


            
        # Continue the game loop        
        return Task.cont


app = MyApp()
app.run()
