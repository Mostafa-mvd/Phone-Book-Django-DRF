from django import template


register = template.Library()


@register.filter
def convert_to_persion_number(value, language):
    converted_number = ""

    if language == 'fa':
        value = str(value)
        for item in value:
            if item == "0":
                converted_number += '۰'
            elif item == "1":
                converted_number += '۱'
            elif item == "2":
                converted_number += '۲'
            elif item == "3":
                converted_number += '۳'
            elif item == "4":
                converted_number += '۴'
            elif item == "5":
                converted_number += '۵'
            elif item == "6":
                converted_number += '۶'
            elif item == "7":
                converted_number += '۷'
            elif item == "8":
                converted_number += '۸'
            elif item == "9":
                converted_number += '۹'
        return converted_number
    return value