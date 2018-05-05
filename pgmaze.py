#! /usr/bin/env python3
"""
pgmaze.py by n2qz

Hacked together from the Simpson College Computer Science Sample
Python/Pygame Programs collection http://programarcadegames.com/python_examples/f.php?file=maze_runner.py

and maze.py by Erik Sweet and Bill Basener
https://gist.github.com/SZanlongo/e293aff9bf9a98164b39e2aa40717dc0

Sound resource "click.wav" is an edited version of Sebastian's "Click2 Sound" http://soundbible.com/1705-Click2.html

Uses "Audience Applause Sound" by matthiew11: http://soundbible.com/2087-Audience-Applause.html

I don't remember where I found charge.wav

"""
import random
import sys
import argparse
import pygame
from maze import maze
import math

# Global constants

BLACK  = (   0,   0,   0)
WHITE  = ( 255, 255, 255)
BLUE   = (   0,   0, 255)
GREEN  = (   0, 255,   0)
RED    = ( 255,   0,   0)
PURPLE = ( 255,   0, 255)
YELLOW = ( 255, 255,   0)
CYAN   = (   0, 255, 255)

wall_colors = [ WHITE, BLUE, GREEN, RED, PURPLE, YELLOW, CYAN ]

class Game(object):
    """This class represents the game object to keep track of various global state"""

    def __init__(self, level, cheat):
        """Constructor function"""

        # Call the parent's constructor
        super().__init__()

        # With a 1900x1900 game display, level 76 is the last level where the 15x15 sprite fits through the maze tunnel

        self.last_level = 76

        if level == 'last':
            self.level = self.last_level
        else:
            self.level = int(level)

        if self.level > self.last_level:
            raise ValueError("Level must be less than " + str(self.last_level + 1))
        if self.level < 1:
            raise ValueError("Level must be greater than 0")

        self.cheat = cheat
        
        if self.cheat:
            print("Cheat mode is active!")
        else:
            pygame.mouse.set_visible(False)

        # Sounds dictionary
        self.sounds = {}

        self.num_cols = self.level
        self.num_rows = self.num_cols

        self.display_width = 1900
        self.display_height = 1900

        self.cell_width = self.display_width / self.num_cols
        self.cell_height = self.display_height / self.num_rows
    
        self.wall_thickness = 5

        player_width = 15
        player_height = player_width

        # Call this function so the Pygame library can initialize itself
        pygame.init()

        # Initialize the joysticks
        pygame.joystick.init()
    
        # Get count of joysticks
        joystick_count = pygame.joystick.get_count()
        print('Joysticks detected:', joystick_count)

        if joystick_count:
            self.caljoy = CalibratedJoystick(0)

        # When my old Microsoft game controller is in hat mode, the joystick axes float unpredictably.
        # When any hat motion is detected, ignore any joystick input until all axes return to 0
        self.hatmode = False

        # We will use channel 0 for click sounds in the player object,
        # so we can track if it is busy without interference from the charge sound
        pygame.mixer.set_reserved(1)
    
        # Load sounds
        self.sounds['click'] = pygame.mixer.Sound("resources/click.wav")
        self.sounds['charge'] = pygame.mixer.Sound("resources/charge.wav")
        self.sounds['applause'] = pygame.mixer.Sound("resources/Audience_Applause-Matthiew11-1206899159.wav")

        # Create the display screen
        self.screen = pygame.display.set_mode([self.display_width, self.display_height])

        # Set the title of the window
        pygame.display.set_caption('PG Maze - Level ' + str(self.level))

        # Create the player paddle object
        self.player = Player(self, 0, 0, player_width, player_height)
        self.movingsprites = pygame.sprite.Group()
        self.movingsprites.add(self.player)
    
        # Create the first room
        self.room = Room(self.num_rows, self.num_cols, self.cell_width, self.cell_height, self.wall_thickness, self.player)

        self.clock = pygame.time.Clock()

        self.done = False

        self.sounds['charge'].play() 

    def youwin_screen(self):
        pygame.display.set_caption('PG Maze - You Win!')
        self.sounds['applause'].play() 

        # process events
        wait_eventlists = [ [pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.MOUSEBUTTONDOWN], [pygame.KEYUP, pygame.JOYBUTTONUP, pygame.MOUSEBUTTONUP] ]
        self.done = False
        while wait_eventlists:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    wait_eventlists = []
                elif wait_eventlists and event.type in wait_eventlists[0]:
                    wait_eventlists.pop(0)
            # Run logic
            pass
            # display frame
            screen_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            text_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            self.screen.fill(screen_color)
            font = pygame.font.Font(None, 72)
            text = font.render("You Win!  Press any key to play again.", True, text_color)
            text_rect = text.get_rect()
            text_x = random.randint(0, self.screen.get_width() - text_rect.width)
            text_y = random.randint(0, self.screen.get_height() - text_rect.height)
            self.screen.blit(text, [text_x, text_y])
            pygame.display.flip()
            self.clock.tick(2)

    def process_events(self):
        keyspeed = 5
        joyspeed = 14
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True
            if self.cheat:
                if event.type == pygame.MOUSEBUTTONUP:
                    self.player.setpos(pygame.mouse.get_pos())
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.player.setxspeed(-keyspeed)
                elif event.key == pygame.K_RIGHT:
                    self.player.setxspeed(keyspeed)
                elif event.key == pygame.K_UP:
                    self.player.setyspeed(-keyspeed)
                elif event.key == pygame.K_DOWN:
                    self.player.setyspeed(keyspeed)
            elif event.type == pygame.KEYUP:
                self.player.unclick()
                if event.key == pygame.K_LEFT:
                    self.player.setxspeed(0)
                elif event.key == pygame.K_RIGHT:
                    self.player.setxspeed(0)
                elif event.key == pygame.K_UP:
                    self.player.setyspeed(0)
                elif event.key == pygame.K_DOWN:
                    self.player.setyspeed(0)
            elif event.type == pygame.JOYAXISMOTION:
#                xaxis = self.caljoy.get_axis_digitized(0)
#                yaxis = self.caljoy.get_axis_digitized(1)
                xaxis = self.caljoy.get_axis_nodrift(0)
                yaxis = self.caljoy.get_axis_nodrift(1)
                if xaxis == 0 and yaxis == 0:
                    # Switching modes midstream isn't working with the calibration code.
                    # For now comment this out so we don't try to switch back
                    # to joystick mode from hat mode
                    # hatmode = False
                    self.player.unclick()
                if not self.hatmode:
                    self.player.setxspeed(xaxis * joyspeed)
                    self.player.setyspeed(yaxis * joyspeed)
            elif event.type == pygame.JOYHATMOTION:
                if not self.hatmode:
                    self.hatmode = True
                    print('Hat mode, joystick input disabled')
                hat = self.caljoy.joystick.get_hat(0)
                print(hat)
                if hat[0] == 0 and hat[1] == 0:
                    self.player.unclick()
                self.player.setxspeed(hat[0] * keyspeed)
                self.player.setyspeed(-hat[1] * keyspeed)
            elif event.type == pygame.JOYBUTTONDOWN:
                self.player.ghost = self.cheat
            elif event.type == pygame.JOYBUTTONUP:
                self.player.ghost = False
        return self.done
    
    def run_logic(self):
        self.player.move(self.room.wall_list)

        # Exited out of maze boundaries
        if self.player.rect.x > self.display_width + 1 or self.player.rect.x < -self.player.width or self.player.rect.y > self.display_height + 1 or self.player.rect.y < -self.player.height:
            self.level += 1
            if self.level > self.last_level:
                self.level = 1
                self.player.setxspeed(0)
                self.player.setyspeed(0)
                self.youwin_screen()
                
            pygame.display.set_caption('PG Maze - Level ' + str(self.level))
            self.num_rows = self.level
            self.num_cols = self.num_rows

            self.cell_width = self.display_width / self.num_cols
            self.cell_height = self.display_height / self.num_rows

            self.room = Room(self.num_rows, self.num_cols, self.cell_width, self.cell_height, self.wall_thickness, self.player)

            self.sounds['charge'].play()
            
    def display_frame(self, screen):            
        # --- Drawing ---
        self.screen.fill(BLACK)

        self.movingsprites.draw(self.screen)
        self.room.wall_list.draw(self.screen)

        pygame.display.flip()
        self.clock.tick(60)

class CalibratedJoystick(object):
    """This class represents a calibrated joystick"""

    # It would be nice if we could inherit from pygame.joystick.Joystick but that doesn't work
    def __init__(self, id):
        """Constructor function"""

        self.joystick = pygame.joystick.Joystick(id)
        self.joystick.init()
        self.numaxes = self.joystick.get_numaxes()
        self.calibrations = [ (0.0, 0.0) for i in range(self.numaxes) ]

    def get_axis(self, axis):
        """Read the specified axis and return a calibrated value in the range -1.0 .. 1.0"""
        value = self.joystick.get_axis(axis)
        (calmin, calmax) = self.calibrations[axis]
        changed = False
        if value < calmin:
            changed = True
            calmin = value
        if value > calmax:
            changed = True
            calmax = value
        if changed:
            self.calibrations[axis] = (calmin, calmax)

        try:
            value = (value - calmin) * 2.0 / (calmax - calmin) - 1.0
        except ZeroDivisionError:
            pass

        return value

    def get_axis_digitized(self, axis):
        """Read the specified axis and return a positional value -1.0, 0, or 1.0"""
        value = self.get_axis(axis)
        threshold = 0.5
        if value < -threshold:
            value = -1.0
        elif value > threshold:
            value = 1.0
        else:
            value = 0.0
        return value

    def get_axis_nodrift(self, axis):
        """Read the specified axis and return an analog positional when outside the threshold"""
        value = self.get_axis(axis)
        threshold = 0.1
        if abs(value) < threshold:
            value = 0
        return value

                    
class Wall(pygame.sprite.Sprite):
    """This class represents the walls of the maze """

    def __init__(self, x, y, width, height, color):
        """ Constructor function """

        # Call the parent's constructor
        super().__init__()

        # Make a wall, of the size and color specified in the parameters
        self.image = pygame.Surface([width, height])
        self.image.fill(color)

        # Make our top-left corner the passed-in location.
        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.x = x

