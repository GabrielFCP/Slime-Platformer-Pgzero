import random
from player_extra import *
from enemy_sprites import *
from collectible_sprite_list import *
from decoration_sprite_list import *
from maps import floor_list

#SOUNDS --------------------------------
deal_damage = sounds.slime_deal_damage
take_damage = sounds.slime_take_damage
jump = sounds.slime_fall
pick_up = sounds.slime_pick_up

# GAME DATA --------------------------------------------------------------------------------------------------------
WIDTH = 1000
HEIGHT = 688
TITLE = "Slime King"
FPS = 60
GRAVITY = 0.9
TERMINAL_VELOCITY = 10
current_floor = 0
sound_enabled = False
game_state = "paused"
obstacle_blocks = {}
enemies_list = {}
collectibles_list = []
decorations_list = []
menu_elements = []

# CLASS DEFINITIONS -------------------------------------------------------------------------------------------------------------------------------
class Menu_btn(Actor):
    def __init__(self, image, position):
        super().__init__(image, position)
        menu_elements.append(self)

class Animated_Object(Actor):
    def __init__(self, image, position):
        super().__init__(image, position)
        self.frame_timer = 0
        self.frameDuration = 10
        self.frameIndex = 0

# COLLECTIBLES
class Collectible(Animated_Object):
    global sound_enabled
    def __init__(self, image, position, floor):
        self.floor = floor
        super().__init__(image, position)
        collectibles_list.append(self)
    def interact(self):
        if sound_enabled:
            pick_up.play()
        self.destroy()
    def destroy(self):
        collectibles_list.remove(self)

    def update_self(self):
        global current_floor
        if self.floor != current_floor:
            self.destroy()

class Heart(Collectible):
    def __init__(self, position, floor):
        self.heal_amount = 1
        super().__init__(heart_collectible_frame[0], position, floor)

    def interact(self):
        player.heal(self.heal_amount)
        super().interact()

    def animation(self):
        self.frame_timer += 1
        if self.frame_timer >= self.frameDuration:
            self.frame_timer = 0
            self.image = heart_collectible_frame[self.frameIndex]
            self.frameIndex = (self.frameIndex + 1) % len(heart_collectible_frame)

    def update_self(self):
        self.animation()
        super().update_self()

# PLATFORMS
class Platform(Actor):
    def __init__(self, image, position, floor):
        self.floor = floor
        self.type = "No type"
        super().__init__(image, position)
        if self.floor not in obstacle_blocks:
            obstacle_blocks[self.floor] = []
        obstacle_blocks[self.floor].append(self)

class Grass(Platform):
    def __init__(self, position, floor):
        super().__init__(grass_block, position, floor)
        self.type = "Grass"

class Dirt(Platform):
    def __init__(self, position, floor):
        super().__init__("grass_dirt_straight", position, floor)
        self.type = "Dirt"

class Decoration(Actor):
    def __init__(self, image, position):
        self.type = "Decoration"
        super().__init__(image, position)
        decorations_list.append(self)

class Foliage(Decoration):
    def __init__(self, position):
        image = foliage_sprite_list[random.randint(0, len(foliage_sprite_list) - 1)]
        super().__init__(image, position)
        self.type = "Foliage"

class Cloud(Decoration):
    def __init__(self, position):
        image = cloud_sprite_list[random.randint(0, len(cloud_sprite_list) - 1)]
        super().__init__(image, position)
        self.type = "Cloud"
        self.speed = random.uniform(0.01, 0.3)

    def update_self(self):
        self.x += self.speed
        if self.x > WIDTH + 60:
            self.x = -100
            self.y = random.randint(70, 600)

class Exit(Platform):
    def __init__(self, position, floor):
        super().__init__(exit_passage, position, floor)
        self.type = "Exit"

    def win(self):
        global game_state
        game_state = "win"
        clock.schedule(quit, 3)

