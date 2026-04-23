import os
import random
import math
import pygame
import json
from os import listdir
from os.path import isfile, join
from enum import Enum

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# =============================================================================
# GLOBAL CONSTANTS - Game Configuration
# =============================================================================

# Window dimensions
WIDTH, HEIGHT = 1280, 830

# Frames per second
FPS = 60

# Create game window
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultimate Platformer - Extreme Edition")

# =============================================================================
# GAME STATE ENUM
# =============================================================================

class GameState(Enum):
    """Enumeration for different game states"""
    MAIN_MENU = 1
    DIFFICULTY_SELECT = 2
    LEVEL_SELECT = 3
    PLAYING = 4
    PAUSED = 5
    GAME_OVER = 6
    LEVEL_COMPLETE = 7
    VICTORY = 8

# =============================================================================
# DIFFICULTY SETTINGS
# =============================================================================

class Difficulty:
    """Difficulty settings that affect gameplay"""
    
    EASY = {
        "name": "EASY",
        "player_health": 150,
        "player_speed": 6,
        "enemy_speed_multiplier": 0.7,
        "enemy_damage_multiplier": 0.5,
        "fire_damage": 10,
        "spike_damage": 15,
        "saw_damage": 20,
        "enemy_contact_damage": 10,
        "projectile_damage": 15,
        "fall_damage_threshold": 25,
        "fall_damage_multiplier": 1.5,
        "color": (0, 255, 0)
    }
    
    NORMAL = {
        "name": "NORMAL",
        "player_health": 100,
        "player_speed": 5,
        "enemy_speed_multiplier": 1.0,
        "enemy_damage_multiplier": 1.0,
        "fire_damage": 15,
        "spike_damage": 25,
        "saw_damage": 30,
        "enemy_contact_damage": 20,
        "projectile_damage": 25,
        "fall_damage_threshold": 20,
        "fall_damage_multiplier": 2.0,
        "color": (255, 255, 0)
    }
    
    HARD = {
        "name": "HARD",
        "player_health": 100,
        "player_speed": 5,
        "enemy_speed_multiplier": 1.3,
        "enemy_damage_multiplier": 1.5,
        "fire_damage": 25,
        "spike_damage": 35,
        "saw_damage": 45,
        "enemy_contact_damage": 30,
        "projectile_damage": 35,
        "fall_damage_threshold": 15,
        "fall_damage_multiplier": 2.5,
        "color": (255, 0, 0)
    }

# Default difficulty
CURRENT_DIFFICULTY = Difficulty.NORMAL

# Damage cooldown
DAMAGE_COOLDOWN = 60

# Death zone
DEATH_ZONE_Y = HEIGHT + 200

# Power-up durations (in frames)
SPEED_BOOST_DURATION = 300
INVINCIBILITY_DURATION = 180

# =============================================================================
# UTILITY FUNCTIONS - Sprite Loading and Manipulation
# =============================================================================

def flip(sprites):
    """Flip a list of sprites horizontally"""
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    """Load sprite sheets from the assets folder"""
    path = join("assets", dir1, dir2)
    
    # Check if path exists
    if not os.path.exists(path):
        # Return empty dict if assets not found
        return {}
    
    images = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size, offset_x=96, offset_y=0):
    """Extract a terrain block from the terrain sprite sheet"""
    path = join("assets", "Terrain", "Terrain.png")
    
    if not os.path.exists(path):
        # Create a placeholder surface
        surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
        surface.fill((100, 100, 100))
        return pygame.transform.scale2x(surface)
    
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(offset_x, offset_y, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)

def get_background(name):
    """Load and tile a background image"""
    path = join("assets", "background", name)
    
    if not os.path.exists(path):
        # Create gradient background
        image = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            color = int(135 + (y / HEIGHT) * 100)
            pygame.draw.line(image, (color, color // 2, color // 3), (0, y), (WIDTH, y))
        return [(0, 0)], image
    
    image = pygame.image.load(path).convert()
    image_rect = image.get_rect()
    width = image_rect.width
    height = image_rect.height
    
    tiles = []
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

# =============================================================================
# PARTICLE SYSTEM
# =============================================================================

class Particle:
    """Simple particle for visual effects"""
    
    def __init__(self, x, y, color, vel_x, vel_y, lifetime=30):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)
    
    def update(self):
        """Update particle physics"""
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.3  # Gravity
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, win, offset_x):
        """Draw particle with fading alpha"""
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, alpha)
        pygame.draw.circle(s, color_with_alpha, (self.size, self.size), self.size)
        win.blit(s, (int(self.x) - offset_x, int(self.y)))

class ParticleSystem:
    """Manages all particles in the game"""
    
    def __init__(self):
        self.particles = []
    
    def emit(self, x, y, color, count=10):
        """Emit particles from a position"""
        for _ in range(count):
            vel_x = random.uniform(-3, 3)
            vel_y = random.uniform(-5, -1)
            self.particles.append(Particle(x, y, color, vel_x, vel_y))
    
    def update(self):
        """Update all particles"""
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, win, offset_x):
        """Draw all particles"""
        for particle in self.particles:
            particle.draw(win, offset_x)
    
    def clear(self):
        """Clear all particles"""
        self.particles.clear()

# =============================================================================
# PLAYER CLASS
# =============================================================================

