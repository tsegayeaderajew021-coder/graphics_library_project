import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math

# --- Global Variables ---
student_pos = [0, -1, 8]
student_target_pos = [0, -1, 8]  # Target position for smooth interpolation
student_rot = 0
student_target_rot = 0
arm_angle = 0
id_raise_progress = 0  # For ID card raise animation (0 to 1)
phase = 0 # 0:Entrance, 1:ID_Check, 2:Librarian_Accept, 3:Shelf, 4:ToTable, 5:Reading
has_id = False
id_shown = False  # Track if ID was already shown in this phase
has_book = False
show_id_timer = 0  # 120 frames = 2 seconds at 60fps
is_sitting = False
sitting_progress = 0  # 0 to 1, for smooth sitting animation
waist_bend = 0  # Amount of waist bending when sitting
head_tilt_angle = 0  # For reading animation
INTERPOLATION_SPEED = 0.08  # Speed of smooth movement interpolation
ROTATION_SPEED = 0.05  # Speed of smooth rotation

# Librarian data
librarian_pos = [0.5, -1, 2.5]
librarian_rot = 180  # Facing the entrance

# የሌሎች ተማሪዎች መረጃ
other_students = [
    {'pos': [4, -1, -3], 'color': [0.8, 0.2, 0.2]}, 
    {'pos': [6, -1, -4], 'color': [0.2, 0.8, 0.2]}
]

