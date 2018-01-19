#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Main module
'''

# Manager imports
import logging
import sys


def get_arguments():
    '''
    Get arguments
    '''
    import argparse
    from control.config import DEFAULT_LOG_FILE, \
        DEFAULT_DELIMITER, TUP_DEFAULT_ALG, TUP_ALG_LIST, \
        SEQ_ALG_LIST, SEQ_DEFAULT_ALG, SUBSEQ_ALG_LIST, \
        DEFAULT_SUBSEQ_ALG, DEFAULT_MAX_TIMESTAMP
    parser = argparse.ArgumentParser('StreamPref')
    parser.add_argument('-e', '--env', required=True, help='Environment file')
    parser.add_argument('-m', '--max', default=DEFAULT_MAX_TIMESTAMP,
                        help='Maximum timestamp to run', type=int)
    parser.add_argument('-l', '--logfile', default=DEFAULT_LOG_FILE,
                        help='Log file')
    parser.add_argument('-D', '--debug', action="store_true",
                        default=False,
                        help='Debug execution')
    parser.add_argument('-o', '--outcomparisons', default=None,
                        help='Output comparisons statistics')
    parser.add_argument('-d', '--details', default=None,
                        help='Append execution details to file')
    parser.add_argument('-r', '--delimiter', default=DEFAULT_DELIMITER,
                        help='File content delimiter')
    parser.add_argument('-p', '--pref', choices=TUP_ALG_LIST,
                        default=TUP_DEFAULT_ALG,
                        help='Preference algorithm')
    parser.add_argument('-t', '--tpref', choices=SEQ_ALG_LIST,
                        default=SEQ_DEFAULT_ALG,
                        help='Temporal preference algorithm')
    parser.add_argument('-s', '--subseq', choices=SUBSEQ_ALG_LIST,
                        default=DEFAULT_SUBSEQ_ALG,
                        help='Subsequence algorithm')
    args = parser.parse_args()
    return args


def main():
    '''
    Main StreamPref function
    '''
    from control.manager import Manager
    from control.config import Config, config_log

    # Change maximum recursion limit
    sys.setrecursionlimit(10000)
    # Get arguments
    args = get_arguments()
    # Start log
    config_log(args.logfile, args.debug)
    logger = logging.getLogger(__name__)
    logger.info('Starting server')
    # Create control
    conf = Config(args)
    man = Manager(conf)
    # Initialize control
    if man.initialize():
        logger.debug('Starting execution')
        # Run
        man.run()
    else:
        logger.error('Initialization failed')
    logger.info('Manager stopped')


if __name__ == '__main__':
    main()
