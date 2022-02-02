#coded by Ruben Bartelet 
#version 1.3
import pygame, math, time, neat, os
from pathlib import Path
import numpy as np
from pygame import draw
from random import randint


pygame.init()

pygame.font.init()

#directory
PROJECT_ROOT = Path(__file__).parent.parent

STAT_FONT = pygame.font.SysFont("arial", 30)

#dimensions for the screen 
WIN_WIDTH = 1600
WIN_HEIGHT = 800

#creating the screen object
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

#the images
CAR_IMAGE = pygame.image.load(PROJECT_ROOT / "CarAI1.2/car.png")
BLUE_CAR_IMAGE = pygame.image.load(PROJECT_ROOT / "CarAI1.2/blue_car.png")
RED_CAR_IMAGE = pygame.image.load(PROJECT_ROOT / "CarAI1.2/red_car.png")
YELLOW_CAR_IMAGE = pygame.image.load(PROJECT_ROOT / "CarAI1.2/yellow_car.png")
WHITE_CAR_IMAGE = pygame.image.load(PROJECT_ROOT / "CarAI1.2/white_car.png")

MAP = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/hitbox_map.png"),(WIN_WIDTH,WIN_HEIGHT))#the map of the hitbox
VIS_MAP = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/visual_map.png"),(WIN_WIDTH,WIN_HEIGHT))#the map that is displayed
LINES = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/lines1.png"),(1500,WIN_HEIGHT))#The lines for the fitness function

MAP_2 = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/hitbox_map2.png"),(WIN_WIDTH,WIN_HEIGHT))#the map of the hitbox
VIS_MAP_2 = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/visual_map2.png"),(WIN_WIDTH,WIN_HEIGHT))#the map that is displayed
LINES_2 = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/lines2.png"),(WIN_WIDTH,WIN_HEIGHT))#The lines for the fitness function

MAP_4 = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/hitbox_map4.png"),(WIN_WIDTH,WIN_HEIGHT))#the map of the hitbox
VIS_MAP_4 = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/visual_map4.png"),(WIN_WIDTH,WIN_HEIGHT))#the map that is displaye
LINES_4 = pygame.transform.scale(pygame.image.load(PROJECT_ROOT / "CarAI1.3/lines4.png"),(WIN_WIDTH,WIN_HEIGHT))#The lines for the fitness function