# ENTITIES
class Enemy(Animated_Object):
    global sound_enabled
    def __init__(self, image, position, floor, health, damage):
        self.health = health
        self.damage = damage
        self.floor = floor
        self.vulnerable = True
        self.invTime = 1.5
        self.direction = -1
        self.speed = 0
        self.temp_speed = 0
        self.loot_chance = 100
        self.time_counter = 0
        super().__init__(image, position)
        if self.floor not in enemies_list:
            enemies_list[self.floor] = []
        enemies_list[self.floor].append(self)

    def take_damage(self, amount):
        if self.vulnerable:
            self.health -= amount
            self.vulnerable = False
            if sound_enabled:
                deal_damage.play()
            for i in range(1, 4):
                clock.schedule(self.inv_anim, self.invTime / i)
            clock.schedule(self.invulnerability_end, self.invTime)

    def invulnerability_end(self):
        self.vulnerable = True

    def inv_anim(self):
        pass

    def movement(self):
        self.direction = 1 if self.speed < 0 else 0
        self.x += self.speed

    def terrain_collision_handler(self):
        if self.right > WIDTH:
            self.temp_speed = self.speed
            self.speed = 0
            self.x -= 5
        if self.left < 0:
            self.temp_speed = self.speed
            self.speed = 0
            self.x += 5
        for ob in obstacle_blocks[self.floor]:
            if self.colliderect(ob):
                if self.speed > 0:
                    self.temp_speed = self.speed
                    self.speed = 0
                    self.x -= 5
                else:
                    self.temp_speed = self.speed
                    self.speed = 0
                    self.x += 5
        if self.speed == 0:
            self.speed -= self.temp_speed

    def destroy(self):
        enemies_list[current_floor].remove(self)
        if random.randint(1, 100) <= self.loot_chance:
            Heart((self.x, self.y),self.floor)

    def update_self(self):
        if self.health <= 0:
            self.destroy()
        self.movement()
        self.terrain_collision_handler()

class Bee(Enemy):
    def __init__(self, position, floor):
        self.health = 2
        self.damage = 1
        super().__init__(bee_fly_frames[0][0], position, floor, self.health, self.damage)
        self.speed = -2

    def take_damage(self, amount):
        self.image = bee_hurt_frame
        super().take_damage(amount)

    def inv_anim(self):
        self.image = bee_transparent_frame

    def animation_handler(self):
        self.frame_timer += 1
        if self.speed != 0:
            if self.frame_timer >= self.frameDuration:
                self.frame_timer = 0
                self.frameIndex = (self.frameIndex + 1) % len(bee_fly_frames[self.direction])
                self.image = bee_fly_frames[self.direction][self.frameIndex]

    def update_self(self):
        self.animation_handler()
        super().update_self()

class Snail(Enemy):
    def __init__(self, position, floor):
        self.health = 4
        self.damage = 2
        self.can_move = True
        self.is_hiding = False
        self.hide_cd = random.randint(3, 6)
        self.shell_time = 6
        super().__init__(snail_walk_frames[0][0], position, floor, self.health, self.damage)
        self.speed = -1
        clock.schedule(self.hide_in_shell, self.hide_cd)

    def movement(self):
        if self.can_move:
            super().movement()

    def hide_in_shell(self):
        self.can_move = False
        self.is_hiding = True
        clock.schedule(self.out_of_shell, self.shell_time)
        clock.schedule(self.out_of_shell, self.shell_time)
        clock.schedule(self.hide_in_shell, self.hide_cd + self.shell_time)

    def out_of_shell(self):
        self.is_hiding = False
        self.can_move = True

    def take_damage(self, amount):
        self.image = snail_hurt_frames[self.direction][0]
        super().take_damage(amount)

    def inv_anim(self):
        self.image = snail_transparent_frame

    def animation_handler(self):
        self.frame_timer += 0.5
        if self.frame_timer < self.frameDuration:
            return
        self.frame_timer = 0

        if self.can_move:
            self.update_walk_animation()
        elif self.is_hiding:
            self.update_hide_animation(forward=True)
        else:
            self.update_hide_animation(forward=False)

    def update_walk_animation(self):
        self.set_state("walking")
        self.frameIndex = (self.frameIndex + 1) % len(snail_walk_frames[self.direction])
        self.image = snail_walk_frames[self.direction][self.frameIndex]

    def update_hide_animation(self, forward=True):
        self.set_state("hiding" if forward else "unhiding")
        if forward:
            if self.frameIndex < len(snail_hide_frames[self.direction]) - 1:
                self.frameIndex += 1
            self.image = snail_hide_frames[self.direction][self.frameIndex]
        else:
            if self.frameIndex > 0:
                self.frameIndex -= 1
            self.image = snail_hide_frames[self.direction][self.frameIndex]

    def set_state(self, new_state):
        if getattr(self, "current_state", None) != new_state:
            self.current_state = new_state
            self.frameIndex = 0
            self.frame_timer = 0

    def update_self(self):
        self.animation_handler()
        super().update_self()

