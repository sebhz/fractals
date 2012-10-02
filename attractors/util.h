void diffTime (const char *caption, struct timeval *t1, struct timeval *t2);

inline GLdouble power (GLdouble base, unsigned int exp);

inline point newPoint (void);

point eval (point p, struct polynom *polynom);

GLdouble euclidianDistance (point a, point b);

inline point _scalar_mul (point p, GLdouble m);

inline GLdouble _abs (point p);

inline GLdouble _modulus (point p);

inline point _sub (point a, point b);;

inline point _middle (point a, point b);
