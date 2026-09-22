import pygame
import sys

# --- 配置常量 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
GRID_SIZE = 50
FPS = 60
UI_HEIGHT = 100

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 100, 200)
YELLOW = (255, 215, 0)
LIGHT_BLUE = (230, 240, 255)

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

# --- 关卡设计 ---
LEVELS = [
    # Level 1
    [
        (2, 2, LEFT), (2, 5, RIGHT), (4, 3, DOWN), (1, 3, UP), (5, 5, RIGHT)
    ],
    # Level 2
    [
        (1, 1, RIGHT), (1, 2, RIGHT), (1, 3, RIGHT),
        (3, 1, DOWN), (4, 1, DOWN),
        (2, 6, LEFT), (2, 5, LEFT)
    ],
    # Level 3
    [
        (2, 2, RIGHT), (2, 3, RIGHT),
        (4, 4, DOWN), (5, 4, DOWN),
        (1, 1, DOWN), (6, 6, LEFT)
    ]
]

MAX_MISTAKES = 3


class Arrow:
    def __init__(self, row, col, direction):
        self.row = row
        self.col = col
        self.direction = direction
        self.rect = pygame.Rect(col * GRID_SIZE, row * GRID_SIZE + UI_HEIGHT, GRID_SIZE, GRID_SIZE)
        self.active = True
        self.shake_timer = 0
        self.fly_offset = 0
        self.flying = False
        self.fly_speed = 15

    def draw(self, screen):
        if not self.active and not self.flying:
            return

        color = BLUE
        draw_rect = self.rect

        if self.shake_timer > 0:
            color = RED
            offset_x = 5 if (self.shake_timer // 4) % 2 == 0 else -5
            draw_rect = self.rect.move(offset_x, 0)
        elif self.flying:
            dx, dy = 0, 0
            if self.direction == UP:
                dy = -self.fly_offset
            elif self.direction == DOWN:
                dy = self.fly_offset
            elif self.direction == LEFT:
                dx = -self.fly_offset
            elif self.direction == RIGHT:
                dx = self.fly_offset
            draw_rect = self.rect.move(dx, dy)

        pygame.draw.rect(screen, color, draw_rect)
        pygame.draw.rect(screen, BLACK, draw_rect, 2)

        font = pygame.font.SysFont("simhei", 32)
        symbols = ["↑", "↓", "←", "→"]
        text_surf = font.render(symbols[self.direction], True, WHITE)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)

    def update(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
        if self.flying:
            self.fly_offset += self.fly_speed
            if self.fly_offset > SCREEN_HEIGHT:
                self.active = False
                self.flying = False


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("一箭又一箭 - 重试修复版")
        self.clock = pygame.time.Clock()

        try:
            self.font = pygame.font.SysFont("simhei", 40)
            self.small_font = pygame.font.SysFont("simhei", 24)
        except:
            self.font = pygame.font.Font(None, 40)
            self.small_font = pygame.font.Font(None, 24)

        self.state = "START"
        self.current_level_idx = 0
        self.arrows = []
        self.mistakes_left = MAX_MISTAKES

        # 按钮定义
        self.start_btn = pygame.Rect(300, 450, 200, 60)  # 用于开始、重试、返回主页
        self.restart_btn = pygame.Rect(680, 20, 100, 40)  # 游戏中右上角的重置
        self.next_btn = pygame.Rect(300, 450, 200, 60)  # 下一关

    def load_level(self, level_idx):
        """加载关卡，重置箭头和失误数"""
        self.arrows = []
        if level_idx < len(LEVELS):
            for r, c, d in LEVELS[level_idx]:
                self.arrows.append(Arrow(r, c, d))
            self.mistakes_left = MAX_MISTAKES
            self.state = "PLAYING"
        else:
            self.state = "WIN"

    def check_path(self, arrow):
        r, c = arrow.row, arrow.col
        dr, dc = 0, 0
        if arrow.direction == UP:
            dr = -1
        elif arrow.direction == DOWN:
            dr = 1
        elif arrow.direction == LEFT:
            dc = -1
        elif arrow.direction == RIGHT:
            dc = 1

        curr_r, curr_c = r + dr, c + dc
        steps = 0
        while steps < 50:
            for other in self.arrows:
                if other.active and other.row == curr_r and other.col == curr_c:
                    return False
            curr_r += dr
            curr_c += dc
            steps += 1
            if curr_r < -5 or curr_r > 20 or curr_c < -5 or curr_c > 20:
                break
        return True

    def handle_click(self, pos):
        if self.state == "START":
            if self.start_btn.collidepoint(pos):
                self.current_level_idx = 0
                self.load_level(self.current_level_idx)

        elif self.state == "PLAYING":
            # 游戏中点击右上角重置
            if self.restart_btn.collidepoint(pos):
                self.load_level(self.current_level_idx)
                return

            for arrow in self.arrows:
                if arrow.active and arrow.rect.collidepoint(pos):
                    if self.check_path(arrow):
                        arrow.flying = True
                    else:
                        arrow.shake_timer = 20
                        self.mistakes_left -= 1
                        if self.mistakes_left <= 0:
                            self.state = "GAME_OVER"
                    break

        elif self.state == "LEVEL_COMPLETE":
            if self.next_btn.collidepoint(pos):
                self.current_level_idx += 1
                self.load_level(self.current_level_idx)

        # ==========================================
        # 【核心修改区域】
        # ==========================================
        elif self.state == "GAME_OVER":
            # 失败后点击按钮 -> 重新加载当前关卡 (不改变 current_level_idx)
            if self.start_btn.collidepoint(pos):
                self.load_level(self.current_level_idx)

        elif self.state == "WIN":
            # 通关后点击按钮 -> 回到主菜单
            if self.start_btn.collidepoint(pos):
                self.state = "START"
                self.current_level_idx = 0

    def update(self):
        if self.state == "PLAYING":
            for arrow in self.arrows:
                arrow.update()
            # 检查是否所有箭头都消失了
            if sum(1 for a in self.arrows if a.active) == 0:
                self.state = "LEVEL_COMPLETE"

    def draw_text(self, text, x, y, color=BLACK, font_obj=None):
        if font_obj is None: font_obj = self.font
        surf = font_obj.render(text, True, color)
        self.screen.blit(surf, (x, y))

    def draw(self):
        self.screen.fill(WHITE)

        if self.state == "START":
            self.draw_text("一箭又一箭", 280, 150)
            self.draw_text("Python 作业 (重试修复版)", 250, 220, GRAY, self.small_font)
            pygame.draw.rect(self.screen, GREEN, self.start_btn)
            self.draw_text("开始游戏", 330, 460, WHITE, self.small_font)

        elif self.state == "PLAYING":
            pygame.draw.rect(self.screen, LIGHT_BLUE, (0, 0, SCREEN_WIDTH, UI_HEIGHT))
            pygame.draw.line(self.screen, BLACK, (0, UI_HEIGHT), (SCREEN_WIDTH, UI_HEIGHT), 2)

            self.draw_text(f"关卡: {self.current_level_idx + 1}", 20, 20, BLACK, self.small_font)
            mistake_color = RED if self.mistakes_left == 1 else BLACK
            self.draw_text(f"剩余失误: {self.mistakes_left}", 20, 60, mistake_color, self.small_font)
            active_arrows = sum(1 for a in self.arrows if a.active)
            self.draw_text(f"剩余箭头: {active_arrows}", 250, 60, BLACK, self.small_font)

            pygame.draw.rect(self.screen, DARK_GRAY, self.restart_btn)
            self.draw_text("重置", 700, 25, WHITE, self.small_font)

            for x in range(0, SCREEN_WIDTH, GRID_SIZE):
                pygame.draw.line(self.screen, GRAY, (x, UI_HEIGHT), (x, SCREEN_HEIGHT))
            for y in range(UI_HEIGHT, SCREEN_HEIGHT, GRID_SIZE):
                pygame.draw.line(self.screen, GRAY, (0, y), (SCREEN_WIDTH, y))

            for arrow in self.arrows:
                arrow.draw(self.screen)

        elif self.state == "LEVEL_COMPLETE":
            self.draw_text("关卡通过!", 300, 250, GREEN)
            pygame.draw.rect(self.screen, BLUE, self.next_btn)
            self.draw_text("下一关", 340, 460, WHITE, self.small_font)

        elif self.state == "GAME_OVER":
            self.draw_text("游戏失败", 300, 250, RED)
            self.draw_text("失误次数已耗尽", 280, 320, GRAY, self.small_font)

            # 【修改】按钮颜色可以用红色或深灰，文字改为“重试本关”
            pygame.draw.rect(self.screen, RED, self.start_btn)
            self.draw_text("重试本关", 330, 460, WHITE, self.small_font)

        elif self.state == "WIN":
            self.draw_text("恭喜通关!", 280, 250, YELLOW)
            self.draw_text("所有关卡已完成", 280, 320, GRAY, self.small_font)
            pygame.draw.rect(self.screen, GREEN, self.start_btn)
            self.draw_text("返回主页", 330, 460, WHITE, self.small_font)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()