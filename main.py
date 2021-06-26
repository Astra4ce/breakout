# coding=utf-8
"""
Breakout Game
Made with PyGame
"""

import pygame, sys, time, random, math


def build_game_levels():
    game_levels = []
    level_file = open('assets/levels.txt', 'r')
    lines = level_file.readlines()
    by = -1
    blocks = []
    levelwidth = 0
    for line in lines:
        line = line.strip()
        if not line.startswith('#'):
            if line.startswith('name:'):
                assert by >= 0
                level = {}
                level['name'] = line[5:]
                level['blocks'] = blocks
                level['height'] = by
                level['width'] = levelwidth
                game_levels.append(level)
                blocks = []
                by = -1
            else:
                blockmap = line.split(' ')
                levelwidth = len(blockmap)
                by += 1
                for bx in range(0, len(blockmap)):
                    block = blockmap[bx]
                    if not block.startswith('.'):
                        blockinfo = {}
                        blockinfo['bx'] = bx
                        blockinfo['by'] = by
                        blockinfo['material'] = block[0]
                        blockinfo['reward'] = block[1]
                        blockinfo['hits'] = 3 if block[0] == 'S' else 1
                        blocks.append(blockinfo)
    return game_levels



# Colors (R, G, B)
black = pygame.Color(0, 0, 0)
white = pygame.Color(255, 255, 255)
red = pygame.Color(255, 0, 0)
green = pygame.Color(0, 255, 0)
blue = pygame.Color(0, 0, 255)

class CollisionBox:
    NONE = 0
    RIGHT = 1
    LEFT = 2
    TOP = 4
    BOTTOM = 8
    INVALID = 15

    def get_collision(self, x, y):
        return CollisionBox.INVALID

class BallBox(CollisionBox):

    def __init__(self, rect, margin):
        self.outside_rect = rect.copy()
        self.inside_rect = self.outside_rect.inflate(-margin * 2, -margin * 2)
        self.margin = margin

    def get_collision(self, x, y):
        if self.inside_rect.collidepoint(x, y):
            return BallBox.NONE

        result = BallBox.NONE
        if x < self.inside_rect.x:
            result |= BallBox.LEFT
        elif x >= self.inside_rect.right:
            result |= BallBox.RIGHT

        if y < self.inside_rect.y:
            result |= BallBox.TOP
        elif y >= self.inside_rect.bottom:
            result |= BallBox.BOTTOM

        if result == BallBox.NONE:
            return BallBox.INVALID

        return result

    def direction_to_vector(self, angle, length):
        dx = length * math.sin(angle)
        dy = length * math.cos(angle)
        return dx, dy

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
        r = pygame.Rect(x + offset_x, y + offset_y, width, height)
        self.ball_box = BallBox(r, radius)
        self.offset_x = offset_x
        self.offset_y = offset_y




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
        self.dx, self.dy = canvas.ball_box.direction_to_vector(heading, speed)





    def draw(self, surface):
        if self.visible:
            pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)

    def update(self):
        x = self.x + self.dx
        y = self.y + self.dy
        result = self.canvas.ball_box.get_collision(x, y)
        if result == BallBox.NONE:
            self.x, self.y = x, y
            return
        if result & (BallBox.LEFT | BallBox.RIGHT):
            self.dx = -self.dx
        if result & (BallBox.TOP | BallBox.BOTTOM):
            self.dy = -self.dy
        self.heading = math.asin(self.dy / self.speed)

class Paddle:
    # represents the paddle
    def __init__(self, canvas):
        self.x = canvas.width / 2
        self.y = canvas.height - 100
        self.canvas = canvas
        self.paddle_img = pygame.image.load("assets/Paddle.png")

    def draw(self, surface):
        pygame.draw.rect(surface, pygame.Color(0, 255, 0), self.canvas.ball_box.inside_rect)
        x = self.x - (self.paddle_img.get_width() / 2) + self.canvas.offset_x
        y = self.y - (self.paddle_img.get_height() / 2) + self.canvas.offset_y
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
        # if event.key == pygame.K_LEFT or event.key == ord('a'):
        # playerPaddle.changePosition(-10)
        # if event.key == pygame.K_RIGHT or event.key == ord('d'):
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
for b in range(0, 250):
    # ball = Ball(white, random.randint(0, 1000), random.randint(0, 1000), 10, 2, 2, True)
    ball = Ball(canvas, white, 200, 300, 10, 5, math.pi * 2 * random.random(), True)
    world.objects.append(ball)
for x in range(0, 300, 50):
    for y in range(0, 200, 20):
        block = Block(red, x, y, 48, 18, True)
        world.objects.append(block)

# for i in range(0, 1):
#     line = AnimatedLine()
#     world.objects.append(line)




game_levels = build_game_levels()
import pprint
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(game_levels)

window_width = canvas.width + background.border_width * 2
window_height = canvas.height + background.header_height
game_window = initialize(window_width, window_height, "breakout")
run(game_window)

