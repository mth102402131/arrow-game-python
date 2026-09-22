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
ORANGE = (255, 165, 0)  # 【新增】用于选关按钮高亮
LOCKED_GRAY = (150, 150, 150)  # 【新增】未解锁关卡颜色

UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

# --- 关卡设计 ---
LEVELS = [
    [(2, 2, LEFT), (2, 5, RIGHT), (4, 3, DOWN), (1, 3, UP), (5, 5, RIGHT)],
    [(1, 1, RIGHT), (1, 2, RIGHT), (1, 3, RIGHT), (3, 1, DOWN), (4, 1, DOWN), (2, 6, LEFT), (2, 5, LEFT)],
    [(2, 2, RIGHT), (2, 3, RIGHT), (4, 4, DOWN), (5, 4, DOWN), (1, 1, DOWN), (6, 6, LEFT)]
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
        pygame.display.set_caption("一箭又一箭 - 关卡选择版")
        self.clock = pygame.time.Clock()

        try:
            self.font = pygame.font.SysFont("simhei", 40)
            self.small_font = pygame.font.SysFont("simhei", 24)
            self.tiny_font = pygame.font.SysFont("simhei", 18)
        except:
            self.font = pygame.font.Font(None, 40)
            self.small_font = pygame.font.Font(None, 24)
            self.tiny_font = pygame.font.Font(None, 18)

        self.state = "START"
        self.current_level_idx = 0
        self.arrows = []
        self.mistakes_left = MAX_MISTAKES

        # 【新增】记录已解锁的最高关卡索引 (0表示只解锁了第1关)
        self.max_unlocked_level = 0

        # 按钮定义
        self.start_btn = pygame.Rect(300, 350, 200, 60)  # 开始游戏
        self.select_btn = pygame.Rect(300, 430, 200, 60)  # 【新增】选择关卡按钮
        self.restart_btn = pygame.Rect(680, 20, 100, 40)  # 游戏中重置
        self.next_btn = pygame.Rect(300, 450, 200, 60)  # 下一关
        self.back_btn = pygame.Rect(300, 550, 200, 60)  # 【新增】返回按钮(选关/通关界面)

        # 【新增】关卡选择按钮列表 (在draw中动态生成，在click中检测)
        self.level_buttons = []

    def load_level(self, level_idx):
        self.arrows = []
        if level_idx < len(LEVELS):
            for r, c, d in LEVELS[level_idx]:
                self.arrows.append(Arrow(r, c, d))
            self.mistakes_left = MAX_MISTAKES
            self.current_level_idx = level_idx
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
        # === START 主菜单 ===
        if self.state == "START":
            if self.start_btn.collidepoint(pos):
                self.current_level_idx = 0
                self.load_level(self.current_level_idx)
            # 【新增】点击进入选关界面
            elif self.select_btn.collidepoint(pos):
                self.state = "LEVEL_SELECT"

        # === PLAYING 游戏中 ===
        elif self.state == "PLAYING":
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

        # === LEVEL_COMPLETE 关卡通过 ===
        elif self.state == "LEVEL_COMPLETE":
            if self.next_btn.collidepoint(pos):
                next_idx = self.current_level_idx + 1
                # 【新增】更新最高解锁关卡
                if next_idx > self.max_unlocked_level:
                    self.max_unlocked_level = next_idx
                self.load_level(next_idx)
            # 【新增】通关后也可以去选关
            elif self.back_btn.collidepoint(pos):
                self.state = "LEVEL_SELECT"

        # === GAME_OVER 失败 ===
        elif self.state == "GAME_OVER":
            if self.start_btn.collidepoint(pos):
                self.load_level(self.current_level_idx)
            # 【新增】失败后也可以去选关界面
            elif self.back_btn.collidepoint(pos):
                self.state = "LEVEL_SELECT"

        # === WIN 全部通关 ===
        elif self.state == "WIN":
            if self.start_btn.collidepoint(pos):
                self.state = "START"
                self.current_level_idx = 0
            elif self.back_btn.collidepoint(pos):
                self.state = "LEVEL_SELECT"

        # 【新增】=== LEVEL_SELECT 选关界面 ===
        elif self.state == "LEVEL_SELECT":
            # 检测关卡按钮点击
            for btn_info in self.level_buttons:
                rect, idx, unlocked = btn_info
                if rect.collidepoint(pos) and unlocked:
                    self.load_level(idx)
                    return
            # 返回主菜单
            if self.back_btn.collidepoint(pos):
                self.state = "START"

    def update(self):
        if self.state == "PLAYING":
            for arrow in self.arrows:
                arrow.update()
            if sum(1 for a in self.arrows if a.active) == 0:
                self.state = "LEVEL_COMPLETE"

    def draw_text(self, text, x, y, color=BLACK, font_obj=None):
        if font_obj is None: font_obj = self.font
        surf = font_obj.render(text, True, color)
        self.screen.blit(surf, (x, y))

    def draw_button(self, rect, text, bg_color, text_color=WHITE, font_obj=None):
        """通用按钮绘制辅助函数"""
        if font_obj is None: font_obj = self.small_font
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)
        pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=8)
        surf = font_obj.render(text, True, text_color)
        text_rect = surf.get_rect(center=rect.center)
        self.screen.blit(surf, text_rect)

    # 【新增】绘制关卡选择界面
    def draw_level_select(self):
        self.screen.fill(WHITE)
        self.draw_text("选择关卡", 310, 50, BLACK)

        # 动态生成关卡按钮网格
        self.level_buttons = []
        cols = 5
        btn_size = 80
        gap = 20
        start_x = (SCREEN_WIDTH - (cols * btn_size + (cols - 1) * gap)) // 2
        start_y = 150

        for i in range(len(LEVELS)):
            row = i // cols
            col = i % cols
            x = start_x + col * (btn_size + gap)
            y = start_y + row * (btn_size + gap)
            rect = pygame.Rect(x, y, btn_size, btn_size)

            unlocked = i <= self.max_unlocked_level

            if unlocked:
                # 已解锁：当前关卡高亮橙色，其他绿色
                bg = ORANGE if i == self.current_level_idx else GREEN
                label = str(i + 1)
                text_color = WHITE
            else:
                # 未解锁：灰色 + 锁图标
                bg = LOCKED_GRAY
                label = "🔒"
                text_color = DARK_GRAY

            self.level_buttons.append((rect, i, unlocked))
            self.draw_button(rect, label, bg, text_color)

            # 在按钮下方显示小标签
            if unlocked:
                status = "✓ 已通" if i < self.max_unlocked_level else "进行中" if i == self.current_level_idx else ""
                if status:
                    s = self.tiny_font.render(status, True, GRAY)
                    self.screen.blit(s, (x + btn_size // 2 - s.get_width() // 2, y + btn_size + 2))

        # 返回按钮
        self.draw_button(self.back_btn, "返回主菜单", DARK_GRAY)

    def draw(self):
        self.screen.fill(WHITE)

        if self.state == "START":
            self.draw_text("一箭又一箭", 280, 150)
            self.draw_text("Python 作业 (关卡选择版)", 240, 220, GRAY, self.small_font)
            self.draw_button(self.start_btn, "开始游戏", GREEN)
            # 【新增】选关按钮
            self.draw_button(self.select_btn, "选择关卡", BLUE)

        elif self.state == "PLAYING":
            pygame.draw.rect(self.screen, LIGHT_BLUE, (0, 0, SCREEN_WIDTH, UI_HEIGHT))
            pygame.draw.line(self.screen, BLACK, (0, UI_HEIGHT), (SCREEN_WIDTH, UI_HEIGHT), 2)
            self.draw_text(f"关卡: {self.current_level_idx + 1}/{len(LEVELS)}", 20, 20, BLACK, self.small_font)
            mistake_color = RED if self.mistakes_left == 1 else BLACK
            self.draw_text(f"剩余失误: {self.mistakes_left}", 20, 60, mistake_color, self.small_font)
            active_arrows = sum(1 for a in self.arrows if a.active)
            self.draw_text(f"剩余箭头: {active_arrows}", 250, 60, BLACK, self.small_font)
            self.draw_button(self.restart_btn, "重置", DARK_GRAY, font_obj=self.tiny_font)
            for x in range(0, SCREEN_WIDTH, GRID_SIZE):
                pygame.draw.line(self.screen, GRAY, (x, UI_HEIGHT), (x, SCREEN_HEIGHT))
            for y in range(UI_HEIGHT, SCREEN_HEIGHT, GRID_SIZE):
                pygame.draw.line(self.screen, GRAY, (0, y), (SCREEN_WIDTH, y))
            for arrow in self.arrows:
                arrow.draw(self.screen)

        elif self.state == "LEVEL_COMPLETE":
            self.draw_text("关卡通过!", 300, 250, GREEN)
            self.draw_button(self.next_btn, "下一关", BLUE)
            # 【新增】通关后可去选关
            self.draw_button(self.back_btn, "选择关卡", DARK_GRAY)

        elif self.state == "GAME_OVER":
            self.draw_text("游戏失败", 300, 200, RED)
            self.draw_text("失误次数已耗尽", 280, 270, GRAY, self.small_font)
            self.draw_button(self.start_btn, "重试本关", RED)
            # 【新增】失败后可去选关
            self.draw_button(self.back_btn, "选择关卡", DARK_GRAY)

        elif self.state == "WIN":
            self.draw_text("🎉 恭喜通关! 🎉", 230, 200, YELLOW)
            self.draw_text("所有关卡已完成", 280, 280, GRAY, self.small_font)
            self.draw_button(self.start_btn, "返回主页", GREEN)
            self.draw_button(self.back_btn, "选择关卡", BLUE)

        # 【新增】选关界面单独绘制
        elif self.state == "LEVEL_SELECT":
            self.draw_level_select()

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