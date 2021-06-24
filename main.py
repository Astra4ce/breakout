# coding=utf-8
"""
Breakout Game
Made with PyGame
"""

import pygame, sys, time, random, math

#with open('levels.txt') as f:
  #  levels = f.readlines()

# Colors (R, G, B)
black = pygame.Color(0, 0, 0)
white = pygame.Color(255, 255, 255)
red = pygame.Color(255, 0, 0)
green = pygame.Color(0, 255, 0)
blue = pygame.Color(0, 0, 255)



class Background:
    def __init__(self):
        self.bg = pygame.image.load("assets/breakoutbg.png")
        self.header = pygame.image.load("assets/header.png")
        self.rightbg = pygame.image.load("assets/rightbg.png")
        self.leftbg = pygame.image.load("assets/leftbg.png")
        self.border_width = self.rightbg.get_width()
        self.header_height = self.header.get_height()
        self.bg_width = self.bg.get_width()
        self.bg_height = self.bg.get_height()


    def draw(self, surface):
        surface.blit(self.rightbg, (canvas.width + self.border_width, 0))
        surface.blit(self.bg, (self.border_width, self.header_height))
        surface.blit(self.header, (self.border_width, 0))
        surface.blit(self.leftbg, (0, 0))

    def update(self):
        pass


class Canvas:
    def __init__(self, x, y, width, height, radius, offset_x, offset_y):
        self.width = width
        self.height = height
        self.left = pygame.Rect(x - 100, y, 100 + radius, height)
        self.right = pygame.Rect(x + width - radius, y, 100, height)
        self.top = pygame.Rect(x, y - 100, width, 100 + radius)
        self.bottom = pygame.Rect(x, y + height - radius, width, 100)
        self.offset_x = offset_x
        self.offset_y = offset_y

    def wall_collision(self, ball):
        result = 0
        if self.left.collidepoint(ball.x, ball.y):
            result += 8
        if self.top.collidepoint(ball.x, ball.y):
            result += 4
        if self.right.collidepoint(ball.x, ball.y):
            result += 2
        if self.bottom.collidepoint(ball.x, ball.y):
            result += 1
        return result

class World:
    def __init__(self):
        self.objects = []

    def draw(self, surface):
        for o in self.objects:
            o.draw(surface)

    def update(self):
        for o in self.objects:
            o.update()

class AnimatedLine:
    def __init__(self):
        self.x = random.randint(0, 300)
        self.y = random.randint(0, 300)
        self.x2 = random.randint(0, 300)
        self.y2 = random.randint(0, 300)
        self.angle = 0

    def update(self):
        self.x += 5 * math.sin(self.angle)
        self.x += 5 * math.cos(self.angle)
        self.x2 += 10 * math.sin(self.angle)
        self.x2 += 10 * math.cos(self.angle)
        self.angle += 0.1

    def draw(self, surface):
        pygame.draw.line(surface, white, (self.x, self.y), (self.x2, self.y2))

class Block:
    def __init__(self, color, x, y, width, height, visible):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = visible

    def draw(self, surface):
        if self.visible:
            pygame.draw.rect(surface, self.color, [self.x, self.y, self.width, self.height])

    def update(self):
        pass

class Ball:
    def __init__(self, canvas, color, x, y, radius, speed, heading, visible):
        self.color = color
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.heading = heading
        self.visible = visible
        self.canvas = canvas

    def draw(self, surface):
        if self.visible:
            pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)

    def update(self):
        self.x = self.x + (self.speed * math.cos(self.heading))
        self.y = self.y - (self.speed * math.sin(self.heading))
        result = self.canvas.wall_collision(self)
        if result == 0:
            return
        if result == 8:
            self.collide_left()
        elif result == 12:
            self.collide_left_top()
        elif result == 4:
            self.collide_top()
        elif result == 6:
            self.collide_top_right()
        elif result == 2:
            self.collide_right()
        elif result == 3:
            self.collide_right_bottom()
        elif result == 1:
            self.collide_bottom()
        elif result == 9:
            self.collide_bottom_left()
        else:
            assert False, "bad result"


    def collide_left(self):
        print("collide_left")
        self.heading += math.pi
    def collide_left_top(self):
        print("collide_left_top")
        self.heading += math.pi
    def collide_top(self):
        print("collide_top")
        self.heading += math.pi
    def collide_top_right(self):
        print("collide_top_right")
        self.heading += math.pi
    def collide_right(self):
        print("collide_right")
        self.heading += math.pi
    def collide_right_bottom(self):
        print("collide_right_bottom")
        self.heading += math.pi
    def collide_bottom(self):
        print("collide_bottom")
        self.heading += math.pi
    def collide_bottom_left(self):
        print("collide_bottom_left")
        self.heading += math.pi




