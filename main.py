# coding=utf-8
"""
Breakout Game
Made with PyGame
"""

import pygame, sys, time, random, math, pprint


class Game:
    INTRO = 1
    PREGAME = 2
    GAME = 3
    SETTINGS = 4
    PAUSE = 5
    LEVEL_CLEARED = 6
    WIN = 7
    LOSS = 8
    EXIT_PROMPT = 9

    state = PREGAME


# single global game object that represents global game state


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

    def calc_bounce(self, cx, cy, dx, dy):
        # function accepts current location of the ball in cx,cy,
        # proposed coordinate changes as dx, dy. if proposed
        # position is inside the box, the function calculates
        # returns the collision point between the ball and the
        # box. as well as the updated dx, dy to reflect
        # the ball's bounce.
        if dy == 0:
            return self.special_calc_bounce(cx, cy, dx, dy)
        return self.normal_calc_bounce(cx, cy, dx, dy)

    def normal_calc_bounce(self, cx, cy, dx, dy):
        px = cx + dx
        py = cy + dy
        slope = (py - cy) / (px - cx)
        r = self.margin
        Rx1 = self.inside_rect.x - r
        Rx2 = self.inside_rect.x + self.inside_rect.width + r
        Ry1 = self.inside_rect.y - r
        Ry2 = self.inside_rect.y + self.inside_rect.height + r
        top_collision = None
        bottom_collision = None
        left_collision = None
        right_collision = None
        collision_bitmap = 0

        # checking bottom
        # y = Ry + Rh + r
        x = ((Ry2 - cy) / slope) + cx

        if x >= Rx1 and x <= Rx2:
            bottom_collision = (x, Ry2)
            collision_bitmap += 1

        # checking top
        x = ((Ry1 - cy) / slope) + cx
        if x >= Rx1 and x <= Rx2:
            top_collision = (x, Ry1)
            collision_bitmap += 4

        # checking left
        y = ((slope * (Rx1 - cx)) + cy)
        if y >= Ry1 and y <= Ry2:
            left_collision = (Rx1, y)
            collision_bitmap += 8

        # checking right
        y = ((slope * (Rx2 - cx)) + cy)
        if y >= Ry1 and y <= Ry2:
            right_collision = (Rx2, y)
            collision_bitmap += 2

        if collision_bitmap == 3:  # bottom or right
            if dy > 0:
                return right_collision, (-dx, dy)
            return bottom_collision, (dx, -dy)
        elif collision_bitmap == 5:  # top or bottom
            if dy > 0:
                return top_collision, (dx, -dy)
            return bottom_collision, (dx, -dy)
        elif collision_bitmap == 6:  # top or right
            if dy > 0:
                return top_collision, (dx, -dy)
            return right_collision, (-dx, dy)
        elif collision_bitmap == 9:  # bottom or left
            if dy > 0:
                return left_collision, (-dx, dy)
            return bottom_collision, (dx, -dy)
        elif collision_bitmap == 10:  # left or right
            if dx > 0:
                return left_collision, (-dx, dy)
            return right_collision, (-dx, dy)
        elif collision_bitmap == 12:  # top or left
            if dy > 0:
                return top_collision, (dx, -dy)
            return left_collision, (-dx, dy)
        return None

    def special_calc_bounce(self, cx, cy, dx, dy):
        pass


class Canvas:
    def __init__(self, x, y, radius):
        self.bg = pygame.image.load("assets/breakoutbg.png")
        self.header = pygame.image.load("assets/header.png")
        self.rightbg = pygame.image.load("assets/rightbg.png")
        self.leftbg = pygame.image.load("assets/leftbg.png")
        self.border_width = self.rightbg.get_width()
        self.header_height = 0  # self.header.get_height()
        self.width = self.bg.get_width()
        self.height = self.bg.get_height()
        self.ball_box_rect = pygame.Rect(x + self.border_width, y + self.header_height, self.width, self.height)
        self.ball_box = BallBox(self.ball_box_rect, radius)
        self.offset_x = x + self.border_width
        self.offset_y = y + self.header_height
        self.radius = radius

    def draw(self, surface):
        if Game.state in (Game.GAME, Game.PREGAME):
            # surface.blit(self.rightbg, (window_width - self.border_width, 0))
            surface.blit(self.bg, (self.offset_x, self.header_height))  # self.border_width
            surface.blit(self.rightbg, (window_width - self.border_width, 0))
            surface.blit(self.leftbg, (self.offset_x - self.border_width, 0))
            # pygame.draw.rect(surface, pygame.Color(0, 100, 0), self.ball_box_rect)
            # for debugging to show ball box dimensions
        elif Game.state == Game.LEVEL_CLEARED:
            pygame.draw.rect(surface, pygame.Color(0, 0, 0), (0, 0, self.width, self.height))

    def update(self):
        pass