class Player(Animated_Object):
    def __init__(self, image, position):
        self.PLAYER_SPEED = 3
        self.MAX_HEALTH = 5
        self.JUMP_CD = 1
        self.INV_TIME = 1
        super().__init__(image, position)
        self.JUMP_STRENGTH = 6
        self.vX = 0
        self.vY = 0
        self.jumpTimer = 0
        self.fallTimer = 0
        self.isWalking = False
        self.moveDirection = 0
        self.isCollidingLeft = False
        self.isCollidingRight = False
        self.playerDamage = 1
        self.isVulnerable = True
        self.health = self.MAX_HEALTH
        self.alive = True
        self.sound_enabled = True
    def move(self, vX, vY):
        self.x += vX
        self.y += vY

    def moveLeft(self, vel):
        if not self.isCollidingLeft:
            self.vX = -vel
            self.isWalking = True
        self.moveDirection = 1
        self.isCollidingRight = False

    def moveRight(self, vel):
        if not self.isCollidingRight:
            self.vX = vel
            self.isWalking = True
        self.moveDirection = 0
        self.isCollidingLeft = False

    def fallLanding(self):
        self.isCollidingLeft = False
        self.isCollidingRight = False

    def handleTerrainCollision(self):
        global current_floor
        for ob in obstacle_blocks[current_floor]:
            if self.colliderect(ob):
                if ob.type == "Exit":
                    ob.win()
                else:
                    if self.vY > 0.01 and self.bottom > ob.top and self.top < ob.top:
                        self.vY = 0
                        self.bottom = ob.top
                        self.fallTimer = 0
                        if self.vX == 0:
                            self.fallLanding()
                    elif self.vY < 0 and self.top < ob.bottom and self.bottom > ob.bottom:
                        self.vY *= -1
                        self.top = ob.bottom
                    elif self.bottom <= ob.bottom and self.top >= ob.top:
                        if self.vX > 0 and self.right >= ob.left:
                            self.vX = 0
                            self.right = ob.left
                            self.isCollidingRight = True
                        elif self.vX < 0 and self.left <= ob.right:
                            self.vX = 0
                            self.left = ob.right
                            self.isCollidingLeft = True

    def handleEnemyCollision(self):
        global current_floor
        for en in enemies_list[current_floor]:
            if self.colliderect(en):
                if self.vY > 0 and self.bottom > en.top:
                    if en.vulnerable:
                        en.take_damage(self.playerDamage)
                        self.vY = -self.JUMP_STRENGTH * 2
                else:
                    if self.bottom > en.top:
                        self.take_damage(en.damage)
                    elif self.right > en.left and self.left < en.right:
                        if self.vX > 0 and self.right >= en.left:
                            self.take_damage(en.damage)
                        elif self.vX < 0 and self.left <= en.right:
                            self.take_damage(en.damage)

    def collectible_collision(self):
        for co in collectibles_list:
            if self.colliderect(co):
                co.interact()

    def take_damage(self, dmg):
        if self.isVulnerable:
            self.image = slimeHurtFrame
            self.health -= dmg
            self.isVulnerable = False
            if self.sound_enabled:
                take_damage.play()
            for i in range(1, 4):
                clock.schedule(self.inv_anim, self.INV_TIME / i)
            clock.schedule(self.inv_end, self.INV_TIME)

    def heal(self, amount):
        if self.health < self.MAX_HEALTH:
            self.health += amount

    def inv_anim(self):
        self.image = slimeTransparentFrame

    def inv_end(self):
        self.isVulnerable = True

    def jump(self):
        global sound_enabled
        if sound_enabled:
            jump.play()
        self.vY -= GRAVITY * self.JUMP_STRENGTH
        self.isCollidingRight = False
        self.isCollidingLeft = False
        self.jumpTimer = self.JUMP_CD

    def die(self):
        self.alive = False
        self.isVulnerable = False
        clock.schedule(quit, 4)

    def animation_handler(self):
        if self.isWalking and self.alive:
            self.frame_timer += 1
            if self.frame_timer >= self.frameDuration:
                self.frame_timer = 0
                self.frameIndex = (self.frameIndex + 1) % len(slimeWalkingFrames[self.moveDirection])
                self.image = slimeWalkingFrames[self.moveDirection][self.frameIndex]
        elif not self.isWalking and self.alive:
            self.idleAnimation()
        else:
            self.death_animation()

    def idleAnimation(self):
        self.frame_timer += 0.5
        if self.frame_timer >= self.frameDuration:
            self.frame_timer = 0
            self.frameIndex = (self.frameIndex + 1) % len(slimeIdleFrames[self.moveDirection])
            self.image = slimeIdleFrames[self.moveDirection][self.frameIndex]

    def death_animation(self):
        if self.frameIndex < len(slimeDeathFrames) - 1:
            self.frame_timer += 0.5
            if self.frame_timer >= self.frameDuration:
                self.frame_timer = 0
                self.frameIndex += 1
                self.image = slimeDeathFrames[self.frameIndex]
        else:
            self.image = slimeDeathFrames[-1]

    def change_floor(self):
        global current_floor
        global decorations_list
        if self.x > WIDTH:
            current_floor +=1
            self.x = 0
            decorations_list = []
            redraw()
        elif self.x < 0 and current_floor > 0:
            current_floor -=1
            self.x = WIDTH
            decorations_list = []
            redraw()

    def updateSelf(self):
        global sound_enabled
        if self.health <= 0:
            self.die()
        self.vY = min(self.vY + GRAVITY * self.fallTimer, TERMINAL_VELOCITY)
        self.fallTimer += 1 / FPS
        self.jumpTimer -= 1 / FPS
        if self.jumpTimer < 0:
            self.jumpTimer = 0
        self.move(self.vX, self.vY)
        self.animation_handler()
        self.handleTerrainCollision()
        self.handleEnemyCollision()
        self.collectible_collision()
        self.sound_enabled = sound_enabled
        self.change_floor()

