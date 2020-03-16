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

Those images were produced using the generate.py script, with 128.000.000 iterations and a downsampling factor of 2.

![22_TW1JgMMoaGoJ](http://sebhz.github.io/img/attractors/22_TW1JgMMoaGoJ.png)
Order 2 polynomial attractor
![23_UP35K8e7GLVe55YLOBR6](http://sebhz.github.io/img/attractors/23_UP35K8e7GLVe55YLOBR6.png)
Order 3 polynomial attractor
![24_bNHps9RshiGTdjPUcJ2KmlMGFAib2C](http://sebhz.github.io/img/attractors/24_bNHps9RshiGTdjPUcJ2KmlMGFAib2C)
Order 4 polynomial attractor
![25_WY8nMzJbpjKXXFqTkSfMgSkPU15XM6xKK1EBI1c3yR](http://sebhz.github.io/img/attractors/25_WY8nMzJbpjKXXFqTkSfMgSkPU15XM6xKK1EBI1c3yR.png)
Order 5 polynomial attractor
![cBK5w](http://sebhz.github.io/img/attractors/cBK5w.png)
Clifford attractor
![ci8rg](http://sebhz.github.io/img/attractors/ci8rg.png)
Clifford attractor
![jlPOc](http://sebhz.github.io/img/attractors/jlPOc.png)
deJong attractor
![jUE7x](http://sebhz.github.io/img/attractors/jUE7x.png)
deJong attractor
![s8kjVW3](http://sebhz.github.io/img/attractors/s8kjVW3.png)
Symmetrical icon attractor
![sABOrJ3](http://sebhz.github.io/img/attractors/sABOrJ3.png)
Symmetrical icon attractor

