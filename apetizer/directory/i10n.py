'''
Created on 23 nov. 2015

@author: biodigitals
'''
'''
Localization related utility methods

Created on Jan 17, 2012

@author: greg
'''
from contextlib import contextmanager

from django.conf import settings
from django.utils import translation
from django.utils.formats import localize
from django.utils.translation import ugettext_lazy as _


MILES_PER_KILOMETER = 0.621371192
YARDS_PER_METER = 1.0936133
YARDS_PER_MILE = 1760.0

_SUPPORTED_COUNTRIES = {}
_SUPPORTED_COUNTRY_CHOICES = ()
CURRENCIES = {}
CURRENCY_BY_COUNTRY = {}
"""
#from moneyed import CURRENCIES
CURRENCY_BY_COUNTRY = {
    'AF': CURRENCIES['AFN'],
    'AL': CURRENCIES['ALL'],
    'DZ': CURRENCIES['DZD'],
    'AS': CURRENCIES['EUR'],
    'AD': CURRENCIES['EUR'],
    'AO': CURRENCIES['AOA'],
    'AI': CURRENCIES['XCD'],
    'AG': CURRENCIES['XCD'],
    'AR': CURRENCIES['ARS'],
    'AM': CURRENCIES['AMD'],
    'AW': CURRENCIES['ANG'],
    'AU': CURRENCIES['AUD'],
    'AT': CURRENCIES['EUR'],
    'AZ': CURRENCIES['AZN'],
    'BS': CURRENCIES['BSD'],
    'BH': CURRENCIES['BHD'],
    'BD': CURRENCIES['BDT'],
    'BB': CURRENCIES['BBD'],
    'BY': CURRENCIES['BYR'],
    'BE': CURRENCIES['EUR'],
    'BZ': CURRENCIES['BZD'],
    #'BJ': CURRENCIES['XOF'],
    'BM': CURRENCIES['BMD'],
    #'BT': CURRENCIES['BTN'],
    #'BO': CURRENCIES['BOB'],
    'BA': CURRENCIES['BAM'],
    'BW': CURRENCIES['BWP'],
    'BV': CURRENCIES['NOK'],
    'BR': CURRENCIES['BRL'],
    'IO': CURRENCIES['USD'],
    'BN': CURRENCIES['BND'],
    'BG': CURRENCIES['BGN'],
    #'BF': CURRENCIES['XOF'],
    'BI': CURRENCIES['BIF'],
    'KH': CURRENCIES['KHR'],
    #'CM': CURRENCIES['XAF'],
    'CA': CURRENCIES['CAD'],
    'CV': CURRENCIES['CVE'],
    'KY': CURRENCIES['KYD'],
    #'CF': CURRENCIES['XAF'],
    #'TD': CURRENCIES['XAF'],
    #'CL': CURRENCIES['CLP'],
    'CN': CURRENCIES['CNY'],
    'CX': CURRENCIES['AUD'],
    'CC': CURRENCIES['AUD'],
    #'CO': CURRENCIES['COP'],
    'KM': CURRENCIES['KMF'],
    #'CG': CURRENCIES['XAF'],
    #'CD': CURRENCIES['CDF'],
    'CK': CURRENCIES['NZD'],
    'CR': CURRENCIES['CRC'],
    'HR': CURRENCIES['HRK'],
    'CU': CURRENCIES['CUP'],
    'CY': CURRENCIES['EUR'],
    'CZ': CURRENCIES['CZK'],
    'DK': CURRENCIES['DKK'],
    'DJ': CURRENCIES['DJF'],
    'DM': CURRENCIES['XCD'],
    'DO': CURRENCIES['DOP'],
    'TP': CURRENCIES['IDR'],
    #'EC': CURRENCIES['ECS'],
    'EG': CURRENCIES['EGP'],
    #'SV': CURRENCIES['SVC'],
    #'GQ': CURRENCIES['XAF'],
    'ER': CURRENCIES['ERN'],
    'EE': CURRENCIES['EEK'],
    'ET': CURRENCIES['ETB'],
    'FK': CURRENCIES['FKP'],
    'FO': CURRENCIES['DKK'],
    'FJ': CURRENCIES['FJD'],
    'FI': CURRENCIES['EUR'],
    'FR': CURRENCIES['EUR'],
    'EN': CURRENCIES['EUR'],
    'GF': CURRENCIES['EUR'],
    'PF': CURRENCIES['XPF'],
    'TF': CURRENCIES['EUR'],
    #'GA': CURRENCIES['XAF'],
    'GM': CURRENCIES['GMD'],
    'GE': CURRENCIES['GEL'],
    'DE': CURRENCIES['EUR'],
    'GH': CURRENCIES['GHS'],
    'GI': CURRENCIES['GIP'],
    'GR': CURRENCIES['EUR'],
    'GL': CURRENCIES['DKK'],
    'GD': CURRENCIES['XCD'],
    'GP': CURRENCIES['EUR'],
    'GU': CURRENCIES['USD'],
    'GT': CURRENCIES['GTQ'],
    'GN': CURRENCIES['GNF'],
    #'GW': CURRENCIES['XOF'],
    'GY': CURRENCIES['GYD'],
    #'HT': CURRENCIES['HTG'],
    'HM': CURRENCIES['AUD'],
    'HN': CURRENCIES['HNL'],
    'HK': CURRENCIES['HKD'],
    'HU': CURRENCIES['HUF'],
    'IS': CURRENCIES['ISK'],
    'IN': CURRENCIES['INR'],
    'ID': CURRENCIES['IDR'],
    'IR': CURRENCIES['IRR'],
    'IQ': CURRENCIES['IQD'],
    'IE': CURRENCIES['EUR'],
    'IL': CURRENCIES['ILS'],
    'IT': CURRENCIES['EUR'],
    #'CI': CURRENCIES['XOF'],
    'JM': CURRENCIES['JMD'],
    'JP': CURRENCIES['JPY'],
    'JO': CURRENCIES['JOD'],
    'KZ': CURRENCIES['KZT'],
    'KE': CURRENCIES['KES'],
    'KI': CURRENCIES['AUD'],
    'KP': CURRENCIES['KPW'],
    'KR': CURRENCIES['KRW'],
    'KW': CURRENCIES['KWD'],
    'KG': CURRENCIES['KGS'],
    'LA': CURRENCIES['LAK'],
    'LV': CURRENCIES['LVL'],
    'LB': CURRENCIES['LBP'],
    #'LS': CURRENCIES['LSL'],
    'LR': CURRENCIES['LRD'],
    'LY': CURRENCIES['LYD'],
    'LI': CURRENCIES['CHF'],
    'LT': CURRENCIES['LTL'],
    'LU': CURRENCIES['EUR'],
    'MO': CURRENCIES['MOP'],
    'MK': CURRENCIES['MKD'],
    #'MG': CURRENCIES['MGF'],
    'MW': CURRENCIES['MWK'],
    'MY': CURRENCIES['MYR'],
    'MV': CURRENCIES['MVR'],
    #'ML': CURRENCIES['XOF'],
    'MT': CURRENCIES['EUR'],
    'MH': CURRENCIES['USD'],
    'MQ': CURRENCIES['EUR'],
    'MR': CURRENCIES['MRO'],
    'MU': CURRENCIES['MUR'],
    'YT': CURRENCIES['EUR'],
    #'MX': CURRENCIES['MXN'],
    'FM': CURRENCIES['USD'],
    'MD': CURRENCIES['MDL'],
    'MC': CURRENCIES['EUR'],
    'MN': CURRENCIES['MNT'],
    'MS': CURRENCIES['XCD'],
    'MA': CURRENCIES['MAD'],
    'MZ': CURRENCIES['MZN'],
    'MM': CURRENCIES['MMK'],
    'NA': CURRENCIES['ZAR'],
    'NR': CURRENCIES['AUD'],
    'NP': CURRENCIES['NPR'],
    'NL': CURRENCIES['EUR'],
    'AN': CURRENCIES['ANG'],
    'NC': CURRENCIES['XPF'],
    'NZ': CURRENCIES['NZD'],
    'NI': CURRENCIES['NIO'],
    #'NE': CURRENCIES['XOF'],
    'NG': CURRENCIES['NGN'],
    'NU': CURRENCIES['NZD'],
    'NF': CURRENCIES['AUD'],
    'MP': CURRENCIES['USD'],
    'NO': CURRENCIES['NOK'],
    'OM': CURRENCIES['OMR'],
    'PK': CURRENCIES['PKR'],
    'PW': CURRENCIES['USD'],
    #'PA': CURRENCIES['PAB'],
    'PG': CURRENCIES['PGK'],
    'PY': CURRENCIES['PYG'],
    'PE': CURRENCIES['PEN'],
    'PH': CURRENCIES['PHP'],
    'PN': CURRENCIES['NZD'],
    'PL': CURRENCIES['PLN'],
    'PT': CURRENCIES['EUR'],
    'PR': CURRENCIES['USD'],
    'QA': CURRENCIES['QAR'],
    'RE': CURRENCIES['EUR'],
    'RO': CURRENCIES['RON'],
    'RU': CURRENCIES['RUB'],
    'RW': CURRENCIES['RWF'],
    'KN': CURRENCIES['XCD'],
    'LC': CURRENCIES['XCD'],
    'VC': CURRENCIES['XCD'],
    'WS': CURRENCIES['WST'],
    'SM': CURRENCIES['EUR'],
    'ST': CURRENCIES['STD'],
    'SA': CURRENCIES['SAR'],
    #'SN': CURRENCIES['XOF'],
    'SC': CURRENCIES['SCR'],
    'SL': CURRENCIES['SLL'],
    'SG': CURRENCIES['SGD'],
    'SK': CURRENCIES['SKK'],
    'SI': CURRENCIES['EUR'],
    'SB': CURRENCIES['SBD'],
    'SO': CURRENCIES['SOS'],
    'ZA': CURRENCIES['ZAR'],
    'GS': CURRENCIES['GBP'],
    'ES': CURRENCIES['EUR'],
    'LK': CURRENCIES['LKR'],
    'SD': CURRENCIES['SDG'],
    'SR': CURRENCIES['SRD'],
    'SJ': CURRENCIES['NOK'],
    'SZ': CURRENCIES['SZL'],
    'SE': CURRENCIES['SEK'],
    'CH': CURRENCIES['CHF'],
    'SY': CURRENCIES['SYP'],
    'TW': CURRENCIES['TWD'],
    'TJ': CURRENCIES['TJS'],
    'TZ': CURRENCIES['TZS'],
    'TH': CURRENCIES['THB'],
    #'TG': CURRENCIES['XOF'],
    'TK': CURRENCIES['NZD'],
    'TO': CURRENCIES['TOP'],
    'TT': CURRENCIES['TTD'],
    'TN': CURRENCIES['TND'],
    'TR': CURRENCIES['TRY'],
    'TM': CURRENCIES['TMM'],
    'TC': CURRENCIES['USD'],
    'TV': CURRENCIES['AUD'],
    'UG': CURRENCIES['UGX'],
    'UA': CURRENCIES['UAH'],
    'AE': CURRENCIES['AED'],
    'GB': CURRENCIES['GBP'],
    'US': CURRENCIES['USD'],
    'UM': CURRENCIES['USD'],
    #'UY': CURRENCIES['UYU'],
    'UZ': CURRENCIES['UZS'],
    'VU': CURRENCIES['VUV'],
    'VA': CURRENCIES['EUR'],
    #'VE': CURRENCIES['VEF'],
    'VN': CURRENCIES['VND'],
    'VG': CURRENCIES['USD'],
    'VI': CURRENCIES['USD'],
    'WF': CURRENCIES['XPF'],
    'EH': CURRENCIES['MAD'],
    'YE': CURRENCIES['YER'],
    #'YU': CURRENCIES['YUN'],
    'ZM': CURRENCIES['ZMK'],
    'ZW': CURRENCIES['ZWD'],
}
"""

