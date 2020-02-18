class Odnode:
    def __init__(self, label, data, pos, chPos):
        self.label = label
        self.data = data
        self.pos = pos
        self.chPos = chPos
    
    def setPos(self, newPos):
        self.pos = newPos

    def setChPos(self, chLabel, chNewPos):
        self.chPos[chLabel] = chNewPos