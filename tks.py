import sqlite3
import io

import tkinter as tk

from tkinter import colorchooser, simpledialog, messagebox
from PIL import Image, ImageTk

import funs

gr_types = {}
gr_types[0] = ['xy']
gr_types[1] = ['xy', 'tx', 'ty']
gr_types[2] = ['xyz', 'tx', 'ty', 'tz']

dg_types = {}
dg_types[0] = 'xy'
dg_types[1] = 'tx'
dg_types[2] = 'ty'
dg_types[3] = 'tz'
dg_types[4] = 'xyz'

fn_label = {}
fn_label['xy'] = "y = f(x)"
fn_label['tx'] = "x = f(t)"
fn_label['ty'] = "y = f(t)"
fn_label['tz'] = "z = f(t)"
fn_label['xyz'] = "z = f(x,y)"

area_colors = {}
area_colors[1] = (255, 255, 255)
area_colors[2] = (212, 255, 255)
area_colors[3] = (255, 232, 255)
area_colors[4] = (255, 255, 222)

def Resize_formula_image(inp_image):
    # Resize the image manually while preserving aspect ratio
    image_width, image_height = inp_image.size
    max_width = 100
    max_height = 50

    max_width = 100
    max_height = 50

    # Calculate the new size based on the aspect ratio
    if image_width > image_height:
        new_width = max_width
        new_height = int(new_width * image_height / image_width)
    else:
        new_height = max_height
        new_width = int(new_height * image_width / image_height)

    # Resize the image with anti-aliasing for smoother results
    resized_image = inp_image.resize((new_width, new_height), Image.LANCZOS)

    # Convert to Tkinter format
    return ImageTk.PhotoImage(resized_image)

class AreaPtr:
     def __init__(self, areaID):
         self.aid = areaID
         self.curves = {}