def setup_lighting():
    """Initialize realistic lighting with ambient and diffuse components"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Ambient light (overall brightness)
    ambient = [0.3, 0.3, 0.3, 1.0]
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient)
    
    # Diffuse light (directional lighting for realistic shading)
    diffuse = [0.8, 0.8, 0.8, 1.0]
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse)
    
    # Specular light (highlights)
    specular = [1.0, 1.0, 1.0, 1.0]
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular)
    
    # Light position (upper left front)
    position = [3.0, 5.0, 3.0, 0.0]
    glLightfv(GL_LIGHT0, GL_POSITION, position)
    
    # Set material properties for better lighting response
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1, 1, 1, 1])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50)

def interpolate_position(current, target, speed):
    """Smoothly interpolate between current and target positions"""
    result = [current[i] for i in range(3)]
    for i in range(3):
        diff = target[i] - current[i]
        if abs(diff) > 0.001:
            result[i] += diff * speed
        else:
            result[i] = target[i]
    return result

def draw_cube(x, y, z, sx, sy, sz, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glColor3f(color[0], color[1], color[2])
    vertices = [
        [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, -1],
        [1, -1, 1], [1, 1, 1], [-1, -1, 1], [-1, 1, 1]
    ]
    surfaces = [(0,1,2,3), (3,2,7,6), (6,7,5,4), (4,5,1,0), (1,5,7,2), (4,0,3,6)]
    glBegin(GL_QUADS)
    for surface in surfaces:
        for vertex in surface:
            glVertex3fv(vertices[vertex])
    glEnd()
    glPopMatrix()

def draw_detailed_human(pos, rot, color, is_reading=False, sitting=False, sitting_progress=0, waist_bend=0):
    """Draw a more detailed human model with articulated segments and facial features"""
    glPushMatrix()
    
    # Calculate vertical offset based on sitting animation
    y_offset = -0.5 * sitting_progress if sitting else 0
    glTranslatef(pos[0], pos[1] + y_offset, pos[2])
    glRotatef(rot, 0, 1, 0)
    
    # Torso (main body)
    torso_color = color
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glRotatef(waist_bend * sitting_progress, 1, 0, 0)  # Waist bending
    draw_cube(0, 0.7, 0, 0.35, 0.7, 0.2, torso_color)
    glPopMatrix()
    
    # Head with facial features
    head_rot = 30 if is_reading else 0
    if is_reading:
        # Smooth head tilting animation while reading
        head_rot += math.sin(pygame.time.get_ticks() * 0.003) * 8 + 5
    
    glPushMatrix()
    glTranslatef(0, 1.6, 0)
    glRotatef(head_rot, 1, 0, 0)
    draw_cube(0, 0, 0, 0.2, 0.25, 0.2, [1, 0.8, 0.6])  # Head
    
    # Eyes (left and right)
    draw_cube(-0.07, 0.05, 0.12, 0.03, 0.03, 0.02, [0, 0, 0])  # Left eye
    draw_cube(0.07, 0.05, 0.12, 0.03, 0.03, 0.02, [0, 0, 0])   # Right eye
    
    glPopMatrix()
    
    # Left arm with articulated upper and lower segments
    arm_rot = 45 if sitting else -arm_angle
    glPushMatrix()
    glTranslatef(-0.3, 1.1, 0)  # Left shoulder joint
    glRotatef(arm_rot * (1 - sitting_progress * 0.5), 1, 0, 0)
    
    # Upper arm
    draw_cube(0, -0.15, 0, 0.12, 0.35, 0.1, torso_color)
    
    # Lower arm (elbow joint)
    glPushMatrix()
    glTranslatef(0, -0.45, 0)
    draw_cube(0, 0, 0, 0.08, 0.3, 0.08, [1, 0.85, 0.7])  # Skin tone
    glPopMatrix()
    
    # Left hand on table when sitting
    if sitting and sitting_progress > 0.5:
        hand_reach = (sitting_progress - 0.5) * 2
        glPushMatrix()
        glTranslatef(0, -0.75, 0.2 * hand_reach)
        draw_cube(0, 0, 0, 0.08, 0.08, 0.1, [1, 0.85, 0.7])
        glPopMatrix()
    glPopMatrix()  # End left arm
    
    # Right arm with articulated upper and lower segments (holds book)
    glPushMatrix()
    glTranslatef(0.3, 1.1, 0)  # Right shoulder joint
    arm_raise = id_raise_progress * 90 if id_raise_progress > 0 else 0
    glRotatef((arm_rot + arm_raise) * (1 - sitting_progress * 0.5), 1, 0, 0)
    
    # Upper arm
    draw_cube(0, -0.15, 0, 0.12, 0.35, 0.1, torso_color)
    
    # Lower arm (elbow joint)
    glPushMatrix()
    glTranslatef(0, -0.45, 0)
    draw_cube(0, 0, 0, 0.08, 0.3, 0.08, [1, 0.85, 0.7])  # Skin tone
    
    # Book held in right hand - positioned to follow arm movement
    # Book remains visible during Phase 4 (walking to table) and all subsequent phases
    if has_book and not sitting:
        glPushMatrix()
        # Position book in hand at the end of the lower arm
        glTranslatef(0.1, -0.35, 0.05)
        draw_cube(0, 0, 0, 0.15, 0.2, 0.03, [1, 0, 0])
        glPopMatrix()
    
    glPopMatrix()  # End lower arm
    
    # Right hand on table when sitting
    if sitting and sitting_progress > 0.5:
        hand_reach = (sitting_progress - 0.5) * 2
        glPushMatrix()
        glTranslatef(0, -0.75, 0.2 * hand_reach)
        draw_cube(0, 0, 0, 0.08, 0.08, 0.1, [1, 0.85, 0.7])
        glPopMatrix()
    glPopMatrix()  # End right arm
    
    # Left leg with articulated upper and lower segments
    glPushMatrix()
    glTranslatef(-0.15, 0, 0)  # Left hip position
    leg_bend = 60 * sitting_progress  # Bend legs when sitting
    glRotatef(leg_bend, 1, 0, 0)
    
    # Upper leg (thigh)
    draw_cube(0, -0.2, 0, 0.12, 0.35, 0.12, [0.3, 0.3, 0.3])  # Pants
    
    # Lower leg (shin) with knee joint
    glPushMatrix()
    glTranslatef(0, -0.5, 0)
    draw_cube(0, 0, 0, 0.1, 0.35, 0.1, [0.3, 0.3, 0.3])  # Pants
    glPopMatrix()
    
    glPopMatrix()  # End left leg
    
    # Right leg with articulated upper and lower segments
    glPushMatrix()
    glTranslatef(0.15, 0, 0)  # Right hip position
    glRotatef(leg_bend, 1, 0, 0)
    
    # Upper leg (thigh)
    draw_cube(0, -0.2, 0, 0.12, 0.35, 0.12, [0.3, 0.3, 0.3])  # Pants
    
    # Lower leg (shin) with knee joint
    glPushMatrix()
    glTranslatef(0, -0.5, 0)
    draw_cube(0, 0, 0, 0.1, 0.35, 0.1, [0.3, 0.3, 0.3])  # Pants
    glPopMatrix()
    
    glPopMatrix()  # End right leg
    
    # ID card when showing (held in raised hand)
    if show_id_timer > 0 and id_raise_progress > 0.3:
        glPushMatrix()
        # Position card in the raised right hand
        glTranslatef(0.3 + id_raise_progress * 0.2, 0.8 + id_raise_progress * 0.5, 0.2)
        glRotatef(id_raise_progress * 30, 0, 1, 0)
        draw_cube(0, 0, 0, 0.09, 0.13, 0.008, [1, 1, 1])
        # Name on ID
        draw_cube(0, -0.03, 0.005, 0.06, 0.02, 0.005, [0.2, 0.2, 0.8])
        glPopMatrix()
    
    glPopMatrix()

def draw_human(pos, rot, color, is_reading=False, sitting=False):
    """Legacy function for backward compatibility"""
    draw_detailed_human(pos, rot, color, is_reading, sitting, 0, 0)

def draw_entrance_door(x, y, z):
    """Draw an entrance door model"""
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Door frame (dark metal)
    draw_cube(0, 0.8, 0, 0.15, 1.8, 0.05, [0.2, 0.2, 0.2])
    
    # Door panel (brownish wood color)
    draw_cube(0, 0.8, 0.1, 0.12, 1.6, 0.15, [0.6, 0.4, 0.2])
    
    # Door handle (brass)
    draw_cube(0.04, 0.8, 0.25, 0.03, 0.08, 0.03, [0.8, 0.7, 0.3])
    
    # Door glass effect (light blue transparent-looking part)
    glColor4f(0.3, 0.5, 0.8, 0.3)
    glBegin(GL_QUADS)
    vertices = [
        [0.06, 0.4, 0.11], [0.06, 1.2, 0.11],
        [-0.06, 1.2, 0.11], [-0.06, 0.4, 0.11]
    ]
    for v in vertices:
        glVertex3fv(v)
    glEnd()
    glColor3f(1, 1, 1)  # Reset color
    
    glPopMatrix()

def draw_scene():
    # Floor
    draw_cube(0, -1.2, 0, 12, 0.1, 12, [0.35, 0.35, 0.35])
    
    # Entrance Door
    draw_entrance_door(0, 0, 8.5)
    
    # Entrance archway/wall
    draw_cube(-3, 1.5, 8.3, 6, 1.5, 0.2, [0.5, 0.5, 0.5])
    
    # Reception Desk (with librarian behind it)
    draw_cube(0, -0.5, 2.5, 1.8, 0.5, 0.7, [0.5, 0.3, 0.1])
    
    # Librarian
    draw_detailed_human(librarian_pos, librarian_rot, [0.9, 0.7, 0.5], is_reading=False, sitting=False, sitting_progress=0, waist_bend=0)
    
    # Bookshelf structure
    draw_cube(-6, 0.5, -4, 0.2, 1.5, 2.5, [0.3, 0.15, 0.05])
    
    # Populate bookshelf with many colored books - 3 rows of shelves
    book_colors = [
        [0, 0, 1],      # blue
        [0, 1, 0],      # green
        [1, 1, 0],      # yellow
        [1, 0.5, 0],    # orange
        [1, 0, 1],      # magenta
        [0, 1, 1],      # cyan
        [0.5, 0.5, 0],  # dark yellow
        [0.5, 0, 0.5],  # purple
        [0, 0.5, 0.5],  # teal
        [0.7, 0.3, 0],  # brown
        [0.8, 0.8, 1]   # light blue
    ]
    
    shelf_y_positions = [0.25, 0.75, 1.25]  # 3 shelf rows (y positions)
    books_per_shelf = 11  # Number of books per shelf
    z_start = -5.0  # Starting z position
    z_end = -3.0    # Ending z position
    z_spacing = (z_end - z_start) / (books_per_shelf - 1)  # Spacing between books
    
    # Nested loop: iterate through each shelf row and populate with books
    for shelf_idx, shelf_y in enumerate(shelf_y_positions):
        for book_idx in range(books_per_shelf):
            book_z = z_start + (book_idx * z_spacing)
            
            # Skip the position of the special red book (middle shelf at z=-4)
            # This preserves the has_book interaction logic
            if shelf_idx == 1 and abs(book_z - (-4.0)) < 0.2:
                continue
            
            # Draw book with color cycling through the palette
            color_idx = (shelf_idx * books_per_shelf + book_idx) % len(book_colors)
            draw_cube(-5.8, shelf_y, book_z, 0.1, 0.35, 0.15, book_colors[color_idx])
    
    # Special pickable red book (only drawn if not yet picked up)
    if not has_book:
        draw_cube(-5.8, 0.8, -4, 0.1, 0.3, 0.2, [1, 0, 0])
    
    # Table 1: ለሌሎች ተማሪዎች
    draw_cube(5, -0.5, -4, 1.5, 0.5, 1.5, [0.5, 0.3, 0.1])
    for student in other_students:
        draw_human(student['pos'], 0, student['color'], is_reading=True, sitting=True)
    
    # Table 2: ለዋናው ተማሪ (የራሱ መማሪያ ጠረጴዛ)
    draw_cube(-1, -0.5, -5, 1.2, 0.5, 1, [0.5, 0.3, 0.1])
    if phase >= 5: # ዋናው ተማሪ እያነበበ ከሆነ መጽሐፉን ጠረጴዛው ላይ እናደርጋለን
        draw_cube(-1, 0.1, -5.2, 0.2, 0.02, 0.3, [1, 0, 0])

def draw_ui_text():
    """Draw 2D HUD text overlay with control instructions"""
    # Save the current matrix state
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # Set orthographic projection for 2D text rendering
    display = pygame.display.get_surface().get_size()
    glOrtho(0, display[0], display[1], 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable lighting and depth test for 2D rendering
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # Set text color to white
    glColor3f(1.0, 1.0, 1.0)
    
    # Control strings to display
    controls = [
        "W = Moving",
        "P = Pick a book",
        "I = Show ID",
        "S = Start",
        "Q = Exit"
    ]
    
    # Draw each line of text at the top-left corner
    line_height = 20
    for i, text in enumerate(controls):
        x = 10
        y = 10 + (i * line_height)
        glRasterPos2f(x, y)
        for char in text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Re-enable lighting and depth test
    glEnable(GL_LIGHTING)
    glEnable(GL_DEPTH_TEST)
    
    # Restore the previous matrix state
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_ui():
    """Update window title with phase-specific instructions"""
    global phase, has_id, has_book, is_sitting, sitting_progress
    
    # Detailed phase descriptions with clear instructions
    phase_messages = {
        0: "PHASE 0 - ENTRANCE | Press [W] to walk to reception desk",
        1: "PHASE 1 - RECEPTION | Press [I] to show your ID card",
        2: "PHASE 2 - APPROVED | Press [W] to walk to the bookshelf",
        3: "PHASE 3 - BOOKSHELF | Press [P] to pick up the red book",
        4: "PHASE 4 - HEADING TO TABLE | Walking to study area...",
        5: "PHASE 5 - READING | Enjoying a good book at the study table!"
    }
    
    # Add current action status
    status = ""
    if phase == 1 and not has_id:
        status = " | [Waiting for ID]"
    elif phase == 1 and has_id and show_id_timer > 0:
        status = f" | [ID shown - {show_id_timer//20}s remaining]"
    elif phase == 3 and not has_book:
        status = " | [Book available]"
    elif phase == 5 and is_sitting:
        status = f" | [Sitting {int(sitting_progress * 100)}%]"
    
    msg = phase_messages.get(phase, "UNKNOWN PHASE")
    pygame.display.set_caption(f"{msg}{status} | Press [Q] to quit")

def main():
    global student_pos, student_target_pos, student_rot, student_target_rot, arm_angle, id_raise_progress, phase, has_id, id_shown, has_book, show_id_timer, is_sitting, sitting_progress, waist_bend
    pygame.init()
    
    # Initialize GLUT for bitmap text rendering
    glutInit()
    
    display = (1000, 700)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    
    # Better camera positioning to see entrance, reception, and study areas
    glTranslatef(0, -2.5, -14)
    glRotatef(20, 1, 0, 0)
    
    # Initialize lighting for realistic visuals
    setup_lighting()
    glEnable(GL_DEPTH_TEST)

    clock = pygame.time.Clock()

    while True:
        update_ui()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); return
            if event.type == KEYDOWN:
                # Quick exit
                if event.key == K_q:
                    pygame.quit()
                    return
                
                # --- STATE MACHINE: Phase Transitions ---
                if event.key == K_w:
                    if phase == 0:  # Entrance: Start walking to reception
                        if student_target_pos[2] <= 3.5:  # Close enough to reception
                            phase = 1
                    elif phase == 1 and has_id:  # ID Check passed: Go to bookshelf
                        phase = 2
                    elif phase == 2 and student_pos[0] <= -5.2:  # Near bookshelf: Pick book
                        phase = 3
                    elif phase == 3 and has_book:  # Book picked: Go to table
                        phase = 4
                
                # Show ID card at reception (Phase 1)
                if event.key == K_i and phase == 1 and not has_id:
                    has_id = True
                    id_shown = True
                    show_id_timer = 120  # 2 seconds at 60fps
                    id_raise_progress = 0  # Start animation
                
                # Pick book from shelf (Phase 3)
                if event.key == K_p and phase == 3 and not has_book:
                    has_book = True

        # --- STATE MACHINE: Movement Logic with Smooth Interpolation ---
        if phase == 0:  # ENTRANCE: Walk from door to reception desk
            student_target_pos[2] -= 0.05  # Continuous walking toward reception
            student_target_rot = 0  # Face forward
            arm_angle = math.sin(pygame.time.get_ticks() * 0.01) * 25  # Natural walking swing
        
        elif phase == 1:  # ID CHECK: Wait at reception desk
            student_target_rot = 0  # Face forward toward librarian
            student_target_pos[2] = 3.2  # Stay at desk
            arm_angle = 0 if show_id_timer == 0 else arm_angle  # Stop arm swing after ID shown
            
        elif phase == 2:  # APPROVED: Walk to bookshelf
            student_target_rot = 90  # Turn toward bookshelf
            if student_target_pos[0] > -5.5:  # Not at shelf yet
                student_target_pos[0] -= 0.08  # Walk toward shelf
                student_target_pos[2] = -4
            else:  # Reached bookshelf
                student_target_pos[0] = -5.8
                student_target_pos[2] = -4
                phase = 3  # Auto-transition to shelf phase
            arm_angle = math.sin(pygame.time.get_ticks() * 0.01) * 20
        
        elif phase == 3:  # BOOKSHELF: Pick book
            student_target_rot = 90  # Face the shelf
            student_target_pos[0] = -5.8
            student_target_pos[2] = -4
            arm_angle = 45  # Reaching arm
            
        elif phase == 4:  # WALK TO TABLE: Head to study area
            student_target_rot = 0
            target_x, target_z = -1, -4.5
            # Move X first, then Z
            if abs(student_target_pos[0] - target_x) > 0.1:
                student_target_pos[0] += 0.08
            elif abs(student_target_pos[2] - target_z) > 0.1:
                student_target_pos[2] -= 0.08
            else:
                # Reached table: transition to reading phase
                phase = 5
                is_sitting = True
            arm_angle = math.sin(pygame.time.get_ticks() * 0.01) * 15
        
        elif phase == 5:  # READING: Sit and read
            student_target_rot = 0
            student_target_pos[0] = -1
            student_target_pos[2] = -4.5
            arm_angle = 0  # No arm swing while sitting

        # Smooth position interpolation
        student_pos = interpolate_position(student_pos, student_target_pos, INTERPOLATION_SPEED)
        
        # Smooth rotation interpolation
        rot_diff = student_target_rot - student_rot
        # Handle wrapping (shortest rotation path)
        if rot_diff > 180:
            rot_diff -= 360
        elif rot_diff < -180:
            rot_diff += 360
        student_rot += rot_diff * ROTATION_SPEED
        
        # Update ID raise animation (smooth raise and lower)
        if show_id_timer > 0:
            show_id_timer -= 1
            id_raise_progress = min(1.0, id_raise_progress + 0.03)
        else:
            id_raise_progress = max(0.0, id_raise_progress - 0.05)
        
        # Smooth sitting animation
        if is_sitting and sitting_progress < 1:
            sitting_progress += 0.05
            waist_bend = 35  # Bending angle at waist
        elif not is_sitting and sitting_progress > 0:
            sitting_progress -= 0.05
            if sitting_progress <= 0:
                sitting_progress = 0
                waist_bend = 0

        # --- Drawing ---
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        
        draw_scene()
        
        # Main student with detailed model and smooth animations
        draw_detailed_human(student_pos, student_rot, [0.2, 0.5, 1.0], 
                           is_reading=(phase==5), sitting=is_sitting, 
                           sitting_progress=sitting_progress, waist_bend=waist_bend)
        
        # Draw 2D HUD overlay with controls
        draw_ui_text()
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()