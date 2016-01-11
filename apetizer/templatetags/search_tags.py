import locale

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.template.defaultfilters import stringformat, urlencode
from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _, to_locale, get_language

from apetizer.forms.search import UserInputForm, SearchInputForm,\
    SearchTypesForm,SearchSettingsForm, SearchAgeForm
from apetizer.directory.utils import get_search_session_vars, \
    _get_default_search_vars


@register.filter
def get_paginator_page_url( path, page ):
    
    if path == None:
        path = 'search/'
    
    if int(page) < 1:
        if path == None:
            return ''
        else:
            return path
    
    if path.endswith('search/'):
        return path+'page_'+str(page)+'/'
    else:
        return path+'?page='+str(page)


def get_form_filters(context):

    user_data = get_search_session_vars(context['request'])
    
    context['search_form'] = SearchSettingsForm(initial=user_data)
    
    context['type_form'] = SearchTypesForm(initial=user_data)
    
    context['age_form'] = SearchAgeForm(initial=user_data)
    
    search_filter_forms = ( context['type_form'], context['age_form'] )
    
    context['search_filter_forms'] = search_filter_forms


@register.inclusion_tag('search/filters.html', takes_context=True)
def search_filters(context):
    
    if not 'search_filter_forms' in context:
        get_form_filters(context)
    
    return context


def get_applied_form_filters( applied_filters, default_form, to_form ):
        
    for field_key in default_form.fields:
        
        default_field = default_form[field_key]
        filter_field = to_form[field_key]
        
        if str(default_field.value()) != str(filter_field.value()):
            
            value = None
            #label = default_form.title.split()[0]
            label = filter_field.label
            #try:
            if default_field.name in ('num_vehicle_seats', 'num_vehicle_doors', 'max_age'):
                for choice in default_field.field.widget.choices:
                    #print unicode(choice[1])
                    if str(choice[0]) == str(filter_field.value()):
                        value = unicode(choice[1])
                        break
                if value == None:
                    value = filter_field.value()
            elif default_field.name == 'brand':
                if filter_field.value() in _all_vehicle_brands:
                    value = _all_vehicle_brands[filter_field.value()]
                else:
                    value = filter_field.value()
            else:
                value = filter_field.value()
            
            applied_filters.append({ 'key': default_field.name,
                                     'label': label,
                                     'value': value,
                                     'default': default_field.value()
                                    })
    
    return applied_filters

@register.inclusion_tag('search/applied.html', takes_context=True)
def search_filters_applied(context):
    
    if not 'search_filter_forms' in context:
        get_form_filters(context)
    
    applied_filters = []
    #applied_filters = get_applied_filters(applied_filters,SearchSettingsForm(initial={}),context['search_form'])
    applied_filters = get_applied_form_filters(applied_filters,SearchTypesForm(initial={}),context['type_form'])
    applied_filters = get_applied_form_filters(applied_filters,SearchAgeForm(initial={}),context['age_form'])
    
    context['applied_filters'] = applied_filters
    
    return context


@register.inclusion_tag('search/banner.html', takes_context=True)
def search_banner(context):
    
    user_data = get_search_session_vars(context['request'])
    
    context['search_input_form'] = SearchInputForm(initial=user_data)
    context['search_form'] = SearchSettingsForm(initial=user_data)
    
    context['user_input_form'] = UserInputForm(initial=user_data)
    
    return context