# INPUT DEFINITIONS --------------------------------------------------------------------------------------------

def on_key_down(key):
    global game_state
    if key == keys.SPACE and player.alive:
        if player.vY < 1 and player.jumpTimer <= 0:
            player.jump()

    if key == keys.ESCAPE and not game_state == "win":
        if game_state == "playing":
            game_state = "paused"
        else:
            game_state = "playing"

def on_mouse_down(pos):
    global game_state
    global sound_enabled
    if game_state == "paused":
        if menu_elements[2].collidepoint(pos):
            game_state = "playing"
        elif menu_elements[3].collidepoint(pos):
            if sound_enabled:
                sound_enabled = False
                music.stop()
            else:
                sound_enabled = True
                music.play("time_for_adventure")
        elif menu_elements[4].collidepoint(pos):
            quit()

def handleInput(player):
    player.vX = 0
    player.isWalking = False
    if player.alive:
        if keyboard.left:
            player.moveLeft(player.PLAYER_SPEED)
        if keyboard.right:
            player.moveRight(player.PLAYER_SPEED)

# MAP GENERATION -----------------------------------------------------------------------------------------------
block_size = 32
for f, floor in enumerate(floor_list):
    enemies_list[f] = []
    obstacle_blocks[f] = []
    rows = floor.strip().split('\n')
    for r, row in enumerate(rows):
        curr_f = row.split(',')
        for c, n in enumerate(curr_f):
            if n == "0":
                Dirt((c * block_size, r * block_size), f)
            if n == "1":
                Grass((c * block_size, r * block_size), f)
            if n == "5":
                Snail((c * block_size -32, HEIGHT - 81), f)
            if n == "6":
                Bee((c * block_size, r * block_size), f)
            if n == "4":
                Exit((c * block_size, r * block_size), f)

# INSTANTIATIONS ------------------------------------------------------------------------------------------------
player = Player(slimeIdleFrames[0][0], (400, HEIGHT - 100))
collumn1 = Actor(exit_collumn, (426, 496))
collumn2 = Actor(exit_collumn, (504, 496))

# UI
menu_elements.append(Actor("main_menu_bg"))
menu_elements.append(Actor("title", (WIDTH / 2, 140)))
sound_ui_display = Actor("ui_sound", (WIDTH - 62, 62))
y_position = 320
for btn_image in main_menu_btns:
    button = Menu_btn(btn_image, (500, y_position))
    y_position += 120

# UPDATE & DRAW -------------------------------------------------------------------------------------------------
drawing_list = [decorations_list, enemies_list[current_floor], obstacle_blocks[current_floor], collectibles_list]
def redraw():
    global drawing_list
    global decorations_list
    global collectibles_list
    for dec in range(1, random.randint(10, 20), 1):
        Foliage((random.randint(0, WIDTH), (HEIGHT - 96)))
        Cloud(((random.randint(0, WIDTH), random.randint(70, int(HEIGHT / 2)))))
    drawing_list = [decorations_list, enemies_list[current_floor], obstacle_blocks[current_floor], collectibles_list]


redraw()

def draw():
    screen.clear()
    screen.blit("background_distantlands", (0, 0))

    if game_state == "playing":
        for c_list in drawing_list:
            for obj in c_list:
                obj.draw()

        if current_floor == 3:
            collumn1.draw()
            collumn2.draw()
        player.draw()
        screen.draw.text(
        f'Life: {player.health}/{player.MAX_HEALTH}',
        (32, 32),
        color="white",
        fontsize=60,
        owidth=0.5,
        ocolor="black")

    if game_state == "paused":
        for el in menu_elements:
            el.draw()

    if game_state == "win":
        screen.draw.text(
        "WIN!",
        (250, 250),
        color="YELLOW",
        fontsize=300,
        owidth=0.5,
        ocolor="black")

    sound_ui_display.draw()

def update():
    if game_state == "playing":
        player.updateSelf()
        handleInput(player)
        for en in enemies_list[current_floor]:
            en.update_self()

        for co in collectibles_list:
            co.update_self()

        for deco in decorations_list:
            if deco.type == "Cloud":
                deco.update_self()

    if sound_enabled:
        sound_ui_display.image = ("ui_sound")
    else:
        sound_ui_display.image = ("ui_sound_off")
