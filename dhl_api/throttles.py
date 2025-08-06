from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class ServiceZoneThrottle(UserRateThrottle):
    """
    Throttle class específica para endpoints de service zones
    Permite más requests por ser consultas a datos locales/cache
    """
    scope = 'service_zones'


class ServiceZoneAnonThrottle(AnonRateThrottle):
    """
    Throttle class para usuarios anónimos consultando service zones
    """
    scope = 'service_zones'
