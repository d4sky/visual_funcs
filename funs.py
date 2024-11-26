import numpy as np
import math, re 

from scipy.integrate import solve_ivp, odeint, RK45

bColors = {}
bColors['xy']  = 'orange'
bColors['tx']  = 'red'
bColors['ty']  = 'green'
bColors['tz']  = 'blue'
bColors['xyz'] = 'indigo'

fn_label = {}
fn_label['xy'] = "y(x)"
fn_label['tx'] = "x(t)"
fn_label['ty'] = "y(t)"
fn_label['tz'] = "z(t)"
fn_label['xyz'] = "z(x,y)"

# Base Curve class (shared by all curve types)
class Curve:
    def __init__(self, name = "Curve", color="black", thickness = 1, xyz0=[], is_parametric=0, formula=None, inpParams={}, Neqs = 2, Ndims = 2):
        self.name      = name
        self.color     = color
        self.thickness = thickness
        
        self.is_parametric = is_parametric
        self.formula = formula

        self.tmin    =  0.0
        self.tmax    = 10.0
        self.t0      =  0.0
        self.tincr   =  1.0
        self.Npoints = 2
        self.t_lst   = [self.t0]
        self.t_vec = np.array(self.t_lst)  

        self.Neqs    = Neqs
        self.Ndims   = Ndims

        self.xyz0 = xyz0
        self.erase() 

        self.sets = []
        if   is_parametric == 0:
            self.sets = ['xy']
        elif is_parametric == 1:
            self.sets = ['xy', 'tx', 'ty']
        elif is_parametric == 2:
            self.sets['xyz', 'tx', 'ty', 'tz'] 

        self.props  = {}
        self.labels = {}
        
        self.area  = {}
        
        self.params    = {}
        for param, inpParamSet in inpParams.items():
            if param == 't':
                #print(inpParamSet)
                self.tmin    = inpParamSet[2] #tmin
                self.tmax    = inpParamSet[3] #tmax
                self.t0      = inpParamSet[4] #tmax
                self.tincr   = inpParamSet[5] #tincr
                self.Npoints = inpParamSet[6] #Npoints
                self.params[param] = inpParamSet
                self.t_lst   = [self.t0]
            else:
                self.params[param] = inpParamSet
                
        self.param_map = {}
    
    def set_param(self, param, val):
        if param in self.param_map:
            setattr(self, self.param_map[param], val)  # Set the attribute using the mapping
        else:
            raise ValueError(f"Unknown parameter name: {param}")
            
    def set_params(self):
      for param in self.param_map:
        self.set_param(param, float(self.params[param][4]))

    def erase(self):
        self.t_vec = np.zeros(self.Npoints)
        self.xyz = np.zeros((self.Npoints, self.Neqs))
        self.current_index = 0
    
    def init(self):
        self.erase()
        self.t_vec = np.linspace(self.tmin, self.tmax, self.Npoints, endpoint=True)  
        self.current_index = len(self.t_vec) - 1
    
    def after_init(self):
        self.props  = {set:(bColors[set], 2) for set in self.sets}
        self.labels = {set:fn_label[set] for set in self.sets}
        self.set_params()
        self.calculate()
    
    #@run_get_min_max_after
    def calculate(self, *args, **kwargs):
        pass

