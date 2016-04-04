"""
Rados modle-based integration tests
"""
import contextlib
import logging

log = logging.getLogger(__name__)

@contextlib.contextmanager
def task(ctx, config):
    """
    For each combination of namespace and name_length, create
    <num_objects> objects with name length <name_length>
    on entry.  On exit, verify that the objects still exist, can
    be deleted, and then don't exist.

    Usage::

       create_verify_lfn_objects.py:
         pool: <pool_name> default: 'data'
         prefix: <prefix> default: ''
         namespace: [<namespace>] default: ['']
         num_objects: [<num_objects>] default: 10
         name_length: [<name_length>] default: [400]
    """
    pool = config.get('pool', 'data')
    num_objects = config.get('num_objects', 10)
    name_length = config.get('name_length', [400])
    namespace = config.get('namespace', [None])
    prefix = config.get('prefix', None)

    objects = []
    for l in name_length:
        for ns in namespace:
            def object_name(i):
                nslength = 0
                if namespace is not '':
                    nslength = len(namespace)
                numstr = str(i)
                fillerlen = name_length - nslength - len(prefix) - len(numstr)
                assert fillerlen >= 0
                return prefix + ('a'*fillerlen) + numstr
            objects.append(map(object_name, range(num_objects)))

    for name in objects:
        err = ctx.manager.do_put(
            pool,
            name,
            '/etc/resolv.conf',
            namespace=namespace)
        assert not err

    try:
        yield
    finally:
        log.info('ceph_verify_lfn_objects verifying...')
        for name in objects:
            err = ctx.manager.do_get(
                pool,
                name,
                namespace=namespace)
            assert not err

        log.info('ceph_verify_lfn_objects deleting...')
        for name in objects:
            err = ctx.manager.do_rm(
                pool,
                name,
                namespace=namespace)
            assert not err

        log.info('ceph_verify_lfn_objects verifying absent...')
        for name in objects:
            err = ctx.manager.do_get(
                pool,
                name,
                namespace=namespace)
            assert err
