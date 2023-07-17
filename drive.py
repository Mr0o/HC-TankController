import telnetlib
import time
import pygame # for input and drawing

# we will use the wonderful openCV library to capture images from the camera
import cv2

CONTROL_PORT = 8150
VIDEO_PORT = 8196
DEFAULT_IP = '10.10.1.1'

try:
    print(f"\nConnecting to {DEFAULT_IP}:{CONTROL_PORT} ...")
    tn = telnetlib.Telnet(DEFAULT_IP, CONTROL_PORT, timeout=10)
except:
    print(f"Failed to connect to {DEFAULT_IP}:{CONTROL_PORT}")
    exit()

print(f"Connected to {DEFAULT_IP}:{CONTROL_PORT}")

print(f"Establishing video capture at {DEFAULT_IP}:{VIDEO_PORT} ...")
# get the ip camera stream from the tank
try:
    video = cv2.VideoCapture(f"http://{DEFAULT_IP}:{VIDEO_PORT}") 
except Exception as e:
    print(f"Failed to connect to {DEFAULT_IP}:{VIDEO_PORT} ...")
    print(str(e))
    exit()

# init pygame
pygame.init()

WIDTH = 800
HEIGHT = int(WIDTH * 3 / 4)

# get the resolution of the display for fullscreen mode
displayInfo = pygame.display.Info()
FULLSCREEN_WIDTH = displayInfo.current_w
FULLSCREEN_HEIGHT = displayInfo.current_h

# create the screen and allow resizing
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE, vsync=True)
clock = pygame.time.Clock()

pygame.display.set_caption("Tank Controller")

tn.write(b"t1\n") # send hello to tank

# commands
L_STOP = " 10"
L_FORWARD = " 11"
L_BACKWARD = " 12"
R_STOP = " 20"
R_FORWARD = " 21"
R_BACKWARD = " 22"
CAMSTOP = " 30"
CAMUP = " 31"
CAMDOWN = " 32"
STOPALL = L_STOP + R_STOP + CAMSTOP

command = ""

def filterCommand(command: str) -> str:
    # remove and conflicting commands (e.g. forward and backward at the same time)
    if L_FORWARD in command and L_BACKWARD in command:
        command = command.replace(L_FORWARD, "")
        command = command.replace(L_BACKWARD, "")
    if R_FORWARD in command and R_BACKWARD in command:
        command = command.replace(R_FORWARD, "")
        command = command.replace(R_BACKWARD, "")
    if CAMUP in command and CAMDOWN in command:
        command = command.replace(CAMUP, "")
        command = command.replace(CAMDOWN, "")
    return command

def sendCommand(command: str, tn=tn) -> None:
    filteredCommand = filterCommand(command)
    if filteredCommand:
        # send command to tank over telnet
        tn.write(f"{filteredCommand}\n".encode())
        # print command to console
        print(f"Sent command:{filteredCommand}")

# main loop
idleTimer = time.time()
running = True
while running:
    takeScreenshot = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sendCommand(STOPALL)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                command += L_FORWARD + R_FORWARD
            if event.key == pygame.K_s:
                command += L_BACKWARD + R_BACKWARD
            if event.key == pygame.K_a:
                command += R_FORWARD + L_BACKWARD
            if event.key == pygame.K_d:
                command += L_FORWARD + R_BACKWARD
            if event.key == pygame.K_q:
                command += CAMUP
            if event.key == pygame.K_e:
                command += CAMDOWN
            if event.key == pygame.K_SPACE:
                takeScreenshot = True
            if event.key == pygame.K_F11:
                # check if we are already in fullscreen mode
                if screen.get_flags() & pygame.FULLSCREEN:
                    # switch to windowed mode
                    pygame.display.quit()
                    pygame.display.init()
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE, vsync=True)
                else:
                    # switch to fullscreen mode
                    pygame.display.quit()
                    pygame.display.init()
                    screen = pygame.display.set_mode((FULLSCREEN_WIDTH, FULLSCREEN_HEIGHT), pygame.FULLSCREEN, vsync=True)
            if event.key == pygame.K_ESCAPE:
                sendCommand(STOPALL)
                running = False
        if event.type == pygame.KEYUP:
            sendCommand(STOPALL)
            command = ""

    if command:
        sendCommand(command)
        # reset idle timer
        idleTimer = time.time()
    else:
        # prevent tank from powering down due to inactivity
        # test if we have been idle for 15 seconds, if so send a command to keep the tank alive
        if time.time() - idleTimer > 15:
            print("Keep alive...")
            sendCommand(L_FORWARD)
            sendCommand(STOPALL)
            idleTimer = time.time()

    # update WIDHT and HEIGHT in case the window was resized
    WIDTH, HEIGHT = pygame.display.get_surface().get_size()

    # maintain aspect ratio 4:3
    if WIDTH / HEIGHT > 4 / 3:
        WIDTH = HEIGHT * 4 / 3
    else:
        HEIGHT = WIDTH * 3 / 4
    
    # get the image from the camera
    ret, frame = video.read()
    if ret:
        # take screenshot
        if takeScreenshot:
            cv2.imwrite(f"screenshot-{time.time()}.png", frame)
            print("Screenshot saved")
        # convert the image to a pygame image
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pygame.surfarray.make_surface(frame)
        # flip frame
        frame = pygame.transform.flip(frame, False, True)
        # rotate frame
        frame = pygame.transform.rotate(frame, 270)
        # scale frame
        frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))

        # keep the frame centered
        frameRect = frame.get_rect()
        frameRect.center = (pygame.display.get_surface().get_size()[0] / 2, pygame.display.get_surface().get_size()[1] / 2)

        # draw background
        screen.fill((0, 0, 0))

        # draw frame
        screen.blit(frame, frameRect)

        # load font for text
        font = pygame.font.SysFont("Arial", 15, bold=True)

        # help text
        text = font.render("Use WASD keys to move the tank", True, (255, 255, 255))
        screen.blit(text, (10, 10))

        text = font.render("Use Q and E keys to move the camera", True, (255, 255, 255))
        screen.blit(text, (10, 30))

        # draw command
        text = font.render(command, True, (255, 255, 255))
        screen.blit(text, (10, 50))

        # draw performance metrics in the top right corner
        text = font.render(f"{round(clock.get_time(), 2)}ms", True, (255, 255, 255))
        screen.blit(text, (pygame.display.get_window_size()[0] - text.get_width() - 10, 10))
        text = font.render(f"{int(clock.get_fps())} fps", True, (255, 255, 255))
        screen.blit(text, (pygame.display.get_window_size()[0] - text.get_width() - 10, 30))


        # set the caption
        pygame.display.set_caption(f"Tank Controller - {int(WIDTH)}x{int(HEIGHT)}")

        clock.tick(30)
        pygame.display.update()