class ControlPanel:
    def __init__(self, parent_frame, shared_item, what="curve_or_system", param='', min_value=20, max_value=200, initial_value=80, step=5, sFactor = 1.0, show_slider = True, alt_name = '', addIncr = 0.0):
        self.parent_frame = parent_frame
        self.shared_item = shared_item
        self.what = what
        self.param = param
        #self.pLabel = param_label

        self.DEC_FACTOR = sFactor
        
        self.act_value = initial_value
        self.min_value = min_value
        self.max_value = max_value
        self.step      = step
        
        self.addIncr   = addIncr
        self.animating = None  # Keeps track of which animation is active

        self.scale_set_values()
                
        # Create a frame to hold all elements of the control panel
        self.control_frame = tk.Frame(parent_frame, bd=1, relief=tk.SOLID)
        self.control_frame.pack(pady=5, padx=10, fill=tk.X)
        
        # Parameter name label on the left
        param_name = alt_name if alt_name != '' else param
        #self.param_label = tk.Label(self.control_frame, text=param, width=5, anchor="w")
        self.param_label = tk.Label(self.control_frame, text=param_name, width=5, anchor="w")
        self.param_label.pack(side=tk.LEFT, padx=5)
        
        # Current value label next to the slider
        #self.value_label = tk.Label(self.control_frame, text=str(int(initial_value)), width=6)
        #self.value_label = tk.Label(self.control_frame, text=str(int(initial_value)))
     
        self.value_label = tk.Label(self.control_frame, text=str(int(self.scaled_act_value)))
        self.value_label.pack(side=tk.LEFT, padx=5)

        # Decrease button
        self.decrease_button = tk.Button(self.control_frame, text=f"-{self.step}", command=self.decrease_value)
        self.decrease_button.pack(side=tk.LEFT, padx=5)

        # Minimum value label
        #self.min_label = tk.Label(self.control_frame, text=str(self.min_value))
        self.min_label = tk.Label(self.control_frame, text=f"{self.min_value:.2f}")
        self.min_label.pack(side=tk.LEFT, padx=2)

        if show_slider:
            self.slider = tk.Scale(
                self.control_frame,
                from_ = self.scaled_min_value,
                to_   = self.scaled_max_value,
                orient=tk.HORIZONTAL,
                command=self.update_value,
                showvalue=0
            )
            self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Maximum value label
        #self.max_label = tk.Label(self.control_frame, text=str(self.max_value))
        self.max_label = tk.Label(self.control_frame, text=f"{self.max_value:.2f}")
        self.max_label.pack(side=tk.LEFT, padx=2)
        
        # Increase button
        self.increase_button = tk.Button(self.control_frame, text=f"+{self.step}", command=self.increase_value)
        self.increase_button.pack(side=tk.LEFT, padx=5)

        # Animation and properties buttons
        self.animate_left_button = tk.Button(self.control_frame, text="<", command=lambda: self.toggle_animation("left"))
        self.animate_left_button.pack(side=tk.LEFT, padx=2)

        self.animate_right_button = tk.Button(self.control_frame, text=">", command=lambda: self.toggle_animation("right"))
        self.animate_right_button.pack(side=tk.LEFT, padx=2)

        self.properties_button = tk.Button(self.control_frame, text="...", command=self.show_properties)
        self.properties_button.pack(side=tk.LEFT, padx=5)

        # Set initial value
        self.slider.set(self.scaled_act_value)

    def scale_set_values(self):
        self.scaled_min_value = int(self.min_value * self.DEC_FACTOR)
        self.scaled_max_value = int(self.max_value * self.DEC_FACTOR)
        self.scaled_act_value = int(self.act_value * self.DEC_FACTOR)
        self.scaled_step      = int(self.step * self.DEC_FACTOR)

    def toggle_animation(self, direction):
        # Stop any ongoing animation before starting a new one
        if self.animating == direction:
            self.stop_animation()
        else:
            self.stop_animation()  # Stop opposite animation, if running
            self.animating = direction
            if direction == "left":
                self.animate_left_button.config(text="||")
                self.animate_right_button.config(text=">")
                self.scaled_animate_step = -self.scaled_step
                self.animate_step = -self.step
            elif direction == "right":
                self.animate_right_button.config(text="||")
                self.animate_left_button.config(text="<")
                self.scaled_animate_step = self.scaled_step
                self.animate_step = self.step
            self.perform_animation_step()  # Start the animation loop

    def perform_animation_step(self):
        if self.animating is None:
            return  # Stop if animation has been cancelled

        new_act_val = self.act_value + self.animate_step
        if self.min_value <= new_act_val <= self.max_value:
            self.update_value(new_act_val, False) 
        else:
            self.stop_animation()  # Stop if it hits boundary

        # Schedule the next step
        if self.animating:
            self.parent_frame.after(100, self.perform_animation_step)  # Adjust delay for animation speed

    def stop_animation(self):
        self.animating = None
        self.animate_left_button.config(text="<")
        self.animate_right_button.config(text=">")

    def decrease_value(self):
        new_act_val = self.act_value - self.step
        if new_act_val > self.min_value:
            self.update_value(new_act_val, False) 

    def increase_value(self):
        new_act_val = self.act_value + self.step
        if new_act_val < self.max_value:
            self.update_value(new_act_val, False) 

    def update_value(self, val, from_slider = True):
        if from_slider:
            float_val = float(val)/self.DEC_FACTOR
            self.value_label.config(text=f"{float_val:.2f}")  # Update label with float value
            self.act_value = float_val
        else:
            self.act_value = val
            self.scaled_act_value = int(self.act_value * self.DEC_FACTOR)
            self.slider.config(command='')
            self.slider.set(self.scaled_act_value)
            self.slider.config(command=self.update_value)
            self.value_label.config(text=f"{val:.2f}")  # Update label with float value
            
        if   self.what == 'curve':
          self.shared_item.set_param(self.param, self.act_value)
          self.shared_item.calculate(self.addIncr)
        elif self.what == 'system':
          self.shared_item.set_param(self.param, self.act_value)
          self.shared_item.calculate() 
        else:
          print("Wrong passed type")

    def show_properties(self):
        # Open a new Toplevel window as a modal popup
        self.popup = tk.Toplevel(self.parent_frame)
        self.popup.title(f"Properties for {self.param}")
        self.popup.geometry("400x300")
        self.popup.transient(self.parent_frame)  # Makes the popup modal
        self.popup.grab_set()

        # Validation command to ensure only integers are entered
        vcmd = (self.popup.register(self.validate_integer), '%P')
        
        # Display main label with the curve name
        tk.Label(self.popup, text=f"Curve: {self.shared_item.name}", font=("Arial", 12, "bold")).pack(pady=5)

        # Display parameter name
        tk.Label(self.popup, text=f"Parameter: {self.param}", font=("Arial", 10)).pack(pady=5)

        # Min value input
        tk.Label(self.popup, text="Min Value:").pack(anchor="w", padx=10)
        self.min_entry = tk.Entry(self.popup)
        self.min_entry.insert(0, str(self.min_value))
        self.min_entry.pack(fill="x", padx=10)

        # Max value input
        tk.Label(self.popup, text="Max Value:").pack(anchor="w", padx=10)
        self.max_entry = tk.Entry(self.popup)
        self.max_entry.insert(0, str(self.max_value))
        self.max_entry.pack(fill="x", padx=10)

        # Step value input
        tk.Label(self.popup, text="Increment Step:").pack(anchor="w", padx=10)
        #self.step_entry = tk.Entry(self.popup)
        #self.step_entry = tk.Entry(self.popup, validate="key", validatecommand=vcmd)
        self.step_entry = tk.Entry(self.popup, validate="key")
        self.step_entry.insert(0, str(self.step))
        self.step_entry.pack(fill="x", padx=10)

        # Update button
        update_button = tk.Button(self.popup, text="Update", command=self.update_parameter_settings)
        update_button.pack(pady=10)
        
    def validate_integer(self, value_if_allowed):
        """Validation callback to check if input is an integer."""
        if value_if_allowed == "":  # Allow deletion of all text
            return True
        try:
            int(value_if_allowed)  # Try converting to integer
            return True
        except ValueError:
            return False
            
    def update_parameter_settings(self):
        # Update the parameter settings and close the popup window.
        self.min_value = float(self.min_entry.get())
        self.max_value = float(self.max_entry.get())
        self.step = float(self.step_entry.get())
        
        self.scale_set_values()
        
        # Apply changes to slider and labels
        #self.slider.config(from_=self.min_value, to=self.max_value)
        self.slider.config(from_=self.scaled_min_value, to=self.scaled_max_value)
        self.min_label.config(text=str(self.min_value))
        self.max_label.config(text=str(self.max_value))
        
        self.decrease_button.config(text=f"-{self.step}")
        self.increase_button.config(text=f"+{self.step}")
        
        # Optionally update shared_item if it needs these values
        self.shared_item.set_param(self.param, self.slider.get())
        
        # Close the popup
        self.popup.destroy()
    
