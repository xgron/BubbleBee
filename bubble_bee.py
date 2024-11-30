import pygame
import random
import math
import sys
import os

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 1024
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BACKGROUND_COLOR = (135, 206, 235)  # Light blue sky
CLOUD_COLOR = (255, 255, 255)  # White
CLOUD_SHADOW = (220, 220, 220)  # Light grey
MIN_SPEED_FACTOR = 0.2  # 10% of original speed
YELLOW = (255, 223, 0)  # Bee yellow color
PLAYER_SPEED = 0.05  # Speed multiplier for player movement (0.1 = slow, 0.5 = fast)

# Add bubble colors
BUBBLE_COLORS = [
    (173, 216, 230),  # light blue
    (221, 160, 221),  # plum
    (152, 251, 152),  # pale green
    (255, 182, 193),  # light pink
    (238, 232, 170),  # pale goldenrod
]

class Cloud:
    def __init__(self):
        self.x = random.randint(-100, WINDOW_WIDTH)
        self.y = random.randint(0, WINDOW_HEIGHT//2)
        self.speed = random.uniform(0.2, 0.5)
        self.size = random.randint(40, 100)
        self.circles = [(random.randint(-20, 20), random.randint(-20, 20), 
                        random.randint(20, 40)) for _ in range(5)]

    def move(self):
        self.x += self.speed
        if self.x > WINDOW_WIDTH + 100:
            self.x = -100
            self.y = random.randint(0, WINDOW_HEIGHT//2)

    def draw(self, screen):
        for offset_x, offset_y, radius in self.circles:
            # Draw cloud shadow
            pygame.draw.circle(screen, CLOUD_SHADOW,
                             (int(self.x + offset_x), int(self.y + offset_y + 2)),
                             radius)
            # Draw cloud
            pygame.draw.circle(screen, CLOUD_COLOR,
                             (int(self.x + offset_x), int(self.y + offset_y)),
                             radius)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Bubble Pop")
        self.clock = pygame.time.Clock()
        self.reset_game()
        pygame.mouse.set_visible(False)
        self.show_start_screen()
        self.player_pos = [WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2]
        self.player_angle = 0
        self.high_scores = self.load_high_scores()
        self.spawn_level = 1
        self.warning_time = 0
        self.showing_warning = False
        self.clouds = [Cloud() for _ in range(5)]
        self.bubbles = []
        self.last_bubble_spawn = 0
        self.bubble_spawn_delay = 2000  # Start with 2 seconds
        self.bullets = []
        self.last_shot_time = 0
        self.shot_delay = 250  # Delay between shots in milliseconds
        self.bullet_speed = 10
        self.min_bubble_radius = 10  # Minimum radius before bubble pops
        self.font = pygame.font.Font(None, 36)
        self.player_name = ""
        self.entering_name = False
        self.crosshair_pos = [WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2]  # Add this line
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 2000  # 2 seconds of invincibility after hit
        self.body_segments = []  # Store bee body segment positions
        self.hurt_effect_start = 0
        self.hurt_effect_duration = 500  # 500ms
        self.screen_shake_amount = 20
        self.hurt_flash = False

    def get_player_name(self):
        input_text = ""
        input_active = True
        
        while input_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text.strip():
                        return input_text
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        if len(input_text) < 10:  # Limit name length
                            input_text += event.unicode
            
            self.screen.fill(BACKGROUND_COLOR)
            name_prompt = self.font.render("Enter your name:", True, WHITE)
            name_text = self.font.render(input_text + "_", True, WHITE)
            
            self.screen.blit(name_prompt, (WINDOW_WIDTH/2 - 100, WINDOW_HEIGHT/2 - 50))
            self.screen.blit(name_text, (WINDOW_WIDTH/2 - 80, WINDOW_HEIGHT/2))
            
            pygame.display.flip()
            self.clock.tick(FPS)

    def load_high_scores(self):
        try:
            with open('high_scores.txt', 'r') as f:
                scores = []
                for line in f:
                    name, score = line.strip().split(',')
                    scores.append((name, int(score)))
                return sorted(scores, key=lambda x: x[1], reverse=True)[:5]
        except FileNotFoundError:
            return []

    def save_high_scores(self):
        with open('high_scores.txt', 'w') as f:
            for name, score in self.high_scores:
                f.write(f"{name},{score}\n")

    def update_high_scores(self):
        player_name = self.get_player_name()
        self.high_scores.append((player_name, self.score))
        self.high_scores.sort(key=lambda x: x[1], reverse=True)
        self.high_scores = self.high_scores[:5]  # Keep only top 5
        self.save_high_scores()

    def show_high_scores(self):
        self.screen.fill(BACKGROUND_COLOR)

        # Load and scale background image while maintaining aspect ratio
        try:
            background = pygame.image.load('bubblebee.png')
            bg_ratio = background.get_width() / background.get_height()
            
            # Calculate new dimensions that maintain aspect ratio and fill screen
            if WINDOW_WIDTH/WINDOW_HEIGHT > bg_ratio:
                new_width = WINDOW_WIDTH
                new_height = int(WINDOW_WIDTH / bg_ratio)
            else:
                new_height = WINDOW_HEIGHT
                new_width = int(WINDOW_HEIGHT * bg_ratio)
                
            background = pygame.transform.scale(background, (new_width, new_height))
            
            # Center the image
            x = (WINDOW_WIDTH - new_width) // 2
            y = (WINDOW_HEIGHT - new_height) // 2
            self.screen.blit(background, (x, y))
        except pygame.error:
            print("Warning: Could not load bubblebee.png")
            self.screen.fill(BACKGROUND_COLOR)
        
        title_text = "High Scores"
        title_pos = (50, 250)
        self.draw_text_with_frame(title_text, title_pos)
        
        y_pos = 350
        for i, (name, score) in enumerate(self.high_scores, 1):
            score_text = f"{i}. {name}: {score}"
            self.draw_text_with_frame(score_text, (50, y_pos))
            y_pos += 60

        restart_text = "Press R to restart or Q to quit"
        restart_pos = (WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT - 100)
        self.draw_text_with_frame(restart_text, restart_pos)
        
        pygame.display.flip()

    def draw_outlined_text(self, text, color, outline_color, position):
        # Create the outline by drawing the text multiple times offset by 2 pixels
        outline_positions = [(x, y) for x in (-2, 2) for y in (-2, 2)]
        text_surface = self.font.render(text, True, outline_color)
        
        for dx, dy in outline_positions:
            x, y = position[0] + dx, position[1] + dy
            self.screen.blit(text_surface, (x, y))
        
        # Draw the main text on top
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, position)

    def draw_text_with_frame(self, text, position, frame_padding=20):
        text_surface = self.font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(topleft=position)
        
        # Draw semi-transparent background frame
        frame_rect = text_rect.inflate(frame_padding * 2, frame_padding * 2)
        frame_surface = pygame.Surface(frame_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(frame_surface, (0, 0, 0, 180), frame_surface.get_rect(), border_radius=10)  # Black with 70% opacity
        self.screen.blit(frame_surface, frame_rect)
        
        # Draw text directly without outline
        self.screen.blit(text_surface, position)

    def show_start_screen(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        # Load and scale background image while maintaining aspect ratio
        try:
            background = pygame.image.load('bubblebee.png')
            bg_ratio = background.get_width() / background.get_height()
            
            # Calculate new dimensions that maintain aspect ratio and fill screen
            if WINDOW_WIDTH/WINDOW_HEIGHT > bg_ratio:
                new_width = WINDOW_WIDTH
                new_height = int(WINDOW_WIDTH / bg_ratio)
            else:
                new_height = WINDOW_HEIGHT
                new_width = int(WINDOW_HEIGHT * bg_ratio)
                
            background = pygame.transform.scale(background, (new_width, new_height))
            
            # Center the image
            x = (WINDOW_WIDTH - new_width) // 2
            y = (WINDOW_HEIGHT - new_height) // 2
            self.screen.blit(background, (x, y))
        except pygame.error:
            print("Warning: Could not load bubblebee.png")
            self.screen.fill(BACKGROUND_COLOR)
        
        font = pygame.font.Font(None, 36)
        start_text = font.render("Press any key to start", True, BLACK)
        text_rect = start_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 50))
        self.screen.blit(start_text, text_rect)
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    waiting = False

    def reset_game(self):
        self.score = 0
        self.game_over = False
        self.bubbles = []
        self.last_bubble_spawn = 0
        self.player_pos = [WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2]
        self.player_angle = 0
        self.spawn_level = 1
        self.warning_time = 0
        self.showing_warning = False
        self.bubble_spawn_delay = 1000
        self.clouds = [Cloud() for _ in range(5)]
        self.bullets = []
        self.last_shot_time = 0
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0

    def spawn_bubble(self):
        side = random.choice(['top', 'right', 'bottom', 'left'])
        radius = random.choices([random.randint(10, 40), random.randint(81, 100), random.randint(200, 250)], [0.8, 0.15, 0.05])[0]
        base_speed = 2.0  # Base speed for the smallest bubble
        speed = base_speed * (10 / radius)  # Adjust speed based on radius
        if side == 'top':
            x = random.randint(0, WINDOW_WIDTH)
            y = -radius * 2
            dy = speed
            dx = random.uniform(-speed, speed)
        elif side == 'right':
            x = WINDOW_WIDTH + radius * 2
            y = random.randint(0, WINDOW_HEIGHT)
            dx = -speed
            dy = random.uniform(-speed, speed)
        elif side == 'bottom':
            x = random.randint(0, WINDOW_WIDTH)
            y = WINDOW_HEIGHT + radius * 2
            dy = -speed
            dx = random.uniform(-speed, speed)
        else:  # left
            x = -radius * 2
            y = random.randint(0, WINDOW_HEIGHT)
            dx = speed
            dy = random.uniform(-speed, speed)
        
        # Ensure the new bubble does not spawn inside another bubble
        for bubble in self.bubbles:
            if math.hypot(x - bubble['x'], y - bubble['y']) < radius + bubble['radius']:
                return  # Do not spawn this bubble

        # Add color and shine properties
        color = random.choice(BUBBLE_COLORS)
        shine_offset = random.randint(-radius//2, -radius//4)  # Position of shine relative to center

        self.bubbles.append({
            'x': x, 'y': y, 'dx': dx, 'dy': dy, 'radius': radius, 'angle': 0,
            'color': color, 'shine_offset': shine_offset
        })

    def enforce_minimum_speed(self, bubble):
        original_speed = 6.0 * (10 / bubble['radius'])  # Same calculation as in spawn_bubble
        min_speed = original_speed * MIN_SPEED_FACTOR
        current_speed = math.hypot(bubble['dx'], bubble['dy'])
        
        if current_speed < min_speed:
            speed_factor = min_speed / current_speed
            bubble['dx'] *= speed_factor
            bubble['dy'] *= speed_factor

    def show_warning(self):
        font = pygame.font.Font(None, 48)
        warning_text = font.render(f"Yay! More bubbles Incoming! ^_^", True, WHITE)
        text_rect = warning_text.get_rect(center=(WINDOW_WIDTH/2, 50))
        self.screen.blit(warning_text, text_rect)

    def shoot(self, current_time):
        if current_time - self.last_shot_time > self.shot_delay:
            direction = math.radians(self.player_angle)
            dx = math.cos(direction) * self.bullet_speed
            dy = -math.sin(direction) * self.bullet_speed
            
            bullet_x = self.player_pos[0] + 20 * math.cos(direction)
            bullet_y = self.player_pos[1] - 20 * math.sin(direction)
            
            self.bullets.append({
                'x': bullet_x,
                'y': bullet_y,
                'dx': dx,
                'dy': dy,
                'rotation': math.degrees(direction)  # Add rotation to track angle
            })
            self.last_shot_time = current_time

    def split_bubble(self, bubble):
        if bubble['radius'] <= self.min_bubble_radius:
            return []
        
        new_radius = bubble['radius'] / 2
        speed_increase = 1.5
        
        # Create two smaller bubbles
        bubble1 = {
            'x': bubble['x'],
            'y': bubble['y'],
            'dx': bubble['dx'] * speed_increase,
            'dy': bubble['dy'] * speed_increase,
            'radius': new_radius,
            'angle': 0,
            'color': bubble['color'],
            'shine_offset': random.randint(-int(new_radius//2), -int(new_radius//4))
        }
        
        bubble2 = {
            'x': bubble['x'],
            'y': bubble['y'],
            'dx': -bubble['dx'] * speed_increase,
            'dy': -bubble['dy'] * speed_increase,
            'radius': new_radius,
            'angle': 0,
            'color': bubble['color'],
            'shine_offset': random.randint(-int(new_radius//2), -int(new_radius//4))
        }
        
        return [bubble1, bubble2] if new_radius > self.min_bubble_radius else []

    def separate_bubbles(self, bubble1, bubble2):
        dx = bubble2['x'] - bubble1['x']
        dy = bubble2['y'] - bubble1['y']
        distance = math.hypot(dx, dy)
        
        if distance == 0:  # Handle edge case of exact overlap
            bubble2['x'] += 1
            return
            
        # Calculate minimum separation distance
        min_distance = bubble1['radius'] + bubble2['radius']
        
        if distance < min_distance:
            # Calculate overlap
            overlap = (min_distance - distance) / 2
            
            # Normalize direction vector
            dx /= distance
            dy /= distance
            
            # Move bubbles apart
            bubble1['x'] -= dx * overlap
            bubble1['y'] -= dy * overlap
            bubble2['x'] += dx * overlap
            bubble2['y'] += dy * overlap

    def get_bee_hitbox(self):
        """Get the hitbox points for the bee's body segments"""
        bee_direction = math.radians(self.player_angle)
        hitbox_points = []
        
        # Get points for each body segment
        for i in range(3):  # 3 body segments
            offset = i * 8 - 8  # Spacing between segments
            x = self.player_pos[0] + offset * math.cos(bee_direction)
            y = self.player_pos[1] - offset * math.sin(bee_direction)
            hitbox_points.append((x, y))
            
        return hitbox_points

    def check_collision_with_bubble(self, bubble):
        """More precise collision detection using body segments"""
        hitbox_points = self.get_bee_hitbox()
        bubble_center = (bubble['x'], bubble['y'])
        segment_radius = 10  # Radius of body segments
        
        # Check each body segment for collision
        for point in hitbox_points:
            distance = math.hypot(point[0] - bubble_center[0], 
                                point[1] - bubble_center[1])
            if distance < (segment_radius + bubble['radius']):
                return True
        return False

    def apply_screen_shake(self, surface):
        if pygame.time.get_ticks() - self.hurt_effect_start < self.hurt_effect_duration:
            offset_x = random.randint(-self.screen_shake_amount, self.screen_shake_amount)
            offset_y = random.randint(-self.screen_shake_amount, self.screen_shake_amount)
            
            # Create a red overlay for the hurt effect
            if self.hurt_flash:
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                overlay.fill((255, 0, 0))  # Red
                overlay.set_alpha(100)  # Semi-transparent
                surface.blit(overlay, (0, 0))
            
            # Apply shake effect
            shifted_surface = surface.copy()
            shifted_rect = shifted_surface.get_rect(center=(WINDOW_WIDTH//2 + offset_x, WINDOW_HEIGHT//2 + offset_y))
            return shifted_surface, shifted_rect
        return surface, surface.get_rect()

    def run(self):
        last_score_update = pygame.time.get_ticks()
        showing_high_scores = False
        while True:
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_score_update) / 1000.0  # Convert milliseconds to seconds
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and (self.game_over or showing_high_scores):
                        showing_high_scores = False
                        self.reset_game()
                    elif event.key == pygame.K_q and showing_high_scores:
                        pygame.quit()
                        sys.exit()

            if self.game_over and not showing_high_scores:
                self.update_high_scores()
                showing_high_scores = True
                self.show_high_scores()
                continue
            
            if showing_high_scores:
                self.show_high_scores()
                continue

            # Update crosshair position to follow mouse directly
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self.crosshair_pos = [mouse_x, mouse_y]

            # Calculate player movement direction towards crosshair with delay
            dx = self.crosshair_pos[0] - self.player_pos[0]
            dy = self.crosshair_pos[1] - self.player_pos[1]
            distance = math.hypot(dx, dy)
            
            # Keep player at a minimum distance from crosshair
            min_distance = 60
            if distance > min_distance:
                # Move player towards crosshair but stay behind it
                target_x = self.crosshair_pos[0] - (dx/distance * min_distance)
                target_y = self.crosshair_pos[1] - (dy/distance * min_distance)
                
                # Smooth movement towards target position with speed control
                self.player_pos[0] += (target_x - self.player_pos[0]) * PLAYER_SPEED
                self.player_pos[1] += (target_y - self.player_pos[1]) * PLAYER_SPEED

            # Update player angle to face crosshair
            if distance > 0:
                self.player_angle = math.degrees(math.atan2(-dy, dx))

            # Handle shooting
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:  # Left mouse button
                self.shoot(current_time)

            if not self.game_over:
                current_level = (self.score // 10) + 1
                
                # Check if we need to increase spawn rate
                if current_level > self.spawn_level:
                    self.spawn_level = current_level
                    self.bubble_spawn_delay *= 0.8  # Decrease spawn delay by 20%
                    print(f"Level up! Current level: {self.bubble_spawn_delay}")
                    self.warning_time = current_time
                    self.showing_warning = True

                # Spawn new bubbles
                if current_time - self.last_bubble_spawn > self.bubble_spawn_delay:
                    self.spawn_bubble()
                    self.last_bubble_spawn = current_time

                # Update bubble positions and rotation
                for bubble in self.bubbles[:]:
                    bubble['x'] += bubble['dx']
                    bubble['y'] += bubble['dy']
                    bubble['angle'] += 1  # Rotate the bubble slowly
                    
                    # Remove bubbles that are off screen
                    if (bubble['x'] < -bubble['radius'] * 2 or bubble['x'] > WINDOW_WIDTH + bubble['radius'] * 2 or
                        bubble['y'] < -bubble['radius'] * 2 or bubble['y'] > WINDOW_HEIGHT + bubble['radius'] * 2):
                        self.bubbles.remove(bubble)

                    # Replace the old collision check with the new precise one
                    if not self.invincible:
                        if self.check_collision_with_bubble(bubble):
                            self.lives -= 1
                            if self.lives <= 0:
                                self.game_over = True
                            else:
                                self.invincible = True
                                self.invincible_timer = current_time
                                self.hurt_effect_start = current_time
                                self.hurt_flash = True
                                # Reset screen shake
                                self.screen_shake_amount = 20

                # Handle invincibility
                if self.invincible:
                    if current_time - self.invincible_timer > self.invincible_duration:
                        self.invincible = False

                # Check collisions between bubbles
                for i, bubble1 in enumerate(self.bubbles):
                    for j, bubble2 in enumerate(self.bubbles):
                        if i >= j:
                            continue
                        
                        distance = math.hypot(bubble1['x'] - bubble2['x'], 
                                           bubble1['y'] - bubble2['y'])
                        
                        if distance < bubble1['radius'] + bubble2['radius']:
                            # First separate overlapping bubbles
                            self.separate_bubbles(bubble1, bubble2)
                            
                            # Calculate masses based on radius
                            m1 = bubble1['radius'] ** 2
                            m2 = bubble2['radius'] ** 2
                            
                            # Calculate new velocities using conservation of momentum
                            total_mass = m1 + m2
                            new_dx1 = (m1 - m2) / total_mass * bubble1['dx'] + (2 * m2) / total_mass * bubble2['dx']
                            new_dy1 = (m1 - m2) / total_mass * bubble1['dy'] + (2 * m2) / total_mass * bubble2['dy']
                            new_dx2 = (2 * m1) / total_mass * bubble1['dx'] + (m2 - m1) / total_mass * bubble2['dx']
                            new_dy2 = (2 * m1) / total_mass * bubble1['dy'] + (m2 - m1) / total_mass * bubble2['dy']
                            
                            # Apply new velocities
                            bubble1['dx'], bubble2['dx'] = new_dx1, new_dx2
                            bubble1['dy'], bubble2['dy'] = new_dy1, new_dy2
                            
                            # Enforce minimum speeds after collision
                            self.enforce_minimum_speed(bubble1)
                            self.enforce_minimum_speed(bubble2)

                # Update bullet positions and check collisions
                for bullet in self.bullets[:]:
                    bullet['x'] += bullet['dx']
                    bullet['y'] += bullet['dy']
                    
                    # Remove bullets that are off screen
                    if (bullet['x'] < 0 or bullet['x'] > WINDOW_WIDTH or
                        bullet['y'] < 0 or bullet['y'] > WINDOW_HEIGHT):
                        self.bullets.remove(bullet)
                        continue
                    
                    # Check bullet collisions with bubbles
                    for bubble in self.bubbles[:]:
                        if math.hypot(bullet['x'] - bubble['x'], 
                                    bullet['y'] - bubble['y']) < bubble['radius']:
                            if bubble in self.bubbles:  # Check if bubble still exists
                                self.bubbles.remove(bubble)
                                self.bubbles.extend(self.split_bubble(bubble))
                                if bullet in self.bullets:  # Check if bullet still exists
                                    self.bullets.remove(bullet)
                                self.score += 1
                                break

                # Increase score by 1 point per real-time second
                if delta_time >= 1:
                    self.score += 1
                    last_score_update = current_time

            # Drawing
            self.screen.fill(BACKGROUND_COLOR)
            
            # Update and draw clouds
            for cloud in self.clouds:
                cloud.move()
                cloud.draw(self.screen)
                
            # Show warning message for 2 seconds
            if self.showing_warning and current_time - self.warning_time < 2000:
                self.show_warning()
            else:
                self.showing_warning = False

            # Draw bubbles
            for bubble in self.bubbles:
                # Draw main bubble
                pygame.draw.circle(self.screen, bubble['color'], 
                                 (int(bubble['x']), int(bubble['y'])), 
                                 bubble['radius'])
                # Draw outline
                pygame.draw.circle(self.screen, WHITE, 
                                 (int(bubble['x']), int(bubble['y'])), 
                                 bubble['radius'], 1)
                # Draw shine (smaller white circle)
                shine_x = int(bubble['x'] + bubble['shine_offset'])
                shine_y = int(bubble['y'] + bubble['shine_offset'])
                shine_radius = max(3, bubble['radius'] // 4)
                pygame.draw.circle(self.screen, WHITE, 
                                 (shine_x, shine_y), 
                                 shine_radius)

            # Draw bullets as stingers
            for bullet in self.bullets:
                # Calculate the three points of the triangle
                angle = math.radians(bullet['rotation'])
                length = 8  # Length of the stinger
                width = 3   # Half width of the stinger base
                
                # Tip of the stinger
                tip_x = bullet['x'] + length * math.cos(angle)
                tip_y = bullet['y'] - length * math.sin(angle)
                
                # Base points of the stinger
                base_angle1 = angle + math.pi/2
                base_angle2 = angle - math.pi/2
                base1_x = bullet['x'] + width * math.cos(base_angle1)
                base1_y = bullet['y'] - width * math.sin(base_angle1)
                base2_x = bullet['x'] + width * math.cos(base_angle2)
                base2_y = bullet['y'] - width * math.sin(base_angle2)
                
                # Draw the stinger
                pygame.draw.polygon(self.screen, BLACK, [
                    (tip_x, tip_y),
                    (base1_x, base1_y),
                    (base2_x, base2_y)
                ])

            # Draw player (bee)
            # Calculate bee parts positions based on angle
            bee_direction = math.radians(self.player_angle)
            
            # Body segments (yellow and black stripes)
            body_colors = [YELLOW, BLACK, YELLOW]
            for i, color in enumerate(body_colors):
                offset = i * 8 - 8  # Spacing between segments
                x = self.player_pos[0] + offset * math.cos(bee_direction)
                y = self.player_pos[1] - offset * math.sin(bee_direction)
                pygame.draw.circle(self.screen, color, (int(x), int(y)), 10)
            
            # Wings
            wing_angle1 = bee_direction + math.pi/2  # Right wing
            wing_angle2 = bee_direction - math.pi/2  # Left wing
            for wing_angle in [wing_angle1, wing_angle2]:
                wing_x = self.player_pos[0] + 5 * math.cos(bee_direction)
                wing_y = self.player_pos[1] - 5 * math.sin(bee_direction)
                wing_x += 12 * math.cos(wing_angle)
                wing_y += 12 * math.sin(wing_angle)
                pygame.draw.circle(self.screen, WHITE, (int(wing_x), int(wing_y)), 8)
            
            # Antennae
            antenna_base_x = self.player_pos[0] + 10 * math.cos(bee_direction)
            antenna_base_y = self.player_pos[1] - 10 * math.sin(bee_direction)
            antenna_angle1 = bee_direction - math.pi/6
            antenna_angle2 = bee_direction + math.pi/6
            for antenna_angle in [antenna_angle1, antenna_angle2]:
                end_x = antenna_base_x + 8 * math.cos(antenna_angle)
                end_y = antenna_base_y - 8 * math.sin(antenna_angle)
                pygame.draw.line(self.screen, BLACK, 
                               (int(antenna_base_x), int(antenna_base_y)),
                               (int(end_x), int(end_y)), 2)
                pygame.draw.circle(self.screen, BLACK, (int(end_x), int(end_y)), 2)

            # Draw crosshair
            crosshair_size = 10
            pygame.draw.line(self.screen, RED, 
                           (self.crosshair_pos[0] - crosshair_size, self.crosshair_pos[1]),
                           (self.crosshair_pos[0] + crosshair_size, self.crosshair_pos[1]), 2)
            pygame.draw.line(self.screen, RED, 
                           (self.crosshair_pos[0], self.crosshair_pos[1] - crosshair_size),
                           (self.crosshair_pos[0], self.crosshair_pos[1] + crosshair_size), 2)

            # Draw score with outline
            font = pygame.font.Font(None, 48)  # Increased font size
            self.draw_outlined_text(f"Score: {self.score}", BLACK, WHITE, (10, 10))

            # Draw lives with outline
            self.draw_outlined_text(f"Lives: {self.lives}", BLACK, WHITE, (WINDOW_WIDTH-120, 10))

            # Draw invincibility effect
            if self.invincible:
                flash = (current_time // 200) % 2  # Flash every 200ms
                if flash:
                    pygame.draw.circle(self.screen, WHITE, 
                                     (int(self.player_pos[0]), int(self.player_pos[1])), 
                                     15, 2)  # Draw white circle around player

            # Update game over screen drawing
            if self.game_over:
                font = pygame.font.Font(None, 36)
                game_over_text = font.render(f"Game Over! Score: {self.score}", True, WHITE)
                text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
                self.screen.blit(game_over_text, text_rect)

            # Apply hurt effect and screen shake
            if pygame.time.get_ticks() - self.hurt_effect_start < self.hurt_effect_duration:
                # Decrease shake amount over time
                self.screen_shake_amount = max(0, self.screen_shake_amount - 1)
                # Toggle hurt flash
                self.hurt_flash = not self.hurt_flash
                
                # Apply the effects
                shaken_screen, shaken_rect = self.apply_screen_shake(self.screen)
                # Create a temporary surface to draw the shaken screen
                temp_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                temp_surface.fill(BACKGROUND_COLOR)
                temp_surface.blit(shaken_screen, shaken_rect)
                # Update the display with the shaken surface
                self.screen.blit(temp_surface, (0, 0))

            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()