import asyncio
import sys
import argparse
import logging
import coloredlogs
from core.peer import Peer
from core.tracker import Tracker
from ui.terminal import TrackerTerminal, PeerTerminal

coloredlogs.install(level='ERROR', fmt='%(levelname)s:%(module)s: %(message)s')

# uvloop does not work on windows, so we will use default loop
if sys.platform != 'win32':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def main():
    arg_parser = argparse.ArgumentParser(description=__doc__)
    # Option argument for a peer or tracker
    arg_parser.add_argument('option', metavar='OPTION', type=str, nargs=1)
    results = arg_parser.parse_args()

    taskloop = asyncio.get_event_loop()
    obj = None
    terminal = None
    if results.option[0] == 'tracker':
        obj = Tracker()
        terminal = TrackerTerminal(obj)
    elif results.option[0] == 'peer':
        obj = Peer()
        taskloop.run_until_complete(obj.start(('localhost', 0)))
        terminal = PeerTerminal(obj)
    else:
        logging.error('Option must either be \'tracker\' or \'peer\'')
        exit(0)
    try:
        taskloop.run_until_complete(terminal.cmdloop())
    except (KeyboardInterrupt, EOFError):
        pass
    except Exception as e:
        logging.error('{}:{}'.format(type(e).__name__, e))
    finally:
        taskloop.run_until_complete(obj.stop())
        taskloop.close()


if __name__ == '__main__':
    main()
