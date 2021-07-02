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


class BlockBox(CollisionBox):
    def __init__(self, rect, margin):
        self.inside_rect = rect.copy()
        self.margin = margin
        self.top_bottom_rect = pygame.Rect(self.inside_rect.x, self.inside_rect.y - self.margin, self.inside_rect.width,
                                           self.inside_rect.height + self.margin * 2)

        self.left_right_rect = pygame.Rect(self.inside_rect.x - self.margin, self.inside_rect.y,
                                           self.inside_rect.width + self.margin * 2, self.inside_rect.height)

    def get_collision(self, x, y):
        if self.top_bottom_rect.collidepoint(x, y):
            return BlockBox.TOP | BlockBox.BOTTOM
        if self.left_right_rect.collidepoint(x, y):
            return BlockBox.LEFT | BlockBox.RIGHT
        if self.point_in_circle(x, y, self.inside_rect.x, self.inside_rect.y, self.margin):
            return BlockBox.TOP | BlockBox.LEFT
        if self.point_in_circle(x, y, self.inside_rect.x + self.inside_rect.width, self.inside_rect.y, self.margin):
            return BlockBox.TOP | BlockBox.RIGHT
        if self.point_in_circle(x, y, self.inside_rect.x, self.inside_rect.y + self.inside_rect.height, self.margin):
            return BlockBox.LEFT | BlockBox.BOTTOM
        if self.point_in_circle(x, y, self.inside_rect.x + self.inside_rect.width,
                                self.inside_rect.y + self.inside_rect.height, self.margin):
            return BlockBox.RIGHT | BlockBox.BOTTOM
        return BlockBox.NONE

    def point_in_circle(self, x, y, cx, cy, r):
        dx = cx - x
        dy = cy - y
        return dx * dx + dy * dy <= r * r

class Canvas:
    def __init__(self, x, y, radius):
        self.bg = pygame.image.load("assets/breakoutbg.png")
        self.header = pygame.image.load("assets/header.png")
        self.rightbg = pygame.image.load("assets/rightbg.png")
        self.leftbg = pygame.image.load("assets/leftbg.png")
        self.border_width = self.rightbg.get_width()
        self.header_height = 0 #self.header.get_height()
        self.width = self.bg.get_width()
        self.height = self.bg.get_height()
        self.ball_box_rect = pygame.Rect(x + self.border_width, y + self.header_height, self.width, self.height)
        self.ball_box = BallBox(self.ball_box_rect, radius)
        self.offset_x = x + self.border_width
        self.offset_y = y + self.header_height
        self.radius = radius


    def draw(self, surface):
        # surface.blit(self.rightbg, (window_width - self.border_width, 0))
        surface.blit(self.bg, (self.offset_x, self.header_height)) #self.border_width
        surface.blit(self.rightbg, (window_width - self.border_width, 0))
        surface.blit(self.leftbg, (self.offset_x - self.border_width, 0))
        #pygame.draw.rect(surface, pygame.Color(0, 100, 0), self.ball_box_rect)
        #for debugging to show ball box dimensions

    def update(self):
        pass

