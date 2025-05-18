import pygame
import sys
import random
import math

# --- Pygame Setup ---
pygame.init()

WIDTH, HEIGHT = 800, 600
BACKGROUND_COLOR = (0xAA, 0x91, 0xA1)
BODY_COLOR = (0xEC, 0xDA, 0xE8)
HEAD_COLOR = (128, 0, 128)  # purple head

FONT = pygame.font.SysFont("comicsans", 32)
BUTTON_FONT = pygame.font.SysFont("comicsans", 24)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nim Game - GUI")

# --- Game Logic ---
def is_terminal(state):
    return all(h == 0 for h in state)

def utility(state, maximizing):
    return -1 if maximizing else 1 if is_terminal(state) else 0

def get_successors(state):
    moves = []
    for i, cnt in enumerate(state):
        for take in range(1, cnt + 1):
            new_state = state.copy()
            new_state[i] -= take
            moves.append((i, take, new_state))
    return moves

def minimax(state, maximizing):
    if is_terminal(state):
        return utility(state, maximizing), None
    best_val, best_move = (-math.inf, None) if maximizing else (math.inf, None)
    for i, take, new_state in get_successors(state):
        val, _ = minimax(new_state, not maximizing)
        if (maximizing and val > best_val) or (not maximizing and val < best_val):
            best_val, best_move = val, (i, take)
    return best_val, best_move

def minimax_ab(state, alpha, beta, maximizing):
    if is_terminal(state):
        return utility(state, maximizing), None
    best_move = None
    if maximizing:
        value = -math.inf
        for i, take, new_state in get_successors(state):
            val, _ = minimax_ab(new_state, alpha, beta, False)
            if val > value:
                value, best_move = val, (i, take)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = math.inf
        for i, take, new_state in get_successors(state):
            val, _ = minimax_ab(new_state, alpha, beta, True)
            if val < value:
                value, best_move = val, (i, take)
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move

# --- MCTS ---
class MCTSNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = get_successors(state)

    def uct_select(self):
        return max(
            self.children,
            key=lambda c: (c.wins / c.visits) + math.sqrt(2 * math.log(self.visits) / c.visits)
        )

def simulate(state):
    current = state.copy()
    maximizing = True
    while not is_terminal(current):
        _, take, next_state = random.choice(get_successors(current))
        current = next_state
        maximizing = not maximizing
    return utility(current, not maximizing)

def mcts(state, iter_count=100):
    root = MCTSNode(state)
    for _ in range(iter_count):
        node = root
        # 1. Selection
        while not node.untried_moves and node.children:
            node = node.uct_select()
        # 2. Expansion
        if node.untried_moves:
            i, take, new_state = node.untried_moves.pop()
            child = MCTSNode(new_state, node)
            node.children.append(child)
            node = child
        # 3. Simulation
        result = simulate(node.state)
        # 4. Backpropagation
        while node:
            node.visits += 1
            node.wins += result
            node = node.parent
    # Pick best child
    best_child = max(root.children, key=lambda c: c.visits)
    for i, take, new_state in get_successors(state):
        if new_state == best_child.state:
            return (i, take)
    return None

# --- UI Helper: customizable button ---
def darken_color(color, factor=0.8):
    """Darken an RGB color by a factor."""
    return tuple(max(0, int(c * factor)) for c in color)