class Level:
    def __init__(self, world, canvas, radius):
        self.world = world
        self.canvas = canvas
        self.game_levels = build_game_levels()
        self.current_level = 0
        self.level_count = len(self.game_levels)
        self.level = None
        self.name = None
        self.score = 0
        self.lives = 3
        self.materials = None
        self.block_width = None
        self.block_height = None
        self.radius = radius
        self.resting_ball = None
        self.active_balls = 0

        print(canvas.radius)

        self.font = pygame.font.SysFont('Comic Sans MS', 25)
        self.new_level(self.current_level)

    def new_level(self, level):
        self.current_level = level
        self.level = self.game_levels[self.current_level]
        blocks = self.level['blocks']
        height = self.level['height']
        width = self.level['width']
        self.name = self.level['name']
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
                                        by * self.block_height + self.canvas.offset_y + 20, self.block_width,
                                        self.block_height)
            block['box'] = BlockBox(block['rect'], canvas.radius)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.level)
        self.active_balls = 0
        self.create_resting_ball()

    def create_resting_ball(self):
        bx = self.canvas.width / 2 + self.canvas.offset_x
        by = self.canvas.height - 60 + self.canvas.offset_y - 25
        self.resting_ball = self.create_ball(bx, by, 0, math.pi * 0.75, True)

    def load_scaled(self, name):
        return pygame.transform.smoothscale(pygame.image.load("assets/" + name + ".png"),
                                            (self.block_width, self.block_height))

    def draw(self, surface):
        if Game.state not in (Game.GAME, Game.PREGAME, Game.PAUSE, Game.EXIT_PROMPT):
            return
        textsurface = self.font.render('Score: %06d' % self.score, False, (255, 255, 255))
        surface.blit(textsurface, (20, 30))
        textsurface = self.font.render('Lives: %d' % self.lives, False, (255, 255, 255))
        surface.blit(textsurface, (20, 60))
        textsurface = self.font.render(self.name, False, (255, 255, 255))
        surface.blit(textsurface, (20, 0))
        blocks = self.level['blocks']
        for block in blocks:
            if block['hits'] != 0:
                # pygame.draw.rect(surface, pygame.Color(0, 0, 120), block['rect'])
                material_name = block['material']
                material = self.materials[material_name]
                index = block['hits'] - 1
                image = material[index]
                r = block['rect']
                surface.blit(image, (r.x, r.y))

    def update(self):
        if Game.state == Game.GAME:
            if self.resting_ball:
                self.resting_ball.set_speed(5)
                self.resting_ball = None

    def is_colliding_with_block(self, x, y, nx, ny, r):
        blocks = self.level['blocks']
        for block in blocks:
            if block['box'].get_collision(nx, ny) != BallBox.NONE:
                if block['hits'] > 0:
                    return block
        return None

    def is_level_cleared(self):
        blocks = self.level['blocks']
        for block in blocks:
            if block['hits'] != 0:
                return False
        return True

    def level_cleared(self):
        if self.current_level == self.level_count - 1:
            Game.state = Game.WIN
        else:
            Game.state = Game.LEVEL_CLEARED
            self.new_level(self.current_level + 1)

    def create_ball(self, x, y, speed, heading, visible):
        self.active_balls += 1
        # math.pi * 2 * random.random()
        ball = Ball(self.canvas, self, white, x, y, self.radius, speed, heading, visible)
        self.world.objects.append(ball)
        return ball

    def delete_ball(self, ball):
        self.world.objects.remove(ball)
        self.active_balls -= 1
        if self.active_balls == 0:
            self.lives -= 1
            if self.lives == 0:
                Game.state = Game.LOSS
            else:
                Game.state = Game.PREGAME
                self.create_resting_ball()


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
        self.motion_enabled = True
        self.dx, self.dy = canvas.ball_box.direction_to_vector(heading, speed)
        self.colliding_with_block = False

    def draw(self, surface):
        if Game.state not in (Game.GAME, Game.PREGAME):
            return
        if self.visible:
            if self.colliding_with_block:
                pygame.draw.circle(surface, pygame.Color(255, 0, 0), (self.x, self.y), self.radius)
            else:
                pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius)

    def update(self):
        if Game.state != Game.GAME:
            return
        if not self.motion_enabled:
            return
        if self.speed == 0:
            return
        x = self.x + self.dx
        y = self.y + self.dy

        self.colliding_with_block = False
        result = self.canvas.ball_box.get_collision(x, y)
        if result == BallBox.NONE:
            result_block = self.level.is_colliding_with_block(self.x, self.y, x, y, self.radius)
            if result_block:
                box = result_block['box']
                bounce_result = box.calc_bounce(self.x, self.y, self.dx, self.dy)
                if bounce_result:
                    np, nd = bounce_result
                    self.x, self.y = np
                    self.dx, self.dy = nd

                    self.colliding_with_block = True
                    if result_block['hits'] > 0:
                        result_block['hits'] -= 1
                        if result_block['hits'] == 0:
                            if self.level.is_level_cleared():
                                level.level_cleared()
            else:
                self.x, self.y = x, y

            return
        if result & BallBox.BOTTOM:
            self.level.delete_ball(self)
            return
        if result & (BallBox.LEFT | BallBox.RIGHT):
            self.dx = -self.dx
        if result & (BallBox.TOP | BallBox.BOTTOM):
            self.dy = -self.dy
        self.heading = math.asin(self.dy / self.speed)

    def move(self, x, y):
        self.x, self.y = x, y

    def set_speed(self, speed):
        self.speed = speed
        self.dx, self.dy = self.canvas.ball_box.direction_to_vector(self.heading, self.speed)