class Player(pygame.sprite.Sprite):
    """Enhanced player with power-ups and improved mechanics"""
    
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, difficulty):
        super().__init__()
        
        # Position and hitbox
        self.rect = pygame.Rect(x, y, width, height)
        self.start_x = x
        self.start_y = y
        
        # Velocity
        self.x_vel = 0
        self.y_vel = 0
        self.base_speed = difficulty["player_speed"]
        
        # Collision
        self.mask = None
        
        # Animation
        self.direction = "left"
        self.animation_count = 0
        
        # Physics
        self.fall_count = 0
        self.jump_count = 0
        
        # Health system
        self.max_health = difficulty["player_health"]
        self.health = self.max_health
        self.is_dead = False
        
        # Damage system
        self.hit = False
        self.hit_count = 0
        self.damage_cooldown = 0
        
        # Fall damage
        self.max_fall_speed = 0
        
        # Power-ups
        self.speed_boost_timer = 0
        self.invincibility_timer = 0
        
        # Stats
        self.coins_collected = 0
        self.enemies_defeated = 0
        
        # Difficulty reference
        self.difficulty = difficulty

    def jump(self):
        """Make the player jump"""
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        """Move the player by delta"""
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        """Trigger hit animation"""
        self.hit = True

    def take_damage(self, amount):
        """Apply damage to player"""
        # Invincibility from power-up
        if self.invincibility_timer > 0:
            return
        
        if self.damage_cooldown <= 0 and not self.is_dead:
            self.health -= amount
            self.damage_cooldown = DAMAGE_COOLDOWN
            self.make_hit()
            
            if self.health <= 0:
                self.health = 0
                self.is_dead = True

    def heal(self, amount):
        """Heal the player"""
        self.health = min(self.health + amount, self.max_health)

    def add_speed_boost(self):
        """Activate speed boost power-up"""
        self.speed_boost_timer = SPEED_BOOST_DURATION

    def add_invincibility(self):
        """Activate invincibility power-up"""
        self.invincibility_timer = INVINCIBILITY_DURATION

    def collect_coin(self):
        """Collect a coin"""
        self.coins_collected += 1

    def respawn(self):
        """Respawn the player"""
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.health = self.max_health
        self.is_dead = False
        self.x_vel = 0
        self.y_vel = 0
        self.fall_count = 0
        self.jump_count = 0
        self.damage_cooldown = 0
        self.hit = False
        self.hit_count = 0
        self.max_fall_speed = 0
        self.speed_boost_timer = 0
        self.invincibility_timer = 0

    def move_left(self, vel):
        """Move left"""
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        """Move right"""
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def get_current_speed(self):
        """Get current speed including power-ups"""
        speed = self.base_speed
        if self.speed_boost_timer > 0:
            speed *= 1.5
        return speed

    def loop(self, fps):
        """Update player every frame"""
        # Apply gravity
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        
        # Track max fall speed
        if self.y_vel > self.max_fall_speed:
            self.max_fall_speed = self.y_vel
        
        # Move
        self.move(self.x_vel, self.y_vel)

        # Update hit animation
        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 0.5:
            self.hit = False
            self.hit_count = 0

        # Update cooldowns
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
        
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= 1
        
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

        self.fall_count += 1
        self.update_sprite()
        
        # Check death zone
        if self.rect.y > DEATH_ZONE_Y:
            self.is_dead = True
            self.health = 0

    def landed(self):
        """Called when player lands"""
        # Fall damage
        if self.max_fall_speed > self.difficulty["fall_damage_threshold"]:
            damage = int((self.max_fall_speed - self.difficulty["fall_damage_threshold"]) * 
                        self.difficulty["fall_damage_multiplier"])
            self.take_damage(damage)
        
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
        self.max_fall_speed = 0

    def hit_head(self):
        """Called when player hits head"""
        self.fall_count = 0
        self.y_vel *= -1

    def update_sprite(self):
        """Update sprite based on state"""
        sprite_sheet = "idle"
        
        if not self.SPRITES:
            # Fallback if sprites not loaded
            self.sprite = pygame.Surface((50, 50), pygame.SRCALPHA)
            self.sprite.fill((255, 0, 0))
            self.update()
            return
        
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES.get(sprite_sheet_name, self.SPRITES.get("idle_" + self.direction, []))
        
        if sprites:
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.sprite = sprites[sprite_index]
            self.animation_count += 1
        else:
            self.sprite = pygame.Surface((50, 50), pygame.SRCALPHA)
            self.sprite.fill((255, 0, 0))
        
        self.update()

    def update(self):
        """Update rect and mask"""
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        """Draw player with effects"""
        # Invincibility glow
        if self.invincibility_timer > 0:
            # Rainbow effect
            hue = (pygame.time.get_ticks() // 50) % 360
            color = pygame.Color(0)
            color.hsva = (hue, 100, 100, 50)
            glow = self.sprite.copy()
            glow.fill(color, special_flags=pygame.BLEND_RGBA_ADD)
            win.blit(glow, (self.rect.x - offset_x, self.rect.y))
        # Damage flash
        elif self.damage_cooldown > 0 and self.damage_cooldown % 10 < 5:
            flash = self.sprite.copy()
            flash.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_ADD)
            win.blit(flash, (self.rect.x - offset_x, self.rect.y))
        else:
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
        
        # Speed boost indicator
        if self.speed_boost_timer > 0:
            # Draw speed lines
            for i in range(3):
                offset = i * 10
                alpha = 100 - i * 30
                surf = pygame.Surface((20, 2), pygame.SRCALPHA)
                surf.fill((255, 255, 0, alpha))
                win.blit(surf, (self.rect.x - offset_x - 25 - offset, self.rect.y + 20 + i * 5))

# =============================================================================
# ENEMY CLASSES
# =============================================================================

class Enemy(pygame.sprite.Sprite):
    """Base enemy class"""
    
    def __init__(self, x, y, width, height, enemy_type="ground"):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.enemy_type = enemy_type
        self.health = 50
        self.max_health = 50
        self.is_dead = False
        self.direction = 1  # 1 for right, -1 for left
        self.speed = 2
        self.animation_count = 0
        
    def take_damage(self, amount):
        """Enemy takes damage"""
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_dead = True
            return True
        return False
    
    def update(self, player, objects):
        """Update enemy AI - override in subclasses"""
        pass
    
    def draw(self, win, offset_x):
        """Draw enemy"""
        # Draw health bar
        if self.health < self.max_health:
            bar_width = 40
            bar_height = 5
            bar_x = self.rect.x - offset_x + (self.rect.width - bar_width) // 2
            bar_y = self.rect.y - 10
            
            pygame.draw.rect(win, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            health_width = int(bar_width * (self.health / self.max_health))
            pygame.draw.rect(win, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))

class GroundEnemy(Enemy):
    """Ground patrolling enemy"""
    
    def __init__(self, x, y, patrol_distance=200):
        super().__init__(x, y, 40, 40, "ground")
        self.start_x = x
        self.patrol_distance = patrol_distance
        self.speed = 2
        self.color = (255, 100, 100)
        
    def update(self, player, objects):
        """Patrol back and forth"""
        if self.is_dead:
            return
        
        # Move
        self.rect.x += self.speed * self.direction
        
        # Check patrol boundaries
        if abs(self.rect.x - self.start_x) > self.patrol_distance:
            self.direction *= -1
        
        # Check collision with blocks
        for obj in objects:
            if isinstance(obj, Block) and self.rect.colliderect(obj.rect):
                if self.direction > 0:
                    self.rect.right = obj.rect.left
                else:
                    self.rect.left = obj.rect.right
                self.direction *= -1
                break
    
    def draw(self, win, offset_x):
        """Draw ground enemy"""
        pygame.draw.rect(win, self.color, 
                        (self.rect.x - offset_x, self.rect.y, self.rect.width, self.rect.height))
        pygame.draw.rect(win, (0, 0, 0), 
                        (self.rect.x - offset_x, self.rect.y, self.rect.width, self.rect.height), 2)
        super().draw(win, offset_x)

class FlyingEnemy(Enemy):
    """Flying enemy that follows player"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 35, 35, "flying")
        self.speed = 1.5
        self.color = (100, 100, 255)
        self.float_offset = 0
        
    def update(self, player, objects):
        """Follow player"""
        if self.is_dead:
            return
        
        # Calculate direction to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0 and distance < 400:  # Detection range
            # Normalize and move
            dx = dx / distance * self.speed
            dy = dy / distance * self.speed
            self.rect.x += dx
            self.rect.y += dy
        
        # Floating animation
        self.float_offset += 0.1
    
    def draw(self, win, offset_x):
        """Draw flying enemy"""
        float_y = int(math.sin(self.float_offset) * 5)
        pygame.draw.circle(win, self.color, 
                          (self.rect.centerx - offset_x, self.rect.centery + float_y), 
                          self.rect.width // 2)
        pygame.draw.circle(win, (0, 0, 0), 
                          (self.rect.centerx - offset_x, self.rect.centery + float_y), 
                          self.rect.width // 2, 2)
        super().draw(win, offset_x)

class ShootingEnemy(Enemy):
    """Stationary enemy that shoots projectiles"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 45, 45, "shooter")
        self.shoot_cooldown = 0
        self.shoot_delay = 120  # Frames between shots
        self.projectiles = []
        self.color = (255, 150, 0)
        
    def update(self, player, objects):
        """Shoot at player"""
        if self.is_dead:
            return
        
        # Update projectiles
        for proj in self.projectiles[:]:
            proj.update()
            if proj.is_dead:
                self.projectiles.remove(proj)
        
        # Shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        else:
            # Check if player in range
            distance = abs(player.rect.centerx - self.rect.centerx)
            if distance < 500:
                # Shoot
                self.shoot(player)
                self.shoot_cooldown = self.shoot_delay
    
    def shoot(self, player):
        """Create a projectile aimed at player"""
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            speed = 5
            vel_x = (dx / distance) * speed
            vel_y = (dy / distance) * speed
            proj = Projectile(self.rect.centerx, self.rect.centery, vel_x, vel_y)
            self.projectiles.append(proj)
    
    def draw(self, win, offset_x):
        """Draw shooter enemy"""
        # Draw body
        pygame.draw.rect(win, self.color, 
                        (self.rect.x - offset_x, self.rect.y, self.rect.width, self.rect.height))
        pygame.draw.rect(win, (0, 0, 0), 
                        (self.rect.x - offset_x, self.rect.y, self.rect.width, self.rect.height), 2)
        
        # Draw cannon
        cannon_rect = pygame.Rect(self.rect.centerx - offset_x - 5, self.rect.centery - 3, 15, 6)
        pygame.draw.rect(win, (50, 50, 50), cannon_rect)
        
        # Draw projectiles
        for proj in self.projectiles:
            proj.draw(win, offset_x)
        
        super().draw(win, offset_x)

