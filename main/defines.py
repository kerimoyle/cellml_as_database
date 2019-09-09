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
    'component': {
        'tabs': [
            {'field': 'variables', 'obj_type': 'variable', 'title': 'Variables',
             'template': 'main/tab_default.html'},
            {'field': 'maths', 'obj_type': 'math', 'title': 'Maths', 'template': 'main/tab_maths.html'},
            {'field': 'resets', 'obj_type': 'reset', 'title': 'Resets', 'template': 'main/tab_default.html'},
        ],
        'present_in':
            [
                {'field': 'models', 'obj_type': 'cellmodel', 'title': 'Models'},
            ]
    },

    'variable': {
        'tabs': [
            {'field': 'equivalent_variables', 'obj_type': 'variable', 'title': 'Equivalent variables',
             'template': 'main/tab_default.html'},
        ],
        'present_in':
            [
                {'field': 'component', 'obj_type': 'component', 'title': 'Component'},
                {'field': 'compoundunit', 'obj_type': 'compoundunit', 'title': 'Units'},
            ],
    },

    'reset': {
        'tabs': [],
        'present_in': []
    },

    'compoundunit': {
        'tabs': [
            {'field': 'product_of', 'obj_type': 'compoundunit', 'title': 'Product of',
             'template': 'main/tab_compoundunits.html'},
            {'field': 'part_of', 'obj_type': 'compoundunit', 'title': 'Used in units',
             'template': 'main/tab_units.html'},
            {'field': 'models', 'obj_type': 'cellmodel', 'title': 'Used in models',
             'template': 'main/tab_fyi.html'},
            {'field': 'variables', 'obj_type': 'variable', 'title': 'Used by variables',
             'template': 'main/tab_fyi.html'},
        ],
        'present_in': []
    },
    'cellmodel': {
        'tabs': [
            {'field': 'components', 'obj_type': 'component', 'title': 'Components',
             'template': 'main/tab_default.html'},
            {'field': 'compoundunits', 'obj_type': 'compoundunit', 'title': 'Units',
             'template': 'main/tab_compoundunits.html'},
        ],
        'present_in': []
    }
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
