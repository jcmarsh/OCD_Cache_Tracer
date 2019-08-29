# Benchmark Programs

These are the programs that can be run for cache profiling / fault injection (soon) / pmu counter tests.

/common: files used for setting up the board and configuring the caches

## Micro Benchmarks

In development.
Each of these is intended to stress a different behavior of the cache or test setup.

/micro_evict: load 2x words (where x is the number of ways) from colliding addresses to force evictions
 
/micro_prefetch: load data by accessing every 2n word in a range, and then access every 2n+1 word (which may have been pre-fetched)

/micro_time: DrSEUs with Simics uses discrete checkpoints to inject faults, whereas our JTAG based approach can inject at any point.
This benchmark should expose how this can lead to differing results.

## MiBench

/mi_adpcm:

/mi_aes:

/mi_basicmath:

/mi_bitcount:

/mi_crc:

/mi_fft:

/mi_gsm:

/mi_qsort:

/mi_qsort_test:

/mi_susan:

## Quinn Benchmarks

/q_aes:

/q_cache:

/q_matrix:

/q_qsort:


## Others

/lzo: Runs LZO to compress and then decompress some data from the Kepler mission.
TODO: Needs to output something to show that the data wasn't corrupted.

/lzo_loop: Similar to lzo, but runs in a longer to loop in an attempt to show timing differences between runs with prefetching enabled or disabled.
Should NOT be run with the normal DrSEUs scripts.

/global_timer_test: Just trying to figure out how to use the ARM global timer and relate it back to wall time.

## Test

/fib_rec:

/fib_short:

/test_binary_out:

/test_loop:
