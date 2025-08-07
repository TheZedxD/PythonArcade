import pygame

class State:
    """Base class for game states."""
    def __init__(self):
        self.done = False
        self.quit = False
        self.next = None
        self.screen = None

    def startup(self, screen):
        """Called when the state starts up."""
        self.done = False
        self.quit = False
        self.screen = screen

    def cleanup(self):
        """Cleanup before the state is destroyed or switched."""
        pass

    def get_event(self, event):
        """Dispatch input events to specialized handlers."""
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            self.handle_keyboard(event)
        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            self.handle_mouse(event)
        elif event.type in (pygame.JOYAXISMOTION, pygame.JOYBALLMOTION,
                             pygame.JOYHATMOTION, pygame.JOYBUTTONDOWN,
                             pygame.JOYBUTTONUP):
            self.handle_gamepad(event)

    def update(self, dt):
        """Update the state. *dt* is elapsed time in seconds."""
        pass

    def draw(self):
        """Draw everything to the screen."""
        pass

    def handle_keyboard(self, event):
        """Handle keyboard events."""
        pass

    def handle_mouse(self, event):
        """Handle mouse events."""
        pass

    def handle_gamepad(self, event):
        """Handle gamepad events."""
        pass
