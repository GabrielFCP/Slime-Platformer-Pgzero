import random
from slime_sprite_list import *
from bee_sprite_list import *
from collectible_sprite_list import *
from decoration_sprite_list import decoration_sprite_list
from maps import floor_list



# GAME DATA --------------------------------------------------------------------------------------------------------
WIDTH = 1000
HEIGHT = 700

SKY_COLOR = (135, 206, 235)

#TILE_C = 32
#TILE_R = 22

TITLE = "Teste pygame"
FPS = 60
GRAVITY = 0.9
TERMINAL_VELOCITY = 10

current_level = 0
obstacle_blocks = []
enemies_list = []
collectibles_list = []
decorations_list = []
drawing_list = [decorations_list, enemies_list, obstacle_blocks, collectibles_list]

last_known_position = (0, 0)
# CLASS DEFINITIONS -------------------------------------------------------------------------------------------------------------------------------
# COLLECTIBLES
class Collectible(Actor):
    def __init__(self, image, position):
        self.frameTimeCounter = 0
        self.frameDuration = 10
        self.frameIndex = 0
        super().__init__(image, position)
        collectibles_list.append(self)

    def interact(self):
        self.destroy()
    def destroy(self):
        pass
        collectibles_list.remove(self)

    def update_self(self):
        pass

class Heart(Collectible):
    def __init__(self, position):
        self.heal_amount = 1
        super().__init__(heart_collectible_frame[0], position)

    def interact(self):
        player.heal(self.heal_amount)
        super().interact()

    def animation(self):
        self.frameTimeCounter += 1
        if self.frameTimeCounter >= self.frameDuration:
            self.frameTimeCounter = 0
            print(self.frameIndex)
            self.image = heart_collectible_frame[self.frameIndex]
            self.frameIndex = (self.frameIndex + 1) % len(heart_collectible_frame)

    def update_self(self):
        self.animation()
        super().update_self()

# PLATFORMS
class Platform(Actor):
    def __init__(self, image, position):
        super().__init__(image, position)
        obstacle_blocks.append(self)

class Grass(Platform):
    def __init__(self, position):
        super().__init__("grass_straight", position)

class Dirt(Platform):
    def __init__(self, position):
        super().__init__("grass_dirt_straight", position)

class Decoration(Actor):
    def __init__(self, position):
        super().__init__(decoration_sprite_list[random.randrange(0, len(decoration_sprite_list))], position)
        decorations_list.append(self)

# ENTITIES
class Enemy(Actor):
    def __init__(self, image, position, health, damage):
        enemies_list.append(self)
        self.health = health
        self.damage = damage
        self.vulnerable = True
        self.invTime = 1.5
        self.frameTimeCounter = 0
        self.frameDuration = 10
        self.frameIndex = 0
        self.direction = -1
        self.speed = 0
        self.loot_chance = 50
        super().__init__(image, position)


    def take_damage(self, amount):
        if self.vulnerable:
            self.health -= amount
            self.vulnerable = False
            for i in range(1, 4):
                clock.schedule(self.inv_anim, self.invTime / i)
            clock.schedule(self.invulnerability_end, self.invTime)

    def invulnerability_end(self):
        self.vulnerable = True

    def inv_anim(self):
        """
        Override in children.
        """
        pass

    def movement(self):
        self.direction = 1 if self.speed < 0 else 0
        self.x += self.speed

    def terrain_collision_handler(self):
        for ob in obstacle_blocks:
            if self.colliderect(ob) or self.x > WIDTH or self.x < 0:
                self.speed *= -1

    def destroy(self):
        enemies_list.remove(self)
        if random.randint(1, 100) <= self.loot_chance:
            Heart((self.x, self.y))


    def update_self(self):
        if self.health <= 0:
            self.destroy()

        self.movement()
        self.terrain_collision_handler()

class Bee(Enemy):
    def __init__(self, position):
        self.health = 2
        self.damage = 1
        super().__init__(bee_fly_frames[0][0], position, self.health, self.damage)
        self.speed = -1

    def take_damage(self, amount):
        self.image = bee_hurt_frame
        super().take_damage(amount)

    def inv_anim(self):
        self.image = bee_transparent_frame

    def animation_handler(self):
        self.frameTimeCounter += 1
        if self.speed != 0:
            if self.frameTimeCounter >= self.frameDuration:
                self.frameTimeCounter = 0
                self.frameIndex = (self.frameIndex + 1) % len(bee_fly_frames[self.direction])
                self.image = bee_fly_frames[self.direction][self.frameIndex]

    def update_self(self):
        self.animation_handler()
        super().update_self()


