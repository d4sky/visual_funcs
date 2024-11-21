import numpy as np
import math

from scipy.integrate import solve_ivp

# Base Curve class (shared by all curve types)
class Curve:
    def __init__(self, name = "Curve", color="black", thickness = 1, xyz0=[], is_parametric=0, formula=None, inpParams={}):
        self.name      = name
        self.color     = color
        self.thickness = thickness
        
        self.is_parametric = is_parametric
        
        self.sets = []
        if   is_parametric == 0:
            self.sets = ['xy']
        elif is_parametric == 1:
            self.sets = ['xy', 'tx', 'ty']
        elif is_parametric == 2:
            self.sets['xyz', 'tx', 'ty', 'tz'] 
            
        self.xyz0 = xyz0
        
        self.formula = formula
        self.Neqs    = 2
        
        self.tmin    =  0.0
        self.tmax    = 10.0
        self.t0      =  0.0
        self.tincr   =  1.0
        self.Npoints = 2
        self.t_lst   = [self.t0]

        self.area    = {}
        
        self.params = {}
        for param, inpParamSet in inpParams.items():
            if param == 't':
                #[defMin, defMax, actMin, actMax, actVal, incr, nPts]
                print(inpParamSet)
                self.tmin    = inpParamSet[2] #tmin
                self.tmax    = inpParamSet[3] #tmax
                self.t0      = inpParamSet[4] #tmax
                self.tincr   = inpParamSet[5] #tincr
                self.Npoints = inpParamSet[6] #Npoints
                self.params[param] = inpParamSet
                self.t_lst   = [self.t0]
            else:
                self.params[param] = inpParamSet
                
        self.t_vec = np.array(self.t_lst)  
        self.param_map = {}
        
        self.erase()
    
    def set_param(self, param, val):
        if param in self.param_map:
            setattr(self, self.param_map[param], val)  # Set the attribute using the mapping
            if param != 't':
              self.t_vec = np.array([])  
        else:
            raise ValueError(f"Unknown parameter name: {param}")
            
    def set_params(self):
      for param in self.param_map:
        if self.params[param] != 't':  
          self.set_param(param, float(self.params[param][4]))

    def erase(self):
        self.xyz = np.zeros((self.Npoints, self.Neqs))
        self.current_index = 0
    
    def init(self):
        self.erase()
        self.t_vec = np.linspace(self.tmin, self.tmax, self.Npoints, endpoint=True)  
        self.current_index = len(self.t_vec) - 1
    
    #@run_get_min_max_after
    def calculate(self, *args, **kwargs):
        pass
        
class Line(Curve):
    def __init__(self, x1=0.0, y1=0.0, x2=0.0, y2=0.0, **kwargs):
        super().__init__(**kwargs)
        self.xyz[0] = [x1, y1]
        self.xyz[1] = [x2, y2]
        self.current_index = 1
        self.calculate()

    def calculate(self,  *args, **kwargs):
        pass

class Line3d(Curve):
    def __init__(self, x1=0.0, y1=0.0, z1=0.0, x2=0.0, y2=0.0, z2=0.0, color='black'):
        super().__init__(color=color)
        self.x_vec = np.array([x1, x2])  
        self.y_vec = np.array([y1, y2])  
        self.z_vec = np.array([z1, z2])  
        self.calculate()

    def calculate(self,  *args, **kwargs):
        pass
        