def supported_countries():
    ''' 
    Return a dict of Country objects that this system supports.  Pulls
    from COUNTRY_CODES setting
    '''
    global _SUPPORTED_COUNTRIES

    if not _SUPPORTED_COUNTRIES:
        countries = {}
        for code in getattr(settings, 'COUNTRY_CODES', []):
            #countries[code.upper()] = Country(code.upper())
            countries[code.upper()] = code.upper()

        _SUPPORTED_COUNTRIES = countries

    return _SUPPORTED_COUNTRIES


def supported_country_choices():
    '''
    Return a tuple of tuples of Country objects that this system supports.
    Suitable for use in a model or form field's "choices" argument.
    '''
    global _SUPPORTED_COUNTRY_CHOICES

    if not _SUPPORTED_COUNTRY_CHOICES:
        country_list = []
        for country in supported_countries().values():
            country_list.append((country.code, _(country.name)))

        _SUPPORTED_COUNTRY_CHOICES = tuple(country_list)

    return _SUPPORTED_COUNTRY_CHOICES


_SUPPORTED_CURRENCIES = {}
_SUPPORTED_CURRENCY_CHOICES = ()


def supported_currencies():
    ''' 
    Return a dict of Currency objects that this system supports.  Pulls
    from COUNTRY_CODES setting
    '''
    global _SUPPORTED_CURRENCIES

    if not _SUPPORTED_CURRENCIES:
        currencies = {}
        for country in supported_countries().values():
            if country.code in CURRENCY_BY_COUNTRY:
                currency = CURRENCY_BY_COUNTRY[country.code]
                currencies[currency.code] = currency

        _SUPPORTED_CURRENCIES = currencies

    return _SUPPORTED_CURRENCIES