class ODECurve(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.y  = np.zeros((1, self.Neqs))
        self.y0 = np.zeros(self.Neqs)
        
    def odesystem(self, t, z):
        pass
            
    def get_y0_parameters(self):
        #pattern = re.compile(r"^y0_\d+$")  # Matches "y0_" followed by one or more digits
        #return {k: v for k, v in vars(self).items() if pattern.match(k)}
        pattern = re.compile(r"^y0_(\d+)$")  # Captures the digits after "y0_"
        return {int(pattern.match(k).group(1))-1: v for k, v in vars(self).items() if pattern.match(k)}
            
    def set_y0(self):        
        y0_parameters = self.get_y0_parameters()
        if set(list(range(self.Neqs))) != set(list(y0_parameters.keys())):
            print("!"*39)
            print("Initial parameters are not properly set")
        else:
            y0_values = [y0_parameters[ei] for ei in range(self.Neqs)]
            self.y0 = np.array(y0_values)
            
    def after_init(self):
        self.props = {set:(bColors[set], 2) for set in self.sets}
        self.labels = {set:fn_label[set] for set in self.sets}
        self.set_params()  
        self.set_y0()      
        self.calculate()   
            
    def calculate(self, tIncrement = 0.0):
        if tIncrement:
          if  len(self.t_vec) == 0:
            self.init()
            self.y  = np.zeros((self.Npoints, self.Neqs))
            self.set_y0()
            self.y[0]   = self.y0
            self.xyz[0] = self.y0
            
            self.current_index = 0
          else:
            if self.current_index+1 >= len(self.t_vec):
                self.t_vec = np.concatenate((self.t_vec, np.zeros(self.Npoints)))
                self.y     = np.vstack(( self.y , np.zeros((self.Npoints, self.Neqs))))
                self.xyz   = np.vstack((self.xyz, np.zeros((self.Npoints, self.Neqs))))
 
          current_i = self.current_index
          new_t = self.t_vec[current_i] + tIncrement
          t_span = (self.t_vec[current_i], new_t)
          
          solution = solve_ivp(
            self.odesystem,
            t_span,
            self.y[current_i],  
            t_eval=[new_t]  
          )
          
          # Update all variables
          next_i = current_i + 1
          self.t_vec[next_i] = new_t
          self.y[next_i] = solution.y[:, -1]  
          for ei in range(self.Ndims):
            self.xyz[next_i, ei] = solution.y[ei]
          self.current_index = next_i
          
        else:
          #meth = "RK45"
          meth = "RK23"
          #meth = "Radau"
          #meth = "BDF"
          #meth = "LSODA"
          #meth = "DOP853"
          self.init()
          self.set_y0()
          t_span = (self.t_vec[0], self.t_vec[-1])
          
          solution = solve_ivp(
            self.odesystem,
            t_span,
            self.y0,  
            method=meth,
            t_eval=self.t_vec  
          )
          self.y = solution.y.T
          for ei in range(self.Ndims):
            self.xyz[:,ei] = solution.y[ei]
            
class Line(Curve):
    def __init__(self, x1=0.0, y1=0.0, x2=0.0, y2=0.0, **kwargs):
        super().__init__(**kwargs)
        self.xyz[0] = [x1, y1]
        self.xyz[1] = [x2, y2]
        self.current_index = 1
        self.props['xy'] = 'black', 2
        
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
        self.param_map = {
            'a': 'a',
            'b': 'b'
        }
        self.after_init()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.a * np.cos(self.t_vec)
        self.xyz[:,1] = self.b * np.sin(self.t_vec)
        
class Linear(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.param_map = {
            't': 't',
            'y0': 'y0',
            'k': 'k',
        }
        self.after_init()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.y0 + self.k * (self.t_vec)

class Parabola(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.param_map = {
            't': 't',
            'y0': 'y0',
            'a': 'a',
            'x0': 'x0',
        }
        self.after_init()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.y0 + self.a * (self.t_vec - self.x0)**2

class Sinus(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.param_map = {
            'A': 'A',
            'ω': 'omega',
            'α': 'alpha',
        }
        self.after_init()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.A * np.sin(self.omega*self.t_vec + self.alpha)

class Exponential(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.param_map = {
            't': 't',
            'A': 'A', 
            'k': 'k',
        }
        self.after_init()

    def calculate(self, *args, **kwargs):
        self.init()
        self.xyz[:,0] = self.t_vec
        self.xyz[:,1] = self.A * np.exp(self.k*self.t_vec)

class Gaussian(Curve):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.param_map = {
            't': 't',
            'σ': 'sigma',
            'µ': 'x0',
        }
        self.after_init()

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
        self.after_init()

    def calculate(self, *args, **kwargs):
        self.init()
        t_fi = self.t_vec
        t_r  = self.A*np.sin(self.n*t_fi)
        self.xyz[:,0] = t_r*np.cos(t_fi)
        self.xyz[:,1] = t_r*np.sin(t_fi)

class Oscillator(ODECurve):
    def __init__(self, is_parametric=1, **kwargs):
        super().__init__(is_parametric=is_parametric, **kwargs)
        self.param_map = {
            't': 't',
            'k' : 'k', 
            'x0': 'y0_1',
            'y0': 'y0_2'
        }
        self.after_init()

    def odesystem(self, t, z):
        x, y = z
        dxdt = y
        dydt = -self.k * self.k * x
        return [dxdt, dydt]

class SIR(ODECurve):
    def __init__(self, is_parametric=1, Neqs=3, **kwargs):
        super().__init__(is_parametric=is_parametric,  Neqs=Neqs, Ndims=3, **kwargs)
        self.param_map = {
            't': 't',
            'β' : 'β', 
            'γ': 'γ',
            'S0': 'y0_1',
            'I0': 'y0_2',
            'R0': 'y0_3',
        }
        self.sets = ['tx', 'ty', 'tz']
        self.after_init()
        self.labels['tx'] = "S(t)"
        self.labels['ty'] = "I(t)"
        self.labels['tz'] = "R(t)"
        
    def odesystem(self, t, z):
        S, I, R = z
        dSdt = -self.β * I * S
        dIdt = self.β * I * S - self.γ * I
        dRdt = self.γ * I
        return [dSdt, dIdt, dRdt]
        
class LotkaVolterra(ODECurve):
    def __init__(self, is_parametric=1, **kwargs):
        super().__init__(is_parametric=is_parametric, **kwargs)
        self.param_map = {
            't': 't',
            'α' : 'α', 
            'β' : 'β', 
            'γ' : 'γ', 
            'δ' : 'δ', 
            'x0': 'y0_1',
            'y0': 'y0_2'
        }
        self.after_init()
        
    def odesystem(self, t, z):
        x, y = z
        dxdt = y
        dxdt =  self.α * x - self.β * x * y
        dydt = -self.γ * y + self.δ * x * y
        return [dxdt, dydt]
        
class LorenzSys(ODECurve):
    def __init__(self, is_parametric=1, Neqs=3, **kwargs):
        super().__init__(is_parametric=is_parametric, Neqs=Neqs, **kwargs)
        self.param_map = {
            't': 't',
            'σ': 'σ', 
            'ρ': 'ρ', 
            'β': 'β',
            'x0': 'y0_1',
            'y0': 'y0_2',
            'z0': 'y0_3',
        }
        self.after_init()
   
    def odesystem(self, t, inpY):
        x, y, z = inpY

        dxdt  = self.σ*(y-x)
        dydt  = x*(self.ρ-z) - y
        dzdt  = x*y - self.β*z
        return [dxdt, dydt, dzdt]
                  
class Newton2D(ODECurve):
    def __init__(self, is_parametric=1, Neqs=4, **kwargs):
        super().__init__(is_parametric=is_parametric, Neqs=Neqs, **kwargs)
        self.param_map = {
            't':   't',
            'm1':  'm1', 
            'm2':  'm2', 
            'x0':  'y0_1',
            'y0':  'y0_2',
            'vx0': 'y0_3',
            'vy0': 'y0_4'
        }
        self.after_init()
   
    def odesystem(self, t, z):
        x, y, vx, vy = z
        r = np.sqrt(x*x + y*y)
        #Fg = 5.76659520*(self.m1 + self.m2)/(r**3)
        #Fg = 1.334*(self.m1 + self.m2)/(r**3)
        #Fg = 6.67e-5*(self.m1 + self.m2)/(r**3)
        Fg = 6.67*7.465*10*(self.m1 + self.m2)/(r**3)

        dxdt  = vx
        dydt  = vy
        dvxdt = -Fg*x
        dvydt = -Fg*y
        return [dxdt, dydt, dvxdt, dvydt]
        
class Hyperbola(Curve):
    def __init__(self, a, ni, color="cyan"):
        super().__init__(color)
        self.a = a  # Hyperbola scaling parameter
        self.ni = ni  # Angle parameter
        self.calculate()

    def calculate(self):
        self.erase()
        i_vals = np.arange(-self.Npoints, self.Npoints)
        i_vals = i_vals[i_vals != 0]  # Exclude zero to avoid division by zero
        i_scaled = i_vals / 100

        # Generate x and y points for the hyperbola
        self.x_vec = self.a * np.cosh(i_scaled) * np.cos(self.ni)
        self.y_vec = self.a * np.sinh(i_scaled) * np.sin(self.ni)

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
        #angles = np.linspace(0, 2 * np.pi, self.Npoints, endpoint=True)  
        self.t_vec = np.linspace(self.tmin, self.tmax, self.Npoints, endpoint=True)  
        
        self.x_vec = self.r0[0] + self.a * np.cos(self.t_vec)
        self.y_vec = self.r0[1] + self.b * np.sin(self.t_vec)

class Bunch:
    def __init__(self, x0=0, y0=0):
        self.x0 = x0
        self.y0 = y0
        self.curves = []

    def erase(self):
        self.curves = []

    def add_curve(self, curve):
        self.curves.append(curve)

    #def calculate(self):
    def calculate(self, *args, **kwargs):
        raise NotImplementedError

    def __add__(self, other):
        if not isinstance(other, Bunch):
            raise TypeError("Only Bunch objects can be added together.")
        
        #combined_bunch = Bunch()  # Change to Bunch instead of MixedBunch
        combined_bunch = MixedBunch()  # Use MixedBunch to combine

        combined_bunch.curves = self.curves + other.curves  # Combine the curve lists
            
        return combined_bunch

class LineBunch(Bunch):
    def __init__(self, point_pairs, thickness):
        super().__init__()
        for pair in point_pairs:
            x1, y1 = pair[0]
            x2, y2 = pair[1]
            line = Line(x1, y1, x2, y2, thickness = thickness)
            self.add_curve(line)  

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

class EllipseBunch(Bunch):
    def __init__(self):
        super().__init__()
        self.calculate()

    def calculate(self, ae=80):
        self.erase()
        e = ae
        incr = 5.0
        for i in range(1, 10):
            a = 80 + i * incr
            b = math.sqrt(a * a - e * e)
            ellipse = Ellipse(a, b)
            self.add_curve(ellipse)

class HyperbolaBunch(Bunch):
    def __init__(self):
        super().__init__()
        self.calculate()

    def calculate(self, ae=80):
        self.erase()
        e = ae
        incr = math.pi / 10
        for i in range(1, 10):
            ani = i * incr
            hyperbola = Hyperbola(e, ani)
            self.add_curve(hyperbola)

class MixedBunch(Bunch):
    def __init__(self):
        super().__init__()

    def calculate(self, ae=80):
        for curve in self.curves:
            curve.clear_points()  # Clear existing points for each curve
            curve.calculate()     # Recalculate each curve based on its type