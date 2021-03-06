# -*- coding: utf-8 -*-

try:
    import ujson as json
except ImportError:
    import json

try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

from .input_option import InputOption


class InputDefinition(object):

    def __init__(self, definition=None):
        definition = definition or []

        self.set_definition(definition)

    def set_definition(self, definition):
        arguments = []
        options = []
        for item in definition:
            if isinstance(item, InputOption):
                options.append(item)
            else:
                arguments.append(item)

        self.set_arguments(arguments)
        self.set_options(options)

    def set_arguments(self, arguments=None):
        arguments = arguments or []

        self.__arguments = OrderedDict()
        self.__required_count = 0
        self.__has_an_array_argument = False
        self.__has_optional = False

        self.add_arguments(arguments)

    def add_arguments(self, arguments=None):
        arguments = arguments or []

        for argument in arguments:
            self.add_argument(argument)

    def add_argument(self, argument):
        if argument.get_name() in self.__arguments:
            raise Exception('An argument with name "%s" already exists.' % argument.get_name())

        if self.__has_an_array_argument:
            raise Exception('Cannot add an argument after a list argument.')

        if argument.is_required() and self.__has_optional:
            raise Exception('Cannot add a required argument after an optional one.')

        if argument.is_list():
            self.__has_an_array_argument = True

        if argument.is_required():
            self.__required_count += 1
        else:
            self.__has_optional = True

        self.__arguments[argument.get_name()] = argument

    def get_argument(self, name):
        arguments = list(self.__arguments.values()) if isinstance(name, int) else self.__arguments

        if not self.has_argument(name):
            raise Exception('The "%s" argument does not exist.' % name)

        return arguments[name]

    def has_argument(self, name):
        arguments = list(self.__arguments.values()) if isinstance(name, int) else self.__arguments

        try:
            arguments[name]

            return True
        except (KeyError, IndexError):
            return False

    def get_arguments(self):
        """
        Gets the list of InputArguments objects.

        :return: A list of InputArguments objects
        :rtype: list
        """
        return list(self.__arguments.values())

    def get_argument_count(self):
        return len(self.__arguments) if not self.__has_an_array_argument else 10000000

    def get_argument_required_count(self):
        return self.__required_count

    def get_argument_defaults(self):
        values = {}

        for argument in self.__arguments.values():
            if not argument.is_required():
                values[argument.get_name()] = argument.get_default()

        return values

    def set_options(self, options=None):
        options = options or []

        self.__options = OrderedDict()
        self.__shortcuts = OrderedDict()

        self.add_options(options)

    def add_options(self, options=None):
        options = options or []

        for option in options:
            self.add_option(option)

    def add_option(self, option):
        if option.get_name() in self.__options \
                and not option.equals(self.__options[option.get_name()]):
            raise Exception('An option named "%s" already exists.' % option.get_name())
        elif option.get_shortcut() in self.__shortcuts \
                and not option.equals(self.__options[self.__shortcuts[option.get_shortcut()]]):
            raise Exception('An option with shortcut "%s" already exists.' % option.get_shortcut())

        self.__options[option.get_name()] = option
        if option.get_shortcut():
            for shortcut in option.get_shortcut().split('|'):
                self.__shortcuts[shortcut] = option.get_name()

    def get_option(self, name):
        if not self.has_option(name):
            raise Exception('The "--%s" option does not exist.' % name)

        return self.__options[name]

    def has_option(self, name):
        return name in self.__options

    def get_options(self):
        return list(self.__options.values())

    def has_shortcut(self, name):
        return name in self.__shortcuts

    def get_option_for_shortcut(self, shortcut):
        return self.get_option(self.shortcut_to_name(shortcut))

    def get_option_defaults(self):
        values = {}
        for option in self.__options.values():
            values[option.get_name()] = option.get_default()

        return values

    def shortcut_to_name(self, shortcut):
        if not self.has_shortcut(shortcut):
            raise Exception('The "-%s" option does not exist.' % shortcut)

        return self.__shortcuts[shortcut]

    def get_synopsis(self, short=False):
        elements = []

        if short and self.get_options():
            elements.append('[options]')
        elif not short:
            for option in self.get_options():
                value = ''


                if option.accept_value():
                    left = ''
                    right = ''

                    if option.is_value_optional():
                        left = '['
                        right = ']'

                    value = ' %s%s%s' % (left, option.get_name().upper(), right)

                shortcut = '-%s|' % option.get_shortcut() if option.get_shortcut() else ''

                elements.append('[%s--%s%s]' % (shortcut, option.get_name(), value))

        if len(elements) and self.get_arguments():
            elements.append('[--]')

        for argument in self.get_arguments():
            element = '<%s>' % argument.get_name()

            if not argument.is_required():
                element = '[%s]' % element
            elif argument.is_list():
                element = '%s (%s)' % (element, element)

            if argument.is_list():
                element += '...'

            elements.append(element)

        return ' '.join(elements)

    def format_default_value(self, default):
        return json.dumps(default)
