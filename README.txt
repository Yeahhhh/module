Build this library package:
    cd module/yeah
    vi GNUmakefile
    gmake clean
    gmake



Use this library package:

Method 1:
    put the entire package ("module") under your project
    cc -I./module -c a.c
    cc a.o -L./module/lib -lyeahc

Method 2:
    source PATH/TO/module/sourceme.bash   # Import environment variables using Bash
    cc -c a.c
    cc a.o -lyeahc