class Paddle:
    #represents the paddle
    def __init__(self, canvas):
        self.x = canvas.width / 2
        self.y = canvas.height - 100
        self.canvas = canvas
        self.paddle_img = pygame.image.load("assets/Paddle.png")

    def draw(self, surface):
        # pygame.draw.rect(surface, self.color,
        #                  [self.x - (self.width/2), self.y - (self.height/2), self.width, self.height])
        x = self.x - (self.paddle_img.get_width()/2) + self.canvas.offset_x
        y = self.y - (self.paddle_img.get_height()/2) + self.canvas.offset_y
        surface.blit(self.paddle_img, (x, y))

    def changePosition(self, dx):
        temp = self.x + dx
        hw = (self.paddle_img.get_width() / 2)
        if temp < hw:
            temp = hw
        elif temp > (canvas.width - hw):
            temp = (canvas.width - hw)
        self.x = temp


    def update(self):
        pass




def initialize(window_width, window_height, window_title):
    # Checks for errors encountered
    check_errors = pygame.init()
    # pygame.init() example output -> (6, 0)
    # second number in tuple gives number of errors
    if check_errors[1] > 0:
        print('[!] Had {check_errors[1]} errors when initialising game, exiting...')
        sys.exit(-1)
    else:
        print('[+] Game successfully initialised')

    # Initialise game window
    pygame.display.set_caption(window_title)
    game_window = pygame.display.set_mode((window_width, window_height))
    return game_window






def process_event(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    # Whenever a key is pressed down
    elif event.type == pygame.KEYDOWN:
        # W -> Up; S -> Down; A -> Left; D -> Right
        # if event.key == pygame.K_UP or event.key == ord('w'):
        # change_to = 'UP'
        # if event.key == pygame.K_DOWN or event.key == ord('s'):
        # change_to = 'DOWN'
        #if event.key == pygame.K_LEFT or event.key == ord('a'):
           # playerPaddle.changePosition(-10)
       #if event.key == pygame.K_RIGHT or event.key == ord('d'):
           # playerPaddle.changePosition(10)
        # Esc -> Create event to quit the game
        if event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
    elif event.type == pygame.MOUSEMOTION:
        for o in world.objects:
            if isinstance(o, AnimatedLine):
                o.x, o.y = pygame.mouse.get_pos()

def process_keyboard_events():
    pressed_keys = pygame.key.get_pressed()
    if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
        playerPaddle.changePosition(-10)
    if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
        playerPaddle.changePosition(10)

def update_world():
    world.update()

def refresh_screen(game_window):
    game_window.fill(black)
    world.draw(game_window)


def run(game_window):
    # FPS (frames per second) controller
    fps_controller = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            process_event(event)
        process_keyboard_events()
        update_world()
        refresh_screen(game_window)
        # Refresh game screen
        pygame.display.update()
        # Refresh rate
        fps_controller.tick(30)

world = World()

background = Background()
canvas = Canvas(0, 0, background.bg_width, background.bg_height, 10, background.border_width, background.header_height)
world.objects.append(background)
playerPaddle = Paddle(canvas)
world.objects.append(playerPaddle)
for b in range(0, 1):
    #ball = Ball(white, random.randint(0, 1000), random.randint(0, 1000), 10, 2, 2, True)
    ball = Ball(canvas, white, 200, 200, 10, 2, 2, True)
    world.objects.append(ball)
for x in range(0, 300, 50):
    for y in range(0, 200, 20):
        block = Block(red, x, y, 48, 18, True)
        world.objects.append(block)

# for i in range(0, 1):
#     line = AnimatedLine()
#     world.objects.append(line)

window_width = canvas.width + background.border_width * 2
window_height = canvas.height + background.header_height
game_window = initialize(window_width, window_height, "breakout")
run(game_window)