class Player(Actor):

    PLAYER_SPEED = 3
    MAX_HEALTH = 5
    JUMP_STRENGHT = 6
    KNOCKBACK_TIME = 0.2
    JUMP_CD = 0.2
    INV_TIME = 1

    jumpSounds = ["slime_jump1.mp3"]
    def __init__(self, image, position):
        super().__init__(image, position)
        self.vX = 0
        self.vY = 0
        self.jumpTimer = 0
        self.fallTimer = 0
        self.isWalking = False
        self.moveDirection = 0
        self.frameIndex = 0
        self.frameDuration = 10
        self.frameTimeCounter = 0
        self.isCollidingLeft = False
        self.isCollidingRight = False
        self.playerDamage = 1
        self.isVulnerable = True
        self.isStunned = False
        self.health = self.MAX_HEALTH
        self.alive = True

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
        for ob in obstacle_blocks:
            if self.colliderect(ob):
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
        for en in enemies_list:
            if self.colliderect(en):
                if self.vY > 0 and self.bottom > en.top and self.top < en.top:
                    if en.vulnerable:
                        en.take_damage(self.playerDamage)
                        self.vY = -self.JUMP_STRENGHT * 1.5
                    else:
                        self.take_damage(en.damage)
                elif self.vY < 0 and self.top < en.bottom and self.bottom > en.bottom:
                    self.stun_self(self.KNOCKBACK_TIME)
                    self.vY *= -1
                    self.top = en.bottom
                    self.take_damage(en.damage)

                if self.bottom <= en.bottom and self.top >= en.top:
                    if self.vX > 0 and self.right >= en.left:
                        self.stun_self(self.KNOCKBACK_TIME)
                        self.take_damage(en.damage)
                        self.vX = -self.vX * self.JUMP_STRENGHT
                        self.right = en.left
                        self.isCollidingRight = True
                    elif self.vX < 0 and self.left <= en.right:
                        self.stun_self(self.KNOCKBACK_TIME)
                        self.vX = self.vX * self.JUMP_STRENGHT
                        self.take_damage(en.damage)
                        self.left = en.right
                        self.isCollidingLeft = True

    def collectible_collision(self):
        for co in collectibles_list:
            if self.colliderect(co):
                co.interact()

    def take_damage(self, dmg):
        if self.isVulnerable:
            self.image = slimeHurtFrame
            self.health -= dmg
            self.isVulnerable = False
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
        self.vY -= GRAVITY * self.JUMP_STRENGHT
        self.isCollidingRight = False
        self.isCollidingLeft = False
        self.jumpTimer = 0
        sounds.slime_jump1.play()

    def stun_self(self, cd):
        self.isStunned = True
        clock.schedule(self.unstun_self, cd)

    def unstun_self(self):
        self.isStunned = False

    def die(self):
        self.alive = False

    def animation_handler(self):
        if self.isWalking and self.alive:
            self.frameTimeCounter += 1
            if self.frameTimeCounter >= self.frameDuration:
                self.frameTimeCounter = 0
                self.frameIndex = (self.frameIndex + 1) % len(slimeWalkingFrames[self.moveDirection])
                self.image = slimeWalkingFrames[self.moveDirection][self.frameIndex]
        elif not self.isWalking and self.alive:
            self.idleAnimation()
        else:
            self.death_animation()

    def idleAnimation(self):
        self.frameTimeCounter += 0.5
        if self.frameTimeCounter >= self.frameDuration:
            self.frameTimeCounter = 0
            self.frameIndex = (self.frameIndex + 1) % len(slimeIdleFrames[self.moveDirection])
            self.image = slimeIdleFrames[self.moveDirection][self.frameIndex]

    def death_animation(self):
        if self.frameIndex < len(slimeDeathFrames) - 1:
            self.frameTimeCounter += 0.5
            if self.frameTimeCounter >= self.frameDuration:
                self.frameTimeCounter = 0
                self.frameIndex += 1
                self.image = slimeDeathFrames[self.frameIndex]
        else:
            self.image = slimeDeathFrames[-1]

    def updateSelf(self):
        if self.health <= 0:
            self.die()
        self.vY = min(self.vY + GRAVITY * (self.fallTimer / FPS), TERMINAL_VELOCITY)
        self.fallTimer += 1
        self.jumpTimer += 1/60
        self.move(self.vX, self.vY)
        self.animation_handler()
        self.handleTerrainCollision()
        self.handleEnemyCollision()
        self.collectible_collision()

# INSTANTIATIONS ------------------------------------------------------------------------------------------------
player = Player(slimeIdleFrames[0][0], (400, 400))
bee = Bee((500, 580))
heart = Heart((600, 580))
# INPUT DEFINITIONS --------------------------------------------------------------------------------------------

def on_key_down(key):
    if key == keys.SPACE and player.alive:
        if player.vY < 1 and player.jumpTimer >= player.JUMP_CD:
            player.jump()

def handleInput(player):
    player.vX = 0
    player.isWalking = False
    if not player.isStunned and player.alive:
        if keyboard.left:
            player.moveLeft(player.PLAYER_SPEED)
        if keyboard.right:
            player.moveRight(player.PLAYER_SPEED)

# MAP GENERATION -----------------------------------------------------------------------------------------------
for floor in floor_list:
    rows = floor.strip().split('\n')
    for l, row in enumerate(rows):
        current_floor = row.split(',')
        for c, n in enumerate(current_floor):
            if n == "0":
                Dirt((c * 32, l * 32))
            if n == "1":
                Grass((c * 32, l * 32))
    for dec in range(1, random.randint(0, 20), 1):
            Decoration((random.randint(0, WIDTH), (HEIGHT - 64)))


# UPDATE & DRAW -------------------------------------------------------------------------------------------------
def draw():
    screen.clear()
    screen.blit("background_distantlands", (0, 0))

    for c_list in drawing_list:
        for obj in c_list:
            obj.draw()

    player.draw()
    screen.draw.text(
    f'Life: {player.health}/{player.MAX_HEALTH}',
    (32, 32),
    color="white",
    fontsize=60,
    owidth=0.5,
    ocolor="black")

def update():
    player.updateSelf()
    handleInput(player)
    for en in enemies_list:
        en.update_self()

    for co in collectibles_list:
        co.update_self()
