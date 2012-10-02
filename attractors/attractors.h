struct attractor *newAttractor (int order, int dimension,
                                int convergenceIterations, int numPoints);

void computeAttractor (struct attractor *a, char *code);

void freeAttractor (struct attractor *at);

int checkCode (char *code);

int isAttractorConverging (struct attractor *at);

void iterateMap (struct attractor *a);

GLdouble getRadius (struct attractor *a);

void centerAttractor (struct attractor *a);
