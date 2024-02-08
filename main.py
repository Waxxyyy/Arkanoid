import pygame
import sys
import random
import sqlite3



# Инициализация Pygame
pygame.init()



# Определение констант
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)


# Открывает файл и выполняет SQL-запрос для создания таблицы
with open('create_tables.sql', 'r') as sql_file:
    sql_script = sql_file.read()

# Подключение к базе данных и выполнение запроса
connection = sqlite3.connect('scores.db')
cursor = connection.cursor()
cursor.executescript(sql_script)
connection.commit()
connection.close()


def save_score(player_name, score):
    print(f"Saving score: {player_name} - {score}")
    connection = sqlite3.connect('scores.db')
    cursor = connection.cursor()
    cursor.execute("INSERT INTO scores (player_name, score) VALUES (?, ?)", (player_name, score))
    connection.commit()
    connection.close()


def get_last_scores():
    print("Fetching last scores...")
    connection = sqlite3.connect('scores.db')
    cursor = connection.cursor()
    cursor.execute("SELECT player_name, score, timestamp FROM scores ORDER BY timestamp DESC LIMIT 20")
    scores = cursor.fetchall()
    connection.close()
    print("Fetched scores:", scores)
    return scores


# Определение класса для игрового объекта
class Ball(pygame.sprite.Sprite):
    def __init__(self, platform):
        super().__init__()
        self.images = [pygame.image.load("flushed-ball.png").convert_alpha(),
                       pygame.image.load("ball2.png").convert_alpha(),
                       pygame.image.load("ball3.png").convert_alpha()]
        self.current_image = 0  # Текущее изображение мяча
        self.original_image = pygame.transform.scale(self.images[self.current_image], (30, 30))
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.centerx = platform.rect.centerx
        self.rect.bottom = platform.rect.top
        self.on_platform = True
        self.speed = [0, 0]
        self.platform = platform  # Сохраняем платформу
        self.animation_delay = 0  # Задержка между сменой кадров
        self.animation_speed = 10  # Скорость анимации 

    def update(self):
        if not self.on_platform:
            # Обновление анимации мячика с учетом задержки
            self.animation_delay += 1
            if self.animation_delay >= self.animation_speed:
                self.animation_delay = 0
                self.current_image = (self.current_image + 1) % len(self.images)
                self.image = pygame.transform.scale(self.images[self.current_image], (30, 30))  # Изменяем размер изображения мяча
                self.rect = self.image.get_rect(center=self.rect.center)
        else:
            # Оставляем мячик 20x20 пикселей на платформе
            self.rect.centerx = self.platform.rect.centerx
            self.rect.bottom = self.platform.rect.top


        if self.on_platform:
            self.rect.centerx = self.platform.rect.centerx
        else:
            self.rect.x += self.speed[0]
            self.rect.y += self.speed[1]

            # Логика отскока от стен
            if self.rect.left < 0 or self.rect.right > WIDTH:
                self.speed[0] = -self.speed[0]
            if self.rect.top < 0:  # Проверка столкновения с верхней гранью окна
                self.speed[1] = -self.speed[1]

            # Логика проверки столкновения с блоками
            for block in blocks:
                if pygame.sprite.collide_rect(ball, block):
                    block.kill()  # Удаляем блок из группы блоков
                    ball.speed[1] = -ball.speed[1]
                    global score
                    score += 1

            if len(blocks) == 0:
                self.restart_level()  # Добавляем вызов функции перезапуска уровня

    def restart_level(self):  # Вставляем функцию перезапуска уровня в класс Ball
        global lives, score, in_main_menu
        global blocks  # Глобальная переменная для блоков
        print("Restarting level...")
        lives = 3
        in_main_menu = False

        # Удаление старых блоков и кнопки
        blocks.empty()
        all_sprites.remove(self)

        # Генерация новых блоков
        for row in range(5):
            for col in range(11):
                block = Block(col * 75, row * 30)
                all_sprites.add(block)
                blocks.add(block)

    def catapult(self):
        if self.on_platform:
            self.speed = [random.choice([-5, 5]), -5]
            self.on_platform = False


# Определение класса для платформы
class Platform(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((100, 20))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 30)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= 5
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += 5


