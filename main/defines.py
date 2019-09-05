"""
This is a simple map which allows us to use different model class names here than are used in the CellML files.
"""
MODEL_NAME_DICT = {
    'component': 'component',
    'encapsulation': 'encapsulation',
    'math': 'math',
    'model': 'cellmodel',
    'reset': 'reset',
    'unit': 'unit',
    'units': 'compoundunit',
    'variable': 'variable',
}

DISPLAY_DICT = {
    'component': [
        {'field': 'variables', 'obj_type': 'variable', 'title': 'Variables'},
        {'field': 'maths', 'obj_type': 'maths', 'title': 'Maths'},
        {'field': 'resets', 'obj_type': 'reset', 'title': 'Resets'}
    ],
    'variable': [
        {'field': 'compoundunit', 'obj_type': 'compoundunit', 'title': 'Units'},
        {'field': 'components', 'obj_type': 'component', 'title': 'Components'},
    ],
    'reset': [

    ],
    'compoundunit': [

    ],

}

MODEL_CLASSES = {
    'cellmodel': 'model',
    # 'encapsulation': 'encapsulation',
    'component': 'component',
    'math': 'maths',
    'compoundunit': 'compound unit',
    # 'unit': 'unit',
    'variable': 'variable',
    'reset': 'reset',
}

MENU_OPTIONS = {
    'create': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'display': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'edit': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'home': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    'upload': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    },
    '': {
        'create': MODEL_CLASSES,
        'browse': MODEL_CLASSES,
    }
}