class AreaSelectionModal(tk.Toplevel):
    def __init__(self, parent, pygame_instance, items, num_areas=4):
        super().__init__(parent)
        self.pygame_instance = pygame_instance
        self.title("Select Area for Curve")
        
        MaxNumAreas = 4
        
        # Number of areas (columns)
        self.num_areas = min(max(num_areas, 1), MaxNumAreas + 1)  # Ensure num_areas is between 1 and 4

        # Variable to hold user selections, initialized as a list of None
        self.selections = [tk.IntVar(value=(2 if i == 0 else 1)) for i in range(len(items))]
        
        # Frame for the grid
        grid_frame = tk.Frame(self)
        grid_frame.pack(padx=10, pady=10)
        
        # Set up headers
        tk.Label(grid_frame, text="").grid(row=0, column=0, padx=5, pady=5)  # Empty top-left cell
        Ncols = max(self.num_areas + 1, len(items)+1)+2
        #Adjust Ncols to maximal number of areas allowed
        Ncols = min(Ncols, MaxNumAreas + 2)

        for col in range(0, Ncols):
            if   col == 0:
                for row, item in enumerate(items, start=1):
                    tk.Label(grid_frame, text=item).grid(row=row, column=col, padx=5, pady=5)
            elif col == 1:
                tk.Label(grid_frame, text=f"Nix").grid(row=0, column=col, padx=5, pady=5)
            elif col <=  self.num_areas + 1:
                tk.Label(grid_frame, text=f"Area {col-1}").grid(row=0, column=col, padx=5, pady=5)
            else:
                tk.Label(grid_frame, text=f"Add {col-1}").grid(row=0, column=col, padx=5, pady=5)

        for row, item in enumerate(items, start=1):
            for col in range(1, Ncols):
                tk.Radiobutton(
                    grid_frame, 
                    variable=self.selections[row - 1], 
                    value=col
                ).grid(row=row, column=col, padx=5, pady=5)
                    
        # Frame to hold the buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        # "Select" button
        self.proceed_button = tk.Button(button_frame, text="Proceed...", command=self.select_areas)
        self.proceed_button.pack(side=tk.RIGHT, padx=5)
        
    def select_areas(self):
        # Collect and print the selections as pairs of (item_index, selected_area_index)
        #self.result = [(idx, var.get()) for idx, var in enumerate(self.selections)]
        self.result = {}
        for item_idx, var in enumerate(self.selections):
            area_id = var.get() - 1
            if area_id > 0:
                self.result[item_idx] = area_id
        self.destroy()  # Close the modal