class Ellipse(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Ellipse"
        self.param_map = {
            't': 't',
            'a': 'a',
            'b': 'b'
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.a * np.cos(self.t_vec)
        self.xyz[:,1] = self.b * np.sin(self.t_vec)
        
class Linear(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Linear"
        self.param_map = {
            't': 't',
            'y0': 'y0',
            'k': 'k',
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.y0 + self.k * (self.t_vec)

class Parabola(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Parabola"
        self.param_map = {
            't': 't',
            'y0': 'y0',
            'a': 'a',
            'x0': 'x0',
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.y0 + self.a * (self.t_vec - self.x0)**2

class Sinus(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Sine"
        self.param_map = {
            't': 't',
            'A': 'A',
            'ω': 'omega',
            'α': 'alpha',
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.A * np.sin(self.omega*self.t_vec + self.alpha)

class Exponential(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Exponential"
        self.param_map = {
            't': 't',
            'A': 'A', 
            'k': 'k',
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.A * np.exp(self.k*self.t_vec)

class Gaussian(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "Gaussian"
        self.param_map = {
            't': 't',
            'σ': 'sigma',
            'µ': 'x0',
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = np.exp((-(self.t_vec - self.x0)**2)/(2*self.sigma*self.sigma))/(self.sigma*np.sqrt(2.0*np.pi))

class RoseSin(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.param_map = {
            't': 't',
            'A': 'A',
            'n': 'n',
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.init()
        t_fi = self.t_vec
        t_r  = self.A*np.sin(self.n*t_fi)
        self.xyz[:,0] = t_r*np.cos(t_fi)
        self.xyz[:,1] = t_r*np.sin(t_fi)

class Oscillator(Curve):
    def __init__(self, is_parametric=1, **kwargs):
        super().__init__(is_parametric=is_parametric, **kwargs)
        self.name = "Oscillator"
        self.param_map = {
            't': 't',
            'k' : 'k', 
            'x0': 'x0',
            'y0': 'y0'
        }
        self.set_params()
        self.calculate()
   
    def calculate(self, tIncrement = 0.0):
        def odesystem(t, z):
            x, y = z
            dxdt = y
            dydt = -self.k * self.k * x
            return [dxdt, dydt]
        
        if tIncrement:
          if  len(self.t_vec) == 0:
            self.init()
            self.xyz[0] = [self.x0, self.y0]
            self.current_index = 0
          else:
            if self.current_index+1 >= len(self.t_vec):
                self.t_vec = np.concatenate((self.t_vec, np.zeros(self.Npoints)))
                self.xyz   = np.vstack((self.xyz, np.zeros((self.Npoints, self.Neqs))))
 
          current_i = self.current_index
          new_t = self.t_vec[current_i] + tIncrement
          t_span = (self.t_vec[current_i], new_t)
          
          solution = solve_ivp(
            odesystem,
            t_span,
            [self.xyz[current_i,0], self.xyz[current_i,1]],  
            t_eval=[new_t]  
          )
          
          # Update all variables
          next_i = current_i + 1
          self.t_vec[next_i] = new_t
          self.xyz[next_i,0] = solution.y[0]
          self.xyz[next_i,1] = solution.y[1]
          self.current_index = next_i
          
        else:
          self.init()
          t_span = (self.t_vec[0], self.t_vec[-1])
          solution = solve_ivp(
            odesystem,
            t_span,
            [self.x0, self.y0],  # Initial values for x and y
            t_eval=self.t_vec  # Evaluate at 100 points within t_span
          )

          self.xyz[:,0] = solution.y[0]
          self.xyz[:,1] = solution.y[1]

class Newton2D(Curve):
    def __init__(self, is_parametric=1, **kwargs):
        super().__init__(is_parametric=is_parametric, **kwargs)
        self.name = "Newton Equation of Motion in 2D"
        self.param_map = {
            't': 't',
            'm1': 'm1', 
            'm2': 'm2', 
            'x0': 'x0',
            'vx0': 'vx0',
            'y0': 'y0',
            'vy0': 'vy0'
        }
        self.set_params()
        self.calculate()
   
    def calculate(self, tIncrement = 0.0):
        def inter_init():
            self.t = self.t0
            self.x = self.x0
            self.y = self.y0
            self.vx = self.vx0
            self.vy = self.vy0
            
            self.t_vec  = np.array([])
            self.x_vec  = np.array([])
            self.y_vec  = np.array([])
            self.vx_vec = np.array([])
            self.vy_vec = np.array([])
            
        def inter_append():
            '''
            self.t_vec  = np.append(self.t_vec, self.t)
            self.x_vec  = np.append(self.x_vec, self.x)
            self.y_vec  = np.append(self.y_vec, self.y)
            self.vx_vec = np.append(self.vx_vec, self.vx)
            self.vy_vec = np.append(self.vy_vec, self.vy)
            '''
            
            new_entry = (self.t, self.x, self.vx, self.y, self.vy)
            self.t_vec  = np.append(self.t_vec, new_entry[0])
            self.x_vec  = np.append(self.x_vec, new_entry[1])
            self.y_vec  = np.append(self.y_vec, new_entry[3])
            self.vx_vec = np.append(self.vx_vec, new_entry[2])
            self.vy_vec = np.append(self.vy_vec, new_entry[4])
            
        def inter_last():
            self.t  = self.t_vec[-1]
            self.x  = self.x_vec[-1]
            self.y  = self.y_vec[-1]
            self.vx = self.vx_vec[-1]
            self.vy = self.vy_vec[-1]
            
        def odesystem(t, z):
            x, y, vx, vy = z
            r = np.sqrt(x*x + y*y)
            #Fg = 5.76659520*(self.m1 + self.m2)/(r**3)
            #Fg = 1.334*(self.m1 + self.m2)/(r**3)
            #Fg = 6.67e-5*(self.m1 + self.m2)/(r**3)
            Fg = 6.67*7.465*10*(self.m1 + self.m2)/(r**3)
            print(Fg)

            dxdt  = vx
            dydt  = vy
            dvxdt = -Fg*x
            dvydt = -Fg*y
            return [dxdt, dydt, dvxdt, dvydt]
        
        if tIncrement:
          if  len(self.t_vec) == 0:
            inter_init()
            inter_append()

          new_t = self.t + tIncrement
          t_span = (self.t, new_t)
          
          solution = solve_ivp(
            odesystem,
            t_span,
            [self.x, self.y, self.vx, self.vy],  # Initial values for x and y
            t_eval=[new_t]  # Only evaluate at the end of this increment
          )
          
          # Update all variables
          print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
          print(solution.y)
          print('*'*111)
          self.t = new_t
          self.x, self.y, self.vx, self.vy = solution.y[:, -1]
          inter_append()
          
        else:
          self.erase()
          inter_init()
          print("HERE WE GO" + '*'*44)
          t_span = (self.t, self.tmax)
          print(t_span)
          self.t_vec = np.linspace(t_span[0], t_span[1], num=self.Npoints)
          print('-'*55)
          print(self.t_vec)
          print('-'*55)
          solution = solve_ivp(
            odesystem,
            t_span,
            [self.x, self.y, self.vx, self.vy],  # Initial values for x and y
            t_eval=self.t_vec  # Evaluate at 100 points within t_span
          )
          print(solution)
          self.x_vec  = solution.y[0]
          self.y_vec  = solution.y[2]
          self.vx_vec = solution.y[1]
          self.vy_vec = solution.y[3]
          
          inter_last()
          
class LotkaVolterra(Curve):
    def __init__(self, is_parametric=1, **kwargs):
        super().__init__(is_parametric=is_parametric, **kwargs)
        self.name = "Lotka–Volterra equations"
        self.param_map = {
            't': 't',
            'α' : 'α', 
            'β' : 'β', 
            'γ' : 'γ', 
            'δ' : 'δ', 
            'x0': 'x0',
            'y0': 'y0'
        }
        self.set_params()
        self.calculate()
        
    def calculate(self, tIncrement = 0.0):
        def odesystem(t, z):
            x, y = z
            dxdt = y
            dxdt =  self.α * x - self.β * x * y
            dydt = -self.γ * y + self.δ * x * y
            return [dxdt, dydt]
        
        if tIncrement:
          if  len(self.t_vec) == 0:
            self.t = self.t0
            self.x = self.x0
            self.y = self.y0
            self.t_vec = np.array([self.t])
            self.x_vec = np.array([self.x])
            self.y_vec = np.array([self.y])
  
          new_t = self.t + tIncrement
          t_span = (self.t, new_t)

          solution = solve_ivp(
            odesystem,
            t_span,
            [self.x, self.y],  # Initial values for x and y
            t_eval=[new_t]  # Only evaluate at the end of this increment
          )
       
          
          # Update all variables
          self.t = new_t
          self.x, self.y = solution.y[:, -1]
          #print(self.t, self.x, self.y)
          #self.t_vec = np.array(self.t_lst)
          self.t_vec = np.append(self.t_vec, self.t)
          self.x_vec = np.append(self.x_vec, self.x)
          self.y_vec = np.append(self.y_vec, self.y)
          
        else:
          self.erase()
          self.t = self.t0
          self.x = self.x0
          self.y = self.y0
          
          t_span = (self.t, self.tmax)
          self.t_vec = np.linspace(t_span[0], t_span[1], num=self.Npoints)
          solution = solve_ivp(
            odesystem,
            t_span,
            [self.x, self.y],  # Initial values for x and y
            t_eval=self.t_vec  # Evaluate at 100 points within t_span
          )
          
          self.x_vec = solution.y[0]
          self.y_vec = solution.y[1]

# Hyperbola class derived from Curve
class Hyperbola(Curve):
    def __init__(self, a, ni, color="cyan"):
        super().__init__(color)
        self.a = a  # Hyperbola scaling parameter
        self.ni = ni  # Angle parameter
        self.calculate()

    def calculate(self):
        self.erase()
        """Generates points for the hyperbola."""
        i_vals = np.arange(-self.Npoints, self.Npoints)
        i_vals = i_vals[i_vals != 0]  # Exclude zero to avoid division by zero
        i_scaled = i_vals / 100

        # Generate x and y points for the hyperbola
        self.x_vec = self.a * np.cosh(i_scaled) * np.cos(self.ni)
        self.y_vec = self.a * np.sinh(i_scaled) * np.sin(self.ni)

# Ellipse class derived from Curve
class test3d(Curve):
    def __init__(self, color="green", thickness=1, x0=0.0, y0=0.0, is_parametric=0, formula=None, inpParams={}):
        super().__init__(color, thickness, x0, y0, is_parametric, formula, inpParams)
        self.name = "TESTING"
        self.param_map = {
            't': 't',
            'a': 'a',
            'b': 'b'
        }
        self.set_params()
        self.calculate()

    def calculate(self, *args, **kwargs):
        self.erase()
        """Generates points for the ellipse."""
        #angles = np.linspace(0, 2 * np.pi, self.Npoints, endpoint=True)  
        self.t_vec = np.linspace(self.tmin, self.tmax, self.Npoints, endpoint=True)  
        
        #self.x = self.x0 + self.a * np.cos(self.t)
        #self.y = self.y0 + self.b * np.sin(self.t)
        self.x_vec = self.r0[0] + self.a * np.cos(self.t_vec)
        self.y_vec = self.r0[1] + self.b * np.sin(self.t_vec)

# Abstract Bunch class (parent for bunches of curves)
class Bunch:
    def __init__(self, x0=0, y0=0):
        self.x0 = x0
        self.y0 = y0
        self.curves = []

    def erase(self):
        """Clears the list of curves."""
        self.curves = []

    def add_curve(self, curve):
        """Adds a single curve to the bunch."""
        self.curves.append(curve)

    #def calculate(self):
    def calculate(self, *args, **kwargs):
        """Abstract method to generate curves (implemented in derived classes)."""
        raise NotImplementedError

    def __add__(self, other):
        """Allows adding two Bunch objects to combine their curves."""
        if not isinstance(other, Bunch):
            raise TypeError("Only Bunch objects can be added together.")
        
        #combined_bunch = Bunch()  # Change to Bunch instead of MixedBunch
        combined_bunch = MixedBunch()  # Use MixedBunch to combine

        combined_bunch.curves = self.curves + other.curves  # Combine the curve lists
            
        return combined_bunch

class LineBunch(Bunch):
    def __init__(self, point_pairs):
        super().__init__()
        for pair in point_pairs:
            x1, y1 = pair[0]
            x2, y2 = pair[1]
            line = Line(x1, y1, x2, y2)
            self.add_curve(line)  
        self.calculate()
    
    def erase(self):
        pass
        
    def calculate(self, *args, **kwargs):
        pass
        #line = Line(self.xmin, self.xmax)
        #self.add_curve(line)    

class LineBunch3d(Bunch):
    def __init__(self, ampl = 1000):
        super().__init__()
        lineX = Line3d(-ampl, 0.0, 0.0, ampl, 0.0, 0.0, 'red')
        lineY = Line3d(0.0, -ampl, 0.0, 0.0, ampl, 0.0, 'green')
        lineZ = Line3d(0.0, 0.0, -ampl, 0.0, 0.0, ampl, 'blue')
        self.add_curve(lineX)  
        self.add_curve(lineY)  
        self.add_curve(lineZ)  
        self.calculate()
    
    def erase(self):
        pass
        
    def calculate(self, *args, **kwargs):
        pass
        #line = Line(self.xmin, self.xmax)
        #self.add_curve(line)    

# Bunch of ellipses
class EllipseBunch(Bunch):
    def __init__(self):
        super().__init__()
        self.calculate()

    def calculate(self, ae=80):
        self.erase()
        """Generates multiple ellipses and adds them to the bunch."""
        e = ae
        incr = 5.0
        for i in range(1, 10):
            a = 80 + i * incr
            b = math.sqrt(a * a - e * e)
            ellipse = Ellipse(a, b)
            self.add_curve(ellipse)

# Bunch of hyperbolas
class HyperbolaBunch(Bunch):
    def __init__(self):
        super().__init__()
        self.calculate()

    def calculate(self, ae=80):
        self.erase()
        """Generates multiple hyperbolas and adds them to the bunch."""
        e = ae
        incr = math.pi / 10
        for i in range(1, 10):
            ani = i * incr
            hyperbola = Hyperbola(e, ani)
            self.add_curve(hyperbola)

# MixedBunch: Combines both Ellipses and Hyperbolas
class MixedBunch(Bunch):
    def __init__(self):
        super().__init__()

    def calculate(self, ae=80):
        """Generates both ellipses and hyperbolas in a mixed bunch."""
        for curve in self.curves:
            curve.clear_points()  # Clear existing points for each curve
            curve.calculate()     # Recalculate each curve based on its type