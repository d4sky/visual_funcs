import numpy as np
import pygame
import threading

from tks import *

def Calculate_denominators():
  nasobky = [2.0, 1.25, 2.0, 2.0]
  denom1 = [1]
  denom2 = [1]
  for i in range(20):
    for nasobok in nasobky:
      new_val = denom1[-1]*nasobok
      denom1.append(new_val)
    for nasobok in list(reversed(nasobky)):
      new_val = denom2[-1]/nasobok
      denom2.append(new_val)

  #denoms = list(reversed(denom1[1:])) + denom2
  denoms = list(reversed(denom1)) + denom2[1:]
  #denoms = list(reversed(denom1[1:])) + denom2[1:]
  return denoms

class Ticks:
    def __init__(self):
        self.Nmin = 5
        self.Navg = 10
        self.Nmax = 15

class Axis:
    def __init__(self):
        self.incr  = 10.0
        self.tikcs = Ticks()

class Area():
    def __init__(self, inpID = 0, x0 = 0, y0 = 0, axisLines=[], denominators = [], width=100, height=100, margin=0, color = 'white', screen=None, font=None, in3d=False):
        self.E0      = np.array([x0, y0], dtype=np.int32)
        self.w       = width
        self.h       = height
        self.margin  = margin
        self.color   = color
        self.ID      = inpID
        
        self.R0 = np.array([self.w//2, self.h//2], dtype=np.int32)

        # Scaling factor
        self.scale    = 1.0  
        self.scaleX, self.scaleY = 1.0, 1.0 
        
        self.dragging_curve = None  # Track the currently dragged curve
        self.dragging_all   = False
        
        self.screen = screen
        self.font   = font
        
        #self.lock = lck
        
        self.revy = np.array([1.0, -1.0])
        self.tick = 5
        
        self.Xaxis, self.Yaxis, self.Zaxis = Axis(), Axis(), Axis()
        self.Xlabels, self.Ylabels, self.Zlabels = [], [], []
        self.denominators = denominators

        self.curves  = []
        self.diags   = {}
        
        self.systems = axisLines
        
        self.in3d = in3d
        self.rotation_matrix = np.eye(3)
        
    def get_screen_coords(self, inp_coords):
        screen_coords = self.E0 + self.R0 + inp_coords * np.array([self.scaleX, self.scaleY]) * self.revy
        return screen_coords.astype(np.int32)
        
    def get_real_coords(self, screen_point):
        scaled_coords = (np.array(screen_point) - self.R0 - self.E0) / np.array([self.scaleX, self.scaleY])
        # Flip the y-coordinate by multiplying by [-1, 1]
        return scaled_coords * self.revy
        
    def zoom(self, mouse_pos, zoom_factor):
        real_pos = self.get_real_coords(mouse_pos)
        self.scaleX = self.scaleX * zoom_factor
        self.scaleY = self.scaleY * zoom_factor

        new_screen_pos = self.get_screen_coords(real_pos)  # Already a NumPy array
 
        delta_shift = new_screen_pos - mouse_pos
        self.R0 = self.R0 - delta_shift
        self.recalculate_grids()
                
    def draw(self):
        def Draw_labels(inp_labels, axis_vector, tick_vector, tick_span, axis_line_color = "black", axis_font_color="blue", middle_label = True):
          factor     = 1
          add_factor = 0
          if len(inp_labels) > 1:
            differences = [np.linalg.norm(inp_labels[i+1] - inp_labels[i]) for i in range(len(inp_labels) - 1)]
            adiff = np.min(differences)  # Get the minimum difference
            
            if adiff >= 1:
              add_factor = 0
            else:
              add_factor = 1
            for factor in range(1,10000):
              adiff *= 10    
              if adiff > 1:
                break 
                
          factor += add_factor
          Nminor = 5
          minor_span = tick_span/Nminor
          baseG = 200
          thinG = baseG + 25
          major_color = (baseG, baseG, baseG)
          minor_color = (thinG, thinG, thinG)
          for Pos in inp_labels:
            screen_coords = self.get_screen_coords(Pos)
            if np.linalg.norm(Pos) != 0.0:
                renderLabel   = self.font.render(f"{np.sum(Pos):.{factor}f}", True, axis_font_color)
                self.screen.blit(renderLabel, (screen_coords + tick_vector))
            else: 
                if middle_label:
                    renderLabel   = self.font.render(f"{np.sum(Pos):.{factor}f}", True, axis_font_color)
                    self.screen.blit(renderLabel, (screen_coords + tick_vector))

            #pygame.draw.line(self.screen, axis_line_color, (screen_coords - tick_vector*self.tick), (screen_coords + tick_vector*self.tick), 1)
            pygame.draw.line(self.screen, major_color, (screen_coords - tick_vector*aDim), (screen_coords + tick_vector*aDim), 1)
            ''' 
            for mi in range(1,Nminor):
                mPos = Pos + mi*minor_span*axis_vector
                m_screen_coords = self.get_screen_coords(mPos)
                #print(mPos, m_screen_coords, tick_vector*aDim)
                pygame.draw.line(self.screen, minor_color, (m_screen_coords - tick_vector*aDim), (m_screen_coords + tick_vector*aDim), 1)
            '''
            
        graphics_area = pygame.Rect(self.E0[0], self.E0[1], self.w - self.margin, self.h)
        self.screen.set_clip(graphics_area)
        pygame.draw.rect(self.screen, self.color, graphics_area)
        
        if self.in3d:
            self.all_curves = [curve for shared_system in self.systems for curve in shared_system.curves] # + [curve for curve in self.curves] 
            for curve in self.all_curves:  
                if len(curve.r_vec) > 1: #break 
                    screen_coors = self.get_screen_coords3d(curve.r_vec)
                    for i in range(len(screen_coors) - 1):
                        pygame.draw.line(self.screen, curve.color, (screen_coors[i]), (screen_coors[i+1]), curve.thickness)
        else:
            self.all_curves = [(curve, ['xy']) for shared_system in self.systems for curve in shared_system.curves] + [(curve, self.diags[curve]) for curve in self.curves]
                
            Draw_labels(self.Xlabels, np.array((1.0, 0.0)), np.array((0.0, 1.0)), self.Xaxis.incr)
            Draw_labels(self.Ylabels, np.array((0.0, 1.0)), np.array((1.0, 0.0)), self.Yaxis.incr, middle_label = False)
            for curve, diags in self.all_curves:  
               if np.count_nonzero(np.any(curve.xyz != 0, axis=1)) > 1:  
                  up_idx = curve.current_index + 1
                  for diag in diags:
                    if   diag == 'xy':
                        screen_coors = self.get_screen_coords(np.vstack((curve.xyz[:up_idx,0], curve.xyz[:up_idx,1])).T)
                    elif diag == 'tx':
                        screen_coors = self.get_screen_coords(np.vstack((curve.t_vec[:up_idx], curve.xyz[:up_idx,0])).T)
                    elif diag == 'ty':
                        screen_coors = self.get_screen_coords(np.vstack((curve.t_vec[:up_idx], curve.xyz[:up_idx,1])).T)
                    elif diag == 'tz':
                        screen_coors = self.get_screen_coords(np.vstack((curve.t_vec[:up_idx], curve.xyz[:up_idx,2])).T)
                        
                    act_color, act_thickness = curve.props[diag]
                    for i in range(len(screen_coors) - 1):
                        #pygame.draw.line(self.screen, curve.color, (screen_coors[i]), (screen_coors[i+1]), curve.thickness)
                        pygame.draw.line(self.screen, act_color, (screen_coors[i]), (screen_coors[i+1]), act_thickness)
                        
                    '''
                    last_point = screen_coors[-1]
                    circle_radius = 5  # Set the radius of the circle
                    outline_thickness = 2  # Set the thickness of the outline
                    
                    pygame.draw.circle(self.screen, curve.color, last_point, circle_radius)
                    # Drawing the circle with only the outline
                    pygame.draw.circle(self.screen, curve.color, last_point, circle_radius+outline_thickness, outline_thickness)
                    '''
        
    def set_scale(self, equal = True):
        all_x = []
        for ci, curve in enumerate(self.curves):
          up_idx = curve.current_index + 1
          for diag in self.diags[curve]:
            #diag_type = self.diags[ci]
            diag_type = diag
            if   diag_type[0] == 'x':
                #all_x.append(curve.x_vec)
                all_x.append(min(curve.xyz[:up_idx,0]))
                all_x.append(max(curve.xyz[:up_idx,0]))
            elif diag_type[0] == 't':
                #all_x.append(curve.t_vec)
                all_x.append(min(curve.t_vec))
                all_x.append(max(curve.t_vec))
                
        all_y = []
        for ci, curve in enumerate(self.curves):
          for diag in self.diags[curve]:
            #diag_type = self.diags[ci]
            diag_type = diag
            if   diag_type[1] == 'x':
                #all_y.append(curve.x_vec)
                all_y.append(min(curve.xyz[:up_idx,0]))
                all_y.append(max(curve.xyz[:up_idx,0]))
            elif diag_type[1] == 'y':
                #all_y.append(curve.y_vec)
                all_y.append(min(curve.xyz[:up_idx,1]))
                all_y.append(max(curve.xyz[:up_idx,1]))
            elif diag_type[1] == 'z':
                #all_y.append(curve.z_vec)
                all_y.append(min(curve.xyz[:up_idx,2]))
                all_y.append(max(curve.xyz[:up_idx,2]))

        all_x.append(0.0)
        all_y.append(0.0)
        if all_x and all_y:
            self.min_x = min(float('inf'), min(all_x))
            self.max_x = max(float('-inf'), max(all_x))
            self.min_y = min(float('inf'), min(all_y))
            self.max_y = max(float('-inf'), max(all_y))
            
            #print(f"MinMax for area {self.ID}",  self.min_x, self.max_x, self.min_y, self.max_y)
            spanX = (self.max_x - self.min_x)*1.2 
            self.scaleX = self.w/2.0 if spanX == 0.0 else self.w/spanX
            
            spanY = (self.max_y - self.min_y)*1.2
            self.scaleY = self.h/2.0 if spanY == 0.0 else self.h/spanY
           
            if equal:
              self.scale = min(self.scaleX, self.scaleY)
              self.scaleX, self.scaleY = self.scale, self.scale
              
            middleX = (self.max_x + self.min_x)/2.0 
            middleY = (self.max_y + self.min_y)/2.0 
            self.R0 = np.array([self.w//2, self.h//2], dtype=np.int32) + [-middleX*self.scaleX, middleY*self.scaleY]
 
        self.recalculate_grids()
            
    def recalculate_grids(self):
        for denominator in self.denominators:
            if self.w/self.scaleX/denominator >= 10.0:
                self.Xaxis.incr = denominator
                break
                
        for denominator in self.denominators:
            if self.h/self.scaleY/denominator >= 10.0:
                self.Yaxis.incr = denominator
                break
                
        self.make_grids()
        
    def make_grids(self):
        if self.in3d:
            Xlabels_list = [[wi * self.Xaxis.incr, 0.0, 0.0] for wi in range(-100, 101)]
            Ylabels_list = [[0.0, wi * self.Yaxis.incr, 0.0] for wi in range(-100, 101)]
            Zlabels_list = [[0.0, 0.0, wi * self.Zaxis.incr] for wi in range(-100, 101)]
            self.Xlabels = np.array(Xlabels_list)
            self.Ylabels = np.array(Ylabels_list)
            self.Zlabels = np.array(Zlabels_list)
        else:
            Xlabels_list = [[wi * self.Xaxis.incr, 0.0] for wi in range(-100, 101)]
            Ylabels_list = [[0.0, wi * self.Yaxis.incr] for wi in range(-100, 101)]
            self.Xlabels = np.array(Xlabels_list)
            self.Ylabels = np.array(Ylabels_list)
            # Remove the origin point from Ylabels if required
            #self.Ylabels = self.Ylabels[np.any(self.Ylabels != [0.0, 0.0], axis=1)]

class PygameWindow():
    def __init__(self, tkinter_instance, denoms, axisLines, width=800, height=800, margin=0, axis3dLines = []):
        self.tkinter_instance = tkinter_instance  # Store the Tkinter instance
        
        self.Xlen = width
        self.Ylen = height

        self.zoom_in  = 1.1
        self.zoom_out = 1/1.1

        self.revy   = np.array([1.0, -1.0])
        self.Areas  = {}
        self.denoms = denoms
        self.aLines = axisLines
        self.a3DLines = axis3dLines
        
        self.screen = None
        self.a_font = None
        
        self.running = True

    def arrange_areas(self, style = 1):
        def append_area(aID, x1, y1, inpW, inpH, color=(255,255,255)):
            self.Areas[aID] = Area(aID, x1, y1, self.aLines, self.denoms, inpW, inpH, color=color, screen=self.screen, font=self.a_font)
            #self.Areas[aID] = Area(aID, x1, y1, self.a3DLines, self.denoms, inpW, inpH, color=color, screen=self.screen, font=self.a_font, in3d=True)

        self.Areas = {}
        if   style == 1:
            Xlen = self.Xlen
            Ylen = self.Ylen
            append_area(1, 0,  0   , Xlen, Ylen, area_colors[1])
        elif style == 2:
            Xlen = self.Xlen
            Ylen = self.Ylen//2
            append_area(1, 0,  0   , Xlen, Ylen, area_colors[1])
            append_area(2, 0,  Ylen, Xlen, Ylen, area_colors[2])
        elif style == 3:
            Xlen = self.Xlen
            Ylen = self.Ylen//3
            append_area(1, 0,      0, Xlen, Ylen, area_colors[1])
            append_area(2, 0,   Ylen, Xlen, Ylen, area_colors[2])
            append_area(3, 0, 2*Ylen, Xlen, Ylen, area_colors[3])
        elif style == 4:
            Xlen = self.Xlen//2
            Ylen = self.Ylen//2
            append_area(1, 0,       0, Xlen, Ylen, area_colors[1])
            append_area(2, Ylen,    0, Xlen, Ylen, area_colors[2])
            append_area(3, 0,    Ylen, Xlen, Ylen, area_colors[3])
            append_area(4, Ylen, Ylen, Xlen, Ylen, area_colors[4])

    def get_active_area(self, pos):
        x, y = pos
        for area in self.Areas.values():
            # Check if pos is within the bounds of the Area
            if (area.E0[0] <= x < area.E0[0] + area.w) and (area.E0[1] <= y < area.E0[1] + area.h):
                return area
        return None

    def start(self):
        pygame.init()        
        pygame.display.set_caption("2D Visual")

        self.screen = pygame.display.set_mode((self.Xlen, self.Ylen))
        self.a_font = pygame.font.Font(None, 14)  # Default font 
        self.arrange_areas(1)
        
        #clock = pygame.time.Clock()
        dragging_all   = False
        dragging_curve = False
        last_mouse_pos = (0, 0)

        active_area  = None  # To track which Area is being interacted with
        area_changed = False
        
        dragging_rotate = False

        self.running = True
        # Pygame main loop
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Pygame window closing...")
                    self.running = False  # Set running to False to stop both windows
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False  # Set running to False to stop both windows
                        
                elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    new_active_area = self.get_active_area(event.pos)
                    if new_active_area != active_area:
                        area_changed = True
                        active_area  = new_active_area
                    else:
                        area_changed = False

                    if active_area is not None:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            if   event.button == 1:  # Left mouse button
                                dragging_rotate = True
                                last_mouse_pos = event.pos
                            elif event.button == 2:  # Middle mouse button
                                dragging_all = True
                                last_mouse_pos = event.pos  # Get the current mouse position
                            elif event.button == 3: # Right mouse button
                                real_pos = active_area.get_real_coords(event.pos)
                                '''
                                if active_area.handle_mouse_button_down(real_pos):
                                    dragging_curve = True
                                    last_mouse_pos = event.pos
                                '''
                            elif event.button == 4:  # Scroll up (zoom in)
                                active_area.zoom(event.pos, self.zoom_in)
                            elif event.button == 5:  # Scroll down (zoom out)
                                active_area.zoom(event.pos, self.zoom_out)
                                
                        elif event.type == pygame.MOUSEMOTION:
                            if area_changed:
                                dragging_all = False
                                dragging_curve = False
                                
                            if dragging_all:
                                current_mouse_pos = pygame.mouse.get_pos()
                                delta_pos = np.array(current_mouse_pos) - np.array(last_mouse_pos)
                                if np.any(np.abs(delta_pos) > 0):
                                  active_area.R0 += delta_pos
                                last_mouse_pos = current_mouse_pos  # Update the last mouse position
                                
                            if dragging_rotate:
                                # Calculate mouse drag delta
                                current_mouse_pos = pygame.mouse.get_pos()
                                delta_pos = np.array(current_mouse_pos) - np.array(last_mouse_pos)
                                
                                # Compute a rotation angle based on mouse movement
                                angle_x = np.radians(delta_pos[1] * 0.5)  # Up/down controls X-axis rotation
                                angle_y = np.radians(delta_pos[0] * 0.5)  # Left/right controls Y-axis rotation
                                
                                # Define rotation matrices around the X and Y axes
                                rotation_x = np.array([
                                    [1, 0, 0],
                                    [0, np.cos(angle_x), -np.sin(angle_x)],
                                    [0, np.sin(angle_x), np.cos(angle_x)]
                                ])
                                
                                rotation_y = np.array([
                                    [np.cos(angle_y), 0, np.sin(angle_y)],
                                    [0, 1, 0],
                                    [-np.sin(angle_y), 0, np.cos(angle_y)]
                                ])
                                
                                # Update the overall rotation matrix by combining new rotations
                                active_area.rotation_matrix = rotation_y @ rotation_x @ active_area.rotation_matrix
                                last_mouse_pos = current_mouse_pos    
        
                        elif event.type == pygame.MOUSEBUTTONUP:
                            if event.button == 1:  # Left mouse button released
                                dragging_rotate = False
                            if event.button == 2:  # Middle mouse button
                                dragging_all = False
                            if event.button == 3:  # Left mouse button
                                active_area.dragging_curve = None  # Stop dragging
            
            # Draw each area individually
            self.screen.fill((255, 255, 255))  # Clear the screen
            for area in self.Areas.values():
                area.draw()  # Separate function for each Area
            pygame.display.flip()

        pygame.quit()

        if not self.running:
            print("Closing Tkinter window from Pygame...")
            self.tkinter_instance.quit()  # Close Tkinter window
                
    def handle_mouse_button_up(self):
        pass

denominators = Calculate_denominators()
aDim   = 100000
axis   = funs.LineBunch([([-aDim, 0], [aDim, 0]), ([0, -aDim], [0, aDim])], 2)
axis3d = funs.LineBunch3d(aDim)

pygame_instance = PygameWindow(None, denominators, [axis], 1000, 1000, axis3dLines = [axis3d]) 
tkinter_instance = TkinterWindow(pygame_instance, 600, 1000, 1000)

pygame_instance.tkinter_instance = tkinter_instance

# Start the Pygame window in a separate thread
pygame_thread = threading.Thread(target=pygame_instance.start)
pygame_thread.start()

# Start the Tkinter window in the main thread (important!)
tkinter_instance.mainloop()

# Ensure the Pygame thread joins properly
pygame_thread.join()

