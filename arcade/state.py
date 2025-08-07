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
        """Handle a single event."""
        pass

    def update(self, dt):
        """Update the state. *dt* is elapsed time in seconds."""
        pass

    def draw(self):
        """Draw everything to the screen."""
        pass