class Projectile:
    """Enemy projectile"""
    
    def __init__(self, x, y, vel_x, vel_y):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.radius = 5
        self.is_dead = False
        self.lifetime = 180  # 3 seconds
        
    def update(self):
        """Update projectile position"""
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifetime -= 1
        
        if self.lifetime <= 0:
            self.is_dead = True
    
    def get_rect(self):
        """Get collision rect"""
        return pygame.Rect(self.x - self.radius, self.y - self.radius, 
                          self.radius * 2, self.radius * 2)
    
    def draw(self, win, offset_x):
        """Draw projectile"""
        pygame.draw.circle(win, (255, 200, 0), 
                          (int(self.x) - offset_x, int(self.y)), self.radius)
        pygame.draw.circle(win, (255, 100, 0), 
                          (int(self.x) - offset_x, int(self.y)), self.radius - 2)

# =============================================================================
# OBJECT CLASSES
# =============================================================================

class Object(pygame.sprite.Sprite):
    """Base object class"""
    
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        """Draw object"""
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    """Solid terrain block"""
    
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    """Fire trap - damages player"""
    
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        
        if self.fire and "off" in self.fire:
            self.image = self.fire["off"][0]
        else:
            # Fallback
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
            self.image.fill((255, 100, 0))
        
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        """Update animation"""
        if not self.fire or self.animation_name not in self.fire:
            return
        
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Spike(Object):
    """Spike trap - more damage than fire"""
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "spike")
        # Create spike visual
        self.image.fill((0, 0, 0, 0))
        points = [
            (width // 2, 0),
            (width, height),
            (0, height)
        ]
        pygame.draw.polygon(self.image, (150, 150, 150), points)
        pygame.draw.polygon(self.image, (100, 100, 100), points, 2)
        self.mask = pygame.mask.from_surface(self.image)

class Saw(Object):
    """Rotating saw trap"""
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "saw")
        self.angle = 0
        self.base_image = self.create_saw_image(width)
        self.image = self.base_image.copy()
        self.mask = pygame.mask.from_surface(self.image)
    
    def create_saw_image(self, size):
        """Create saw blade visual"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Draw blade
        pygame.draw.circle(surf, (180, 180, 180), (center, center), center)
        pygame.draw.circle(surf, (150, 150, 150), (center, center), center - 3)
        
        # Draw teeth
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = center + int(math.cos(angle) * (center - 5))
            y1 = center + int(math.sin(angle) * (center - 5))
            x2 = center + int(math.cos(angle) * center)
            y2 = center + int(math.sin(angle) * center)
            pygame.draw.line(surf, (100, 100, 100), (x1, y1), (x2, y2), 3)
        
        # Center
        pygame.draw.circle(surf, (80, 80, 80), (center, center), 5)
        
        return surf
    
    def loop(self):
        """Rotate saw"""
        self.angle = (self.angle + 5) % 360
        self.image = pygame.transform.rotate(self.base_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

class MovingPlatform(Object):
    """Platform that moves back and forth"""
    
    def __init__(self, x, y, width, height, move_range, speed, vertical=False):
        super().__init__(x, y, width, height, "platform")
        self.start_pos = x if not vertical else y
        self.move_range = move_range
        self.speed = speed
        self.direction = 1
        self.vertical = vertical
        
        # Create platform visual
        block = get_block(height)
        for i in range(width // height):
            self.image.blit(block, (i * height, 0))
        self.mask = pygame.mask.from_surface(self.image)
    
    def loop(self):
        """Update platform movement"""
        if self.vertical:
            self.rect.y += self.speed * self.direction
            if abs(self.rect.y - self.start_pos) >= self.move_range:
                self.direction *= -1
                self.rect.y += self.speed * self.direction
        else:
            self.rect.x += self.speed * self.direction
            if abs(self.rect.x - self.start_pos) >= self.move_range:
                self.direction *= -1
                self.rect.x += self.speed * self.direction

class Collectible(Object):
    """Collectible item (coin/gem)"""
    
    def __init__(self, x, y, item_type="coin"):
        super().__init__(x, y, 30, 30, item_type)
        self.item_type = item_type
        self.animation_count = 0
        self.collected = False
        self.create_visual()
    
    def create_visual(self):
        """Create visual for collectible"""
        if self.item_type == "coin":
            pygame.draw.circle(self.image, (255, 215, 0), (15, 15), 12)
            pygame.draw.circle(self.image, (255, 180, 0), (15, 15), 12, 2)
            font = pygame.font.Font(None, 20)
            text = font.render("$", True, (200, 150, 0))
            self.image.blit(text, (8, 5))
        elif self.item_type == "health":
            pygame.draw.rect(self.image, (255, 0, 0), (5, 12, 20, 6))
            pygame.draw.rect(self.image, (255, 0, 0), (12, 5, 6, 20))
            pygame.draw.rect(self.image, (200, 0, 0), (5, 12, 20, 6), 2)
            pygame.draw.rect(self.image, (200, 0, 0), (12, 5, 6, 20), 2)
        
        self.mask = pygame.mask.from_surface(self.image)
    
    def loop(self):
        """Animate collectible"""
        self.animation_count += 1
        offset = int(math.sin(self.animation_count * 0.1) * 5)
        self.rect.y += offset - int(math.sin((self.animation_count - 1) * 0.1) * 5)

class PowerUp(Object):
    """Power-up item"""
    
    def __init__(self, x, y, power_type):
        super().__init__(x, y, 35, 35, power_type)
        self.power_type = power_type
        self.animation_count = 0
        self.collected = False
        self.create_visual()
    
    def create_visual(self):
        """Create visual for power-up"""
        if self.power_type == "speed":
            pygame.draw.polygon(self.image, (0, 255, 255), 
                              [(5, 17), (25, 5), (25, 30)])
            pygame.draw.polygon(self.image, (0, 200, 200), 
                              [(5, 17), (25, 5), (25, 30)], 2)
        elif self.power_type == "invincibility":
            pygame.draw.circle(self.image, (255, 0, 255), (17, 17), 12)
            pygame.draw.circle(self.image, (200, 0, 200), (17, 17), 12, 2)
            pygame.draw.circle(self.image, (255, 100, 255), (17, 17), 6)
        
        self.mask = pygame.mask.from_surface(self.image)
    
    def loop(self):
        """Animate power-up"""
        self.animation_count += 1
        offset = int(math.sin(self.animation_count * 0.15) * 3)
        self.rect.y += offset - int(math.sin((self.animation_count - 1) * 0.15) * 3)

class Goal(Object):
    """Level end goal"""
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "goal")
        self.animation_count = 0
        self.create_visual()
    
    def create_visual(self):
        """Create flag/goal visual"""
        # Pole
        pygame.draw.rect(self.image, (100, 50, 0), (5, 0, 8, self.height))
        
        # Flag
        points = [(13, 10), (13, 40), (60, 25)]
        pygame.draw.polygon(self.image, (0, 255, 0), points)
        pygame.draw.polygon(self.image, (0, 200, 0), points, 2)
        
        self.mask = pygame.mask.from_surface(self.image)
    
    def loop(self):
        """Animate flag"""
        self.animation_count += 1

# =============================================================================
# LEVEL SYSTEM
# =============================================================================

class Level:
    """Level configuration"""
    
    def __init__(self, level_num, difficulty):
        self.level_num = level_num
        self.difficulty = difficulty
        self.block_size = 96
        self.player_start = (100, 100)
        self.objects = []
        self.enemies = []
        self.collectibles = []
        self.powerups = []
        self.background_name = "Brown.png"
        self.goal = None
        self.time_limit = 300  # 5 minutes in seconds
        
        self.build_level()
    
    def build_level(self):
        """Build level based on level number"""
        # Different levels have different layouts
        if self.level_num == 1:
            self.build_level_1()
        elif self.level_num == 2:
            self.build_level_2()
        elif self.level_num == 3:
            self.build_level_3()
        elif self.level_num == 4:
            self.build_level_4()
        elif self.level_num == 5:
            self.build_level_5()
        elif self.level_num == 6:
            self.build_level_6()
        elif self.level_num == 7:
            self.build_level_7()
        elif self.level_num == 8:
            self.build_level_8()
        elif self.level_num == 9:
            self.build_level_9()
        elif self.level_num == 10:
            self.build_level_10()
    
    def build_level_1(self):
        """Tutorial level - Basic platforming"""
        bs = self.block_size
        
        # Floor
        for i in range(-WIDTH // bs, 150):
            if not (10 <= i <= 13 or 25 <= i <= 28):
                self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Simple platforms
        for i in range(5):
            self.objects.append(Block((15 + i * 4) * bs, HEIGHT - (2 + i) * bs, bs))
        
        # Coins
        for i in range(10):
            self.collectibles.append(Collectible((5 + i * 3) * bs, HEIGHT - 5 * bs))
        
        # Health pack
        self.collectibles.append(Collectible(30 * bs, HEIGHT - 3 * bs, "health"))
        
        # Fire hazards
        self.objects.append(Fire(20 * bs, HEIGHT - bs - 64, 16, 32))
        self.objects[-1].on()
        
        # Goal
        self.goal = Goal(140 * bs, HEIGHT - 4 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_2(self):
        """Enemy introduction"""
        bs = self.block_size
        
        # Floor with gaps
        for i in range(-WIDTH // bs, 120):
            if not (15 <= i <= 18 or 35 <= i <= 38 or 55 <= i <= 57):
                self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Platforms
        for i in range(10):
            self.objects.append(Block((20 + i * 5) * bs, HEIGHT - (3 + (i % 3)) * bs, bs))
        
        # Ground enemies
        self.enemies.append(GroundEnemy(10 * bs, HEIGHT - 2 * bs, 300))
        self.enemies.append(GroundEnemy(30 * bs, HEIGHT - 2 * bs, 200))
        self.enemies.append(GroundEnemy(60 * bs, HEIGHT - 2 * bs, 400))
        
        # Spikes
        for i in range(5):
            self.objects.append(Spike((25 + i) * bs, HEIGHT - bs - 32, 32, 32))
        
        # Power-up
        self.powerups.append(PowerUp(45 * bs, HEIGHT - 5 * bs, "speed"))
        
        # Coins
        for i in range(15):
            self.collectibles.append(Collectible((8 + i * 4) * bs, HEIGHT - 6 * bs))
        
        # Goal
        self.goal = Goal(110 * bs, HEIGHT - 3 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_3(self):
        """Flying enemies and vertical movement"""
        bs = self.block_size
        
        # Floor
        for i in range(-WIDTH // bs, 130):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Vertical tower
        for j in range(2, 9):
            self.objects.append(Block(20 * bs, HEIGHT - j * bs, bs))
            self.objects.append(Block(30 * bs, HEIGHT - j * bs, bs))
        
        # Platforms inside tower
        for i in range(1, 10):
            if i % 2 == 0:
                self.objects.append(Block((21 + (i % 3)) * bs, HEIGHT - i * bs, bs))
        
        # Flying enemies
        self.enemies.append(FlyingEnemy(25 * bs, HEIGHT - 5 * bs))
        self.enemies.append(FlyingEnemy(27 * bs, HEIGHT - 7 * bs))
        self.enemies.append(FlyingEnemy(50 * bs, HEIGHT - 4 * bs))
        
        # Saws
        self.objects.append(Saw(40 * bs, HEIGHT - 3 * bs, 48, 48))
        self.objects.append(Saw(60 * bs, HEIGHT - 4 * bs, 48, 48))
        
        # Collectibles
        for i in range(20):
            self.collectibles.append(Collectible((10 + i * 3) * bs, HEIGHT - (3 + i % 5) * bs))
        
        # Invincibility
        self.powerups.append(PowerUp(25 * bs, HEIGHT - 8 * bs, "invincibility"))
        
        # Goal
        self.goal = Goal(120 * bs, HEIGHT - 2 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_4(self):
        """Moving platforms"""
        bs = self.block_size
        
        # Floor with big gaps
        for i in range(-WIDTH // bs, 20):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        for i in range(100, 140):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Moving platforms
        for i in range(8):
            plat = MovingPlatform((25 + i * 10) * bs, HEIGHT - (3 + i % 2) * bs, 
                                 bs * 2, bs, 200, 2)
            self.objects.append(plat)
        
        # Vertical moving platforms
        for i in range(3):
            plat = MovingPlatform((50 + i * 15) * bs, HEIGHT - 5 * bs, 
                                 bs * 2, bs, 300, 2, vertical=True)
            self.objects.append(plat)
        
        # Fire on platforms
        fire = Fire(30 * bs, HEIGHT - 4 * bs - 64, 16, 32)
        fire.on()
        self.objects.append(fire)
        
        # Enemies
        self.enemies.append(FlyingEnemy(40 * bs, HEIGHT - 5 * bs))
        self.enemies.append(FlyingEnemy(70 * bs, HEIGHT - 6 * bs))
        
        # Coins in air
        for i in range(25):
            self.collectibles.append(Collectible((25 + i * 3) * bs, HEIGHT - (4 + i % 4) * bs))
        
        # Goal
        self.goal = Goal(130 * bs, HEIGHT - 2 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_5(self):
        """Shooter enemies gauntlet"""
        bs = self.block_size
        
        # Long floor
        for i in range(-WIDTH // bs, 150):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Cover platforms
        for i in range(20):
            x = (10 + i * 5) * bs
            height = 2 + (i % 3)
            self.objects.append(Block(x, HEIGHT - height * bs, bs))
            self.objects.append(Block(x + bs, HEIGHT - height * bs, bs))
        
        # Shooter enemies on pillars
        for i in range(10):
            x = (15 + i * 10) * bs
            # Pillar
            for j in range(2, 6):
                self.objects.append(Block(x, HEIGHT - j * bs, bs))
            # Shooter on top
            self.enemies.append(ShootingEnemy(x, HEIGHT - 7 * bs))
        
        # Health packs
        for i in range(5):
            self.collectibles.append(Collectible((20 + i * 15) * bs, HEIGHT - 2 * bs, "health"))
        
        # Power-ups
        self.powerups.append(PowerUp(50 * bs, HEIGHT - 2 * bs, "invincibility"))
        self.powerups.append(PowerUp(100 * bs, HEIGHT - 2 * bs, "speed"))
        
        # Goal
        self.goal = Goal(140 * bs, HEIGHT - 2 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_6(self):
        """Spike maze"""
        bs = self.block_size
        
        # Floor
        for i in range(-WIDTH // bs, 160):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Spike patterns
        for i in range(50):
            if i % 3 != 0:
                self.objects.append(Spike((10 + i) * bs, HEIGHT - bs - 32, 32, 32))
        
        # Safe platforms above spikes
        for i in range(15):
            x = (12 + i * 3) * bs
            y = HEIGHT - (3 + i % 2) * bs
            self.objects.append(Block(x, y, bs))
        
        # Saw obstacles
        for i in range(8):
            self.objects.append(Saw((20 + i * 10) * bs, HEIGHT - 5 * bs, 48, 48))
        
        # Flying enemies
        for i in range(6):
            self.enemies.append(FlyingEnemy((25 + i * 15) * bs, HEIGHT - 4 * bs))
        
        # Coins high up
        for i in range(30):
            self.collectibles.append(Collectible((15 + i * 2) * bs, HEIGHT - 7 * bs))
        
        # Health scattered
        for i in range(4):
            self.collectibles.append(Collectible((30 + i * 20) * bs, HEIGHT - 4 * bs, "health"))
        
        # Goal
        self.goal = Goal(150 * bs, HEIGHT - 2 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_7(self):
        """Vertical climb challenge"""
        bs = self.block_size
        
        # Small starting floor
        for i in range(-WIDTH // bs, 15):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Vertical zigzag climb
        for level in range(1, 12):
            direction = 1 if level % 2 == 0 else -1
            start_x = 20 if level % 2 == 0 else 5
            
            for i in range(5):
                x = (start_x + i * direction * 2) * bs
                y = HEIGHT - (level * 2) * bs
                self.objects.append(Block(x, y, bs))
            
            # Enemy on some platforms
            if level % 3 == 0:
                self.enemies.append(GroundEnemy(start_x * bs, y - bs, 200))
        
        # Top platform
        for i in range(20):
            self.objects.append(Block((10 + i) * bs, HEIGHT - 25 * bs, bs))
        
        # Flying enemies going up and down
        for i in range(8):
            self.enemies.append(FlyingEnemy(15 * bs, HEIGHT - (3 + i * 3) * bs))
        
        # Collectibles
        for level in range(2, 12, 2):
            self.collectibles.append(Collectible(12 * bs, HEIGHT - level * 2 * bs - bs))
        
        # Power-ups
        self.powerups.append(PowerUp(15 * bs, HEIGHT - 12 * bs, "invincibility"))
        
        # Goal at top
        self.goal = Goal(20 * bs, HEIGHT - 26 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_8(self):
        """Everything combined - chaos level"""
        bs = self.block_size
        
        # Complex floor pattern
        for i in range(-WIDTH // bs, 200):
            if not (i % 7 in [3, 4]):
                self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Random platform chaos
        random.seed(8)  # Consistent randomness
        for i in range(100):
            x = random.randint(10, 180) * bs
            y = HEIGHT - random.randint(2, 8) * bs
            self.objects.append(Block(x, y, bs))
        
        # All enemy types
        for i in range(10):
            self.enemies.append(GroundEnemy((15 + i * 15) * bs, HEIGHT - 2 * bs, 250))
        for i in range(8):
            self.enemies.append(FlyingEnemy((20 + i * 20) * bs, HEIGHT - 5 * bs))
        for i in range(6):
            self.enemies.append(ShootingEnemy((25 + i * 25) * bs, HEIGHT - 6 * bs))
        
        # All hazards
        for i in range(30):
            if i % 2 == 0:
                fire = Fire((10 + i * 3) * bs, HEIGHT - bs - 64, 16, 32)
                fire.on()
                self.objects.append(fire)
            else:
                self.objects.append(Spike((10 + i * 3) * bs, HEIGHT - bs - 32, 32, 32))
        
        # Saws everywhere
        for i in range(15):
            self.objects.append(Saw((15 + i * 10) * bs, HEIGHT - random.randint(3, 7) * bs, 48, 48))
        
        # Moving platforms
        for i in range(10):
            plat = MovingPlatform((30 + i * 15) * bs, HEIGHT - 4 * bs, bs * 2, bs, 200, 3)
            self.objects.append(plat)
        
        # Many collectibles
        for i in range(50):
            self.collectibles.append(Collectible(random.randint(10, 180) * bs, 
                                                HEIGHT - random.randint(3, 8) * bs))
        
        # Health and power-ups
        for i in range(10):
            self.collectibles.append(Collectible((20 + i * 15) * bs, HEIGHT - 5 * bs, "health"))
        self.powerups.append(PowerUp(50 * bs, HEIGHT - 6 * bs, "speed"))
        self.powerups.append(PowerUp(100 * bs, HEIGHT - 6 * bs, "invincibility"))
        self.powerups.append(PowerUp(150 * bs, HEIGHT - 6 * bs, "speed"))
        
        random.seed()  # Reset seed
        
        # Goal far away
        self.goal = Goal(190 * bs, HEIGHT - 2 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_9(self):
        """Precision platforming"""
        bs = self.block_size
        
        # Starting platform
        for i in range(10):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Single block jumps
        for i in range(50):
            x = (12 + i * 4) * bs
            y = HEIGHT - (2 + (i % 5)) * bs
            self.objects.append(Block(x, y, bs))
            
            # Small spikes between
            if i < 49:
                self.objects.append(Spike((x + bs * 2), y + bs - 32, 32, 32))
        
        # Moving single blocks
        for i in range(10):
            plat = MovingPlatform((50 + i * 12) * bs, HEIGHT - 6 * bs, bs, bs, 150, 2)
            self.objects.append(plat)
        
        # Vertical moving single blocks
        for i in range(8):
            plat = MovingPlatform((100 + i * 10) * bs, HEIGHT - 4 * bs, bs, bs, 
                                 200, 1, vertical=True)
            self.objects.append(plat)
        
        # Flying enemies to increase pressure
        for i in range(12):
            self.enemies.append(FlyingEnemy((20 + i * 15) * bs, HEIGHT - 5 * bs))
        
        # Saws between platforms
        for i in range(20):
            self.objects.append(Saw((15 + i * 8) * bs, HEIGHT - 4 * bs, 48, 48))
        
        # Ending platform
        for i in range(180, 200):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Goal
        self.goal = Goal(195 * bs, HEIGHT - 2 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def build_level_10(self):
        """Final boss level - extreme challenge"""
        bs = self.block_size
        
        # Arena floor
        for i in range(-10, 100):
            self.objects.append(Block(i * bs, HEIGHT - bs, bs))
        
        # Walls
        for j in range(2, 10):
            self.objects.append(Block(-10 * bs, HEIGHT - j * bs, bs))
            self.objects.append(Block(99 * bs, HEIGHT - j * bs, bs))
        
        # Platform arenas at different heights
        for level in [3, 6, 8]:
            for i in range(10, 90, 8):
                for w in range(3):
                    self.objects.append(Block((i + w) * bs, HEIGHT - level * bs, bs))
        
        # MANY enemies
        # Ground patrol
        for i in range(0, 80, 10):
            self.enemies.append(GroundEnemy(i * bs, HEIGHT - 2 * bs, 400))
        
        # Flyers everywhere
        for i in range(20):
            self.enemies.append(FlyingEnemy(random.randint(10, 90) * bs, 
                                           HEIGHT - random.randint(3, 8) * bs))
        
        # Shooter army
        for i in range(10, 90, 8):
            for level in [4, 7]:
                self.enemies.append(ShootingEnemy(i * bs, HEIGHT - level * bs))
        
        # Hazards everywhere
        for i in range(0, 100, 3):
            trap_type = random.choice(['fire', 'spike', 'saw'])
            if trap_type == 'fire':
                fire = Fire(i * bs, HEIGHT - bs - 64, 16, 32)
                fire.on()
                self.objects.append(fire)
            elif trap_type == 'spike':
                self.objects.append(Spike(i * bs, HEIGHT - bs - 32, 32, 32))
            else:
                self.objects.append(Saw(i * bs, HEIGHT - 3 * bs, 48, 48))
        
        # Moving death saws
        for i in range(15):
            plat_saw = Saw((10 + i * 5) * bs, HEIGHT - 5 * bs, 64, 64)
            self.objects.append(plat_saw)
        
        # Moving platforms for survival
        for i in range(12):
            plat = MovingPlatform((15 + i * 7) * bs, HEIGHT - 5 * bs, bs * 2, bs, 250, 3)
            self.objects.append(plat)
        
        # Many health packs (you'll need them)
        for i in range(15):
            self.collectibles.append(Collectible(random.randint(10, 90) * bs, 
                                                HEIGHT - random.randint(2, 8) * bs, "health"))
        
        # Power-ups
        for i in range(5):
            self.powerups.append(PowerUp((20 + i * 15) * bs, HEIGHT - 7 * bs, "invincibility"))
        for i in range(5):
            self.powerups.append(PowerUp((25 + i * 15) * bs, HEIGHT - 4 * bs, "speed"))
        
        # Coins for score
        for i in range(100):
            self.collectibles.append(Collectible(random.randint(10, 90) * bs, 
                                                HEIGHT - random.randint(2, 9) * bs))
        
        # Goal at the end
        self.goal = Goal(95 * bs, HEIGHT - 2 * bs, 64, 96)
        self.objects.append(self.goal)
    
    def get_all_objects(self):
        """Get all objects including collectibles and power-ups"""
        return self.objects + self.collectibles + self.powerups

# =============================================================================
# UI AND MENU SYSTEM
# =============================================================================

class Button:
    """Clickable button"""
    
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def draw(self, win):
        """Draw button"""
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(win, color, self.rect)
        pygame.draw.rect(win, (255, 255, 255), self.rect, 3)
        
        font = pygame.font.Font(None, 48)
        text = font.render(self.text, True, (255, 255, 255))
        text_rect = text.get_rect(center=self.rect.center)
        win.blit(text, text_rect)
    
    def handle_event(self, event):
        """Check if button is clicked"""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class Menu:
    """Base menu class"""
    
    def __init__(self):
        self.buttons = []
    
    def draw(self, win):
        """Draw menu"""
        pass
    
    def handle_event(self, event):
        """Handle menu events"""
        pass

class MainMenu(Menu):
    """Main menu screen"""
    
    def __init__(self):
        super().__init__()
        
        button_width = 400
        button_height = 80
        button_x = WIDTH // 2 - button_width // 2
        
        self.buttons = [
            Button(button_x, 300, button_width, button_height, 
                  "START GAME", (0, 150, 0), (0, 200, 0)),
            Button(button_x, 420, button_width, button_height, 
                  "LEVEL SELECT", (0, 100, 150), (0, 150, 200)),
            Button(button_x, 540, button_width, button_height, 
                  "QUIT", (150, 0, 0), (200, 0, 0))
        ]
    
    def draw(self, win):
        """Draw main menu"""
        # Background gradient
        for y in range(HEIGHT):
            color = int(20 + (y / HEIGHT) * 60)
            pygame.draw.line(win, (color // 3, color // 2, color), (0, y), (WIDTH, y))
        
        # Title
        font_title = pygame.font.Font(None, 120)
        title = font_title.render("ULTIMATE PLATFORMER", True, (255, 215, 0))
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        
        # Title shadow
        shadow = font_title.render("ULTIMATE PLATFORMER", True, (100, 80, 0))
        win.blit(shadow, (title_rect.x + 5, title_rect.y + 5))
        win.blit(title, title_rect)
        
        # Subtitle
        font_sub = pygame.font.Font(None, 36)
        subtitle = font_sub.render("Extreme Edition - 10 Levels of Mayhem", True, (200, 200, 200))
        sub_rect = subtitle.get_rect(center=(WIDTH // 2, 220))
        win.blit(subtitle, sub_rect)
        
        # Buttons
        for button in self.buttons:
            button.draw(win)
    
    def handle_event(self, event):
        """Handle main menu events"""
        if self.buttons[0].handle_event(event):
            return "difficulty_select"
        if self.buttons[1].handle_event(event):
            return "level_select"
        if self.buttons[2].handle_event(event):
            return "quit"
        
        # Also handle mouse motion for all buttons
        for button in self.buttons:
            button.handle_event(event)
        
        return None

class DifficultyMenu(Menu):
    """Difficulty selection menu"""
    
    def __init__(self):
        super().__init__()
        
        button_width = 400
        button_height = 80
        button_x = WIDTH // 2 - button_width // 2
        
        self.buttons = [
            Button(button_x, 300, button_width, button_height, 
                  "EASY", (0, 200, 0), (0, 255, 0)),
            Button(button_x, 410, button_width, button_height, 
                  "NORMAL", (200, 200, 0), (255, 255, 0)),
            Button(button_x, 520, button_width, button_height, 
                  "HARD", (200, 0, 0), (255, 0, 0)),
            Button(button_x, 650, button_width // 2, button_height - 20, 
                  "BACK", (100, 100, 100), (150, 150, 150))
        ]
    
    def draw(self, win):
        """Draw difficulty menu"""
        # Background
        win.fill((30, 30, 50))
        
        # Title
        font_title = pygame.font.Font(None, 100)
        title = font_title.render("SELECT DIFFICULTY", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        win.blit(title, title_rect)
        
        # Difficulty descriptions
        descriptions = [
            "More health, less damage, slower enemies",
            "Balanced gameplay experience",
            "Less health, more damage, faster enemies"
        ]
        
        font_desc = pygame.font.Font(None, 28)
        for i, desc in enumerate(descriptions):
            text = font_desc.render(desc, True, (180, 180, 180))
            text_rect = text.get_rect(center=(WIDTH // 2, 355 + i * 110))
            win.blit(text, text_rect)
        
        # Buttons
        for button in self.buttons:
            button.draw(win)
    
    def handle_event(self, event):
        """Handle difficulty selection"""
        if self.buttons[0].handle_event(event):
            return "easy"
        if self.buttons[1].handle_event(event):
            return "normal"
        if self.buttons[2].handle_event(event):
            return "hard"
        if self.buttons[3].handle_event(event):
            return "back"
        
        for button in self.buttons:
            button.handle_event(event)
        
        return None

class LevelSelectMenu(Menu):
    """Level selection menu"""
    
    def __init__(self, unlocked_levels):
        super().__init__()
        self.unlocked_levels = unlocked_levels
        self.buttons = []
        
        # Create 10 level buttons in 2 rows
        button_width = 120
        button_height = 120
        start_x = WIDTH // 2 - (5 * button_width + 4 * 20) // 2
        
        for i in range(10):
            row = i // 5
            col = i % 5
            x = start_x + col * (button_width + 20)
            y = 250 + row * (button_height + 30)
            
            if i + 1 <= unlocked_levels:
                color = (0, 150, 0)
                hover_color = (0, 200, 0)
            else:
                color = (80, 80, 80)
                hover_color = (100, 100, 100)
            
            button = Button(x, y, button_width, button_height, 
                          str(i + 1), color, hover_color)
            self.buttons.append(button)
        
        # Back button
        self.back_button = Button(WIDTH // 2 - 100, 650, 200, 60, 
                                  "BACK", (100, 100, 100), (150, 150, 150))
    
    def draw(self, win):
        """Draw level select"""
        win.fill((20, 20, 40))
        
        # Title
        font_title = pygame.font.Font(None, 100)
        title = font_title.render("SELECT LEVEL", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 120))
        win.blit(title, title_rect)
        
        # Level buttons
        for i, button in enumerate(self.buttons):
            button.draw(win)
            
            # Lock icon for locked levels
            if i + 1 > self.unlocked_levels:
                font = pygame.font.Font(None, 60)
                lock = font.render("🔒", True, (255, 255, 255))
                lock_rect = lock.get_rect(center=button.rect.center)
                win.blit(lock, lock_rect)
        
        # Back button
        self.back_button.draw(win)
    
    def handle_event(self, event):
        """Handle level selection"""
        for i, button in enumerate(self.buttons):
            if button.handle_event(event) and i + 1 <= self.unlocked_levels:
                return f"level_{i + 1}"
            button.handle_event(event)  # Update hover state
        
        if self.back_button.handle_event(event):
            return "back"
        self.back_button.handle_event(event)
        
        return None

class PauseMenu(Menu):
    """Pause menu overlay"""
    
    def __init__(self):
        super().__init__()
        
        button_width = 350
        button_height = 70
        button_x = WIDTH // 2 - button_width // 2
        
        self.buttons = [
            Button(button_x, 300, button_width, button_height, 
                  "RESUME", (0, 150, 0), (0, 200, 0)),
            Button(button_x, 400, button_width, button_height, 
                  "RESTART LEVEL", (150, 150, 0), (200, 200, 0)),
            Button(button_x, 500, button_width, button_height, 
                  "MAIN MENU", (150, 0, 0), (200, 0, 0))
        ]
    
    def draw(self, win):
        """Draw pause overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        win.blit(overlay, (0, 0))
        
        # Paused text
        font_title = pygame.font.Font(None, 120)
        title = font_title.render("PAUSED", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        win.blit(title, title_rect)
        
        # Buttons
        for button in self.buttons:
            button.draw(win)
    
    def handle_event(self, event):
        """Handle pause menu events"""
        if self.buttons[0].handle_event(event):
            return "resume"
        if self.buttons[1].handle_event(event):
            return "restart"
        if self.buttons[2].handle_event(event):
            return "main_menu"
        
        for button in self.buttons:
            button.handle_event(event)
        
        return None

# =============================================================================
# GAME UI FUNCTIONS
# =============================================================================

def draw_health_bar(window, player, x, y, width, height):
    """Draw player health bar"""
    health_percentage = player.health / player.max_health
    
    if health_percentage > 0.6:
        bar_color = (0, 255, 0)
    elif health_percentage > 0.3:
        bar_color = (255, 255, 0)
    else:
        bar_color = (255, 0, 0)
    
    border_thickness = 3
    pygame.draw.rect(window, (0, 0, 0), (x - border_thickness, y - border_thickness, 
                                          width + border_thickness * 2, height + border_thickness * 2))
    
    pygame.draw.rect(window, (100, 100, 100), (x, y, width, height))
    
    current_width = int(width * health_percentage)
    pygame.draw.rect(window, bar_color, (x, y, current_width, height))
    
    font = pygame.font.Font(None, 32)
    health_text = font.render(f"HP: {int(player.health)}/{player.max_health}", True, (255, 255, 255))
    window.blit(health_text, (x, y - 28))

def draw_game_ui(window, player, level_num, time_remaining, difficulty_name):
    """Draw all game UI elements"""
    # Health bar
    draw_health_bar(window, player, 20, 20, 300, 30)
    
    # Level info
    font = pygame.font.Font(None, 36)
    level_text = font.render(f"LEVEL {level_num}", True, (255, 255, 255))
    window.blit(level_text, (WIDTH - 200, 20))
    
    # Difficulty
    diff_color = CURRENT_DIFFICULTY["color"]
    diff_text = font.render(difficulty_name, True, diff_color)
    window.blit(diff_text, (WIDTH - 200, 60))
    
    # Timer
    minutes = int(time_remaining // 60)
    seconds = int(time_remaining % 60)
    time_text = font.render(f"TIME: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
    window.blit(time_text, (WIDTH - 220, 100))
    
    # Score
    score_text = font.render(f"COINS: {player.coins_collected}", True, (255, 215, 0))
    window.blit(score_text, (20, 70))
    
    # Power-up indicators
    y_offset = 120
    if player.speed_boost_timer > 0:
        boost_text = font.render(f"SPEED BOOST: {player.speed_boost_timer // 60}s", 
                                True, (0, 255, 255))
        window.blit(boost_text, (20, y_offset))
        y_offset += 35
    
    if player.invincibility_timer > 0:
        inv_text = font.render(f"INVINCIBLE: {player.invincibility_timer // 60}s", 
                              True, (255, 0, 255))
        window.blit(inv_text, (20, y_offset))

def draw_game_over(window, player):
    """Draw game over screen"""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    window.blit(overlay, (0, 0))
    
    font_large = pygame.font.Font(None, 100)
    game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
    text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
    window.blit(game_over_text, text_rect)
    
    font_medium = pygame.font.Font(None, 50)
    
    score_text = font_medium.render(f"Coins Collected: {player.coins_collected}", 
                                   True, (255, 215, 0))
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    window.blit(score_text, score_rect)
    
    font_small = pygame.font.Font(None, 40)
    restart_text = font_small.render("Press R to Restart | ESC for Menu", True, (255, 255, 255))
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
    window.blit(restart_text, restart_rect)

def draw_level_complete(window, player, level_num):
    """Draw level complete screen"""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    window.blit(overlay, (0, 0))
    
    font_large = pygame.font.Font(None, 100)
    complete_text = font_large.render("LEVEL COMPLETE!", True, (0, 255, 0))
    text_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
    window.blit(complete_text, text_rect)
    
    font_medium = pygame.font.Font(None, 50)
    
    level_text = font_medium.render(f"Level {level_num} Beaten!", True, (255, 255, 255))
    level_rect = level_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    window.blit(level_text, level_rect)
    
    score_text = font_medium.render(f"Coins: {player.coins_collected}", True, (255, 215, 0))
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    window.blit(score_text, score_rect)
    
    font_small = pygame.font.Font(None, 40)
    if level_num < 10:
        next_text = font_small.render("Press SPACE for Next Level | ESC for Menu", 
                                     True, (255, 255, 255))
    else:
        next_text = font_small.render("You beat all levels! Press ESC for Menu", 
                                     True, (255, 255, 0))
    next_rect = next_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
    window.blit(next_text, next_rect)

# =============================================================================
# COLLISION FUNCTIONS
# =============================================================================

def handle_vertical_collision(player, objects, dy):
    """Handle vertical collisions"""
    collided_objects = []
    
    for obj in objects:
        if isinstance(obj, (Collectible, PowerUp, Goal)):
            continue
            
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects

def collide(player, objects, dx):
    """Check horizontal collision"""
    player.move(dx, 0)
    player.update()
    collided_object = None
    
    for obj in objects:
        if isinstance(obj, (Collectible, PowerUp, Goal)):
            continue
            
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    """Handle player movement"""
    keys = pygame.key.get_pressed()
    player.x_vel = 0
    
    current_speed = player.get_current_speed()
    
    collide_left = collide(player, objects, -current_speed * 2)
    collide_right = collide(player, objects, current_speed * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(current_speed)
    
    if keys[pygame.K_d] and not collide_right:
        player.move_right(current_speed)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    
    to_check = [collide_left, collide_right, *vertical_collide]
    
    for obj in to_check:
        if obj:
            if obj.name == "fire":
                player.take_damage(CURRENT_DIFFICULTY["fire_damage"])
            elif obj.name == "spike":
                player.take_damage(CURRENT_DIFFICULTY["spike_damage"])
            elif obj.name == "saw":
                player.take_damage(CURRENT_DIFFICULTY["saw_damage"])

def check_collectibles(player, collectibles, particles):
    """Check and collect items"""
    for item in collectibles[:]:
        if not item.collected and pygame.sprite.collide_mask(player, item):
            item.collected = True
            collectibles.remove(item)
            
            # Particle effect
            if item.item_type == "coin":
                particles.emit(item.rect.centerx, item.rect.centery, (255, 215, 0), 15)
                player.collect_coin()
            elif item.item_type == "health":
                particles.emit(item.rect.centerx, item.rect.centery, (255, 0, 0), 15)
                player.heal(30)

def check_powerups(player, powerups, particles):
    """Check and collect power-ups"""
    for powerup in powerups[:]:
        if not powerup.collected and pygame.sprite.collide_mask(player, powerup):
            powerup.collected = True
            powerups.remove(powerup)
            
            if powerup.power_type == "speed":
                particles.emit(powerup.rect.centerx, powerup.rect.centery, (0, 255, 255), 20)
                player.add_speed_boost()
            elif powerup.power_type == "invincibility":
                particles.emit(powerup.rect.centerx, powerup.rect.centery, (255, 0, 255), 20)
                player.add_invincibility()

def check_enemies(player, enemies, particles):
    """Check collision with enemies"""
    for enemy in enemies:
        if enemy.is_dead:
            continue
        
        # Check player collision with enemy
        if player.rect.colliderect(enemy.rect):
            player.take_damage(CURRENT_DIFFICULTY["enemy_contact_damage"])
            # Knockback
            if player.rect.centerx < enemy.rect.centerx:
                player.x_vel = -10
            else:
                player.x_vel = 10
        
        # Check shooting enemy projectiles
        if isinstance(enemy, ShootingEnemy):
            for proj in enemy.projectiles:
                if player.rect.colliderect(proj.get_rect()):
                    player.take_damage(CURRENT_DIFFICULTY["projectile_damage"])
                    proj.is_dead = True
                    particles.emit(proj.x, proj.y, (255, 100, 0), 10)

def check_goal(player, goal):
    """Check if player reached goal"""
    if goal and pygame.sprite.collide_mask(player, goal):
        return True
    return False

# =============================================================================
# MAIN GAME CLASS
# =============================================================================

class Game:
    """Main game controller"""
    
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.state = GameState.MAIN_MENU
        self.difficulty = Difficulty.NORMAL
        self.current_level = 1
        self.unlocked_levels = 1
        self.player = None
        self.level = None
        self.particles = ParticleSystem()
        self.offset_x = 0
        self.scroll_area_width = 500
        self.time_elapsed = 0
        
        # Menus
        self.main_menu = MainMenu()
        self.difficulty_menu = DifficultyMenu()
        self.level_select_menu = None
        self.pause_menu = PauseMenu()
        
        # Background
        self.background, self.bg_image = get_background("Brown.png")
    
    def set_difficulty(self, difficulty):
        """Set game difficulty"""
        global CURRENT_DIFFICULTY
        if difficulty == "easy":
            CURRENT_DIFFICULTY = Difficulty.EASY
        elif difficulty == "normal":
            CURRENT_DIFFICULTY = Difficulty.NORMAL
        elif difficulty == "hard":
            CURRENT_DIFFICULTY = Difficulty.HARD
        self.difficulty = CURRENT_DIFFICULTY
    
    def start_level(self, level_num):
        """Initialize and start a level"""
        self.current_level = level_num
        self.level = Level(level_num, self.difficulty)
        self.player = Player(self.level.player_start[0], self.level.player_start[1], 
                            50, 50, self.difficulty)
        self.offset_x = 0
        self.time_elapsed = 0
        self.particles.clear()
        self.state = GameState.PLAYING
    
    def update_playing(self):
        """Update game when playing"""
        # Update player
        self.player.loop(FPS)
        
        # Update enemies
        for enemy in self.level.enemies:
            if not enemy.is_dead:
                enemy.update(self.player, self.level.objects)
        
        # Update traps
        for obj in self.level.objects:
            if isinstance(obj, (Fire, Saw, MovingPlatform)):
                obj.loop()
        
        # Update collectibles
        for item in self.level.collectibles:
            item.loop()
        
        # Update power-ups
        for powerup in self.level.powerups:
            powerup.loop()
        
        # Handle player movement
        handle_move(self.player, self.level.objects)
        
        # Check collectibles
        check_collectibles(self.player, self.level.collectibles, self.particles)
        
        # Check power-ups
        check_powerups(self.player, self.level.powerups, self.particles)
        
        # Check enemies
        check_enemies(self.player, self.level.enemies, self.particles)
        
        # Check goal
        if check_goal(self.player, self.level.goal):
            self.state = GameState.LEVEL_COMPLETE
            # Unlock next level
            if self.current_level >= self.unlocked_levels and self.current_level < 10:
                self.unlocked_levels = self.current_level + 1
        
        # Update particles
        self.particles.update()
        
        # Camera scrolling
        if ((self.player.rect.right - self.offset_x >= WIDTH - self.scroll_area_width) and 
            self.player.x_vel > 0) or \
           ((self.player.rect.left - self.offset_x <= self.scroll_area_width) and 
            self.player.x_vel < 0):
            self.offset_x += self.player.x_vel
        
        # Update timer
        self.time_elapsed += 1 / FPS
        time_remaining = self.level.time_limit - self.time_elapsed
        
        # Time's up
        if time_remaining <= 0:
            self.player.is_dead = True
            self.player.health = 0
        
        # Check death
        if self.player.is_dead:
            self.state = GameState.GAME_OVER
            self.particles.emit(self.player.rect.centerx, self.player.rect.centery, 
                              (255, 0, 0), 30)
    
    def draw_playing(self):
        """Draw game screen"""
        # Background
        for tile in self.background:
            WIN.blit(self.bg_image, tile)
        
        # Objects
        for obj in self.level.objects:
            obj.draw(WIN, self.offset_x)
        
        # Collectibles
        for item in self.level.collectibles:
            item.draw(WIN, self.offset_x)
        
        # Power-ups
        for powerup in self.level.powerups:
            powerup.draw(WIN, self.offset_x)
        
        # Enemies
        for enemy in self.level.enemies:
            if not enemy.is_dead:
                enemy.draw(WIN, self.offset_x)
        
        # Player
        self.player.draw(WIN, self.offset_x)
        
        # Particles
        self.particles.draw(WIN, self.offset_x)
        
        # UI
        time_remaining = max(0, self.level.time_limit - self.time_elapsed)
        draw_game_ui(WIN, self.player, self.current_level, time_remaining, 
                    self.difficulty["name"])
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            self.clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                
                # Handle different game states
                if self.state == GameState.MAIN_MENU:
                    result = self.main_menu.handle_event(event)
                    if result == "difficulty_select":
                        self.state = GameState.DIFFICULTY_SELECT
                    elif result == "level_select":
                        self.level_select_menu = LevelSelectMenu(self.unlocked_levels)
                        self.state = GameState.LEVEL_SELECT
                    elif result == "quit":
                        running = False
                
                elif self.state == GameState.DIFFICULTY_SELECT:
                    result = self.difficulty_menu.handle_event(event)
                    if result in ["easy", "normal", "hard"]:
                        self.set_difficulty(result)
                        self.start_level(1)
                    elif result == "back":
                        self.state = GameState.MAIN_MENU
                
                elif self.state == GameState.LEVEL_SELECT:
                    result = self.level_select_menu.handle_event(event)
                    if result and result.startswith("level_"):
                        level_num = int(result.split("_")[1])
                        if self.difficulty == Difficulty.NORMAL:
                            self.set_difficulty("normal")
                        self.start_level(level_num)
                    elif result == "back":
                        self.state = GameState.MAIN_MENU
                
                elif self.state == GameState.PLAYING:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE and self.player.jump_count < 2:
                            self.player.jump()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.PAUSED
                
                elif self.state == GameState.PAUSED:
                    result = self.pause_menu.handle_event(event)
                    if result == "resume":
                        self.state = GameState.PLAYING
                    elif result == "restart":
                        self.start_level(self.current_level)
                    elif result == "main_menu":
                        self.state = GameState.MAIN_MENU
                
                elif self.state == GameState.GAME_OVER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.start_level(self.current_level)
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MAIN_MENU
                
                elif self.state == GameState.LEVEL_COMPLETE:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE and self.current_level < 10:
                            self.start_level(self.current_level + 1)
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MAIN_MENU
            
            # Update
            if self.state == GameState.PLAYING:
                self.update_playing()
            
            # Draw
            if self.state == GameState.MAIN_MENU:
                self.main_menu.draw(WIN)
            
            elif self.state == GameState.DIFFICULTY_SELECT:
                self.difficulty_menu.draw(WIN)
            
            elif self.state == GameState.LEVEL_SELECT:
                self.level_select_menu.draw(WIN)
            
            elif self.state == GameState.PLAYING:
                self.draw_playing()
            
            elif self.state == GameState.PAUSED:
                self.draw_playing()
                self.pause_menu.draw(WIN)
            
            elif self.state == GameState.GAME_OVER:
                self.draw_playing()
                draw_game_over(WIN, self.player)
            
            elif self.state == GameState.LEVEL_COMPLETE:
                self.draw_playing()
                draw_level_complete(WIN, self.player, self.current_level)
            
            pygame.display.update()
        
        pygame.quit()

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    game = Game()
    game.run()