@register.inclusion_tag('search/items/item.html', takes_context=True)
def search_result_item(context, parking_address, result_index):
    
    #context['result_unavailable'] = 'srslt-unavailable' if not parking_address.available else ''
    
    context['result_pa_uid'] = parking_address.id if parking_address.id else ''
    context['result_pa_town'] = parking_address.town if parking_address.town else ''
    context['result_pa_postalcode'] = parking_address.postal_code if parking_address.postal_code else ''    
    context['result_pa_fuzzy_latitude'] = stringformat(parking_address.fuzzy_latitude, ".6f") if parking_address.fuzzy_latitude else ''
    context['result_pa_fuzzy_longitude'] = stringformat(parking_address.fuzzy_longitude, ".6f") if parking_address.fuzzy_longitude else ''
    
    item = parking_address.item
    
    context['result_id'] = item.id
    
    context['result_index'] = result_index
    
    context['result_description'] = item.title
    context['result_owner_name'] = item.get_full_name()
    context['result_comments'] = len(item.get_comments())
    
    context['result_url'] = item.get_url()

    return context

    context['result_pa_rounded_distance'] = _(u'%(distance)s away') % {'distance': parking_address.rounded_distance_string}

    
    vehicle = parking_address.vehicle
    context['result_url'] = vehicle.get_absolute_url()
    
    context['result_type_slug'] = ''
    if vehicle.first_valid_photo():
        result_photo = vehicle.first_valid_photo().url_400x300
    else:
        result_photo = context['STATIC_URL'] + 'css/img/vehicle-default-' + vehicle.type.slug + '.png'
    context['result_photo'] = result_photo
    
    if 'search_tab' in context['user_data']\
        and context['user_data']['search_tab'] == 'tree':
        context['result_short_description'] = (vehicle.driver_notes[:180] + '...') if len(vehicle.driver_notes) > 75 else vehicle.driver_notes
    else:
        context['result_short_description'] = (vehicle.driver_notes[:66] + '...') if len(vehicle.driver_notes) > 75 else vehicle.driver_notes
    
    context['result_make'] = vehicle.model.make.brand
    context['result_model'] = vehicle.model
    context['result_model_name'] = vehicle.model.name
    context['result_year'] = '(' + str(vehicle.year) + ')'
    

    #context['add_fav_title'] = _(u'Add to your favorite')
    #context['del_fav_title'] = _(u'Remove from your favorite')
    #context['favorite_api_url'] = reverse('api_vehicle_favorite')
    
    result_description = vehicle.type.name + ', ' + vehicle.fuel_type.name
    if vehicle.number_of_seats > 0:
        result_description += _(u', %(num_seats)s\u00A0seats') % {'num_seats': vehicle.number_of_seats,}
        if vehicle.num_baby_seat > 0 or vehicle.num_child_seat > 0:
            result_description += _(u' including ')
    if vehicle.num_baby_seat > 0:
        if vehicle.num_baby_seat > 1:
            result_description += _(u'%(num_baby_seat)s\u00A0baby seats ') % {'num_baby_seat':vehicle.num_baby_seat}
        else:
            result_description += _(u'%(num_baby_seat)s\u00A0baby seat ') % {'num_baby_seat':vehicle.num_baby_seat}
    if vehicle.num_baby_seat > 0 and vehicle.num_child_seat > 0:
        result_description += _(u'and ')
    if vehicle.num_child_seat > 0:
        if vehicle.num_child_seat > 1:
            result_description += _(u'%(num_child_seat)s\u00A0child seats') % {'num_child_seat': vehicle.num_child_seat}
        else:
            result_description += _(u'%(num_child_seat)s\u00A0child seat') % {'num_child_seat': vehicle.num_child_seat}
    if vehicle.num_doors > 0:
        result_description += _(u', %(num_doors)s\u00A0doors ') % {'num_doors': vehicle.num_doors}
    context['result_description'] = result_description
    
    context['result_owner_name'] = vehicle.owner.user_profile.display_name
    
    result_new = ''
    if vehicle.created_date > context['x_days_ago']:
        result_new = _(u'New')
    context['result_new'] = result_new
        
    result_rentals = ''
    if context['x_days_ago'] >= vehicle.created_date or vehicle.owner.reservation_count > 0:
        if vehicle.owner.reservation_count > 1:
            result_rentals = _(u'%(reservation_count)s\u00A0rentals') % {'reservation_count': vehicle.owner.reservation_count}
        else:
            result_rentals = _(u'%(reservation_count)s\u00A0rental') % {'reservation_count': vehicle.owner.reservation_count}
    context['result_rentals'] = result_rentals
    
    result_comments = ''
    try:
        positive_comments, negative_comments = get_comments_repartition(vehicle.owner.user_profile)    
        positive_comments_count = len(positive_comments)
        comments_count = positive_comments_count + len(negative_comments)
        if positive_comments_count > 1:
            result_comments = str(positive_comments_count) + ' ' + _(u'positive comments out of') + ' ' + str(comments_count)
        else:
            if comments_count > 0:
                result_comments = str(positive_comments_count) + ' ' + _(u'positive comment out of') + ' ' + str(comments_count)
    except ObjectDoesNotExist:
        pass
    context['result_comments'] = result_comments
    
    result_reactivity = ''
    if vehicle.owner.response_rate:
        result_reactivity = str(parking_address.vehicle.owner.response_rate) + '% ' + _(u'response rate') + ' '
        if vehicle.owner.response_rate > 0 and vehicle.owner.average_response_time:
            result_reactivity += _(u' in') + ' '
            if vehicle.owner.average_response_time_in_hours_and_minutes[0] > 0:
                result_reactivity += str(int(round(parking_address.vehicle.owner.average_response_time_in_hours_and_minutes[0], 0))) + _(u'h')
            else:
                result_reactivity += str(parking_address.vehicle.owner.average_response_time_in_hours_and_minutes[1]) + _(u'm')
    context['result_reactivity'] = result_reactivity
    
    if 'search_tab' in context['user_data']\
        and context['user_data']['search_tab'] == 'tree':
        context['result_price'] = ''
        context['result_duration'] = ''
    else:
        context['result_price'] = vehicle.estimated_cost_without_gas
        context['result_currency_ISO'] = 'EUR'
        context['result_duration'] = _(u'for %(pretty_duration)s and %(estimated_distance)s %(distance_units)s') % {
                                                                                   'pretty_duration': context['pretty_duration'], 
                                                                                   'estimated_distance': context['estimated_distance'], 
                                                                                   'distance_units': vehicle.distance_units}

    loc = locale.normalize(get_language()).split('.')[0]
    #context['result_hourly_price'] = format_money(vehicle.cached_current_rate.without_fuel.hourly, locale=loc, decimal_places=0)
    context['per_hour'] = _(u'/h')
    #context['result_daily_price'] = format_money(vehicle.cached_current_rate.without_fuel.daily, locale=loc, decimal_places=0)
    context['per_day'] = _(u'/d')
    context['result_distance_price'] = vehicle.cached_current_rate.without_fuel.unit_distance
    if parking_address.units == 'imperial':
        per_distance = _(u"/mile")
    else:
        per_distance = _(u"/km")
    context['per_distance'] = per_distance
    context['result_inclusions'] = _(u'%(distance_units)s and insurance included') % {'distance_units': parking_address.vehicle.distance_units}
    
    context['see'] = _(u'See')
    context['this_car'] = _(u'this car')
    
    
    return context

@register.simple_tag(takes_context=True)
def link_to_search(context, start_date, end_date, estimated_distance, search_lat='', search_lng='', title='', btn_color=''):
    
    template_args = {}
    
    if not title:
        title = _(u'Search')
    template_args['title'] = title
    
    default_data = _get_default_search_vars(default_start=start_date, default_end=end_date)
    
    if estimated_distance:
        template_args['estimated_distance'] = estimated_distance
    else:
        template_args['estimated_distance'] = default_data['estimated_distance']
        
    if search_lat:
        template_args['search_lat'] = stringformat(search_lat, ".4f")
    else:
        template_args['search_lat'] = ''

    if search_lng:
        template_args['search_lng'] = stringformat(search_lng, ".4f")
    else:
        template_args['search_lng'] = ''

    template_args['search_radius'] = '2000'
    
    template_args['start_date'] = default_data['start_date']
    template_args['start_hour'] = default_data['start_hour']
    template_args['end_date'] = default_data['end_date']
    template_args['end_hour'] = default_data['end_hour']
    template_args['btn_color'] = 'flat-' + btn_color if btn_color else 'flat-blue'
    

    return render_to_string('search/link.html', template_args, context)