# Определение класса для блоков
class Block(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((75, 30))
        self.image.fill((random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


def show_scores():
    scores_menu = ScoresMenu()
    scores_menu.show_scores_menu(scores=[])


# Класс главного меню игры
# Определение класса для главного меню игры
class MainMenu(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.all_sprites = pygame.sprite.Group()
        self.image = pygame.Surface((WIDTH, HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.play_button = Button("Играть", (WIDTH // 2 - 50, HEIGHT // 2 - 50), action=start_game)
        self.scores_menu_button = Button("Очки", (100, 200), action=self.show_scores_menu)

        self.settings_button = Button("Настройки", (WIDTH // 2 - 50, HEIGHT // 2 + 50),
                                      action=self.show_settings_menu)
        self.exit_button = Button("Выход", (WIDTH // 2 - 50, HEIGHT // 2 + 100), action=sys.exit)

        self.buttons = pygame.sprite.Group(self.play_button, self.scores_menu_button, self.settings_button,
                                           self.exit_button)
        self.language_menu = LanguageMenu()
        self.scores_menu = ScoresMenu()
        self.all_sprites.add(self.scores_menu_button)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.buttons)
        self.all_sprites.add(self)
        self.settings_menu = None

    def show_scores_menu(self):
        global in_main_menu
        in_main_menu = False
        self.all_sprites = pygame.sprite.Group(self)
        scores = get_last_scores()
        self.text_surface = self.create_text_surface(scores)
        self.scores_menu.show_scores_menu(scores)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= 5
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += 5

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                button.handle_event(event)

    def draw(self, screen):
        screen.fill(WHITE)
        for button in self.all_sprites:
            button.draw(screen)

    def show_settings_menu(self):
        global in_main_menu, all_sprites
        in_main_menu = False
        settings_menu = SettingsMenu(self)
        self.settings_menu = settings_menu  # Сохраняем экземпляр для последующего использования
        all_sprites = pygame.sprite.Group(settings_menu)
        return settings_menu


# Определение класса для экрана выбора языка
class LanguageMenu(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((WIDTH, HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.SettingsMenu = SettingsMenu
        self.font = pygame.font.Font(None, 36)
        self.languages = ["Русский", "English", "Türkçe", "日本語", "o'zbek tili", "Deutsch"]
        self.buttons = [Button(lang, (WIDTH // 2 - 50, 100 + i * 50), action=lambda l=lang: self.set_language(l)) for
                        i, lang
                        in enumerate(self.languages)]
        self.back_button = Button("Назад", (WIDTH // 2 - 50, HEIGHT - 100),
                                  action=lambda: self.show_main_menu())
        self.all_sprites = pygame.sprite.Group(self.buttons + [self.back_button])

    def handle_event(self, event):
        for button in self.all_sprites:
            button.handle_event(event)

    def draw(self, screen):
        screen.fill(WHITE)
        for button in self.all_sprites:
            button.draw(screen)

    def show_main_menu(self):
        global in_main_menu, all_sprites
        in_main_menu = True
        all_sprites = pygame.sprite.Group(main_menu)

    def set_language(self, language):
        print(f"Выбран язык: {language}")
        main_menu.show_main_menu()

    def show_settings_menu(self):
        global in_main_menu, all_sprites
        in_main_menu = False
        settings_menu = SettingsMenu(self)
        all_sprites = pygame.sprite.Group(settings_menu)


# Определение класса для меню настроек
class SettingsMenu(pygame.sprite.Sprite):
    def __init__(self, main_menu):
        super().__init__()
        self.image = pygame.Surface((WIDTH, HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.main_menu = main_menu
        self.font = pygame.font.Font(None, 36)
        self.languages = ["Русский", "English", "Türkçe", "日本語", "o'zbek tili", "Deutsch"]
        self.language_buttons = [
            Button(lang, (WIDTH // 2 - 50, 100 + i * 50), action=lambda l=lang: self.set_language(l)) for i, lang in
            enumerate(self.languages)]
        self.back_button = Button("Назад", (10, HEIGHT - 40), action=lambda: self.back_to_main_menu())
        self.all_sprites = pygame.sprite.Group(self.language_buttons + [self.back_button])

    def handle_event(self, event):
        for button in self.all_sprites:
            button.handle_event(event)

    def draw(self, screen):
        screen.fill(WHITE)
        self.all_sprites.draw(screen)

    def back_to_main_menu(self):
        self.main_menu.settings_menu = None
        all_sprites.remove(self)
        all_sprites.add(self.main_menu)

    def set_language(self, language):
        print(f"Выбран язык: {language}")
        self.main_menu.language_menu.show_language_menu()


# Определение класса для кнопки
# Определение класса для кнопки
class Button(pygame.sprite.Sprite):
    def __init__(self, text, pos, action=None):
        super().__init__()
        self.font = pygame.font.Font(None, 36)
        self.text = text
        self.image = self.font.render(text, True, BLUE)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.action = action

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                print(f"Button {self.text} clicked")
                if self.action:
                    self.action()


class ScoresMenu(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((WIDTH, HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.font = pygame.font.Font(None, 36)
        self.back_button = Button("Назад", (WIDTH // 2 - 50, HEIGHT - 50), action=self.show_main_menu)
        self.all_sprites = pygame.sprite.Group(self.back_button)

    def handle_event(self, event):
        for button in self.all_sprites:
            button.handle_event(event)

    def draw(self, screen):
        screen.fill(WHITE)
        screen.blit(self.text_surface, (50, 50))
        self.all_sprites.draw(screen)

    def show_main_menu(self):
        global in_main_menu, all_sprites
        in_main_menu = True
        all_sprites = pygame.sprite.Group(main_menu)

    def create_text_surface(self, scores):
        formatted_scores = [f"{name}: {score} points ({timestamp})" for name, score, timestamp in scores]
        unique_scores = list(set(formatted_scores))
        last_20_scores = unique_scores[:20]
        scores_text = "\n".join(last_20_scores)
        return self.font.render(scores_text, True, BLUE)

    def show_scores_menu(self, scores):
        global in_main_menu, all_sprites
        in_main_menu = False
        all_sprites = pygame.sprite.Group(self)
        self.text_surface = self.create_text_surface(scores)


# Определение функций
# Определение функций
def restart_game():
    global lives, score, in_main_menu, all_sprites, blocks
    print("Restarting game...")
    lives = 4
    score = 0
    in_main_menu = False

    # Удаление старых блоков и других спрайтов
    all_sprites.empty()
    blocks.empty()

    # Генерация новых блоков
    for row in range(5):
        for col in range(11):
            block = Block(col * 75, row * 30)
            all_sprites.add(block)
            blocks.add(block)

    # Добавление платформы и мяча
    all_sprites.add(platform, ball)


def return_to_main_menu():
    global in_main_menu
    global lives, score
    print("Returning to main menu...")
    lives = 4
    score = 0
    in_main_menu = True
    all_sprites.remove(death_screen)  # Удаляем экран смерти
    all_sprites.add(main_menu)  # Добавляем главное меню
    all_sprites.remove(platform, ball)  # Удаляем платформу и мяч
    all_sprites.remove(death_screen.restart_button, death_screen.menu_button)
    all_sprites.add(buttons)  # Добавляем кнопки главного меню


def restart_level(self):
    global lives, score, in_main_menu
    global blocks  # Глобальная переменная для блоков
    print("Restarting level...")
    lives = 4
    in_main_menu = False

    # Удаление старых блоков и кнопки
    blocks.empty()
    all_sprites.remove(self)

    # Генерация новых блоков
    for row in range(5):
        for col in range(11):
            block = Block(col * 75, row * 30)
            all_sprites.add(block)
            blocks.add(block)


def start_game():
    global in_main_menu
    in_main_menu = False
    all_sprites.remove(main_menu, buttons)
    all_sprites.add(platform, ball)

    # Генерация блоков
    for row in range(5):
        for col in range(11):
            block = Block(col * 75, row * 30)
            all_sprites.add(block)
            blocks.add(block)


# Инициализация экрана смерти
# Определение класса для экрана смерти
class DeathScreen(pygame.sprite.Sprite):
    def __init__(self, restart_action, menu_action):
        super().__init__()
        self.image = pygame.Surface((WIDTH, HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)
        self.font = pygame.font.Font(None, 50)

        self.restart_button = Button("Повторить игру", (WIDTH // 2 - 120, HEIGHT // 2), action=restart_action)
        self.menu_button = Button("Вернуться в главное меню", (WIDTH // 2 - 120, HEIGHT // 2 + 70), action=menu_action)

        self.buttons = pygame.sprite.Group(self.restart_button, self.menu_button)
        self.all_sprites = pygame.sprite.Group(self.buttons)

    def handle_event(self, event):
        for button in self.all_sprites:
            button.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.menu_button.rect.collidepoint(pygame.mouse.get_pos()):
                return_to_main_menu()
                save_score("Player1", score)
            else:
                restart_level
                save_score("Player1", score)

    def draw(self, screen):
        screen.fill(WHITE)
        for button in self.buttons:
            button.draw(screen)


# После этого вы можете создать экземпляр DeathScreen
death_screen = DeathScreen(restart_game, return_to_main_menu)

# Инициализация окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arkanoid Game")

# Инициализация игровых объектов
all_sprites = pygame.sprite.Group()
blocks = pygame.sprite.Group()
platform = Platform()
ball = Ball(platform)  # Передаем платформу при создании мяча
main_menu = MainMenu()
all_sprites.add(main_menu)

language_menu = LanguageMenu()

# Добавление кнопок в главное меню
play_button = Button("Играть", (WIDTH // 2 - 50, HEIGHT // 2 - 50), action=start_game)
score_button = Button("Очки", (WIDTH // 2 - 50, HEIGHT // 2), action=show_scores)
settings_button = Button("Настройки", (WIDTH // 2 - 50, HEIGHT // 2 + 50),
                         action=lambda: main_menu.language_menu.show_settings_menu())
exit_button = Button("Выход", (WIDTH // 2 - 50, HEIGHT // 2 + 100), action=sys.exit)

buttons = pygame.sprite.Group(play_button, score_button, settings_button, exit_button)
all_sprites.add(buttons)

lives = 3
score = 0

in_main_menu = True
# Переменная для хранения времени последнего обновления кадров
last_frame_update = pygame.time.get_ticks()

# Инициализация игрового цикла
clock = pygame.time.Clock()
running = True

while running:
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return_to_main_menu()

        elif in_main_menu:
            for button in buttons:
                button.handle_event(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if in_main_menu:
                for button in buttons:
                    button.handle_event(event)
            else:
                ball.catapult()  # Обработка клика мыши только во время игры
        # Обновление кадров каждые 16 миллисекунд (примерно 60 FPS)
    current_time = pygame.time.get_ticks()
    if current_time - last_frame_update >= 16:

        if not in_main_menu:
            all_sprites.update()
            screen.fill(WHITE)
            all_sprites.draw(screen)

            for block in blocks:
                if pygame.sprite.collide_rect(ball, block):
                    block.kill()  # Удаляем блок из группы блоков
                    ball.speed[1] = -ball.speed[1]
                    score += 1

            if pygame.sprite.spritecollide(ball, [platform], False):
                ball.speed[1] = -ball.speed[1]

            if ball.rect.top > HEIGHT:
                lives -= 1
                if lives > 0:
                    ball.rect.centerx = platform.rect.centerx
                    ball.rect.bottom = platform.rect.top
                    ball.on_platform = True
                    ball.speed = [0, 0]
                # Отобразить экран смерти
                if lives <= 0:
                    lives = 0
                    # Отобразить экран смерти
                    all_sprites.remove(platform, ball)
                    all_sprites.add(death_screen.all_sprites)

                    # Обработка событий на экране смерти
                    for event in events:
                        death_screen.handle_event(event)
                    # Сохраняем текущее время для следующего обновления кадров
            last_frame_update = current_time

            # Отображение счетчика жизней
            font = pygame.font.Font(None, 36)
            lives_text = font.render(f'Lives: {lives}', True, BLUE)
            screen.blit(lives_text, (WIDTH - 120, HEIGHT - 30))

            # Отображение счетчика очков
            score_text = font.render(f'Score: {score}', True, BLUE)
            screen.blit(score_text, (10, HEIGHT - 30))

        elif not in_main_menu and event.type == pygame.MOUSEBUTTONDOWN:
            ball.catapult()

    if in_main_menu:
        all_sprites.update()
        screen.fill(WHITE)
        all_sprites.draw(screen)

        collisions = pygame.sprite.spritecollide(ball, blocks, True)
        for block in collisions:
            ball.speed[1] = -ball.speed[1]
            score += 1

        if pygame.sprite.spritecollide(ball, [platform], False):
            ball.speed[1] = -ball.speed[1]

        if ball.rect.top > HEIGHT:
            lives -= 1
            if lives > 0:
                ball.rect.centerx = platform.rect.centerx
                ball.rect.bottom = platform.rect.top
                ball.on_platform = True
                ball.speed = [0, 0]
            else:
                in_main_menu = False
                all_sprites.remove[platform, ball]
                all_sprites.add(death_screen.all_sprites)
                lives = 0  # Добавлено условие, чтобы счетчик жизней не уходил в отрицательные значения

    # Переключение экранов
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
