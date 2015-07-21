# -*- coding: utf-8 -*-

import functools
import sys

import click_log

from .. import __version__, log
from ..doubleclick import click


cli_logger = log.get(__name__)


class AppContext(object):
    def __init__(self):
        self.config = None
        self.passwords = {}
        self.logger = None


pass_context = click.make_pass_decorator(AppContext, ensure=True)


class CliError(RuntimeError):
    def __init__(self, msg, problems=None):
        self.msg = msg
        self.problems = problems
        RuntimeError.__init__(self, msg)

    def format_cli(self):
        msg = self.msg.rstrip(u'.:')
        if self.problems:
            msg += u':'
            if len(self.problems) == 1:
                msg += u' {}'.format(self.problems[0])
            else:
                msg += u'\n' + u'\n  - '.join(self.problems) + u'\n\n'

        return msg


def catch_errors(f):
    @functools.wraps(f)
    def inner(*a, **kw):
        try:
            f(*a, **kw)
        except:
            from .utils import handle_cli_error
            handle_cli_error()
            sys.exit(1)

    return inner


def validate_verbosity(ctx, param, value):
    x = getattr(log.logging, value.upper(), None)
    if x is None:
        raise click.BadParameter(
            'Must be CRITICAL, ERROR, WARNING, INFO or DEBUG, not {}'
            .format(value)
        )
    return x


@click.group()
@click_log.init('vdirsyncer')
@click_log.simple_verbosity_option()
@click.version_option(version=__version__)
@pass_context
@catch_errors
def app(ctx):
    '''
    vdirsyncer -- synchronize calendars and contacts
    '''
    from .utils import load_config

    if not ctx.config:
        ctx.config = load_config()

main = app


def max_workers_callback(ctx, param, value):
    if value == 0 and click_log.get_level() == log.logging.DEBUG:
        value = 1

    cli_logger.debug('Using {} maximal workers.'.format(value))
    return value


max_workers_option = click.option(
    '--max-workers', default=0, type=click.IntRange(min=0, max=None),
    callback=max_workers_callback,
    help=('Use at most this many connections. With debug messages enabled, '
          'the default is 1, otherwise one connection per collection is '
          'opened.')
)


@app.command()
@click.argument('pairs', nargs=-1)
@click.option('--force-delete/--no-force-delete',
              help=('Do/Don\'t abort synchronization when all items are about '
                    'to be deleted from both sides.'))
@max_workers_option
@pass_context
@catch_errors
def sync(ctx, pairs, force_delete, max_workers):
    '''
    Synchronize the given pairs. If no arguments are given, all will be
    synchronized.

    This command will not synchronize metadata, use `vdirsyncer metasync` for
    that.

    Examples:

        `vdirsyncer sync` will sync everything configured.

        `vdirsyncer sync bob frank` will sync the pairs "bob" and "frank".

        `vdirsyncer sync bob/first_collection` will sync "first_collection"
        from the pair "bob".
    '''
    from .tasks import prepare_pair, sync_collection
    from .utils import parse_pairs_args, WorkerQueue
    general, all_pairs, all_storages = ctx.config

    wq = WorkerQueue(max_workers)

    for pair_name, collections in parse_pairs_args(pairs, all_pairs):
        wq.put(functools.partial(prepare_pair, pair_name=pair_name,
                                 collections=collections,
                                 general=general, all_pairs=all_pairs,
                                 all_storages=all_storages,
                                 force_delete=force_delete,
                                 callback=sync_collection))
        wq.spawn_worker()

    wq.join()


@app.command()
@click.argument('pairs', nargs=-1)
@max_workers_option
@pass_context
@catch_errors
def metasync(ctx, pairs, max_workers):
    '''
    Synchronize metadata of the given pairs.

    See the `sync` command regarding the PAIRS argument.
    '''
    from .tasks import prepare_pair, metasync_collection
    from .utils import parse_pairs_args, WorkerQueue
    general, all_pairs, all_storages = ctx.config

    wq = WorkerQueue(max_workers)

    for pair_name, collections in parse_pairs_args(pairs, all_pairs):
        wq.put(functools.partial(prepare_pair, pair_name=pair_name,
                                 collections=collections,
                                 general=general, all_pairs=all_pairs,
                                 all_storages=all_storages,
                                 callback=metasync_collection))
        wq.spawn_worker()

    wq.join()


@app.command()
@click.argument('pairs', nargs=-1)
@max_workers_option
@pass_context
@catch_errors
def discover(ctx, pairs, max_workers):
    '''
    Refresh collection cache for the given pairs.
    '''
    from .tasks import discover_collections
    from .utils import WorkerQueue
    general, all_pairs, all_storages = ctx.config
    wq = WorkerQueue(max_workers)

    for pair in (pairs or all_pairs):
        try:
            name_a, name_b, pair_options = all_pairs[pair]
        except KeyError:
            raise CliError('Pair not found: {}\n'
                           'These are the pairs found: {}'
                           .format(pair, list(all_pairs)))

        wq.put(functools.partial(
            discover_collections,
            status_path=general['status_path'], name_a=name_a, name_b=name_b,
            pair_name=pair, config_a=all_storages[name_a],
            config_b=all_storages[name_b], pair_options=pair_options,
            skip_cache=True
        ))
        wq.spawn_worker()

    wq.join()


@app.command()
@click.argument('collection')
@pass_context
@catch_errors
def repair(ctx, collection):
    '''
    Repair a given collection.

    Downloads all items and repairs some properties if necessary. Currently
    this only fixes absent or duplicate UIDs.

    Example: `vdirsyncer repair calendars_local/foo` repairs the `foo`
    collection of the `calendars_local` storage.
    '''
    from .tasks import repair_collection
    general, all_pairs, all_storages = ctx.config
    repair_collection(general, all_pairs, all_storages, collection)

# Not sure if useful. I originally wanted it because:
# * my password manager has a timeout for caching the master password
# * when calling vdirsyncer in a cronjob, the master password prompt would
#   randomly pop up
# So I planned on piping a FIFO to vdirsyncer, and writing to that FIFO from a
# cronjob.

try:
    import click_repl
    click_repl.register_repl(app)
except ImportError:
    pass
