import pygame
from pygame.locals import *
import random
import sys

SCREEN_MENU = "menu"
SCREEN_GAME = "game"
SCREEN_SETTINGS = "settings"
SCREEN_SKINS = "skins"

current_screen = SCREEN_MENU
flying = False
pygame.init()

clock = pygame.time.Clock()
fps = 120
slow_fps = 25
screen_width = 864
screen_height = 936
death_timer = 0
death_duration = 20
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Flappy Bird")
music_volume = 0.5
sfx_volume = 0.5
font = pygame.font.Font("resources/font/flappy-font.ttf", 70)

font2 = pygame.font.Font("resources/font/flappy-font.ttf", 40)

white = (255, 255, 255)

ground_scroll = 0
flying = False
Game_over = False
pipe_gap = 250
pipe_frequency = 1500  # pipe per milliseconds
last_pipe = pygame.time.get_ticks() - pipe_frequency
score = 0
pass_pipe = False
scroll_speed = 9
ready_done = False


pygame.mixer.init()
# Game Assets
point_sound = pygame.mixer.Sound("resources/bgm/poing.mp3")
hit_sound = pygame.mixer.Sound("resources/bgm/hit.mp3")
jump_sound = pygame.mixer.Sound("resources/bgm/bark.mp3")
ready = pygame.mixer.Sound("resources/bgm/Ready.mp3")
sett = pygame.mixer.Sound("resources/bgm/Set.mp3")
goo = pygame.mixer.Sound("resources/bgm/Go.mp3")
pygame.mixer.music.load("resources/bgm/back.mp3")
pygame.mixer.music.set_volume(music_volume)
pygame.mixer.music.play(-1)

ready.set_volume(0.5)
sett.set_volume(0.5)
goo.set_volume(0.5)


jump_sound.set_volume(0.5)

bg1 = pygame.image.load("resources/summer.png").convert()
bg2 = pygame.image.load("resources/Background/aa.png").convert()
bg3 = pygame.image.load("resources/Background/night.png").convert()
ground = pygame.image.load("resources/ground.png")
button_img = pygame.image.load("resources/restart.png")
menu_img = pygame.image.load("resources/menus.png")
menu_img = pygame.transform.scale(menu_img, (130, 50))
highscore = pygame.image.load("resources/highscore.png")
highscore = pygame.transform.scale(highscore, (600, 400))
gameover_text = pygame.image.load("skins/gameovr.png")
gameover_text = pygame.transform.scale(gameover_text, (400, 150))
getready = pygame.image.load("resources/getready.png")
set = pygame.image.load("resources/set.png")
go = pygame.image.load("resources/go.png")


SEQ_WIDTH = 400
SEQ_HEIGHT = 200

ready_img = pygame.transform.scale(getready, (600, SEQ_HEIGHT))
set_img = pygame.transform.scale(set, (SEQ_WIDTH, SEQ_HEIGHT))
go_img = pygame.transform.scale(go, (300, SEQ_HEIGHT))

backgrounds = [bg1, bg2, bg3]

current_bg = 0
next_bg = 0
bg_transition = False
bg_alpha = 0
TRANSITION_SPEED = 8


def draw_fade_center(image, alpha):
    img = image.copy()
    img.set_alpha(alpha)
    rect = img.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
    screen.blit(img, rect)


def show_ready_sequence():
    global ready_done

    sequence = [
        (ready_img, ready, 700),
        (set_img, sett, 700),
        (go_img, goo, 500),
    ]

    for img, sound, duration in sequence:
        sound.play()
        start = pygame.time.get_ticks()

        while True:
            now = pygame.time.get_ticks()
            elapsed = now - start

            if elapsed >= duration:
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            draw_background()
            pipe_group.draw(screen)
            bird_group.draw(screen)
            screen.blit(ground, (ground_scroll, 768))

            #  FADE IN → HOLD → FADE OUT
            if elapsed < 200:
                alpha = int((elapsed / 200) * 255)
            elif elapsed > duration - 200:
                alpha = int(((duration - elapsed) / 200) * 255)
            else:
                alpha = 255

            draw_fade_center(img, alpha)

            pygame.display.update()
            clock.tick(60)

    ready_done = True


