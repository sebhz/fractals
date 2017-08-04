## Synopsis

Various programs, scripts and other trials around fractals in C and Python.
Most are pretty old, and I am not even sure they still compile.

For the record you will find here:

- `mandelbrot/yambe`: "Yet Another MandelBrot Explorer". Written in C. Can use MPFR library for high precision computation. Uses SDL1.2 for rendering. Single threaded. Can display Julia sets too.
- `mandelbrot/other scripts`: plain simple mandelbrot explorers/renderers in other languages (Python and Lua). Can also display Collatz fractal.
- `lsystems`: [lsystems](https://en.wikipedia.org/wiki/L-system) generator written in C.
- `attractors`: Strange attractors in 2D and 3D, in  C and Python. Only `python/attractors.py` is probably a bit interesting. Its performance is pretty poor though.

The only one I am still playing with is the python polynomial strange attractors generator, which is able to generate some pretty nice pictures like the one below.

![27_VOno5297VsEUWfQOXJQZHiOL93D01EMguf9BVmgNkfIAbIMaYJrLYAD9ulGNtMQpO8CXhgT5](http://sebhz.github.io/img/27_VOno5297VsEUWfQOXJQZHiOL93D01EMguf9BVmgNkfIAbIMaYJrLYAD9ulGNtMQpO8CXhgT5_8.png)

## Credits

The `attractors.py` script is based on [Julien's Sprott book](http://sprott.physics.wisc.edu/sa.htm). Some of the coloring ideas (histogram equalization) come from [Ian Witham's blog](http://ianwitham.wordpress.com/category/graphics/strange-attractors-graphics/) (but I prefer my version!). Mandelbrot set colorization ideas came from [David Madore's site](http://www.madore.org/~david/programs/#prog_mandel).

## License

All those are GPL - even if I doubt those half-baked scripts would be of any use to anyone. Feel free to use any of them under the GPL terms !


