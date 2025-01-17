import random
from slime_sprite_list import *
from bee_sprite_list import *
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

obstacle_blocks = []
enemies_list = []
collectibles_list = []

# CLASS DEFINITIONS -------------------------------------------------------------------------------------------------------------------------------
class Enemy(Actor):
    def __init__(self, image, position, health, damage):
        super().__init__(image, position)
        enemies_list.append(self)
        self.health = health
        self.damage = damage
        self.vulnerable = True
        self.invTime = 2

    def take_damage(self, amount):
        if self.vulnerable:
            self.health -= amount
            self.vulnerable = False
            clock.schedule(self.invulnerability_end, self.invTime)

    def invulnerability_end(self):
        self.vulnerable = True

    def destroy(self):
        enemies_list.remove(self)

    def update_self(self):
        if self.health == 0:
            self.destroy()

class Bee(Enemy):
        def __init__(self, position):
            self.health = 2
            self.damage = 1
            super().__init__(bee_fly_frames[0], position, self.health, self.damage)


        def take_damage(self, amount):
            self.image = bee_hurt_frame
            clock.schedule(self.inv_anim, self.invTime/4)
            clock.schedule(self.inv_anim, self.invTime/2)
            super().take_damage(amount)

        def inv_anim(self):
            self.image = bee_transparent_frame



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

class Collectible(Actor):
    def __init__(self, image, position):
        super().__init__(image, position)

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


                # Horizontal Collision
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

    def take_damage(self, dmg):
        if self.isVulnerable:
            self.image = slimeHurtFrame
            self.health -= dmg
            self.isVulnerable = False
            clock.schedule(self.inv_anim, self.INV_TIME/4)
            clock.schedule(self.inv_anim, self.INV_TIME/2)
            clock.schedule(self.inv_end, self.INV_TIME)

    def heal(self, amount):
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

        #print(self.vX)
        self.move(self.vX, self.vY)
        self.animation_handler()
        self.handleTerrainCollision()
        self.handleEnemyCollision()

# INSTANTIATIONS ------------------------------------------------------------------------------------------------
player = Player(slimeIdleFrames[0][0], (400, 400))
bee = Bee((500, 580))
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



# MAP GENERATION
for floor in floor_list:
    rows = floor.strip().split('\n')
    for l, row in enumerate(rows):
        current_floor = row.split(',')
        for c, n in enumerate(current_floor):
            if n == "0":
                Dirt((c * 32, l * 32))
            if n == "1":
                Grass((c * 32, l * 32))







# UPDATE & DRAW -------------------------------------------------------------------------------------------------
def draw():
    screen.clear()
    screen.fill(SKY_COLOR)
    player.draw()
    screen.draw.text(str(player.health) + '/' + str(player.MAX_HEALTH), (32, 32), color="white", fontsize=60)


    #boxy = Rect((player.x - 20, player.y - 12), (40, 24))
    #screen.draw.rect(boxy, (0, 255, 0))
    for en in enemies_list:
        en.draw()

    for ob in obstacle_blocks:
        ob.draw()
        #boxes = Rect((ob.x - 16, ob.y - 16), (32, 32))
        #screen.draw.rect(boxes, (255, 0, 0))

def update():
    player.updateSelf()
    handleInput(player)
    for en in enemies_list:
        en.update_self()
