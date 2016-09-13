libraries that I frequently use in Linux X86_64





Build this library package:
    cd module/yeah
    vi GNUmakefile
    gmake clean
    gmake




Use this library package:

Method 1 (prefered):
    source PATH/TO/module/sourceme.bash   # Import environment variables in Bash
    cc -c a.c
    cc a.o -lyeahc

Method 2:
    put the entire package ("module") under your project
    cc -I./module -c a.c
    cc a.o -L./module/lib -lyeahc