class Paddle:
    # represents the paddle
    def __init__(self, canvas, level):
        self.level = level
        self.x = canvas.width / 2
        self.y = canvas.height - 60
        self.canvas = canvas
        self.paddle_img = pygame.image.load("assets/Paddle.png")

    def draw(self, surface):
        if Game.state not in (Game.GAME, Game.PREGAME, Game.PAUSE):
            return
        # pygame.draw.rect(surface, pygame.Color(0, 255, 0), self.canvas.ball_box.inside_rect)
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
        if self.level.resting_ball:
            self.level.resting_ball.move(self.x + self.canvas.offset_x, self.y + self.canvas.offset_y - 25)

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


def process_keyboard_event(event):
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
    if Game.state == Game.EXIT_PROMPT:
        if event.key == pygame.K_y:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        else:
            Game.state = Game.GAME
    elif Game.state == Game.LEVEL_CLEARED:
        Game.state = Game.PREGAME
    elif Game.state == Game.PREGAME:
        if event.key == pygame.K_SPACE:
            Game.state = Game.GAME


def process_mouse_event(event):
    for o in world.objects:
        if isinstance(o, Ball):
            if not o.motion_enabled:
                o.x, o.y = pygame.mouse.get_pos()
        if isinstance(o, Level):
            o.score += 10


def process_event(event):
    if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()
    # Whenever a key is pressed down
    elif event.type == pygame.KEYDOWN:
        process_keyboard_event(event)
    elif event.type == pygame.MOUSEMOTION:
        process_mouse_event(event)


def process_keyboard_state():
    if Game.state in (Game.GAME, Game.PREGAME):
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
        process_keyboard_state()
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

level = Level(world, canvas, radius)
world.objects.append(level)

playerPaddle = Paddle(canvas, level)
world.objects.append(playerPaddle)

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
