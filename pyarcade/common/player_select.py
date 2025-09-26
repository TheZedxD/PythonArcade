import pygame
from .theme import BG_COLOR, PRIMARY_COLOR, ACCENT_COLOR, get_font, draw_text

class PlayerSelectOverlay:
    """
    Minimal, non-blocking 1–2 player selector.
    Usage:
        selector = PlayerSelectOverlay()
        players = selector.run(screen)  # returns 1 or 2
    Controls:
        - Press "1" or "2"
        - Left/Right arrows to move selection, Enter to confirm
        - Gamepad: DPAD left/right to toggle, A to confirm
        - ESC quits back with default 1
    """
    def __init__(self):
        self.options = [1, 2]
        self.index = 0

    def run(self, screen):
        clock = pygame.time.Clock()
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION])
        font_title = get_font(48)
        font_opt   = get_font(36)

        # pre-init joystick if present
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            pygame.joystick.Joystick(0).init()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return self.options[self.index]
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return self.options[self.index]
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.index = 0
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.index = 1
                    elif event.key == pygame.K_RETURN:
                        return self.options[self.index]
                    elif event.key == pygame.K_1:
                        return 1
                    elif event.key == pygame.K_2:
                        return 2
                # Simple gamepad support
                if event.type == pygame.JOYHATMOTION:
                    hatx, _ = event.value
                    if hatx < 0: self.index = 0
                    if hatx > 0: self.index = 1
                if event.type == pygame.JOYBUTTONDOWN:
                    # A button on most pads is 0
                    if event.button == 0:
                        return self.options[self.index]

            screen.fill(BG_COLOR)
            draw_text(screen, "SELECT PLAYERS", font_title, PRIMARY_COLOR, y_offset=-80)

            # draw two “buttons”
            w, h = screen.get_size()
            btn_w, btn_h = int(w*0.25), int(h*0.18)
            gap = int(w*0.08)
            x1 = w//2 - btn_w - gap//2
            x2 = w//2 + gap//2
            y  = h//2 - btn_h//2

            # outlines
            pygame.draw.rect(screen, ACCENT_COLOR if self.index==0 else PRIMARY_COLOR, (x1, y, btn_w, btn_h), 3, border_radius=16)
            pygame.draw.rect(screen, ACCENT_COLOR if self.index==1 else PRIMARY_COLOR, (x2, y, btn_w, btn_h), 3, border_radius=16)

            # labels
            draw_text(screen, "1", font_opt, PRIMARY_COLOR, center=(x1+btn_w//2, y+btn_h//2))
            draw_text(screen, "2", font_opt, PRIMARY_COLOR, center=(x2+btn_w//2, y+btn_h//2))

            # hint
            draw_text(screen, "Use ←/→ + Enter or press 1/2  (Gamepad: DPAD + A)", get_font(18), PRIMARY_COLOR, y_offset=h//2 + btn_h//2 + 40)

            pygame.display.flip()
            clock.tick(60)