def draw_center(image):
    rect = image.get_rect(center=(screen_width // 2, screen_height // 2 - 100))
    screen.blit(image, rect)


def draw_background():
    global bg_alpha, bg_transition, current_bg, fade_bg_surface
    # Draw current background
    screen.blit(backgrounds[current_bg], (0, 0))
    if bg_transition:
        if fade_bg_surface is None:
            fade_bg_surface = backgrounds[next_bg].copy()
        fade_bg_surface.set_alpha(bg_alpha)
        screen.blit(fade_bg_surface, (0, 0))
        bg_alpha += TRANSITION_SPEED
        if bg_alpha >= 255:
            bg_alpha = 255
            current_bg = next_bg
            bg_transition = False
            fade_bg_surface = None


# Draw current background
screen.blit(backgrounds[current_bg], (0, 0))

# Fade transition
if bg_transition:
    fade_bg_surface = backgrounds[next_bg].copy()
    fade_bg_surface.set_alpha(bg_alpha)
    screen.blit(fade_bg_surface, (0, 0))
    bg_alpha += TRANSITION_SPEED
    if bg_alpha >= 255:
        bg_alpha = 255
        current_bg = next_bg
        bg_transition = False


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def reset_game():
    pipe_group.empty()
    bird = bird_group.sprites()[0]
    bird.rect.x = 100
    bird.rect.y = int(screen_height / 2)
    bird.vel = 0
    return 0


class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.images = []
        self.index = 0
        self.counter = 0
        for num in range(1, 4):
            img = pygame.image.load(f"skins/nyan{num}.png").convert_alpha()
            img = pygame.transform.scale(img, (72, 50))
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect(center=(x, y))
        self.vel = 0
        self.clicked = False

    def update(self):
        # Gravity
        if flying:
            self.vel += 0.5
            if self.vel > 8:
                self.vel = 8
            if self.rect.bottom < 768:
                self.rect.y += int(self.vel)
        keys = pygame.key.get_pressed()
        if not Game_over:
            # Jump
            if (pygame.mouse.get_pressed()[0]) and not self.clicked:
                self.clicked = True
                self.vel = -10
                jump_sound.play()
            if not pygame.mouse.get_pressed()[0]:
                self.clicked = False
            # Animation
            self.counter += 1
            flap_cooldown = 4
            if self.counter > flap_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images):
                    self.index = 0
            # Rotate while flying
            self.image = pygame.transform.rotate(self.images[self.index], self.vel * -2)
        else:
            # Rotate down ONLY when game over
            self.image = pygame.transform.rotate(self.images[self.index], -90)


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        super().__init__()
        self.pipe_gap = pipe_gap
        self.image_orig = pygame.image.load("resources/towers.png").convert_alpha()
        self.image_top = pygame.transform.flip(self.image_orig, False, True)
        self.image_bottom = self.image_orig
        if position == 1:  # top pipe
            self.image = self.image_top
            self.rect = self.image.get_rect(midbottom=(x, y - self.pipe_gap // 2))
        else:  # bottom pipe
            self.image = self.image_bottom
            self.rect = self.image.get_rect(midtop=(x, y + self.pipe_gap // 2))

    def update(self, scroll_speed):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()

    def draw(self, screen):
        screen.blit(self.image_top, self.rect_top)
        screen.blit(self.image_bottom, self.rect_bottom)


class Button:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True
        screen.blit(self.image, (self.rect.x, self.rect.y))
        return action


bird_group = pygame.sprite.Group()
pipe_group = pygame.sprite.Group()
flappy = Bird(100, int(screen_height / 2))
bird_group.add(flappy)

button = Button(screen_width // 1 - 330, screen_height // 1 - 250, button_img)
main_menu = Button(screen_width // 2 - 230, screen_height // 1 - 250, menu_img)
gameover = Button(screen_width // 2 - 205, screen_height // 2 - 350, gameover_text)
gameover_ui = Button(screen_width // 2 - 305, screen_height // 2 - 200, highscore)

run = True


# Stroke function for score
def draw_text(text, font, color, x, y, stroke_color=(0, 0, 0), stroke_width=5):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(x, y))
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                outline = font.render(text, True, stroke_color)
                screen.blit(outline, rect.move(dx, dy))
    screen.blit(text_surface, rect)


class Slider:
    def __init__(self, x, y, width, min_val, max_val, value):
        self.rect = pygame.Rect(x, y, width, 6)
        self.knob_radius = 10
        self.min = min_val
        self.max = max_val
        self.value = value
        self.dragging = False
        self.knob_x = x + int((value - min_val) / (max_val - min_val) * width)

    def draw(self):
        pygame.draw.rect(screen, (200, 200, 200), self.rect)
        pygame.draw.circle(
            screen,
            (255, 255, 255),
            (self.knob_x, self.rect.centery),
            self.knob_radius,
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if abs(event.pos[0] - self.knob_x) <= self.knob_radius + 5:
                self.dragging = True

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.knob_x = max(self.rect.left, min(event.pos[0], self.rect.right))
            percent = (self.knob_x - self.rect.left) / self.rect.width
            self.value = self.min + percent * (self.max - self.min)


music_slider = Slider(screen_width // 2 - 150, 300, 300, 0.0, 1.0, music_volume)
sfx_slider = Slider(screen_width // 2 - 150, 380, 300, 0.0, 1.0, sfx_volume)


# SETTINGS FUNCTION
def settings_screen():
    global current_screen, music_volume, sfx_volume

    while current_screen == SCREEN_SETTINGS:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            music_slider.handle_event(event)
            sfx_slider.handle_event(event)

        # APPLY VOLUME LIVE
        music_volume = music_slider.value
        sfx_volume = sfx_slider.value
        pygame.mixer.music.set_volume(music_volume)
        jump_sound.set_volume(sfx_volume)
        hit_sound.set_volume(sfx_volume)
        point_sound.set_volume(sfx_volume)
        ready.set_volume(sfx_volume)
        sett.set_volume(sfx_volume)
        goo.set_volume(sfx_volume)

        # DRAW
        draw_background()
        screen.blit(menu_overlay, (0, 0))
        draw_text("SETTINGS", font, white, screen_width // 2, 120)

        draw_text("Music Volume", font2, white, screen_width // 2, 260)
        music_slider.draw()
        draw_text("SFX Volume", font2, white, screen_width // 2, 340)
        sfx_slider.draw()
        draw_text(
            f"{int(music_volume*100)}%", font2, white, screen_width // 2 + 200, 260
        )
        draw_text(f"{int(sfx_volume*100)}%", font2, white, screen_width // 2 + 200, 340)
        if back_button.draw():
            current_screen = SCREEN_MENU
            return

        pygame.display.update()
        clock.tick(60)


# SKINS FUNCTION
def skins_screen():
    global current_screen

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        draw_background()
        screen.blit(menu_overlay, (0, 0))

        draw_text("SKINS", font, white, screen_width // 2, 120)

        # EXAMPLE SKIN BUTTONS
        skin1 = pygame.image.load("skins/nyan1.png").convert_alpha()
        skin1 = pygame.transform.scale(skin1, (80, 60))
        screen.blit(skin1, (screen_width // 2 - 120, 300))

        skin2 = pygame.image.load("skins/nyan2.png").convert_alpha()
        skin2 = pygame.transform.scale(skin2, (80, 60))
        screen.blit(skin2, (screen_width // 2 + 40, 300))

        if back_button.draw():
            current_screen = SCREEN_MENU
            return

        pygame.display.update()
        clock.tick(60)


# Buttons Image
start_button_img = pygame.image.load("resources/Game Buttons/playy.png").convert_alpha()
settings_button_img = pygame.image.load(
    "resources/Game Buttons/settings.png"
).convert_alpha()
flappy_img = pygame.image.load("resources/flappy text.png").convert_alpha()
quit_button_img = pygame.image.load("resources/Game Buttons/quit.png").convert_alpha()
skins_ui = pygame.image.load("resources/skins.png").convert_alpha()
back_img = pygame.image.load("resources/back.png").convert_alpha()
# SCALING BUTTONS
back_img = pygame.transform.scale(back_img, (90, 80))
back_button = Button(40, 40, back_img)
start_button_img = pygame.transform.scale(start_button_img, (250, 90))
quit_button_img = pygame.transform.scale(quit_button_img, (180, 90))
settings_button_img = pygame.transform.scale(settings_button_img, (180, 90))
skins_ui = pygame.transform.scale(skins_ui, (300, 90))
flappy_img = pygame.transform.scale(flappy_img, (600, 200))

# BUTTON POSITIONS
start_button = Button(
    screen_width // 2 - 145, screen_height // 2 + 150, start_button_img
)
skins_ui = Button(screen_width // 1 - 605, screen_height // 2 + 50, skins_ui)
quit_button = Button(screen_width // 1 - 280, screen_height // 2 + 150, quit_button_img)
settings_button = Button(
    screen_width // 2 - 380, screen_height // 2 + 150, settings_button_img
)
flappy_text = Button(screen_width // 2 - 300, screen_height // 1 + -800, flappy_img)

menu_overlay = pygame.Surface((screen_width, screen_height))
menu_overlay.set_alpha(50)
menu_overlay.fill((0, 0, 0))

start_clicked = False


# --- MENU LOOP ---
while current_screen == SCREEN_MENU:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- GAME UPDATES IN BACKGROUND ---
    bird_group.update()
    if not Game_over:
        pipe_group.update(scroll_speed)
        time_now = pygame.time.get_ticks()
        if time_now - last_pipe > pipe_frequency:
            pipe_height = random.randint(-120, 120)
            pipe_group.add(Pipe(screen_width, screen_height // 2 + pipe_height, -1))
            pipe_group.add(Pipe(screen_width, screen_height // 2 + pipe_height, 1))
            last_pipe = time_now
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0
            jump_sound.stop()

    # --- DRAW GAME IN BACKGROUND ---
    draw_background()
    pipe_group.draw(screen)
    bird_group.draw(screen)
    screen.blit(ground, (ground_scroll, 768))

    # --- DRAW MENU OVERLAY ---
    screen.blit(menu_overlay, (0, 0))
    start_button.draw()
    quit_button.draw()
    settings_button.draw()
    flappy_text.draw()
    skins_ui.draw()

    # --- BUTTON LOGIC ---
    if start_button.draw():
        current_screen = SCREEN_GAME
        score = reset_game()
        flying = True
        break

    if settings_button.draw():
        current_screen = SCREEN_SETTINGS
        settings_screen()

    if skins_ui.draw():
        current_screen = SCREEN_SKINS
        skins_screen()

    if quit_button.draw():
        pygame.quit()
        sys.exit()

    # --- CHECK IF START CLICKED (only once) ---
    if not start_clicked and start_button.draw():
        start_clicked = True  # prevent repeating fade

        # --- FADE OUT ---
        fade_bg_surface = pygame.Surface((screen_width, screen_height))
        fade_bg_surface.fill((0, 0, 0))

        for alpha in range(0, 200, 5):
            fade_bg_surface.set_alpha(alpha)

            # Draw current game background under fade
            draw_background()
            pipe_group.draw(screen)
            bird_group.draw(screen)
            screen.blit(ground, (ground_scroll, 768))

            # Draw fade overlay
            screen.blit(fade_bg_surface, (0, 0))
            pygame.display.update()
            pygame.time.delay(10)  # small delay for smooth fade

        # --- RESET GAME TO FIRST PIPE ---
        score = reset_game()
        flying = True
        menu = False  # exit menu loop

    pygame.display.update()
    clock.tick(fps)

# --- GAME MUSIC AFTER MENU ---
pygame.mixer.music.load("resources/bgm/nyan.mp3")
pygame.mixer.music.set_volume(music_volume)
pygame.mixer.music.play(-1)


# --- MAIN GAME LOOP ---
run = True
while current_screen == SCREEN_GAME:

    # --- EVENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # --- COLLISIONS & DEATH ---
    bird = bird_group.sprites()[0]  # get the bird
    hit_pipe = pygame.sprite.groupcollide(bird_group, pipe_group, False, False)
    hit_ground = bird.rect.bottom >= 768

    if not Game_over and (hit_pipe or hit_ground):
        Game_over = True
        death_timer = death_duration
        hit_sound.play()

    # --- FPS CONTROL (slow motion on death) ---
    if death_timer > 0:
        clock.tick(slow_fps)
        death_timer -= 1
    else:
        clock.tick(fps)

    # --- UPDATE SPRITES ---
    bird_group.update()
    if not Game_over:
        pipe_group.update(scroll_speed)

        # Generate pipes if flying
        time_now = pygame.time.get_ticks()
        if time_now - last_pipe > pipe_frequency and flying:
            pipe_height = random.randint(-120, 120)
            pipe_group.add(Pipe(screen_width, screen_height // 2 + pipe_height, -1))
            pipe_group.add(Pipe(screen_width, screen_height // 2 + pipe_height, 1))
            last_pipe = time_now

        # Scroll ground
        ground_scroll -= scroll_speed
        if abs(ground_scroll) > 35:
            ground_scroll = 0

    # --- DRAW EVERYTHING ---
    draw_background()
    pipe_group.draw(screen)
    bird_group.draw(screen)
    screen.blit(ground, (ground_scroll, 768))
    draw_text(str(score), font, white, screen_width // 2, 50)

    if not ready_done:
        score = reset_game()
        flying = False
        show_ready_sequence()
        ready_done = True
        flying = True
        menu = False

    # --- SCORING ---
    if len(pipe_group) > 0:
        pipe = pipe_group.sprites()[0]
        if (
            bird.rect.left > pipe.rect.left
            and bird.rect.right < pipe.rect.right
            and not pass_pipe
        ):
            pass_pipe = True
        if pass_pipe and bird.rect.left > pipe.rect.right:
            score += 1
            pass_pipe = False
            point_sound.play()

    # --- BACKGROUND TRANSITIONS ---
    if score == 25 and current_bg == 0:
        next_bg = 1
        bg_transition = True
        bg_alpha = 0
    if score == 50 and current_bg == 1:
        next_bg = 2
        bg_transition = True
        bg_alpha = 0

    # --- GAME OVER BUTTON ---
    if Game_over:
        gameover.draw()
        gameover_ui.draw()
        main_menu.draw()
        if button.draw():
            # Reset everything

            Game_over = False
            flying = True
            score = reset_game()
            menu = False
            show_ready_sequence()
            current_bg = 0
            next_bg = 0
            bg_transition = False
            bg_alpha = 0
            fade_bg_surface = None

    # UPDATE DISPLAY
    pygame.display.update()