class TkinterWindow(tk.Tk):
    def __init__(self, pygame_instance, cWinW = 600, cWinH = 400, dWin = 1000):
        super().__init__()  
        self.db_path = 'curves.db'
        
        self.DisplayWindow = dWin
        self.DisplayWindow = dWin
        self.pygame_instance = pygame_instance  
        
        # Set up the Tkinter window
        self.geometry(f"{cWinW}x{cWinH}")
        self.title("Tkinter Control Panel")
        
        # Create a Listbox for curves
        self.curve_listbox = tk.Listbox(self, selectmode=tk.SINGLE)
        self.curve_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Add a scrollbar to the Listbox
        scrollbar = tk.Scrollbar(self.curve_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.curve_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.curve_listbox.yview)
        
        # Bind selection event for Listbox
        self.curve_listbox.bind("<Double-Button-1>", self.on_curve_listbox_double_click)

        # Populate the Listbox with data from SQLite
        self.populate_listbox()
       
        self.curve_instances = {}
 
        # curveID as key:
        self.curve_sets   = {}  # collects which set of given Curve is on which plot area
        self.shown_sets   = {}  # attribute if the Area assignment for given Curve, Set and Ares is shown shown_sets[curve_id][set] = [AreaID1, AreaID1...]
        
        self.curve_frames = {}  # which TK frame has given Curve
        self.areas_frames = {}  # TK frame for given Curve on which assignment to Areas are shown
        self.param_frames = {}  # collection of frames for all parameters for given Curve
        
        self.line_properties = {} 
        
        # Handle the closing of the Tkinter window
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def populate_listbox(self):
        """Retrieve data from SQLite and populate the Listbox."""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM curves")
        rows = cursor.fetchall()

        self.curve_map = {}  # Map to store curve ID by listbox index
        for index, row in enumerate(rows):
            curve_id, curve_name = row
            self.curve_map[index] = curve_id
            self.curve_listbox.insert(tk.END, curve_name)

        connection.close()
        
    def on_curve_listbox_double_click(self, event):
        def adding_curve_wraper():
          if setID == 0 and parametric == 2:
            actDiagram = dg_types[4] #!!! Perhaps not optimal :-)
          else:
            actDiagram = dg_types[setID]
              
          self.add_curve_to_area(areaID, curveInstance, [actDiagram])  
          curveInstance.area[actDiagram] = areaID
          self.curve_sets[curve_id][actDiagram].append(AreaPtr(areaID))
        
        # Get selected curve index and ID
        selected_index = self.curve_listbox.curselection()
        if not selected_index:
            return  # No selection

        curve_id = self.curve_map[selected_index[0]]

        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()

        curveSQL = f"SELECT ID, name, className, color, thickness, parametric, formula, radians, also3d FROM curves WHERE ID={curve_id};"
        curves = cursor.execute(curveSQL).fetchall()
        curve_record = curves[0]
        curve_id     = curve_record[0]
        curve_name   = curve_record[1]
        class_name   = curve_record[2]
        curve_color  = curve_record[3]
        curve_thickness =curve_record[4]
        parametric   = int(curve_record[5])
        formula_png  = curve_record[6]
        t_in_radians = curve_record[7]
        is_3d        = curve_record[8]
        
        if formula_png: formula = Image.open(io.BytesIO(formula_png))
        else:           formula = ""
            
        if hasattr(funs, class_name):
            paramSQL = f"SELECT param, type, magnitude, valMin, valMax, val0, incr, Npoints FROM params WHERE curve_id={curve_id};"
            params = cursor.execute(paramSQL).fetchall()
            gotParams = {}
            tMin  =  0.0
            tMax  = 10.0
            tIncr =  1.0
            tPts  = 10 
            for paramSet in params:
                print("Param Set:")
                print(paramSet)
                paramName = paramSet[0]
                paramType = paramSet[1]
                magnitude = float(paramSet[2])
                if paramName == 't' and t_in_radians: magnitude *= 3.14159265358979323846
                    
                if paramType == 1:
                  defMin = 0.0
                else:
                  defMin = -magnitude
                defMax = magnitude
                
                actMin = defMin*paramSet[3]
                actMax = defMax*paramSet[4]
                actVal = paramSet[5]
                
                incr   = paramSet[6]
                nPts   = paramSet[7]

                gotParams[paramName] = [defMin, defMax, actMin, actMax, actVal, incr, nPts]
                
            print("Got Parameters")
            print(tMin, tMax, tIncr, tPts)
            print(parametric, formula)
            print(gotParams)
            print('='*33)
            if curve_id in self.curve_instances:
                new_curve = False
                curveInstance = self.curve_instances[curve_id]
            else:
                new_curve = True
                curveClass = getattr(funs, class_name)  # Get the class by name
                #curveInstance = curveClass(color=curve_record[2], thickness=curve_record[3], x0=0.0, y0=0.0, tmin=tMin, tmax=tMax, tincr=tIncr, Npoints = tPts, is_parametric=parametric, formula=formula, inpParams=gotParams)
                #curveInstance = curveClass(color=curve_color, thickness=curve_thickness, x0=0.0, y0=0.0, is_parametric=parametric, formula=formula, inpParams=gotParams)
                curveInstance = curveClass(name=curve_name, color=curve_color, thickness=curve_thickness, is_parametric=parametric, formula=formula, inpParams=gotParams)
                self.curve_instances[curve_id] = curveInstance
                self.curve_sets[curve_id] = {}
                self.shown_sets[curve_id] = {}
                for set in curveInstance.sets:
                  self.curve_sets[curve_id][set] = []
                  self.shown_sets[curve_id][set] = []
                
            #!!!!!! parametric determines the type of curve:
            # 0 - just simple y = f(x) dependency
            # 1 - two variables both dependent thorugh parameter t, i.e. y=f(x), x=f(t), y=f(t)
            # 2 = three variables: y=f(x), x=f(t), y=f(t) requering all four grapsh
            
            subtraction = 0
            Nareas = len(self.pygame_instance.Areas)            
            if Nareas == 1 and len(self.pygame_instance.Areas[1].curves) == 0 and parametric == 0:
              self.add_curve_to_area(1, curveInstance, 'xy')
              curveInstance.area['xy'] = 1
              self.curve_sets[curve_id]['xy'].append(AreaPtr(1))
            else:
              #area_modal = AreaSelectionModal(self, self.pygame_instance)
              area_modal = AreaSelectionModal(self, self.pygame_instance, gr_types[parametric], Nareas)
              self.wait_window(area_modal)
              if area_modal:
                  print(area_modal.result)
                  areaToSet = {arID:[] for arID in range(1,5)}
                  for setID, areaID in area_modal.result.items():
                    areaToSet[areaID].append(setID)
                
                  if Nareas == 1 and len(self.pygame_instance.Areas[1].curves) == 0: Nareas = 0
                  additions = []
                  for areaID in areaToSet:
                    if areaID > Nareas: 
                      if len(areaToSet[areaID]) > 0:
                        additions.append(areaToSet[areaID])
                        
                  Nadditions = len(additions) 
                  if Nadditions > 0:
                      print("Will be added", Nareas, Nadditions)
                      stored_curves_dict = {areaID: area.curves for areaID, area in self.pygame_instance.Areas.items()}
                      stored_diags_dict  = {areaID: area.diags  for areaID, area in self.pygame_instance.Areas.items()}
                      stored_diags_dict = {areaID: {curve: area.diags[curve] for curve in area.curves} for areaID, area in self.pygame_instance.Areas.items()}
                      self.pygame_instance.arrange_areas(Nareas + Nadditions)
                      #for area_id, curves in stored_curves_dict.items():
                      #    self.add_curve_to_area(area_id, curves, stored_diags_dict[area_id])
                          
                      # Restore data to areas
                      for area_id, curves in stored_curves_dict.items():
                          for curve in curves:
                              self.add_curve_to_area(area_id, curve, stored_diags_dict[area_id][curve])

                  for areaID in range(1,Nareas + 1):  
                    for setID in areaToSet[areaID]:
                      adding_curve_wraper()
                      
                  areaID = Nareas + 1
                  for adding in additions:
                    for setID in adding:
                      adding_curve_wraper()
                    areaID += 1
              else:
                print("Modal closed with 'x'")
            if new_curve:
                self.add_controls()  # Refresh control panels to reflect changes
            self.update_controls()
        else:
            print(f"Class {class_name} not found in module 'funs'.")
        connection.close()
       
    def add_curve_to_area(self, area_index, adding_curve_curves, set_sets):
        if type(adding_curve_curves) == list:
            self.pygame_instance.Areas[area_index].curves.extend(adding_curve_curves)
            for curve in adding_curve_curves:
                if curve not in self.pygame_instance.Areas[area_index].diags:
                    self.pygame_instance.Areas[area_index].diags[curve] = []
            if set_sets not in self.pygame_instance.Areas[area_index].diags[adding_curve_curves]:
                self.pygame_instance.Areas[area_index].diags[adding_curve_curves].extend(set_sets)
        else:
            if adding_curve_curves not in self.pygame_instance.Areas[area_index].curves:
                self.pygame_instance.Areas[area_index].curves.append(adding_curve_curves)
            if adding_curve_curves not in self.pygame_instance.Areas[area_index].diags:
                self.pygame_instance.Areas[area_index].diags[adding_curve_curves] = []
                
            if type(set_sets) == list:
                for set in set_sets:
                    if set not in self.pygame_instance.Areas[area_index].diags[adding_curve_curves]:
                        self.pygame_instance.Areas[area_index].diags[adding_curve_curves].append(set)
            else:
                if set_sets not in self.pygame_instance.Areas[area_index].diags[adding_curve_curves]:
                    self.pygame_instance.Areas[area_index].diags[adding_curve_curves].append(set_sets)
        self.pygame_instance.Areas[area_index].set_scale()
    
    def add_controls(self):
        for curve_id, curve in self.curve_instances.items():
          if curve_id not in self.curve_frames:
            # Create a frame for this curve's controls
            curve_frame = tk.Frame(self, bd=2, relief=tk.GROOVE, padx=5, pady=5)
            curve_frame.pack(fill=tk.X, pady=2, padx=2)
            self.curve_frames[curve_id] = curve_frame
            self.areas_frames[curve_id] = []
            self.param_frames[curve_id] = []

            #****************************************************************************************************
            #  UPPER ROW-FRAME FOR THE CURVE
            # Frame for the top row (curve name, formula image, HTML link)
            top_row_frame = tk.Frame(curve_frame)
            top_row_frame.pack(side=tk.TOP, fill=tk.X)

            # Curve name label
            curve_label = tk.Label(top_row_frame, text=f"{curve.name}", font=("Arial", 10, "bold"))
            curve_label.pack(side=tk.LEFT, anchor=tk.W, padx=5)

            if curve.formula:
                # Formula image label (resized using Resize_formula_image)
                #formula_image_tk = Resize_formula_image(curve.formula)
                formula_image_tk = ImageTk.PhotoImage(curve.formula)
                formula_image_label = tk.Label(top_row_frame, image=formula_image_tk)
                formula_image_label.image = formula_image_tk
                formula_image_label.pack(side=tk.LEFT, padx=5)

            # Placeholder for HTML link label
            html_link_label = tk.Label(top_row_frame, text="View Formula", fg="blue", cursor="hand2")
            html_link_label.pack(side=tk.LEFT, padx=5)
            html_link_label.bind("<Button-1>", lambda e: open_html_link(curve.html_link))

            # Delete button
            #delete_button = tk.Button(top_row_frame, text='Delete', command=lambda cf=curve_frame, cv=curve: self.delete_curve_frame(cf, cv)) 
            delete_button = tk.Button(top_row_frame, text='Delete', command=lambda cf=curve_frame, cv=curve, ci=curve_id: self.delete_curve_frame(cf, cv, ci))
            delete_button.pack(side=tk.LEFT, padx=5)

            #****************************************************************************************************
            #  BOTTOM ROW-FRAME FOR THE CURVE
            # Frame for the bottom row (line style, setup button, delete button, and slider)
            bottom_row_frame = tk.Frame(curve_frame)
            bottom_row_frame.pack(side=tk.TOP, fill=tk.X)
            self.areas_frames[curve_id] = bottom_row_frame
            
            #zoom_button = tk.Button(bottom_row_frame, text='Zoom', command=lambda af=area_id: self.zoom_in_area(af)) 
            #zoom_button.pack(side=tk.LEFT, padx=5)
            
            #****************************************************************************************************
            #  FRAME FOR ALL CONTROLS FOR THE CURVE
            params_frame = tk.Frame(curve_frame)
            params_frame.pack(side=tk.TOP, fill=tk.X)
            
            #ancor_frame = curve_frame
            ancor_frame = params_frame
            print("PARAMS FOR CURVE ", curve)
            print(curve.params)
            for param, setvals in curve.params.items():
                span = setvals[3] - setvals[2]
                scaleFactor = self.DisplayWindow/span
                print("Scale Factor ", scaleFactor)
                if param == 't':
                    if curve.is_parametric > 0:
                        #param_frame = ControlPanel(ancor_frame, curve, "curve", param, curve.tmin, curve.tmax, curve.tmax, curve.tincr, scaleFactor, True , 't', curve.tincr)
                        param_frame = ControlPanel(ancor_frame, curve, "curve", param, curve.tmin, 2*curve.tmax, curve.tmax, curve.tincr, scaleFactor, True , 't', curve.tincr)
                        self.param_frames[curve_id].append(param_frame.control_frame)
                    '''    
                    if curve.is_parametric != 0:
                        if curve.is_parametric == 1:
                            param_frame = ControlPanel(ancor_frame, curve, "curve", param, curve.tmin, curve.tmax, 0.0, curve.tincr, scaleFactor, True , 't', curve.tincr)
                        else:
                            param_frame = ControlPanel(ancor_frame, curve, "curve", param, curve.tmin, curve.tmax, 0.0, curve.tincr, scaleFactor, False, 't', curve.tincr)
                        #self.curve_frames[area_id][-1][1].append(param_frame.control_frame)
                        self.param_frames[curve_id].append(param_frame.control_frame
                    '''
                else:
                    param_frame = ControlPanel(curve_frame, curve, "curve", param, setvals[2], setvals[3], setvals[4], setvals[5], scaleFactor)
                    #self.curve_frames[area_id][-1][1].append(param_frame.control_frame)
                    self.param_frames[curve_id].append(param_frame.control_frame)
                
    def update_controls(self):
        def clear_frame(frame):
            for widget in frame.winfo_children():
                widget.destroy()

        def get_color_for_area(areaID):
            if areaID in area_colors:
                R, G, B = area_colors[areaID][0], area_colors[areaID][1], area_colors[areaID][2]
                return f"#{R:02x}{G:02x}{B:02x}"  # Format as a hex color code
            else:
                return "lightblue"

        def function_control(above_frame, line_color = "black", line_thickness = 1):
            f1_frame = tk.Frame(above_frame)    
            f1_frame.pack(side=tk.LEFT, padx=5) #, fill=tk.X)
                
            # Line style canvas
            color_line = tk.Canvas(f1_frame, width=20, height=10)
            line_id = color_line.create_line(0, 5, 20, 5, fill=line_color, width=line_thickness) 
            color_line.pack(side=tk.LEFT, padx=(2, 2))

            self.line_properties[line_id] = {
                "canvas": color_line,
                "color": line_color,
                "thickness": line_thickness
            }

            change_button = tk.Button(f1_frame, text="...", command=lambda c=curve, lid=line_id: self.open_curve_settings(c, lid))
            change_button.pack(side=tk.LEFT)  

            return f1_frame
            
        for curve_id, curve_frame in self.areas_frames.items():
            clear_frame(curve_frame)  # Clear all widgets in the frame for the curve_id    
            
        for curve_id, curve in self.curve_instances.items():
          if len(self.curve_sets[curve_id].items()) > 0:
            funControl = function_control(self.areas_frames[curve_id], curve.color, curve.thickness)
            for cSet, aPtrs in self.curve_sets[curve_id].items():
              if len(aPtrs) > 0:
                f1_label = tk.Label(funControl, text= fn_label[cSet], font=("Times New Roman", 10, "italic bold"))
                f1_label.pack(side=tk.LEFT, anchor=tk.W, padx=1)          
                for aPtr in aPtrs:
                  if aPtr.aid not in self.shown_sets[curve_id][cSet]:
                    new_bg_color = get_color_for_area(aPtr.aid)
                    button = tk.Button(funControl, text="  ", bg=new_bg_color, fg="blue", command=lambda areaID=aPtr.aid: self.zoom_in_area(areaID))
                    button.pack(side=tk.LEFT, padx=2, pady=2)  # Add padding for spacing
            
    def zoom_in_area(self, areaID):
        if areaID in self.pygame_instance.Areas: 
            self.pygame_instance.Areas[areaID].set_scale()
                
    def delete_curve_frame(self, curve_frame, toDel_curve, curveID):
        for area_id, area in self.pygame_instance.Areas.items():
            if toDel_curve in area.curves:
                if toDel_curve in area.diags:
                    del area.diags[toDel_curve]
                area.curves.remove(toDel_curve)  # Remove the curve from the area

        # Remove curve references from associated dictionaries/lists
        if curveID in self.curve_frames:
            del self.curve_frames[curveID]
        if curveID in self.areas_frames:
            del self.areas_frames[curveID]
        if curveID in self.param_frames:
            del self.param_frames[curveID]
        if curveID in self.curve_instances:
            del self.curve_instances[curveID]

        curve_frame.destroy()
        '''
        # Ensure an affected area is found
        if affected_area_id is not None:
            # Find and destroy the curve frame and its parameter frames in Tkinter
            curve_list = self.curve_frames.get(affected_area_id, [])
            for i, (stored_curve_frame, param_frames) in enumerate(curve_list):
                if stored_curve_frame == curve_frame:
                    # Destroy each parameter frame associated with this curve frame
                    for param_frame in param_frames:
                        param_frame.destroy()

                    # Destroy the curve frame itself
                    stored_curve_frame.destroy()

                    # Remove this curve frame entry from the list in curve_frames
                    del curve_list[i]
                    break
            if not curve_list:
                pass
        '''
        
        print(f"Deleted curve: {toDel_curve.name}")
        for sArea in self.pygame_instance.Areas.values():
            sArea.set_scale()

    #def open_curve_settings(self, curve):
    def open_curve_settings(self, curve, line_id):
        line_data = self.line_properties[line_id]
        current_canvas = line_data["canvas"]
        current_color = line_data["color"]
        current_thickness = line_data["thickness"]
        
       # Open a modal dialog to change color
        color = colorchooser.askcolor(initialcolor=current_color)[1]
        if color:  # If a color was chosen
            self.line_properties[line_id]["color"] = color  # Update the color
            curve.color = color  # Update the curve's color

        # Get the thickness from the user
        thickness = simpledialog.askinteger("Thickness", "Enter thickness:", initialvalue=current_thickness, minvalue=1)
        if thickness:  # If a thickness was entered
            self.line_properties[line_id]["thickness"] = thickness  # Update the thickness
            curve.thickness = thickness 

        current_canvas.itemconfig(line_id,
                                  fill=self.line_properties[line_id]["color"],
                                  width=self.line_properties[line_id]["thickness"])

        
        # Optionally, refresh the display (update the line) after changing settings
        self.add_controls()  # Refresh control panels to reflect changes
        self.update_controls()
        
    def on_closing(self):
        print("Tkinter window closing...")
        self.pygame_instance.running = False
        self.quit()  # Properly stop the Tkinter main loop