class Car:
    def __init__(self):
        #position variables
        self.x = 1050
        self.y = 633

        #rotation variables
        self.size = 90
        rand_color = randint(0, 3)
        if rand_color == 0:
            COLOR_IMG = BLUE_CAR_IMAGE
        elif rand_color == 1:
            COLOR_IMG = RED_CAR_IMAGE    
        elif rand_color == 2:
            COLOR_IMG = YELLOW_CAR_IMAGE
        elif rand_color == 3:
            COLOR_IMG = WHITE_CAR_IMAGE
        self.static_surface = pygame.transform.scale(COLOR_IMG, (self.size, self.size))
        self.rotate_surface = self.static_surface
        self.angle = 0
        self.rotating_speed = 5

        #speed variables
        self.speed = 2.5
        self.current_speed = 0
        self.terminal_vel = 20

        self.slowing_down = 0.5
        self.distance_traveled = 0
        self.minimal_speed = 2.5

        #map 
        self.bad_color = (0,255,1,255)
        self.alive = True

        #radar
        self.radars = []
        self.radars_for_draw = []
        self.max_length = 250


        #going the correct way variables
        self.last_color = 'null'
        self.should_get_reward = False
        self.reward = 25
        self.how_long_no_reward = 0
        self.last_how_long_no_reward = 0
        self.constant_how_long_no_reward = 35 #how fast the car between the checkpoints must go or it will be killed 

        self.time = 0

      
    def draw(self, screen):
        screen.blit(self.rotate_surface, (self.x, self.y))

    def get_rotate_image(self, surface, angle):#the function of rotation the car
        rotated_rect = surface.get_rect()
        rotated_image = pygame.transform.rotate(surface, angle)
        rotated_rect.center = rotated_image.get_rect().center
        rotated_image = rotated_image.subsurface(rotated_rect).copy()
        return rotated_image

    def draw_radars(self, screen):
        for radar in self.radars:
            end_position = radar
            pygame.draw.circle(screen,(255,255,255), end_position[0], 5)
            pygame.draw.line(screen, (255,255,255), (self.center_x, self.center_y), end_position[0], 1)#draws a line from the center to the end position.

    def get_radars(self, angle_, map):
        length = 0 #length of the radar
        x = int(self.center_x + math.cos(math.radians(360-(self.angle+angle_)))*length)
        y = int(self.center_y + math.sin(math.radians(360-(self.angle+angle_)))*length)

        while not map.get_at((x,y)) == self.bad_color and length < self.max_length:
            length += 1
            x = int(self.center_x + math.cos(math.radians(360-(self.angle+angle_)))*length)
            y = int(self.center_y + math.sin(math.radians(360-(self.angle+angle_)))*length)
        
        distance = math.sqrt((x - self.center_x)**2 + (y- self.center_y)**2) #theorem of pythagoras, calculates the length of the line 
        self.radars.append([(x,y), int(distance)])


    def check_collision(self, map,lines):
        self.alive = True
        #check if the position of the x and y cord of the point has a 'bad' color
        for x in range(0,4):
            if map.get_at(self.points[x]) == self.bad_color:
                self.alive = False
            elif lines.get_at(self.points[x]) == ((0,0,255,255)):
                if self.last_color == 'null' or self.last_color == 'red':
                    self.last_color = 'blue'                    
                    self.should_get_reward = True
                elif self.last_color == 'blue': 
                    self.last_color = 'blue'
                else:
                    self.alive = False
            elif lines.get_at(self.points[x]) == ((0,255,0,255)):
                if self.last_color == 'blue':
                    self.last_color = 'green'                    
                    self.should_get_reward = True
                elif self.last_color == 'green': 
                    self.last_color = 'green'
                else:
                    self.alive = False
            elif lines.get_at(self.points[x]) == ((255,0,0,255)):
                if self.last_color == 'green':
                    self.last_color = 'red'
                    self.should_get_reward = True
                elif self.last_color == 'red': 
                    self.last_color = 'red'
                else:
                    self.alive = False
                
    
    def get_AI_data(self):
        radars = self.radars
        rad = [0, 0, 0, 0, 0, 0, 0, 0, self.current_speed]
        for i, ra in enumerate(radars):
            rad[i] = int(ra[1] / 30)
        return rad

    def get_reward(self):
        if self.should_get_reward == True:
            self.should_get_reward = False
            return int(self.reward + (self.constant_how_long_no_reward-self.last_how_long_no_reward)*10)#constant reward + time between the checkpoints
        else:
            return int(0)

    def update(self, map, lines, how_long_before_killed):
        #calculate surfaces agian for color swap
        self.rotate_surface = self.static_surface

        self.distance_traveled += self.current_speed**2
        #rotation and how it correlates to position
        self.rotate_surface = self.get_rotate_image(self.static_surface, self.angle)
        self.x += math.cos(math.radians(360 - self.angle)) * self.current_speed
        self.y += math.sin(math.radians(360 - self.angle)) * self.current_speed
        
        #calculate position of the four points
        self.center_x = int(self.x) + (self.size/2)
        self.center_y = int(self.y) + (self.size/2)
        
        length = 30 #the length from the middle
        
        #calculate the position of the four points
        left_top_x = math.cos(math.radians(330 - self.angle)) * length + self.center_x
        left_top_y = math.sin(math.radians(330 - self.angle)) * length + self.center_y 

        right_top_x = math.cos(math.radians(210 - self.angle)) * length + self.center_x
        right_top_y = math.sin(math.radians(210 - self.angle)) * length + self.center_y 
        
        left_bottom_x = math.cos(math.radians(150 - self.angle)) * length + self.center_x
        left_bottom_y = math.sin(math.radians(150 - self.angle)) * length + self.center_y 

        right_bottom_x = math.cos(math.radians(30 - self.angle)) * length + self.center_x
        right_bottom_y = math.sin(math.radians(30 - self.angle)) * length + self.center_y

        self.topleft = [left_top_x,left_top_y]
        self.topRight = [right_top_x, right_top_y]
        self.bottomLeft = [left_bottom_x, left_bottom_y]
        self.bottomRight = [right_bottom_x,right_bottom_y]

        self.points = np.array((self.topleft, self.topRight, self.bottomLeft, self.bottomRight))
        self.points = self.points.astype(int)
        
        self.check_collision(map, lines)
        self.radars.clear()#start again with calculation the position of the radars
        for angle in range(360,0,-45):#the eight angles of radars
            self.get_radars(angle, map)
        
        
        if self.should_get_reward == False:
            self.how_long_no_reward += 1
        
        if self.how_long_no_reward > self.constant_how_long_no_reward:
            self.alive = False
        
        if self.should_get_reward == True:
            self.last_how_long_no_reward = self.how_long_no_reward
            self.how_long_no_reward = 0

        self.time += 1
        if how_long_before_killed < self.time:
            self.alive = False
        
        
        