def supported_currency_choices():
    '''
    Return a tuple of tuples of Currency objects that this system supports.
    Suitable for use in a model or form field's "choices" argument.
    '''
    global _SUPPORTED_CURRENCY_CHOICES

    if not _SUPPORTED_CURRENCY_CHOICES:
        currency_list = []
        for currency in supported_currencies().values():
            currency_list.append((currency.code, currency.name))

        _SUPPORTED_CURRENCY_CHOICES = sorted(tuple(currency_list))

    return _SUPPORTED_CURRENCY_CHOICES


def currency_for_country(country):
    '''
    Pass in a django_countries Country and get a moneyed Currency.
    
    If the Country isn't supported you'll get a ValueError.
    If the Currency isn't known you'll get a NotImplemented.
    '''
    if not country or not hasattr(country, 'code'):
        raise ValueError('Must provide a valid Country to look up Currency')

    if country.code not in supported_countries():
        raise ValueError('Country not supported')

    if country.code in CURRENCY_BY_COUNTRY:
        return CURRENCY_BY_COUNTRY[country.code]
    raise NotImplemented('Do not know Currency for Country %s' % country)


def units_for_country(country):
    '''
    Pass in a django_countries Country and get back measurement units, either
    "metric" or "imperial".    
    '''
    if not country or not hasattr(country, 'code'):
        raise ValueError('Must provide a valid Country to look up distance units')

    if country.code == 'US':
        return 'imperial'

    return 'metric'


