**Table of Contents**

- [Introduction](#introduction)
- [Command Line](#command-line)

# Introduction

StreamPref is a data stream management system (DSMS) prototype with support to temporal conditional preferences queries [StreamPref Project](http://streampref.github.io).

The execution of queries by the system is controlled by an environment file.
On following, we have an example of a environment file:

```
###############################################################################
# Registration of tables and streams
#
# You have to inform the table/stream name, attributes, attributes types and
# the input file (for data reading). 

# Stream example
REGISTER STREAM s (a INTEGER, b STRING, c FLOAT)
INPUT 'in/s.csv';

# Stream table example
REGISTER TABLE t (a INTEGER, b STRING, c FLOAT)
INPUT 'in/t.csv';
###############################################################################
# Registration of queries
#
# You have to inform the query name, the input file with the query code.
# Optionally, you can inform an output file to print the query result.

REGISTER QUERY q
INPUT 'queries/q.query'
OUTPUT 'out/q.out';

# You also can use the keyword CHANGE to print the insertions and deletions
# instead of the query result

REGISTER QUERY q2
INPUT 'queries/q2.query' 
OUTPUT CHANGES 'out/q2.out';
```

Every input file must have the column **_fl** with the instant (or timestamp) of the tuple and the remaining columns.
The name of the columns must be identical to attributes name declared in the registration of the stream/table.
Example of an input stream file:

```
_ts,  a, b,  c
  0,  1, AA, 0.5
  0,  2, BB, 0.6
  1,  1, AA, 0.5
  2,  3, CC, 1.6
  2,  1, AA, 0.7
  2,  2, BB, 0.8
  3,  1, AA, 0.9
  4,  3, CC, 1.0
```
The input table files must have the additional attribute **_fl**.
This attributes indicates the insertion (+) or deletion of a tuple (-).
We can delete only those tuples inserted in previous instant.
If you try to delete an non-existing tuple, the system raises an exception.
Example of an input table file:

```
_ts, _fl, a, b,  c
  0, +, 1, AA, 0.5
  0, +, 2, BB, 0.6
  1, -, 1, AA, 0.5
  2, +, 3, CC, 1.6
  2, +, 1, AA, 0.7
  2, -, 2, BB, 0.6
  3, +, 1, AA, 0.9
  4, +, 3, CC, 1.0
```

Example of an query file:

Please see the directory [examples](examples/) for more examples.

# Command Line

```
usage: StreamPref [-h] -e ENV [-m MAX] [-l LOG] [-D] [-o OUTCOMP]
                  [-d DETAILS] [-r DELIMITER] [-p PREF_ALG] [-t TPREF_ALG]
                  [-s SUBSEQ_ALG]

optional arguments:
  -h, --help                              Show the help message and exit
  -e ENV, --env ENV                       Environment file
  -m MAX, --max MAX                       Maximum timestamp to run
  -l LOG, --logfile LOG                   Log file
  -D, --debug                             Debug execution
  -o OUTCOMP, --outcomparisons OUTCOMP    Output comparisons statistics
  -d DETAILS, --details DETAILS           Save execution details to file
  -r DELIMITER, --delimiter DELIMITER     File content delimiter
  -p PREF_ALG, --pref PREF_ALG            Preference algorithm
  -t TPREF_ALG, --tpref TPREF_ALG         Temporal preference algorithm
  -s SUBSEQ_ALG, --subseq SUBSEQ_ALG      Subsequence algorithm
```