class Player(pygame.sprite.Sprite):
    """ This class represents the moving object that the player controls """

    # Set speed vector
    change_x = 0
    change_y = 0

    def __init__(self, game, x, y, width, height):
        """ Constructor function """

        # Call the parent's constructor
        super().__init__()

        # Game global state
        self.game = game
        
        # Set height, width
        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)
        self.width = width
        self.height = height

        # Make our top-left corner the passed-in location.
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        # Audio channel for click sounds
        self.click_channel = pygame.mixer.Channel(0)

        # Don't click again after wall collision until key-up event
        self.clicked = False

        # Ghost through walls with joystick button press in cheat mode
        self.ghost = False

    def changespeed(self, x, y):
        """ Change the speed of the player. Called with a keypress. """
        self.change_x += x
        self.change_y += y

    def setxspeed(self, speed):
        """ Set the x speed of the player. Called with a keypress. """
        self.change_x = speed

    def setyspeed(self, speed):
        """ Set the y speed of the player. Called with a keypress. """
        self.change_y = speed

    def setpos(self, coord):
        """ Set position of the player. """
        self.rect.x = coord[0]
        self.rect.y = coord[1]

    def move(self, walls):
        """Find a new position for the player and perform collision detection"""
        if self.ghost:
            self.image.fill(GREEN)
        else:
            self.image.fill(WHITE)
            
        collision = False
        
        # Move left/right
        self.rect.x += self.change_x

        # Did this update cause us to hit a wall?
        while True and not self.ghost:
            if not self.change_x:
                break
            block_hit_list = pygame.sprite.spritecollide(self, walls, False)
            if not block_hit_list:
                break
            self.rect.x -= math.copysign(1, self.change_x)
            collision = True
            
        # Move up/down
        self.rect.y += self.change_y

        # Did this update cause us to hit a wall?
        while True and not self.ghost:
            if not self.change_y:
                break
            block_hit_list = pygame.sprite.spritecollide(self, walls, False)
            if not block_hit_list:
                break
            self.rect.y -= math.copysign(1, self.change_y)
            collision = True

        if collision and not self.clicked and not self.click_channel.get_busy():
            self.click_channel.play(self.game.sounds['click'])
            self.clicked = True

    def unclick(self):
        self.clicked = False
            
class Room(object):
    """Room object. Each room has a list of walls."""

    def __init__(self, num_rows, num_cols, cell_width, cell_height, wall_thickness, player):
        """ Constructor, create our lists. """
        self.wall_list = pygame.sprite.Group()
        self.wall_color = random.choice(wall_colors)

        M = maze.generate_maze(num_rows, num_cols, 0, 1)
        
        for row in range(0,num_rows):
            for col in range(0,num_cols):
                cell_data = M[row,col]
                # Make the walls. (x, y, width, height, color)
                # Only make left and top walls for most cells, since border walls are the same in both directions
                # Make right and bottom walls only for the far edges of maze
                if cell_data[0] == 0: # left
                    wall = Wall(col * cell_width, row * cell_height, wall_thickness, cell_height, self.wall_color)
                    self.wall_list.add(wall)
                if cell_data[1] == 0: # top
                    wall = Wall(col * cell_width, row * cell_height, cell_width, wall_thickness, self.wall_color)
                    self.wall_list.add(wall)
                if cell_data[2] == 0 and col == num_cols - 1: # right
                    wall = Wall((col + 1) * cell_width - wall_thickness, row * cell_height, wall_thickness, cell_height, self.wall_color)
                    self.wall_list.add(wall)
                if cell_data[3] == 0 and row == num_rows - 1: # bottom
                    wall = Wall(col * cell_width, (row + 1) * cell_height - wall_thickness, cell_width, wall_thickness, self.wall_color)
                    self.wall_list.add(wall)

        # Move the player to the center of the top-left cell
        player.setpos(((cell_width - player.width) / 2, (cell_height - player.height) / 2))

def usage():
    print("Usage:", sys.argv[0], "[-ch] [-l levelnum] [--cheat] [--help] [--level=levelnum]")
        
def main():
    """ Main program function. """

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--level", type=int, default=1, help="set starting level")
    parser.add_argument("-c", "--cheat", action="store_true", help="enable cheat mode")
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug output")
    args = parser.parse_args()

    # Initialize Pygame and set up the window
    pygame.init()

    # Create our objects and set the data
    clock = pygame.time.Clock()

    # Create an instance of the Game class
    game = Game(args.level, args.cheat)
    game.done = False

    # Main game loop
    while not game.done:

        # Process events (keystrokes, mouse clicks, etc)
        game.done = game.process_events()

        # Update object positions, check for collisions
        game.run_logic()

        # Draw the current frame
        game.display_frame(game.screen)

        # Pause for the next frame
        clock.tick(60)

    # Close window and exit
    pygame.quit()

# Call the main function, start up the game
if __name__ == "__main__":
    main()