def draw_button(text, x, y, w, h, bg_color, text_color=(0, 0, 0), pressed=False):
    """Draw a button, darkening bg_color if pressed."""
    r = pygame.Rect(x, y, w, h)
    color = darken_color(bg_color) if pressed else bg_color
    pygame.draw.rect(screen, color, r, border_radius=8)
    label = BUTTON_FONT.render(text, True, text_color)
    screen.blit(label,
                (x + (w - label.get_width()) // 2,
                 y + (h - label.get_height()) // 2))
    return r

# --- AI selection menu ---
def draw_ai_menu():
    screen.fill(BACKGROUND_COLOR)
    title = FONT.render("Choose AI Mode", True, (0, 0, 0))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

    options = [
        ("Minimax", "minimax"),
        ("Minimax + Alpha-Beta", "minimax_ab"),
        ("MCTS", "mcts")
    ]
    rects = []
    pressed_button = None

    while True:
        screen.fill(BACKGROUND_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
        rects.clear()

        for idx, (label, mode) in enumerate(options):
            pressed = pressed_button == idx
            btn = draw_button(label, 250, 200 + idx * 80, 300, 60,
                              (41, 48, 76), (255, 255, 255), pressed)
            rects.append((btn, mode, idx))

        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for btn, mode, idx in rects:
                    if btn.collidepoint(ev.pos):
                        pressed_button = idx
            if ev.type == pygame.MOUSEBUTTONUP:
                for btn, mode, idx in rects:
                    if btn.collidepoint(ev.pos) and pressed_button == idx:
                        return mode
                pressed_button = None

# --- Drawing matches & row-buttons ---
def draw_matches(state, selected_row, pressed_row=None, pressed_action=None):
    screen.fill(BACKGROUND_COLOR)

    # build one match image
    match_w, shaft_h, head_h = 10, 40, 12
    match_img = pygame.Surface((match_w, shaft_h + head_h), pygame.SRCALPHA)
    pygame.draw.ellipse(match_img, HEAD_COLOR, (0, 0, match_w, head_h * 2))
    shaft_rect = (match_w // 4, head_h, match_w // 2, shaft_h)
    pygame.draw.rect(match_img, BODY_COLOR, shaft_rect, border_radius=3)

    # tile each row
    start_y = 100
    row_rects = []
    for row, count in enumerate(state):
        start_x = WIDTH // 2 - (count * (match_w + 5)) // 2
        for i in range(count):
            screen.blit(match_img, (start_x + i * (match_w + 5), start_y))

        # row button
        pressed = pressed_row == row
        btn = draw_button(
            f"Row {row + 1}",
            WIDTH - 120, start_y + 10,
            100, 40,
            bg_color=(137, 117, 140),
            text_color=(236, 218, 232),
            pressed=pressed
        )
        row_rects.append((btn, row))
        start_y += 80

    return row_rects

# --- Main Game Loop ---
def game_loop():
    state = [1, 3, 5, 7]
    selected_row = None
    turn = "player"
    ai_mode = draw_ai_menu()
    pressed_row = None
    pressed_action = None

    while True:
        row_rects = draw_matches(state, selected_row, pressed_row, pressed_action)

        # global buttons with pressed state
        new_btn = draw_button("New game", 40, 520, 120, 40,
                              bg_color=(137, 117, 140), text_color=(236, 218, 232),
                              pressed=pressed_action == "new")
        exit_btn = draw_button("Close window", 180, 520, 140, 40,
                               bg_color=(137, 117, 140), text_color=(236, 218, 232),
                               pressed=pressed_action == "exit")
        take_btn = draw_button("Take 1", 340, 520, 120, 40,
                               bg_color=(0x29, 0x30, 0x4C), text_color=(255, 255, 255),
                               pressed=pressed_action == "take")
        confirm_btn = draw_button("Confirm", 480, 520, 120, 40,
                                  bg_color=(0x5D, 0x62, 0x7A), text_color=(0xEC, 0xDA, 0xE8),
                                  pressed=pressed_action == "confirm")

        pygame.display.update()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.MOUSEBUTTONDOWN:
                x, y = ev.pos

                # check row buttons
                for btn, row in row_rects:
                    if btn.collidepoint(x, y) and state[row] > 0:
                        pressed_row = row

                # check action buttons
                if new_btn.collidepoint(x, y):
                    pressed_action = "new"
                elif exit_btn.collidepoint(x, y):
                    pressed_action = "exit"
                elif take_btn.collidepoint(x, y):
                    pressed_action = "take"
                elif confirm_btn.collidepoint(x, y):
                    pressed_action = "confirm"

            if ev.type == pygame.MOUSEBUTTONUP:
                x, y = ev.pos

                # reset / exit
                if new_btn.collidepoint(x, y) and pressed_action == "new":
                    return game_loop()
                if exit_btn.collidepoint(x, y) and pressed_action == "exit":
                    pygame.quit()
                    sys.exit()

                # player turn
                if turn == "player":
                    # pick a row only once
                    if selected_row is None:
                        for btn, row in row_rects:
                            if btn.collidepoint(x, y) and state[row] > 0 and pressed_row == row:
                                selected_row = row

                    # take 1 stick
                    if take_btn.collidepoint(x, y) and pressed_action == "take" and selected_row is not None and state[selected_row] > 0:
                        state[selected_row] -= 1

                    # confirm end of turn
                    if confirm_btn.collidepoint(x, y) and pressed_action == "confirm" and selected_row is not None:
                        if is_terminal(state):
                            screen.fill(BACKGROUND_COLOR)
                            win_txt = FONT.render("Player Wins!", True, (41, 48, 76))
                            screen.blit(win_txt, (WIDTH // 2 - win_txt.get_width() // 2, HEIGHT // 2))
                            pygame.display.update()
                            pygame.time.wait(2000)
                            return game_loop()
                        turn = "pc"
                        selected_row = None

                pressed_row = None
                pressed_action = None

        # AI turn
        if turn == "pc":
            pygame.time.wait(800)
            if ai_mode == "minimax":
                _, move = minimax(state, True)
            elif ai_mode == "minimax_ab":
                _, move = minimax_ab(state, -math.inf, math.inf, True)
            else:
                move = mcts(state)

            if move:
                i, t = move
                state[i] -= t

            if is_terminal(state):
                screen.fill(BACKGROUND_COLOR)
                lose_txt = FONT.render("PC Wins!", True, (41, 48, 76))
                screen.blit(lose_txt, (WIDTH // 2 - lose_txt.get_width() // 2, HEIGHT // 2))
                pygame.display.update()
                pygame.time.wait(2000)
                return game_loop()

            turn = "player"
            selected_row = None

if __name__ == "__main__":
    game_loop()