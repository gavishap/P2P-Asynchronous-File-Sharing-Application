import os
from asyncio import IncompleteReadError
from beautifultable import BeautifulTable
from core.tracker import Tracker
from core.peer import Peer
from core.exceptions import *
import ui.aiocmd as aiocmd
from aioconsole.stream import get_standard_streams
import logging

# Terminal input and output requests
class TrackerTerminal(aiocmd.Cmd):
    INTRO = 'Welcome to \033[1mTracker\033[0m terminal.    Type help or ? to list commands.\n'
    PROMPT = '\033[1mTracker>\033[0m '

    def __init__(self, tracker):
        assert isinstance(tracker, Tracker)
        self._tracker = tracker
        super().__init__()

    async def do_start(self, arg):
        arg = arg.split(' ')
        if len(arg) < 2:
            print('Not enough argument, start <host> <port>')
        else:
            try:
                await self._tracker.start((arg[0], int(arg[1])))
            except ServerRunningError:
                print('Tracker is already running.')
            except OSError as e:
                if e.errno == 48:
                    print('Cannot bind on address {}:{}.'.format(arg[0], arg[1]))
                else:
                    raise
        print('Tracker started listening on {}'.format(self._tracker.address()))


    async def do_list_peers(self, arg):
        table = BeautifulTable()
        table.rows.separator = ''
        table.columns.header = ['Peer Address']
        for peer in self._tracker.peers():
            table.rows.append([peer])
        _, std_writer = await get_standard_streams()
        std_writer.write(str(table).encode('utf-8'))
        std_writer.write('\n'.encode('utf-8'))
        await std_writer.drain()

    async def do_list_files(self, arg):
        file_list_dict = self._tracker.file_list()
        table = BeautifulTable()
        table.rows.separator = ''

        for filename, fileinfo in file_list_dict.items():
            if len(table.columns) == 0:
                table.columns.header = ['Filename'] + list(map(lambda x: x.capitalize(), tuple(fileinfo.keys())))
            table.rows.append((filename, ) + tuple(fileinfo.values()))
        _, std_writer = await get_standard_streams()
        std_writer.write(str(table).encode('utf-8'))
        std_writer.write('\n'.encode('utf-8'))
        await std_writer.drain()

    # Get file chunk details
    async def do_list_chunkinfo(self, arg):
        _, std_writer = await get_standard_streams()
        std_writer.write(str(self._tracker.chunkinfo()).encode('utf-8'))
        std_writer.write('\n'.encode('utf-8'))
        await std_writer.drain()

    async def do_exit(self, arg):
        await self._tracker.stop()
        return True


# Peer input and output requests
class PeerTerminal(aiocmd.Cmd):
    INTRO = 'Welcome to \033[1mPeer\033[0m terminal.    Type help or ? to list commands.\n'
    PROMPT = '\033[1mPeer>\033[0m '

    def __init__(self, peer):
        assert isinstance(peer, Peer)
        self._peer = peer
        super().__init__()

    async def do_publish(self, arg):
        arg = arg.split(' ')[0]
        try:
            await self._peer.publish(arg)
        except FileNotFoundError:
            print('File {} doesn\'t exist.'.format(arg))
        except FileExistsError:
            print('File {} already registered on tracker, use \'list_files\' to see.'.format(arg))
        except TrackerNotConnectedError:
            print('Tracker is not connected. Use \'connect <tracker_ip> <tracker_port> to connect.\' ')
        except (ConnectionError, RuntimeError, IncompleteReadError):
            print('Error occurred during communications with tracker, try to re-connect.')
        except InProgressError:
            print('Publish file {} already in progress.'.format(arg))
        else:
            print('File {} successfully published on tracker.'.format(arg))

    # Connect to the main server
    async def do_connect(self, arg):
        arg = arg.split(' ')
        if len(arg) < 2:
            print('More arguments required! Usage: connect <address> <port>')
        try:
            await self._peer.connect((arg[0], int(arg[1])))
        except AlreadyConnectedError as e:
            print('Peer already connected to {}.'.format(e.address))
        except ConnectionRefusedError:
            print('Cannot connect to tracker.')
        except (ConnectionError, RuntimeError, IncompleteReadError, AssertionError):
            print('Error occurred during communications with tracker.')
        else:
            print('Successfully connected!')

    async def do_list_files(self, arg):
        try:
            file_list_dict = await self._peer.list_file()
        except TrackerNotConnectedError:
            print('Tracker is not connected, try \'connect <tracker_ip> <tracker_port>\' to connect.')
        except (ConnectionError, RuntimeError, IncompleteReadError):
            print('Error occured during communications with tracker, '
                  'try \'connect <tracker_ip> <tracker_port>\' to re-connect.')
        else:
            table = BeautifulTable()
            table.rows.separator = ''

            for filename, fileinfo in file_list_dict.items():
                if len(table.columns) == 0:
                    table.columns.header = ['Filename'] + list(map(lambda x: x.capitalize(), tuple(fileinfo.keys())))
                table.rows.append((filename,) + tuple(fileinfo.values()))
            print(table)

    async def do_set_delay(self, arg):
        arg = arg.split(' ')[0]
        if arg == '':
            print('Usage: set_delay <delay>, <delay> is required.')
        else:
            self._peer.set_delay(float(arg))
            print('Delay {} successfully set.'.format(arg))

    async def do_download(self, arg):
        filename, destination, *_ = arg.split(' ')
        from tqdm import tqdm

        def tqdm_hook_wrapper(t):
            last_chunk = [0]

            def update_to(chunknum=1, chunksize=1, tsize=None):
                if tsize is not None:
                    t.total = tsize
                t.update((chunknum - last_chunk[0]) * chunksize)
                last_chunk[0] = chunknum

            return update_to
        try:
            with tqdm(unit='B', unit_scale=True, unit_divisor=1024, miniters=1, desc='Downloading ...') as t:
                # no report hook if we need debug logging (too many logs will cause trouble to tqdm)
                hook = tqdm_hook_wrapper(t) if logging.getLogger().getEffectiveLevel() != logging.DEBUG else None

                await self._peer.download(filename, destination, reporthook=hook)
        except TrackerNotConnectedError:
            print('Tracker not connected, cannot pull initial chunk information.')
        except FileNotFoundError:
            print('File {} doesn\'t exist, please check filename and try again.'.format(filename))
        except (IncompleteReadError, ConnectionError, RuntimeError):
            print('Error occurred during transmission.')
        except DownloadIncompleteError as e:
            print('File chunk # {} doesn\'t exist on any peers, download isn\'t completed.'.format(e.chunknum))
            # try to remove incomplete file
            try:
                os.remove(destination)
            except FileNotFoundError:
                pass
        else:
            print('File {} successfully downloaded to {}.'.format(filename, destination))

    async def do_exit(self, arg):
        await self._peer.stop()
        return True
