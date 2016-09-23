"""strange attractors generation

This package provides classes and function to help
generating and rendering strange attractors.

It supports both polynomial strange attractors and
De Jong strange attractors.

The attractors images can be saved in PNG format if pyPNG is
installed.

Example:

The following code creates, generates and renders a 2nd order polynomial attractor
in a 1024x768 8-bits greyscale PNG image.

	from attractor import util, render, attractor
	geometry = (1024, 768)
	it = util.getIdealIterationNumber('polynomial', geometry)
	at = attractor.PolynomialAttractor(order=2, iter=it)
	at.explore()
	r = render.Renderer(mode='greyscale', geometry=geometry)
	frequencyMap = at.createFrequencyMap(r.geometry, 4)
	pixelArray = r.renderAttractor(frequencyMap)
	r.writeAttractorPNG(pixelArray, "attractor.png")

"""