class Level:
    def __init__(self, canvas):
        self.canvas = canvas
        self.game_levels = build_game_levels()
        self.level = self.game_levels[0]
        import pprint
        blocks = self.level['blocks']
        height = self.level['height']
        width = self.level['width']
        self.name = self.level['name']
        self.score = 0
        self.lives = 3



        print(canvas.radius)
        self.block_width = (self.canvas.width - 300) / width
        self.block_height = int(self.block_width / 2.5)
        self.materials = {}
        self.materials['A'] = [self.load_scaled("A1")]
        self.materials['B'] = [self.load_scaled("B1")]
        self.materials['C'] = [self.load_scaled("C1")]
        self.materials['D'] = [self.load_scaled("D1")]
        self.materials['E'] = [self.load_scaled("E1")]
        self.materials['F'] = [self.load_scaled("F1")]
        self.materials['S'] = [self.load_scaled("S1"), self.load_scaled("S2"), self.load_scaled("S3")]
        for block in blocks:
            bx = block['bx']
            by = block['by']
            block['rect'] = pygame.Rect(bx * self.block_width + self.canvas.offset_x + 150,
                                        by * self.block_height + self.canvas.offset_y + 20, self.block_width, self.block_height)
            block['box'] = BlockBox(block['rect'], canvas.radius)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.level)
        self.font = pygame.font.SysFont('Comic Sans MS', 25)

    def load_scaled(self, name):
        return pygame.transform.smoothscale(pygame.image.load("assets/" + name + ".png"), (self.block_width, self.block_height))


    def draw(self, surface):
        textsurface = self.font.render('Score: %06d' % self.score, False, (255, 255, 255))
        surface.blit(textsurface, (20, 30))
        textsurface = self.font.render('Lives: %d' % self.lives, False, (255, 255, 255))
        surface.blit(textsurface, (20, 60))
        textsurface = self.font.render(self.name, False, (255, 255, 255))
        surface.blit(textsurface, (20, 0))
        blocks = self.level['blocks']
        for block in blocks:
            if block['hits'] != 0:
                #pygame.draw.rect(surface, pygame.Color(0, 0, 120), block['rect'])
                material_name = block['material']
                material = self.materials[material_name]
                index = block['hits'] - 1
                image = material[index]
                r = block['rect']
                surface.blit(image, (r.x, r.y))



    def update(self):
        pass

    def is_colliding_with_block(self, x, y, nx, ny, r):
        blocks = self.level['blocks']
        for block in blocks:
            if block['box'].get_collision(nx, ny) != BallBox.NONE:
                if block['hits'] > 0:
                    return block
        return None


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
    def __init__(self, canvas, level, color, x, y, radius, speed, heading, visible):
        self.color = color
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.heading = heading
        self.visible = visible
        self.canvas = canvas
        self.level = level
        self.motion_enabled = False
        self.dx, self.dy = canvas.ball_box.direction_to_vector(heading, speed)
        self.colliding_with_block = False

    def draw(self, surface):
        if self.visible:
            if self.colliding_with_block:
                pygame.draw.circle(surface, pygame.Color(255, 0, 0), (self.x, self.y), self.radius)
            else:
                pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)

    def update(self):
        if self.motion_enabled:
            x = self.x + self.dx
            y = self.y + self.dy
        else:
            x = self.x
            y = self.y
        result = self.canvas.ball_box.get_collision(x, y)
        if result == BallBox.NONE:
            result_block = self.level.is_colliding_with_block(self.x, self.y, x, y, self.radius)
            if result_block:
                self.colliding_with_block = True
                if result_block['hits'] > 0:
                    result_block['hits'] -= 1
            else:
                self.colliding_with_block = False

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
        self.y = canvas.height - 60
        self.canvas = canvas
        self.paddle_img = pygame.image.load("assets/Paddle.png")

    def draw(self, surface):
        #pygame.draw.rect(surface, pygame.Color(0, 255, 0), self.canvas.ball_box.inside_rect)
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
            if isinstance(o, Ball):
                o.x, o.y = pygame.mouse.get_pos()
            if isinstance(o, Level):
                o.score += 10


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
side_panel_width = 250
radius = 10
pygame.font.init()
canvas = Canvas(side_panel_width, 0, radius)
world.objects.append(canvas)
playerPaddle = Paddle(canvas)
world.objects.append(playerPaddle)
level = Level(canvas)
world.objects.append(level)
for b in range(0, 1):
    # ball = Ball(white, random.randint(0, 1000), random.randint(0, 1000), 10, 2, 2, True)
    ball = Ball(canvas, level, white, 200, 300, radius, 5, math.pi * 2 * random.random(), True)
    world.objects.append(ball)
# for x in range(0, 300, 50):
#     for y in range(0, 200, 20):
#         block = Block(red, x, y, 48, 18, True)
#         world.objects.append(block)

# for i in range(0, 1):
#     line = AnimatedLine()
#     world.objects.append(line)


window_width = side_panel_width + canvas.width + canvas.border_width * 2
window_height = canvas.height + canvas.header_height
game_window = initialize(window_width, window_height, "breakout")
run(game_window)
