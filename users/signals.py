import logging

from django.core.cache import cache
from django.dispatch import Signal, receiver
# from memcached_stats import MemcachedStats

logger = logging.getLogger(__name__)

logout_signal = Signal()
# mem = MemcachedStats()


@receiver(logout_signal)
def clear_user_cache(sender, **kwargs):
    # Method 1 -> deleting cache without using Low-Level cache
    # for key in mem.keys():
    #    cache.delete(key.replace(':1:', ''))

    # Method 3 -> Using Low-Level cache
    user = kwargs['user']
    cache.delete(user.id)
    logger.info("user's cache deleted")