clock = pygame.time.Clock()
draw_radar = False
draw_lines = False
draw_anything = True #so that the AI training doesnt need as much computation power
how_long_before_killed = 500 #how many frames before the car is killed. This is so that cars cannot keep living forever and make no improvement
gen = 0
CURRENT_MAP_INFO = []

def random_map():
    rand = randint(1,3)
    if rand == 1:
        MAP_INFO = [MAP,VIS_MAP,LINES]
        return MAP_INFO 
    elif rand == 2:
        MAP_INFO = [MAP_2,VIS_MAP_2,LINES_2]
        return MAP_INFO 
    elif rand == 3:
        MAP_INFO = [MAP_4,VIS_MAP_4,LINES_4]
        return MAP_INFO 
         

def draw_window(screen, cars, radar, lines, visual_map, liness):
    if draw_anything:
        screen.blit(visual_map, (0,0))
        if lines:
            screen.blit(liness, (0,0))
        for car in cars:
            if car.alive:
                if radar:
                    car.draw_radars(screen)
                car.draw(screen)
                #drawing the collision dots (will remove in later versions)
                color = (0,0,0)
                size_of_dot = 0
                pygame.draw.rect(screen, (color), pygame.Rect(car.topleft[0], car.topleft[1], size_of_dot, size_of_dot))
                pygame.draw.rect(screen, (color), pygame.Rect(car.topRight[0], car.topRight[1], size_of_dot, size_of_dot))
                pygame.draw.rect(screen, (color), pygame.Rect(car.bottomLeft[0], car.bottomLeft[1], size_of_dot, size_of_dot))
                pygame.draw.rect(screen, (color), pygame.Rect(car.bottomRight[0], car.bottomRight[1], size_of_dot, size_of_dot))
        
                text = STAT_FONT.render("Frames left: "+str(how_long_before_killed - car.time), 1, (0,0,0))
                screen.blit(text, (WIN_WIDTH- 10 - text.get_width(),10))#will always keep the score on the screen 
                text2 = STAT_FONT.render("Gen: "+str(gen), 1, (0,0,0))
                screen.blit(text2, (WIN_WIDTH- 10 - text2.get_width(),text.get_height()*1.5))#will always keep the score on the screen 
            
    else:
        screen.fill((0,0,0))

def main(genomes, config):
    global draw_lines, draw_radar, how_long_before_killed, gen, draw_anything
    nets = []
    cars = []
    ge = []
    CURRENT_MAP_INFO = random_map()

    for _, g in genomes: #_, because genomes are a tuple and this way we only get the genome id
        net = neat.nn.FeedForwardNetwork.create(g, config)# sets a neural network for the genome
        nets.append(net) #appends it to the nets list
        cars.append(Car()) #append it to the cars list
        g.fitness = 0 #set the genome fitness to zero
        ge.append(g) #append the genome to the genome list

    run = True
    while run:#the main game loop
        clock.tick(30)#the frame rate
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if not draw_radar:
                        draw_radar = True
                    else:
                        draw_radar = False
                if event.key == pygame.K_r:
                    if not draw_lines:
                        draw_lines = True
                    else:
                        draw_lines = False
                if event.key == pygame.K_t:
                    if not draw_anything:
                        draw_anything = True
                    else:
                        draw_anything = False
                    
                
        remain_cars = 0
        for x, car in enumerate(cars):#the main fitness loop
            output = nets[x].activate((car.get_AI_data()))
            if output[1] > 0.5 and not car.current_speed <= car.minimal_speed:
                car.angle += 7
            if output[0] > 0.5 and not car.current_speed <= car.minimal_speed:
                car.angle -= 7
            if output[2] >= 0.5:
                car.current_speed += car.speed
            elif output[2] <= 0.5 and car.current_speed > 0:
                car.current_speed -= car.speed
            if car.current_speed < 0:
                car.current_speed = 0
            if car.current_speed > car.terminal_vel:
                car.current_speed = car.terminal_vel
            if car.alive:
                remain_cars += 1
                car.update(CURRENT_MAP_INFO[0], CURRENT_MAP_INFO[2], how_long_before_killed)
                if car.current_speed != car.minimal_speed:
                    ge[x].fitness += car.get_reward()#if they are alive this frame they'll get a fitnesss reward
        
        
        if remain_cars == 0:#when Run = false a new generation is 'born'
            how_long_before_killed += 0
            gen += 1

            run = False

        draw_window(screen, cars, draw_radar, draw_lines, CURRENT_MAP_INFO[1], CURRENT_MAP_INFO[2])
        pygame.display.update()

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    
    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)#give us the output of the experiment

    p.run(main, 1000)

    
if __name__ == '__main__':#find the path of the config file
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
