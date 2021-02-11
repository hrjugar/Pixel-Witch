"""
Contains sprite classes and default tile size.
"""

import pygame
from enums import *
from constants import *
from image import *
from sound import *


class LevelSprite(pygame.sprite.Sprite):
    """
    All the sprites seen in a single level.
    """

    def __init__(self, image, x, y, width, height, *groups):
        super().__init__(*groups)
        self.image = pygame.transform.scale(image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))


class Background(LevelSprite):
    """
    Moving background in a single level.
    """

    def __init__(self, width, height, *groups):
        super().__init__(bg_level_img, 0, 0, width, height, *groups)


class Platform(LevelSprite):
    """
    Wall, floor, or obstacles that are able to collide with the player.
    """

    def __init__(self, x, y, *groups):
        super().__init__(platform_img, x, y, tile_size, tile_size, *groups)


class Potion(LevelSprite):
    """
    One-time use items which changes the player's ColorState based on its color.
    """

    def __init__(self, color_state, image, x, y, *groups):
        super().__init__(image, x, y, tile_size, tile_size, *groups)
        self.color_state = color_state


class BluePotion(Potion):
    """
    Potion that gives the player the ability to jump.
    """

    def __init__(self, x, y, *groups):
        super().__init__(ColorState.BLUE, potion_blue_img, x, y, *groups)


class RedPotion(Potion):
    """
    Potion that gives the player the ability to attack.
    """

    def __init__(self, x, y, *groups):
        super().__init__(ColorState.RED, potion_red_img, x, y, *groups)


class YellowPotion(Potion):
    """
    Potion that gives the player a shield.
    """

    def __init__(self, x, y, *groups):
        super().__init__(ColorState.YELLOW, potion_yellow_img, x, y, *groups)


class Gem(LevelSprite):
    """
    Gems that the player collects to gain points.
    """

    def __init__(self, x, y, *groups):
        super().__init__(gem_img, x, y, 20, 20, *groups)  # image is placeholder


class Key(LevelSprite):
    """
    Key to open door and finish the level.
    """

    def __init__(self, x, y, *groups):
        super().__init__(key_img, x, y, 20, 20, *groups)  # image is placeholder


class Enemy(LevelSprite):
    """
    Sprites that results to game over if collided with the player.
    """

    def __init__(self, x, y, *groups):
        super().__init__(enemy_img, x, y, 65, 65, *groups)
        self.move_direction = 1
        self.move_count = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_count += 1
        if self.move_count > 20:
            self.move_direction *= -1
            self.move_count *= -1


class Door(LevelSprite):
    """
    Sprites that finish the level if collided with the player.
    """

    def __init__(self, x, y, *groups):
        super().__init__(door_img, x, y, 48, 48, *groups)


class Fireball(LevelSprite):
    """
    A fireball attack casted by a player when pressing SPACE while in yellow color state.
    """

    def __init__(self, *groups):
        super().__init__(fireball_img, 0, 0, 10, 10, *groups)
        self.attacking = False
        self.move_speed = 5
        self.direction = 0

    def attack(self, level):
        x_movement = self.direction * self.move_speed
        self.rect.x += x_movement
        player_atk_sfx.play()

        # Platform collision
        for platform in level.platforms:
            if platform.rect.colliderect(self.rect) and platform in level.active_sprites:
                enemy_hit_sfx.play()
                self.attacking = False
                return

        # Enemy collision
        for enemy in level.enemies:
            if enemy.rect.colliderect(self.rect) and enemy in level.active_sprites:
                level.active_sprites.remove(enemy)
                self.attacking = False
                enemy_hit_sfx.play()
                return