def shift_currency(money, country):
    '''
    Given some Money, change the currency to the given Country's
    if needed.  Does nothing if the currency is already proper.
    Returns True if the currency was shifted, False otherwise.
    '''
    if money and hasattr(money, 'currency') and country:
        check_currency = currency_for_country(country)
        if money.currency != check_currency:
            money.currency = check_currency
            return True
    return False

'''
Various math methods

Created on Feb 14, 2012

@author: greg
'''

def round_to(x, base=50):
    '''
    Round a number to a given base
    '''
    return int(base * round(float(x)/base))


def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """
    Converts an integer to a base36 string.  
    
    From http://en.wikipedia.org/wiki/Base_36#Python_Conversion_Code
    """
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')

    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36


def base36decode(number):
    return int(number, 36)


def pretty_distance(meters, units='metric'):
    '''
    Given a distance in meters and desired units (metric or imperial),
    return a string of distance suitable for display.
    '''
    if units == 'imperial':
        rounded_distance_yd = round_to(YARDS_PER_METER * meters, 50)
        if rounded_distance_yd >= YARDS_PER_MILE:
            rounded_distance_mi = round(rounded_distance_yd / YARDS_PER_MILE, 1)
            if rounded_distance_mi == 1.0:
                return _(u"1 mile")
            return _(u"%s miles") % localize(rounded_distance_mi)
        else:
            return _(u"%s yards") % localize(rounded_distance_yd)

    rounded_distance_m = round_to(meters, 50)
    if rounded_distance_m >= 1000:
        rounded_distance_km = round(rounded_distance_m / 1000.0, 1)
        if rounded_distance_km == 1.0:
            return _(u"1 km")
        return _(u"%s km") % localize(rounded_distance_km)
    else:
        return _(u"%s meters") % localize(rounded_distance_m)


@contextmanager
def activate_translation(new_translation):
    prev_language = translation.get_language()

    try:
        translation.activate(new_translation)
        yield
    finally:
        translation.activate(prev_language)
        
