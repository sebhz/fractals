# Synopsis

Python strange attractor generator.

Can create and display:

- Polynomial attractors,
- Peter de Jong attractors,
- Clifford Pickover attractors,
- Symmetrical icons attractors.

Adding new attractor type is trivial.

# Reference and credits

Polynomial attractors convergence is checked using the algorithms described in Julian C. Sprott [Creating pattern in chaos](http://sprott.physics.wisc.edu/fractals/booktext/sabook.pdf) book - which by the way is a must read if you are interested in fractals and attractors.

The symmetrical icons are described in Michael Field and Martin Golubitsky "Symmetry in chaos" book. J.C. Sprott also had written an article describing similar techniques in the early 90's.

The original coloring ideas (histogram equalization) came from [Ian Witham's blog](http://ianwitham.wordpress.com/category/graphics/strange-attractors-graphics/). I ended up implementing coloring using gradient mapping and equalizing only Value component, which gives nice results.

There are many other softwares out there dealing with strange attractors generation. They are much more advanced and efficient than my programs. Check them !

# Dependencies

Those scripts depend on python-opencv for image display, image saving (PNG format) and image resizing.

# Images

The images below were produced using the `generate.py` script, with 128.000.000 iterations and a downsampling factor of 2.

### Order 2 polynomial attractor
x<sub>n+1</sub>=-0.125+0.250*x<sub>n</sub>-3.625*x<sub>n</sub><sup>2</sup>-1.375*y<sub>n</sub>+1.500*x<sub>n</sub>*y<sub>n</sub>-1.000*y<sub>n</sub><sup>2</sup>
y<sub>n+1</sub>=-1.000+2.500*x<sub>n</sub>+0.750*x<sub>n</sub><sup>2</sup>-1.750*y<sub>n</sub>+2.500*x<sub>n</sub>*y<sub>n</sub>-1.375*y<sub>n</sub><sup>2</sup>

![22_TW1JgMMoaGoJ](https://sebhz.github.io/img/attractors/22_TW1JgMMoaGoJ.png)

### Order 3 polynomial attractor
x<sub>n+1</sub>=-0.625*x<sub>n</sub>-3.375*x<sub>n</sub><sup>2</sup>-3.125*x<sub>n</sub><sup>3</sup>-1.250*y<sub>n</sub>-2.750*x<sub>n</sub>*y<sub>n</sub>+1.250*x<sub>n</sub><sup>2</sup>*y<sub>n</sub>-2.875*y<sub>n</sub><sup>2</sup>-1.750*x<sub>n</sub>*y<sub>n</sub><sup>2</sup>-1.125*y<sub>n</sub><sup>3</sup><br>
y<sub>n+1</sub>=0.125+1.250*x<sub>n</sub>-3.125*x<sub>n</sub><sup>2</sup>-3.125*x<sub>n</sub><sup>3</sup>+0.500*y<sub>n</sub>-1.125*x<sub>n</sub>*y<sub>n</sub>-0.750*x<sub>n</sub><sup>2</sup>*y<sub>n</sub>-2.375*y<sub>n</sub><sup>2</sup>-0.375*x<sub>n</sub>*y<sub>n</sub><sup>2</sup>-3.000*y<sub>n</sub><sup>3</sup>

![23_UP35K8e7GLVe55YLOBR6](https://sebhz.github.io/img/attractors/23_UP35K8e7GLVe55YLOBR6.png)

### Order 4 polynomial attractor
x<sub>n+1</sub>=0.875-0.875*x<sub>n</sub>-1.625*x<sub>n</sub><sup>2</sup>+2.625*x<sub>n</sub><sup>3</sup>+3.000*x<sub>n</sub><sup>4</sup>-2.625*y<sub>n</sub>-0.375*x<sub>n</sub>*y<sub>n</sub>+3.000*x<sub>n</sub><sup>2</sup>*y<sub>n</sub>+1.625*x<sub>n</sub><sup>3</sup>*y<sub>n</sub>+1.750*y<sub>n</sub><sup>2</sup>-1.750*x<sub>n</sub>*y<sub>n</sub><sup>2</sup>-0.125*x<sub>n</sub><sup>2</sup>*y<sub>n</sub><sup>2</sup>+1.125*y<sub>n</sub><sup>3</sup>+1.875*x<sub>n</sub>*y<sub>n</sub><sup>3</sup>-0.625*y<sub>n</sub><sup>4</sup><br>
y<sub>n+1</sub>=1.000*x<sub>n</sub>-1.375*x<sub>n</sub><sup>2</sup>-3.500*x<sub>n</sub><sup>3</sup>-1.250*x<sub>n</sub><sup>4</sup>+2.250*y<sub>n</sub>+2.125*x<sub>n</sub>*y<sub>n</sub>-1.000*x<sub>n</sub><sup>2</sup>*y<sub>n</sub>-1.750*x<sub>n</sub><sup>3</sup>*y<sub>n</sub>-1.875*y<sub>n</sub><sup>2</sup>-2.500*x<sub>n</sub>*y<sub>n</sub><sup>2</sup>+1.750*x<sub>n</sub><sup>2</sup>*y<sub>n</sub><sup>2</sup>+0.875*y<sub>n</sub><sup>3</sup>-3.500*x<sub>n</sub>*y<sub>n</sub><sup>3</sup>-2.250*y<sub>n</sub><sup>4</sup>

![24_bNHps9RshiGTdjPUcJ2KmlMGFAib2C](https://sebhz.github.io/img/attractors/24_bNHps9RshiGTdjPUcJ2KmlMGFAib2C.png)

### Clifford attractor
x<sub>n+1</sub>=sin(-1.1875*y<sub>n</sub>)-0.6250*cos(-1.1875*x<sub>n</sub>)<br>
y<sub>n+1</sub>=sin(-1.5625*x<sub>n</sub>)+1.7500*cos(-1.5625*y<sub>n</sub>)

![cBK5w](https://sebhz.github.io/img/attractors/cBK5w.png)

### Clifford attractor
x<sub>n+1</sub>=sin(0.8750*y<sub>n</sub>)-1.3750*cos(0.8750*x<sub>n</sub>)<br>
y<sub>n+1</sub>=sin(1.4375*x<sub>n</sub>)+0.7500*cos(1.4375*y<sub>n</sub>)

![ci8rg](https://sebhz.github.io/img/attractors/ci8rg.png)

### deJong attractor
x<sub>n+1</sub>=sin(2.125*y<sub>n</sub>)-cos(-0.625*x<sub>n</sub>)<br>
y<sub>n+1</sub>=sin(-0.750*x<sub>n</sub>)-cos(-2.250*y<sub>n</sub>)

![jlPOC](https://sebhz.github.io/img/attractors/jlPOC.png)

### deJong attractor
x<sub>n+1</sub>=-cos(-2.000*x<sub>n</sub>)<br>
y<sub>n+1</sub>=sin(-2.875*x<sub>n</sub>)-cos(3.625*y<sub>n</sub>)

![jUE7x](https://sebhz.github.io/img/attractors/jUE7x.png)

### Symmetrical icon attractor
Symmetry order: 3<br>
&lambda;=2.000 - &alpha;=-2.750 - &beta;=1.875 - &gamma;=0.125 - &omega;=0.250

![s8kjVW3](https://sebhz.github.io/img/attractors/s8kjVW3.png)

### Symmetrical icon attractor
Symmetry order: 3<br>
&lambda;=0.875 - &alpha;=-2.500 - &beta;=-0.750 - &gamma;=2.875 - &omega;=-1.375

![sAbOrJ3](https://sebhz.github.io/img/attractors/sAbOrJ3.png)

