# Table of Contents

- [Introduction](#introduction)
- [Command Line](#command-line)
- [Algorithms](#algorithms)

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

The query file content must follow the StreamPref grammar (see file __grammar/streampref.ebnf__).
Example of an query file with temporal conditional preferences:

```
SELECT SUBSEQUENCE END POSITION
FROM SUBSEQUENCE CONSECUTIVE TUPLES
FROM SEQUENCE IDENTIFIED BY pid [RANGE 20 SECOND]
FROM moves AS m
WHERE MINIMUM LENGTH IS 2
AND MAXIMUM LENGTH IS 4
ACCORDING TO TEMPORAL PREFERENCES
IF FIRST THEN move = 'rec' BETTER move = 'lbal'
AND
IF PREVIOUS (move = 'cond') THEN (move = 'drib') BETTER (move = 'pass')[place]
AND
(move = 'pass') BETTER (move = 'bpas')[place]
AND
IF ALL PREVIOUS (place = 'oi') THEN (place = 'oi') BETTER (place = 'mf');
```

Please see the directory __examples__ for more examples.

# Command Line

```
streampref.py [-h] -e ENV [-m MAX] [-l LOG] [-D] [-o OUTCOMP]
              [-d DETAILS] [-r DELIMITER] [-p PREF_ALG] [-t TPREF_ALG]
              [-s SUBSEQ_ALG]
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

# Algorithms

When the queries have the operators __BEST__, __TOPK__, __CONSEQ__, __ENDSEQ__, __BESTSEQ__ and __TOPKSEQ__, the user can choose an algorithm to evaluate the operators.
The evaluations of the operators __BEST__ and __TOPK__ can be performed by the following algorithms:
- *depth_search*: Depth search first comparison algorithm (non incremental);
- *partition*: Preference partition algorithm (non incremental);
- *inc_ancestors*: Ancestors list algorithm (incremental);
- *inc_graph*: Graph algorithm (incremental);
- *inc_graph_no_transitive*: Graph algorithm without transitive comparisons (incremental); 
- *inc_partition*: Preference partition algorithm (incremental).

The evaluation of operators __CONSEQ__ and __ENDSEQ__ can be performed by the following algorithms:
- *naive*: Naive algorithm (non incremental);
- *incremental*: Incremental algorithm using deletions and insertions.

The evaluation of the algorithms __BESTSEQ__ and __TOPKSEQ__ can be performed by the following algorithms:
- *depth_search*: Depth search first algorithm (non incremental);
- *inc_seqtree*: Algorithm using the sequences tree index (incremental);
- *inc_seqtree_pruning*: Algorithm using the sequences tree index with pruning strategy (incremental).

Please see the related publications for more information.
