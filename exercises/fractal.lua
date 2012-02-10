#!/usr/bin/lua

require "gd"

-------------------------------------------------------------
-- Basic complex operations implemented as a "class"
-- Very crude and incomplete implementation
--
complex = {}

function complex:new(r, i)
	if i == nil then i = 0 end
	if type(r) ~= "number" or type(i) ~= "number" then
	   error("Bad argument for complex constructor", 1)
	end
	local c = { real = r, imag = i }
	setmetatable(c, self)
	self.__index = self
	return c
end

function complex:cos()
	return complex:new( math.cos(self.real)*math.cosh(self.imag),
				       -math.sin(self.real)*math.sinh(self.imag))
end

function complex:modulus()
	return math.sqrt(self.real*self.real + self.imag*self.imag)
end

function complex.__mul(a, b)
	if type(b) == "number" then return complex.new (a.real*b, a.imag*b) end
	return complex:new( a.real*b.real - a.imag*b.imag, 
		                a.imag*b.real + a.real*b.imag)
end

function complex.__add(a, b)
	if type(b) == "number" then return complex:new( a.real + b, a.imag ) end
	return complex:new( a.real+ b.real, a.imag + b.imag )
end

function complex:__tostring()
	return "(" .. self.real .. "," .. self.imag .. ")"
end

---------------------------------------------------------
-- Now the crude fractal class
fractal = {}

function fractal:new(l, m, t)
	local f = { limit = l, maxiter = m }
	
	if t == "julia" then
		f.f = self.julia
	elseif t == "mandelbrot" then
		f.f = self.mandelbrot
	else
		print("Unsupported fractal type. Defaulting to good old Mandelbrot")
		f.f = self.mandelbrot
	end
	setmetatable(f, self)
	self.__index = self
	return f
end

function fractal:julia(c, p)
	local m, escape
	
	for i = 0,self.maxiter-1 do
		c = c*c + p
		m = c:modulus()
		escape = i
		if m > self.limit then break end
	end
	
	return { escape, m }
end

function fractal:mandelbrot(c, p)
	local z = complex:new(0)
	local m, escape
	
	for i = 0,self.maxiter-1 do
		z = z*z + c
		m = z:modulus()
		escape = i
		if m > self.limit then break end
	end

	return { escape, m }
end

-- collatz : (2 + 7*c - (2 + 5*c)*cmath.cos(cmath.pi*c))/4;
-- not implemented here - too complicated to play with metamethods :-) 

function fractal:compute(center, xres, yres, xlength, p)
	-- set the center point in the center of the window, 
	-- with an X axis of size xlength, and an orthogonal projection
	local ratio = yres/xres
	local xmin = center.real - xlength/2
	local ymin = center.imag - xlength*ratio/2
	local ylength = xlength * ratio
	local l = {}
	local i = 1
	
	for y=0, yres-1 do
		for x=0, xres-1 do
			local c = complex:new(xmin + (x - 0.0)*xlength/xres,
			                      ymin + (y - 0.0)*ylength/yres)
			l[i] = self:f(c, p)
			i = i + 1
		end
	end
	return l
end

------------------------------------------
-- coloring/display functions
function colorize(l, ccoef, maxiter)
	-- From 0->511 to 0->255 using a triangular map
	local col = 
		function(c) if c < 128 then	return c+128
					elseif c < 384 then return 383-c
					else return c-384 end
		end
	local log2 = function(x) return math.log(x)/math.log(2) end			
	local lc = {}
	
	for i, item in ipairs(l) do
		if item[1] == maxiter - 1 then
			lc[i] = { red = 0, green = 0, blue = 0 }
		else
			local v = 8 * math.sqrt(item[1] + 3 - 
					  log2(math.log(math.sqrt (item[2]))));
			lc[i] = { blue  = col(math.floor((v*ccoef.cblue))%512),  
			          green = col(math.floor((v*ccoef.cgreen))%512),
					  red   = col(math.floor((v*ccoef.cred))%512) }
		end
	end
	return lc
end
	
function createImage(w, h, l)
	local image = gd.createTrueColor(w, h)
	for i, color in ipairs(l) do
		c = image:colorAllocate(color.red, color.green, color.blue)
		local x = i % w
		local y = math.floor(i/w)
		image:setPixel(x, y, c)
	end
	return image
end
------------------------------------------
-- Main program
local c = complex:new(-0.5, 0)
local xres = 320 --2048
local yres = 240 --1536
local maxiter = 128
local f = fractal:new(8, maxiter, "mandelbrot")
local t = os.clock()
local l = f:compute(c, xres, yres, 3.4)
t = os.clock()-t
print("Time taken to compute and color set: ", t, " secs")
local lc = colorize(l, {cblue = 2, cgreen = 3, cred = 5}, maxiter)
local image = createImage(xres, yres, lc)
image:png("out.png")