class Player(pygame.sprite.Sprite):
    """
    The sprite being controlled by the user.
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        # ANIMATION
        self.index = 0
        self.counter = 0
        self.image = player_default_right_images[self.index]

        # DISPLAY
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = 0, 0
        self.width, self.height = self.image.get_width(), self.image.get_height()

        # STATE
        self.current_level = None
        self.has_key = False
        self.color_state = ColorState.WHITE
        self.player_state = PlayerState.ALIVE

        # MOVEMENT
        self.y_vel = 0
        self.jump_cooldown = 0
        self.direction = 1
        self.on_ground = True

        # ABILITY
        self.jump_cooldown = 0
        self.atk_cooldown = 0
        self.fireball = Fireball()
        self.has_shield = False

    def update(self):
        if self.player_state == PlayerState.ALIVE:
            self._refresh_cooldown()
            self._update_fireball()
            x_movement, y_movement = self._move()
            self._animate()
            y_movement = self._gravitate(y_movement)
            x_movement, y_movement, self.player_state = self._collide(x_movement, y_movement)

            # COORD UPDATES
            self.rect.x += x_movement
            self.rect.y += y_movement

    def _refresh_cooldown(self):
        if self.on_ground and self.jump_cooldown > 0:
            self.jump_cooldown -= 1
        if self.atk_cooldown > 0:
            self.atk_cooldown -= 1

    def _update_fireball(self):
        if self.fireball.attacking:
            self.current_level.active_sprites.add(self.fireball)
            self.fireball.attack(self.current_level)
        else:
            self.current_level.active_sprites.remove(self.fireball)
            self.fireball.rect.x, self.fireball.rect.y = self.rect.x + 15, self.rect.y + 10

    def _move(self):
        """
        Moves player based on certain key presses.
        :return: tuple representing x and y movement
        """

        x_movement, y_movement = 0, 0
        keypress = pygame.key.get_pressed()
        if keypress[pygame.K_LEFT] and not keypress[pygame.K_RIGHT]:
            x_movement -= 5
            self.counter += 1
            self.direction = -1
        if keypress[pygame.K_RIGHT] and not keypress[pygame.K_LEFT]:
            x_movement += 5
            self.counter += 1
            self.direction = 1
        if not keypress[pygame.K_LEFT] and not keypress[pygame.K_RIGHT]:
            self.counter = 0
            self.index = 0
            self._display_frame()
        if keypress[pygame.K_SPACE]:
            if self.color_state == ColorState.BLUE and self.on_ground and self.jump_cooldown == 0:
                self.jump_cooldown = fps // 5  # 0.20 second cooldown
                self.on_ground = False
                self.y_vel = -20
                jump_sfx.play()
            elif self.color_state == ColorState.YELLOW and self.atk_cooldown == 0 and not self.fireball.attacking \
                    and self.fireball.rect.x == self.rect.x + 15 and self.fireball.rect.y == self.rect.y + 10:
                self.atk_cooldown = fps  # 1 second cooldown
                self.fireball.attacking = True
                self.fireball.direction = self.direction
                pass

        return x_movement, y_movement

    def _animate(self):
        walk_cooldown = 5
        if self.counter > walk_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(player_default_right_images):
                self.index = 0
            self._display_frame()

    def _gravitate(self, y_movement):
        self.y_vel += 1
        if self.y_vel > 10:
            self.y_vel = 10
        y_movement += self.y_vel
        return y_movement

    def _collide(self, x_movement, y_movement):
        """
        Applies collision with player and other level sprites.
        :return: tuple representing x and y movement and player state
        """
        player_state = PlayerState.ALIVE

        for platform in self.current_level.platforms:
            # X-DIR. COLLISION
            if platform.rect.colliderect(self.rect.x + x_movement, self.rect.y, self.width, self.height):
                x_movement = 0
            # Y-DIR. COLLISION
            if platform.rect.colliderect(self.rect.x, self.rect.y + y_movement, self.width, self.height):
                # check if below the ground i.e. jumping
                if self.y_vel < 0:
                    y_movement = platform.rect.bottom - self.rect.top
                    self.y_vel = 0
                # check if above the ground i.e. falling
                elif self.y_vel >= 0:
                    y_movement = platform.rect.top - self.rect.bottom
                    self.y_vel = 0
                    self.on_ground = True

        # ENEMY COLLISION
        for enemy in self.current_level.enemies:
            if enemy.rect.colliderect(self.rect) and enemy in self.current_level.active_sprites:
                player_state = PlayerState.LOST
                game_over_sfx.play()

        # DOOR COLLISION
        if self.current_level.door.rect.colliderect(self.rect) and self.has_key:
            player_state = PlayerState.WON
            win_sfx.play()

        # CONSUMABLE COLLISION
        for consumable in self.current_level.consumables:
            if consumable.rect.colliderect(self.rect) and consumable in self.current_level.active_sprites:
                if isinstance(consumable, BluePotion):
                    print("BLUE")
                    self.color_state = ColorState.BLUE
                    potion_collect_sfx.play()
                if isinstance(consumable, RedPotion):
                    print("RED")
                    self.color_state = ColorState.RED
                    potion_collect_sfx.play()
                if isinstance(consumable, YellowPotion):
                    print("YELLOW")
                    self.color_state = ColorState.YELLOW
                    potion_collect_sfx.play()
                if isinstance(consumable, Gem):
                    self.current_level.score += 5
                    gem_collect_sfx.play()
                if isinstance(consumable, Key):
                    self.has_key = True
                    key_collect_sfx.play()
                self.current_level.active_sprites.remove(consumable)

        return x_movement, y_movement, player_state

    def _display_frame(self):
        if self.direction == 1:
            if self.color_state == ColorState.WHITE:
                self.image = player_default_right_images[self.index]
            elif self.color_state == ColorState.BLUE:
                self.image = player_jump_right_images[self.index]
            elif self.color_state == ColorState.RED:
                self.image = player_health_right_images[self.index]
            elif self.color_state == ColorState.YELLOW:
                self.image = player_atk_right_images[self.index]
        if self.direction == -1:
            if self.color_state == ColorState.WHITE:
                self.image = player_default_left_images[self.index]
            elif self.color_state == ColorState.BLUE:
                self.image = player_jump_left_images[self.index]
            elif self.color_state == ColorState.RED:
                self.image = player_health_left_images[self.index]
            elif self.color_state == ColorState.YELLOW:
                self.image = player_atk_left_images[self.index]

    def reset(self, x, y, level):
        # ANIMATION AND DISPLAY
        self.image = player_default_right_images[0]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # STATE
        self.current_level = level
        self.has_key = False
        self.color_state = ColorState.WHITE
        self.player_state = PlayerState.ALIVE

        # MOVEMENT
        self.y_vel = 0
        self.direction = 1
        self.on_ground = True

        # ABILITY
        self.jump_cooldown = 0
        self.atk_cooldown = 0
        self.has_shield = False