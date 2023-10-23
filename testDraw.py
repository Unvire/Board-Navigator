import pygame
import math
import mathFunctions

class DrawArc():
    def __init__(self):
        '''
        Creates a SoftwareRenderer instance. Variables: resolution, middle of the screen, FPS, running
        '''
        pygame.init()
        self.RES = self.WIDTH, self.HEIGHT = 1600, 900
        self.FPS = 60
        self.screen = pygame.display.set_mode(self.RES)
        self.clock = pygame.time.Clock()

        self.running = True

    def run(self):
        RED = 255, 0, 0
        GREEN = 0, 255, 0
        BLUE = 0, 0, 255
        WHITE = 255, 255, 255
        layer = pygame.Surface((self.WIDTH, self.HEIGHT))
        #######################################

        point1 = (50.9978, 35.1377)
        point2 = (24.6355, 61.5)
        point3 = (61.5, 24.6355)

        rect, startAngle, endAngle = mathFunctions.threePointToPygameArc(point1, point2, point3)
        print(math.degrees(startAngle), math.degrees(endAngle))

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            pygame.draw.arc(layer, WHITE, rect, startAngle, endAngle)

            pygame.draw.circle(layer, RED, point1, 5)
            pygame.draw.circle(layer, GREEN, point2, 5)
            pygame.draw.circle(layer, BLUE, point3, 5)


            self.screen.blit(layer, (0,0))
            pygame.display.update()

        pygame.quit()

if __name__ == '__main__':
    app = DrawArc()
    app.run()


