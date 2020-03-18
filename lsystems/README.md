# Fractal plants and more

Iterated l-systems in C. See [The algorithmic beauty of plants](http://algorithmicbotany.org/papers/abop/abop.pdf) book.

# Dependencies

This program depends on libsdl and libsdl_gfx. We are talking about libsdl1 here...

# Pictures

### Plant #1
Angle: 25&deg;<br>
Initial string: X<br>
Rules:<br>
    F -> FF<br>
    X -> F-[[X]+X]+F[+FX]-X

![plant1](https://sebhz.github.io/img/lsystems/plant1.png)

### Plant #2
Angle: 18&deg;<br>
Initial string: SLFFF<br>
Rules:<br>
    H -> -Z[+H]L<br>
    L -> [-FFF][+FFF]F<br>
    S -> [+++Z][---Z]TS<br>
    T -> TL<br>
    Z -> +H[-Z]L

![plant2](https://sebhz.github.io/img/lsystems/plant2.png)

### Plant #3
Angle: 22.5&deg;<br>
Initial string: F<br>
Rules:<br>
    F -> FF-[-F+F+F]+[+F-F-F]

![plant3](https://sebhz.github.io/img/lsystems/plant3.png)
